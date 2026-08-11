from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from paperworks.profiling.task039d1_fit_v1 import (
    AUTHORIZED_RELATIVE_FILES,
    SELECTED_COLUMNS,
    DataAccessStateV1,
    TASK039D1Error,
    assert_public_payload_safe_v1,
    load_expected_file_identities_v1,
    reject_br2_pair_input_v1,
    validate_external_roots_v1,
)


ROOT = Path(__file__).resolve().parents[1]


class Task039D1DataBoundaryTests(unittest.TestCase):
    def test_only_train1_train2_exact_paths_and_24_columns_are_authorized(self) -> None:
        state = DataAccessStateV1()
        for name in AUTHORIZED_RELATIVE_FILES:
            state.authorize(name, SELECTED_COLUMNS)
        with self.assertRaises(TASK039D1Error):
            state.authorize(AUTHORIZED_RELATIVE_FILES[0], SELECTED_COLUMNS + ("P2_X",))
        self.assertEqual(state.prohibited_access_count, 1)

    def test_train3_train4_test_labels_and_other_process_are_rejected(self) -> None:
        for name in (
            "hai-23.05/hai-train3.csv", "hai-23.05/hai-train4.csv",
            "hai-23.05/hai-test1.csv", "hai-23.05/label-test1.csv",
            "attacks", "P2", "P3", "P4",
        ):
            state = DataAccessStateV1()
            with self.subTest(name=name), self.assertRaises(TASK039D1Error):
                state.authorize(name, SELECTED_COLUMNS)
            self.assertEqual(state.prohibited_access_count, 1)

    def test_path_traversal_and_absolute_paths_rejected(self) -> None:
        state = DataAccessStateV1()
        for name in ("../hai-train1.csv", "C:/private/hai-train1.csv"):
            with self.subTest(name=name), self.assertRaises(TASK039D1Error):
                state.authorize(name, SELECTED_COLUMNS)

    def test_br2_pair_artifacts_rejected(self) -> None:
        for name in (
            "fit_supported_pairs", "confirmed_pairs", "selected_horizons",
            "selected_directions", "pair_consistencies", "pair_effect_ratios",
            "source_numeric_parameters", "target_numeric_parameters", "private_relation_ledger",
        ):
            with self.subTest(name=name), self.assertRaises(TASK039D1Error):
                reject_br2_pair_input_v1(artifact_name=name)

    def test_roots_inside_repo_and_identical_roots_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            outside = Path(folder)
            with self.assertRaises(TASK039D1Error):
                validate_external_roots_v1(
                    repository_root=ROOT,
                    data_root_value=str(ROOT),
                    private_root_value=str(outside / "private"),
                )
            with self.assertRaises(TASK039D1Error):
                validate_external_roots_v1(
                    repository_root=ROOT,
                    data_root_value=str(outside),
                    private_root_value=str(outside),
                )

    def test_public_raw_numeric_path_and_event_fields_rejected(self) -> None:
        for payload in (
            {"source_noise_scale": 1.0}, {"raw_windows": []}, {"event_index": 3},
            {"note": "C:\\private\\data.csv"},
        ):
            with self.subTest(payload=payload), self.assertRaises(TASK039D1Error):
                assert_public_payload_safe_v1(payload)

    def test_public_dataset_manifest_bindings_are_exact_without_data_access(self) -> None:
        records = load_expected_file_identities_v1(ROOT)
        self.assertEqual(tuple(item["relative_path"] for item in records), AUTHORIZED_RELATIVE_FILES)
        self.assertEqual([item["row_count"] for item in records], [280800, 291600])


if __name__ == "__main__":
    unittest.main()
