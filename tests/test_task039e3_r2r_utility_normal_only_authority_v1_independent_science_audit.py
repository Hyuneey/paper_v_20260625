from __future__ import annotations

from hashlib import sha256
import json
import math
from pathlib import Path
import random
import statistics
import subprocess
import unittest

import paperworks.v6.task039e3_r2r_utility_normal_only_authority_v1 as subject


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs" / "task_reports"

EXPECTED_HISTORICAL_ROLES = (
    "source_step_threshold",
    "source_stability_tolerance",
    "target_noise_scale",
    "selected_delay_horizon_seconds",
    "source_pre_window_seconds",
    "source_post_window_seconds",
    "minimum_source_stability_fraction",
    "source_refractory_seconds",
    "cross_source_isolation_radius_seconds",
    "target_baseline_window_seconds",
    "target_response_window_seconds",
)
EXPECTED_UTILITY_ROLES = tuple(
    role for role in EXPECTED_HISTORICAL_ROLES if role != "selected_delay_horizon_seconds"
)
EXPECTED_WINDOWS: dict[str, int | float] = {
    "source_pre_window_seconds": 5,
    "source_post_window_seconds": 5,
    "minimum_source_stability_fraction": 0.8,
    "source_refractory_seconds": 10,
    "cross_source_isolation_radius_seconds": 2,
    "target_baseline_window_seconds": 5,
    "target_response_window_seconds": 3,
}


def load(name: str) -> dict[str, object]:
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


def independent_median(values: tuple[float, ...] | list[float]) -> float:
    return float(statistics.median(values))


