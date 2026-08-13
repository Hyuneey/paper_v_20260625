from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import inspect
import json
from pathlib import Path
import tempfile
from typing import Any
import unittest

from paperworks.v6.common import stable_hash_v1, thaw_json
from paperworks.v6.task039e2_execution_configuration_v1 import (
    CALIBRATED_NUMERIC_ROLES,
    WINDOW_NUMERIC_ROLES,
    DIRECT_NUMBER_PROVIDER_SCHEMA_V1,
    render_direct_number_model_content_v1,
)
from paperworks.v6.task039e3_execution_prep_v1 import (
    ConstructionInputViewV1,
    DIRECT_NUMBER_PROMPT_HASH,
    FrozenE2ExecutionBindingV1,
    MockProviderEventV1,
    MockProviderTransportV1,
    ProviderCallLedgerV1,
    TASK039E3PreparationError,
    build_direct_number_request_v1,
    render_direct_number_input_v1,
)
from paperworks.v6.task039e3_orchestration_v1 import (
    ConstructionOutcomeLedgerV1,
    ConstructionProposalLedgerV1,
    run_direct_number_v1,
)
from paperworks.v6.task039e3_r2r_execution_v1 import (
    HISTORICAL_ORIGINAL_R2_SCIENTIFIC_LOGICAL_CALLS,
    HISTORICAL_PARTIAL_R2R_SCIENTIFIC_LOGICAL_CALLS,
    HISTORICAL_SCIENTIFIC_LOGICAL_CALLS_TOTAL,
    HISTORICAL_ZERO_CONTACT_R2R_SCIENTIFIC_LOGICAL_CALLS,
    build_lifetime_accounting_v1,
    run_injected_r2r_scientific_cohort_v1,
)
from paperworks.v6.task039e3_r2r_request_contract_v1 import (
    DIRECT_NUMBER_PROVIDER_SCHEMA_V1_HASH,
    RECOVERY_MAIN_PROVIDER_SCHEMA_V2_HASH,
    build_r2r_main_request_v1,
    build_r2r_t2_followup_request_v1,
)
from paperworks.v6.task039e3_recovery_science_v2 import ScientificLedgersV2
from paperworks.v6.task039e3_recovery_transactional_custody_v3 import (
    TransactionalHashChainCustodyV3,
)
from task039e3_support import direct_number_payload, make_evidence, valid_core_document
from tests.test_task039e3_r2r_live_executor_remediation import (
    _DirectLedger,
    _provider_schema_hash,
    _success_transport,
    _transactional_ledger,
)


EXPECTED_DIRECT_PROMPT_HASH = (
    "fb01d8990ee3a7affe540dfdf3556b46d7bd744cd1e3a04d6fd9d79772dd2769"
)
EXPECTED_DIRECT_SCHEMA_HASH = (
    "b1b91bf27fd191da57984be625a2547e4e5ee96a0aca52535df071af92bfd6ca"
)


class RealE1AliasFaithfulEvidence:
    """Synthetic values with the exact real-E1 identity/reference topology."""

    def __init__(self, index: int) -> None:
        base = make_evidence(index)
        self.relation = base.relation
        self.numeric_evidence = base.numeric_evidence
        self.numeric_bindings = tuple(
            replace(binding, evidence_identity=binding.reference)
            for binding in base.numeric_bindings
        )
        self.approved_evidence_identities = tuple(
            binding.reference for binding in self.numeric_bindings
        )
        self.semantic_process_metadata = base.semantic_process_metadata

    def render_view(self) -> ConstructionInputViewV1:
        return ConstructionInputViewV1(
            relation_identity=self.relation.relation_identity,
            source=self.relation.source,
            source_step_direction=self.relation.source_step_direction,
            target=self.relation.target,
            target_response_direction=self.relation.target_response_direction,
            selected_delay_horizon_seconds=(
                self.relation.selected_delay_horizon_seconds
            ),
            numeric_bindings=self.numeric_bindings,
            approved_evidence_identities=self.approved_evidence_identities,
            semantic_process_metadata=self.semantic_process_metadata,
        )


def _direct_payload(view: ConstructionInputViewV1) -> dict[str, Any]:
    rendered = render_direct_number_model_content_v1(view.to_dict())
    marker = "\n\nDIRECT_NUMBER_INPUT_JSON\n"
    if marker not in rendered:
        raise AssertionError("direct-number marker differs")
    payload = json.loads(rendered.split(marker, 1)[1])
    if not isinstance(payload, dict):
        raise AssertionError("direct-number payload is not an object")
    return payload


