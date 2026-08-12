from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_r2r_authorization_v1 import (
    DIRECT_NUMBER_PROMPT_HASH,
    DIRECT_NUMBER_SCHEMA_HASH,
    EXACT_ENDPOINT,
    EXACT_MODEL,
    MAIN_PROMPT_HASH,
    RECOVERY_SCHEMA_V2_HASH,
    RELATION_SCHEDULE_HASH,
    T2_FOLLOWUP_PROMPT_HASH,
    validate_r2r_authorization_v1,
)
from paperworks.v6.task039e3_r2r_live_execution_v1 import (
    INDEPENDENT_AUDIT_RECEIPT_PATH,
    R2RAuthorityContextV1,
    TASK039E3R2RLiveExecutionError,
    _validate_git_source,
)
from paperworks.v6.task039e3_r2r_precontact_v1 import (
    R2RObservedIntegrityStateV1,
    R2RPostContactIntegrityGuardV1,
    R2RSourceBlobIdentityV1,
    R2R_SCIENTIFIC_ACCOUNTING_BEHAVIOR_HASH_V1,
    capture_r2r_integrity_snapshot_v1,
)
from paperworks.v6.task039e3_r2r_result_finalizer_v1 import (
    PRIVATE_ARTIFACT_NAMES_R2R_V1,
    PUBLIC_ARTIFACT_NAMES_R2R_V1,
    SUCCESS_STATUS,
    TASK039E3R2RResultFinalizationError,
    finalize_successful_r2r_scientific_result_v1,
)
from paperworks.v6.task039e3_recovery_serialization_v1 import (
    finalize_public_artifact_v1,
    verify_public_artifact_v1,
    write_public_artifact_atomic_v1,
)
from tests.test_task039e3_r2r_finalization_v1 import _arguments
from tests.test_task039e3_r2r_independent_audit_source_precontact import (
    AUTHORIZATION_SCHEMA,
    reconstruct_active_closure,
)


ROOT = Path(__file__).resolve().parents[1]
IMPLEMENTATION_A = "eb62b449e06ea5f6c4a2d445223f6ca98de3690c"
IMPLEMENTATION_B = "2caec1dbdfd175e07bc2d5d5bf4d36896f56f99d"
NEW_MANIFEST_HASH = "01c8e23f2eb15f321295bf0163dcbd81df67ed0179817acb725614a45bfede1d"
NEW_MANIFEST_PATH = (
    "docs/task_reports/"
    "TASK-039E3_R2R_FINALIZATION_REMEDIATION_SOURCE_FREEZE.json"
)
OLD_IMPLEMENTATION_A = "3aa63588b08692b0333de26d3042b717e62014f2"
OLD_IMPLEMENTATION_B = "c6e34440ee362df51e95b6181853f3f89fe4310e"
OLD_MANIFEST_HASH = "35e73804156c097b27ae3d216575af6867a6330d346ddc71c888b5917a60859a"
OLD_MANIFEST_PATH = "docs/task_reports/TASK-039E3_R2R_C1_SOURCE_FREEZE.json"
FINALIZER_PATH = "src/paperworks/v6/task039e3_r2r_result_finalizer_v1.py"
ENTRYPOINT = "scripts/run_task039e3_r2r_scientific_execution_v1.py"
AUTHORIZATION_SCHEMA_PATH = (
    ROOT / "schemas/v6/task039e3_r2r_execution_authorization_v1_schema.json"
)

PUBLIC_BINDINGS = {
    "capability_reuse": "capability_reuse_artifact_hash",
    "provider_custody": "provider_custody_binding_hash",
    "private_bindings": "private_ledger_bindings_hash",
    "construction_metrics": "construction_metrics_hash",
    "direct_number_metrics": "direct_number_metrics_hash",
    "execution_summary": "execution_summary_hash",
    "data_access_audit": "data_access_audit_hash",
}
PRIVATE_BINDINGS = {
    "scientific_provider": "scientific_provider_ledger_hash",
    "proposal_validity": "proposal_validity_ledger_hash",
    "construction_outcome": "construction_outcome_ledger_hash",
    "direct_number": "direct_number_ledger_hash",
}


def _git_bytes(commit: str, path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def _git_text(*arguments: str, repository: Path = ROOT) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ).stdout.strip()


