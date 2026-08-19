from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import unittest

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_r2r_utility_protocol_v3 import (
    PROTOCOL_ID,
    UTILITY_OPPORTUNITY_SAMPLING_POLICY,
    authority_snapshot_v3,
    validate_reopen_authority_v3,
)


ROOT = Path(__file__).resolve().parents[1]


def load(name: str) -> dict[str, object]:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def self_hash(document: dict[str, object], key: str = "artifact_hash") -> str:
    observed = document[key]
    assert isinstance(observed, str)
    return observed if stable_hash_v1({name: value for name, value in document.items() if name != key}) == observed else ""


class V3ScientificRegressionTests(unittest.TestCase):
    def test_reopen_authority_is_exact_and_scope_limited(self) -> None:
        authority = load("docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_V3_REOPEN_AUTHORIZATION.json")
        self.assertEqual(
            validate_reopen_authority_v3(authority),
            "dffef0fcc2bdd5d6c0473cac027c81b050c2f9f0bbe74c6b577875de827c2f5a",
        )
        self.assertEqual(len(authority["exact_open_blockers"]), 2)
        self.assertTrue(all(value is False for value in authority["prohibited_authorities"].values()))

    def test_v1_and_v2_sources_are_byte_immutable(self) -> None:
        records = (
            (
                "0eec09c662ecc1c78daa5f661c2471aba69cf905",
                "src/paperworks/v6/task039e3_r2r_utility_protocol_v1.py",
                "56305eced40020b00e29783fa9d795f3a352b230e584ffed0ae5465f1f1a5165",
            ),
            (
                "6c63a9a8410d083c8b0e71c344d799284f02941b",
                "src/paperworks/v6/task039e3_r2r_utility_protocol_v2.py",
                "0e9f9be8d5f8ed09ea7d0b385ffe37b7fbaa53834ac3bfffd17e740d8d4fdf01",
            ),
        )
        for commit, relative, expected_sha in records:
            current = (ROOT / relative).read_bytes()
            historical = subprocess.run(
                ["git", "show", f"{commit}:{relative}"],
                cwd=ROOT,
                check=True,
                capture_output=True,
            ).stdout
            with self.subTest(relative=relative):
                self.assertEqual(current, historical)
                self.assertEqual(hashlib.sha256(current).hexdigest(), expected_sha)

    def test_construction_and_executable_equivalence_unchanged(self) -> None:
        construction = load("docs/task_reports/TASK-039E3_R2R_RESULT_ANALYSIS_CONSTRUCTION.json")
        self.assertEqual(self_hash(construction), "2175fca3c3bcc5ccffe7dfca1fcd8c3a0687ac94a56d077f5db53a6632bf2159")
        outcomes = construction["arm_results"]
        self.assertEqual((outcomes["T0"]["accepted"], outcomes["T0"]["no_rule"]), (42, 0))
        self.assertEqual((outcomes["T1"]["accepted"], outcomes["T1"]["no_rule"]), (42, 0))
        self.assertEqual((outcomes["T1-B"]["accepted"], outcomes["T1-B"]["no_rule"]), (42, 0))
        self.assertEqual((outcomes["T2"]["accepted"], outcomes["T2"]["no_rule"]), (39, 3))
        equivalence = load("docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_EXECUTABLE_EQUIVALENCE.json")
        self.assertEqual(self_hash(equivalence), "3efdce159bc5ac39825d4e4654428237e47205307f83aae7a133db6c5789f60f")
        self.assertEqual(equivalence["T0_T1_T1B_equivalent_relation_count"], 42)
        self.assertEqual(equivalence["T2_accepted_equivalent_count"], 39)
        self.assertEqual(equivalence["T2_no_rule_count"], 3)
        self.assertTrue(equivalence["T2_no_rule_cells_preserved"])

    def test_numeric_reference_authority_remains_420_of_420(self) -> None:
        numeric = load("docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_REAUDIT_NUMERIC_AUTHORITY.json")
        self.assertEqual(self_hash(numeric), "e50300efd372fb8a5c4567a6fa9e3277e36804506b306ea0053f7fc4ab48ceed")
        self.assertEqual(numeric["records_checked"], 420)
        self.assertEqual(numeric["exact_e1_numeric_matches"], 420)
        self.assertEqual(numeric["missing"], 0)
        self.assertEqual(numeric["ambiguous"], 0)
        self.assertEqual(numeric["nonfinite"], 0)

    def test_continuous_semantics_and_metrics_remain_frozen(self) -> None:
        source = ROOT / "src/paperworks/v6/continuous_step_protocol_v1.py"
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), "cc88b692d9dee50b3b8cc5497f596595a74082ee5c7a838b5fe51e7c381c4596")
        text = source.read_text(encoding="utf-8")
        for token in ("pre_window_seconds=5", "post_hold_window_seconds=5", "target_response_window_seconds=3"):
            self.assertIn(token, text)
        metrics = load("docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_METRIC_POLICY.json")
        self.assertEqual(self_hash(metrics), "4c7b6cfdb6b3889e56e7151be60b92a7e6f46ce0135de0ed65ebf3207a7b0d6a")
        self.assertEqual(set(metrics["co_primary_endpoints"]), {"attack_event_recall", "normal_false_alarm_rate_per_hour"})
        self.assertEqual(metrics["point_adjustment"], "PROHIBITED")
        self.assertIsNone(metrics["weighted_composite"])

    def test_cost_origin_and_direct_number_boundaries_unchanged(self) -> None:
        cost = load("docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_REMEDIATION_COST_POLICY.json")
        self.assertEqual(self_hash(cost), "d0111f06020e2cd134a948e3d1463b6e71cdeaaee232f9fee48b151b8f05f89b")
        self.assertEqual(cost["construction_provider_calls"], {"T0": 0, "T1": 42, "T1-B": 126, "T2": 42})
        origin = load("docs/task_reports/TASK-039E3_R2R_RESULT_ANALYSIS_ORIGIN.json")
        self.assertEqual(self_hash(origin), "562de7029e1e6768b34ffa9455e280eed7512c5312669ac5e34d7b8b419513c5")
        self.assertEqual(origin["claim_classification"], "INCONCLUSIVE")
        interpreter = load("docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_INTERPRETER_POLICY.json")
        self.assertEqual(interpreter["parameter_policy"]["direct_number_substitution"], False)

    def test_v3_authority_remains_pending_audit_and_execution_false(self) -> None:
        snapshot = authority_snapshot_v3()
        self.assertEqual(PROTOCOL_ID, "BASE_V1_PLUS_REMEDIATION_V2_PLUS_FINAL_CLOSURE_V3")
        self.assertEqual(UTILITY_OPPORTUNITY_SAMPLING_POLICY, "FULL_CENSUS_NO_FIXED_SAMPLE_SIZE")
        self.assertTrue(snapshot["utility_protocol_v3_frozen"])
        for key in (
            "utility_protocol_audited", "utility_evaluator_implementation_ready",
            "utility_execution_authorization_ready", "real_hai_test_access",
            "real_label_access", "inner_execution", "outer_execution",
            "detector_integration", "rule_v2", "production_runtime", "winner",
        ):
            self.assertFalse(snapshot[key])

    def test_new_json_schemas_parse(self) -> None:
        for relative in (
            "schemas/v6/task039e3_r2r_opportunity_custody_v3_schema.json",
            "schemas/v6/task039e3_r2r_feature_schema_v3_schema.json",
        ):
            document = load(relative)
            self.assertEqual(document["$schema"], "https://json-schema.org/draft/2020-12/schema")


if __name__ == "__main__":
    unittest.main()
