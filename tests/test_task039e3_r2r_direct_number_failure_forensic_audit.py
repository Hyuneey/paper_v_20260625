from __future__ import annotations

from hashlib import sha256
import inspect
import json
import os
from pathlib import Path
import subprocess
from typing import Any, Mapping
import unittest

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e2_execution_configuration_v1 import (
    CALIBRATED_NUMERIC_ROLES,
    render_direct_number_model_content_v1,
)
from paperworks.v6.task039e3_execution_prep_v1 import (
    TASK039E3PreparationError,
    build_direct_number_request_v1,
)
from paperworks.v6.task039e3_orchestration_v1 import run_direct_number_v1
from paperworks.v6.task039e3_recovery_serialization_v1 import (
    verify_public_artifact_v1,
)
from paperworks.v6.task039e3_recovery_transactional_custody_v3 import (
    reconstruct_transactional_ledger_v3,
)
from paperworks.v6.task039e3_scientific_execution_v1 import (
    _verify_self_hash,
    project_real_evidence_v1,
    validate_public_preflight_v1,
)
from task039e3_support import make_evidence


EXECUTION_COMMIT = "f10365adbdde5bb2070df429770174d215829dc6"
AUTHORIZATION_V2_HASH = (
    "ce5ef3e3d4d737721b53fdb2ec43d116d93eeb4bd1471dd6fc4f5c0f7e306b8f"
)
FAILURE_RECEIPT_HASH = (
    "b68443208e7dca30aaad862610421d7c78cf40cc8c951b33ef4a55a9929c5393"
)
EXPECTED_EXCEPTION_MESSAGE = "direct-number calibrated reference leaked"
EXPECTED_EXCEPTION_MESSAGE_SHA256 = sha256(
    EXPECTED_EXCEPTION_MESSAGE.encode("utf-8")
).hexdigest()
EXPECTED_ROOT_CAUSE = (
    "REAL_E1_NUMERIC_REFERENCE_ALIASED_AS_APPROVED_EVIDENCE_IDENTITY_"
    "CAUSES_DIRECT_NUMBER_LEAK_GUARD"
)
EXPECTED_TEST_GAP = (
    "SYNTHETIC_FIXTURE_DID_NOT_PRESERVE_REAL_E1_REFERENCE_IDENTITY_ALIASING"
)
PRIVATE_LEDGER_FILE = "TASK039E1_PRIVATE_CONSTRUCTION_EVIDENCE_LEDGER.json"


def _read_jsonl(path: Path) -> tuple[dict[str, Any], ...]:
    with path.open("r", encoding="utf-8") as handle:
        return tuple(json.loads(line) for line in handle if line.strip())


def _stream_private_relation_record(
    ledger_path: Path, target_relation_identity: str
) -> tuple[dict[str, Any], int, int]:
    """Read only through the target relation instead of decoding all private E1."""

    decoder = json.JSONDecoder()
    buffer = ""
    bytes_read = 0
    position: int | None = None
    decoded_count = 0
    with ledger_path.open("r", encoding="utf-8") as handle:
        while True:
            if position is None:
                marker = buffer.find('"records"')
                bracket = buffer.find("[", marker) if marker >= 0 else -1
                if bracket >= 0:
                    position = bracket + 1
            if position is not None:
                while position < len(buffer) and buffer[position] in " \t\r\n,":
                    position += 1
                if position < len(buffer):
                    try:
                        item, end = decoder.raw_decode(buffer, position)
                    except json.JSONDecodeError:
                        pass
                    else:
                        if not isinstance(item, dict):
                            raise AssertionError("private E1 relation record is not an object")
                        decoded_count += 1
                        if item.get("relation_identity") == target_relation_identity:
                            return item, decoded_count, bytes_read
                        position = end
                        continue
            chunk = handle.read(4096)
            if not chunk:
                raise AssertionError("scheduled relation zero is absent from private E1")
            buffer += chunk
            bytes_read += len(chunk.encode("utf-8"))


def project_relation_zero_v1(
    *, execution_repository: Path, e1_private_root: Path
) -> tuple[Any, dict[str, Any]]:
    public = validate_public_preflight_v1(execution_repository)
    schedule = tuple(public["schedule"]["relation_identities"])
    relation_identity = schedule[0]
    private, decoded_count, bytes_read = _stream_private_relation_record(
        e1_private_root / PRIVATE_LEDGER_FILE, relation_identity
    )
    _verify_self_hash(private)
    cohort = public["cohort"]
    primitives = {
        item["relation_identity"]: item
        for item in cohort["confirmed_relation_primitives"]
    }
    bundles = {
        item["relation_binding_hash"]: item
        for item in cohort["approved_numeric_evidence_bundles"]
    }
    manifests = {
        item["relation_identity"]: item for item in cohort["public_manifest_entries"]
    }
    evidence = project_real_evidence_v1(
        private_record=private,
        public_primitive=primitives[relation_identity],
        public_bundle=bundles[private["relation_binding_hash"]],
        public_manifest=manifests[relation_identity],
    )
    return evidence, {
        "relation_schedule_index": 0,
        "relation_identity_hash": sha256(relation_identity.encode("utf-8")).hexdigest(),
        "private_e1_records_decoded": decoded_count,
        "private_e1_bytes_read_upper_bound": bytes_read,
    }


