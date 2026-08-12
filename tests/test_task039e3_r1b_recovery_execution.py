from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_execution_prep_v1 import (
    EXACT_MODEL,
    FrozenProviderRequestV1,
    MockProviderResponseV1,
    MockProviderTransportV1,
)
from paperworks.v6.task039e3_recovery_capability_v1 import (
    RECOVERY_CAPABILITY_FIXTURE_ID,
    RECOVERY_CAPABILITY_TOKEN,
    build_recovery_capability_request_v1,
)
from paperworks.v6.task039e3_recovery_execution_v1 import (
    RecoveryCapabilityCustodyBindingV1,
    RecoveryScientificCompatibilityTransportV1,
    build_recovery_capability_receipt_v1,
    build_recovery_run_identity_v1,
    execute_recovery_probe_v1,
    load_prior_authority_state_v1,
    run_recovery_capability_phase_v1,
    write_recovery_capability_private_custody_v1,
)


class _ScriptedTransport(MockProviderTransportV1):
    def __init__(self, responses: list[MockProviderResponseV1]) -> None:
        self.responses = list(responses)
        self.index = 0

    def send(self, _request: FrozenProviderRequestV1) -> MockProviderResponseV1:
        response = self.responses[self.index]
        self.index += 1
        return response


def _response(*, token: str = RECOVERY_CAPABILITY_TOKEN) -> MockProviderResponseV1:
    return MockProviderResponseV1(
        response_present=True,
        outcome="successful_response",
        status_code=200,
        model=EXACT_MODEL,
        content=json.dumps(
            {
                "fixture_id": RECOVERY_CAPABILITY_FIXTURE_ID,
                "capability_token": token,
            }
        ),
        finish_reason="stop",
        response_id="SYNTHETIC_RESPONSE",
        token_usage={"total_tokens": 2},
    )


