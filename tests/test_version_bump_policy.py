from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "check_version_bump.py"


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True, check=False)


def _write(repo: Path, rel: str, content: str) -> None:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _commit(repo: Path, message: str) -> str:
    env = {
        "GIT_AUTHOR_NAME": "Test User",
        "GIT_AUTHOR_EMAIL": "test@example.com",
        "GIT_COMMITTER_NAME": "Test User",
        "GIT_COMMITTER_EMAIL": "test@example.com",
    }
    proc = subprocess.run(["git", "commit", "-m", message], cwd=repo, text=True, capture_output=True, check=False, env=env)
    assert proc.returncode == 0, proc.stderr
    head = _git(repo, "rev-parse", "HEAD")
    assert head.returncode == 0
    return head.stdout.strip()


def _init_repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    assert _git(repo, "init").returncode == 0
    _write(repo, "influxbro/config.yaml", 'version: "1.0.0"\n')
    _write(repo, "influxbro/app/app.py", 'print("v1")\n')
    _write(repo, "README.md", "demo\n")
    assert _git(repo, "add", ".").returncode == 0
    base = _commit(repo, "base")
    return repo, base


def _run_guard(repo: Path, mode: str, stdin_text: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(ROOT / ".venv" / "bin" / "python3"), str(SCRIPT), "--mode", mode, "--repo", str(repo)],
        cwd=ROOT,
        text=True,
        input=stdin_text,
        capture_output=True,
        check=False,
    )


def test_precommit_rejects_code_change_without_version_bump(tmp_path):
    repo, _base = _init_repo(tmp_path)
    _write(repo, "influxbro/app/app.py", 'print("v2")\n')
    assert _git(repo, "add", "influxbro/app/app.py").returncode == 0
    proc = _run_guard(repo, "pre-commit")
    assert proc.returncode == 1
    assert "Versionsbump fehlt" in proc.stderr


def test_precommit_accepts_code_change_with_staged_version_bump(tmp_path):
    repo, _base = _init_repo(tmp_path)
    _write(repo, "influxbro/app/app.py", 'print("v2")\n')
    _write(repo, "influxbro/config.yaml", 'version: "1.0.1"\n')
    assert _git(repo, "add", "influxbro/app/app.py", "influxbro/config.yaml").returncode == 0
    proc = _run_guard(repo, "pre-commit")
    assert proc.returncode == 0


def test_prepush_rejects_commit_without_version_bump(tmp_path):
    repo, base = _init_repo(tmp_path)
    _write(repo, "influxbro/app/app.py", 'print("v2")\n')
    assert _git(repo, "add", "influxbro/app/app.py").returncode == 0
    head = _commit(repo, "code only")
    proc = _run_guard(repo, "pre-push", f"refs/heads/main {head} refs/heads/main {base}\n")
    assert proc.returncode == 1
    assert "Push blockiert" in proc.stderr


def test_prepush_accepts_commit_with_version_bump(tmp_path):
    repo, base = _init_repo(tmp_path)
    _write(repo, "influxbro/app/app.py", 'print("v2")\n')
    _write(repo, "influxbro/config.yaml", 'version: "1.0.1"\n')
    assert _git(repo, "add", "influxbro/app/app.py", "influxbro/config.yaml").returncode == 0
    head = _commit(repo, "code with bump")
    proc = _run_guard(repo, "pre-push", f"refs/heads/main {head} refs/heads/main {base}\n")
    assert proc.returncode == 0
