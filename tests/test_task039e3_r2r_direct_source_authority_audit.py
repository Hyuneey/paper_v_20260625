from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
from typing import Any
import unittest


ROOT = Path(__file__).resolve().parents[1]
FORENSIC_B = "4712eeea87f0f60b51f4db9414fb589391c899d1"
REMEDIATION_A = "5dca2d0431d60ef2f2bdfc907ebfe3fe18521f16"
REMEDIATION_B = "d511372db560fd2cf27c2d56db7c637a3324584f"
MANIFEST_HASH = "9037fda0bc7694fd643058a9779fb919c75664824f2f11c49dde9f4be1b209b8"
MANIFEST_PATH = (
    "docs/task_reports/"
    "TASK-039E3_R2R_DIRECT_NUMBER_RENDERING_REMEDIATION_SOURCE_FREEZE.json"
)
ENTRYPOINT = "scripts/run_task039e3_r2r_scientific_execution_v1.py"
AUTHORIZATION_SCHEMA = (
    "schemas/v6/task039e3_r2r_execution_authorization_v1_schema.json"
)
EXPECTED_CHANGED_SOURCE = {
    "src/paperworks/v6/task039e2_execution_configuration_v1.py",
    "src/paperworks/v6/task039e3_r2r_execution_v1.py",
    "src/paperworks/v6/task039e3_r2r_failure_finalizer_v1.py",
    "src/paperworks/v6/task039e3_r2r_live_execution_v1.py",
    "src/paperworks/v6/task039e3_r2r_precontact_v1.py",
    "src/paperworks/v6/task039e3_r2r_result_finalizer_v1.py",
}


def _git_bytes(*arguments: str) -> bytes:
    return subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def _git_text(*arguments: str) -> str:
    return _git_bytes(*arguments).decode("utf-8").strip()


def _blob(commit: str, path: str) -> bytes:
    return _git_bytes("show", f"{commit}:{path}")


def _canonical_hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _load_self_hashed(commit: str, path: str) -> dict[str, Any]:
    document = json.loads(_blob(commit, path))
    supplied = document.pop("artifact_hash")
    if supplied != _canonical_hash(document):
        raise AssertionError(f"self-hash mismatch: {path}")
    return {"artifact_hash": supplied, **document}


def _tracked(commit: str) -> set[str]:
    return set(_git_text("ls-tree", "-r", "--name-only", commit).splitlines())


def _package_for(path: str) -> str:
    components = path.removeprefix("src/").removesuffix(".py").split("/")
    components.pop()
    return ".".join(components)


def _resolve_module(module: str, tracked: set[str]) -> set[str]:
    if not (module == "paperworks" or module.startswith("paperworks.")):
        return set()
    components = module.split(".")
    resolved: set[str] = set()
    for length in range(1, len(components)):
        initializer = f"src/{'/'.join(components[:length])}/__init__.py"
        if initializer in tracked:
            resolved.add(initializer)
    stem = f"src/{module.replace('.', '/')}"
    for candidate in (f"{stem}.py", f"{stem}/__init__.py"):
        if candidate in tracked:
            resolved.add(candidate)
    return resolved


def _independent_closure(commit: str) -> tuple[set[str], set[str], set[str]]:
    """Resolve the runner closure directly from raw Git blobs."""

    tracked = _tracked(commit)
    pending = [ENTRYPOINT]
    observed: set[str] = set()
    dynamic: set[str] = set()
    unresolved: set[str] = set()
    while pending:
        path = pending.pop()
        if path in observed:
            continue
        observed.add(path)
        tree = ast.parse(_blob(commit, path).decode("utf-8"), filename=path)
        for node in ast.walk(tree):
            modules: list[str] = []
            if isinstance(node, ast.Import):
                modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    relative = "." * node.level + (node.module or "")
                    module = importlib.util.resolve_name(relative, _package_for(path))
                else:
                    module = node.module or ""
                if module:
                    modules.append(module)
                    modules.extend(f"{module}.{item.name}" for item in node.names)
            for module in modules:
                pending.extend(_resolve_module(module, tracked) - observed)
            if isinstance(node, ast.Call):
                name = ""
                if isinstance(node.func, ast.Name):
                    name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    name = node.func.attr
                if name in {
                    "__import__",
                    "import_module",
                    "spec_from_file_location",
                    "SourceFileLoader",
                }:
                    marker = f"{path}:{getattr(node, 'lineno', 0)}:{name}"
                    dynamic.add(marker)
                    if not node.args or not isinstance(node.args[0], ast.Constant):
                        unresolved.add(marker)
    return observed, dynamic, unresolved


class DirectRenderingSourceAuthorityAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = _load_self_hashed(REMEDIATION_B, MANIFEST_PATH)

    def test_manifest_self_hash_topology_and_every_source_identity(self) -> None:
        self.assertEqual(self.manifest["artifact_hash"], MANIFEST_HASH)
        self.assertEqual(self.manifest["described_commit"], REMEDIATION_A)
        closure, dynamic, unresolved = _independent_closure(REMEDIATION_A)
        self.assertEqual(len(closure), 49)
        self.assertEqual(dynamic, set())
        self.assertEqual(unresolved, set())
        records = self.manifest["source_records"]
        self.assertEqual(len(records), 50)
        self.assertEqual(
            {item["repository_path"] for item in records},
            closure | {AUTHORIZATION_SCHEMA},
        )
        for record in records:
            with self.subTest(path=record["repository_path"]):
                path = record["repository_path"]
                raw = _blob(REMEDIATION_A, path)
                self.assertEqual(
                    _git_text("rev-parse", f"{REMEDIATION_A}:{path}"),
                    record["git_blob_sha"],
                )
                self.assertEqual(hashlib.sha256(raw).hexdigest(), record["sha256"])
                self.assertEqual((ROOT / path).read_bytes(), raw)
        self.assertEqual(self.manifest["unbound_material_project_local_dependency_count"], 0)
        self.assertEqual(self.manifest["dynamic_imports_found"], 0)
        self.assertEqual(self.manifest["unresolved_dynamic_imports"], 0)

    def test_exact_active_source_delta_is_exhaustively_classified(self) -> None:
        changed = set(
            _git_text(
                "diff",
                "--name-only",
                FORENSIC_B,
                REMEDIATION_A,
                "--",
                "src",
                "scripts",
                "schemas",
            ).splitlines()
        )
        self.assertEqual(changed, EXPECTED_CHANGED_SOURCE)
        rendering = "src/paperworks/v6/task039e2_execution_configuration_v1.py"
        self.assertIn("withheld_evidence_identities", _blob(REMEDIATION_A, rendering).decode())
        self.assertNotIn("withheld_evidence_identities", _blob(FORENSIC_B, rendering).decode())
        self.assertEqual(
            changed - {rendering},
            EXPECTED_CHANGED_SOURCE - {rendering},
        )
        self.assertEqual(
            _git_text("diff", "--name-only", REMEDIATION_A, REMEDIATION_B, "--", "src", "scripts", "schemas"),
            "",
        )

    def test_remediation_lineage_receipt_and_bundle_reproduce(self) -> None:
        test_report = _load_self_hashed(
            REMEDIATION_B,
            "docs/task_reports/"
            "TASK-039E3_R2R_DIRECT_NUMBER_RENDERING_REMEDIATION_TEST_REPORT.json",
        )
        receipt = _load_self_hashed(
            REMEDIATION_B,
            "docs/task_reports/"
            "TASK-039E3_R2R_DIRECT_NUMBER_RENDERING_REMEDIATION_RECEIPT.json",
        )
        report_sha = hashlib.sha256(
            _blob(
                REMEDIATION_B,
                "docs/task_reports/"
                "TASK-039E3_R2R_DIRECT_NUMBER_RENDERING_REMEDIATION_REPORT.md",
            )
        ).hexdigest()
        bundle = _canonical_hash(
            {
                "task_id": "TASK-039E3-R2R-DIRECT-NUMBER-RENDERING-REMEDIATION",
                "remediation_commit_a": REMEDIATION_A,
                "source_manifest_hash": self.manifest["artifact_hash"],
                "test_report_hash": test_report["artifact_hash"],
                "report_sha256": report_sha,
            }
        )
        self.assertEqual(bundle, "ed53460360705d17630b39749f5b39cfe4229f0a535f9814730681aa5d0fbf78")
        self.assertEqual(receipt["remediation_bundle_hash"], bundle)
        self.assertEqual(receipt["artifact_hash"], "721cbc3f51709293bf489a0622843e0f968957fcd24672756a0409e55ea7f43d")
        self.assertEqual(receipt["forensic_audit_commit_a"], "86da3bfd609a92540a781dfa7cd05f92c74692ec")
        self.assertEqual(receipt["forensic_audit_commit_b"], FORENSIC_B)
        self.assertEqual(receipt["failed_execution_receipt_hash"], "b68443208e7dca30aaad862610421d7c78cf40cc8c951b33ef4a55a9929c5393")


if __name__ == "__main__":
    unittest.main()
