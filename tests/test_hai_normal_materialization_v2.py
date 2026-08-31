from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from paperworks.data import hai_normal_materialization_v2 as subject


def structural_records() -> list[dict[str, object]]:
    return [
        {
            "symbolic_id": item.symbolic_id,
            "relative_path": item.relative_path,
            "sha256": item.sha256,
            "size_bytes": item.size_bytes,
            "row_count": item.row_count,
            "header_field_count": 87,
            "header_sha256": subject.CANONICAL_HEADER_HASH,
            "timestamp_field": "timestamp",
            "nominal_timestamp_delta_seconds": 1.0,
            "timestamps_strictly_increasing": True,
            "malformed_row_count": 0,
            "inconsistent_field_count_rows": 0,
            "normal_file_status": "normal_only_verified",
        }
        for item in subject.NORMAL_SPLITS
    ]


class HAINormalMaterializationV2Tests(unittest.TestCase):
    def test_exact_four_normal_authority(self) -> None:
        self.assertEqual(
            [item.symbolic_id for item in subject.NORMAL_SPLITS],
            ["HAI_TRAIN1", "HAI_TRAIN2", "HAI_TRAIN3", "HAI_TRAIN4"],
        )
        self.assertEqual(len(subject.AUTHORIZED_RELATIVE_PATHS), 4)
        self.assertTrue(all("train" in path and "test" not in path for path in subject.AUTHORIZED_RELATIVE_PATHS))
        subject.require_authorized_members(tuple(item.relative_path for item in subject.NORMAL_SPLITS))

    def test_no_caller_subset_or_extra_member(self) -> None:
        valid = tuple(item.relative_path for item in subject.NORMAL_SPLITS)
        for invalid in (
            valid[:3],
            tuple(reversed(valid)),
            valid + ("hai-23.05/hai-test1.csv",),
            valid + ("hai-23.05/hai-test2.csv",),
            valid + ("hai-23.05/label-test1.csv",),
            valid + ("../hai-train1.csv",),
        ):
            with self.assertRaisesRegex(subject.HAINormalMaterializationV2Error, subject.BLOCKED_METADATA):
                subject.require_authorized_members(invalid)

    def test_public_receipt_is_self_hashed_and_public_safe(self) -> None:
        receipt = subject.build_public_receipt(
            execution_commit="a" * 40,
            code_hash="b" * 64,
            private_manifest_hash="c" * 64,
            structural_records=structural_records(),
            created_at_utc="2026-08-31T00:00:00Z",
        )
        self.assertEqual(subject.validate_public_receipt(receipt), receipt["self_hash"])
        encoded = json.dumps(receipt, ensure_ascii=False)
        self.assertNotIn("absolute_path", encoded)
        self.assertNotIn("signed", encoded.lower())
        self.assertNotIn("credential", encoded.lower())
        self.assertEqual(receipt["metadata_phase"], "REUSED_COMMITTED_SANITIZED_METADATA_RECEIPT")
        counters = receipt["access_counters"]
        for key in (
            "test1_download", "test1_open", "test1_hash", "test1_parse",
            "test2_download", "test2_stat", "test2_open", "test2_hash", "test2_parse",
            "label_access", "held_out_access", "private_exposures",
        ):
            self.assertEqual(counters[key], 0)

    def test_mutation_hash_schema_and_access_counter_rejected(self) -> None:
        receipt = subject.build_public_receipt(
            execution_commit="a" * 40,
            code_hash="b" * 64,
            private_manifest_hash="c" * 64,
            structural_records=structural_records(),
            created_at_utc="2026-08-31T00:00:00Z",
        )
        mutations = []
        changed = copy.deepcopy(receipt)
        changed["normal_splits"][0]["size_bytes"] += 1
        mutations.append(changed)
        changed = copy.deepcopy(receipt)
        changed["access_counters"]["test1_open"] = 1
        changed["self_hash"] = subject.canonical_hash(changed)
        mutations.append(changed)
        changed = copy.deepcopy(receipt)
        changed["official_payload_route"] = "unofficial/mirror"
        changed["self_hash"] = subject.canonical_hash(changed)
        mutations.append(changed)
        for value in mutations:
            with self.assertRaises(subject.HAINormalMaterializationV2Error):
                subject.validate_public_receipt(value)

    def test_runner_has_fixed_allowlist_and_no_full_historical_download(self) -> None:
        source = (Path(__file__).resolve().parents[1] / "scripts/materialize_hai_2305_normal_v2.py").read_text(encoding="utf-8")
        self.assertIn("raw_specs()", source)
        self.assertNotIn("command_download", source)
        self.assertNotIn("materialize-lfs", source)
        self.assertNotIn("HAIEnd", source)


if __name__ == "__main__":
    unittest.main()
