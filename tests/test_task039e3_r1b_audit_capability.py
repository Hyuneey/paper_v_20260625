from __future__ import annotations

from hashlib import sha256
import inspect
import json
from pathlib import Path
import unittest

from paperworks.v6.common import thaw_json
from paperworks.v6.task039e3_execution_prep_v1 import MockProviderResponseV1
from paperworks.v6.task039e3_recovery_capability_v1 import (
    R0_CHECKER_SPEC_HASH,
    R0_REQUEST_BUILDER_CONTRACT_HASH,
    RECOVERY_CAPABILITY_PROMPT_SHA256,
    RECOVERY_CAPABILITY_PROMPT_V1,
    RECOVERY_CAPABILITY_SCHEMA_SHA256,
    RECOVERY_CAPABILITY_SCHEMA_V1,
    build_recovery_capability_request_v1,
    evaluate_recovery_capability_response_v1,
)


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_MODEL = "gpt-5.4-2026-03-05"
EXPECTED_PROMPT = (
    "SYNTHETIC_CAPABILITY_CHECK\n"
    "Return exactly the frozen capability acknowledgement. "
    "No scientific evidence is supplied."
)
EXPECTED_PROMPT_HASH = (
    "b725da5aaf23913c5c5ad7c74aa8260304c27a53f004d588d34b386ecfe0372b"
)
EXPECTED_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "additionalProperties": False,
    "properties": {
        "capability_token": {
            "const": "TASK039E3_STRICT_JSON_SCHEMA_V1",
            "type": "string",
        },
        "fixture_id": {
            "const": "SYNTHETIC_CAPABILITY_CHECK",
            "type": "string",
        },
    },
    "required": ["fixture_id", "capability_token"],
    "type": "object",
}
EXPECTED_SCHEMA_HASH = (
    "7fb77614ef8df85ea6c03afe7b47ec6fda06c5b09d8f37722daae39de0f57e9a"
)
EXPECTED_CHECKER_HASH = (
    "a2484b2a1327a48b2b02ee7d2dc3cb05909daed8724a736c806117253b4df783"
)
EXPECTED_REQUEST_CONTRACT_HASH = (
    "8bdd8612f57bef011a28f3c130953f0e2fbd05f0e0ba153a8c712688cec10864"
)


def _canonical_hash(value: object) -> str:
    """Independent standard-library canonical hash oracle."""

    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _response(
    payload: object,
    *,
    model: str = EXPECTED_MODEL,
    refusal: bool = False,
    response_present: bool = True,
) -> MockProviderResponseV1:
    if not response_present:
        return MockProviderResponseV1(
            response_present=False,
            outcome="timeout_before_response",
            status_code=None,
            model=None,
            content=None,
        )
    return MockProviderResponseV1(
        response_present=True,
        outcome="provider_refusal" if refusal else "successful_response",
        status_code=200,
        model=model,
        content=json.dumps(payload, separators=(",", ":")),
        refusal=refusal,
        finish_reason="stop",
        response_id="audit-response",
    )


def _independent_schema_accepts(payload: object) -> bool:
    return bool(
        isinstance(payload, dict)
        and set(payload) == {"fixture_id", "capability_token"}
        and type(payload["fixture_id"]) is str
        and type(payload["capability_token"]) is str
        and payload["fixture_id"] == "SYNTHETIC_CAPABILITY_CHECK"
        and payload["capability_token"] == "TASK039E3_STRICT_JSON_SCHEMA_V1"
    )


