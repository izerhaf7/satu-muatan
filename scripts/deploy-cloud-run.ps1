[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,

    [Parameter(Mandatory = $true)]
    [string]$Image,

    [Parameter(Mandatory = $true)]
    [string]$ServiceName,

    [Parameter(Mandatory = $true)]
    [string]$MigrationJobName,

    [Parameter(Mandatory = $true)]
    [string]$DatabaseUrlSecret,

    [Parameter(Mandatory = $true)]
    [string]$JwtSecret,

    [Parameter(Mandatory = $true)]
    [string]$CorsOrigins,

    [string]$FirebaseRtdbUrl = "",

    [string]$FirebaseDatabaseSecret = "",

    [string]$Region = "asia-southeast2"
)

$ErrorActionPreference = "Stop"

function Assert-SafeIdentifier([string]$Name, [string]$Value) {
    if ([string]::IsNullOrWhiteSpace($Value) -or $Value -match "[\s,=@]" -or $Value.StartsWith("-")) {
        throw "$Name must not contain whitespace, comma, equals, at-sign, or start with a dash."
    }
}

function Assert-ArtifactRegistryImage([string]$Value) {
    Assert-SafeIdentifier "Image" $Value
    if ($Value -notmatch "^[a-z0-9][a-z0-9.-]*-docker\.pkg\.dev/[a-z0-9][a-z0-9._-]*/[a-z0-9][a-z0-9._-]*/[a-z0-9][a-z0-9._-]*(?::[A-Za-z0-9][A-Za-z0-9._-]*|@sha256:[a-f0-9]{64})$") {
        throw "Image must use Artifact Registry form: REGION-docker.pkg.dev/PROJECT/REPOSITORY/IMAGE:TAG."
    }
}

function Assert-CorsOrigins([string]$Value) {
    $origins = $Value.Split(",")
    if ($origins.Count -eq 0) { throw "CorsOrigins must contain at least one origin." }

    foreach ($origin in $origins) {
        if ($origin -match "\s|@" -or -not [uri]::IsWellFormedUriString($origin, [System.UriKind]::Absolute)) {
            throw "CorsOrigins must contain comma-separated absolute HTTP(S) origins only."
        }
        $uri = [uri]$origin
        if ($uri.Scheme -notin @("http", "https") -or -not [string]::IsNullOrEmpty($uri.UserInfo) -or $uri.Query -or $uri.Fragment -or $uri.AbsolutePath -ne "/") {
            throw "CorsOrigins must contain origins without path, query, fragment, or userinfo."
        }
    }

    return $origins -join ","
}

Assert-SafeIdentifier "ProjectId" $ProjectId
Assert-ArtifactRegistryImage $Image
Assert-SafeIdentifier "ServiceName" $ServiceName
Assert-SafeIdentifier "MigrationJobName" $MigrationJobName
Assert-SafeIdentifier "DatabaseUrlSecret" $DatabaseUrlSecret
Assert-SafeIdentifier "JwtSecret" $JwtSecret
Assert-SafeIdentifier "Region" $Region
if (-not [string]::IsNullOrWhiteSpace($FirebaseDatabaseSecret)) {
    Assert-SafeIdentifier "FirebaseDatabaseSecret" $FirebaseDatabaseSecret
}
$CorsOrigins = Assert-CorsOrigins $CorsOrigins

$secretBindings = "DATABASE_URL=$DatabaseUrlSecret`:latest,JWT_SECRET=$JwtSecret`:latest"
if (-not [string]::IsNullOrWhiteSpace($FirebaseDatabaseSecret)) {
    $secretBindings += ",FIREBASE_DATABASE_SECRET=$FirebaseDatabaseSecret`:latest"
}
$runtimeEnvironment = "^@^RUN_MIGRATIONS=false@VENDOR_ADAPTER=MOCK@DEMO_MODE=true@CORS_ORIGINS=$CorsOrigins@FIREBASE_TIMEOUT_DETIK=5"
if (-not [string]::IsNullOrWhiteSpace($FirebaseRtdbUrl)) {
    $runtimeEnvironment += "@FIREBASE_RTDB_URL=$FirebaseRtdbUrl"
}
$migrationFlagsPath = Join-Path $PSScriptRoot "cloud-run-migration-flags.yaml"

Write-Host "Deploying serialized migration job $MigrationJobName. Secret values stay in Secret Manager."
& gcloud run jobs deploy $MigrationJobName `
    --project $ProjectId `
    --region $Region `
    --image $Image `
    --command alembic `
    --flags-file $migrationFlagsPath `
    --set-secrets $secretBindings `
    --tasks 1 `
    --parallelism 1 `
    --max-retries 0 `
    --quiet
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Executing migration job before service rollout."
& gcloud run jobs execute $MigrationJobName `
    --project $ProjectId `
    --region $Region `
    --wait `
    --quiet
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Deploying Cloud Run revision without traffic."
& gcloud run deploy $ServiceName `
    --project $ProjectId `
    --region $Region `
    --image $Image `
    --update-env-vars $runtimeEnvironment `
    --update-secrets $secretBindings `
    --no-traffic `
    --quiet
exit $LASTEXITCODE
