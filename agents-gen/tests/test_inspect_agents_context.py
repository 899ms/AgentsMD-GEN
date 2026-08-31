from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "inspect_agents_context.py"
SPEC = importlib.util.spec_from_file_location("inspect_agents_context", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class InspectAgentsContextTests(unittest.TestCase):
    def run_cli(self, project: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(project)],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_empty_project_has_no_invented_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            project = Path(raw)
            completed = self.run_cli(project)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            data = json.loads(completed.stdout)
            self.assertEqual(data["manifests"], [])
            self.assertEqual(data["lockfiles"], [])
            self.assertEqual(data["instruction_files"], [])
            self.assertFalse(data["git"]["present"])

    def test_collects_scoped_instructions_scripts_and_links(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            project = Path(raw)
            (project / "packages" / "api").mkdir(parents=True)
            (project / "src" / "auth").mkdir(parents=True)
            (project / "docs").mkdir()
            (project / "docs" / "TESTING.md").write_text("# Testing\n", encoding="utf-8")
            (project / "docs" / "TYPESCRIPT.md").write_text(
                "# TypeScript\n\nSee [testing](TESTING.md).\n", encoding="utf-8"
            )
            (project / "src" / "auth" / "handlers.ts").write_text(
                "export {};\n", encoding="utf-8"
            )
            (project / "AGENTS.md").write_text(
                "# Project\n\nSee [TypeScript](docs/TYPESCRIPT.md) and "
                "[missing](docs/MISSING.md). Authentication currently lives at "
                "`src/auth/handlers.ts`.\n",
                encoding="utf-8",
            )
            (project / "packages" / "api" / "AGENTS.md").write_text(
                "# API\n", encoding="utf-8"
            )
            (project / "CLAUDE.md").write_text("# Claude\n", encoding="utf-8")
            (project / "package.json").write_text(
                json.dumps(
                    {
                        "name": "example-workspace",
                        "private": True,
                        "packageManager": "pnpm@10.0.0",
                        "workspaces": ["packages/*"],
                        "scripts": {"test": "node --test", "typecheck": "tsc --noEmit"},
                    }
                ),
                encoding="utf-8",
            )
            (project / "packages" / "api" / "package.json").write_text(
                json.dumps({"name": "@example/api", "scripts": {"test": "node --test"}}),
                encoding="utf-8",
            )
            (project / "pnpm-workspace.yaml").write_text(
                "packages:\n  - packages/*\n", encoding="utf-8"
            )

            completed = self.run_cli(project)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            data = json.loads(completed.stdout)
            self.assertEqual(data["schema_version"], "1.1")
            by_path = {item["path"]: item for item in data["instruction_files"]}
            self.assertEqual(by_path["AGENTS.md"]["scope"], ".")
            self.assertEqual(by_path["packages/api/AGENTS.md"]["scope"], "packages/api")
            self.assertIn("CLAUDE.md", by_path)
            packages = {item["path"]: item for item in data["package_json"]}
            self.assertEqual(packages["package.json"]["name"], "example-workspace")
            self.assertEqual(packages["package.json"]["package_manager"], "pnpm@10.0.0")
            self.assertEqual(packages["package.json"]["workspaces"], ["packages/*"])
            self.assertEqual(packages["package.json"]["scripts"]["test"], "node --test")
            self.assertEqual(data["workspace_files"], ["pnpm-workspace.yaml"])
            self.assertEqual(
                data["subproject_candidates"],
                [
                    {
                        "scope": "packages/api",
                        "evidence": ["packages/api/package.json"],
                        "agents_path": "packages/api/AGENTS.md",
                        "agents_exists": True,
                    }
                ],
            )
            links = {item["target"]: item for item in data["instruction_links"]}
            self.assertTrue(links["docs/TYPESCRIPT.md"]["exists"])
            self.assertFalse(links["docs/MISSING.md"]["exists"])
            path_references = {
                (item["target"], item["kind"]): item
                for item in data["instruction_path_references"]
            }
            self.assertTrue(
                path_references[("src/auth/handlers.ts", "inline_code")]["exists"]
            )
            documentation_links = {
                (item["source"], item["target"]): item
                for item in data["documentation_links"]
            }
            self.assertTrue(
                documentation_links[("docs/TYPESCRIPT.md", "TESTING.md")]["exists"]
            )

    def test_ordinary_directories_and_weak_dependency_files_are_not_subprojects(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            project = Path(raw)
            (project / "src").mkdir()
            (project / "tests").mkdir()
            (project / "examples").mkdir()
            (project / "src" / "module.py").write_text("", encoding="utf-8")
            (project / "tests" / "test_module.py").write_text("", encoding="utf-8")
            (project / "examples" / "requirements.txt").write_text(
                "example-package\n", encoding="utf-8"
            )

            completed = self.run_cli(project)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            data = json.loads(completed.stdout)
            self.assertEqual(data["subproject_candidates"], [])

    def test_skill_manifest_marks_an_independent_skill_subproject(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            project = Path(raw)
            skill = project / "skills" / "example"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: example\ndescription: Example skill.\n---\n",
                encoding="utf-8",
            )

            completed = self.run_cli(project)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            data = json.loads(completed.stdout)
            self.assertEqual(
                data["subproject_candidates"],
                [
                    {
                        "scope": "skills/example",
                        "evidence": ["skills/example/SKILL.md"],
                        "agents_path": "skills/example/AGENTS.md",
                        "agents_exists": False,
                    }
                ],
            )

    def test_reports_project_git_changes_without_inheriting_an_ancestor(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            project = Path(raw) / "project"
            project.mkdir()
            subprocess.run(["git", "init", "-q", "-b", "main", str(project)], check=True)
            (project / "new.txt").write_text("new\n", encoding="utf-8")

            completed = self.run_cli(project)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            data = json.loads(completed.stdout)
            self.assertEqual(data["git"]["scope"], "project")
            self.assertIn("new.txt", {item["path"] for item in data["git"]["changes"]})

    def test_does_not_inherit_an_ancestor_git_repository(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            parent = Path(raw)
            subprocess.run(["git", "init", "-q", "-b", "main", str(parent)], check=True)
            project = parent / "opened-project"
            project.mkdir()
            (project / "README.md").write_text("# Opened project\n", encoding="utf-8")

            completed = self.run_cli(project)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            data = json.loads(completed.stdout)
            self.assertFalse(data["git"]["present"])
            self.assertEqual(data["git"]["scope"], "none")

    def test_rejects_relative_project_path(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "."],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("must be absolute", completed.stderr)

    def test_inspection_does_not_modify_source_files(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            project = Path(raw)
            source = project / "AGENTS.md"
            source.write_text("# Stable\n", encoding="utf-8")
            before = source.read_bytes()

            completed = self.run_cli(project)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(source.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
