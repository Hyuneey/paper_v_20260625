from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from paperworks.metadata import (
    MetadataRegistry,
    MetadataSourceMethod,
    MetadataValidationError,
    PhysicalType,
    ReviewStatus,
    ValueType,
    VariableMetadata,
    VariableRole,
    load_metadata_json,
    suggest_metadata_from_name,
    validate_feature_coverage,
)


EXPECTED_SWAT_FEATURES = (
    "FIT101",
    "LIT101",
    "MV101",
    "P101",
    "P102",
    "AIT201",
    "AIT202",
    "AIT203",
    "FIT201",
    "MV201",
    "P201",
    "P202",
    "P203",
    "P204",
    "P205",
    "P206",
    "DPIT301",
    "FIT301",
    "LIT301",
    "MV301",
    "MV302",
    "MV303",
    "MV304",
    "P301",
    "P302",
    "AIT401",
    "AIT402",
    "FIT401",
    "LIT401",
    "P401",
    "P402",
    "P403",
    "P404",
    "UV401",
    "AIT501",
    "AIT502",
    "AIT503",
    "AIT504",
    "FIT501",
    "FIT502",
    "FIT503",
    "FIT504",
    "P501",
    "P502",
    "PIT501",
    "PIT502",
    "PIT503",
    "FIT601",
    "P601",
    "P602",
    "P603",
)


def synthetic_sensor(name: str = "SENSOR_A") -> VariableMetadata:
    return VariableMetadata(
        name=name,
        role=VariableRole.SENSOR,
        value_type=ValueType.CONTINUOUS,
        physical_type=PhysicalType.FLOW,
        source_method=MetadataSourceMethod.MANUAL_REVIEW,
        source_reference="synthetic fixture",
        description="Synthetic flow sensor fixture.",
        confidence=1.0,
        review_status=ReviewStatus.REVIEWED,
    )


class MetadataSchemaTests(unittest.TestCase):
    def test_round_trip_preserves_provenance_and_review_status(self) -> None:
        registry = MetadataRegistry(
            [
                synthetic_sensor(),
                VariableMetadata(
                    name="ACTUATOR_A",
                    role=VariableRole.ACTUATOR,
                    value_type=ValueType.BINARY,
                    physical_type=PhysicalType.VALVE,
                    allowed_states=("closed", "open"),
                    description="Synthetic valve actuator fixture.",
                    source_method=MetadataSourceMethod.NAME_PATTERN,
                    source_reference="synthetic fixture",
                    confidence=0.6,
                    review_status=ReviewStatus.UNREVIEWED,
                ),
            ]
        )
        restored = MetadataRegistry.from_json(registry.to_json())
        self.assertEqual(restored.get("ACTUATOR_A").source_method, MetadataSourceMethod.NAME_PATTERN)
        self.assertEqual(restored.get("ACTUATOR_A").review_status, ReviewStatus.UNREVIEWED)
        self.assertEqual(restored.get("ACTUATOR_A").allowed_states, ("closed", "open"))
        self.assertEqual(restored.get("ACTUATOR_A").description, "Synthetic valve actuator fixture.")

    def test_duplicate_name_rejection(self) -> None:
        with self.assertRaises(MetadataValidationError):
            MetadataRegistry([synthetic_sensor("X"), synthetic_sensor("X")])

    def test_invalid_enum_rejection(self) -> None:
        payload = synthetic_sensor().to_dict()
        payload["role"] = "controller"
        with self.assertRaises((ValueError, MetadataValidationError)):
            VariableMetadata.from_dict(payload)

    def test_invalid_role_value_type_combination(self) -> None:
        with self.assertRaises(MetadataValidationError):
            VariableMetadata(
                name="BAD_ACTUATOR",
                role=VariableRole.ACTUATOR,
                value_type=ValueType.CONTINUOUS,
                physical_type=PhysicalType.VALVE,
            )

    def test_blank_description_rejection(self) -> None:
        payload = synthetic_sensor().to_dict()
        payload["description"] = " "
        with self.assertRaises(MetadataValidationError):
            VariableMetadata.from_dict(payload)

    def test_unknown_value_handling_and_coverage_report(self) -> None:
        registry = MetadataRegistry(
            [
                synthetic_sensor("KNOWN"),
                VariableMetadata(
                    name="UNKNOWN_VAR",
                    role=VariableRole.UNKNOWN,
                    value_type=ValueType.UNKNOWN,
                    physical_type=PhysicalType.UNKNOWN,
                    source_method=MetadataSourceMethod.UNKNOWN,
                    review_status=ReviewStatus.UNREVIEWED,
                ),
            ]
        )
        report = registry.coverage_report(("KNOWN", "UNKNOWN_VAR"))
        self.assertTrue(report.is_complete)
        self.assertEqual(report.unknown_field_counts["role"], 1)
        self.assertEqual(report.source_method_counts["unknown"], 1)
        self.assertEqual(report.review_status_counts["unreviewed"], 1)

    def test_inferred_versus_reviewed_provenance(self) -> None:
        inferred = suggest_metadata_from_name("FIT999", source_reference="name parser")
        reviewed = synthetic_sensor("REVIEWED")
        self.assertEqual(inferred.source_method, MetadataSourceMethod.NAME_PATTERN)
        self.assertEqual(inferred.review_status, ReviewStatus.UNREVIEWED)
        self.assertEqual(reviewed.source_method, MetadataSourceMethod.MANUAL_REVIEW)
        self.assertEqual(reviewed.review_status, ReviewStatus.REVIEWED)

    def test_feature_list_mismatch_detection(self) -> None:
        registry = MetadataRegistry([synthetic_sensor("A")])
        with self.assertRaises(MetadataValidationError):
            validate_feature_coverage(registry, ("A", "B"))

    def test_project_swat_metadata_covers_all_features_once(self) -> None:
        registry = load_metadata_json(Path("configs/metadata/swat_variables.json"))
        report = validate_feature_coverage(registry, EXPECTED_SWAT_FEATURES)
        self.assertEqual(len(registry), 51)
        self.assertTrue(report.is_complete)
        self.assertEqual(report.source_method_counts["dataset_documentation"], 51)
        self.assertEqual(report.review_status_counts["unreviewed"], 51)
        self.assertEqual(report.unknown_field_counts["role"], 0)
        self.assertEqual(report.unknown_field_counts["value_type"], 0)
        self.assertEqual(registry.get("FIT101").description, "Measures the flow rate of raw water entering the system.")

    def test_loader_accepts_project_local_metadata_format(self) -> None:
        source = Path("TEMPLATES/VARIABLE_METADATA_TEMPLATE.json")
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "metadata.json"
            target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            registry = load_metadata_json(target)
        self.assertEqual(len(registry), 2)
        self.assertIn("SENSOR_A", registry)


if __name__ == "__main__":
    unittest.main()
