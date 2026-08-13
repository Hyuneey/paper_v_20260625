from __future__ import annotations

import ast
import json
from pathlib import Path
import unittest

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_r2r_authorization_v1 import (
    TASK039E3R2RAuthorizationError,
    validate_r2r_authorization_v1,
)
from paperworks.v6.task039e3_r2r_capability_reuse_v1 import (
    CAPABILITY_PROVIDER_LEDGER_HASH,
    CAPABILITY_PROVIDER_LEDGER_HEAD_HASH,
    CapabilityLedgerObservationR2RV1,
    TASK039E3R2RCapabilityReuseError,
    validate_capability_reuse_v1,
)
from paperworks.v6.task039e3_r2r_execution_v1 import (
    EXPECTED_EMPTY_LEDGER_KINDS,
    FreshLedgerObservationR2RV1,
    TASK039E3R2RExecutionError,
    build_lifetime_accounting_v1,
    run_fresh_r2r_cohort_v1,
)


ROOT = Path(__file__).resolve().parents[1]
AUTHORIZATION_SCHEMA = (
    ROOT / "schemas" / "v6" / "task039e3_r2r_execution_authorization_v1_schema.json"
)


def _authorization() -> dict[str, object]:
    schema = json.loads(AUTHORIZATION_SCHEMA.read_text(encoding="utf-8"))
    result: dict[str, object] = {}
    for key, definition in schema["properties"].items():
        if key == "self_hash":
            continue
        if "const" in definition:
            result[key] = definition["const"]
        elif "{40}" in definition.get("pattern", ""):
            result[key] = "a" * 40
        else:
            result[key] = "b" * 64
    result["self_hash"] = stable_hash_v1(result)
    return result


def _attempt() -> dict[str, object]:
    attempt: dict[str, object] = {
        "sequence_index": 0,
        "attempt_number": 1,
        "request_hash": "90ba8e7cf83a59573bf6776de65015aa30c1c5037898eef1c38c3e29feec57fd",
        "response_origin": "provider",
        "transport_response_received": True,
        "provider_payload_received": True,
        "provider_contacted": True,
        "provider_authored_response": True,
        "response_present": True,
        "structured_payload_valid": True,
        "outcome": "successful_response",
        "terminal_classification": "completed_provider_response",
        "status_code": 200,
        "returned_model": "gpt-5.4-2026-03-05",
        "response_id": "chatcmpl-EBymHEjpmxFMggRlkPRcAH7HW4tAu",
        "finish_reason": "stop",
        "token_usage": {"prompt_tokens": 97, "completion_tokens": 44, "total_tokens": 141},
        "system_fingerprint": "synthetic-redacted",
        "provider_payload_hash": "c" * 64,
        "retry_eligible": False,
        "actual_retry_delay_before_attempt_seconds": None,
        "retry_after_seconds_observed": None,
    }
    attempt["record_hash"] = stable_hash_v1(attempt)
    return attempt


def _capability_record() -> dict[str, object]:
    return {
        "record_hash": CAPABILITY_PROVIDER_LEDGER_HEAD_HASH,
        "sequence_index": 0,
        "previous_record_hash": None,
        "ledger_kind": "recovery_capability",
        "logical_call_kind": "recovery_capability",
        "payload": {
            "logical_call_kind": "recovery_capability",
            "scientific": False,
            "response_origin": "provider",
            "provider_contacted": True,
            "provider_authored_response": True,
            "transport_response_received": True,
            "provider_payload_received": True,
            "response_present": True,
            "structured_payload_valid": True,
            "returned_model": "gpt-5.4-2026-03-05",
            "response_id": "chatcmpl-EBymHEjpmxFMggRlkPRcAH7HW4tAu",
            "finish_reason": "stop",
            "parse_status": "provider_response_received",
            "terminal_slot_state": "completed_provider_response",
            "gate_status": "PASS",
            "transport_attempts": [_attempt()],
        },
    }


def _ledger() -> CapabilityLedgerObservationR2RV1:
    return CapabilityLedgerObservationR2RV1(
        ledger_kind="recovery_capability",
        ledger_hash=CAPABILITY_PROVIDER_LEDGER_HASH,
        head_record_hash=CAPABILITY_PROVIDER_LEDGER_HEAD_HASH,
        authoritative_record_count=1,
        orphan_record_hashes=(),
        pending_files=(),
        reachable_record=_capability_record(),
    )