def replay_relation_zero_direct_failure_v1(
    *, execution_repository: Path, e1_private_root: Path
) -> dict[str, Any]:
    evidence, access = project_relation_zero_v1(
        execution_repository=execution_repository, e1_private_root=e1_private_root
    )
    view = evidence.render_view()
    bindings = tuple(view.numeric_bindings)
    aliases = tuple(item for item in bindings if item.reference == item.evidence_identity)
    approved = tuple(view.approved_evidence_identities)
    if approved != tuple(item.reference for item in bindings):
        raise AssertionError("real E1 approved identity/reference projection differs")

    rendered = render_direct_number_model_content_v1(view.to_dict())
    marker = "\n\nDIRECT_NUMBER_INPUT_JSON\n"
    if marker not in rendered:
        raise AssertionError("direct-number rendering marker differs")
    payload = json.loads(rendered.split(marker, 1)[1])
    calibrated = tuple(
        item for item in bindings if item.numeric_role in CALIBRATED_NUMERIC_ROLES
    )
    payload_bindings = tuple(payload.get("numeric_bindings", ()))
    payload_references = payload.get("numeric_references", {})
    payload_approved = tuple(payload.get("approved_evidence_identities", ()))
    remaining_aliases = tuple(
        item.reference for item in calibrated if item.reference in payload_approved
    )

    try:
        build_direct_number_request_v1(view)
    except TASK039E3PreparationError as exc:
        exception_class = type(exc).__name__
        exception_message = str(exc)
    else:
        raise AssertionError("relation-zero direct request unexpectedly built")

    return {
        **access,
        "numeric_binding_count": len(bindings),
        "reference_equals_evidence_identity_count": len(aliases),
        "approved_evidence_identities_equal_binding_references": True,
        "withheld_calibrated_role_count": len(calibrated),
        "calibrated_bindings_remaining_in_model_payload": sum(
            1
            for item in payload_bindings
            if item.get("numeric_role") in CALIBRATED_NUMERIC_ROLES
        ),
        "calibrated_numeric_references_remaining_in_model_payload": sum(
            1 for role in CALIBRATED_NUMERIC_ROLES if role in payload_references
        ),
        "withheld_references_remaining_via_approved_evidence_identities": len(
            remaining_aliases
        ),
        "exception_class": exception_class,
        "exception_message": exception_message,
        "exception_message_sha256": sha256(
            exception_message.encode("utf-8")
        ).hexdigest(),
        "sentinel_send_calls": 0,
        "direct_provider_send_reached": False,
        "root_cause_classification": EXPECTED_ROOT_CAUSE,
    }


