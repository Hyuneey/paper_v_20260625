from __future__ import annotations

import unittest

from paperworks.candidates import CandidatePolicy, build_candidate_universe
from paperworks.data import DataViewManifest, DataViewName, SplitManifest, SplitRole
from paperworks.data.contracts import stable_hash
from paperworks.data.splits import SplitPermissionError
from paperworks.gdn import (
    EmbeddingCheckpoint,
    GDNExtractionConfig,
    GDNExtractionError,
    TorchGDNTrainingConfig,
    cosine_similarity_matrix,
    extract_masked_topk_edges,
    fit_deterministic_embedding_checkpoint,
    fit_torch_gdn_embedding_checkpoint,
    message_passing_self_loops,
)
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
DATASET_ID = "a" * 64
DATA_VIEW_ID = "b" * 64


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
        dataset_manifest_id=DATASET_ID,
        data_view_id=DATA_VIEW_ID,
        role=role,
        raw_index_ranges=((0, 8),),
        purge_gap_samples=0,
        seed=7,
    )


def data_view() -> DataViewManifest:
    return DataViewManifest(
        name=DataViewName.CANONICAL_RULE,
        sampling_period_seconds=1.0,
        preprocessing_config={},
        upstream_dataset_manifest_id=DATASET_ID,
        fingerprint="c" * 64,
        source_view="canonical_rule_view",
    )


def candidate_universe(policy: CandidatePolicy | None = None):
    return build_candidate_universe(
        metadata=registry(),
        feature_order=FEATURE_ORDER,
        policy=policy or CandidatePolicy(domain_same_stage=False, fallback_min_candidates_per_target=2),
        split=split(),
        data_view=data_view(),
        metadata_artifact_id=stable_hash({"fixture": "metadata"}),
        created_at="2026-06-25T00:00:00Z",
    )


def checkpoint(embeddings=None) -> EmbeddingCheckpoint:
    feature_order_hash = stable_hash({"feature_order": list(FEATURE_ORDER)})
    return EmbeddingCheckpoint(
        feature_order=FEATURE_ORDER,
        feature_order_hash=feature_order_hash,
        embeddings=embeddings
        or {
            "A1": (1.0, 0.0),
            "A2": (0.0, 1.0),
            "S1": (1.0, 0.0),
            "S2": (0.0, 1.0),
            "S3": (1.0, 1.0),
        },
        seed=7,
        split_name=SplitRole.TRAIN_NORMAL.value,
        source_view="canonical_rule_view",
        sampling_period_seconds=1.0,
        training_config={"backend": "synthetic fixture"},
        dataset_manifest_id=DATASET_ID,
        data_view_id=DATA_VIEW_ID,
    )


def extract(policy: CandidatePolicy | None = None, config: GDNExtractionConfig | None = None):
    return extract_masked_topk_edges(
        candidate_universe=candidate_universe(policy),
        checkpoint=checkpoint(),
        config=config or GDNExtractionConfig(top_k=1, seed=7),
        split=split(),
        data_view=data_view(),
        created_at="2026-06-25T00:00:00Z",
    )


def synthetic_sequence() -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for index in range(8):
        a1 = float(index % 2)
        a2 = float((index + 1) % 2)
        rows.append(
            {
                "A1": a1,
                "A2": a2,
                "S1": a1,
                "S2": a2,
                "S3": (a1 + a2) / 2.0,
            }
        )
    return rows


