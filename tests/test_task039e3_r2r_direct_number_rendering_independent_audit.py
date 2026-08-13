from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
from unittest.mock import patch
import unittest

from paperworks.v6.common import stable_hash_v1, thaw_json
from paperworks.v6.task039e2_execution_configuration_v1 import (
    CALIBRATED_NUMERIC_ROLES,
    DIRECT_NUMBER_PROVIDER_SCHEMA_V1,
    TASK039E2ConfigurationError,
    WINDOW_NUMERIC_ROLES,
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
from paperworks.v6.task039e3_orchestration_v1 import run_direct_number_v1
from paperworks.v6.task039e3_r2r_request_contract_v1 import (
    DIRECT_NUMBER_PROVIDER_SCHEMA_V1_HASH,
)
from task039e3_support import direct_number_payload, make_evidence


DIRECT_PROMPT_HASH = "fb01d8990ee3a7affe540dfdf3556b46d7bd744cd1e3a04d6fd9d79772dd2769"
DIRECT_SCHEMA_HASH = "b1b91bf27fd191da57984be625a2547e4e5ee96a0aca52535df071af92bfd6ca"


def _view(*, alias: bool, index: int) -> ConstructionInputViewV1:
    base = make_evidence(index).render_view()
    bindings = tuple(
        replace(item, evidence_identity=item.reference) for item in base.numeric_bindings
    ) if alias else base.numeric_bindings
    return ConstructionInputViewV1(
        relation_identity=base.relation_identity,
        source=base.source,
        source_step_direction=base.source_step_direction,
        target=base.target,
        target_response_direction=base.target_response_direction,
        selected_delay_horizon_seconds=base.selected_delay_horizon_seconds,
        numeric_bindings=bindings,
        approved_evidence_identities=tuple(item.evidence_identity for item in bindings),
        semantic_process_metadata=thaw_json(base.semantic_process_metadata),
    )


def _payload(view: ConstructionInputViewV1) -> tuple[str, dict[str, object]]:
    rendered = render_direct_number_model_content_v1(view.to_dict())
    content = rendered.split("\n\nDIRECT_NUMBER_INPUT_JSON\n", 1)[1]
    document = json.loads(content)
    if not isinstance(document, dict):
        raise AssertionError("direct payload must be an object")
    return rendered, document


class DirectNumberWithholdingIndependentAudit(unittest.TestCase):
    def test_alias_and_nonalias_structures_have_identical_withholding_policy(self) -> None:
        for alias in (True, False):
            with self.subTest(alias=alias):
                view = _view(alias=alias, index=11 if alias else 12)
                self.assertEqual(len(view.numeric_bindings), 10)
                if alias:
                    self.assertTrue(
                        all(item.evidence_identity == item.reference for item in view.numeric_bindings)
                    )
                else:
                    self.assertTrue(
                        all(item.evidence_identity != item.reference for item in view.numeric_bindings)
                    )
                request = build_direct_number_request_v1(view)
                rendered, payload = _payload(view)
                bindings = payload["numeric_bindings"]
                references = payload["numeric_references"]
                identities = payload["approved_evidence_identities"]
                self.assertEqual(len(bindings), 7)
                self.assertEqual(len(references), 7)
                self.assertEqual(len(identities), 7)
                self.assertEqual(
                    [item["numeric_role"] for item in bindings],
                    list(WINDOW_NUMERIC_ROLES),
                )
                self.assertEqual(set(references), set(WINDOW_NUMERIC_ROLES))
                self.assertEqual(
                    identities,
                    [
                        item.evidence_identity
                        for item in view.numeric_bindings
                        if item.numeric_role in WINDOW_NUMERIC_ROLES
                    ],
                )
                for item in view.numeric_bindings:
                    if item.numeric_role in CALIBRATED_NUMERIC_ROLES:
                        self.assertNotIn(item.reference, rendered)
                        self.assertNotIn(item.evidence_identity, rendered)
                self.assertEqual(request.purpose, "direct_number")

    def test_renderer_and_existing_request_guard_reject_residual_calibrated_data(self) -> None:
        for alias in (True, False):
            with self.subTest(alias=alias):
                view = _view(alias=alias, index=13 if alias else 14)
                calibrated = next(
                    item
                    for item in view.numeric_bindings
                    if item.numeric_role in CALIBRATED_NUMERIC_ROLES
                )
                document = view.to_dict()
                document["semantic_process_metadata"]["residual_probe"] = (
                    calibrated.evidence_identity
                )
                with self.assertRaisesRegex(
                    TASK039E2ConfigurationError,
                    "calibrated evidence leaked",
                ):
                    render_direct_number_model_content_v1(document)

        alias_view = _view(alias=True, index=15)
        calibrated_reference = next(
            item.reference
            for item in alias_view.numeric_bindings
            if item.numeric_role in CALIBRATED_NUMERIC_ROLES
        )
        rendered, payload = _payload(alias_view)
        payload["semantic_process_metadata"]["residual_probe"] = calibrated_reference
        unsafe = rendered.split("\n\nDIRECT_NUMBER_INPUT_JSON\n", 1)[0]
        unsafe += "\n\nDIRECT_NUMBER_INPUT_JSON\n" + json.dumps(
            payload,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        with patch(
            "paperworks.v6.task039e3_execution_prep_v1."
            "render_direct_number_model_content_v1",
            return_value=unsafe,
        ):
            with self.assertRaisesRegex(
                TASK039E3PreparationError,
                "direct-number calibrated reference leaked",
            ):
                render_direct_number_input_v1(alias_view)

    def test_frozen_contract_and_one_call_no_authority_outcome(self) -> None:
        view = _view(alias=True, index=16)
        request = build_direct_number_request_v1(view)
        body = thaw_json(request.request_body)
        self.assertEqual(DIRECT_NUMBER_PROMPT_HASH, DIRECT_PROMPT_HASH)
        self.assertEqual(FrozenE2ExecutionBindingV1().direct_number_prompt_hash, DIRECT_PROMPT_HASH)
        self.assertEqual(stable_hash_v1(DIRECT_NUMBER_PROVIDER_SCHEMA_V1), DIRECT_SCHEMA_HASH)
        self.assertEqual(DIRECT_NUMBER_PROVIDER_SCHEMA_V1_HASH, DIRECT_SCHEMA_HASH)
        self.assertEqual(request.provider_schema_hash, DIRECT_SCHEMA_HASH)
        self.assertEqual(body["model"], "gpt-5.4-2026-03-05")
        self.assertEqual(body["reasoning_effort"], "none")
        self.assertEqual(body["temperature"], 0.7)
        self.assertEqual(body["top_p"], 1.0)
        self.assertEqual(body["max_completion_tokens"], 1024)
        self.assertEqual(body["n"], 1)
        self.assertEqual(body["presence_penalty"], 0)
        self.assertEqual(body["frequency_penalty"], 0)
        self.assertFalse(body["stream"])
        self.assertFalse(body["store"])
        content = body["messages"][0]["content"]
        self.assertEqual(request.model_visible_content_hash, sha256(content.encode()).hexdigest())

        base_evidence = make_evidence(16)

        class AliasEvidence:
            relation = base_evidence.relation

            @staticmethod
            def render_view() -> ConstructionInputViewV1:
                return view

        evidence = AliasEvidence()
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
        self.assertEqual(len(ledger.records), 1)
        self.assertEqual(len(ledger.records[0].transport_attempts), 1)
        self.assertEqual(outcome.generation_calls_consumed, 1)
        self.assertFalse(outcome.validity_authority)
        self.assertFalse(outcome.runtime_authority)


if __name__ == "__main__":
    unittest.main()