class RecoveryExecutionTests(unittest.TestCase):
    def test_committed_r0_and_r1a_authority_artifacts_verify(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        state = load_prior_authority_state_v1(repository)
        self.assertEqual(state.r0_commit, "d5164aa93cc4c3efb6a343e0890b554f436a7e39")
        self.assertEqual(state.r1a_commit, "260b91be463815bc5bb453ca2cc05cec741aacc3")

    def test_transport_retries_do_not_allocate_another_logical_probe(self) -> None:
        timeout = MockProviderResponseV1(
            False, "timeout_before_response", None, None, None
        )
        execution = execute_recovery_probe_v1(
            _ScriptedTransport([timeout, _response()])
        )
        self.assertEqual(execution.transport_attempts, 2)
        self.assertEqual(execution.transport_retries, 1)
        self.assertEqual(execution.accounting.current_recovery_probe_count, 1)
        self.assertEqual(execution.accounting.cumulative_probe_count, 2)
        self.assertEqual(execution.gate.gate_status, "PASS")

    def test_nonretryable_model_mismatch_is_terminal(self) -> None:
        mismatch = MockProviderResponseV1(
            True,
            "successful_response",
            200,
            "gpt-other",
            _response().content,
            finish_reason="stop",
            response_id="SYNTHETIC_MISMATCH",
        )
        transport = _ScriptedTransport([mismatch, _response()])
        execution = execute_recovery_probe_v1(transport)
        self.assertEqual(execution.transport_attempts, 1)
        self.assertEqual(execution.gate.gate_status, "BLOCK")
        self.assertEqual(transport.index, 1)

    def test_capability_phase_orders_custody_before_e1(self) -> None:
        events: list[str] = []
        gate = execute_recovery_probe_v1(_ScriptedTransport([_response()])).gate
        result = run_recovery_capability_phase_v1(
            precontact_guard_runner=lambda: events.append("guards") or "bootstrap",
            probe_executor=lambda value: events.append(f"probe:{value}") or gate,
            custody_writer=lambda value: events.append(f"custody:{value.gate_status}") or "hash",
            e1_loader=lambda value: events.append(f"e1:{value}") or "evidence",
        )
        self.assertEqual(events, ["guards", "probe:bootstrap", "custody:PASS", "e1:bootstrap"])
        self.assertTrue(result.e1_loaded)

    def test_capability_block_never_loads_e1(self) -> None:
        events: list[str] = []
        gate = execute_recovery_probe_v1(
            _ScriptedTransport([_response(token="WRONG")])
        ).gate
        result = run_recovery_capability_phase_v1(
            precontact_guard_runner=lambda: "bootstrap",
            probe_executor=lambda _value: gate,
            custody_writer=lambda _value: events.append("custody") or "hash",
            e1_loader=lambda _value: events.append("e1"),
        )
        self.assertEqual(result.gate_status, "BLOCK")
        self.assertEqual(events, ["custody"])

    def test_recovery_receipt_and_run_identity_are_sanitized(self) -> None:
        execution = execute_recovery_probe_v1(_ScriptedTransport([_response()]))
        identity = build_recovery_run_identity_v1(
            r1b_commit="a" * 40,
            source_manifest_hash="b" * 64,
            r2_authorization_hash="c" * 64,
        )
        receipt = build_recovery_capability_receipt_v1(
            run_identity=identity,
            execution_commit="a" * 40,
            source_manifest_hash="b" * 64,
            r2_authorization_hash="c" * 64,
            execution=execution,
            custody_binding=RecoveryCapabilityCustodyBindingV1(
                provider_ledger_hash="d" * 64,
                provider_ledger_head_hash="e" * 64,
            ),
        )
        self.assertEqual(receipt["gate_status"], "PASS")
        self.assertEqual(receipt["current_recovery_probe_count"], 1)
        self.assertEqual(
            receipt["artifact_hash"],
            stable_hash_v1({k: v for k, v in receipt.items() if k != "artifact_hash"}),
        )
        serialized = json.dumps(receipt)
        self.assertNotIn("Authorization", serialized)
        self.assertNotIn("api_key", serialized.lower())

    def test_corrected_probe_private_custody_is_one_hash_chained_record(self) -> None:
        execution = execute_recovery_probe_v1(_ScriptedTransport([_response()]))
        with tempfile.TemporaryDirectory() as temporary:
            binding = write_recovery_capability_private_custody_v1(
                recovery_private_root=Path(temporary),
                run_identity="f" * 64,
                execution=execution,
            )
            lines = (
                Path(temporary) / "recovery_capability_provider_calls.jsonl"
            ).read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 1)
            record = json.loads(lines[0])
            self.assertEqual(record["record_hash"], binding.provider_ledger_head_hash)
            self.assertIsNone(record["previous_record_hash"])
            provider_record = record["provider_record"]
            self.assertFalse(provider_record["slot"]["scientific"])
            self.assertFalse(provider_record["api_key_stored"])
            self.assertFalse(provider_record["chain_of_thought_stored"])

    def test_compatibility_bridge_is_local_then_delegates(self) -> None:
        delegate = _ScriptedTransport([_response()])
        bridge = RecoveryScientificCompatibilityTransportV1(
            delegate=delegate,  # type: ignore[arg-type]
            recovery_response=_response(),
        )
        request = build_recovery_capability_request_v1()
        local = bridge.send(request)
        self.assertEqual(delegate.index, 0)
        self.assertIn("structured_output_supported", local.content or "")
        bridge.send(request)
        self.assertEqual(delegate.index, 1)

    def test_runner_has_one_deferred_credential_lookup(self) -> None:
        root = Path(__file__).resolve().parents[1]
        text = (root / "scripts/run_task039e3_recovery_execution.py").read_text(
            encoding="utf-8"
        )
        self.assertEqual(text.count('os.environ.get("OPENAI_API_KEY")'), 1)
        self.assertLess(
            text.index("run_ordered_precontact_guards_v1"),
            text.index('os.environ.get("OPENAI_API_KEY")'),
        )


if __name__ == "__main__":
    unittest.main()
