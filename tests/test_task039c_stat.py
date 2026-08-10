from __future__ import annotations

import json
import hashlib
import math
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from paperworks.candidates.statistical_candidate_discovery_v1 import (
    EXPECTED_C0_PROTOCOL_HASH,
    EXPECTED_FILES,
    EXPECTED_HORIZONS,
    EXPECTED_PAIR_COUNT,
    EXPECTED_PAIR_UNIVERSE_HASH,
    EXPECTED_SOURCE_IDENTITY_HASH,
    EXPECTED_STAT_POLICY_HASH,
    EXPECTED_TARGET_IDENTITY_HASH,
    PairStatisticalEvidenceV1,
    ExpectedFileIdentityV1,
    STATDataAccessLedgerV1,
    StatisticalCandidateDiscoveryError,
    assert_public_stat_payload_safe_v1,
    assert_stat_candidate_in_universe_v1,
    authorize_stat_value_request_v1,
    build_public_result_v1,
    file_local_differences_v1,
    load_frozen_c0_bundle_v1,
    pearson_correlation_reference_v1,
    read_authorized_stat_file_v1,
    rank_pair_evidence_v1,
    reference_file_lagged_correlation_v1,
    reject_br2_pair_supervision_v1,
    select_pair_horizon_v1,
    vectorized_file_lagged_correlations_v1,
    verify_vectorized_parity_v1,
)
from paperworks.v6.common import stable_hash_v1


HASH = "a" * 64
COMMIT = "b" * 40
CREATED_AT = "2026-08-10T00:00:00+00:00"


def _pair(
    source: str,
    target: str,
    correlations: dict[int, tuple[float | None, float | None]],
) -> PairStatisticalEvidenceV1:
    horizons, selection, sign = select_pair_horizon_v1(correlations)
    return PairStatisticalEvidenceV1(source, target, horizons, selection, sign)


def _stable_correlations(value: float = 0.2) -> dict[int, tuple[float, float]]:
    return {horizon: (value, value * 1.5) for horizon in EXPECTED_HORIZONS}


def _unstable_correlations() -> dict[int, tuple[float, float]]:
    return {horizon: (0.2, -0.2) for horizon in EXPECTED_HORIZONS}


