"""Independent Git/source-closure oracle for TASK-039E3-R1D2-AUDIT.

This oracle intentionally characterizes an implementation blocker instead of
repairing it: the declared 16-record freeze is byte-correct, but it omits
project modules that Python executes through the V3 runner's transitive import
closure.
"""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import subprocess
import unittest


MAIN = "11a5f04a0422049a099020f06c59ec23bc72d130"
BLOCKED_R1D = "66e15fcdae2e932bebf09b569fefbe6028443d79"
R1D2_A = "2653f2b7349a049f9ca4828d736dfea9462c4748"
R1D2_B = "3da8b7007b7dd78d934554b299e6cb264a0e6470"
SOURCE_MANIFEST_HASH = (
    "d9ea32af4ffb60af8bb6d0b7a496a74e4126d8e411e337da64ce64e15a152e48"
)

REPORTS_ONLY = {
    "docs/task_reports/TASK-039E3_R1D2_BLOCKER_CLOSURE.json",
    "docs/task_reports/TASK-039E3_R1D2_CORRECTED_AUTHORITY.json",
    "docs/task_reports/TASK-039E3_R1D2_DATA_ACCESS_AUDIT.json",
    "docs/task_reports/TASK-039E3_R1D2_IMPLEMENTATION_RECEIPT.json",
    "docs/task_reports/TASK-039E3_R1D2_RECOVERY_CONFIGURATION.json",
    "docs/task_reports/TASK-039E3_R1D2_REPORT.md",
    "docs/task_reports/TASK-039E3_R1D2_RESULT_CONTRACT.json",
    "docs/task_reports/TASK-039E3_R1D2_SOURCE_FREEZE.json",
    "docs/task_reports/TASK-039E3_R1D2_TEST_REPORT.json",
}


def _repository() -> Path:
    return Path(__file__).resolve().parents[1]


def _git_bytes(*arguments: str) -> bytes:
    return subprocess.run(
        ["git", *arguments],
        cwd=_repository(),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def _git_text(*arguments: str) -> str:
    return _git_bytes(*arguments).decode("utf-8").strip()


def _blob(commit: str, repository_path: str) -> bytes:
    return _git_bytes("show", f"{commit}:{repository_path}")


def _parent(commit: str) -> str:
    values = _git_text("rev-list", "--parents", "-n", "1", commit).split()
    if len(values) != 2:
        raise AssertionError(f"one parent required for {commit}: {values[1:]}")
    return values[1]


def _canonical_sha256(document: object) -> str:
    return hashlib.sha256(
        json.dumps(
            document,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _tracked_paths(commit: str) -> set[str]:
    return set(_git_text("ls-tree", "-r", "--name-only", commit).splitlines())


def _module_paths(module: str, tracked: set[str]) -> set[str]:
    """Resolve a project import plus every package initializer Python runs."""

    if not module.startswith("paperworks"):
        return set()
    parts = module.split(".")
    paths: set[str] = set()
    for index in range(1, len(parts)):
        initializer = f"src/{'/'.join(parts[:index])}/__init__.py"
        if initializer in tracked:
            paths.add(initializer)
    stem = f"src/{module.replace('.', '/')}"
    for candidate in (f"{stem}.py", f"{stem}/__init__.py"):
        if candidate in tracked:
            paths.add(candidate)
    return paths


def active_project_import_closure(commit: str) -> set[str]:
    """Recursively parse exact Git blobs, including import-time package code."""

    tracked = _tracked_paths(commit)
    pending = ["scripts/run_task039e3_recovery_execution_v3.py"]
    closure: set[str] = set()
    while pending:
        path = pending.pop()
        if path in closure:
            continue
        closure.add(path)
        tree = ast.parse(_blob(commit, path).decode("utf-8"), filename=path)
        for node in ast.walk(tree):
            modules: list[str] = []
            if isinstance(node, ast.Import):
                modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                modules.append(node.module)
                modules.extend(f"{node.module}.{alias.name}" for alias in node.names)
            for module in modules:
                pending.extend(_module_paths(module, tracked) - closure)
    return closure


class R1D2AuditGitSourceClosureTests(unittest.TestCase):
    def test_exact_lineage_main_and_reports_only_commit_b(self) -> None:
        self.assertEqual(_git_text("rev-parse", "main"), MAIN)
        self.assertEqual(_git_text("rev-parse", "origin/main"), MAIN)
        self.assertEqual(_parent(R1D2_A), BLOCKED_R1D)
        self.assertEqual(_parent(R1D2_B), R1D2_A)
        changes = _git_text(
            "diff", "--name-status", "--no-renames", R1D2_A, R1D2_B
        ).splitlines()
        self.assertEqual({line.split("\t", 1)[1] for line in changes}, REPORTS_ONLY)
        self.assertTrue(all(line.startswith("A\t") for line in changes))

    def test_declared_sixteen_raw_git_records_are_exact(self) -> None:
        path = "docs/task_reports/TASK-039E3_R1D2_SOURCE_FREEZE.json"
        manifest = json.loads(_blob(R1D2_B, path).decode("utf-8"))
        supplied = manifest.pop("artifact_hash")
        self.assertEqual(supplied, SOURCE_MANIFEST_HASH)
        self.assertEqual(_canonical_sha256(manifest), SOURCE_MANIFEST_HASH)
        self.assertEqual(manifest["described_commit"], R1D2_A)
        self.assertEqual(manifest["source_record_count"], 16)
        records = manifest["source_records"]
        self.assertEqual(len(records), 16)
        self.assertEqual(len({record["repository_path"] for record in records}), 16)
        for record in records:
            with self.subTest(path=record["repository_path"]):
                raw = _blob(R1D2_A, record["repository_path"])
                self.assertEqual(
                    _git_text("rev-parse", f"{R1D2_A}:{record['repository_path']}"),
                    record["git_blob_sha"],
                )
                self.assertEqual(hashlib.sha256(raw).hexdigest(), record["sha256"])
                self.assertEqual(_blob(R1D2_B, record["repository_path"]), raw)

    def test_transitive_material_closure_is_incomplete_blocking_characterization(self) -> None:
        manifest = json.loads(
            _blob(
                R1D2_B,
                "docs/task_reports/TASK-039E3_R1D2_SOURCE_FREEZE.json",
            ).decode("utf-8")
        )
        frozen = {record["repository_path"] for record in manifest["source_records"]}
        closure = active_project_import_closure(R1D2_A)

        # Every member is executed directly or at package-import time and is
        # therefore material to availability/behavior of the active runner.
        material = set(closure)
        bound = material & frozen
        unbound = material - frozen

        self.assertEqual(len(closure), 40)
        self.assertEqual(len(material), 40)
        self.assertEqual(len(bound), 15)
        self.assertEqual(len(unbound), 25)
        self.assertTrue(
            {
                "src/paperworks/v6/common.py",
                "src/paperworks/v6/task039e2_execution_configuration_v1.py",
                "src/paperworks/v6/task039e3_live_transport_v1.py",
                "src/paperworks/v6/task039e3_recovery_authorization_v1.py",
                "src/paperworks/v6/__init__.py",
                "src/paperworks/data/__init__.py",
            }.issubset(unbound)
        )
        self.assertFalse(not unbound, "active_source_freeze_complete must be false")


if __name__ == "__main__":
    unittest.main()
