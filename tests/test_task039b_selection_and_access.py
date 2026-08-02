from __future__ import annotations

import unittest

from paperworks.data.contracts_v2 import CreationMetadataV2
from paperworks.feasibility.hai_process_v1 import (
    APPROVED_TRAIN_FILES,
    HAIProcessFeasibilityRecordV1,
    TASK039BDataAccessError,
    TASK039BDataAccessLedger,
    create_process_split_manifests,
    create_process_views,
    select_process,
)


HASH = "a" * 64


def feasibility(process: str, *, passed: bool, sources: int = 2, targets: int = 2, pairs: int = 3) -> HAIProcessFeasibilityRecordV1:
    return HAIProcessFeasibilityRecordV1(
        process_id=process,
        process_name="Boiler" if process == "P1" else "Water Treatment",
        process_feature_count=10,
        metadata_reviewed_count=9,
        metadata_unresolved_count=1,
        eligible_source_variable_count=2,
        eligible_source_transition_count=4,
        eligible_continuous_target_count=3,
        screened_pair_count=12,
        fit_supported_pair_count=6,
        calibration_confirmed_pair_count=4,
        canonical_increase_ready_pair_count=pairs,
        future_decrease_pair_count=1,
        distinct_confirmed_source_count=sources,
        distinct_confirmed_target_count=targets,
        fit_to_calibration_transfer_rate=0.75,
        median_fit_isolated_trigger_count=30.0,
        median_calibration_isolated_trigger_count=10.0,
        median_isolation_ratio=0.8,
        missing_or_nonfinite_rate=0.0,
        official_graph_reference_available=process == "P1",
        manual_metadata_coverage=0.9,
        boundary_violation_count=0,
        candidate_fit_files=APPROVED_TRAIN_FILES[:2],
        calibration_file=APPROVED_TRAIN_FILES[2],
        normal_guard_values_accessed=False,
        feasibility_gate_passed=passed,
        private_screening_ledger_hash=HASH,
        claim_boundary="normal_only_feasibility_not_causal_or_performance_evidence",
    )


class Task039BSelectionAndAccessTests(unittest.TestCase):
    def test_prohibited_paths_and_normal_guard_values_fail_closed(self) -> None:
        ledger = TASK039BDataAccessLedger()
        for path in ("hai-23.05/hai-test1.csv", "hai-23.05/label-test1.csv", "private/x"):
            with self.assertRaises(TASK039BDataAccessError):
                ledger.authorize(path, purpose="test", feature_values_accessed=False)
        with self.assertRaises(TASK039BDataAccessError):
            ledger.authorize(
                APPROVED_TRAIN_FILES[3], purpose="screen", feature_values_accessed=True, process_scope=("P1",)
            )

    def test_access_ledger_freezes_without_guard_values(self) -> None:
        ledger = TASK039BDataAccessLedger()
        ledger.authorize(APPROVED_TRAIN_FILES[3], purpose="hash_header_row_count", feature_values_accessed=False)
        self.assertFalse(ledger.freeze().normal_guard_feature_values_accessed)

    def test_exactly_one_eligible_process_is_selected(self) -> None:
        result = select_process(
            p1=feasibility("P1", passed=True),
            p3=feasibility("P3", passed=False),
            selection_policy_id="TASK039B-PARETO-V1",
            selection_policy_hash=HASH,
        )
        self.assertEqual(result.selected_process_id, "P1")

    def test_no_feasible_process_blocks(self) -> None:
        result = select_process(
            p1=feasibility("P1", passed=False),
            p3=feasibility("P3", passed=False),
            selection_policy_id="TASK039B-PARETO-V1",
            selection_policy_hash=HASH,
        )
        self.assertEqual(result.selection_status, "blocked_no_feasible_delayed_response_process")

    def test_pareto_indeterminate_has_no_process_id_tie_break(self) -> None:
        result = select_process(
            p1=feasibility("P1", passed=True),
            p3=feasibility("P3", passed=True),
            selection_policy_id="TASK039B-PARETO-V1",
            selection_policy_hash=HASH,
        )
        self.assertEqual(result.selection_status, "blocked_process_selection_indeterminate")

    def test_official_graph_does_not_enter_selection(self) -> None:
        p1 = feasibility("P1", passed=True)
        p3 = feasibility("P3", passed=True)
        result = select_process(
            p1=p1,
            p3=p3,
            selection_policy_id="TASK039B-PARETO-V1",
            selection_policy_hash=HASH,
        )
        self.assertFalse(result.official_graph_used_for_scoring)

    def test_views_and_splits_preserve_second_level_boundary(self) -> None:
        creation = CreationMetadataV2(
            created_at="2026-08-02T00:00:00Z", created_by="synthetic test", code_commit="abcdef0", config_hash=HASH
        )
        canonical, candidate = create_process_views(
            dataset_manifest_id=HASH,
            process_id="P1",
            feature_names=("P1_A", "P1_B"),
            creation_metadata=creation,
        )
        self.assertTrue(canonical.second_level_rule_calibration_allowed)
        self.assertFalse(candidate.second_level_rule_calibration_allowed)
        splits = create_process_split_manifests(
            dataset_manifest_id=HASH,
            data_view_id=canonical.view_id,
            process_id="P1",
            row_counts={name: 1000 for name in APPROVED_TRAIN_FILES},
            creation_metadata=creation,
        )
        self.assertEqual([item.purge_gap_samples for item in splits], [120, 120, 120])
        self.assertIsNone(splits[2].event_ids)


if __name__ == "__main__":
    unittest.main()