def independent_q75(values: list[float]) -> float:
    ordered = sorted(values)
    position = 0.75 * (len(ordered) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(ordered[lower])
    fraction = position - lower
    return float(ordered[lower] + fraction * (ordered[upper] - ordered[lower]))


def independent_scale(files: tuple[tuple[float, ...], tuple[float, ...]]) -> float:
    differences = [
        values[index] - values[index - 1]
        for values in files
        for index in range(1, len(values))
    ]
    center = independent_median(differences)
    mad = independent_median([abs(value - center) for value in differences])
    return max(1.4826 * mad, 1e-12)


def independent_source(
    train1: tuple[float, ...], train2: tuple[float, ...]
) -> tuple[str, float, float | None, float | None, int]:
    files = (train1, train2)
    noise = independent_scale(files)
    amplitudes: list[float] = []
    for values in files:
        for event_index in range(5, len(values) - 5 + 1):
            pre = independent_median(list(values[event_index - 5 : event_index]))
            post = independent_median(list(values[event_index : event_index + 5]))
            amplitude = abs(post - pre)
            if amplitude > noise:
                amplitudes.append(amplitude)
    if len(amplitudes) < 20:
        return "insufficient_nontrivial_amplitudes", noise, None, None, len(amplitudes)
    threshold = max(5.0 * noise, independent_q75(amplitudes))
    tolerance = max(3.0 * noise, 0.10 * threshold)
    return "supported", noise, threshold, tolerance, len(amplitudes)


class IndependentScienceAudit(unittest.TestCase):
    def test_frozen_calibration_source_bytes_and_blobs(self) -> None:
        expectations = {
            "src/paperworks/v6/relation_profiling_protocol_v1.py": (
                "7d7da2c07cbd5207edc223b4a854885f30b584b3",
                "ba7a7ea29eb0d68077a51442691d201915470d16dca751dff3c214a7ead3c529",
            ),
            "src/paperworks/v6/task039e1_evidence_materialization_v1.py": (
                "af4401cbcf2240df8523a36c0ff69a197fdfae4b",
                "2a6e627fcc95b532fead6619c3aa7d0a6f5781537206cddb2638c736c0856a24",
            ),
        }
        for relative, (expected_blob, expected_raw) in expectations.items():
            observed_blob = subprocess.run(
                ["git", "-C", str(ROOT), "rev-parse", f"HEAD:{relative}"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            observed_raw = sha256((ROOT / relative).read_bytes()).hexdigest()
            with self.subTest(relative=relative):
                self.assertEqual(observed_blob, expected_blob)
                self.assertEqual(observed_raw, expected_raw)

    def test_historical_462_to_utility_420_reduction_is_only_horizon(self) -> None:
        manifest = load("TASK-039E1_CONSTRUCTION_EVIDENCE_MANIFEST.json")
        entries = manifest["entries"]
        self.assertIsInstance(entries, list)
        self.assertEqual(len(entries), 42)
        observed_role_sets = {
            tuple(row["numeric_role"] for row in entry["numeric_references"])
            for entry in entries
        }
        self.assertEqual(observed_role_sets, {EXPECTED_HISTORICAL_ROLES})
        self.assertEqual(42 * len(EXPECTED_HISTORICAL_ROLES), 462)
        self.assertEqual(subject.UTILITY_NUMERIC_ROLES, EXPECTED_UTILITY_ROLES)
        self.assertEqual(42 * len(EXPECTED_UTILITY_ROLES), 420)
        self.assertEqual(
            set(EXPECTED_HISTORICAL_ROLES) - set(subject.UTILITY_NUMERIC_ROLES),
            {"selected_delay_horizon_seconds"},
        )

        equivalence = load("TASK-039E3_R2R_UTILITY_PROTOCOL_EXECUTABLE_EQUIVALENCE.json")
        horizons = []
        for record in equivalence["relation_records"]:
            signature = record["executable_signature"]
            horizon = signature["selected_delay_horizon_seconds"]
            self.assertIs(type(horizon), int)
            self.assertIn(horizon, {1, 5, 10, 30, 60})
            self.assertEqual(record["semantic_execution_hash"], subject.stable_hash_v1(signature))
            horizons.append(horizon)
        self.assertEqual(len(horizons), 42)
        self.assertNotIn("selected_delay_horizon_seconds", subject.UTILITY_NUMERIC_ROLES)

    def test_source_threshold_and_tolerance_match_independent_formula(self) -> None:
        generator = random.Random(12345)
        noisy_files: list[tuple[float, ...]] = []
        for _ in range(2):
            current = 0.0
            values: list[float] = []
            for _index in range(200):
                current += generator.gauss(0.0, 0.2)
                values.append(current)
            noisy_files.append(tuple(values))
        fixtures = (
            (
                tuple(float(index) for index in range(80)),
                tuple(float(index) for index in range(80)),
            ),
            (
                tuple(float(index) for index in range(80)),
                tuple(10_000.0 + float(index) for index in range(80)),
            ),
            (
                tuple(float(index // 7) for index in range(140)),
                tuple(float((index // 9) * 2) for index in range(140)),
            ),
            tuple(noisy_files),
            (
                tuple(float(index * index) for index in range(19)),
                tuple(10_000.0 + float(index * index) for index in range(19)),
            ),
        )
        for train1, train2 in fixtures:
            status, _, threshold, tolerance, retained = independent_source(train1, train2)
            self.assertEqual(status, "supported")
            self.assertGreaterEqual(retained, 20)
            observed = subject.derive_source_parameters_normal_only_v1(train1, train2)
            with self.subTest(lengths=(len(train1), len(train2))):
                self.assertEqual(observed, (threshold, tolerance))

        status, noise, threshold, tolerance, _ = independent_source(*tuple(noisy_files))
        self.assertEqual(status, "supported")
        self.assertEqual(threshold, 5.0 * noise)
        self.assertEqual(tolerance, 3.0 * noise)
        self.assertEqual(
            subject.derive_source_parameters_normal_only_v1(*tuple(noisy_files)),
            (threshold, tolerance),
        )

    def test_source_formula_fails_closed_for_unsupported_and_malformed_series(self) -> None:
        unsupported = (
            (tuple(float(index) for index in range(10)),) * 2,
            ((0.0,) * 80,) * 2,
        )
        for files in unsupported:
            status, _, threshold, tolerance, retained = independent_source(*files)
            self.assertEqual(status, "insufficient_nontrivial_amplitudes")
            self.assertLess(retained, 20)
            self.assertIsNone(threshold)
            self.assertIsNone(tolerance)
            with self.subTest(lengths=tuple(map(len, files))), self.assertRaises(subject.NormalOnlyAuthorityV1Error):
                subject.derive_source_parameters_normal_only_v1(*files)
        ramp = tuple(float(index) for index in range(80))
        malformed = ramp[:-1] + (math.nan,)
        with self.assertRaises(subject.NormalOnlyAuthorityV1Error):
            subject.derive_source_parameters_normal_only_v1(malformed, ramp)

    def test_target_scale_matches_independent_file_local_formula(self) -> None:
        fixtures = (
            (
                tuple(float(index) for index in range(80)),
                tuple(50_000.0 + float(index) for index in range(80)),
            ),
            (
                tuple(float(index * index) for index in range(50)),
                tuple(float(index * index + 100_000) for index in range(50)),
            ),
        )
        for files in fixtures:
            expected = independent_scale(files)
            observed = subject.derive_target_scale_normal_only_v1(*files)
            with self.subTest(lengths=tuple(map(len, files))):
                self.assertEqual(observed, expected)
                self.assertGreater(observed, 0.0)
        constant = (0.0,) * 30
        self.assertEqual(subject.derive_target_scale_normal_only_v1(constant, constant), 1e-12)
        with self.assertRaises(subject.NormalOnlyAuthorityV1Error):
            subject.derive_target_scale_normal_only_v1(constant[:-1] + (math.inf,), constant)

    def test_window_constants_are_exact_and_not_overrideable(self) -> None:
        bundle = subject.PreregisteredWindowConstantBundleV1()
        observed = {key: bundle.to_dict()[key] for key in EXPECTED_WINDOWS}
        self.assertEqual(observed, EXPECTED_WINDOWS)
        for key, expected in EXPECTED_WINDOWS.items():
            wrong = dict(EXPECTED_WINDOWS)
            wrong[key] = expected + 1
            with self.subTest(key=key), self.assertRaises(Exception):
                subject.PreregisteredWindowConstantBundleV1(**wrong)

    def test_train1_train2_identities_are_independently_bound_and_exclusive(self) -> None:
        expected = {
            "hai-23.05/hai-train1.csv": (
                "53007b0ba604fbf338e7ac2e08cd81d874b5d1388f3aecb213ddcba5bf2bec4a",
                162_418_984,
                280_800,
            ),
            "hai-23.05/hai-train2.csv": (
                "0e520e82bf78a661ab19ce4967f3c766bd809820f457a9c90c365102d4534c56",
                169_121_615,
                291_600,
            ),
        }
        dataset = load("TASK-039A_DATASET_MANIFEST_V2.json")
        d1 = load("TASK-039D1_DATA_ACCESS_AUDIT.json")
        dataset_by_path = {row["relative_local_path"]: row for row in dataset["files"]}
        d1_by_path = {row["relative_path"]: row for row in d1["file_records"]}
        for path, (digest, size, rows) in expected.items():
            self.assertEqual(dataset_by_path[path]["sha256"], digest)
            self.assertEqual(dataset_by_path[path]["byte_size"], size)
            self.assertEqual(dataset_by_path[path]["row_count"], rows)
            self.assertEqual(d1_by_path[path]["sha256"], digest)
            self.assertEqual(d1_by_path[path]["byte_size"], size)
            self.assertEqual(d1_by_path[path]["row_count"], rows)
            self.assertEqual(
                d1_by_path[path]["header_sha256"],
                "95968d825d1c9caab778a857cec618b64674ec5a85d94e6952d99c2cab08d16a",
            )
        self.assertEqual(set(d1_by_path), set(expected))
        self.assertFalse(d1["train3_accessed"])
        self.assertFalse(d1["test_accessed"])
        self.assertFalse(d1["labels_accessed"])


if __name__ == "__main__":
    unittest.main()
