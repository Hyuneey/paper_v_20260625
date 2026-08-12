from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import unittest

from paperworks.v6.common import stable_hash_v1, thaw_json
from paperworks.v6.task039e3_execution_prep_v1 import MockProviderResponseV1
from paperworks.v6.task039e3_recovery_capability_v1 import (
    RECOVERY_CAPABILITY_PROMPT_SHA256,
    RECOVERY_CAPABILITY_PROMPT_V1,
    RECOVERY_CAPABILITY_SCHEMA_SHA256,
    RECOVERY_CAPABILITY_SCHEMA_V1,
    RecoveryProbeAccountingV1,
    TASK039E3RecoveryCapabilityError,
    build_recovery_capability_request_v1,
    evaluate_recovery_capability_response_v1,
)


def _response(
    *,
    model: str = "gpt-5.4-2026-03-05",
    content: str | None = None,
    refusal: bool = False,
) -> MockProviderResponseV1:
    return MockProviderResponseV1(
        response_present=True,
        outcome="provider_refusal" if refusal else "successful_response",
        status_code=200,
        model=model,
        content=content
        if content is not None
        else json.dumps(
            {
                "fixture_id": "SYNTHETIC_CAPABILITY_CHECK",
                "capability_token": "TASK039E3_STRICT_JSON_SCHEMA_V1",
            }
        ),
        refusal=refusal,
        finish_reason="stop",
        response_id="synthetic-response",
    )


class RecoveryCapabilityContractTests(unittest.TestCase):
    def test_prompt_and_schema_hashes_are_exact(self) -> None:
        self.assertEqual(
            sha256(RECOVERY_CAPABILITY_PROMPT_V1.encode("utf-8")).hexdigest(),
            RECOVERY_CAPABILITY_PROMPT_SHA256,
        )
        self.assertEqual(
            stable_hash_v1(RECOVERY_CAPABILITY_SCHEMA_V1),
            RECOVERY_CAPABILITY_SCHEMA_SHA256,
        )
        path = (
            Path(__file__).resolve().parents[1]
            / "schemas/v6/task039e3_recovery_capability_response_v1_schema.json"
        )
        self.assertEqual(json.loads(path.read_text(encoding="utf-8")), thaw_json(RECOVERY_CAPABILITY_SCHEMA_V1))

    def test_request_is_exact_stateless_strict_schema(self) -> None:
        request = build_recovery_capability_request_v1()
        body = thaw_json(request.request_body)
        self.assertEqual(body["model"], "gpt-5.4-2026-03-05")
        self.assertEqual(body["messages"], [{"role": "user", "content": RECOVERY_CAPABILITY_PROMPT_V1}])
        self.assertEqual(body["response_format"]["type"], "json_schema")
        contract = body["response_format"]["json_schema"]
        self.assertTrue(contract["strict"])
        self.assertEqual(contract["schema"], thaw_json(RECOVERY_CAPABILITY_SCHEMA_V1))
        self.assertNotIn("tools", body)
        self.assertNotIn("seed", body)

    def test_corrected_gate_passes_authoritative_observations(self) -> None:
        result = evaluate_recovery_capability_response_v1(_response())
        self.assertEqual(result.gate_status, "PASS")
        self.assertEqual(result.failure_codes, ())
        self.assertEqual(result.provider_model_identity_source, "provider_response_metadata_only")
        self.assertEqual(result.structured_output_authority_source, "observed_strict_schema_parse_and_validation")

    def test_wrong_provider_model_blocks(self) -> None:
        result = evaluate_recovery_capability_response_v1(_response(model="wrong-model"))
        self.assertEqual(result.gate_status, "BLOCK")
        self.assertIn("returned_model_mismatch", result.failure_codes)

    def test_provider_refusal_blocks_and_is_not_parsed(self) -> None:
        result = evaluate_recovery_capability_response_v1(_response(refusal=True))
        self.assertEqual(result.gate_status, "BLOCK")
        self.assertIn("provider_refusal", result.failure_codes)
        self.assertFalse(result.structured_parse_pass)

    def test_malformed_json_blocks(self) -> None:
        result = evaluate_recovery_capability_response_v1(_response(content="{"))
        self.assertEqual(result.gate_status, "BLOCK")
        self.assertIn("structured_parse_failed", result.failure_codes)

    def test_closed_schema_rejects_missing_extra_and_wrong_types(self) -> None:
        payloads = (
            {"fixture_id": "SYNTHETIC_CAPABILITY_CHECK"},
            {
                "fixture_id": "SYNTHETIC_CAPABILITY_CHECK",
                "capability_token": "TASK039E3_STRICT_JSON_SCHEMA_V1",
                "extra": True,
            },
            {
                "fixture_id": "SYNTHETIC_CAPABILITY_CHECK",
                "capability_token": 1,
            },
        )
        for payload in payloads:
            with self.subTest(payload=payload):
                result = evaluate_recovery_capability_response_v1(_response(content=json.dumps(payload)))
                self.assertEqual(result.gate_status, "BLOCK")
                self.assertIn("schema_validation_failed", result.failure_codes)

    def test_wrong_fixture_and_token_block(self) -> None:
        for field, expected_code in (
            ("fixture_id", "fixture_id_mismatch"),
            ("capability_token", "capability_token_mismatch"),
        ):
            payload = {
                "fixture_id": "SYNTHETIC_CAPABILITY_CHECK",
                "capability_token": "TASK039E3_STRICT_JSON_SCHEMA_V1",
            }
            payload[field] = "wrong"
            result = evaluate_recovery_capability_response_v1(_response(content=json.dumps(payload)))
            self.assertEqual(result.gate_status, "BLOCK")
            self.assertIn(expected_code, result.failure_codes)

    def test_self_report_fields_have_no_authority_and_are_rejected(self) -> None:
        payload = {
            "fixture_id": "SYNTHETIC_CAPABILITY_CHECK",
            "capability_token": "TASK039E3_STRICT_JSON_SCHEMA_V1",
            "model_snapshot": "gpt-5.4-2026-03-05",
            "structured_output_supported": True,
        }
        result = evaluate_recovery_capability_response_v1(_response(content=json.dumps(payload)))
        self.assertEqual(result.gate_status, "BLOCK")
        self.assertIn("schema_validation_failed", result.failure_codes)

    def test_transport_failure_blocks(self) -> None:
        response = MockProviderResponseV1(False, "timeout_before_response", None, None, None)
        result = evaluate_recovery_capability_response_v1(response)
        self.assertEqual(result.gate_status, "BLOCK")
        self.assertIn("transport_response_failed", result.failure_codes)

    def test_probe_accounting_preserves_history_and_prevents_third_probe(self) -> None:
        before = RecoveryProbeAccountingV1()
        self.assertEqual(before.historical_probe_count, 1)
        self.assertEqual(before.cumulative_probe_count, 1)
        after = before.after_logical_recovery_probe()
        self.assertEqual(after.current_recovery_probe_count, 1)
        self.assertEqual(after.cumulative_probe_count, 2)
        with self.assertRaisesRegex(TASK039E3RecoveryCapabilityError, "third"):
            after.after_logical_recovery_probe()


if __name__ == "__main__":
    unittest.main()