class MaskedGDNExtractionTests(unittest.TestCase):
    def test_candidate_mask_enforcement(self) -> None:
        artifact = extract()
        self.assertEqual([(edge.source, edge.target) for edge in artifact.edges], [("A1", "S1"), ("A2", "S2"), ("A1", "S3")])
        for edge in artifact.edges:
            self.assertIn(edge.source, {"A1", "A2"})
            self.assertIn(edge.target, {"S1", "S2", "S3"})
            self.assertTrue(edge.candidate_origins)

    def test_self_candidate_exclusion(self) -> None:
        artifact = extract(config=GDNExtractionConfig(top_k=5, seed=7))
        self.assertTrue(artifact.edges)
        self.assertTrue(all(edge.source != edge.target for edge in artifact.edges))

    def test_message_passing_self_loops_are_separate(self) -> None:
        artifact = extract(config=GDNExtractionConfig(top_k=5, seed=7))
        self.assertEqual(message_passing_self_loops(FEATURE_ORDER), tuple((name, name) for name in FEATURE_ORDER))
        self.assertEqual(artifact.message_passing_self_loop_count, len(FEATURE_ORDER))
        self.assertTrue(all(edge.source != edge.target for edge in artifact.edges))

    def test_k_larger_than_candidate_count(self) -> None:
        artifact = extract(config=GDNExtractionConfig(top_k=20, seed=7))
        by_target: dict[str, int] = {}
        for edge in artifact.edges:
            by_target[edge.target] = by_target.get(edge.target, 0) + 1
        self.assertEqual(by_target["S1"], 2)
        self.assertEqual(by_target["S2"], 2)
        self.assertEqual(by_target["S3"], 2)

    def test_empty_candidate_set_emits_no_edges(self) -> None:
        artifact = extract(policy=CandidatePolicy(domain_same_stage=True), config=GDNExtractionConfig(top_k=5, seed=7))
        self.assertNotIn("S3", {edge.target for edge in artifact.edges})

    def test_feature_order_mismatch_rejection(self) -> None:
        bad_checkpoint = EmbeddingCheckpoint(
            feature_order=("A2", "A1", "S1", "S2", "S3"),
            feature_order_hash=stable_hash({"feature_order": ["A2", "A1", "S1", "S2", "S3"]}),
            embeddings={
                "A1": (1.0, 0.0),
                "A2": (0.0, 1.0),
                "S1": (1.0, 0.0),
                "S2": (0.0, 1.0),
                "S3": (1.0, 1.0),
            },
            seed=7,
            split_name=SplitRole.TRAIN_NORMAL.value,
            source_view="canonical_rule_view",
            sampling_period_seconds=1.0,
            training_config={"backend": "synthetic fixture"},
            dataset_manifest_id=DATASET_ID,
            data_view_id=DATA_VIEW_ID,
        )
        with self.assertRaises(GDNExtractionError):
            extract_masked_topk_edges(
                candidate_universe=candidate_universe(),
                checkpoint=bad_checkpoint,
                config=GDNExtractionConfig(top_k=1, seed=7),
                split=split(),
                data_view=data_view(),
            )

    def test_deterministic_seed_behavior(self) -> None:
        first = extract()
        second = extract()
        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertEqual(first.artifact_id, second.artifact_id)

    def test_synthetic_training_smoke_uses_train_normal(self) -> None:
        config = GDNExtractionConfig(top_k=1, seed=7)
        trained = fit_deterministic_embedding_checkpoint(
            normal_windows=[
                {"A1": 0, "A2": 1, "S1": 0.0, "S2": 1.0, "S3": 0.5},
                {"A1": 1, "A2": 0, "S1": 1.0, "S2": 0.0, "S3": 0.5},
            ],
            feature_order=FEATURE_ORDER,
            split=split(),
            data_view=data_view(),
            config=config,
        )
        artifact = extract_masked_topk_edges(
            candidate_universe=candidate_universe(),
            checkpoint=trained,
            config=config,
            split=split(),
            data_view=data_view(),
        )
        self.assertEqual(trained.split_name, SplitRole.TRAIN_NORMAL.value)
        self.assertTrue(artifact.edges)

    def test_torch_pyg_training_smoke_exports_checkpoint(self) -> None:
        config = TorchGDNTrainingConfig(seed=11, embedding_dim=4, hidden_dim=8, epochs=5, learning_rate=0.02)
        trained = fit_torch_gdn_embedding_checkpoint(
            normal_windows=synthetic_sequence(),
            candidate_universe=candidate_universe(),
            split=split(),
            data_view=data_view(),
            config=config,
        )
        self.assertEqual(trained.training_config["backend"], "torch_pyg_cpu")
        self.assertEqual(trained.training_config["candidate_edge_count"], 6)
        self.assertEqual(len(trained.embeddings["A1"]), 4)
        self.assertEqual(trained.split_name, SplitRole.TRAIN_NORMAL.value)

        artifact = extract_masked_topk_edges(
            candidate_universe=candidate_universe(),
            checkpoint=trained,
            config=GDNExtractionConfig(top_k=1, seed=11, backend="torch_pyg_cpu"),
            split=split(),
            data_view=data_view(),
        )
        self.assertTrue(artifact.edges)
        self.assertTrue(all(edge.source != edge.target for edge in artifact.edges))

    def test_torch_pyg_training_is_deterministic_for_same_seed(self) -> None:
        config = TorchGDNTrainingConfig(seed=13, embedding_dim=4, hidden_dim=8, epochs=3, learning_rate=0.02)
        first = fit_torch_gdn_embedding_checkpoint(
            normal_windows=synthetic_sequence(),
            candidate_universe=candidate_universe(),
            split=split(),
            data_view=data_view(),
            config=config,
        )
        second = fit_torch_gdn_embedding_checkpoint(
            normal_windows=synthetic_sequence(),
            candidate_universe=candidate_universe(),
            split=split(),
            data_view=data_view(),
            config=config,
        )
        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertEqual(first.checkpoint_id, second.checkpoint_id)

    def test_torch_pyg_training_rejects_test_split(self) -> None:
        with self.assertRaises(SplitPermissionError):
            fit_torch_gdn_embedding_checkpoint(
                normal_windows=synthetic_sequence(),
                candidate_universe=candidate_universe(),
                split=split(SplitRole.TEST),
                data_view=data_view(),
                config=TorchGDNTrainingConfig(seed=11, epochs=2),
            )

    def test_no_test_split_guard(self) -> None:
        with self.assertRaises(SplitPermissionError):
            fit_deterministic_embedding_checkpoint(
                normal_windows=[{"A1": 0, "A2": 1, "S1": 0.0, "S2": 1.0, "S3": 0.5}],
                feature_order=FEATURE_ORDER,
                split=split(SplitRole.TEST),
                data_view=data_view(),
                config=GDNExtractionConfig(top_k=1, seed=7),
            )
        with self.assertRaises(SplitPermissionError):
            extract_masked_topk_edges(
                candidate_universe=candidate_universe(),
                checkpoint=checkpoint(),
                config=GDNExtractionConfig(top_k=1, seed=7),
                split=split(SplitRole.TEST),
                data_view=data_view(),
            )

    def test_behavioral_comparison_against_reference_calculation(self) -> None:
        matrix = cosine_similarity_matrix(checkpoint().embeddings, FEATURE_ORDER)
        target_index = FEATURE_ORDER.index("S3")
        source_scores = {
            "A1": matrix[target_index][FEATURE_ORDER.index("A1")],
            "A2": matrix[target_index][FEATURE_ORDER.index("A2")],
        }
        expected_source = sorted(source_scores.items(), key=lambda item: (-item[1], FEATURE_ORDER.index(item[0])))[0][0]
        edge = [edge for edge in extract().edges if edge.target == "S3"][0]
        self.assertEqual(edge.source, expected_source)
        self.assertAlmostEqual(edge.embedding_similarity, source_scores[expected_source])


if __name__ == "__main__":
    unittest.main()
