from __future__ import annotations

import unittest

from paperworks.data import DataViewManifest, DataViewName, SplitManifest, SplitRole
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
from paperworks.profiling import (
    RelationEvidencePack,
    RelationProfile,
    RelationProfilingConfig,
    RelationProfilingError,
    build_relation_evidence_pack,
    calibrate_relation_profile,
    profile_binary_actuator_to_continuous_sensor,
)


DATASET_ID = "a" * 64
DATA_VIEW_ID = "b" * 64


def actuator(name: str = "A1") -> VariableMetadata:
    return VariableMetadata(
        name=name,
        role=VariableRole.ACTUATOR,
        value_type=ValueType.BINARY,
        physical_type=PhysicalType.PUMP,
        subsystem="stage_1",
        stage="1",
        source_method=MetadataSourceMethod.MANUAL_REVIEW,
        source_reference="synthetic fixture",
        confidence=1.0,
        review_status=ReviewStatus.REVIEWED,
    )


def sensor(name: str = "S1") -> VariableMetadata:
    return VariableMetadata(
        name=name,
        role=VariableRole.SENSOR,
        value_type=ValueType.CONTINUOUS,
        physical_type=PhysicalType.FLOW,
        subsystem="stage_1",
        stage="1",
        source_method=MetadataSourceMethod.MANUAL_REVIEW,
        source_reference="synthetic fixture",
        confidence=1.0,
        review_status=ReviewStatus.REVIEWED,
    )


def registry() -> MetadataRegistry:
    return MetadataRegistry([actuator(), sensor()])


def split(role: SplitRole = SplitRole.CALIBRATION_NORMAL) -> SplitManifest:
    return SplitManifest(
        dataset_manifest_id=DATASET_ID,
        data_view_id=DATA_VIEW_ID,
        role=role,
        raw_index_ranges=((0, 12),),
        purge_gap_samples=0,
        seed=11,
    )


def data_view(
    *,
    name: DataViewName = DataViewName.CANONICAL_RULE,
    sampling_period_seconds: float = 1.0,
    source_view: str = "canonical_rule_view",
) -> DataViewManifest:
    return DataViewManifest(
        name=name,
        sampling_period_seconds=sampling_period_seconds,
        preprocessing_config={},
        upstream_dataset_manifest_id=DATASET_ID,
        fingerprint="c" * 64,
        source_view=source_view,
    )


def config(
    *,
    max_response_delay_samples: int = 4,
    min_matched_response_count: int = 2,
) -> RelationProfilingConfig:
    return RelationProfilingConfig(
        max_response_delay_samples=max_response_delay_samples,
        min_matched_response_count=min_matched_response_count,
        delay_quantile=1.0,
        magnitude_quantile=0.0,
    )


def profile(series, *, cfg: RelationProfilingConfig | None = None, view: DataViewManifest | None = None) -> RelationProfile:
    return profile_binary_actuator_to_continuous_sensor(
        source="A1",
        target="S1",
        series=series,
        metadata=registry(),
        split=split(),
        data_view=view or data_view(),
        config=cfg or config(),
        upstream_artifact_ids=("d" * 64,),
        dataset="synthetic",
        data_fingerprint="e" * 64,
        random_seed=11,
        created_at="2026-06-25T00:00:00Z",
    )