def _self_hashed_git_document(commit: str, path: str) -> dict[str, object]:
    document = json.loads(_git_bytes(commit, path))
    claimed = document.pop("artifact_hash")
    self_hash = stable_hash_v1(document)
    if claimed != self_hash:
        raise AssertionError(f"self-hash mismatch: {path}")
    return {"artifact_hash": claimed, **document}


def _future_authorization() -> dict[str, object]:
    schema = json.loads(AUTHORIZATION_SCHEMA_PATH.read_text(encoding="utf-8"))
    document: dict[str, object] = {}
    for key, definition in schema["properties"].items():
        if key == "self_hash":
            continue
        if "const" in definition:
            document[key] = definition["const"]
        elif "{40}" in definition.get("pattern", ""):
            document[key] = "a" * 40
        else:
            document[key] = "b" * 64
    document.update(
        {
            "implementation_commit_a": IMPLEMENTATION_A,
            "implementation_commit_b": IMPLEMENTATION_B,
            "implementation_source_manifest_hash": NEW_MANIFEST_HASH,
            "independent_audit_commit_b": "d" * 40,
            "independent_audit_bundle_hash": "e" * 64,
            "independent_audit_receipt_hash": "f" * 64,
            "recovery_execution_configuration_hash": "c" * 64,
        }
    )
    document["self_hash"] = stable_hash_v1(document)
    return document


def _integrity_state(manifest: dict[str, object]) -> R2RObservedIntegrityStateV1:
    identities = tuple(
        R2RSourceBlobIdentityV1(
            str(record["repository_path"]),
            str(record["git_blob_sha"]),
            str(record["sha256"]),
        )
        for record in manifest["source_records"]  # type: ignore[index]
    )
    return R2RObservedIntegrityStateV1(
        execution_commit=IMPLEMENTATION_A,
        source_manifest_hash=NEW_MANIFEST_HASH,
        source_blobs=identities,
        authorization_hash="a" * 64,
        recovery_main_provider_schema_v2_hash=RECOVERY_SCHEMA_V2_HASH,
        main_prompt_hash=MAIN_PROMPT_HASH,
        t2_followup_prompt_hash=T2_FOLLOWUP_PROMPT_HASH,
        direct_number_prompt_hash=DIRECT_NUMBER_PROMPT_HASH,
        direct_number_schema_hash=DIRECT_NUMBER_SCHEMA_HASH,
        exact_model=EXACT_MODEL,
        endpoint=EXACT_ENDPOINT,
        sampling_configuration_hash="b" * 64,
        timeout_seconds=30.0,
        retry_policy_hash="c" * 64,
        relation_schedule_hash=RELATION_SCHEDULE_HASH,
        scientific_concurrency=1,
        scientific_call_budget_hash="d" * 64,
        scientific_accounting_behavior_hash=(
            R2R_SCIENTIFIC_ACCOUNTING_BEHAVIOR_HASH_V1
        ),
        recovery_execution_configuration_hash="e" * 64,
    )


class _AfterReceiptMutationWriter:
    def __init__(
        self,
        *,
        target: Path,
        mutation: str,
        binding_field: str | None = None,
    ) -> None:
        self.target = target
        self.mutation = mutation
        self.binding_field = binding_field

    def __call__(
        self, path: str | Path, document: dict[str, object]
    ) -> dict[str, object]:
        destination = Path(path)
        written = write_public_artifact_atomic_v1(destination, document)
        if destination.name != PUBLIC_ARTIFACT_NAMES_R2R_V1["execution_receipt"]:
            return written
        if self.mutation == "delete":
            self.target.unlink()
        elif self.mutation == "corrupt":
            altered = json.loads(self.target.read_text(encoding="utf-8"))
            altered["artifact_hash"] = "0" * 64
            self.target.write_text(
                json.dumps(altered, sort_keys=True, separators=(",", ":")) + "\n",
                encoding="utf-8",
            )
        elif self.mutation == "rebind" and self.binding_field:
            altered = json.loads(self.target.read_text(encoding="utf-8"))
            altered.pop("artifact_hash")
            altered[self.binding_field] = "0" * 64
            write_public_artifact_atomic_v1(
                self.target, finalize_public_artifact_v1(altered)
            )
        else:
            raise AssertionError("unsupported terminal mutation")
        return written


