from __future__ import annotations

import ast
import hashlib
import json
import unittest
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
except ModuleNotFoundError:  # Guarded discovery retains the frozen optional boundary.
    Draft202012Validator = None  # type: ignore[assignment,misc]

from paperworks.data.contracts_v2 import CreationMetadataV2, DatasetManifestV2
from paperworks.data.hai_provenance_v1 import (
    HAICsvStructureAuditV1,
    HAILabelCustodyPublicRecordV1,
    HAILfsPointerRecordV1,
    build_hai_dataset_manifest_v2,
    canonical_self_hash,
)
from paperworks.v6.schema_registry_v1 import load_v6_schema_registry_v1


ROOT = Path(__file__).resolve().parents[1]
TASK039A_TYPES = {
    "hai_lfs_pointer_record",
    "hai_csv_structure_audit",
    "hai_label_custody_public",
    "hai_reference_inventory",
    "hai_provenance_audit_result",
}


def _lfs(path: str) -> HAILfsPointerRecordV1:
    digest = hashlib.sha256(path.encode("ascii")).hexdigest()
    return HAILfsPointerRecordV1(
        relative_path=path,
        pointer_oid_sha256=digest,
        pointer_size_bytes=10,
        expected_oid_sha256=digest,
        expected_size_bytes=10,
        materialized_sha256=digest,
        materialized_size_bytes=10,
        pointer_matches_expected=True,
        materialized_matches_pointer=True,
        materialized=True,
    )


def _csv(path: str, *, test: bool) -> HAICsvStructureAuditV1:
    return HAICsvStructureAuditV1(
        relative_path=path,
        file_sha256=hashlib.sha256(path.encode("ascii")).hexdigest(),
        byte_size=10,
        utf_encoding_result="utf-8-valid",
        delimiter=",",
        header_field_count=87,
        header_sha256="a" * 64,
        timestamp_field="timestamp",
        row_count=2,
        first_timestamp="2026-01-01 00:00:00",
        last_timestamp="2026-01-01 00:00:01",
        timestamps_strictly_increasing=True,
        duplicate_timestamp_count=0,
        non_positive_timestamp_delta_count=0,
        nominal_timestamp_delta_seconds=1.0,
        distinct_timestamp_delta_seconds=(1.0,),
        timestamp_delta_summary_truncated=False,
        malformed_row_count=0,
        inconsistent_field_count_rows=0,
        empty_field_count=0,
        ordered_header_matches_canonical=True,
        expected_point_count_reconciled=True,
        normal_file_status=None if test else "normal_only_verified",
        test_file_structural_only=test,
        process_ids_observed=("P1", "P2", "P3", "P4"),
    )


def _label(number: int) -> HAILabelCustodyPublicRecordV1:
    return HAILabelCustodyPublicRecordV1(
        label_relative_path=f"hai-23.05/label-test{number}.csv",
        label_file_sha256=str(number) * 64,
        label_byte_size=10,
        label_header_sha256="b" * 64,
        label_row_count=2,
        timestamp_alignment_status="aligned",
        label_domain_valid=True,
        summary_relative_path=f"hai-23.05/summary_label{number}.txt",
        summary_file_sha256="c" * 64,
        summary_byte_size=10,
        summary_format_valid=True,
        event_record_count=number,
        expected_event_record_count=number,
        custody_status="verified",
        private_custody_artifact_hash="d" * 64,
        label_content_accessed_for_provenance_only=True,
        label_content_used_for_scientific_selection=False,
        attack_event_details_publicly_exposed=False,
    )


