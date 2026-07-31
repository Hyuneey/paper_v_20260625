from __future__ import annotations

import dataclasses
import unittest

from paperworks.contracts.canonical_collection_v1 import (
    CanonicalContextMappingsV1,
    build_canonical_delayed_response_context_v1,
)
from paperworks.v6.normal_evidence_v1 import (
    DistributionSummaryV1,
    EvidenceStatusV1,
    RelationStabilitySummaryV1,
    ResponseDirectionV1,
    StabilityStatusV1,
)

from task039p1b_support import creation_metadata
from task039p1c_support import (
    SUBSYSTEM,
    build_canonical_fixture,
)


class Task039P1CCanonicalContextTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = build_canonical_fixture()

    def build(self, **changes):
        values = {
            "dataset_manifest": self.fixture.dataset,
            "data_view": self.fixture.view,
            "split_manifest": self.fixture.split,
            "normal_evidence": self.fixture.normal_evidence,
            "graph": self.fixture.graph,
            "parameters": self.fixture.parameters,
            "mappings": self.fixture.mappings,
            "subsystem": SUBSYSTEM,
            "binding_policy": self.fixture.build_result.collection
            and self._policy(),
            "creation_metadata": creation_metadata(),
        }
        values.update(changes)
        return build_canonical_delayed_response_context_v1(**values)

    def _policy(self):
        from paperworks.contracts.canonical_collection_v1 import (
            CanonicalBindingPolicyV1,
        )

        return CanonicalBindingPolicyV1(
            matching_policy_id="MATCH-V6-SYNTHETIC",
            matching_policy_version="1.0.0",
            matching_method="exact_regime_then_lexicographic",
            deterministic_tie_breaking=True,
            selection_policy_id="SELECT-V6-SYNTHETIC",
            selection_policy_version="1.0.0",
            selection_pre_registered=True,
        )

    def test_complete_increase_context_is_deterministic_and_non_authoritative(
        self,
    ) -> None:
        first = self.fixture.build_result
        second = self.build()
        self.assertEqual(first.status, "created")
        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertFalse(first.collection.rule_binding_verified)
        self.assertFalse(first.collection.runtime_authorized)
        self.assertFalse(first.rule_evidence_binding.validity_authority_granted)
        self.assertFalse(first.normal_reference_binding.authority_granted)
        self.assertRegex(first.rule_evidence_binding.evidence_id, r"^EVID-V6-")
        self.assertRegex(
            first.normal_reference_binding.normal_reference_id,
            r"^NREF-V6-",
        )

    def test_unsupported_evidence_states_emit_no_partial_target(self) -> None:
        insufficient = dataclasses.replace(
            self.fixture.normal_evidence,
            evidence_status=EvidenceStatusV1.INSUFFICIENT_SUPPORT,
            evidence_insufficiency_reasons=("insufficient_trigger_support",),
        )
        unstable = dataclasses.replace(
            self.fixture.normal_evidence,
            evidence_status=EvidenceStatusV1.UNSTABLE,
            evidence_insufficiency_reasons=("unstable_lag",),
            stability_summary=RelationStabilitySummaryV1(
                status=StabilityStatusV1.UNSTABLE,
                method="synthetic_replicates",
                replicate_count=3,
                variation_measure=0.9,
                confidence_lower=0.7,
                confidence_upper=1.0,
            ),
        )
        for evidence in (insufficient, unstable):
            with self.subTest(status=evidence.evidence_status.value):
                result = self.build(normal_evidence=evidence)
                self.assertEqual(result.status, "unsupported_source")
                self.assertIsNone(result.collection)
                self.assertIsNone(result.rule_evidence_binding)
                self.assertIsNone(result.normal_reference_binding)

    def test_decrease_requires_future_rule_family(self) -> None:
        result = self.build(
            normal_evidence=dataclasses.replace(
                self.fixture.normal_evidence,
                response_direction=ResponseDirectionV1.DECREASE,
            )
        )
        self.assertEqual(result.status, "unsupported_source")
        self.assertIn(
            "DECREASE_RELATION_REQUIRES_FUTURE_RULE_FAMILY",
            result.issue_codes,
        )

    def test_missing_edge_mapping_and_required_parameters_are_pending(self) -> None:
        mappings = dataclasses.replace(
            self.fixture.mappings,
            edge_ids_by_source_hash={},
            required_parameter_ids_by_role={},
        )
        result = self.build(mappings=mappings)
        self.assertEqual(result.status, "pending_context")
        self.assertTrue(
            any(item.startswith("graph_edge_mapping:") for item in result.missing_context)
        )
        self.assertIn(
            "canonical_parameter_role:severity_boundary",
            result.missing_context,
        )
        self.assertIn(
            "canonical_parameter_role:persistence_duration",
            result.missing_context,
        )
        self.assertIsNone(result.collection)

    def test_condition_artifact_hash_mismatch_is_invalid(self) -> None:
        condition_id = next(
            iter(self.fixture.mappings.condition_artifact_hashes_by_id)
        )
        mappings = dataclasses.replace(
            self.fixture.mappings,
            condition_artifact_hashes_by_id={condition_id: "0" * 64},
        )
        result = self.build(mappings=mappings)
        self.assertEqual(result.status, "invalid_source")
        self.assertIsNone(result.collection)

    def test_graph_metadata_process_regime_and_lag_mismatches_fail_closed(
        self,
    ) -> None:
        lag = self.fixture.normal_evidence.lag_summary
        assert lag is not None
        cases = {
            "metadata": dataclasses.replace(
                self.fixture.normal_evidence,
                source_metadata_ref="0" * 64,
            ),
            "process": dataclasses.replace(
                self.fixture.normal_evidence,
                process_scope=("P3",),
            ),
            "regime": dataclasses.replace(
                self.fixture.normal_evidence,
                operating_regime_id="REGIME-OTHER",
            ),
            "lag": dataclasses.replace(
                self.fixture.normal_evidence,
                lag_summary=DistributionSummaryV1(
                    count=lag.count,
                    minimum=lag.minimum,
                    p50=lag.p50,
                    p95=6.0,
                    maximum=7.0,
                    unit=lag.unit,
                    method=lag.method,
                    value_semantics=lag.value_semantics,
                ),
            ),
        }
        for name, evidence in cases.items():
            with self.subTest(name=name):
                result = self.build(normal_evidence=evidence)
                self.assertEqual(result.status, "invalid_source")
                self.assertIsNone(result.collection)

    def test_parameter_source_hash_mismatch_is_invalid(self) -> None:
        refs = self.fixture.normal_evidence.calibration_parameter_refs
        first_id = self.fixture.mappings.parameter_ids_by_source_hash[
            refs[0].artifact_ref
        ]
        second_id = self.fixture.mappings.parameter_ids_by_source_hash[
            refs[1].artifact_ref
        ]
        mappings = CanonicalContextMappingsV1(
            edge_ids_by_source_hash=self.fixture.mappings.edge_ids_by_source_hash,
            condition_ids_by_source_hash=(
                self.fixture.mappings.condition_ids_by_source_hash
            ),
            condition_artifact_hashes_by_id=(
                self.fixture.mappings.condition_artifact_hashes_by_id
            ),
            parameter_ids_by_source_hash={
                refs[0].artifact_ref: second_id,
                refs[1].artifact_ref: first_id,
            },
            required_parameter_ids_by_role=(
                self.fixture.mappings.required_parameter_ids_by_role
            ),
        )
        result = self.build(mappings=mappings)
        self.assertEqual(result.status, "invalid_source")
        self.assertIsNone(result.collection)

    def test_build_does_not_mutate_callers(self) -> None:
        before = (
            self.fixture.dataset.to_dict(),
            self.fixture.normal_evidence.to_dict(),
            self.fixture.mappings.edge_ids_by_source_hash.copy(),
        )
        self.build()
        after = (
            self.fixture.dataset.to_dict(),
            self.fixture.normal_evidence.to_dict(),
            self.fixture.mappings.edge_ids_by_source_hash.copy(),
        )
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
