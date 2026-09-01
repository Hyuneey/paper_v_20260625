from __future__ import annotations

from hashlib import sha256
import inspect
import json
import tracemalloc
import unittest

import numpy as np

from paperworks.validation_v2 import isolation_forest_v1 as isolation
from paperworks.validation_v2 import pca_spe_v2 as pca
from tests.test_validation_v2_isolation_forest_v1 import matrix_input


class DetectorStreamingHashV1Tests(unittest.TestCase):
    def test_streaming_hash_is_exactly_legacy_tobytes_hash(self) -> None:
        prefix = b'{"contract":"synthetic"}'
        arrays = (
            np.ascontiguousarray(np.arange(37, dtype=np.float64)),
            np.ascontiguousarray(np.arange(3 * 37, dtype=np.float64).reshape(3, 37)),
            np.ascontiguousarray(np.asarray([0.0, -0.0, np.pi], dtype=np.float64)),
        )
        for array in arrays:
            with self.subTest(shape=array.shape):
                legacy = sha256(prefix + array.tobytes(order="C")).hexdigest()
                observed = isolation._sha256_contiguous_array_v1(
                    array, prefix=prefix
                )
                self.assertEqual(observed, legacy)

    def test_non_contiguous_and_non_bytes_prefix_fail_closed(self) -> None:
        non_contiguous = np.arange(40, dtype=np.float64).reshape(5, 8)[:, ::2]
        self.assertFalse(non_contiguous.flags.c_contiguous)
        with self.assertRaisesRegex(
            isolation.IsolationForestContractError, "C-contiguous"
        ):
            isolation._sha256_contiguous_array_v1(non_contiguous)
        with self.assertRaisesRegex(
            isolation.IsolationForestContractError, "prefix"
        ):
            isolation._sha256_contiguous_array_v1(
                np.arange(3, dtype=np.float64), prefix=bytearray(b"x")  # type: ignore[arg-type]
            )

    def test_matrix_binding_hash_matches_legacy_contract(self) -> None:
        value = matrix_input("NORMAL_FIT_PRIMARY", 32, 71)
        matrix, binding = isolation._normalize_matrix_input(
            value, expected_role="NORMAL_FIT_PRIMARY"
        )
        prefix = json.dumps(
            {
                "shape": [int(matrix.shape[0]), int(matrix.shape[1])],
                "feature_ids": list(value.feature_ids),
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        legacy = sha256(prefix + matrix.tobytes(order="C")).hexdigest()
        self.assertEqual(binding.matrix_sha256, legacy)

    def test_streaming_path_avoids_full_array_bytes_allocation(self) -> None:
        array = np.ascontiguousarray(np.arange(1_000_000, dtype=np.float64))
        prefix = b"synthetic-prefix"

        tracemalloc.start()
        streaming = isolation._sha256_contiguous_array_v1(array, prefix=prefix)
        _current, streaming_peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        tracemalloc.start()
        legacy = sha256(prefix + array.tobytes(order="C")).hexdigest()
        _current, legacy_peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        self.assertEqual(streaming, legacy)
        self.assertLess(streaming_peak * 4, legacy_peak)

    def test_detector_hashing_call_sites_no_longer_use_tobytes(self) -> None:
        for function in (
            isolation._normalize_matrix_input,
            isolation.fit_isolation_forest_v1,
            isolation.calibrate_isolation_forest_threshold_v1,
            pca.calibrate_pca_spe_threshold_v2,
        ):
            with self.subTest(function=function.__name__):
                self.assertNotIn("tobytes", inspect.getsource(function))


if __name__ == "__main__":
    unittest.main()
