from __future__ import annotations

import json
import unittest
from pathlib import Path

from paperworks.candidates import (
    CandidatePolicy,
    CandidateTargetStatus,
    CandidateUniverseError,
    build_candidate_universe,
    candidate_mask,
    indexed_candidates_by_target,
)
from paperworks.data import DataViewManifest, DataViewName, SplitManifest, SplitRole
from paperworks.data.contracts import stable_hash
from paperworks.data.splits import SplitPermissionError
from paperworks.metadata import (
    MetadataRegistry,
    MetadataSourceMethod,
    PhysicalType,
    ReviewStatus,
    ValueType,
    VariableMetadata,
    VariableRole,
)


FEATURE_ORDER = ("A1", "A2", "S1", "S2", "S3")
HASH = "a" * 64


def actuator(name: str, stage: str) -> VariableMetadata:
    return VariableMetadata(
        name=name,
        role=VariableRole.ACTUATOR,
        value_type=ValueType.BINARY,
        physical_type=PhysicalType.PUMP,
        subsystem=f"stage_{stage}",
        stage=stage,
        source_method=MetadataSourceMethod.MANUAL_REVIEW,
        source_reference="synthetic fixture",
        confidence=1.0,
        review_status=ReviewStatus.REVIEWED,
    )


def sensor(name: str, stage: str) -> VariableMetadata:
    return VariableMetadata(
        name=name,
        role=VariableRole.SENSOR,
        value_type=ValueType.CONTINUOUS,
        physical_type=PhysicalType.FLOW,
        subsystem=f"stage_{stage}",
        stage=stage,
        source_method=MetadataSourceMethod.MANUAL_REVIEW,
        source_reference="synthetic fixture",
        confidence=1.0,
        review_status=ReviewStatus.REVIEWED,
    )


def registry() -> MetadataRegistry:
    return MetadataRegistry(
        [
            actuator("A1", "1"),
            actuator("A2", "2"),
            sensor("S1", "1"),
            sensor("S2", "2"),
            sensor("S3", "3"),
        ]
    )


def split(role: SplitRole = SplitRole.TRAIN_NORMAL) -> SplitManifest:
    return SplitManifest(
        dataset_manifest_id=HASH,
        data_view_id="b" * 64,
        role=role,
        raw_index_ranges=((0, 8),),
        purge_gap_samples=0,
        seed=123,
    )


def data_view() -> DataViewManifest:
    return DataViewManifest(
        name=DataViewName.CANONICAL_RULE,
        sampling_period_seconds=1.0,
        preprocessing_config={},
        upstream_dataset_manifest_id=HASH,
        fingerprint="c" * 64,
        source_view="canonical_rule_view",
    )


def metadata_artifact_id() -> str:
    return stable_hash({"fixture": "metadata"})


def build(**kwargs):
    defaults = {
        "metadata": registry(),
        "feature_order": FEATURE_ORDER,
        "policy": CandidatePolicy(),
        "split": split(),
        "data_view": data_view(),
        "metadata_artifact_id": metadata_artifact_id(),
        "created_at": "2026-06-25T00:00:00Z",
    }
    defaults.update(kwargs)
    return build_candidate_universe(**defaults)


