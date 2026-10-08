"""Check invocation routing without running OpenRewrite or modifying a real app."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / "scripts/migrate.sh"
DEFAULT_VERSION = (SKILL / "references/recipe-version").read_text().strip()
RECIPES = {
    "axon": "org.axonframework.migration.UpgradeAxon4ToAxon5",
    "axoniq": "io.axoniq.framework.migration.UpgradeAxon4ToAxoniq5",
}
MOCK = """#!/bin/sh
printf '%s\\n' "$0" "$@" > "$COMMAND_LOG"
exit "${MOCK_EXIT:-0}"
"""


class MigrateInvocationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="axon-rewrite-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project = self.root / "project with spaces"
        self.project.mkdir()
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.log = self.root / "arguments"
        self.env = {
            **os.environ,
            "PATH": str(self.bin) + ":/usr/bin:/bin",
            "COMMAND_LOG": str(self.log),
            "MOCK_EXIT": "0",
        }
        for name in ("mvn", "gradle"):
            self.mock(self.bin / name)

    def mock(self, path):
        path.write_text(MOCK)
        path.chmod(0o755)

    def run_script(self, *args):
        return subprocess.run(
            ["/bin/bash", str(SCRIPT), *args],
            cwd=self.project,
            env=self.env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_default_and_override_reach_each_build_route(self):
        for build_file, wrapper in (
            ("pom.xml", False),
            ("build.gradle", False),
            ("build.gradle.kts", False),
            ("build.gradle", True),
            ("build.gradle.kts", True),
        ):
            for framework in RECIPES:
                for override in (None, "5.4.0"):
                    with self.subTest(build=build_file, wrapper=wrapper,
                                      framework=framework, override=override):
                        for old in self.project.iterdir():
                            old.unlink()
                        (self.project / build_file).touch()
                        if wrapper:
                            self.mock(self.project / "gradlew")
                        args = [framework] + ([override] if override else [])
                        result = self.run_script(*args)
                        self.assertEqual(0, result.returncode, result.stderr)
                        recorded = self.log.read_text().splitlines()
                        version = override or DEFAULT_VERSION
                        recipe = RECIPES[framework]
                        if build_file == "pom.xml":
                            self.assertEqual("mvn", Path(recorded[0]).name)
                            self.assertEqual([
                                "-U",
                                "org.openrewrite.maven:rewrite-maven-plugin:6.46.1:run",
                                "-Drewrite.recipeArtifactCoordinates="
                                f"org.axonframework:axon-migration:{version}",
                                f"-Drewrite.activeRecipes={recipe}",
                            ], recorded[1:])
                        else:
                            self.assertEqual("gradlew" if wrapper else "gradle",
                                             Path(recorded[0]).name)
                            self.assertEqual([
                                "rewriteRun", "--init-script",
                                str(SKILL / "assets/init.gradle"),
                                f"-Drewrite.activeRecipe={recipe}",
                                f"-Drewrite.axonMigrationVersion={version}",
                            ], recorded[1:])
                        self.assertIn(f"axon-migration:{version}", result.stderr)
                        expected_files = {build_file} | ({"gradlew"} if wrapper else set())
                        self.assertEqual(expected_files,
                                         {p.name for p in self.project.iterdir()})
        self.assertEqual(DEFAULT_VERSION,
                         (SKILL / "references/recipe-version").read_text().strip())

    def test_no_arguments_keep_existing_default(self):
        (self.project / "pom.xml").touch()
        result = self.run_script()
        self.assertEqual(0, result.returncode, result.stderr)
        args = self.log.read_text()
        self.assertIn(f"axon-migration:{DEFAULT_VERSION}", args)
        self.assertIn(RECIPES["axoniq"], args)

    def test_invalid_versions_never_invoke_build(self):
        (self.project / "pom.xml").touch()
        for version in ("", " 5.4.0", "5.4.0 extra", "-Dother=true", "../5.4.0",
                        "5.4.0;touch injected", "5.4.0\nextra", "${VERSION}",
                        "5.4.0:other", "5.4.0$(touch injected)"):
            with self.subTest(version=version):
                result = self.run_script("axoniq", version)
                self.assertEqual(2, result.returncode)
                self.assertIn("recipe version must", result.stderr)
                self.assertFalse(self.log.exists())
                self.assertEqual({"pom.xml"}, {p.name for p in self.project.iterdir()})

    def test_extra_arguments_are_rejected(self):
        (self.project / "pom.xml").touch()
        result = self.run_script("axoniq", "5.4.0", "--extra")
        self.assertEqual(2, result.returncode)
        self.assertFalse(self.log.exists())

    def test_build_failure_preserves_exit_and_reports_resolved_version(self):
        (self.project / "pom.xml").touch()
        self.env["MOCK_EXIT"] = "17"
        result = self.run_script("axoniq", "5.4.0")
        self.assertEqual(17, result.returncode)
        self.assertIn("axon-migration:5.4.0", result.stderr)


if __name__ == "__main__":
    unittest.main()
