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
            (project / "docs").mkdir()
            (project / "docs" / "TESTING.md").write_text("# Testing\n", encoding="utf-8")
            (project / "AGENTS.md").write_text(
                "# Project\n\nSee [testing](docs/TESTING.md) and [missing](docs/MISSING.md).\n",
                encoding="utf-8",
            )
            (project / "packages" / "api" / "AGENTS.md").write_text(
                "# API\n", encoding="utf-8"
            )
            (project / "CLAUDE.md").write_text("# Claude\n", encoding="utf-8")
            (project / "package.json").write_text(
                json.dumps(
                    {
                        "packageManager": "pnpm@10.0.0",
                        "scripts": {"test": "node --test", "typecheck": "tsc --noEmit"},
                    }
                ),
                encoding="utf-8",
            )

            completed = self.run_cli(project)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            data = json.loads(completed.stdout)
            by_path = {item["path"]: item for item in data["instruction_files"]}
            self.assertEqual(by_path["AGENTS.md"]["scope"], ".")
            self.assertEqual(by_path["packages/api/AGENTS.md"]["scope"], "packages/api")
            self.assertIn("CLAUDE.md", by_path)
            self.assertEqual(data["package_json"][0]["package_manager"], "pnpm@10.0.0")
            self.assertEqual(data["package_json"][0]["scripts"]["test"], "node --test")
            links = {item["target"]: item for item in data["instruction_links"]}
            self.assertTrue(links["docs/TESTING.md"]["exists"])
            self.assertFalse(links["docs/MISSING.md"]["exists"])

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
