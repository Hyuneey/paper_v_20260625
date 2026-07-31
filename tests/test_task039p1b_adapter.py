from __future__ import annotations

import copy
import unittest

from paperworks.v6.adapters_v1 import (
    V6EvidenceAdapterResultV1,
    V6EvidenceAdapterStatusV1,
    adapt_serialized_legacy_relation_evidence_v1,
)
from tests.task039p1b_support import legacy_sources


class LegacyEvidenceAdapterTests(unittest.TestCase):
    def test_complete_synthetic_conversion(self) -> None:
        profile, pack, context = legacy_sources()
        result = adapt_serialized_legacy_relation_evidence_v1(
            profile, pack, external_context=context
        )
        self.assertEqual(result.status, V6EvidenceAdapterStatusV1.CREATED)
        self.assertIsNotNone(result.artifact)
        self.assertFalse(result.rule_validity_granted)
        self.assertFalse(result.runtime_authority_granted)
        repeated = adapt_serialized_legacy_relation_evidence_v1(
            profile, pack, external_context=context
        )
        self.assertEqual(result.artifact_hash, repeated.artifact_hash)
        self.assertEqual(
            V6EvidenceAdapterResultV1.from_json(result.to_json()).artifact_hash,
            result.artifact_hash,
        )

    def test_missing_external_context_is_pending(self) -> None:
        profile, pack, context = legacy_sources()
        del context["process_scope"]
        result = adapt_serialized_legacy_relation_evidence_v1(
            profile, pack, external_context=context
        )
        self.assertEqual(result.status, V6EvidenceAdapterStatusV1.PENDING_CONTEXT)
        self.assertIsNone(result.artifact)
        self.assertIsNone(result.target_artifact_hash)

    def test_incorrect_artifact_type_is_invalid(self) -> None:
        profile, pack, context = legacy_sources()
        profile["artifact_type"] = "unexpected"
        result = adapt_serialized_legacy_relation_evidence_v1(
            profile, pack, external_context=context
        )
        self.assertEqual(result.status, V6EvidenceAdapterStatusV1.INVALID_SOURCE)

    def test_unsupported_relation_and_wrong_split(self) -> None:
        for mutation in ("relation", "split"):
            profile, pack, context = legacy_sources()
            if mutation == "relation":
                profile["relation_type"] = "correlation"
            else:
                profile["split_name"] = "validation"
            result = adapt_serialized_legacy_relation_evidence_v1(
                profile, pack, external_context=context
            )
            with self.subTest(mutation=mutation):
                self.assertEqual(
                    result.status, V6EvidenceAdapterStatusV1.UNSUPPORTED_SOURCE
                )

    def test_wrong_target_role_is_unsupported(self) -> None:
        profile, pack, context = legacy_sources()
        context["target_split_role"] = "inner_utility"
        result = adapt_serialized_legacy_relation_evidence_v1(
            profile, pack, external_context=context
        )
        self.assertEqual(result.status, V6EvidenceAdapterStatusV1.UNSUPPORTED_SOURCE)

    def test_raw_events_and_numeric_parameters_are_not_copied(self) -> None:
        profile, pack, context = legacy_sources()
        profile["trigger_events"] = object()
        profile["response_events"] = object()
        result = adapt_serialized_legacy_relation_evidence_v1(
            profile, pack, external_context=context
        )
        self.assertEqual(result.status, V6EvidenceAdapterStatusV1.CREATED)
        target = result.artifact.to_dict() if result.artifact else {}
        serialized = str(target)
        self.assertNotIn("trigger_events", serialized)
        self.assertNotIn("response_events", serialized)
        self.assertNotIn("calibrated_parameters", serialized)

    def test_information_loss_is_explicit(self) -> None:
        profile, pack, context = legacy_sources()
        result = adapt_serialized_legacy_relation_evidence_v1(
            profile, pack, external_context=context
        )
        self.assertIn("legacy_trigger_events_not_copied", result.information_loss)
        self.assertIn("legacy_lag_p95_unavailable", result.information_loss)
        self.assertIn("legacy_magnitude_unit_unverified", result.information_loss)

    def test_source_mappings_are_not_mutated(self) -> None:
        profile, pack, context = legacy_sources()
        originals = copy.deepcopy((profile, pack, context))
        adapt_serialized_legacy_relation_evidence_v1(
            profile, pack, external_context=context
        )
        self.assertEqual((profile, pack, context), originals)

    def test_invalid_aggregate_emits_no_partial_target(self) -> None:
        profile, pack, context = legacy_sources()
        pack["support_counts"]["trigger_count"] = 999
        result = adapt_serialized_legacy_relation_evidence_v1(
            profile, pack, external_context=context
        )
        self.assertEqual(result.status, V6EvidenceAdapterStatusV1.INVALID_SOURCE)
        self.assertIsNone(result.target_artifact_type)
        self.assertIsNone(result.target_evidence_id)
        self.assertIsNone(result.target_artifact_hash)


if __name__ == "__main__":
    unittest.main()
