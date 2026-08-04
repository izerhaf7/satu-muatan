$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "deploy-cloud-run.ps1"
$temporaryDirectory = Join-Path ([System.IO.Path]::GetTempPath()) ("satu-muatan-gcloud-stub-" + [guid]::NewGuid())
$logPath = Join-Path $temporaryDirectory "gcloud.log"
$stubPath = Join-Path $temporaryDirectory "gcloud.cmd"
$stubScriptPath = Join-Path $temporaryDirectory "gcloud-stub.ps1"
$databaseSecret = "database-url-secret"
$jwtSecret = "jwt-secret"
$unrelatedExistingBinding = "GOOGLE_MAPS_API_KEY=maps-key:latest"

New-Item -ItemType Directory -Path $temporaryDirectory | Out-Null
"@echo off`r`npowershell -NoProfile -ExecutionPolicy Bypass -File `"%~dp0gcloud-stub.ps1`" %*`r`n" | Set-Content -LiteralPath $stubPath -NoNewline
@'
param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)
[System.IO.File]::AppendAllText($env:GCLOUD_STUB_LOG, ($Arguments -join [Environment]::NewLine) + [Environment]::NewLine + "--CALL--" + [Environment]::NewLine)
'@ | Set-Content -LiteralPath $stubScriptPath -NoNewline

function Assert-True([bool]$Condition, [string]$Message) {
    if (-not $Condition) { throw $Message }
}

function Invoke-Deploy([string[]]$Arguments) {
    $oldPath = $env:PATH
    $previousErrorActionPreference = $ErrorActionPreference
    try {
        $env:PATH = "$temporaryDirectory$([System.IO.Path]::PathSeparator)$oldPath"
        $env:GCLOUD_STUB_LOG = $logPath
        $ErrorActionPreference = "Continue"
        return & powershell -NoProfile -ExecutionPolicy Bypass -File $scriptPath @Arguments 2>&1
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
        $env:PATH = $oldPath
        Remove-Item Env:GCLOUD_STUB_LOG -ErrorAction SilentlyContinue
    }
}

try {
    $output = Invoke-Deploy @(
        "-ProjectId", "alexas-503209",
        "-Image", "asia-southeast2-docker.pkg.dev/alexas-503209/satu-muatan/api:commit-sha",
        "-ServiceName", "satu-muatan-api",
        "-MigrationJobName", "satu-muatan-migrate",
        "-DatabaseUrlSecret", $databaseSecret,
        "-JwtSecret", $jwtSecret,
        "-CorsOrigins", "https://satu-muatan.vercel.app,https://preview.example.test",
        "-Region", "asia-southeast2"
    )
    Assert-True ($LASTEXITCODE -eq 0) "Deploy script failed with gcloud stub."
    $calls = (Get-Content -LiteralPath $logPath -Raw) -split [regex]::Escape("--CALL--") | Where-Object { $_.Trim() } | ForEach-Object { ($_ -replace "`r`n", "`n").Trim() }
    Assert-True ($calls.Count -eq 3) "Expected exactly three gcloud calls."
    Assert-True ($calls[0] -match "^run`njobs`ndeploy`nsatu-muatan-migrate") "First call must deploy migration job."
    Assert-True ($calls[0] -match "--command`nalembic" -and $calls[0] -match "--args`nupgrade,head") "Migration job must invoke alembic upgrade head."
    Assert-True ($calls[0] -match "--tasks`n1" -and $calls[0] -match "--parallelism`n1" -and $calls[0] -match "--max-retries`n0") "Migration job must be serialized with no retries."
    Assert-True ($calls[1] -match "^run`njobs`nexecute`nsatu-muatan-migrate" -and $calls[1] -match "--wait") "Second call must wait for migration execution."
    Assert-True ($calls[2] -match "^run`ndeploy`nsatu-muatan-api" -and $calls[2] -match "--no-traffic") "Third call must deploy service without traffic."
    Assert-True ((Get-Content -LiteralPath $scriptPath -Raw) -match '"\^\^\^\^@\^\^\^\^RUN_MIGRATIONS=false') "PowerShell source must escape custom delimiter carets."
    Assert-True ($calls[2] -match "--update-env-vars`n\^@\^RUN_MIGRATIONS=false@VENDOR_ADAPTER=MOCK@DEMO_MODE=true@CORS_ORIGINS=https://satu-muatan.vercel.app,https://preview.example.test") "Service must update one custom-delimited CORS value and disable runtime migrations."
    Assert-True ($calls[2] -match "--update-secrets`nDATABASE_URL=$databaseSecret`:latest,JWT_SECRET=$jwtSecret`:latest") "Service must update required secret bindings."
    Assert-True ($calls[2] -notmatch "--set-env-vars|--set-secrets") "Service must not replace existing runtime configuration."
    Assert-True ($calls[2] -notmatch [regex]::Escape($unrelatedExistingBinding)) "Service arguments must not include or replace unrelated existing secret bindings."
    Assert-True ($calls[0] -match "DATABASE_URL=$databaseSecret`:latest,JWT_SECRET=$jwtSecret`:latest") "Migration job must receive secret names."
    Assert-True ($calls[2] -match "DATABASE_URL=$databaseSecret`:latest,JWT_SECRET=$jwtSecret`:latest") "Service must receive secret names."
    Assert-True (($output -join "`n") -notmatch "postgresql://|test-secret-value") "Deploy output must not print secret values."

    $validArguments = @(
        "-ProjectId", "alexas-503209",
        "-Image", "asia-southeast2-docker.pkg.dev/alexas-503209/satu-muatan/api:commit-sha",
        "-ServiceName", "satu-muatan-api",
        "-MigrationJobName", "satu-muatan-migrate",
        "-DatabaseUrlSecret", $databaseSecret,
        "-JwtSecret", $jwtSecret,
        "-CorsOrigins", "https://satu-muatan.vercel.app",
        "-Region", "asia-southeast2"
    )
    $invalidIdentifiers = @(
        @("-ProjectId", "alexas-503209 --quiet"), @("-ServiceName", "service,name"),
        @("-MigrationJobName", "job=value"), @("-DatabaseUrlSecret", "database@secret"),
        @("-JwtSecret", "-jwt-secret"), @("-Region", "asia southeast2"),
        @("-Image", "-image"), @("-Image", "registry.example.test/api:commit-sha")
    )
    foreach ($invalidIdentifier in $invalidIdentifiers) {
        Remove-Item -LiteralPath $logPath -ErrorAction SilentlyContinue
        $index = [array]::IndexOf($validArguments, $invalidIdentifier[0]) + 1
        $arguments = [string[]]$validArguments.Clone()
        $arguments[$index] = $invalidIdentifier[1]
        $null = Invoke-Deploy $arguments
        Assert-True ($LASTEXITCODE -ne 0) "Invalid $($invalidIdentifier[0]) must fail validation."
        Assert-True (-not (Test-Path -LiteralPath $logPath)) "Invalid $($invalidIdentifier[0]) must not invoke gcloud."
    }
    foreach ($invalidCors in @("https://example.test/path", "https://example.test?query=value", "https://user@example.test", "ftp://example.test", "https://one.test, https://two.test")) {
        Remove-Item -LiteralPath $logPath -ErrorAction SilentlyContinue
        $arguments = [string[]]$validArguments.Clone()
        $arguments[[array]::IndexOf($arguments, "-CorsOrigins") + 1] = $invalidCors
        $null = Invoke-Deploy $arguments
        Assert-True ($LASTEXITCODE -ne 0) "Invalid CorsOrigins must fail validation."
        Assert-True (-not (Test-Path -LiteralPath $logPath)) "Invalid CorsOrigins must not invoke gcloud."
    }
}
finally {
    Remove-Item -Recurse -Force -LiteralPath $temporaryDirectory -ErrorAction SilentlyContinue
}
