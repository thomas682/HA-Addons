#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path, PurePosixPath


CONFIG_PATH = "influxbro/config.yaml"
CODE_FILENAMES = {"Dockerfile"}
CODE_SUFFIXES = {".py", ".html", ".js", ".css", ".sh"}


def _git(repo: Path, *args: str, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        input=input_text,
        capture_output=True,
        check=False,
    )


def _changed_paths(repo: Path, *args: str) -> list[str]:
    proc = _git(repo, *args)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "git command failed")
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def _is_code_path(path: str) -> bool:
    p = PurePosixPath(path)
    return p.name in CODE_FILENAMES or p.suffix.lower() in CODE_SUFFIXES


def _diff_has_version_bump(diff_text: str) -> bool:
    old_version = None
    new_version = None
    for line in diff_text.splitlines():
        if line.startswith("---") or line.startswith("+++"):
            continue
        if line.startswith("-") and "version:" in line:
            old_version = line[1:].strip()
        elif line.startswith("+") and "version:" in line:
            new_version = line[1:].strip()
    return bool(old_version and new_version and old_version != new_version)


def _staged_diff_has_version_bump(repo: Path) -> bool:
    proc = _git(repo, "diff", "--cached", "--unified=0", "--", CONFIG_PATH)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "git diff failed")
    return _diff_has_version_bump(proc.stdout)


def _commit_has_version_bump(repo: Path, commit: str) -> bool:
    proc = _git(repo, "diff", f"{commit}^!", "--unified=0", "--", CONFIG_PATH)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "git diff failed")
    return _diff_has_version_bump(proc.stdout)


def _commits_for_push(repo: Path, updates: list[tuple[str, str]]) -> list[str]:
    commits: list[str] = []
    seen: set[str] = set()
    for local_sha, remote_sha in updates:
        if not local_sha or local_sha == "0" * 40:
            continue
        if remote_sha and remote_sha != "0" * 40:
            proc = _git(repo, "rev-list", "--reverse", f"{remote_sha}..{local_sha}")
        else:
            proc = _git(repo, "rev-list", "--reverse", local_sha, "--not", "--all")
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "git rev-list failed")
        for line in proc.stdout.splitlines():
            sha = line.strip()
            if sha and sha not in seen:
                seen.add(sha)
                commits.append(sha)
    return commits


def _run_pre_commit(repo: Path) -> int:
    paths = _changed_paths(repo, "diff", "--cached", "--name-only", "--diff-filter=ACMR")
    code_paths = [path for path in paths if _is_code_path(path)]
    if not code_paths:
        return 0
    if CONFIG_PATH not in paths:
        print(
            "Versionsbump fehlt: Code-Aenderungen sind gestaged, aber influxbro/config.yaml ist nicht Teil des Commits.",
            file=sys.stderr,
        )
        return 1
    if not _staged_diff_has_version_bump(repo):
        print(
            "Versionsbump fehlt: influxbro/config.yaml ist gestaged, aber die version:-Zeile wurde in diesem Commit nicht erhoeht.",
            file=sys.stderr,
        )
        return 1
    return 0


def _run_pre_push(repo: Path, stdin_text: str) -> int:
    updates: list[tuple[str, str]] = []
    for line in stdin_text.splitlines():
        parts = line.strip().split()
        if len(parts) != 4:
            continue
        _local_ref, local_sha, _remote_ref, remote_sha = parts
        updates.append((local_sha, remote_sha))
    for commit in _commits_for_push(repo, updates):
        paths = _changed_paths(repo, "diff-tree", "--no-commit-id", "--name-only", "-r", commit)
        if not any(_is_code_path(path) for path in paths):
            continue
        if not _commit_has_version_bump(repo, commit):
            print(
                f"Push blockiert: Commit {commit[:12]} enthaelt Code-Aenderungen ohne Versionsbump in {CONFIG_PATH}.",
                file=sys.stderr,
            )
            return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("pre-commit", "pre-push"), required=True)
    parser.add_argument("--repo", default=".")
    args = parser.parse_args()
    repo = Path(args.repo).resolve()

    try:
        if args.mode == "pre-commit":
            return _run_pre_commit(repo)
        return _run_pre_push(repo, sys.stdin.read())
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
