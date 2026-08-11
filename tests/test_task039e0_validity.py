from __future__ import annotations

import copy
import unittest

from paperworks.v6.task039e0_rule_construction_prep_v1 import (
    MAIN_NUMERIC_ORIGIN,
)
from paperworks.v6.task039e0_validity_v1 import (
    ValidityIssueCodeV1,
    verify_prepared_rule_proposal_v1,
)
from paperworks.v6.outcomes_v1 import ConstructionArmV1
from tests.task039e0_support import (
    rehash_proposal,
    synthetic_proposal,
    synthetic_provenance,
)


def _verify(fixture, proposal=None, **overrides):
    document, relation, evidence, budget, provenance = fixture
    values = {
        "relation": relation,
        "numeric_evidence": evidence,
        "provenance": provenance,
        "budget": budget,
        "allowed_variables": frozenset({relation.source, relation.target}),
    }
    values.update(overrides)
    return verify_prepared_rule_proposal_v1(
        document if proposal is None else proposal, **values
    )


def _codes(result):
    return {item.code for item in result.issues}


class PreparedValidityVerifierTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = synthetic_proposal()

    def _mutate(self, field, value, *, rehash=True):
        proposal = copy.deepcopy(self.fixture[0])
        proposal[field] = value
        if rehash:
            rehash_proposal(proposal)
        return proposal

    def test_calibrated_t0_proposal_is_admissible(self) -> None:
        result = _verify(self.fixture)
        self.assertEqual(result.status, "admissible")
        self.assertEqual(result.issues, ())
        self.assertFalse(result.validity_authority_granted)
        self.assertFalse(result.runtime_authority_granted)

    def test_valid_constrained_t1_proposal_envelope(self) -> None:
        fixture = synthetic_proposal(arm=ConstructionArmV1.T1)
        result = _verify(fixture)
        self.assertEqual(result.status, "admissible")
        self.assertEqual(fixture[0]["numeric_origin"], MAIN_NUMERIC_ORIGIN)

    def test_unapproved_numeric_literal_is_rejected(self) -> None:
        result = _verify(
            self.fixture,
            self._mutate("numeric_literals", [0.12345]),
        )
        self.assertIn(
            ValidityIssueCodeV1.UNAPPROVED_NUMERIC_LITERAL, _codes(result)
        )

    def test_wrong_source_and_target_are_rejected(self) -> None:
        source_result = _verify(
            self.fixture,
            self._mutate("source", "SYNTH_UNAPPROVED_SOURCE"),
        )
        self.assertIn(
            ValidityIssueCodeV1.SOURCE_BINDING_MISMATCH,
            _codes(source_result),
        )
        self.assertIn(ValidityIssueCodeV1.SOURCE_NOT_ALLOWED, _codes(source_result))

        target_result = _verify(
            self.fixture,
            self._mutate("target", "SYNTH_UNAPPROVED_TARGET"),
        )
        self.assertIn(
            ValidityIssueCodeV1.TARGET_BINDING_MISMATCH,
            _codes(target_result),
        )
        self.assertIn(ValidityIssueCodeV1.TARGET_NOT_ALLOWED, _codes(target_result))

    def test_wrong_source_direction_target_direction_and_horizon_are_rejected(self) -> None:
        cases = (
            (
                "source_step_direction",
                "step_down",
                ValidityIssueCodeV1.SOURCE_DIRECTION_MISMATCH,
            ),
            (
                "target_response_direction",
                "decrease",
                ValidityIssueCodeV1.TARGET_DIRECTION_MISMATCH,
            ),
            (
                "selected_delay_horizon_seconds",
                10,
                ValidityIssueCodeV1.HORIZON_MISMATCH,
            ),
        )
        for field, value, code in cases:
            with self.subTest(field=field):
                result = _verify(self.fixture, self._mutate(field, value))
                self.assertIn(code, _codes(result))

    def test_malformed_dsl_is_rejected(self) -> None:
        proposal = copy.deepcopy(self.fixture[0])
        del proposal["runtime_logic"]
        result = _verify(self.fixture, proposal)
        self.assertEqual(result.status, "rejected")
        self.assertIn(ValidityIssueCodeV1.MALFORMED_DSL, _codes(result))

    def test_unsupported_variable_is_rejected(self) -> None:
        result = _verify(
            self.fixture,
            self._mutate(
                "variables",
                ["SYNTH_ACTUATOR_A", "SYNTH_SENSOR_B", "SYNTH_HIDDEN_C"],
            ),
        )
        self.assertIn(ValidityIssueCodeV1.UNSUPPORTED_VARIABLE, _codes(result))

    def test_free_text_runtime_logic_and_prohibited_data_reference_are_rejected(self) -> None:
        free_text = _verify(
            self.fixture,
            self._mutate("free_text_runtime_logic", "execute arbitrary logic"),
        )
        self.assertIn(ValidityIssueCodeV1.FREE_TEXT_RUNTIME_LOGIC, _codes(free_text))
        prohibited = _verify(
            self.fixture,
            self._mutate("prohibited_data_references", ["labels"]),
        )
        self.assertIn(
            ValidityIssueCodeV1.PROHIBITED_DATA_REFERENCE,
            _codes(prohibited),
        )

    def test_wrong_numeric_reference_and_origin_are_rejected(self) -> None:
        wrong_ref = _verify(
            self.fixture,
            self._mutate("source_threshold_reference", "f" * 64),
        )
        self.assertIn(
            ValidityIssueCodeV1.NUMERIC_REFERENCE_MISMATCH, _codes(wrong_ref)
        )
        wrong_origin = _verify(
            self.fixture,
            self._mutate("numeric_origin", "llm_direct_number_ablation"),
        )
        self.assertIn(
            ValidityIssueCodeV1.NUMERIC_ORIGIN_UNAPPROVED,
            _codes(wrong_origin),
        )

    def test_label_and_utility_inputs_are_rejected_without_being_used(self) -> None:
        label_result = _verify(self.fixture, label_input=object())
        self.assertIn(
            ValidityIssueCodeV1.LABEL_INPUT_PROHIBITED, _codes(label_result)
        )
        self.assertFalse(label_result.label_input_used)
        utility_result = _verify(self.fixture, utility_input=object())
        self.assertIn(
            ValidityIssueCodeV1.UTILITY_INPUT_PROHIBITED,
            _codes(utility_result),
        )
        self.assertFalse(utility_result.utility_input_used)

    def test_deterministic_verifier_replay(self) -> None:
        first = _verify(self.fixture)
        second = _verify(self.fixture)
        self.assertEqual(first, second)
        self.assertEqual(first.artifact_hash, second.artifact_hash)
        self.assertEqual(first.to_dict(), second.to_dict())

    def test_serialization_and_authority_preclaims_are_rejected(self) -> None:
        stale = self._mutate("target", "SYNTH_SENSOR_B", rehash=False)
        stale["proposal_hash"] = "0" * 64
        result = _verify(self.fixture, stale)
        self.assertIn(
            ValidityIssueCodeV1.SERIALIZATION_HASH_MISMATCH, _codes(result)
        )
        authority = _verify(
            self.fixture,
            self._mutate("runtime_authority_granted", True),
        )
        self.assertIn(ValidityIssueCodeV1.AUTHORITY_PRECLAIMED, _codes(authority))

    def test_wrong_arm_protocol_provenance_is_rejected(self) -> None:
        proposal, relation, evidence, budget, _ = self.fixture
        invalid_provenance = synthetic_provenance(
            arm=ConstructionArmV1.T0,
            evidence=evidence,
            budget=budget,
            arm_protocol_hash="f" * 64,
        )
        document = copy.deepcopy(proposal)
        document["construction_provenance_hash"] = invalid_provenance.artifact_hash
        rehash_proposal(document)
        result = _verify(
            self.fixture,
            document,
            provenance=invalid_provenance,
        )
        self.assertIn(
            ValidityIssueCodeV1.CONSTRUCTION_PROVENANCE_INVALID,
            _codes(result),
        )


if __name__ == "__main__":
    unittest.main()
