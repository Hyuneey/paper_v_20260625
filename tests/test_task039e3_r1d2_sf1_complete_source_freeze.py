"""Independent offline oracle for the SF1 complete active-source freeze."""

from __future__ import annotations

import ast
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from paperworks.v6 import task039e3_recovery_authorization_v3 as authority
from paperworks.v6 import task039e3_recovery_integrity_v3 as integrity
from paperworks.v6.task039e3_recovery_execution_v3 import (
    collect_git_execution_state_v3,
)
from tests import test_task039e3_r1d2_authorization_chain_v3 as auth_fixture


R1D2_A = "2653f2b7349a049f9ca4828d736dfea9462c4748"
R1D2_B = "3da8b7007b7dd78d934554b299e6cb264a0e6470"
BLOCKED_AUDIT_B = "460cc11a038ba2fd5604a4b2b0b57616b70c97cc"
BLOCKED_AUDIT_BUNDLE = (
    "0a7e48afb8ea99600deae9d90e29d9d4d1c02e7d568dac8748759538631b5d9b"
)
BLOCKED_AUDIT_RECEIPT = (
    "523368de774b289823206ddf976a8a9e164c3c397427f68c19fb7b952a3db8db"
)
BLOCKED_SOURCE_CLOSURE = (
    "3579a22005ea590aad31a13b9ace62431d552b9430082dd2ecceda2526ed6cdc"
)
HISTORICAL_MANIFEST = (
    "d9ea32af4ffb60af8bb6d0b7a496a74e4126d8e411e337da64ce64e15a152e48"
)
MANIFEST_PATH = (
    "docs/task_reports/TASK-039E3_R1D2_SF1_COMPLETE_SOURCE_FREEZE.json"
)
ENTRYPOINT = "scripts/run_task039e3_recovery_execution_v3.py"

PREVIOUSLY_UNBOUND = {
    "src/paperworks/__init__.py",
    "src/paperworks/data/__init__.py",
    "src/paperworks/data/contracts.py",
    "src/paperworks/data/contracts_v2.py",
    "src/paperworks/data/files.py",
    "src/paperworks/data/official_swat.py",
    "src/paperworks/data/splits.py",
    "src/paperworks/data/splits_v2.py",
    "src/paperworks/data/staging_swat.py",
    "src/paperworks/metadata/__init__.py",
    "src/paperworks/metadata/schema.py",
    "src/paperworks/v6/__init__.py",
    "src/paperworks/v6/adapters_v1.py",
    "src/paperworks/v6/candidate_discovery_protocol_v1.py",
    "src/paperworks/v6/common.py",
    "src/paperworks/v6/continuous_step_protocol_v1.py",
    "src/paperworks/v6/detector_context_v1.py",
    "src/paperworks/v6/normal_evidence_v1.py",
    "src/paperworks/v6/outcomes_v1.py",
    "src/paperworks/v6/schema_registry_v1.py",
    "src/paperworks/v6/task039e0_rule_construction_prep_v1.py",
    "src/paperworks/v6/task039e0_validity_v1.py",
    "src/paperworks/v6/task039e2_execution_configuration_v1.py",
    "src/paperworks/v6/task039e3_live_transport_v1.py",
    "src/paperworks/v6/task039e3_recovery_authorization_v1.py",
}


def _repository() -> Path:
    return Path(__file__).resolve().parents[1]