class RelationProfilingTests(unittest.TestCase):
    def test_exact_synthetic_response_delay_and_magnitude(self) -> None:
        cfg = config(max_response_delay_samples=3)
        view = data_view(sampling_period_seconds=2.0)
        artifact = profile(
            {
                "A1": [0, 1, 1, 1, 0, 1, 1],
                "S1": [10, 10, 10, 13, 13, 13, 15],
            },
            cfg=cfg,
            view=view,
        )

        self.assertEqual(artifact.normal_support_status, "supported")
        self.assertEqual(artifact.trigger_count, 2)
        self.assertEqual(artifact.matched_response_count, 2)
        self.assertEqual(artifact.response_events[0].delay_seconds, 4.0)
        self.assertEqual(artifact.response_events[0].magnitude, 3.0)
        self.assertEqual(artifact.response_events[1].delay_seconds, 2.0)
        self.assertEqual(artifact.response_events[1].magnitude, 2.0)

        records = calibrate_relation_profile(profile=artifact, split=split(), config=cfg)
        values = {record.parameter_name: record.value for record in records}
        self.assertEqual(values["max_response_delay_seconds"], 4.0)
        self.assertEqual(values["min_response_magnitude"], 2.0)

    def test_repeated_trigger_overlap_is_recorded(self) -> None:
        artifact = profile(
            {
                "A1": [0, 1, 0, 1, 1, 1],
                "S1": [0, 0, 1, 1, 1, 3],
            },
            cfg=config(max_response_delay_samples=3),
        )

        self.assertEqual(artifact.trigger_count, 2)
        self.assertEqual(artifact.overlapping_window_count, 1)
        self.assertEqual(artifact.matched_response_count, 2)

    def test_missing_response_is_reported_not_dropped(self) -> None:
        artifact = profile(
            {
                "A1": [0, 1, 1, 1, 1, 1],
                "S1": [2, 2, 2, 2, 2, 2],
            },
            cfg=config(max_response_delay_samples=2),
        )

        self.assertEqual(artifact.normal_support_status, "INSUFFICIENT_NORMAL_SUPPORT")
        self.assertEqual(artifact.trigger_count, 1)
        self.assertEqual(artifact.matched_response_count, 0)
        self.assertEqual(artifact.missing_response_count, 1)
        self.assertEqual(artifact.censored_or_missing_count, 1)

    def test_right_censored_trigger_is_reported(self) -> None:
        artifact = profile(
            {
                "A1": [0, 1, 1],
                "S1": [5, 5, 5],
            },
            cfg=config(max_response_delay_samples=4),
        )

        self.assertEqual(artifact.right_censored_count, 1)
        self.assertEqual(artifact.trigger_events[0].status, "right_censored")

    def test_insufficient_support_blocks_calibration(self) -> None:
        artifact = profile(
            {
                "A1": [0, 1, 1, 1],
                "S1": [0, 0, 1, 1],
            },
            cfg=config(max_response_delay_samples=2),
        )

        self.assertEqual(artifact.normal_support_status, "INSUFFICIENT_NORMAL_SUPPORT")
        with self.assertRaises(RelationProfilingError):
            calibrate_relation_profile(profile=artifact, split=split(), config=config(max_response_delay_samples=2))

    def test_irregular_sampling_policy_rejects_timestamp_gaps(self) -> None:
        with self.assertRaisesRegex(RelationProfilingError, "irregular sampling"):
            profile_binary_actuator_to_continuous_sensor(
                source="A1",
                target="S1",
                series={"A1": [0, 1, 1, 1], "S1": [0, 0, 0, 1]},
                metadata=registry(),
                split=split(),
                data_view=data_view(),
                config=config(max_response_delay_samples=3, min_matched_response_count=1),
                timestamps_seconds=[0.0, 1.0, 3.0, 4.0],
            )

    def test_wrong_view_is_rejected(self) -> None:
        with self.assertRaisesRegex(RelationProfilingError, "canonical rule view"):
            profile(
                {
                    "A1": [0, 1, 1],
                    "S1": [0, 0, 1],
                },
                cfg=config(max_response_delay_samples=2, min_matched_response_count=1),
                view=data_view(name=DataViewName.GDN, source_view="gdn"),
            )

    def test_test_split_is_rejected(self) -> None:
        with self.assertRaises(SplitPermissionError):
            profile_binary_actuator_to_continuous_sensor(
                source="A1",
                target="S1",
                series={"A1": [0, 1, 1], "S1": [0, 0, 1]},
                metadata=registry(),
                split=split(SplitRole.TEST),
                data_view=data_view(),
                config=config(max_response_delay_samples=2, min_matched_response_count=1),
            )

    def test_unsupported_pair_type_is_rejected(self) -> None:
        bad_registry = MetadataRegistry([sensor("A1"), sensor("S1")])
        with self.assertRaisesRegex(RelationProfilingError, "source must be a binary actuator"):
            profile_binary_actuator_to_continuous_sensor(
                source="A1",
                target="S1",
                series={"A1": [0, 1, 1], "S1": [0, 0, 1]},
                metadata=bad_registry,
                split=split(),
                data_view=data_view(),
                config=config(max_response_delay_samples=2, min_matched_response_count=1),
            )

    def test_evidence_pack_provenance_round_trip(self) -> None:
        cfg = config(max_response_delay_samples=3)
        artifact = profile(
            {
                "A1": [0, 1, 1, 1, 0, 1, 1],
                "S1": [10, 10, 10, 13, 13, 13, 15],
            },
            cfg=cfg,
            view=data_view(sampling_period_seconds=2.0),
        )
        records = calibrate_relation_profile(profile=artifact, split=split(), config=cfg)
        evidence = build_relation_evidence_pack(profile=artifact, calibration_records=records)

        self.assertEqual(evidence.source_view, "canonical_rule_view")
        self.assertEqual(evidence.support_counts["matched_response_count"], 2)
        self.assertEqual(set(evidence.calibration_record_ids), {"max_response_delay_seconds", "min_response_magnitude"})
        self.assertEqual(
            RelationEvidencePack.from_dict(evidence.to_dict()).to_dict(),
            evidence.to_dict(),
        )
        self.assertEqual(
            RelationProfile.from_dict(artifact.to_dict()).to_dict(),
            artifact.to_dict(),
        )
        self.assertEqual(evidence.evidence_pack_id, RelationEvidencePack.from_dict(evidence.to_dict()).evidence_pack_id)


if __name__ == "__main__":
    unittest.main()