def reconstruct_failed_execution_v1(
    *, recovery_private_root: Path, public_failure_receipt: Path
) -> dict[str, Any]:
    receipt = verify_public_artifact_v1(
        json.loads(public_failure_receipt.read_text(encoding="utf-8"))
    )
    expected_public = {
        "artifact_hash": FAILURE_RECEIPT_HASH,
        "status": "failed_task039e3_r2r_scientific_execution",
        "execution_commit": EXECUTION_COMMIT,
        "authorization_hash": AUTHORIZATION_V2_HASH,
        "completed_r2r_scientific_logical_calls": 5,
        "r2r_scientific_transport_attempts": 5,
        "proposal_committed_count": 6,
        "outcome_committed_count": 4,
        "direct_number_committed_count": 0,
        "postcontact_integrity_status": "verified_unchanged",
        "failure_classification": "TASK039E3PreparationError",
    }
    for key, expected in expected_public.items():
        if receipt.get(key) != expected:
            raise AssertionError(f"public failure receipt differs: {key}")
    for key in (
        "rule_v2_authorized",
        "runtime_authority",
        "utility_evaluation_authorized",
        "winner_selected",
        "provider_recontact_authorized",
        "automatic_resume_authorized",
        "patch_and_continue_authorized",
        "historical_partial_results_reused",
    ):
        if receipt.get(key) is not False:
            raise AssertionError(f"public failure prohibition differs: {key}")

    science = recovery_private_root / "scientific_r2r_v1"
    provider = reconstruct_transactional_ledger_v3(
        science / "provider", ledger_kind="scientific_provider"
    )
    http_error = reconstruct_transactional_ledger_v3(
        science / "http_error_attempts", ledger_kind="http_error_custody"
    )
    if provider.orphan_record_hashes or provider.pending_files:
        raise AssertionError("provider custody contains non-authoritative state")
    if http_error.orphan_record_hashes or http_error.pending_files:
        raise AssertionError("HTTP-error custody contains non-authoritative state")
    if provider.authoritative_record_count != 5:
        raise AssertionError("provider custody count differs")
    if http_error.authoritative_record_count != 0:
        raise AssertionError("HTTP-error custody is not empty")

    proposals = _read_jsonl(science / "proposals_working.jsonl")
    outcomes = _read_jsonl(science / "outcomes_working.jsonl")
    direct = _read_jsonl(science / "direct_working.jsonl")
    if (len(proposals), len(outcomes), len(direct)) != (6, 4, 0):
        raise AssertionError("partial scientific custody counts differ")
    relation_identities = {
        str(item["relation_identity"]) for item in (*proposals, *outcomes)
    }
    if len(relation_identities) != 1:
        raise AssertionError("partial custody spans more than relation zero")

    expected_slots = (("T1", 1), ("T1-B", 1), ("T1-B", 2), ("T1-B", 3), ("T2", 1))
    provider_metadata: list[dict[str, Any]] = []
    for record, expected_slot in zip(provider.reachable_records, expected_slots):
        payload = record["payload"]
        slot = payload["slot"]
        observed_slot = (slot["arm"], slot["arm_local_call_number"])
        if observed_slot != expected_slot or slot["relation_schedule_index"] != 0:
            raise AssertionError("scientific provider slot sequence differs")
        metadata = payload["provider_response_metadata"]
        if (
            payload["response_present"] is not True
            or payload["terminal_slot_state"] != "completed_provider_response"
            or metadata.get("model") != "gpt-5.4-2026-03-05"
            or payload.get("provider_contacted") is not True
            or payload.get("provider_authored_response") is not True
        ):
            raise AssertionError("provider record completion metadata differs")
        provider_metadata.append(
            {
                "arm": slot["arm"],
                "local_call_number": slot["arm_local_call_number"],
                "response_present": payload["response_present"],
                "returned_model": metadata.get("model"),
                "terminal_state": payload["terminal_slot_state"],
                "parse_status": payload["parse_status"],
                "record_hash": record["record_hash"],
            }
        )

    proposal_arms = tuple((item["arm"], item["call_number"]) for item in proposals)
    if proposal_arms != (("T0", 0), *expected_slots):
        raise AssertionError("proposal sequence differs")
    outcome_arms = tuple(item["arm"] for item in outcomes)
    if outcome_arms != ("T0", "T1", "T1-B", "T2"):
        raise AssertionError("outcome sequence differs")
    for item in proposals:
        if (
            item.get("proposal_hash") != item.get("project_proposal", {}).get("proposal_hash")
            or item.get("validity_hash")
            != item.get("validity_result", {}).get("artifact_hash")
        ):
            raise AssertionError("proposal/validity persisted hash binding differs")
    for item in outcomes:
        content = {key: value for key, value in item.items() if key != "artifact_hash"}
        if stable_hash_v1(content) != item.get("artifact_hash"):
            raise AssertionError("outcome self-hash differs")

    t2_proposal = proposals[-1]
    t2_outcome = outcomes[-1]
    validity = t2_proposal["validity_result"]
    if (
        t2_outcome["outcome"] != "accepted_proposal"
        or t2_outcome["accepted_call_index"] != 1
        or t2_outcome["generation_calls_consumed"] != 1
        or t2_outcome["retrieval_count"] != 0
        or t2_outcome["revise_count"] != 0
        or validity["status"] != "admissible"
    ):
        raise AssertionError("T2 call-one completion differs")

    return {
        "failure_receipt_hash": receipt["artifact_hash"],
        "provider_contacted": receipt.get("provider_contacted"),
        "scientific_provider_record_count": provider.authoritative_record_count,
        "scientific_provider_ledger_hash": provider.ledger_hash,
        "scientific_provider_ledger_head_hash": provider.head_record_hash,
        "provider_records": provider_metadata,
        "http_error_record_count": http_error.authoritative_record_count,
        "http_error_ledger_hash": http_error.ledger_hash,
        "http_error_ledger_head_hash": http_error.head_record_hash,
        "proposal_record_count": len(proposals),
        "outcome_record_count": len(outcomes),
        "direct_number_record_count": len(direct),
        "relation_identity_hash": sha256(
            next(iter(relation_identities)).encode("utf-8")
        ).hexdigest(),
        "proposal_sequence": [list(item) for item in proposal_arms],
        "outcome_sequence": list(outcome_arms),
        "t2_call_1": {
            "validity_status": validity["status"],
            "outcome": t2_outcome["outcome"],
            "accepted_call_index": t2_outcome["accepted_call_index"],
            "verifier_issue_codes": [item["code"] for item in validity["issues"]],
            "retrieval_count": t2_outcome["retrieval_count"],
            "revise_count": t2_outcome["revise_count"],
            "generation_calls_consumed": t2_outcome["generation_calls_consumed"],
        },
        "all_transactional_chains_valid": True,
        "working_outcome_hashes_valid": True,
        "proposal_validity_hash_bindings_valid": True,
    }


