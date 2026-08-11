from __future__ import annotations

import copy
import unittest

from paperworks.v6.task039e1_final_audit_v1 import (
    NUMERIC_ROLE_ORDER,
    TASK039E1FinalAuditError,
    WINDOW_BUNDLE_HASH,
    independent_numeric_binding_v1,
    independent_resolve_reference_v1,
    verify_self_hash_v1,
    window_bundle_v1,
    with_hash_v1,
)


HASHES = [f"{index:064x}" for index in range(1, 7)]


def _binding(role: str = "source_step_threshold") -> dict:
    return independent_numeric_binding_v1(
        relation_identity="P1_FCV01D:step_up:P1_FT01:increase",
        numeric_role=role,
        numeric_value=2.5,
        source_parameter_record_hash=HASHES[0],
        target_parameter_record_hash=HASHES[1],
        d1_fit_evidence_hash=HASHES[2],
        d2_confirmation_evidence_hash=HASHES[3],
        window_constant_bundle_hash=HASHES[4],
    )


def _private(binding: dict) -> dict:
    return with_hash_v1(
        {
            "schema_version": "1.0.0",
            "artifact_type": "task039e1_real_private_construction_evidence_v1",
            "relation_binding_hash": HASHES[5],
            "relation_identity": binding["relation_identity"],
            "numeric_bindings": [binding],
            "construction_evidence_status": "approved",
        }
    )


class IndependentAuditOracleTests(unittest.TestCase):
    def test_window_bundle_is_independently_reproduced(self) -> None:
        window = window_bundle_v1()
        self.assertEqual(WINDOW_BUNDLE_HASH, window["artifact_hash"])
        self.assertEqual(5, window["source_pre_window_seconds"])
        self.assertEqual(3, window["target_response_window_seconds"])
        verify_self_hash_v1(window, expected_hash=WINDOW_BUNDLE_HASH)

    def test_exact_real_role_order_is_frozen(self) -> None:
        self.assertEqual(11, len(NUMERIC_ROLE_ORDER))
        self.assertEqual("selected_delay_horizon_seconds", NUMERIC_ROLE_ORDER[3])
        self.assertEqual("target_response_window_seconds", NUMERIC_ROLE_ORDER[-1])

    def test_numeric_reference_binds_value_and_all_provenance(self) -> None:
        reference = _binding()["numeric_reference"]
        self.assertEqual(reference, _binding()["numeric_reference"])
        changed = independent_numeric_binding_v1(
            relation_identity="P1_FCV01D:step_up:P1_FT01:increase",
            numeric_role="source_step_threshold",
            numeric_value=2.5000001,
            source_parameter_record_hash=HASHES[0],
            target_parameter_record_hash=HASHES[1],
            d1_fit_evidence_hash=HASHES[2],
            d2_confirmation_evidence_hash=HASHES[3],
            window_constant_bundle_hash=HASHES[4],
        )
        self.assertNotEqual(reference, changed["numeric_reference"])

    def test_resolver_positive_and_all_required_negative_guards(self) -> None:
        binding = _binding()
        private = _private(binding)
        common = {
            "proposal_numeric_reference": binding["numeric_reference"],
            "relation_binding_hash": private["relation_binding_hash"],
            "numeric_role": binding["numeric_role"],
            "private_evidence_record_hash": private["artifact_hash"],
            "private_evidence": private,
        }
        resolved = independent_resolve_reference_v1(**common)
        self.assertEqual(2.5, resolved["numeric_value"])
        self.assertFalse(resolved["runtime_authority"])
        for mutation in (
            {"relation_binding_hash": "0" * 64},
            {"numeric_role": "target_noise_scale"},
            {"proposal_numeric_reference": "0" * 64},
            {"private_evidence_record_hash": "0" * 64},
        ):
            with self.subTest(mutation=mutation):
                with self.assertRaises(TASK039E1FinalAuditError):
                    independent_resolve_reference_v1(**{**common, **mutation})
        unapproved = copy.deepcopy(private)
        unapproved["construction_evidence_status"] = "rejected"
        with self.assertRaises(TASK039E1FinalAuditError):
            independent_resolve_reference_v1(
                **{**common, "private_evidence": unapproved}
            )


if __name__ == "__main__":
    unittest.main()