class CandidateUniverseTests(unittest.TestCase):
    def test_same_stage_domain_policy(self) -> None:
        artifact = build()
        pairs = {(pair.source, pair.target): pair for pair in artifact.pairs}
        self.assertIn(("A1", "S1"), pairs)
        self.assertIn(("A2", "S2"), pairs)
        self.assertNotIn(("A1", "S2"), pairs)
        self.assertEqual(pairs[("A1", "S1")].origins, ("domain",))
        self.assertEqual(artifact.target_status["S3"], CandidateTargetStatus.UNSUPPORTED_EMPTY_SET)

    def test_type_compatible_configured_fallback(self) -> None:
        policy = CandidatePolicy(domain_same_stage=False, fallback_min_candidates_per_target=2)
        artifact = build(policy=policy)
        by_target = indexed_candidates_by_target(artifact)
        self.assertEqual(by_target["S1"], (0, 1))
        self.assertEqual(by_target["S2"], (0, 1))
        self.assertEqual(by_target["S3"], (0, 1))
        self.assertEqual(artifact.target_status["S3"], CandidateTargetStatus.EXPANDED_BY_CONFIGURED_FALLBACK)

    def test_statistical_top_m_uses_train_normal_series(self) -> None:
        normal_data = {
            "A1": [0, 1, 0, 1, 0, 1],
            "A2": [0, 0, 1, 1, 0, 0],
            "S1": [0, 0, 1, 1, 0, 0],
            "S2": [0, 1, 0, 1, 0, 1],
            "S3": [1, 1, 1, 1, 1, 1],
        }
        policy = CandidatePolicy(domain_same_stage=False, statistical_top_m=1)
        artifact = build(policy=policy, normal_data=normal_data, normal_summary_artifact_id="d" * 64)
        pairs = {(pair.source, pair.target): pair for pair in artifact.pairs}
        self.assertIn(("A2", "S1"), pairs)
        self.assertEqual(pairs[("A2", "S1")].origins, ("stat",))
        self.assertGreater(pairs[("A2", "S1")].origin_scores["stat"], 0.99)

    def test_union_provenance_merges_origins(self) -> None:
        normal_data = {
            "A1": [0, 1, 0, 1, 0, 1],
            "A2": [0, 0, 1, 1, 0, 0],
            "S1": [0, 1, 0, 1, 0, 1],
            "S2": [0, 0, 1, 1, 0, 0],
            "S3": [1, 0, 1, 0, 1, 0],
        }
        policy = CandidatePolicy(domain_same_stage=True, statistical_top_m=1)
        artifact = build(policy=policy, normal_data=normal_data, normal_summary_artifact_id="d" * 64)
        pairs = {(pair.source, pair.target): pair for pair in artifact.pairs}
        self.assertEqual(pairs[("A1", "S1")].origins, ("domain", "stat"))
        self.assertEqual(pairs[("A2", "S2")].origins, ("domain", "stat"))

    def test_self_edges_are_excluded_from_pairs_and_mask(self) -> None:
        artifact = build(policy=CandidatePolicy(domain_same_stage=False, fallback_min_candidates_per_target=2))
        for pair in artifact.pairs:
            self.assertNotEqual(pair.source, pair.target)
        mask = candidate_mask(artifact)
        for index in range(len(FEATURE_ORDER)):
            self.assertFalse(mask[index][index])

    def test_mask_name_alignment_is_target_major(self) -> None:
        artifact = build()
        mask = candidate_mask(artifact)
        source_index = FEATURE_ORDER.index("A1")
        target_index = FEATURE_ORDER.index("S1")
        self.assertTrue(mask[target_index][source_index])
        self.assertFalse(mask[source_index][target_index])

    def test_empty_targets_are_explicit(self) -> None:
        artifact = build()
        self.assertIn("A1", artifact.empty_targets)
        self.assertIn("A2", artifact.empty_targets)
        self.assertIn("S3", artifact.empty_targets)
        self.assertEqual(artifact.target_candidate_counts["S3"], 0)

    def test_deterministic_artifact_id(self) -> None:
        first = build()
        second = build()
        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertEqual(first.artifact_id, second.artifact_id)

    def test_prohibited_test_split_input(self) -> None:
        with self.assertRaises(SplitPermissionError):
            build(split=split(SplitRole.TEST))

    def test_statistical_policy_requires_normal_data(self) -> None:
        with self.assertRaises(CandidateUniverseError):
            build(policy=CandidatePolicy(domain_same_stage=False, statistical_top_m=1))

    def test_normal_summary_artifact_id_must_be_hash(self) -> None:
        normal_data = {
            "A1": [0, 1, 0],
            "A2": [1, 0, 1],
            "S1": [0, 1, 0],
            "S2": [1, 0, 1],
            "S3": [0, 0, 0],
        }
        with self.assertRaises(CandidateUniverseError):
            build(
                policy=CandidatePolicy(domain_same_stage=False, statistical_top_m=1),
                normal_data=normal_data,
                normal_summary_artifact_id="not-a-hash",
            )

    def test_policy_loads_from_project_config(self) -> None:
        payload = json.loads(Path("configs/candidates/swat_candidate_policy.json").read_text(encoding="utf-8"))
        policy = CandidatePolicy.from_dict(payload)
        self.assertTrue(policy.domain_same_stage)
        self.assertFalse(policy.statistical_enabled)
        self.assertFalse(policy.fallback_enabled)


if __name__ == "__main__":
    unittest.main()