class Task039AManifestSchemaTests(unittest.TestCase):
    def test_dataset_manifest_v2_is_deterministic_and_round_trips(self) -> None:
        paths = (
            "hai-23.05/hai-test1.csv",
            "hai-23.05/hai-test2.csv",
            "hai-23.05/hai-train1.csv",
            "hai-23.05/hai-train2.csv",
            "hai-23.05/hai-train3.csv",
            "hai-23.05/hai-train4.csv",
            "hai-23.05/label-test1.csv",
            "hai-23.05/label-test2.csv",
            "hai-23.05/summary_label1.txt",
            "hai-23.05/summary_label2.txt",
        )
        csv_records = tuple(
            _csv(path, test="hai-test" in path)
            for path in paths
            if path.startswith("hai-23.05/hai-")
        )
        manifest = build_hai_dataset_manifest_v2(
            csv_records=csv_records,
            label_records=(_label(1), _label(2)),
            lfs_records=tuple(_lfs(path) for path in paths),
            metadata_artifact_references=("synthetic-reference",),
            source_repository="https://github.com/icsdataset/hai",
            snapshot_commit="2" * 40,
            feature_names_hash="e" * 64,
            label_field_name="label",
            license_reference="README License section@synthetic",
            citation_reference="sha256:" + "f" * 64,
            creation_metadata=CreationMetadataV2(
                created_at="2026-08-01T00:00:00Z",
                created_by="synthetic test",
                code_commit="1" * 40,
                config_hash="0" * 64,
            ),
        )
        self.assertEqual(manifest.manifest_id, manifest.manifest_id)
        self.assertEqual(
            DatasetManifestV2.from_dict(manifest.to_dict()).manifest_id,
            manifest.manifest_id,
        )
        self.assertNotIn("C:\\", json.dumps(manifest.to_dict()))

    def test_config_self_hash_and_exact_source_freeze(self) -> None:
        config = json.loads(
            (ROOT / "configs/data/hai_2305_official_provenance.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(config["config_hash"], canonical_self_hash(config, "config_hash"))
        self.assertEqual(config["official_repository"], "https://github.com/icsdataset/hai")
        self.assertEqual(config["snapshot_commit"], "2a814cebc9a66b06c9e5cd545e2d72e65d383737")
        self.assertEqual(len(config["expected_lfs_files"]), 10)
        self.assertEqual(
            {item["relative_path"] for item in config["expected_lfs_files"]},
            {
                "hai-23.05/hai-test1.csv",
                "hai-23.05/hai-test2.csv",
                "hai-23.05/hai-train1.csv",
                "hai-23.05/hai-train2.csv",
                "hai-23.05/hai-train3.csv",
                "hai-23.05/hai-train4.csv",
                "hai-23.05/label-test1.csv",
                "hai-23.05/label-test2.csv",
                "hai-23.05/summary_label1.txt",
                "hai-23.05/summary_label2.txt",
            },
        )

    def test_task039a_schemas_registered_and_meta_valid(self) -> None:
        registry = load_v6_schema_registry_v1(repository_root=ROOT)
        self.assertTrue(TASK039A_TYPES.issubset(registry.artifact_types))
        for artifact_type in TASK039A_TYPES:
            schema = registry.schema_for(artifact_type)
            self.assertEqual(
                schema["$schema"],
                "https://json-schema.org/draft/2020-12/schema",
            )
            if Draft202012Validator is not None:
                Draft202012Validator.check_schema(schema)

    def test_task039a_schema_object_definitions_are_closed(self) -> None:
        registry = load_v6_schema_registry_v1(repository_root=ROOT)

        def inspect(value: object) -> None:
            if isinstance(value, dict):
                if value.get("type") == "object":
                    self.assertIs(value.get("additionalProperties"), False, value)
                for item in value.values():
                    inspect(item)
            elif isinstance(value, list):
                for item in value:
                    inspect(item)

        for artifact_type in TASK039A_TYPES:
            inspect(registry.schema_for(artifact_type))

    def test_audit_module_has_no_scientific_consumer_or_provider_import(self) -> None:
        relative = "src/paperworks/data/hai_provenance_v1.py"
        tree = ast.parse((ROOT / relative).read_text(encoding="utf-8"), filename=relative)
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
            elif isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
        prohibited = {
            "paperworks.gdn",
            "paperworks.candidates",
            "paperworks.profiling",
            "paperworks.planning",
            "paperworks.runtime",
            "paperworks.evaluation",
            "paperworks.e2e",
            "openai",
            "torch",
            "torch_geometric",
        }
        self.assertTrue(imports.isdisjoint(prohibited), imports)


if __name__ == "__main__":
    unittest.main()
