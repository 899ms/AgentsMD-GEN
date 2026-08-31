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
            self.assertEqual(data["schema_version"], "1.2")
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

    def test_collects_scoped_single_file_and_package_guides(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            project = Path(raw)
            package = project / "packages" / "api"
            root_guides = project / ".agent-guides"
            local_guide = package / ".agent-guides" / "testing"
            references = local_guide / "references"
            root_guides.mkdir()
            references.mkdir(parents=True)
            (project / "AGENTS.md").write_text(
                "# Project\n\nDiscover `.agent-guides/` for every applicable "
                "AGENTS.md scope.\n",
                encoding="utf-8",
            )
            (package / "AGENTS.md").write_text("# API\n", encoding="utf-8")
            (root_guides / "security.md").write_text(
                "---\ndescription: Use when changing authentication or sensitive data.\n"
                "---\n\n# Security\n",
                encoding="utf-8",
            )
            (local_guide / "GUIDE.md").write_text(
                "---\ndescription: Use when adding or changing API tests.\n---\n\n"
                "# Testing\n\nFor unit tests, read "
                "[unit testing](references/unit-tests.md).\n",
                encoding="utf-8",
            )
            (references / "unit-tests.md").write_text(
                "# Unit testing\n", encoding="utf-8"
            )

            completed = self.run_cli(project)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            data = json.loads(completed.stdout)
            self.assertTrue(data["guide_protocol_declared"])
            entries = {item["path"]: item for item in data["guide_entries"]}
            self.assertEqual(entries[".agent-guides/security.md"]["scope"], ".")
            self.assertEqual(
                entries[".agent-guides/security.md"]["type"], "single-file"
            )
            self.assertEqual(
                entries["packages/api/.agent-guides/testing/GUIDE.md"]["scope"],
                "packages/api",
            )
            self.assertEqual(
                entries["packages/api/.agent-guides/testing/GUIDE.md"]["type"],
                "package",
            )
            self.assertEqual(
                entries["packages/api/.agent-guides/testing/GUIDE.md"]["description"],
                "Use when adding or changing API tests.",
            )
            self.assertEqual(data["guide_issues"], [])
            self.assertEqual(
                data["guide_references"][0]["target"], "references/unit-tests.md"
            )
            self.assertTrue(data["guide_references"][0]["exists"])

    def test_reports_invalid_unscoped_and_broken_guides(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            project = Path(raw)
            guide = project / "module" / ".agent-guides" / "testing"
            guide.mkdir(parents=True)
            (project / "AGENTS.md").write_text("# Project\n", encoding="utf-8")
            (guide / "GUIDE.md").write_text(
                "# Testing\n\nSee [missing](references/missing.md).\n",
                encoding="utf-8",
            )

            completed = self.run_cli(project)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            data = json.loads(completed.stdout)
            issue_kinds = {item["kind"] for item in data["guide_issues"]}
            self.assertIn("missing_guide_protocol", issue_kinds)
            self.assertIn("unscoped_guide_directory", issue_kinds)
            self.assertIn("missing_frontmatter", issue_kinds)
            self.assertIn("broken_guide_link", issue_kinds)

    def test_discovers_renamed_guide_without_an_index(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            project = Path(raw)
            guides = project / ".agent-guides"
            guides.mkdir()
            root = project / "AGENTS.md"
            root.write_text(
                "# Project\n\nDiscover `.agent-guides/` dynamically.\n",
                encoding="utf-8",
            )
            original = guides / "tests.md"
            original.write_text(
                "---\ndescription: Use when changing tests.\n---\n",
                encoding="utf-8",
            )
            before = root.read_bytes()
            original.rename(guides / "verification.md")

            completed = self.run_cli(project)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            data = json.loads(completed.stdout)
            self.assertEqual(root.read_bytes(), before)
            self.assertEqual(
                [item["path"] for item in data["guide_entries"]],
                [".agent-guides/verification.md"],
            )

    def test_reports_nested_references_and_unexpected_package_files(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            project = Path(raw)
            guide = project / ".agent-guides" / "testing"
            nested = guide / "references" / "unit"
            nested.mkdir(parents=True)
            (project / "AGENTS.md").write_text(
                "# Project\n\nDiscover `.agent-guides/` dynamically.\n",
                encoding="utf-8",
            )
            (guide / "GUIDE.md").write_text(
                "---\ndescription: Use when changing tests.\n---\n",
                encoding="utf-8",
            )
            (guide / "notes.md").write_text("# Notes\n", encoding="utf-8")
            (guide / "references" / "fixture.bin").write_bytes(b"fixture")
            (nested / "details.md").write_text("# Details\n", encoding="utf-8")

            completed = self.run_cli(project)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            data = json.loads(completed.stdout)
            issue_kinds = {item["kind"] for item in data["guide_issues"]}
            self.assertIn("unexpected_guide_file", issue_kinds)
            self.assertIn("nested_reference_directory", issue_kinds)

    def test_reports_root_size_as_a_review_signal(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            project = Path(raw)
            (project / "AGENTS.md").write_text(
                "\n".join(f"Rule {index}" for index in range(51)), encoding="utf-8"
            )

            completed = self.run_cli(project)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            data = json.loads(completed.stdout)
            root = data["instruction_files"][0]
            self.assertEqual(root["line_count"], 51)
            self.assertTrue(root["review_size"])

    def test_validates_supported_guide_description_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            project = Path(raw)
            guides = project / ".agent-guides"
            guides.mkdir()
            (project / "AGENTS.md").write_text(
                "# Project\n\nDiscover `.agent-guides/` dynamically.\n",
                encoding="utf-8",
            )
            (guides / "quoted.md").write_text(
                "---\ndescription: 'Use when preparing releases.'\n---\n",
                encoding="utf-8",
            )
            (guides / "empty.md").write_text(
                "---\ndescription:\n---\n", encoding="utf-8"
            )
            (guides / "multiline.md").write_text(
                "---\ndescription: |\n  Use when testing.\n---\n", encoding="utf-8"
            )
            (guides / "duplicate.md").write_text(
                "---\ndescription: First.\ndescription: Second.\n---\n",
                encoding="utf-8",
            )
            (guides / "unterminated.md").write_text(
                "---\ndescription: Use when documenting.\n", encoding="utf-8"
            )

            completed = self.run_cli(project)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            data = json.loads(completed.stdout)
            entries = {item["path"]: item for item in data["guide_entries"]}
            self.assertEqual(
                entries[".agent-guides/quoted.md"]["description"],
                "Use when preparing releases.",
            )
            issue_kinds = {item["kind"] for item in data["guide_issues"]}
            self.assertIn("empty_description", issue_kinds)
            self.assertIn("multiline_description", issue_kinds)
            self.assertIn("duplicate_description", issue_kinds)
            self.assertIn("unterminated_frontmatter", issue_kinds)

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