class Task039CSTATTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bundle = load_frozen_c0_bundle_v1(ROOT)

    def test_exact_frozen_universe_and_protocol_hashes(self) -> None:
        universe = self.bundle.universe_policy
        self.assertEqual(self.bundle.artifact_hash, EXPECTED_C0_PROTOCOL_HASH)
        self.assertEqual(
            self.bundle.statistical_policy.artifact_hash, EXPECTED_STAT_POLICY_HASH
        )
        self.assertEqual(universe.source_identity_list_hash, EXPECTED_SOURCE_IDENTITY_HASH)
        self.assertEqual(universe.target_identity_list_hash, EXPECTED_TARGET_IDENTITY_HASH)
        self.assertEqual(universe.eligible_pair_universe_hash, EXPECTED_PAIR_UNIVERSE_HASH)
        self.assertEqual(universe.eligible_pair_count, EXPECTED_PAIR_COUNT)

    def test_out_of_universe_rejected(self) -> None:
        with self.assertRaisesRegex(
            StatisticalCandidateDiscoveryError, "failed_stat_protocol_compliance"
        ):
            assert_stat_candidate_in_universe_v1(
                self.bundle, "P1_UNKNOWN", self.bundle.universe_policy.target_variables[0]
            )

    def test_train1_and_train2_are_allowed(self) -> None:
        source = self.bundle.universe_policy.source_variables[0]
        for relative in EXPECTED_FILES:
            authorize_stat_value_request_v1(
                bundle=self.bundle,
                process_id="P1",
                relative_path=relative,
                columns=(source,),
            )

    def test_reader_checks_identity_selects_only_frozen_columns_and_reads_once(self) -> None:
        columns = (
            self.bundle.universe_policy.source_variables
            + self.bundle.universe_policy.target_variables
        )
        ledger = STATDataAccessLedgerV1(allowed_columns=columns)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for file_index, relative in enumerate(EXPECTED_FILES):
                path = root / Path(relative).name
                lines = [",".join(columns)]
                lines.extend(
                    ",".join(str(float(row + column + file_index)) for column in range(24))
                    for row in range(4)
                )
                payload = ("\n".join(lines) + "\n").encode("utf-8")
                path.write_bytes(payload)
                identity = ExpectedFileIdentityV1(
                    relative_path=relative,
                    sha256=hashlib.sha256(payload).hexdigest(),
                    byte_size=len(payload),
                    row_count=4,
                    feature_names_hash=HASH,
                )
                matrix = read_authorized_stat_file_v1(
                    data_root=root,
                    identity=identity,
                    columns=columns,
                    bundle=self.bundle,
                    ledger=ledger,
                )
                self.assertEqual(matrix.values.shape, (4, 24))
            self.assertTrue(
                all(item["file_open_count"] == 1 for item in ledger.records)
            )
            with self.assertRaisesRegex(
                StatisticalCandidateDiscoveryError, "failed_stat_data_boundary"
            ):
                read_authorized_stat_file_v1(
                    data_root=root,
                    identity=identity,
                    columns=columns,
                    bundle=self.bundle,
                    ledger=ledger,
                )

    def test_train3_train4_test_and_label_are_rejected(self) -> None:
        source = self.bundle.universe_policy.source_variables[0]
        for relative in (
            "hai-23.05/hai-train3.csv",
            "hai-23.05/hai-train4.csv",
            "hai-23.05/hai-test1.csv",
            "hai-23.05/label-test1.csv",
        ):
            with self.subTest(relative=relative):
                with self.assertRaisesRegex(
                    StatisticalCandidateDiscoveryError, "failed_stat_data_boundary"
                ):
                    authorize_stat_value_request_v1(
                        bundle=self.bundle,
                        process_id="P1",
                        relative_path=relative,
                        columns=(source,),
                    )

    def test_other_process_and_columns_are_rejected(self) -> None:
        source = self.bundle.universe_policy.source_variables[0]
        for process_id in ("P2", "P3", "P4"):
            with self.subTest(process_id=process_id):
                with self.assertRaisesRegex(
                    StatisticalCandidateDiscoveryError, "failed_stat_data_boundary"
                ):
                    authorize_stat_value_request_v1(
                        bundle=self.bundle,
                        process_id=process_id,
                        relative_path=EXPECTED_FILES[0],
                        columns=(source,),
                    )
        with self.assertRaisesRegex(
            StatisticalCandidateDiscoveryError, "failed_stat_data_boundary"
        ):
            authorize_stat_value_request_v1(
                bundle=self.bundle,
                process_id="P1",
                relative_path=EXPECTED_FILES[0],
                columns=("P2_X",),
            )

    def test_br2_pair_result_supervision_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            StatisticalCandidateDiscoveryError, "failed_stat_data_boundary"
        ):
            reject_br2_pair_supervision_v1(
                bundle=self.bundle, artifact_kind="BR2_directional_fit_records"
            )

    def test_no_cross_file_difference(self) -> None:
        differences = file_local_differences_v1(
            {
                "train1": np.asarray([[0.0], [1.0], [3.0]]),
                "train2": np.asarray([[1000.0], [1004.0], [1009.0]]),
            }
        )
        np.testing.assert_array_equal(differences["train1"][:, 0], [1.0, 2.0])
        np.testing.assert_array_equal(differences["train2"][:, 0], [4.0, 5.0])
        self.assertNotIn(997.0, differences["train1"])
        self.assertNotIn(997.0, differences["train2"])

    def test_no_cross_file_lag_pair(self) -> None:
        first_source = np.arange(0.0, 80.0).reshape(-1, 1)
        first_target = np.arange(10.0, 90.0).reshape(-1, 1)
        second_source = np.arange(1000.0, 1080.0).reshape(-1, 1)
        second_target = -np.arange(2000.0, 2080.0).reshape(-1, 1)
        first = vectorized_file_lagged_correlations_v1(
            source_values=first_source, target_values=first_target
        )
        second = vectorized_file_lagged_correlations_v1(
            source_values=second_source, target_values=second_target
        )
        self.assertTrue(math.isnan(float(first[1][0, 0])))
        self.assertTrue(math.isnan(float(second[1][0, 0])))

    def test_known_positive_lagged_correlation(self) -> None:
        dx = [1.0, 3.0, -2.0, 4.0, 2.0, -1.0, 5.0]
        source = np.concatenate(([0.0], np.cumsum(dx)))
        dy = [9.0, *dx[:-1]]
        target = np.concatenate(([0.0], np.cumsum(dy)))
        self.assertAlmostEqual(
            reference_file_lagged_correlation_v1(source, target, 1), 1.0
        )

    def test_known_negative_lagged_correlation(self) -> None:
        dx = [1.0, 3.0, -2.0, 4.0, 2.0, -1.0, 5.0]
        source = np.concatenate(([0.0], np.cumsum(dx)))
        dy = [9.0, *(-np.asarray(dx[:-1]))]
        target = np.concatenate(([0.0], np.cumsum(dy)))
        self.assertAlmostEqual(
            reference_file_lagged_correlation_v1(source, target, 1), -1.0
        )

    def test_sign_disagreement_is_direction_unstable(self) -> None:
        _, selection, sign = select_pair_horizon_v1(_unstable_correlations())
        self.assertEqual(selection.status, "direction_unstable")
        self.assertEqual(selection.score, 0.0)
        self.assertIsNone(sign)

    def test_exact_zero_is_not_sign_stable(self) -> None:
        exact_zero = pearson_correlation_reference_v1(
            [-1.0, 0.0, 1.0], [1.0, -2.0, 1.0]
        )
        self.assertEqual(exact_zero, 0.0)
        correlations = {horizon: (exact_zero, 0.2) for horizon in EXPECTED_HORIZONS}
        _, selection, _ = select_pair_horizon_v1(correlations)
        self.assertEqual(selection.status, "direction_unstable")

    def test_zero_variance_is_unusable(self) -> None:
        self.assertIsNone(
            pearson_correlation_reference_v1([1.0, 1.0, 1.0], [1.0, 2.0, 3.0])
        )

    def test_nonfinite_values_are_pairwise_filtered_and_not_imputed(self) -> None:
        self.assertAlmostEqual(
            pearson_correlation_reference_v1(
                [0.0, 1.0, math.nan, 2.0, math.inf],
                [0.0, 2.0, 7.0, 4.0, 9.0],
            ),
            1.0,
        )
        self.assertIsNone(
            pearson_correlation_reference_v1(
                [math.nan, 1.0, math.inf], [2.0, 3.0, 4.0]
            )
        )
        records, selection, _ = select_pair_horizon_v1(
            {horizon: (None, 0.2) for horizon in EXPECTED_HORIZONS}
        )
        self.assertTrue(all(not item.train1_usable for item in records))
        self.assertEqual(selection.status, "direction_unstable")

    def test_strongest_horizon_is_selected(self) -> None:
        correlations = {
            1: (0.2, 0.3),
            5: (-0.6, -0.5),
            10: (0.4, 0.45),
            30: (0.1, -0.8),
            60: (0.0, 0.9),
        }
        _, selection, sign = select_pair_horizon_v1(correlations)
        self.assertEqual(selection.selected_horizon, 5)
        self.assertEqual(selection.score, 0.5)
        self.assertEqual(sign, "negative")

    def test_shorter_horizon_wins_exact_strength_tie(self) -> None:
        correlations = {
            1: (0.2, 0.2),
            5: (0.2, 0.8),
            10: (0.1, -0.1),
            30: (0.1, -0.1),
            60: (0.1, -0.1),
        }
        _, selection, _ = select_pair_horizon_v1(correlations)
        self.assertEqual(selection.selected_horizon, 1)

    def test_stable_candidates_rank_before_unstable(self) -> None:
        ranked = rank_pair_evidence_v1(
            (
                _pair("A", "A", _unstable_correlations()),
                _pair("Z", "Z", _stable_correlations()),
            )
        )
        self.assertEqual([(item.source, item.supported) for item in ranked], [("Z", True), ("A", False)])

    def test_no_minimum_correlation_threshold(self) -> None:
        smallest_positive = math.nextafter(0.0, 1.0)
        _, selection, _ = select_pair_horizon_v1(
            {horizon: (smallest_positive, smallest_positive) for horizon in EXPECTED_HORIZONS}
        )
        self.assertEqual(selection.status, "cross_file_sign_stable")
        self.assertEqual(selection.score, smallest_positive)

    def test_unstable_pairs_do_not_pad_budget_views(self) -> None:
        ranked = (
            _pair("S1", "T1", _stable_correlations(0.3)),
            _pair("S2", "T2", _stable_correlations(0.2)),
            _pair("S3", "T3", _unstable_correlations()),
        )
        result = build_public_result_v1(
            ranked_pairs=ranked,
            private_ledger_hash=HASH,
            data_access_audit_hash=HASH,
            execution_code_commit=COMMIT,
            created_at=CREATED_AT,
        )
        self.assertEqual(len(result["top10"]), 2)
        self.assertEqual(len(result["top20"]), 2)
        self.assertEqual(len(result["top40"]), 2)
        self.assertTrue(result["candidate_shortfall"])
        self.assertFalse(any(item["source"] == "S3" for item in result["top40"]))

    def test_top10_top20_top40_are_prefixes_of_one_ranking(self) -> None:
        ranked = tuple(
            _pair(f"S{index:02d}", f"T{index:02d}", _stable_correlations(0.9 - index / 100.0))
            for index in range(45)
        )
        result = build_public_result_v1(
            ranked_pairs=ranked,
            private_ledger_hash=HASH,
            data_access_audit_hash=HASH,
            execution_code_commit=COMMIT,
            created_at=CREATED_AT,
        )
        ranking_pairs = [(item["source"], item["target"]) for item in result["supported_ranking"]]
        for key, size in (("top10", 10), ("top20", 20), ("top40", 40)):
            self.assertEqual(
                [(item["source"], item["target"]) for item in result[key]],
                ranking_pairs[:size],
            )

    def test_vectorized_backend_matches_independent_reference(self) -> None:
        verify_vectorized_parity_v1()

    def test_result_hash_is_deterministic_and_schema_valid(self) -> None:
        pairs = tuple(
            _pair(source, target, _stable_correlations(0.25))
            for source in self.bundle.universe_policy.source_variables
            for target in self.bundle.universe_policy.target_variables
        )
        ranked = rank_pair_evidence_v1(pairs)
        first = build_public_result_v1(
            ranked_pairs=ranked,
            private_ledger_hash=HASH,
            data_access_audit_hash=HASH,
            execution_code_commit=COMMIT,
            created_at=CREATED_AT,
        )
        second = build_public_result_v1(
            ranked_pairs=ranked,
            private_ledger_hash=HASH,
            data_access_audit_hash=HASH,
            execution_code_commit=COMMIT,
            created_at=CREATED_AT,
        )
        self.assertEqual(first, second)
        self.assertEqual(
            first["artifact_hash"],
            stable_hash_v1({key: value for key, value in first.items() if key != "artifact_hash"}),
        )
        schema = json.loads(
            (ROOT / "schemas/v6/statistical_candidate_result_v1_schema.json").read_text(
                encoding="utf-8"
            )
        )
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(first)

    def test_public_raw_value_and_absolute_path_leak_scan(self) -> None:
        assert_public_stat_payload_safe_v1(
            {"train3_accessed": False, "raw_time_series_samples_exposed": False}
        )
        for payload in (
            {"raw_samples": [1.0]},
            {"note": "C:\\private\\hai-train1.csv"},
            {"score": math.inf},
        ):
            with self.subTest(payload=payload):
                with self.assertRaisesRegex(
                    StatisticalCandidateDiscoveryError, "failed_stat_data_boundary"
                ):
                    assert_public_stat_payload_safe_v1(payload)


if __name__ == "__main__":
    unittest.main()