class IndependentRecoveryCapabilityAuditTests(unittest.TestCase):
    def test_prompt_and_schema_are_reconstructed_from_raw_bytes(self) -> None:
        committed_schema = json.loads(
            (
                ROOT
                / "schemas/v6/task039e3_recovery_capability_response_v1_schema.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(EXPECTED_PROMPT, RECOVERY_CAPABILITY_PROMPT_V1)
        self.assertEqual(
            sha256(EXPECTED_PROMPT.encode("utf-8")).hexdigest(),
            EXPECTED_PROMPT_HASH,
        )
        self.assertEqual(RECOVERY_CAPABILITY_PROMPT_SHA256, EXPECTED_PROMPT_HASH)
        self.assertEqual(committed_schema, EXPECTED_SCHEMA)
        self.assertEqual(thaw_json(RECOVERY_CAPABILITY_SCHEMA_V1), EXPECTED_SCHEMA)
        self.assertEqual(_canonical_hash(EXPECTED_SCHEMA), EXPECTED_SCHEMA_HASH)
        self.assertEqual(RECOVERY_CAPABILITY_SCHEMA_SHA256, EXPECTED_SCHEMA_HASH)

    def test_r0_checker_and_request_contract_hashes_derive_independently(self) -> None:
        protocol = json.loads(
            (ROOT / "docs/task_reports/TASK-039E3_R0_RECOVERY_PROTOCOL.json").read_text(
                encoding="utf-8"
            )
        )
        gate = protocol["corrected_capability_gate"]
        self.assertEqual(
            sha256(gate["checker_source_specification"].encode("utf-8")).hexdigest(),
            EXPECTED_CHECKER_HASH,
        )
        self.assertEqual(
            _canonical_hash(gate["request_builder_contract"]),
            EXPECTED_REQUEST_CONTRACT_HASH,
        )
        self.assertEqual(R0_CHECKER_SPEC_HASH, EXPECTED_CHECKER_HASH)
        self.assertEqual(
            R0_REQUEST_BUILDER_CONTRACT_HASH,
            EXPECTED_REQUEST_CONTRACT_HASH,
        )

    def test_actual_request_body_equals_independent_frozen_contract(self) -> None:
        request = build_recovery_capability_request_v1()
        body = thaw_json(request.request_body)
        expected_body = {
            "model": EXPECTED_MODEL,
            "messages": [{"role": "user", "content": EXPECTED_PROMPT}],
            "reasoning_effort": "none",
            "temperature": 0.7,
            "top_p": 1.0,
            "max_completion_tokens": 1024,
            "n": 1,
            "presence_penalty": 0,
            "frequency_penalty": 0,
            "stream": False,
            "store": False,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "task039e3_recovery_capability_response_v1",
                    "strict": True,
                    "schema": EXPECTED_SCHEMA,
                },
            },
        }
        self.assertEqual(body, expected_body)
        self.assertEqual(request.endpoint, "https://api.openai.com/v1/chat/completions")
        self.assertIsNone(request.system_prompt)
        self.assertIsNone(request.developer_prompt)
        for prohibited in (
            "seed",
            "tools",
            "tool_choice",
            "conversation",
            "previous_response_id",
            "model_alias",
            "fallback_model",
        ):
            self.assertNotIn(prohibited, body)

    def test_independent_decision_table_matches_pass_and_each_block_condition(self) -> None:
        valid = {
            "fixture_id": "SYNTHETIC_CAPABILITY_CHECK",
            "capability_token": "TASK039E3_STRICT_JSON_SCHEMA_V1",
        }
        cases = (
            ("pass", _response(valid), "PASS"),
            ("no_transport", _response(valid, response_present=False), "BLOCK"),
            ("wrong_model", _response(valid, model="unexpected-model"), "BLOCK"),
            ("refusal", _response(valid, refusal=True), "BLOCK"),
            ("wrong_fixture", _response({**valid, "fixture_id": "wrong"}), "BLOCK"),
            ("wrong_token", _response({**valid, "capability_token": "wrong"}), "BLOCK"),
            ("missing", _response({"fixture_id": valid["fixture_id"]}), "BLOCK"),
        )
        for name, response, expected in cases:
            with self.subTest(name=name):
                result = evaluate_recovery_capability_response_v1(response)
                self.assertEqual(result.gate_status, expected)
                parsed = json.loads(response.content) if response.content else None
                independent_pass = bool(
                    response.response_present
                    and response.status_code == 200
                    and response.model == EXPECTED_MODEL
                    and not response.refusal
                    and _independent_schema_accepts(parsed)
                )
                self.assertEqual(result.gate_status == "PASS", independent_pass)

    def test_malformed_json_blocks_without_schema_authority(self) -> None:
        response = MockProviderResponseV1(
            response_present=True,
            outcome="successful_response",
            status_code=200,
            model=EXPECTED_MODEL,
            content="{",
            response_id="audit-malformed",
        )
        result = evaluate_recovery_capability_response_v1(response)
        self.assertEqual(result.gate_status, "BLOCK")
        self.assertFalse(result.structured_parse_pass)
        self.assertFalse(result.schema_validation_pass)

    def test_self_report_fields_are_closed_schema_noise_not_authority(self) -> None:
        base = {
            "fixture_id": "SYNTHETIC_CAPABILITY_CHECK",
            "capability_token": "TASK039E3_STRICT_JSON_SCHEMA_V1",
        }
        for snapshot, supported in (
            (EXPECTED_MODEL, True),
            ("wrong-model", False),
            (EXPECTED_MODEL, False),
            ("wrong-model", True),
        ):
            payload = {
                **base,
                "model_snapshot": snapshot,
                "structured_output_supported": supported,
            }
            with self.subTest(snapshot=snapshot, supported=supported):
                self.assertFalse(_independent_schema_accepts(payload))
                result = evaluate_recovery_capability_response_v1(_response(payload))
                self.assertEqual(result.gate_status, "BLOCK")
                self.assertEqual(
                    result.failure_codes,
                    (
                        "schema_validation_failed",
                        "fixture_id_mismatch",
                        "capability_token_mismatch",
                    ),
                )

    def test_provider_metadata_cannot_be_overridden_by_model_self_report(self) -> None:
        payload = {
            "fixture_id": "SYNTHETIC_CAPABILITY_CHECK",
            "capability_token": "TASK039E3_STRICT_JSON_SCHEMA_V1",
            "model_snapshot": EXPECTED_MODEL,
            "structured_output_supported": True,
        }
        result = evaluate_recovery_capability_response_v1(
            _response(payload, model="unexpected-provider-model")
        )
        self.assertEqual(result.gate_status, "BLOCK")
        self.assertIn("returned_model_mismatch", result.failure_codes)
        self.assertEqual(
            result.provider_model_identity_source,
            "provider_response_metadata_only",
        )

    def test_gate_source_contains_no_self_report_lookup(self) -> None:
        source = inspect.getsource(evaluate_recovery_capability_response_v1)
        self.assertNotIn("model_snapshot", source)
        self.assertNotIn("structured_output_supported", source)
        self.assertIn("response.model", source)
        self.assertIn("response.refusal", source)


if __name__ == "__main__":
    unittest.main()