def _receipt() -> dict[str, object]:
    receipt: dict[str, object] = {
        "schema_version": "3.0.0",
        "artifact_type": "task039e3_recovery_capability_receipt_v3",
        "task_id": "TASK-039E3-R2_RECOVERY_EXECUTION",
        "status": "passed_task039e3_recovery_capability_gate",
        "gate_status": "PASS",
        "execution_commit": "2653f2b7349a049f9ca4828d736dfea9462c4748",
        "source_manifest_hash": "e8f236a8238bad744eced3009e2000bab9597094cab04446d920df0a0ddf9283",
        "r2_authorization_hash": "2133f54651447258c00546d6293600f95bbea86500a7ced7ca9bbe820ef373cc",
        "historical_capability_probes": 1,
        "current_recovery_capability_logical_calls": 1,
        "cumulative_real_provider_capability_probes": 2,
        "transport_attempts": 1,
        "transport_retries": 0,
        "response_present": True,
        "provider_authored_response": True,
        "returned_model": "gpt-5.4-2026-03-05",
        "response_id": "chatcmpl-EBymHEjpmxFMggRlkPRcAH7HW4tAu",
        "finish_reason": "stop",
        "usage": {"prompt_tokens": 97, "completion_tokens": 44, "total_tokens": 141},
        "terminal_slot_state": "completed_provider_response",
        "capability_provider_ledger_hash": CAPABILITY_PROVIDER_LEDGER_HASH,
        "capability_provider_ledger_head_hash": CAPABILITY_PROVIDER_LEDGER_HEAD_HASH,
        "gate": {
            "gate_status": "PASS",
            "failure_codes": [],
            "provider_model_identity_source": "provider_response_metadata_only",
            "structured_output_authority_source": "observed_strict_schema_parse_and_validation",
            "transport_response_succeeded": True,
            "model_identity_match": True,
            "refusal_absent": True,
            "structured_parse_pass": True,
            "schema_validation_pass": True,
            "fixture_id_match": True,
            "capability_token_match": True,
            "parsed_payload": {
                "fixture_id": "SYNTHETIC_CAPABILITY_CHECK",
                "capability_token": "TASK039E3_STRICT_JSON_SCHEMA_V1",
            },
        },
        "local_compatibility_slots": 0,
        "credential_persisted": False,
        "authorization_header_persisted": False,
    }
    receipt["artifact_hash"] = stable_hash_v1(receipt)
    return receipt


def _empty_ledgers() -> tuple[FreshLedgerObservationR2RV1, ...]:
    return tuple(
        FreshLedgerObservationR2RV1(kind, 0, None)
        for kind in EXPECTED_EMPTY_LEDGER_KINDS
    )


