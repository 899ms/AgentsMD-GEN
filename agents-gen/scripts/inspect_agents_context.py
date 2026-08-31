#!/usr/bin/env python3
"""Collect deterministic, read-only evidence for AGENTS.md lifecycle decisions."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional


SCHEMA_VERSION = "1.0"
SKIP_DIRS = {
    ".git",
    ".hg",
    ".idea",
    ".mypy_cache",
    ".next",
    ".pytest_cache",
    ".ruff_cache",
    ".svn",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "out",
    "target",
    "vendor",
}
MANIFEST_NAMES = {
    "Cargo.toml",
    "Gemfile",
    "go.mod",
    "package.json",
    "pom.xml",
    "pyproject.toml",
    "requirements.txt",
}
LOCKFILE_NAMES = {
    "Cargo.lock",
    "Gemfile.lock",
    "bun.lock",
    "bun.lockb",
    "composer.lock",
    "package-lock.json",
    "pnpm-lock.yaml",
    "poetry.lock",
    "uv.lock",
    "yarn.lock",
}
TASK_FILE_NAMES = {
    "Makefile",
    "Taskfile.yml",
    "Taskfile.yaml",
    "justfile",
}
INSTRUCTION_NAMES = {"AGENTS.md", "AGENTS.override.md", "CLAUDE.md"}
DOC_NAMES = {"CONTRIBUTING.md", "DEVELOPMENT.md", "README.md"}
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")


def iter_project_files(project: Path):
    for root, dirs, files in os.walk(project, followlinks=False):
        dirs[:] = sorted(name for name in dirs if name not in SKIP_DIRS)
        root_path = Path(root)
        for name in sorted(files):
            yield root_path / name


def relative(project: Path, path: Path) -> str:
    return path.relative_to(project).as_posix()


def read_text(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None


def instruction_record(project: Path, path: Path) -> dict[str, Any]:
    text = read_text(path)
    is_symlink = path.is_symlink()
    target_exists = path.exists() if is_symlink else None
    return {
        "path": relative(project, path),
        "kind": path.name,
        "scope": relative(project, path.parent) or ".",
        "line_count": len(text.splitlines()) if text is not None else None,
        "review_size": len(text.splitlines()) > 50 if text is not None else None,
        "is_symlink": is_symlink,
        "symlink_target_exists": target_exists,
        "readable": text is not None,
    }


def package_scripts(project: Path, package_json: Path) -> dict[str, Any]:
    text = read_text(package_json)
    if text is None:
        return {"path": relative(project, package_json), "error": "unreadable"}
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return {
            "path": relative(project, package_json),
            "error": f"invalid JSON at line {exc.lineno}",
        }
    scripts = data.get("scripts")
    return {
        "path": relative(project, package_json),
        "package_manager": data.get("packageManager"),
        "scripts": scripts if isinstance(scripts, dict) else {},
    }


def run_git(project: Path, *args: str) -> tuple[int, str]:
    completed = subprocess.run(
        ["git", "-C", str(project), *args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    return completed.returncode, completed.stdout.rstrip()


def parse_status_z(raw: str) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    parts = raw.split("\0")
    index = 0
    while index < len(parts):
        item = parts[index]
        if not item:
            index += 1
            continue
        status = item[:2]
        path = item[3:] if len(item) > 3 else ""
        record = {"status": status, "path": path}
        if "R" in status or "C" in status:
            if index + 1 < len(parts) and parts[index + 1]:
                record["source_path"] = parts[index + 1]
                index += 1
        records.append(record)
        index += 1
    return records


def git_record(project: Path) -> dict[str, Any]:
    if not (project / ".git").exists():
        return {"present": False, "root": None, "scope": "none", "changes": []}

    root_code, root_raw = run_git(project, "rev-parse", "--show-toplevel")
    git_root = Path(root_raw).resolve() if root_code == 0 and root_raw else None
    scope = "project" if git_root == project else "mismatch"
    changes: list[dict[str, str]] = []
    if scope == "project":
        status_code, status_raw = run_git(
            project,
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
        )
        if status_code == 0:
            changes = parse_status_z(status_raw)
    return {
        "present": True,
        "root": str(git_root) if git_root else None,
        "scope": scope,
        "changes": changes,
    }


def link_records(project: Path, instruction_paths: list[Path]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for source in instruction_paths:
        text = read_text(source)
        if text is None:
            continue
        for raw_target in MARKDOWN_LINK.findall(text):
            target = raw_target.strip().split(maxsplit=1)[0].strip("<>")
            if not target or target.startswith(("#", "http://", "https://", "mailto:")):
                continue
            clean_target = target.split("#", 1)[0]
            resolved = (source.parent / clean_target).resolve()
            records.append(
                {
                    "source": relative(project, source),
                    "target": target,
                    "exists": resolved.exists(),
                    "inside_project": resolved == project or project in resolved.parents,
                }
            )
    return records


def inspect(project: Path) -> dict[str, Any]:
    files = list(iter_project_files(project))
    instructions = [path for path in files if path.name in INSTRUCTION_NAMES]
    manifests = [relative(project, path) for path in files if path.name in MANIFEST_NAMES]
    lockfiles = [relative(project, path) for path in files if path.name in LOCKFILE_NAMES]
    task_files = [relative(project, path) for path in files if path.name in TASK_FILE_NAMES]
    docs = [
        relative(project, path)
        for path in files
        if path.name in DOC_NAMES or ("docs" in path.relative_to(project).parts and path.suffix.lower() == ".md")
    ]
    packages = [package_scripts(project, path) for path in files if path.name == "package.json"]
    return {
        "schema_version": SCHEMA_VERSION,
        "project_root": str(project),
        "git": git_record(project),
        "instruction_files": [instruction_record(project, path) for path in instructions],
        "manifests": manifests,
        "lockfiles": lockfiles,
        "task_files": task_files,
        "documentation": docs,
        "package_json": packages,
        "instruction_links": link_records(project, instructions),
    }


def main(argv: Optional[list[str]] = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("Usage: inspect_agents_context.py <absolute-project-path>", file=sys.stderr)
        return 2

    raw_path = Path(args[0]).expanduser()
    if not raw_path.is_absolute():
        print("Project path must be absolute.", file=sys.stderr)
        return 2
    project = raw_path.resolve()
    if not project.is_dir():
        print(f"Project directory does not exist: {project}", file=sys.stderr)
        return 2

    print(json.dumps(inspect(project), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