class R2RDirectNumberFailureForensicAuditTests(unittest.TestCase):
    def test_frozen_source_proves_real_e1_identity_alias_invariant(self) -> None:
        source = inspect.getsource(project_real_evidence_v1)
        self.assertIn('evidence_identity=str(item["numeric_reference"])', source)
        self.assertIn("approved_evidence_identities=tuple(item.reference for item in bindings)", source)

    def test_renderer_removes_calibrated_fields_but_not_approved_aliases(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        renderer = subprocess.check_output(
            [
                "git",
                "show",
                (
                    f"{EXECUTION_COMMIT}:"
                    "src/paperworks/v6/task039e2_execution_configuration_v1.py"
                ),
            ],
            cwd=repository,
            text=True,
        )
        self.assertIn("rendered[\"numeric_bindings\"] = retained", renderer)
        self.assertIn("rendered[\"numeric_references\"]", renderer)
        self.assertNotIn("approved_evidence_identities", renderer)
        builder = inspect.getsource(build_direct_number_request_v1)
        self.assertIn("render_direct_number_input_v1(view)", builder)
        direct = inspect.getsource(run_direct_number_v1)
        self.assertLess(direct.index("build_direct_number_request_v1"), direct.index("ProviderCallSlotV1"))

    def test_synthetic_fixture_does_not_preserve_real_alias(self) -> None:
        evidence = make_evidence(1)
        for binding in evidence.numeric_bindings:
            self.assertNotEqual(binding.reference, binding.evidence_identity)
        self.assertEqual(
            evidence.approved_evidence_identities,
            tuple(binding.evidence_identity for binding in evidence.numeric_bindings),
        )

    def test_expected_exception_message_hash_is_frozen(self) -> None:
        self.assertEqual(
            EXPECTED_EXCEPTION_MESSAGE_SHA256,
            sha256(EXPECTED_EXCEPTION_MESSAGE.encode("utf-8")).hexdigest(),
        )

    @unittest.skipUnless(
        os.environ.get("TASK039E3_R2R_FORENSIC_PRIVATE_READ") == "AUTHORIZED",
        "coordinator-only post-Commit-A private read is not enabled",
    )
    def test_exact_preserved_custody_and_real_relation_zero_replay(self) -> None:
        required = {
            name: os.environ.get(name)
            for name in (
                "TASK039E3_EXECUTION_REPOSITORY",
                "TASK039E3_E1_PRIVATE_ROOT",
                "TASK039E3_R2R_FAILED_PRIVATE_ROOT",
                "TASK039E3_R2R_FAILURE_RECEIPT",
            )
        }
        if any(value is None for value in required.values()):
            self.fail("exact forensic path binding is incomplete")
        replay = replay_relation_zero_direct_failure_v1(
            execution_repository=Path(required["TASK039E3_EXECUTION_REPOSITORY"] or ""),
            e1_private_root=Path(required["TASK039E3_E1_PRIVATE_ROOT"] or ""),
        )
        custody = reconstruct_failed_execution_v1(
            recovery_private_root=Path(required["TASK039E3_R2R_FAILED_PRIVATE_ROOT"] or ""),
            public_failure_receipt=Path(required["TASK039E3_R2R_FAILURE_RECEIPT"] or ""),
        )
        self.assertEqual(replay["relation_identity_hash"], custody["relation_identity_hash"])
        self.assertEqual(replay["reference_equals_evidence_identity_count"], 10)
        self.assertEqual(replay["withheld_calibrated_role_count"], 3)
        self.assertEqual(
            replay["withheld_references_remaining_via_approved_evidence_identities"], 3
        )
        self.assertEqual(replay["calibrated_bindings_remaining_in_model_payload"], 0)
        self.assertEqual(replay["calibrated_numeric_references_remaining_in_model_payload"], 0)
        self.assertEqual(replay["exception_class"], "TASK039E3PreparationError")
        self.assertEqual(replay["exception_message"], EXPECTED_EXCEPTION_MESSAGE)
        self.assertEqual(replay["exception_message_sha256"], EXPECTED_EXCEPTION_MESSAGE_SHA256)
        self.assertEqual(replay["sentinel_send_calls"], 0)
        self.assertEqual(custody["t2_call_1"]["outcome"], "accepted_proposal")


if __name__ == "__main__":
    unittest.main()
