"""Independent raw-Git and AST-closure oracle for TASK-039E3-R1C."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import unittest


MAIN = "11a5f04a0422049a099020f06c59ec23bc72d130"
R1B_AUDIT_B = "1747ece15cac693b2ec84c7f780bd1a817a78469"
R1C_A = "42f51cba0168f8050803139ec3333156ed2fa403"
R1C_B = "a1a802eb814937e2f024b6caa429943690bc6976"
SOURCE_MANIFEST_HASH = (
    "e494c727d03b75cbec7123c7bb92da61ead345673f678078d32a217dfe6350d0"
)

REPORTS_ONLY = {
    "docs/task_reports/TASK-039E3_R1C_BLOCKER_CLOSURE.json",
    "docs/task_reports/TASK-039E3_R1C_DATA_ACCESS_AUDIT.json",
    "docs/task_reports/TASK-039E3_R1C_IMPLEMENTATION_RECEIPT.json",
    "docs/task_reports/TASK-039E3_R1C_RECOVERY_CONFIGURATION.json",
    "docs/task_reports/TASK-039E3_R1C_REMEDIATION_AUTHORITY.json",
    "docs/task_reports/TASK-039E3_R1C_REPORT.md",
    "docs/task_reports/TASK-039E3_R1C_SOURCE_FREEZE.json",
    "docs/task_reports/TASK-039E3_R1C_TEST_REPORT.json",
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
        raise AssertionError(f"expected one parent for {commit}: {values[1:]}")
    return values[1]


def _canonical_sha256(document: object) -> str:
    encoded = json.dumps(
        document,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _module_path(module: str) -> str | None:
    prefix = "paperworks.v6."
    if not module.startswith(prefix):
        return None
    suffix = module.removeprefix(prefix).replace(".", "/")
    return f"src/paperworks/v6/{suffix}.py"


def _active_import_closure(commit: str) -> tuple[set[str], set[str]]:
    """Build the repository-local import closure from raw Commit-A blobs."""

    entry = "scripts/run_task039e3_recovery_execution_v2.py"
    queued = [entry]
    paths: set[str] = set()
    imported_names: set[str] = set()
    while queued:
        path = queued.pop()
        if path in paths:
            continue
        source = _blob(commit, path).decode("utf-8")
        paths.add(path)
        tree = ast.parse(source, filename=f"{commit}:{path}")
        for node in ast.walk(tree):
            module: str | None = None
            if isinstance(node, ast.Import):
                for alias in node.names:
                    candidate = _module_path(alias.name)
                    if candidate is not None and candidate not in paths:
                        queued.append(candidate)
                    imported_names.add(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                module = node.module
                if module is not None:
                    candidate = _module_path(module)
                    if candidate is not None and candidate not in paths:
                        queued.append(candidate)
                for alias in node.names:
                    imported_names.add(alias.name)
    return paths, imported_names


def _literal_dictionary_keys(source: str) -> set[str]:
    keys: set[str] = set()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        for key in node.keys:
            if isinstance(key, ast.Constant) and isinstance(key.value, str):
                keys.add(key.value)
    return keys


class R1CGitAndActiveClosureAuditTests(unittest.TestCase):
    def test_exact_lineage_and_reports_only_commit_b(self) -> None:
        self.assertEqual(_git_text("rev-parse", "origin/main"), MAIN)
        self.assertEqual(_parent(R1C_A), R1B_AUDIT_B)
        self.assertEqual(_parent(R1C_B), R1C_A)
        changed_lines = _git_text(
            "diff", "--name-status", "--no-renames", R1C_A, R1C_B
        ).splitlines()
        self.assertEqual(
            {line.split("\t", 1)[1] for line in changed_lines}, REPORTS_ONLY
        )
        self.assertTrue(all(line.startswith("A\t") for line in changed_lines))

    def test_fourteen_raw_git_records_and_commit_b_identity(self) -> None:
        manifest_path = "docs/task_reports/TASK-039E3_R1C_SOURCE_FREEZE.json"
        manifest = json.loads(_blob(R1C_B, manifest_path).decode("utf-8"))
        supplied_hash = manifest.pop("artifact_hash")
        self.assertEqual(supplied_hash, SOURCE_MANIFEST_HASH)
        self.assertEqual(_canonical_sha256(manifest), SOURCE_MANIFEST_HASH)
        manifest["artifact_hash"] = supplied_hash
        self.assertEqual(manifest["described_commit"], R1C_A)
        self.assertEqual(manifest["source_record_count"], 14)
        records = manifest["source_records"]
        self.assertIsInstance(records, list)
        self.assertEqual(len(records), 14)
        paths: set[str] = set()
        for record in records:
            path = record["repository_path"]
            self.assertNotIn(path, paths)
            paths.add(path)
            raw = _blob(R1C_A, path)
            self.assertEqual(
                _git_text("rev-parse", f"{R1C_A}:{path}"),
                record["git_blob_sha"],
            )
            self.assertEqual(hashlib.sha256(raw).hexdigest(), record["sha256"])
            self.assertEqual(
                _git_text("rev-parse", f"{R1C_B}:{path}"),
                record["git_blob_sha"],
            )
            self.assertEqual(_blob(R1C_B, path), raw)

    def test_ast_import_closure_excludes_compatibility_execution(self) -> None:
        closure, imported_names = _active_import_closure(R1C_A)
        self.assertIn(
            "src/paperworks/v6/task039e3_recovery_execution_v2.py", closure
        )
        self.assertIn(
            "src/paperworks/v6/task039e3_recovery_science_v2.py", closure
        )
        self.assertNotIn(
            "src/paperworks/v6/task039e3_recovery_execution_v1.py", closure
        )
        self.assertNotIn("RecoveryScientificCompatibilityTransportV1", imported_names)

        # Independently inspect executable V2 dictionaries: the active V2
        # coordinator and runner never synthesize the legacy self-report fields.
        v2_paths = {
            "scripts/run_task039e3_recovery_execution_v2.py",
            "src/paperworks/v6/task039e3_recovery_execution_v2.py",
            "src/paperworks/v6/task039e3_recovery_science_v2.py",
        }
        legacy_keys = {"model_snapshot", "structured_output_supported"}
        for path in v2_paths:
            with self.subTest(path=path):
                source = _blob(R1C_A, path).decode("utf-8")
                self.assertTrue(legacy_keys.isdisjoint(_literal_dictionary_keys(source)))
                parsed = ast.parse(source)
                called_names = {
                    node.func.id
                    for node in ast.walk(parsed)
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                }
                self.assertNotIn(
                    "RecoveryScientificCompatibilityTransportV1", called_names
                )


if __name__ == "__main__":
    unittest.main()
