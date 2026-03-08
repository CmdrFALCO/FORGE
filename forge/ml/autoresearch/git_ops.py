"""Git subprocess helpers for autoresearch workflows."""

import logging
import subprocess
from pathlib import Path
from typing import Iterable

logger = logging.getLogger(__name__)


def _run_git(*args: str, repo_dir: Path, dry_run: bool = False) -> str:
    """Run a git command in repo_dir and return stdout."""
    command = ["git", *args]
    if dry_run:
        logger.info("DRY_RUN git command: %s", " ".join(command))
        return "DRY_RUN"

    completed = subprocess.run(
        command,
        cwd=repo_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(f"git command failed ({' '.join(command)}): {message}")
    return completed.stdout.strip()


def create_branch(name: str, repo_dir: Path, dry_run: bool = False) -> str:
    """Create and checkout a branch."""
    _run_git("checkout", "-b", name, repo_dir=repo_dir, dry_run=dry_run)
    return name


def commit(
    message: str,
    repo_dir: Path,
    files: list[str] | None = None,
    dry_run: bool = False,
) -> str:
    """Commit staged or explicit files and return short git hash."""
    if files:
        _run_git("add", *list(_iter_files(files)), repo_dir=repo_dir, dry_run=dry_run)

    _run_git("commit", "-m", message, repo_dir=repo_dir, dry_run=dry_run)
    return get_current_hash(repo_dir=repo_dir, dry_run=dry_run)


def _iter_files(files: Iterable[str]) -> Iterable[str]:
    """Yield normalized file arguments for git add."""
    for file_path in files:
        if file_path:
            yield file_path


def get_current_hash(repo_dir: Path, dry_run: bool = False) -> str:
    """Return current short commit hash."""
    return _run_git("rev-parse", "--short", "HEAD", repo_dir=repo_dir, dry_run=dry_run)


def get_diff_summary(repo_dir: Path, dry_run: bool = False) -> str:
    """Return diff summary against previous commit."""
    return _run_git("diff", "--stat", "HEAD~1", repo_dir=repo_dir, dry_run=dry_run)


def restore_file(file_path: str, ref: str = "HEAD", *, repo_dir: Path, dry_run: bool = False) -> None:
    """Restore file to the given git ref state."""
    _run_git("checkout", ref, "--", file_path, repo_dir=repo_dir, dry_run=dry_run)