def _git_bytes(*arguments: str, repository: Path | None = None) -> bytes:
    return subprocess.run(
        ["git", *arguments],
        cwd=repository or _repository(),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def _git_text(*arguments: str, repository: Path | None = None) -> str:
    return _git_bytes(*arguments, repository=repository).decode("utf-8").strip()


def _blob(path: str) -> bytes:
    return _git_bytes("show", f"{R1D2_A}:{path}")


def _canonical_hash(document: object) -> str:
    return hashlib.sha256(
        json.dumps(
            document,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _self_hashed_git_document(commit: str, path: str) -> dict[str, object]:
    document = json.loads(_git_bytes("show", f"{commit}:{path}"))
    supplied = str(document.pop("artifact_hash"))
    if supplied != _canonical_hash(document):
        raise AssertionError(f"self-hash mismatch: {path}")
    return {"artifact_hash": supplied, **document}


def _module_paths(module: str, tracked: set[str]) -> set[str]:
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


def _active_closure() -> tuple[set[str], set[str]]:
    tracked = set(_git_text("ls-tree", "-r", "--name-only", R1D2_A).splitlines())
    pending = [ENTRYPOINT]
    closure: set[str] = set()
    dynamic_calls: set[str] = set()
    dynamic_names = {
        "__import__",
        "importlib.import_module",
        "importlib.util.spec_from_file_location",
        "importlib.machinery.SourceFileLoader",
    }
    while pending:
        path = pending.pop()
        if path in closure:
            continue
        closure.add(path)
        tree = ast.parse(_blob(path).decode("utf-8"), filename=path)
        for node in ast.walk(tree):
            modules: list[str] = []
            if isinstance(node, ast.Import):
                modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                modules.append(node.module)
                modules.extend(f"{node.module}.{alias.name}" for alias in node.names)
            for module in modules:
                pending.extend(_module_paths(module, tracked) - closure)
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    call_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    parts: list[str] = []
                    item: ast.expr = node.func
                    while isinstance(item, ast.Attribute):
                        parts.append(item.attr)
                        item = item.value
                    if isinstance(item, ast.Name):
                        parts.append(item.id)
                    call_name = ".".join(reversed(parts))
                else:
                    call_name = ""
                if call_name in dynamic_names:
                    dynamic_calls.add(f"{path}:{call_name}")
    return closure, dynamic_calls


def _manifest() -> dict[str, object]:
    return json.loads((_repository() / MANIFEST_PATH).read_text(encoding="utf-8"))


def _integrity_state(manifest: dict[str, object]) -> integrity.ObservedExecutionIntegrityStateV3:
    records = manifest["source_records"]
    assert isinstance(records, list)
    blobs = tuple(
        integrity.FrozenSourceBlobV3(
            repository_path=str(record["repository_path"]),
            git_blob_sha=str(record["git_blob_sha"]),
            sha256=str(record["sha256"]),
        )
        for record in records
        if str(record["repository_path"]).endswith(".py")
    )
    return integrity.build_frozen_execution_integrity_state_v3(
        head_commit=R1D2_A,
        source_manifest_hash=str(manifest["artifact_hash"]),
        source_blobs=blobs,
        scientific_accounting_behavior_hash="b" * 64,
        r2_authorization_hash="c" * 64,
    )


class CompleteActiveSourceFreezeTests(unittest.TestCase):
    def test_blocked_audit_authority_and_historical_artifacts_are_immutable(self) -> None:
        receipt = _self_hashed_git_document(
            BLOCKED_AUDIT_B,
            "docs/task_reports/TASK-039E3_R1D2_AUDIT_RECEIPT.json",
        )
        closure = _self_hashed_git_document(
            BLOCKED_AUDIT_B,
            "docs/task_reports/TASK-039E3_R1D2_AUDIT_SOURCE_CLOSURE.json",
        )
        self.assertEqual(receipt["artifact_hash"], BLOCKED_AUDIT_RECEIPT)
        self.assertEqual(receipt["audit_bundle_hash"], BLOCKED_AUDIT_BUNDLE)
        self.assertEqual(
            receipt["status"], "blocked_task039e3_r1d2_independent_audit"
        )
        self.assertEqual(closure["artifact_hash"], BLOCKED_SOURCE_CLOSURE)
        old = _self_hashed_git_document(
            R1D2_B, "docs/task_reports/TASK-039E3_R1D2_SOURCE_FREEZE.json"
        )
        self.assertEqual(old["artifact_hash"], HISTORICAL_MANIFEST)
        self.assertEqual(old["source_record_count"], 16)

    def test_complete_closure_and_all_raw_git_records_reconstruct(self) -> None:
        manifest = _manifest()
        supplied = str(manifest.pop("artifact_hash"))
        self.assertEqual(supplied, _canonical_hash(manifest))
        self.assertEqual(manifest["described_execution_commit"], R1D2_A)
        self.assertEqual(manifest["source_record_count"], 41)
        records = manifest["source_records"]
        assert isinstance(records, list)
        paths = [str(record["repository_path"]) for record in records]
        self.assertEqual(paths, sorted(paths))
        self.assertEqual(len(paths), len(set(paths)))
        closure, dynamic = _active_closure()
        self.assertEqual(len(closure), 40)
        self.assertEqual(dynamic, set())
        self.assertEqual(PREVIOUSLY_UNBOUND, closure - set(
            record["repository_path"]
            for record in _self_hashed_git_document(
                R1D2_B, "docs/task_reports/TASK-039E3_R1D2_SOURCE_FREEZE.json"
            )["source_records"]
        ))
        self.assertEqual(closure - set(paths), set())
        self.assertEqual(set(paths) - closure, {
            "schemas/v6/task039e3_recovery_execution_authorization_v3_schema.json"
        })
        for record in records:
            path = str(record["repository_path"])
            raw = _blob(path)
            with self.subTest(path=path):
                self.assertEqual(
                    _git_text("rev-parse", f"{R1D2_A}:{path}"),
                    record["git_blob_sha"],
                )
                self.assertEqual(hashlib.sha256(raw).hexdigest(), record["sha256"])
                self.assertEqual(_git_bytes("show", f"{BLOCKED_AUDIT_B}:{path}"), raw)

    def test_existing_integrity_guard_rejects_every_material_mutation(self) -> None:
        manifest = _manifest()
        initial = _integrity_state(manifest)
        material = {blob.repository_path for blob in initial.source_blobs}
        self.assertEqual(len(material), 40)
        self.assertTrue(PREVIOUSLY_UNBOUND.issubset(material))
        for path in sorted(material):
            for field in ("git_blob_sha", "sha256"):
                with self.subTest(path=path, field=field):
                    holder = {"state": initial}
                    guard = integrity.PostContactIntegrityGuardV3(
                        snapshot=integrity.capture_execution_integrity_snapshot_v3(initial),
                        observed_state_loader=lambda: holder["state"],
                    )
                    guard.execute_provider_attempt(lambda: "synthetic-response")
                    changed = tuple(
                        replace(blob, **{field: "f" * (40 if field == "git_blob_sha" else 64)})
                        if blob.repository_path == path else blob
                        for blob in initial.source_blobs
                    )
                    holder["state"] = replace(initial, source_blobs=changed)
                    with self.assertRaises(integrity.TASK039E3RecoveryIntegrityV3Error):
                        guard.assert_before_terminal_pass()
                    attempts: list[str] = []
                    with self.assertRaisesRegex(
                        integrity.TASK039E3RecoveryIntegrityV3Error,
                        "permanently blocked",
                    ):
                        guard.execute_provider_attempt(lambda: attempts.append("attempt"))
                    self.assertEqual(attempts, [])

    def test_existing_runtime_and_authorization_accept_complete_manifest(self) -> None:
        manifest = _manifest()
        manifest_hash = str(manifest["artifact_hash"])
        receipt = auth_fixture._audit_receipt(
            r1d2_commit_a=R1D2_A,
            r1d2_commit_b=R1D2_B,
            r1d2_source_manifest_hash=manifest_hash,
        )
        authorization_document = auth_fixture._authorization(
            r1d2_commit_a=R1D2_A,
            r1d2_commit_b=R1D2_B,
            r1d2_source_manifest_hash=manifest_hash,
            r1d2_audit_receipt_hash=receipt["artifact_hash"],
        )
        validated = authority.validate_r2_authorization_v3(authorization_document)
        self.assertEqual(validated.r1d2_source_manifest_hash, manifest_hash)

        with tempfile.TemporaryDirectory() as temporary:
            clone = Path(temporary) / "exact-a"
            subprocess.run(
                [
                    "git",
                    "-c",
                    "safe.directory=*",
                    "clone",
                    "--local",
                    "--no-hardlinks",
                    str(_repository()),
                    str(clone),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            subprocess.run(
                ["git", "checkout", "--detach", R1D2_A],
                cwd=clone,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            git_state = collect_git_execution_state_v3(clone, manifest)
            authority.validate_git_and_source_state_v3(
                git_state, authorization=validated
            )
            events: list[str] = []
            credential_calls: list[str] = []
            bootstrap = authority.run_ordered_precontact_guards_v3(
                authorization_document=authorization_document,
                prior_authority_state_loader=auth_fixture._prior,
                git_state_loader=lambda: git_state,
                external_audit_receipt=receipt,
                git_receipt_blob_loader=lambda _commit, _path: auth_fixture._git_blob(receipt),
                historical_capability_receipt_hash=authority.HISTORICAL_CAPABILITY_RECEIPT_HASH,
                historical_provider_ledger_head_hash=authority.HISTORICAL_PROVIDER_LEDGER_HEAD_HASH,
                root_guard_loader=lambda: {"synthetic_roots": "valid"},
                scientific_preflight_loader=lambda: {"synthetic_public_preflight": "valid"},
                credential_loader=lambda: credential_calls.append("credential") or "sentinel",
                event_sink=events.append,
            )
            self.assertEqual(bootstrap.credential, "sentinel")
            self.assertEqual(credential_calls, ["credential"])
            self.assertEqual(events[-1], "credential_loaded")
            self.assertEqual(_git_text("rev-parse", "HEAD", repository=clone), R1D2_A)
            self.assertEqual(_git_text("status", "--porcelain=v1", repository=clone), "")


if __name__ == "__main__":
    unittest.main()
