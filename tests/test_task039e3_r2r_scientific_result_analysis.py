from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

from paperworks.v6.common import stable_hash_v1


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "task039e3_result_analysis",
    ROOT / "scripts/analyze_task039e3_r2r_scientific_result_v1.py",
)
assert SPEC is not None and SPEC.loader is not None
analysis_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(analysis_module)


class ResultAnalysisPureFunctionTests(unittest.TestCase):
    def test_type7_quantiles_and_exact_paired_binomial(self) -> None:
        self.assertEqual(analysis_module.quantile_type7([0.0, 1.0, 2.0], 0.25), 0.5)
        self.assertEqual(analysis_module.quantile_type7([0.0, 1.0, 2.0], 0.90), 1.8)
        self.assertEqual(analysis_module.exact_paired_binomial_p(0, 0), 1.0)
        self.assertEqual(analysis_module.exact_paired_binomial_p(3, 0), 0.25)

    def test_describe_uses_complete_cohort_population_sd_and_strict_cutoffs(self) -> None:
        values = [0.0] * 38 + [0.10, 0.25, 0.50, 1.00]
        result = analysis_module.describe(values)
        self.assertEqual(result["count"], 42)
        self.assertIn("population_standard_deviation", result)
        self.assertEqual(
            result["threshold_exceedance_counts"],
            {"gt_0_10": 3, "gt_0_25": 2, "gt_0_50": 1, "gt_1_00": 0},
        )