class R2RCapabilityReuseAndExecutionTests(unittest.TestCase):
    def test_exact_capability_pass_reuse_and_closed_authorization(self) -> None:
        authority = validate_r2r_authorization_v1(_authorization())
        reuse = validate_capability_reuse_v1(
            private_capability_receipt=_receipt(), ledger_observation=_ledger()
        )
        self.assertEqual(authority.implementation_commit_a, "a" * 40)
        self.assertEqual(reuse.additional_capability_probes, 0)
        self.assertFalse(reuse.capability_transport_reachable)

    def test_capability_receipt_or_custody_drift_fails_closed(self) -> None:
        for field, bad in (
            ("gate_status", "BLOCK"),
            ("returned_model", "wrong-model"),
            ("transport_attempts", 2),
            ("transport_retries", 1),
            ("local_compatibility_slots", 1),
            ("cumulative_real_provider_capability_probes", 3),
        ):
            with self.subTest(field=field):
                receipt = _receipt()
                receipt[field] = bad
                receipt["artifact_hash"] = stable_hash_v1(
                    {key: value for key, value in receipt.items() if key != "artifact_hash"}
                )
                with self.assertRaises(TASK039E3R2RCapabilityReuseError):
                    validate_capability_reuse_v1(
                        private_capability_receipt=receipt,
                        ledger_observation=_ledger(),
                    )
        bad_ledger = CapabilityLedgerObservationR2RV1(
            **{**_ledger().__dict__, "pending_files": ("unexpected.pending",)}
        )
        with self.assertRaises(TASK039E3R2RCapabilityReuseError):
            validate_capability_reuse_v1(
                private_capability_receipt=_receipt(),
                ledger_observation=bad_ledger,
            )

    def test_e1_and_science_unreachable_when_fresh_ledger_is_not_empty(self) -> None:
        events: list[str] = []
        ledgers = list(_empty_ledgers())
        ledgers[0] = FreshLedgerObservationR2RV1("scientific_provider", 1, "d" * 64)
        with self.assertRaises(TASK039E3R2RExecutionError):
            run_fresh_r2r_cohort_v1(
                authorization_document=_authorization(),
                private_capability_receipt=_receipt(),
                capability_ledger_observation=_ledger(),
                fresh_ledger_observations_loader=lambda: tuple(ledgers),
                e1_loader=lambda: events.append("e1"),
                scientific_runner=lambda _e1: events.append("science"),
            )
        self.assertEqual(events, [])

    def test_fresh_full_cohort_order_has_no_capability_transport_or_resume(self) -> None:
        events: list[str] = []
        result = run_fresh_r2r_cohort_v1(
            authorization_document=_authorization(),
            private_capability_receipt=_receipt(),
            capability_ledger_observation=_ledger(),
            fresh_ledger_observations_loader=lambda: _empty_ledgers(),
            e1_loader=lambda: events.append("e1") or "same-e1-cohort",
            scientific_runner=lambda evidence: events.append("science") or evidence,
            stage_sink=events.append,
        )
        self.assertEqual(result.capability_transport_calls, 0)
        self.assertEqual(result.capability_probe_calls, 0)
        self.assertEqual(result.prior_partial_records_reused, 0)
        self.assertEqual(result.recovery_execution_mode, "FRESH_FULL_COHORT_RESTART")
        self.assertEqual(
            events,
            [
                "r2r_authorization_validated",
                "durable_capability_pass_reused",
                "fresh_full_cohort_ledgers_empty",
                "e1",
                "e1_loaded_after_reuse_and_empty_ledgers",
                "science",
                "fresh_scientific_cohort_executed",
            ],
        )
        self.assertEqual(result.scientific_result, "same-e1-cohort")

    def test_lifetime_and_recovery_accounting_namespaces_are_separate(self) -> None:
        low = build_lifetime_accounting_v1(252)
        high = build_lifetime_accounting_v1(336)
        self.assertEqual(low.historical_scientific_logical_calls_total, 6)
        self.assertEqual(high.historical_scientific_logical_calls_total, 6)
        self.assertEqual(low.lifetime_scientific_logical_call_attempts, 258)
        self.assertEqual(high.lifetime_scientific_logical_call_attempts, 342)
        for invalid in (251, 337, True):
            with self.assertRaises(TASK039E3R2RExecutionError):
                build_lifetime_accounting_v1(invalid)

    def test_authorization_schema_is_closed_and_prohibits_probe_resume_and_downstream_authority(self) -> None:
        schema = json.loads(AUTHORIZATION_SCHEMA.read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(set(schema["required"]), set(schema["properties"]))
        for key in (
            "capability_probe_authorized",
            "provider_diagnostic_call_authorized",
            "resume_authorized",
            "historical_partial_result_reuse_authorized",
            "rule_v2_authorized",
            "runtime_authority",
            "utility_evaluation_authorized",
            "winner_selected",
        ):
            self.assertFalse(schema["properties"][key]["const"])
        authority = _authorization()
        authority["capability_probe_authorized"] = True
        authority["self_hash"] = stable_hash_v1(
            {key: value for key, value in authority.items() if key != "self_hash"}
        )
        with self.assertRaises(TASK039E3R2RAuthorizationError):
            validate_r2r_authorization_v1(authority)

    def test_modules_contain_no_network_environment_or_capability_request_path(self) -> None:
        for relative in (
            "src/paperworks/v6/task039e3_r2r_capability_reuse_v1.py",
            "src/paperworks/v6/task039e3_r2r_execution_v1.py",
            "src/paperworks/v6/task039e3_r2r_authorization_v1.py",
        ):
            source = (ROOT / relative).read_text(encoding="utf-8")
            tree = ast.parse(source)
            imported = {
                node.module or ""
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom)
            } | {
                alias.name
                for node in ast.walk(tree)
                if isinstance(node, ast.Import)
                for alias in node.names
            }
            self.assertFalse(
                imported
                & {"os", "socket", "urllib", "urllib.request", "requests", "httpx", "openai"}
            )
            self.assertNotIn("build_recovery_capability_request", source)
            self.assertNotIn("OPENAI_API_KEY", source)


if __name__ == "__main__":
    unittest.main()
