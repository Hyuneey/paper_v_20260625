from __future__ import annotations

import ast
import copy
import unittest

from paperworks.data.contracts_v2 import (
    AggregationDescriptionV2,
    DataContractV2Error,
    DataViewKindV2,
    DataViewManifestV2,
    DatasetFileV2,
    DatasetManifestV2,
    ProvenanceStatusV2,
    TimeRangeV2,
    assert_second_level_rule_calibration_compatible,
)
from tests.test_task039p0_alignment_audit import ROOT, read_public_text
from tests.task039p1a_support import (
    HASH_C,
    creation_metadata,
    data_view_manifest_v2,
    dataset_manifest_v2,
)


class Task039P1AContractsV2Tests(unittest.TestCase):
    def test_dataset_manifest_round_trip_hash_is_deterministic(self) -> None:
        manifest = dataset_manifest_v2()
        restored = DatasetManifestV2.from_json(manifest.to_json())
        self.assertEqual(restored.to_dict(), manifest.to_dict())
        self.assertEqual(restored.manifest_id, manifest.manifest_id)
        self.assertRegex(manifest.manifest_id, r"^[a-f0-9]{64}$")

    def test_multiple_file_roles_and_independent_label_availability(self) -> None:
        manifest = dataset_manifest_v2()
        self.assertEqual(
            [item.logical_file_role for item in manifest.files],
            ["normal_measurements", "labeled_evaluation"],
        )
        self.assertNotEqual(
            manifest.files[0].label_availability,
            manifest.files[1].label_availability,
        )

    def test_unknown_fields_and_unselected_process_scope_are_explicit(self) -> None:
        manifest = dataset_manifest_v2()
        view = data_view_manifest_v2(process_scope=None)
        self.assertEqual(manifest.dataset_version_or_edition, "unverified")
        self.assertEqual(manifest.provenance_status, ProvenanceStatusV2.UNVERIFIED)
        self.assertEqual(manifest.available_process_ids, ("process_a", "process_b"))
        self.assertIsNone(view.process_scope)

    def test_external_mapping_inputs_are_frozen_without_source_mutation(self) -> None:
        source_config = {"steps": [{"name": "identity"}]}
        before = copy.deepcopy(source_config)
        base = data_view_manifest_v2()
        view = DataViewManifestV2(
            view_kind=DataViewKindV2.CANONICAL_RULE,
            source_dataset_manifest_id=base.source_dataset_manifest_id,
            process_scope=None,
            sampling_interval_seconds=1.0,
            preprocessing_config=source_config,
            aggregation=base.aggregation,
            feature_order_hash=HASH_C,
            second_level_rule_calibration_allowed=True,
            provenance_status=ProvenanceStatusV2.VERIFIED,
            creation_metadata=creation_metadata(),
        )
        source_config["steps"][0]["name"] = "changed"
        self.assertEqual(before, {"steps": [{"name": "identity"}]})
        self.assertEqual(
            view.to_dict()["preprocessing_config"],
            {"steps": [{"name": "identity"}]},
        )

    def test_unsafe_relative_paths_and_bad_hashes_fail(self) -> None:
        template = dataset_manifest_v2().files[0]
        for path in ("../escape.csv", "/absolute.csv", "C:/drive.csv", "a\\b.csv"):
            with self.subTest(path=path), self.assertRaises(DataContractV2Error):
                DatasetFileV2(
                    logical_file_role=template.logical_file_role,
                    relative_local_path=path,
                    sha256=template.sha256,
                    byte_size=template.byte_size,
                    row_count=template.row_count,
                    compression=template.compression,
                    time_range=None,
                    process_ids=None,
                    label_availability=None,
                    provenance_status=template.provenance_status,
                )
        with self.assertRaises(DataContractV2Error):
            DatasetFileV2(
                logical_file_role="bad_hash",
                relative_local_path="bad.csv",
                sha256="A" * 64,
                byte_size=0,
                row_count=0,
                compression=template.compression,
                time_range=None,
                process_ids=None,
                label_availability=None,
                provenance_status=template.provenance_status,
            )

    def test_time_range_rejects_malformed_or_reversed_timestamps(self) -> None:
        with self.assertRaises(DataContractV2Error):
            TimeRangeV2("not-a-time", "2026-01-01T00:00:00Z")
        with self.assertRaises(DataContractV2Error):
            TimeRangeV2(
                "2026-01-02T00:00:00Z",
                "2026-01-01T00:00:00Z",
            )

    def test_downsampling_requires_explicit_description_and_blocks_calibration(
        self,
    ) -> None:
        base = data_view_manifest_v2()
        with self.assertRaises(DataContractV2Error):
            AggregationDescriptionV2(
                method="mean",
                source_sampling_interval_seconds=1.0,
                output_sampling_interval_seconds=5.0,
                explicit=False,
                description="Implicit downsampling is prohibited.",
            )
        downsampled = DataViewManifestV2(
            view_kind=DataViewKindV2.GDN,
            source_dataset_manifest_id=base.source_dataset_manifest_id,
            process_scope=("process_a",),
            sampling_interval_seconds=5.0,
            preprocessing_config={},
            aggregation=AggregationDescriptionV2(
                method="mean",
                source_sampling_interval_seconds=1.0,
                output_sampling_interval_seconds=5.0,
                explicit=True,
                description="Explicit synthetic downsampling.",
            ),
            feature_order_hash=HASH_C,
            second_level_rule_calibration_allowed=False,
            provenance_status=ProvenanceStatusV2.VERIFIED,
            creation_metadata=creation_metadata(),
        )
        with self.assertRaises(DataContractV2Error):
            assert_second_level_rule_calibration_compatible(downsampled)
        assert_second_level_rule_calibration_compatible(base)

    def test_contract_source_contains_no_dataset_specific_assumption(self) -> None:
        source = read_public_text(ROOT / "src/paperworks/data/contracts_v2.py")
        ast.parse(source)
        lowered = source.lower()
        for marker in ("swat", "wadi", "hai 23", "kpi"):
            self.assertNotIn(marker, lowered)


if __name__ == "__main__":
    unittest.main()