@unittest.skipUnless(
    all(
        os.environ.get(name)
        for name in (
            "TASK039E3_SUCCESS_PUBLIC_ROOT",
            "TASK039E3_SUCCESS_PRIVATE_ROOT",
        )
    ),
    "task-local successful custody paths are intentionally external",
)
class ExactEvaluableResultAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.analysis, cls.private_matrix = analysis_module.analyze_result(
            public_root=Path(os.environ["TASK039E3_SUCCESS_PUBLIC_ROOT"]),
            private_root=Path(os.environ["TASK039E3_SUCCESS_PRIVATE_ROOT"]),
            candidate_cohort_path=ROOT / "docs/task_reports/TASK-039C_CANDIDATE_PROFILING_COHORT.json",
            custody_audit_receipt_path=ROOT / "docs/task_reports/TASK-039E3_R2R_TERMINAL_CUSTODY_AUDIT_RECEIPT.json",
        )

    def test_authority_denominators_and_paired_relation_coverage(self) -> None:
        self.assertTrue(self.analysis["input_authority"]["scientific_result_evaluable"])
        self.assertEqual(len(self.private_matrix), 42)
        self.assertEqual(len({row["relation_identity"] for row in self.private_matrix}), 42)
        self.assertEqual(
            {arm: self.analysis["construction"]["arms"][arm]["accepted"] for arm in analysis_module.ARMS},
            {"T0": 42, "T1": 42, "T1-B": 42, "T2": 39},
        )
        self.assertTrue(self.analysis["construction"]["relation_level_validity_ceiling_observed"])
        self.assertEqual(
            self.analysis["construction"]["paired_comparisons"]["T1_vs_T2"],
            {
                "both_accepted": 39,
                "left_only_accepted": 3,
                "right_only_accepted": 0,
                "neither_accepted": 0,
                "accepted_rate_difference_percentage_points_left_minus_right": 100 / 14,
                "exact_two_sided_mcnemar_binomial_p": 0.25,
                "inferential_role": "supplementary",
            },
        )

    def test_call_accounting_and_initial_request_fairness(self) -> None:
        self.assertEqual(
            self.analysis["accounting"],
            {
                "historical_scientific_logical_calls": 6,
                "fresh_scientific_logical_calls": 252,
                "lifetime_scientific_logical_calls": 258,
                "historical_partial_records_reused": 0,
            },
        )
        self.assertEqual(
            self.analysis["construction"]["initial_request_fairness"],
            {
                "relations_compared": 42,
                "relations_with_identical_t1_t1b_t2_initial_request_hashes": 42,
                "request_hash_mismatches": 0,
                "arm_identity_model_visible": False,
            },
        )
        self.assertEqual(
            {arm: self.analysis["efficiency"]["arms"][arm]["provider_logical_calls"] for arm in ("T1", "T1-B", "T2")},
            {"T1": 42, "T1-B": 126, "T2": 42},
        )

    def test_t1b_selection_schema_failure_and_marginal_yield(self) -> None:
        t1b = self.analysis["t1b"]
        self.assertEqual((t1b["materialized_proposals"], t1b["admissible_materialized_proposals"], t1b["rejected_materialized_proposals"], t1b["schema_parse_failures"]), (125, 122, 3, 1))
        self.assertEqual(t1b["admissible_proposals_per_relation_distribution"], {"0": 0, "1": 1, "2": 2, "3": 39})
        self.assertEqual(t1b["selected_call_distribution"], {"1": 41, "2": 0, "3": 1})
        self.assertEqual(t1b["cumulative_relation_yield"], {"after_call_1": 41, "after_calls_1_2": 41, "after_calls_1_2_3": 42})
        self.assertEqual(t1b["incremental_recovery"], {"call_2": 0, "call_3": 1})

    def test_t2_controller_and_no_rule_categories(self) -> None:
        t2 = self.analysis["t2"]
        self.assertEqual((t2["accepted_relations"], t2["no_rule_relations"]), (39, 3))
        self.assertTrue(t2["all_terminated_after_call_1"])
        self.assertFalse(t2["feedback_path_empirically_exercised"])
        self.assertEqual((t2["feedback_eligible_rejections"], t2["revise_actions"], t2["retrieve_actions"], t2["follow_up_generations"], t2["successful_recoveries"]), (0, 0, 0, 0, 0))
        self.assertEqual(t2["sanitized_issue_categories"], [{"code": "VALIDITY_UNSUPPORTED_VARIABLE", "field_category": "variables", "repairability": "non_repairable", "controller_action": "no_rule", "count": 3}])

    def test_direct_number_aggregation_and_robustness(self) -> None:
        direct = self.analysis["direct_number"]
        self.assertEqual((direct["missing_number_count"], direct["nonfinite_or_parse_failure_count"], direct["sign_domain_violation_count"]), (0, 0, 0))
        self.assertAlmostEqual(direct["roles"]["source_step_threshold"]["mean"], 0.6620709165201911)
        self.assertAlmostEqual(direct["roles"]["source_stability_tolerance"]["median"], 0.49035418075741677)
        self.assertAlmostEqual(direct["roles"]["target_noise_scale"]["p90_type7"], 86.59620252943506)
        self.assertEqual(direct["roles"]["target_noise_scale"]["threshold_exceedance_counts"], {"gt_0_10": 42, "gt_0_25": 42, "gt_0_50": 40, "gt_1_00": 14})

    def test_nonexclusive_origin_memberships_cover_all_relations(self) -> None:
        origin = self.analysis["origin"]
        self.assertTrue(origin["memberships_nonexclusive"])
        self.assertTrue(origin["all_relations_mapped"])
        self.assertEqual(origin["membership_pattern_counts"], {"GDN": 3, "META": 7, "META+STAT": 21, "STAT": 9, "STAT+GDN": 2})
        self.assertEqual({key: value["eligible_relations"] for key, value in origin["origins"].items()}, {"META": 28, "STAT": 32, "GDN": 5})
        self.assertEqual({key: value["t2_no_rule"] for key, value in origin["origins"].items()}, {"META": 0, "STAT": 2, "GDN": 2})

    def test_sanitized_analysis_excludes_relation_identities_and_private_paths(self) -> None:
        text = json.dumps(self.analysis, sort_keys=True)
        self.assertNotIn("directional_relation:", text)
        self.assertNotIn("AppData", text)
        self.assertNotIn("recovery_private", text)
        self.assertEqual(
            stable_hash_v1({key: value for key, value in self.analysis.items() if key != "analysis_hash"}),
            self.analysis["analysis_hash"],
        )


if __name__ == "__main__":
    unittest.main()
