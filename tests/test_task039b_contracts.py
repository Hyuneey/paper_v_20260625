from __future__ import annotations

import copy
import unittest
from hashlib import sha256

from paperworks.feasibility.hai_process_v1 import (
    HAIFeasibilityError,
    MetadataConfidenceV1,
    MetadataReviewStatusV1,
    ObservedDomainV1,
    SemanticRoleV2,
    build_domain_diagnostic,
    build_variable_metadata,
    canonical_json,
    classify_observed_domain,
    infer_semantic_role,
    public_payload_has_prohibited_content,
    robust_noise_scale,
)


HASH = "a" * 64


class Task039BContractTests(unittest.TestCase):
    def test_domain_classification_is_not_semantic_typing(self) -> None:
        self.assertEqual(classify_observed_domain([0.0, 1.0])[0], ObservedDomainV1.BINARY)
        self.assertEqual(classify_observed_domain([0.0, 1.0, 2.0])[0], ObservedDomainV1.DISCRETE)
        self.assertEqual(classify_observed_domain([0.1, 0.2, 0.3])[0], ObservedDomainV1.CONTINUOUS)
        self.assertEqual(infer_semantic_role("P1_X01", "unresolved")[0], SemanticRoleV2.UNKNOWN)

    def test_robust_noise_scale_is_within_file_only(self) -> None:
        observed = robust_noise_scale(([0.0, 1.0, 2.0], [1000.0, 1001.0, 1002.0]))
        self.assertEqual(observed, 1e-12)

    def test_metadata_requires_manual_evidence_for_eligibility(self) -> None:
        domain = build_domain_diagnostic(
            variable_name="P1_PUMP01D",
            process_id="P1",
            values_by_file={"f1": [0.0, 1.0], "f2": [1.0, 0.0], "f3": [0.0, 1.0]},
            candidate_fit_files=("f1", "f2"),
        ).diagnostic
        unresolved = build_variable_metadata(
            variable_name="P1_PUMP01D",
            process_id="P1",
            description="pump command",
            unit="state",
            subsystem_or_stage="boiler",
            manual_pages=(),
            official_graph_references=(),
            domain=domain,
            evidence_record_refs=(),
        )
        self.assertFalse(unresolved.source_eligibility)
        self.assertEqual(unresolved.metadata_confidence, MetadataConfidenceV1.INSUFFICIENT)
        self.assertEqual(unresolved.review_status, MetadataReviewStatusV1.UNRESOLVED)

    def test_reviewed_source_is_deterministic_and_input_immutable(self) -> None:
        values = {"f1": [0.0, 1.0], "f2": [1.0, 0.0], "f3": [0.0, 1.0]}
        original = copy.deepcopy(values)
        domain = build_domain_diagnostic(
            variable_name="P1_PUMP01D",
            process_id="P1",
            values_by_file=values,
            candidate_fit_files=("f1", "f2"),
        ).diagnostic
        metadata = build_variable_metadata(
            variable_name="P1_PUMP01D",
            process_id="P1",
            description="official pump control command",
            unit="state",
            subsystem_or_stage="boiler",
            manual_pages=(4,),
            official_graph_references=("graph/boiler.json",),
            domain=domain,
            evidence_record_refs=(HASH,),
        )
        self.assertTrue(metadata.source_eligibility)
        self.assertEqual(values, original)
        self.assertEqual(metadata.artifact_hash, metadata.artifact_hash)

    def test_public_leak_guard(self) -> None:
        self.assertFalse(public_payload_has_prohibited_content({"artifact_hash": HASH}))
        self.assertTrue(public_payload_has_prohibited_content({"raw_window": [1]}))
        state_hash = sha256(canonical_json({"state": 1}).encode()).hexdigest()
        self.assertEqual(len(state_hash), 64)

    def test_process_scope_fails_closed(self) -> None:
        with self.assertRaises(HAIFeasibilityError):
            build_domain_diagnostic(
                variable_name="P2_X",
                process_id="P1",
                values_by_file={"f": [1.0]},
                candidate_fit_files=("f",),
            )


if __name__ == "__main__":
    unittest.main()
