import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest


ENTRYPOINT = Path(os.environ.get("ENTRYPOINT_PATH", Path(__file__).resolve().parents[1] / "docker-entrypoint.sh"))


def _command_stub(directory: Path, name: str, log_path: Path) -> None:
    command = directory / name
    command.write_text(
        "#!/bin/sh\n"
        f"printf '%s %s\\n' '{name}' \"$*\" >> '{log_path.as_posix()}'\n",
        encoding="utf-8",
    )
    command.chmod(command.stat().st_mode | stat.S_IXUSR)


def _run_entrypoint(tmp_path: Path, run_migrations: str | None) -> list[str]:
    shell = shutil.which("sh")
    if shell is None:
        pytest.skip("POSIX shell tidak tersedia")

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log_path = tmp_path / "commands.log"
    _command_stub(bin_dir, "alembic", log_path)
    _command_stub(bin_dir, "uvicorn", log_path)

    env = os.environ | {"PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}", "PORT": "9123"}
    env.pop("RUN_MIGRATIONS", None)
    if run_migrations is not None:
        env["RUN_MIGRATIONS"] = run_migrations

    result = subprocess.run([shell, str(ENTRYPOINT)], env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr

    return log_path.read_text(encoding="utf-8").splitlines()


def test_entrypoint_default_mengabaikan_run_migrations_false_dari_host(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RUN_MIGRATIONS", "false")
    assert _run_entrypoint(tmp_path, None) == [
        "alembic upgrade head",
        "uvicorn app.main:app --host 0.0.0.0 --port 9123",
    ]


def test_entrypoint_run_migrations_false_menjalankan_uvicorn_tanpa_alembic(tmp_path: Path) -> None:
    assert _run_entrypoint(tmp_path, "false") == [
        "uvicorn app.main:app --host 0.0.0.0 --port 9123",
    ]


def test_entrypoint_run_migrations_tak_terduga_tetap_menjalankan_migrasi(tmp_path: Path) -> None:
    assert _run_entrypoint(tmp_path, "unexpected") == [
        "alembic upgrade head",
        "uvicorn app.main:app --host 0.0.0.0 --port 9123",
    ]
