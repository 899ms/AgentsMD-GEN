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


SCHEMA_VERSION = "1.2"
GUIDE_DIRECTORY_NAME = ".agent-guides"
GUIDE_ENTRY_NAME = "GUIDE.md"
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
WORKSPACE_FILE_NAMES = {
    "go.work",
    "lerna.json",
    "nx.json",
    "pnpm-workspace.yaml",
    "pnpm-workspace.yml",
    "turbo.json",
}
SUBPROJECT_MANIFEST_NAMES = {
    "Cargo.toml",
    "Gemfile",
    "SKILL.md",
    "go.mod",
    "package.json",
    "pom.xml",
    "pyproject.toml",
}
INSTRUCTION_NAMES = {"AGENTS.md", "AGENTS.override.md", "CLAUDE.md"}
DOC_NAMES = {"CONTRIBUTING.md", "DEVELOPMENT.md", "README.md"}
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
INLINE_CODE = re.compile(r"`([^`\n]+)`")
PATH_SUFFIXES = {
    ".c",
    ".cpp",
    ".go",
    ".h",
    ".java",
    ".js",
    ".json",
    ".jsx",
    ".md",
    ".py",
    ".rb",
    ".rs",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".yaml",
    ".yml",
}


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


def guide_description(path: Path) -> tuple[Optional[str], Optional[str]]:
    text = read_text(path)
    if text is None:
        return None, "unreadable"
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, "missing_frontmatter"
    try:
        closing = next(
            index for index, line in enumerate(lines[1:21], start=1)
            if line.strip() == "---"
        )
    except StopIteration:
        return None, "unterminated_frontmatter"

    values = []
    for line in lines[1:closing]:
        key, separator, value = line.partition(":")
        if separator and key.strip() == "description":
            values.append(value.strip())
    if not values:
        return None, "missing_description"
    if len(values) > 1:
        return None, "duplicate_description"
    value = values[0]
    if not value:
        return None, "empty_description"
    if value in {">", "|", ">-", "|-", ">+", "|+"}:
        return None, "multiline_description"
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1].strip()
    if not value:
        return None, "empty_description"
    return value, None


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
    workspaces = data.get("workspaces")
    return {
        "path": relative(project, package_json),
        "name": data.get("name"),
        "private": data.get("private"),
        "package_manager": data.get("packageManager"),
        "scripts": scripts if isinstance(scripts, dict) else {},
        "workspaces": workspaces if isinstance(workspaces, (list, dict)) else None,
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


def reference_record(
    project: Path, source: Path, target: str, kind: str
) -> dict[str, Any]:
    clean_target = target.split("#", 1)[0]
    candidate = Path(clean_target).expanduser()
    resolved = (
        candidate.resolve()
        if candidate.is_absolute()
        else (source.parent / candidate).resolve()
    )
    return {
        "source": relative(project, source),
        "target": target,
        "kind": kind,
        "exists": resolved.exists(),
        "inside_project": resolved == project or project in resolved.parents,
    }


def link_records(project: Path, source_paths: list[Path]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for source in source_paths:
        text = read_text(source)
        if text is None:
            continue
        for raw_target in MARKDOWN_LINK.findall(text):
            target = raw_target.strip().split(maxsplit=1)[0].strip("<>")
            if not target or target.startswith(("#", "http://", "https://", "mailto:")):
                continue
            records.append(reference_record(project, source, target, "markdown_link"))
    return records


def looks_like_file_path(value: str) -> bool:
    candidate = value.strip().strip("<>")
    if not candidate or any(character.isspace() for character in candidate):
        return False
    if candidate.startswith(("#", "http://", "https://", "mailto:", "${")):
        return False
    if any(character in candidate for character in ("*", "|", ";", "=")):
        return False
    suffix = Path(candidate.split("#", 1)[0]).suffix.lower()
    return suffix in PATH_SUFFIXES or Path(candidate).name in (
        INSTRUCTION_NAMES | MANIFEST_NAMES | TASK_FILE_NAMES | DOC_NAMES | WORKSPACE_FILE_NAMES
    )


def instruction_path_records(
    project: Path, instruction_paths: list[Path]
) -> list[dict[str, Any]]:
    records = link_records(project, instruction_paths)
    seen = {(item["source"], item["target"], item["kind"]) for item in records}
    for source in instruction_paths:
        text = read_text(source)
        if text is None:
            continue
        for raw_target in INLINE_CODE.findall(text):
            target = raw_target.strip().strip("<>")
            key = (relative(project, source), target, "inline_code")
            if looks_like_file_path(target) and key not in seen:
                records.append(reference_record(project, source, target, "inline_code"))
                seen.add(key)
    return records


def subproject_records(project: Path, files: list[Path]) -> list[dict[str, Any]]:
    manifests_by_scope: dict[Path, list[Path]] = {}
    task_files_by_scope: dict[Path, list[Path]] = {}
    for path in files:
        if path.parent == project:
            continue
        if path.name in SUBPROJECT_MANIFEST_NAMES:
            manifests_by_scope.setdefault(path.parent, []).append(path)
        if path.name in TASK_FILE_NAMES:
            task_files_by_scope.setdefault(path.parent, []).append(path)

    records: list[dict[str, Any]] = []
    for scope_path in sorted(manifests_by_scope, key=lambda item: relative(project, item)):
        scope = relative(project, scope_path)
        agents_path = scope_path / "AGENTS.md"
        evidence = sorted(
            relative(project, path)
            for path in manifests_by_scope[scope_path] + task_files_by_scope.get(scope_path, [])
        )
        records.append(
            {
                "scope": scope,
                "evidence": evidence,
                "agents_path": relative(project, agents_path),
                "agents_exists": agents_path.is_file(),
            }
        )
    return records


def guide_directory_for(project: Path, path: Path) -> Optional[Path]:
    for parent in path.parents:
        if parent == project.parent:
            break
        if parent.name == GUIDE_DIRECTORY_NAME:
            return parent
        if parent == project:
            break
    return None


def guide_records(
    project: Path, files: list[Path], root_agents_text: Optional[str]
) -> dict[str, Any]:
    guide_files_by_directory: dict[Path, list[Path]] = {}
    for path in files:
        guide_directory = guide_directory_for(project, path)
        if guide_directory is not None:
            guide_files_by_directory.setdefault(guide_directory, []).append(path)

    entries: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    markdown_files: list[Path] = []

    for guide_directory in sorted(
        guide_files_by_directory, key=lambda item: relative(project, item)
    ):
        scope_path = guide_directory.parent
        scope = relative(project, scope_path) or "."
        agents_path = scope_path / "AGENTS.md"
        scoped_files = sorted(
            guide_files_by_directory[guide_directory],
            key=lambda item: relative(project, item),
        )
        markdown_files.extend(
            path for path in scoped_files if path.suffix.lower() == ".md"
        )
        if not agents_path.is_file():
            issues.append(
                {
                    "kind": "unscoped_guide_directory",
                    "path": relative(project, guide_directory),
                    "scope": scope,
                }
            )

        for path in scoped_files:
            if path.parent == guide_directory and path.suffix.lower() != ".md":
                issues.append(
                    {
                        "kind": "unexpected_guide_file",
                        "path": relative(project, path),
                        "scope": scope,
                    }
                )

        direct_entries = {
            path.stem: path
            for path in scoped_files
            if path.parent == guide_directory and path.suffix.lower() == ".md"
        }
        package_directories = sorted(
            {
                path.relative_to(guide_directory).parts[0]
                for path in scoped_files
                if len(path.relative_to(guide_directory).parts) > 1
            }
        )

        for topic, path in sorted(direct_entries.items()):
            description, error = guide_description(path)
            entries.append(
                {
                    "scope": scope,
                    "path": relative(project, path),
                    "type": "single-file",
                    "description": description,
                    "metadata_valid": error is None,
                    "readable": error != "unreadable",
                }
            )
            if error:
                issues.append(
                    {"kind": error, "path": relative(project, path), "scope": scope}
                )
            if (guide_directory / topic / GUIDE_ENTRY_NAME).is_file():
                issues.append(
                    {
                        "kind": "duplicate_topic_entry",
                        "path": relative(project, path),
                        "other_path": relative(
                            project, guide_directory / topic / GUIDE_ENTRY_NAME
                        ),
                        "scope": scope,
                    }
                )

        for topic in package_directories:
            package_directory = guide_directory / topic
            entry_path = package_directory / GUIDE_ENTRY_NAME
            if not entry_path.is_file():
                issues.append(
                    {
                        "kind": "missing_guide_entry",
                        "path": relative(project, package_directory),
                        "scope": scope,
                    }
                )
                continue
            description, error = guide_description(entry_path)
            entries.append(
                {
                    "scope": scope,
                    "path": relative(project, entry_path),
                    "type": "package",
                    "description": description,
                    "metadata_valid": error is None,
                    "readable": error != "unreadable",
                }
            )
            if error:
                issues.append(
                    {
                        "kind": error,
                        "path": relative(project, entry_path),
                        "scope": scope,
                    }
                )

            references_directory = package_directory / "references"
            for path in scoped_files:
                if package_directory not in path.parents:
                    continue
                if path == entry_path:
                    continue
                if references_directory not in path.parents:
                    issues.append(
                        {
                            "kind": "unexpected_guide_file",
                            "path": relative(project, path),
                            "scope": scope,
                        }
                    )
                    continue
                relative_reference = path.relative_to(references_directory)
                if path.suffix.lower() != ".md":
                    issues.append(
                        {
                            "kind": "unexpected_guide_file",
                            "path": relative(project, path),
                            "scope": scope,
                        }
                    )
                if len(relative_reference.parts) > 1:
                    issues.append(
                        {
                            "kind": "nested_reference_directory",
                            "path": relative(project, path),
                            "scope": scope,
                        }
                    )
                if path.name == GUIDE_ENTRY_NAME:
                    issues.append(
                        {
                            "kind": "nested_guide_entry",
                            "path": relative(project, path),
                            "scope": scope,
                        }
                    )

    protocol_declared = bool(
        root_agents_text and GUIDE_DIRECTORY_NAME in root_agents_text
    )
    if guide_files_by_directory and not protocol_declared:
        issues.append(
            {
                "kind": "missing_guide_protocol",
                "path": "AGENTS.md",
                "scope": ".",
            }
        )

    references = link_records(project, markdown_files)
    for record in references:
        if not record["exists"]:
            issues.append(
                {
                    "kind": "broken_guide_link",
                    "path": record["source"],
                    "target": record["target"],
                }
            )
        if not record["inside_project"]:
            issues.append(
                {
                    "kind": "outside_project_guide_link",
                    "path": record["source"],
                    "target": record["target"],
                }
            )

    return {
        "guide_protocol_declared": protocol_declared,
        "guide_entries": entries,
        "guide_references": references,
        "guide_issues": issues,
    }


def inspect(project: Path) -> dict[str, Any]:
    files = list(iter_project_files(project))
    instructions = [path for path in files if path.name in INSTRUCTION_NAMES]
    manifests = [relative(project, path) for path in files if path.name in MANIFEST_NAMES]
    lockfiles = [relative(project, path) for path in files if path.name in LOCKFILE_NAMES]
    task_files = [relative(project, path) for path in files if path.name in TASK_FILE_NAMES]
    workspace_files = [
        relative(project, path) for path in files if path.name in WORKSPACE_FILE_NAMES
    ]
    doc_paths = [
        path
        for path in files
        if path.name in DOC_NAMES or ("docs" in path.relative_to(project).parts and path.suffix.lower() == ".md")
    ]
    docs = [relative(project, path) for path in doc_paths]
    packages = [package_scripts(project, path) for path in files if path.name == "package.json"]
    root_agents_text = read_text(project / "AGENTS.md")
    guides = guide_records(project, files, root_agents_text)
    return {
        "schema_version": SCHEMA_VERSION,
        "project_root": str(project),
        "git": git_record(project),
        "instruction_files": [instruction_record(project, path) for path in instructions],
        "manifests": manifests,
        "lockfiles": lockfiles,
        "task_files": task_files,
        "workspace_files": workspace_files,
        "subproject_candidates": subproject_records(project, files),
        "documentation": docs,
        "package_json": packages,
        "instruction_links": link_records(project, instructions),
        "instruction_path_references": instruction_path_records(project, instructions),
        "documentation_links": link_records(project, doc_paths),
        **guides,
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
