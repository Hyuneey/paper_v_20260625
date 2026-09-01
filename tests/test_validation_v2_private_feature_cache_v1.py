from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import numpy as np

from paperworks.validation_v2.private_feature_cache_v1 import (
    PrivateFeatureCacheError,
    persist_private_feature_cache_v1,
    reopen_private_feature_cache_v1,
)
from paperworks.v6.task039e3_r2r_d0_detector_design_v1 import P1_FEATURE_ORDER


H = "a" * 64
COMMIT = "1" * 40


class ValidationV2PrivateFeatureCacheTests(unittest.TestCase):
    def persist(self, repository: Path, private: Path, **overrides):
        values = dict(
            repository_root=repository,
            private_root=private,
            split_id="train1",
            file_id="hai-train1.csv",
            file_content_sha256=H,
            parser_source_sha256="b" * 64,
            sampling_contract_sha256="c" * 64,
            source_commit=COMMIT,
            feature_ids=P1_FEATURE_ORDER,
            matrix=np.arange(4 * 37, dtype=np.float64).reshape(4, 37),
        )
        values.update(overrides)
        return persist_private_feature_cache_v1(**values)

    def test_atomic_private_cache_reopens_with_path_free_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            repository = base / "repository"
            private = base / "private"
            repository.mkdir()
            binding = self.persist(repository, private)
            with reopen_private_feature_cache_v1(binding) as replay:
                self.assertTrue(np.array_equal(replay.matrix, np.arange(4 * 37, dtype=np.float64).reshape(4, 37)))
                self.assertFalse(bool(replay.matrix.flags.writeable))
            document = binding.receipt.to_document()
            self.assertNotIn(str(private), str(document))
            self.assertFalse(document["labels_accessed"])
            self.assertEqual(document["test1_accesses"], 0)
            self.assertEqual(document["test2_accesses"], 0)
            self.assertFalse(document["scientific_authority"])

    def test_non_normal_split_and_repository_storage_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            repository = base / "repository"
            repository.mkdir()
            with self.assertRaisesRegex(PrivateFeatureCacheError, "NON_NORMAL_SPLIT"):
                self.persist(repository, base / "private", split_id="test1")
            with self.assertRaisesRegex(PrivateFeatureCacheError, "INSIDE_REPOSITORY"):
                self.persist(repository, repository / "cache")

    def test_mutated_cache_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            repository = base / "repository"
            private = base / "private"
            repository.mkdir()
            binding = self.persist(repository, private)
            with binding.cache_path.open("ab") as stream:
                stream.write(b"mutation")
            with self.assertRaisesRegex(PrivateFeatureCacheError, "BYTE_SIZE_MISMATCH"):
                reopen_private_feature_cache_v1(binding)

    def test_no_overwrite_and_exact_feature_order(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            repository = base / "repository"
            private = base / "private"
            repository.mkdir()
            self.persist(repository, private)
            with self.assertRaisesRegex(PrivateFeatureCacheError, "EXISTING_OR_PARTIAL"):
                self.persist(repository, private)
            other = base / "private-2"
            with self.assertRaisesRegex(PrivateFeatureCacheError, "FEATURE_ORDER"):
                self.persist(repository, other, feature_ids=tuple(reversed(P1_FEATURE_ORDER)))


if __name__ == "__main__":
    unittest.main()