class R2RDirectNumberRenderingRemediationTests(unittest.TestCase):
    def test_real_e1_alias_faithful_request_withholds_only_calibrated_evidence(self) -> None:
        evidence = RealE1AliasFaithfulEvidence(1)
        view = evidence.render_view()
        self.assertEqual(len(view.numeric_bindings), 10)
        self.assertTrue(
            all(item.evidence_identity == item.reference for item in view.numeric_bindings)
        )
        self.assertEqual(
            view.approved_evidence_identities,
            tuple(item.reference for item in view.numeric_bindings),
        )
        request = build_direct_number_request_v1(view)
        payload = _direct_payload(view)
        retained_bindings = payload["numeric_bindings"]
        retained_references = payload["numeric_references"]
        retained_identities = payload["approved_evidence_identities"]
        self.assertEqual(
            [item["numeric_role"] for item in retained_bindings],
            list(WINDOW_NUMERIC_ROLES),
        )
        self.assertEqual(set(retained_references), set(WINDOW_NUMERIC_ROLES))
        self.assertEqual(
            retained_identities,
            [
                item.evidence_identity
                for item in view.numeric_bindings
                if item.numeric_role in WINDOW_NUMERIC_ROLES
            ],
        )
        withheld = tuple(
            item
            for item in view.numeric_bindings
            if item.numeric_role in CALIBRATED_NUMERIC_ROLES
        )
        content = thaw_json(request.request_body)["messages"][0]["content"]
        for item in withheld:
            self.assertNotIn(item.reference, content)
            self.assertNotIn(item.evidence_identity, content)
            self.assertNotIn(str(item.value), content)
        self.assertEqual(request.purpose, "direct_number")
        self.assertEqual(request.provider_schema_hash, EXPECTED_DIRECT_SCHEMA_HASH)
        self.assertEqual(
            request.model_visible_content_hash,
            sha256(content.encode("utf-8")).hexdigest(),
        )
        body = thaw_json(request.request_body)
        self.assertEqual(body["model"], "gpt-5.4-2026-03-05")
        self.assertEqual(
            {key: body[key] for key in ("temperature", "top_p", "max_completion_tokens")},
            {"temperature": 0.7, "top_p": 1.0, "max_completion_tokens": 1024},
        )

    def test_distinct_calibrated_evidence_identities_are_also_withheld(self) -> None:
        evidence = make_evidence(2)
        view = evidence.render_view()
        payload = _direct_payload(view)
        retained = payload["approved_evidence_identities"]
        calibrated = {
            item.evidence_identity
            for item in view.numeric_bindings
            if item.numeric_role in CALIBRATED_NUMERIC_ROLES
        }
        window = [
            item.evidence_identity
            for item in view.numeric_bindings
            if item.numeric_role in WINDOW_NUMERIC_ROLES
        ]
        self.assertTrue(calibrated.isdisjoint(retained))
        self.assertEqual(retained, window)

    def test_existing_calibrated_reference_guard_remains_active(self) -> None:
        evidence = RealE1AliasFaithfulEvidence(3)
        view = evidence.render_view()
        reference = next(
            item.reference
            for item in view.numeric_bindings
            if item.numeric_role in CALIBRATED_NUMERIC_ROLES
        )
        safe_rendered = render_direct_number_model_content_v1(view.to_dict())
        marker = "\n\nDIRECT_NUMBER_INPUT_JSON\n"
        prefix, payload_text = safe_rendered.split(marker, 1)
        payload = json.loads(payload_text)
        payload["semantic_process_metadata"]["synthetic_guard_probe"] = reference
        injected = prefix + marker + json.dumps(
            payload, ensure_ascii=True, allow_nan=False, sort_keys=True, separators=(",", ":")
        )
        from unittest.mock import patch

        with patch(
            "paperworks.v6.task039e3_execution_prep_v1.render_direct_number_model_content_v1",
            return_value=injected,
        ):
            with self.assertRaisesRegex(
                TASK039E3PreparationError,
                "direct-number calibrated reference leaked",
            ):
                render_direct_number_input_v1(view)
        self.assertIn(
            "direct-number calibrated reference leaked",
            inspect.getsource(render_direct_number_input_v1),
        )

    def test_full_direct_number_offline_execution_uses_one_call(self) -> None:
        evidence = RealE1AliasFaithfulEvidence(4)
        transport = MockProviderTransportV1(
            (MockProviderEventV1("valid_direct_number", direct_number_payload()),)
        )
        ledger = ProviderCallLedgerV1()
        outcome = run_direct_number_v1(
            relation_schedule_index=0,
            evidence=evidence,
            transport=transport,
            call_ledger=ledger,
        )
        self.assertEqual(transport.calls, 1)
        self.assertEqual(len(transport.request_hashes), 1)
        self.assertEqual(len(ledger.records), 1)
        self.assertEqual(len(ledger.records[0].transport_attempts), 1)
        self.assertEqual(outcome.generation_calls_consumed, 1)
        self.assertFalse(outcome.validity_authority)
        self.assertFalse(outcome.runtime_authority)

    def test_main_and_t2_contracts_and_direct_prompt_schema_remain_frozen(self) -> None:
        evidence = RealE1AliasFaithfulEvidence(5)
        view = evidence.render_view()
        main = build_r2r_main_request_v1(view)
        followup = build_r2r_t2_followup_request_v1(
            view=view,
            verifier_issue_codes=("SYNTHETIC_ISSUE",),
            affected_fields=("source",),
            previous_proposal_hash="a" * 64,
            retrieved_evidence=None,
        )
        self.assertEqual(main.provider_schema_hash, RECOVERY_MAIN_PROVIDER_SCHEMA_V2_HASH)
        self.assertEqual(followup.provider_schema_hash, RECOVERY_MAIN_PROVIDER_SCHEMA_V2_HASH)
        self.assertEqual(DIRECT_NUMBER_PROMPT_HASH, EXPECTED_DIRECT_PROMPT_HASH)
        self.assertEqual(FrozenE2ExecutionBindingV1().direct_number_prompt_hash, EXPECTED_DIRECT_PROMPT_HASH)
        self.assertEqual(stable_hash_v1(DIRECT_NUMBER_PROVIDER_SCHEMA_V1), EXPECTED_DIRECT_SCHEMA_HASH)
        self.assertEqual(DIRECT_NUMBER_PROVIDER_SCHEMA_V1_HASH, EXPECTED_DIRECT_SCHEMA_HASH)
        main_content = thaw_json(main.request_body)["messages"][0]["content"]
        for binding in view.numeric_bindings:
            self.assertIn(binding.evidence_identity, main_content)

    def test_lifetime_accounting_rolls_all_failed_runs_forward(self) -> None:
        self.assertEqual(HISTORICAL_ORIGINAL_R2_SCIENTIFIC_LOGICAL_CALLS, 1)
        self.assertEqual(HISTORICAL_ZERO_CONTACT_R2R_SCIENTIFIC_LOGICAL_CALLS, 0)
        self.assertEqual(HISTORICAL_PARTIAL_R2R_SCIENTIFIC_LOGICAL_CALLS, 5)
        self.assertEqual(HISTORICAL_SCIENTIFIC_LOGICAL_CALLS_TOTAL, 6)
        low = build_lifetime_accounting_v1(252)
        high = build_lifetime_accounting_v1(336)
        self.assertEqual(low.recovery_cohort_scientific_logical_calls, 252)
        self.assertEqual(high.recovery_cohort_scientific_logical_calls, 336)
        self.assertEqual(low.lifetime_scientific_logical_call_attempts, 258)
        self.assertEqual(high.lifetime_scientific_logical_call_attempts, 342)

    def test_full_42_relation_real_alias_faithful_offline_cohort(self) -> None:
        evidence_records = tuple(
            RealE1AliasFaithfulEvidence(index) for index in range(1, 43)
        )
        payloads: list[object] = []
        for evidence in evidence_records:
            payloads.extend(valid_core_document(evidence) for _ in range(5))
            payloads.append(direct_number_payload())
        guarded, raw, opener, delays, checks = _success_transport(payloads)
        proposal = ConstructionProposalLedgerV1()
        outcome = ConstructionOutcomeLedgerV1()
        direct = _DirectLedger()
        with tempfile.TemporaryDirectory() as temporary:
            provider, custody = _transactional_ledger(Path(temporary), guarded)
            result = run_injected_r2r_scientific_cohort_v1(
                relation_identities=tuple(
                    item.relation.relation_identity for item in evidence_records
                ),
                evidence_records=evidence_records,
                transport=guarded,
                ledgers=ScientificLedgersV2(provider, proposal, outcome, direct),
                progress=lambda _message: None,
            )
            reconstructed = custody.reconstruct()
        self.assertEqual(result.relation_count, 42)
        self.assertEqual(result.t0_outcomes, 42)
        self.assertEqual(result.t1_logical_calls, 42)
        self.assertEqual(result.t1b_logical_calls, 126)
        self.assertEqual(result.t2_logical_calls, 42)
        self.assertEqual(result.direct_number_logical_calls, 42)
        self.assertEqual(result.scientific_logical_calls, 252)
        self.assertEqual((raw.calls, opener.calls, len(checks)), (252, 252, 252))
        self.assertEqual((len(proposal.records), len(outcome.records), len(direct.records)), (252, 168, 42))
        self.assertEqual(reconstructed.authoritative_record_count, 252)
        self.assertFalse(reconstructed.orphan_record_hashes)
        self.assertFalse(reconstructed.pending_files)
        self.assertEqual(delays, [])
        for offset in range(0, 252, 6):
            self.assertTrue(
                all(
                    _provider_schema_hash(body) == RECOVERY_MAIN_PROVIDER_SCHEMA_V2_HASH
                    for body in opener.request_bodies[offset : offset + 5]
                )
            )
            direct_body = opener.request_bodies[offset + 5]
            self.assertEqual(_provider_schema_hash(direct_body), EXPECTED_DIRECT_SCHEMA_HASH)
            direct_content = direct_body["messages"][0]["content"]
            evidence = evidence_records[offset // 6]
            for binding in evidence.numeric_bindings:
                if binding.numeric_role in CALIBRATED_NUMERIC_ROLES:
                    self.assertNotIn(binding.reference, direct_content)
                    self.assertNotIn(binding.evidence_identity, direct_content)
        self.assertEqual(build_lifetime_accounting_v1(252).lifetime_scientific_logical_call_attempts, 258)


if __name__ == "__main__":
    unittest.main()
