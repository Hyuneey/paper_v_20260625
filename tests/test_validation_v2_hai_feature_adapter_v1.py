from __future__ import annotations

from datetime import datetime, timedelta
from hashlib import sha256
import os
from pathlib import Path
import pickle
import tempfile
import unittest
from unittest.mock import patch

from paperworks.validation_v2 import hai_feature_adapter_v1 as adapter
from paperworks.v6.task039e3_r2r_d0_detector_design_v1 import P1_FEATURE_ORDER


class HAIFeatureAdapterV1Tests(unittest.TestCase):
    def _fixture(self, root: Path, *, break_time: bool = False, nonfinite: bool = False):
        edition = root / "hai-23.05"
        edition.mkdir()
        path = edition / "synthetic.csv"
        filler = tuple(f"X{index:02d}" for index in range(49))
        header = ("timestamp",) + tuple(P1_FEATURE_ORDER) + filler
        start = datetime(2025, 1, 1)
        lines = [",".join(header)]
        for row_index in range(3):
            second = row_index + (1 if break_time and row_index == 2 else 0)
            timestamp = (start + timedelta(seconds=second)).isoformat()
            values = [str(row_index + column / 100) for column in range(37)]
            if nonfinite and row_index == 1:
                values[4] = "nan"
            lines.append(",".join((timestamp, *values, *("0" for _ in filler))))
        payload = ("\n".join(lines) + "\n").encode("utf-8")
        path.write_bytes(payload)
        spec = adapter.HAIFeatureFileSpecV1(
            split_id="train1",
            role="NORMAL_FIT_PRIMARY",
            relative_path="hai-23.05/synthetic.csv",
            sha256_hex=sha256(payload).hexdigest(),
            byte_size=len(payload),
            row_count=3,
            raw_header_sha256=sha256(lines[0].encode("utf-8")).hexdigest(),
            header_field_count=87,
        )
        return path, spec

    def _capability(self, repository: Path, data_root: Path):
        with patch.dict(os.environ, {"HAI_DATA_ROOT": str(data_root)}, clear=False):
            return adapter.resolve_hai_feature_root_capability_v1(repository)

    def test_exact_single_open_parse_returns_private_immutable_frame(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            _path, spec = self._fixture(root)
            capability = self._capability(repository, root)
            self.assertEqual(repr(capability), "HAIFeatureRootCapabilityV1(<redacted>)")
            frame = adapter._load_feature_file_from_spec_v1(capability, spec)
            matrix = frame.numeric_matrix()
            self.assertEqual(matrix.shape, (3, 37))
            self.assertFalse(matrix.flags.writeable)
            self.assertEqual(len(frame.file_local_timestamps()), 3)
            receipt = frame.receipt.to_dict()
            self.assertEqual(receipt["file_open_count"], 1)
            self.assertFalse(receipt["labels_accessed"])
            self.assertEqual(receipt["test2_accesses"], 0)
            self.assertNotIn(str(root), repr(receipt))
            with self.assertRaises(ValueError):
                matrix[0, 0] = 999.0
            with self.assertRaises(adapter.HAIFeatureAdapterError):
                pickle.dumps(frame)

    def test_continuity_and_nonfinite_values_fail_closed_without_path(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        for kwargs, code in (
            ({"break_time": True}, "FEATURE_TIMESTAMP_CONTINUITY_REJECTED"),
            ({"nonfinite": True}, "FEATURE_NONFINITE_REJECTED"),
        ):
            with self.subTest(code=code), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                _path, spec = self._fixture(root, **kwargs)
                capability = self._capability(repository, root)
                with self.assertRaisesRegex(adapter.HAIFeatureAdapterError, f"^{code}$") as raised:
                    adapter._load_feature_file_from_spec_v1(capability, spec)
                self.assertNotIn(str(root), str(raised.exception))

    def test_wrong_hash_and_duplicate_open_fail_closed(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            _path, spec = self._fixture(root)
            capability = self._capability(repository, root)
            wrong = adapter.HAIFeatureFileSpecV1(
                split_id=spec.split_id,
                role=spec.role,
                relative_path=spec.relative_path,
                sha256_hex="0" * 64,
                byte_size=spec.byte_size,
                row_count=spec.row_count,
                raw_header_sha256=spec.raw_header_sha256,
                header_field_count=spec.header_field_count,
            )
            with self.assertRaisesRegex(adapter.HAIFeatureAdapterError, "FEATURE_FILE_IDENTITY_REJECTED"):
                adapter._load_feature_file_from_spec_v1(capability, wrong)
            ledger = adapter.HAIFeatureAccessLedgerV1(experiment_id="SYNTHETIC")
            ledger.authorize_once("train1")
            with self.assertRaisesRegex(adapter.HAIFeatureAdapterError, "DUPLICATE_FEATURE_FILE_OPEN_REJECTED"):
                ledger.authorize_once("train1")
            ledger.mark_labels_accessed()
            with self.assertRaisesRegex(adapter.HAIFeatureAdapterError, "FEATURE_ACCESS_AFTER_LABELS_REJECTED"):
                ledger.authorize_once("train2")

    def test_root_inside_repository_and_missing_binding_are_rejected(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        with patch.dict(os.environ, {}, clear=True), patch(
            "paperworks.validation_v2.hai_feature_adapter_v1._binding_from_file",
            return_value=None,
        ):
            with self.assertRaisesRegex(adapter.HAIFeatureAdapterError, "HAI_DATA_ROOT_BINDING_REQUIRED"):
                adapter.resolve_hai_feature_root_capability_v1(repository)
        local = repository / ".adapter-test-root"
        local.mkdir(exist_ok=False)
        try:
            (local / "hai-23.05").mkdir()
            with patch.dict(os.environ, {"HAI_DATA_ROOT": str(local)}, clear=False):
                with self.assertRaisesRegex(adapter.HAIFeatureAdapterError, "FEATURE_ROOT_INSIDE_REPOSITORY_REJECTED"):
                    adapter.resolve_hai_feature_root_capability_v1(repository)
        finally:
            (local / "hai-23.05").rmdir()
            local.rmdir()

    def test_no_label_or_heldout_mapping_and_public_specs_are_closed(self) -> None:
        specs = adapter.authorized_hai_feature_specs_v1()
        self.assertEqual({item["split_id"] for item in specs}, {"train1", "train2", "train3", "train4", "test1"})
        rendered = repr(specs).lower()
        self.assertNotIn("label-test", rendered)
        self.assertNotIn("test2", rendered)
        self.assertNotIn("heldout", rendered)
        self.assertEqual(len(tuple(P1_FEATURE_ORDER)), 37)


if __name__ == "__main__":
    unittest.main()