class R2RIndependentAuditRerunTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.new_manifest = _self_hashed_git_document(
            IMPLEMENTATION_B, NEW_MANIFEST_PATH
        )
        cls.old_manifest = _self_hashed_git_document(
            IMPLEMENTATION_B, OLD_MANIFEST_PATH
        )

    def test_new_source_closure_records_and_only_finalizer_identity_changed(self) -> None:
        closure, dynamic, unresolved = reconstruct_active_closure(IMPLEMENTATION_A)
        new_records = {
            str(record["repository_path"]): record
            for record in self.new_manifest["source_records"]  # type: ignore[index]
        }
        old_records = {
            str(record["repository_path"]): record
            for record in self.old_manifest["source_records"]  # type: ignore[index]
        }
        self.assertEqual(len(closure), 49)
        self.assertEqual(len(closure - {ENTRYPOINT}), 48)
        self.assertEqual(dynamic, set())
        self.assertEqual(unresolved, set())
        self.assertEqual(set(new_records), closure | {AUTHORIZATION_SCHEMA})
        self.assertEqual(len(new_records), 50)
        changed = {
            path
            for path in new_records
            if new_records[path] != old_records[path]
        }
        self.assertEqual(changed, {FINALIZER_PATH})
        for path, record in new_records.items():
            raw = _git_bytes(IMPLEMENTATION_A, path)
            with self.subTest(path=path):
                self.assertEqual(
                    _git_text("rev-parse", f"{IMPLEMENTATION_A}:{path}"),
                    record["git_blob_sha"],
                )
                self.assertEqual(hashlib.sha256(raw).hexdigest(), record["sha256"])

    def test_new_finalizer_blob_and_sha_mutations_are_rejected_and_latched(self) -> None:
        baseline = _integrity_state(self.new_manifest)
        index = next(
            index
            for index, identity in enumerate(baseline.source_blobs)
            if identity.repository_path == FINALIZER_PATH
        )
        for field, value in (("git_blob_sha", "0" * 40), ("sha256", "0" * 64)):
            with self.subTest(field=field):
                changed = list(baseline.source_blobs)
                changed[index] = replace(changed[index], **{field: value})
                state = replace(baseline, source_blobs=tuple(changed))
                guard = R2RPostContactIntegrityGuardV1(
                    capture_r2r_integrity_snapshot_v1(baseline), lambda: state
                )
                calls: list[int] = []
                with self.assertRaises(Exception):
                    guard.invoke_guarded_provider_attempt(lambda: calls.append(1))
                self.assertEqual(calls, [])
                self.assertTrue(guard.blocked)

    def test_private_and_receipt_postwrite_mutation_matrix_blocks_pass(self) -> None:
        cases: list[tuple[str, str, str]] = []
        for key, filename in PRIVATE_ARTIFACT_NAMES_R2R_V1.items():
            cases.extend((key, filename, mutation) for mutation in ("delete", "corrupt"))
        receipt_filename = PUBLIC_ARTIFACT_NAMES_R2R_V1["execution_receipt"]
        cases.extend(
            ("execution_receipt", receipt_filename, mutation)
            for mutation in ("delete", "corrupt")
        )
        blocked: list[str] = []
        for key, filename, mutation in cases:
            with self.subTest(key=key, mutation=mutation):
                with tempfile.TemporaryDirectory() as temporary:
                    base = Path(temporary)
                    private = base / "private"
                    public = base / "public"
                    private.mkdir()
                    if key == "execution_receipt":
                        target = public / filename
                    else:
                        target = private / "final_authoritative_r2r_v1" / filename
                    arguments = _arguments(private, public)
                    arguments["artifact_writer"] = _AfterReceiptMutationWriter(
                        target=target, mutation=mutation
                    )
                    with self.assertRaises(TASK039E3R2RResultFinalizationError):
                        finalize_successful_r2r_scientific_result_v1(**arguments)
                    blocked.append(f"{key}:{mutation}")
        self.assertEqual(len(blocked), 10)

    def test_every_public_and_private_cross_binding_mutation_blocks_pass(self) -> None:
        cases = [
            ("receipt", key, field) for key, field in PUBLIC_BINDINGS.items()
        ] + [
            ("private_bindings", key, field)
            for key, field in PRIVATE_BINDINGS.items()
        ]
        blocked: list[str] = []
        for owner, key, field in cases:
            with self.subTest(owner=owner, key=key):
                with tempfile.TemporaryDirectory() as temporary:
                    base = Path(temporary)
                    private = base / "private"
                    public = base / "public"
                    private.mkdir()
                    target_key = (
                        "execution_receipt" if owner == "receipt" else "private_bindings"
                    )
                    target = public / PUBLIC_ARTIFACT_NAMES_R2R_V1[target_key]
                    arguments = _arguments(private, public)
                    arguments["artifact_writer"] = _AfterReceiptMutationWriter(
                        target=target,
                        mutation="rebind",
                        binding_field=field,
                    )
                    with self.assertRaises(TASK039E3R2RResultFinalizationError):
                        finalize_successful_r2r_scientific_result_v1(**arguments)
                    blocked.append(f"{owner}:{key}")
        self.assertEqual(len(blocked), 11)

    def test_normal_result_returns_only_reread_durable_hashes_and_bindings(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            private = base / "private"
            public = base / "public"
            private.mkdir()
            result = finalize_successful_r2r_scientific_result_v1(
                **_arguments(private, public)
            )
            self.assertEqual(result.status, SUCCESS_STATUS)
            observed_public: dict[str, dict[str, object]] = {}
            for key, filename in PUBLIC_ARTIFACT_NAMES_R2R_V1.items():
                observed_public[key] = verify_public_artifact_v1(
                    json.loads((public / filename).read_text(encoding="utf-8"))
                )
                self.assertEqual(
                    result.public_artifact_hashes[key],
                    observed_public[key]["artifact_hash"],
                )
            observed_private: dict[str, dict[str, object]] = {}
            private_root = private / "final_authoritative_r2r_v1"
            for key, filename in PRIVATE_ARTIFACT_NAMES_R2R_V1.items():
                observed_private[key] = verify_public_artifact_v1(
                    json.loads((private_root / filename).read_text(encoding="utf-8"))
                )
                self.assertEqual(
                    result.private_artifact_hashes[key],
                    observed_private[key]["artifact_hash"],
                )
            receipt = observed_public["execution_receipt"]
            for key, field in PUBLIC_BINDINGS.items():
                self.assertEqual(receipt[field], observed_public[key]["artifact_hash"])
            private_bindings = observed_public["private_bindings"]
            for key, field in PRIVATE_BINDINGS.items():
                self.assertEqual(
                    private_bindings[field], observed_private[key]["artifact_hash"]
                )
            self.assertEqual(
                result.execution_receipt_hash, receipt["artifact_hash"]
            )

    def test_future_authorization_and_live_source_guard_bind_only_new_pairing(self) -> None:
        document = _future_authorization()
        validated = validate_r2r_authorization_v1(document)
        self.assertEqual(validated.implementation_commit_a, IMPLEMENTATION_A)
        self.assertEqual(validated.implementation_commit_b, IMPLEMENTATION_B)
        self.assertEqual(
            validated.implementation_source_manifest_hash, NEW_MANIFEST_HASH
        )
        context = R2RAuthorityContextV1(document, validated)
        with tempfile.TemporaryDirectory(prefix="r2r-audit-rerun-source-") as temporary:
            checkout = Path(temporary) / "execution"
            subprocess.run(
                ["git", "clone", "--no-checkout", "--shared", str(ROOT), str(checkout)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            subprocess.run(
                [
                    "git",
                    "-c",
                    "core.autocrlf=false",
                    "-c",
                    "core.eol=lf",
                    "checkout",
                    "--detach",
                    "-f",
                    IMPLEMENTATION_A,
                ],
                cwd=checkout,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            source = _validate_git_source(
                checkout, context, ROOT / NEW_MANIFEST_PATH
            )
            self.assertEqual(len(source.source_blobs), 50)
            with self.assertRaises(TASK039E3R2RLiveExecutionError):
                _validate_git_source(checkout, context, ROOT / OLD_MANIFEST_PATH)

    def test_canonical_exact_git_receipt_path_is_frozen(self) -> None:
        self.assertEqual(
            INDEPENDENT_AUDIT_RECEIPT_PATH,
            "docs/task_reports/TASK-039E3_R2R_AUDIT_RECEIPT.json",
        )


if __name__ == "__main__":
    unittest.main()
