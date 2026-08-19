from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import subprocess
import unittest

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_r2r_utility_protocol_v2 import (
    CROSS_SOURCE_ISOLATION_RADIUS_SECONDS,
    SOURCE_POST_WINDOW,
    SOURCE_PRE_WINDOW,
    SOURCE_REFRACTORY_SECONDS,
    SUPPORTED_HORIZONS,
    TARGET_RESPONSE_WINDOW,
    UTILITY_SOURCE_UNIVERSE_V2,
)


ROOT = Path(__file__).resolve().parents[1]
BASE = "ee7656531f662e6204a666af1499174184b2c746"
COMMIT_A = "a3d9e8d324e8492144eea4a2baa3bde746545acc"


def load(relative: str) -> dict[str, object]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def artifact_hash(relative: str) -> str:
    document = load(relative)
    observed = document["artifact_hash"]
    payload = {key: value for key, value in document.items() if key != "artifact_hash"}
    if stable_hash_v1(payload) != observed:
        raise AssertionError(f"self-hash mismatch: {relative}")
    return observed


class IndependentFeatureAndRegressionAudit(unittest.TestCase):
    def test_feature_set_is_independently_derived_from_lower_authorities(self) -> None:
        c0 = load("configs/v6/task039c0_candidate_discovery_protocol.json")
        br2 = load("configs/v6/task039br2_hai_continuous_step_feasibility.json")
        equivalence = load(
            "docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_EXECUTABLE_EQUIVALENCE.json"
        )
        feature_artifact = load(
            "docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_V3_FEATURE_SCHEMA.json"
        )
        sources = tuple(
            item["variable_name"]
            for item in c0["common_universe"]["source_identities"]
        )
        targets = {
            item["executable_signature"]["target"]
            for item in equivalence["relation_records"]
        }
        br2_sources = {
            item["variable_name"]
            for item in br2["frozen_eligibility"]["P1"]["sources"]
        }
        br2_targets = {
            item["variable_name"]
            for item in br2["frozen_eligibility"]["P1"]["targets"]
        }
        self.assertEqual(tuple(sources), tuple(UTILITY_SOURCE_UNIVERSE_V2))
        self.assertEqual(len(set(sources)), 12)
        self.assertEqual(len(targets), 10)
        self.assertEqual(len(set(sources) | targets), 22)
        self.assertEqual(set(sources), br2_sources)
        self.assertTrue(targets <= br2_targets)
        artifact_features = {item["feature_name"] for item in feature_artifact["features"]}
        self.assertEqual(artifact_features, set(sources) | targets)
        self.assertEqual(feature_artifact["missing_or_ambiguous_feature_types"], 0)
        self.assertEqual(feature_artifact["source_count"], 12)
        self.assertEqual(feature_artifact["target_count"], 10)

    def test_physical_storage_dtype_is_not_invented(self) -> None:
        feature = load(
            "docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_V3_FEATURE_SCHEMA.json"
        )
        self.assertEqual(feature["raw_storage_dtype_claim"], "NOT_CLAIMED")
        self.assertEqual(feature["expected_raw_representation"], "strict_decimal_numeric_token")
        self.assertEqual(feature["expected_logical_type"], "finite_real_scalar")
        self.assertEqual(feature["unit_policy"], "UNBOUND_NULL_NO_INFERENCE")
        self.assertTrue(all(item["unit_identity"] is None for item in feature["features"]))

    def test_construction_equivalence_and_numeric_counts_are_unchanged(self) -> None:
        construction = load(
            "docs/task_reports/TASK-039E3_R2R_RESULT_ANALYSIS_CONSTRUCTION.json"
        )
        equivalence = load(
            "docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_EXECUTABLE_EQUIVALENCE.json"
        )
        numeric = load(
            "docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_REAUDIT_NUMERIC_AUTHORITY.json"
        )
        self.assertEqual(
            {arm: (values["accepted"], values["no_rule"]) for arm, values in construction["arm_results"].items()},
            {"T0": (42, 0), "T1": (42, 0), "T1-B": (42, 0), "T2": (39, 3)},
        )
        self.assertEqual(equivalence["T0_T1_T1B_equivalent_relation_count"], 42)
        self.assertEqual(equivalence["T2_accepted_equivalent_count"], 39)
        self.assertEqual(equivalence["T2_no_rule_count"], 3)
        self.assertEqual(
            (numeric["records_checked"], numeric["exact_e1_numeric_matches"]),
            (420, 420),
        )
        self.assertEqual(
            (numeric["missing"], numeric["ambiguous"], numeric["nonfinite"]),
            (0, 0, 0),
        )

    def test_continuous_step_and_claim_boundaries_are_unchanged(self) -> None:
        event = load("docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_EVENT_POLICY.json")
        metric = load("docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_METRIC_POLICY.json")
        origin = load("docs/task_reports/TASK-039E3_R2R_RESULT_ANALYSIS_ORIGIN.json")
        self.assertEqual((SOURCE_PRE_WINDOW, SOURCE_POST_WINDOW), (5, 5))
        self.assertEqual(SOURCE_REFRACTORY_SECONDS, 10)
        self.assertEqual(CROSS_SOURCE_ISOLATION_RADIUS_SECONDS, 2)
        self.assertEqual(set(SUPPORTED_HORIZONS), {1, 5, 10, 30, 60})
        self.assertEqual(TARGET_RESPONSE_WINDOW, 3)
        self.assertEqual(event["point_adjustment"], "PROHIBITED")
        self.assertEqual(metric["point_adjustment"], "PROHIBITED")
        self.assertEqual(metric["direct_number_utility"], "NOT_APPLICABLE")
        self.assertEqual(
            load("docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_V3_REGRESSION.json")[
                "direct_number"
            ],
            "EXCLUDED_FROM_UTILITY_THRESHOLDS",
        )
        self.assertEqual(origin["claim_classification"], "INCONCLUSIVE")

    def test_v3_regression_component_hashes_match_committed_authorities(self) -> None:
        regression = load(
            "docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_V3_REGRESSION.json"
        )
        expected_numeric = artifact_hash(
            "docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_REAUDIT_NUMERIC_AUTHORITY.json"
        )
        expected_event = artifact_hash(
            "docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_EVENT_POLICY.json"
        )
        expected_metric = artifact_hash(
            "docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_METRIC_POLICY.json"
        )
        self.assertEqual(regression["numeric_reference_authority"]["authority_hash"], expected_numeric)
        self.assertEqual(regression["metrics"]["event_policy_hash"], expected_event)
        self.assertEqual(regression["metrics"]["metric_policy_hash"], expected_metric)

    def test_source_freeze_records_and_protocol_immutability(self) -> None:
        source_freeze = load(
            "docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_V3_SOURCE_FREEZE.json"
        )
        self.assertEqual(source_freeze["commit_a"], COMMIT_A)
        records = (
            *source_freeze["active_v3_records"],
            *source_freeze["immutable_historical_sources"],
            *source_freeze["active_dependency_records"],
        )
        self.assertEqual(len(records), 16)
        for record in records:
            path = record["path"]
            observed_blob = subprocess.check_output(
                ["git", "rev-parse", f"{COMMIT_A}:{path}"], cwd=ROOT, text=True
            ).strip()
            observed_sha = sha256((ROOT / path).read_bytes()).hexdigest()
            with self.subTest(path=path):
                self.assertEqual(observed_blob, record["git_blob"])
                self.assertEqual(observed_sha, record["raw_byte_sha256"])
        self.assertFalse(source_freeze["construction_scientific_source_modified"])
        self.assertFalse(source_freeze["construction_result_artifacts_modified"])
        immutable = {record["path"]: record for record in source_freeze["immutable_historical_sources"]}
        self.assertFalse(immutable["src/paperworks/v6/task039e3_r2r_utility_protocol_v1.py"]["modified"])
        self.assertFalse(immutable["src/paperworks/v6/task039e3_r2r_utility_protocol_v2.py"]["modified"])
        v3_blob = subprocess.check_output(
            ["git", "rev-parse", f"{COMMIT_A}:src/paperworks/v6/task039e3_r2r_utility_protocol_v3.py"],
            cwd=ROOT,
            text=True,
        ).strip()
        self.assertEqual(v3_blob, "d233cb05ce2a10930ee20952f3ce6784f3ece8bf")
        changed = subprocess.check_output(
            ["git", "diff", "--name-only", f"{COMMIT_A}..{BASE}"], cwd=ROOT, text=True
        ).splitlines()
        self.assertTrue(changed)
        self.assertTrue(all(path.startswith("docs/task_reports/") for path in changed))


if __name__ == "__main__":
    unittest.main()
