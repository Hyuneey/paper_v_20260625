from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from paperworks.feasibility.hai_continuous_step_v1 import (
    AUTHORIZED_VALUE_FILES,
    BR1_PROTOCOL_BUNDLE_HASH,
    DATASET_MANIFEST_ID,
    ContinuousCalibrationConfirmationRecordV1,
    ContinuousDirectionalFitRecordV1,
    ContinuousSourceScreeningRecordV1,
    HAIContinuousProcessFeasibilityV1,
    HAIContinuousProcessFreezeV1,
    HAIContinuousStepError,
    TASK039BR2DataAccessLedger,
    TASK039BR2ExecutionInterpretationV1,
    VerifiedNormalFileV1,
    assert_public_payload_safe_v1,
    build_process_selection_v1,
    deduplicate_directional_relations_v1,
    execute_process_v1,
)
from paperworks.v6.common import CreationMetadataV1


HASH = "a" * 64
META = CreationMetadataV1("2026-08-04T00:00:00+09:00", "test", "a" * 40, HASH)


def feasibility(process: str, *, feasible: bool, sources: int = 2, targets: int = 3) -> HAIContinuousProcessFeasibilityV1:
    confirmed = 3 if feasible else 0
    return HAIContinuousProcessFeasibilityV1(
        process_id=process,
        process_name="Boiler" if process == "P1" else "Water Treatment",
        documented_sources_with_valid_fit_thresholds=sources if feasible else 0,
        eligible_continuous_targets=targets,
        calibration_confirmed_directional_pairs=confirmed,
        distinct_confirmed_sources=2 if feasible else 0,
        distinct_confirmed_targets=2 if feasible else 0,
        fit_supported_directional_pairs=confirmed,
        fit_to_calibration_transfer_rate=1.0 if feasible else 0.0,
        normal_candidate_fit_files=("hai-train1.csv", "hai-train2.csv"),
        normal_relation_calibration_file="hai-train3.csv",
        normal_guard_feature_values_accessed=False,
        prohibited_data_access_count=0,
        median_calibration_isolated_event_support=6.0 if feasible else 0.0,
        manual_metadata_coverage=1.0,
        metadata_unresolved_ratio=0.0,
        non_isolated_source_event_ratio=0.1,
        missing_or_nonfinite_rate=0.0,
        source_status_counts={"supported": sources},
        fit_status_counts={"fit_supported": confirmed},
        calibration_status_counts={"calibration_confirmed": confirmed},
        private_source_parameter_ledger_hash=HASH,
        private_event_ledger_hash="b" * 64,
        private_relation_ledger_hash="c" * 64,
        feasibility_gate_passed=feasible,
        process_outcome="feasible" if feasible else "infeasible",
        weighted_score_used=False,
        official_graph_used_for_scoring=False,
        attack_information_used=False,
        raw_values_included=False,
        creation_metadata=META,
    )


class ContractTests(unittest.TestCase):
    def test_source_parameter_non_promotion(self) -> None:
        record = ContinuousSourceScreeningRecordV1(
            "P1", "P1_A", HASH, "b" * 64,
            ("hai-23.05/hai-train1.csv", "hai-23.05/hai-train2.csv"),
            1.0, 20, 5.0, 3.0,
            "linear_interpolation_index_0.75_times_n_minus_1", "supported",
            "feasibility_screening", True, False, False, META,
        )
        self.assertFalse(record.final_parameter_authority)

    def test_train3_retuning_rejected(self) -> None:
        with self.assertRaises(HAIContinuousStepError):
            ContinuousCalibrationConfirmationRecordV1(
                "P1", HASH, "P1_A", "step_up", "P1_Y", "increase", 5,
                5, 0, 0.8, 0.1, 2.0, True, False, HASH, "b" * 64,
                "calibration_confirmed", META,
            )

    def test_lower_ranked_fallback_rejected(self) -> None:
        with self.assertRaises(HAIContinuousStepError):
            ContinuousDirectionalFitRecordV1(
                "P1", "P1_A", "step_up", "P1_Y", "increase", 5,
                10, 10, 20, 0, 0, 0.8, 0.8, 0.8, 2.0, 2.0, True, True, True,
                "fit_supported", HASH, "b" * 64, META,
            )

    def test_horizons_do_not_inflate_relation_count(self) -> None:
        first = ContinuousCalibrationConfirmationRecordV1(
            "P1", HASH, "P1_A", "step_up", "P1_Y", "increase", 5,
            5, 0, 0.8, 0.1, 2.0, True, True, HASH, "b" * 64,
            "calibration_confirmed", META,
        )
        second = replace(first, selected_horizon_seconds=10)
        self.assertEqual(len(deduplicate_directional_relations_v1((first, second))), 1)

    def test_round_trip_and_unknown_field_rejection(self) -> None:
        document = TASK039BR2ExecutionInterpretationV1(
            BR1_PROTOCOL_BUNDLE_HASH,
            "continuous_step_delayed_response_v1",
            "selected_consistency_strictly_greater_than_opposite_in_train1_and_train2",
            True,
            ("a", "b", "c", "d"),
            True,
            True,
            True,
            (),
            False,
            META,
        ).to_dict()
        self.assertEqual(TASK039BR2ExecutionInterpretationV1.from_dict(document).to_dict(), document)
        bad = copy.deepcopy(document)
        bad["unexpected"] = True
        with self.assertRaises(HAIContinuousStepError):
            TASK039BR2ExecutionInterpretationV1.from_dict(bad)

    def test_p1_only_selection(self) -> None:
        result = build_process_selection_v1(
            p1=feasibility("P1", feasible=True),
            p3=feasibility("P3", feasible=False),
            selection_policy_hash=HASH,
            creation_metadata=META,
        )
        self.assertEqual(result.selected_process_id, "P1")

    def test_p3_only_selection(self) -> None:
        result = build_process_selection_v1(
            p1=feasibility("P1", feasible=False),
            p3=feasibility("P3", feasible=True),
            selection_policy_hash=HASH,
            creation_metadata=META,
        )
        self.assertEqual(result.selected_process_id, "P3")

    def test_neither_feasible(self) -> None:
        result = build_process_selection_v1(
            p1=feasibility("P1", feasible=False),
            p3=feasibility("P3", feasible=False),
            selection_policy_hash=HASH,
            creation_metadata=META,
        )
        self.assertEqual(result.selection_status, "blocked_no_feasible_continuous_step_process")

    def test_equal_feasible_is_indeterminate(self) -> None:
        result = build_process_selection_v1(
            p1=feasibility("P1", feasible=True),
            p3=feasibility("P3", feasible=True),
            selection_policy_hash=HASH,
            creation_metadata=META,
        )
        self.assertEqual(result.selection_status, "blocked_continuous_process_selection_indeterminate")

    def test_pareto_dominance(self) -> None:
        p1 = replace(
            feasibility("P1", feasible=True),
            median_calibration_isolated_event_support=7.0,
            non_isolated_source_event_ratio=0.05,
        )
        p3 = feasibility("P3", feasible=True)
        result = build_process_selection_v1(
            p1=p1, p3=p3, selection_policy_hash=HASH, creation_metadata=META
        )
        self.assertEqual(result.selected_process_id, "P1")

    def test_process_freeze_has_no_rule_authority(self) -> None:
        freeze = HAIContinuousProcessFreezeV1(
            dataset_manifest_id=DATASET_MANIFEST_ID,
            br0_decision_hash="3eceafb47742af9fc1be5dba82f148d33e31ba3095ba4b8a2d513ab9d4632a7b",
            br1_protocol_bundle_hash=BR1_PROTOCOL_BUNDLE_HASH,
            execution_code_commit="a" * 40,
            selected_process_id="P1",
            selected_process_name="Boiler",
            excluded_process_id="P3",
            selection_reason="only_P1_feasible",
            selection_policy_hash=HASH,
            p1_feasibility_report_hash=HASH,
            p3_feasibility_report_hash="b" * 64,
            selected_private_relation_ledger_hash="c" * 64,
            selected_source_parameter_ledger_hash="d" * 64,
            normal_candidate_fit_split_id="e" * 64,
            normal_relation_calibration_split_id="f" * 64,
            normal_guard_split_id="1" * 64,
            canonical_rule_view_id="2" * 64,
            candidate_learning_view_id="3" * 64,
            gdn_view_status="pending_production_backend",
            rule_v2_status="not_created",
            task039c_authorized=True,
            claim_boundary=("candidate_universe_only",),
            validity_authority_granted=False,
            runtime_authority_granted=False,
            creation_metadata=META,
        )
        self.assertFalse(freeze.validity_authority_granted)
        self.assertFalse(freeze.runtime_authority_granted)


class AccessBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ledger = TASK039BR2DataAccessLedger({"P1": ("P1_A",), "P3": ("P3_A",)})

    def test_authorized_files(self) -> None:
        for path in AUTHORIZED_VALUE_FILES:
            self.ledger.authorize_value_file(path)
        self.assertEqual(self.ledger.opened_value_files, set(AUTHORIZED_VALUE_FILES))

    def test_normal_guard_rejected(self) -> None:
        with self.assertRaisesRegex(HAIContinuousStepError, "TASK039BR2_PROHIBITED_DATA_ACCESS"):
            self.ledger.authorize_value_file("hai-23.05/hai-train4.csv")

    def test_test_label_summary_rejected(self) -> None:
        for path in ("hai-23.05/hai-test1.csv", "hai-23.05/label-test1.csv", "hai-23.05/summary_label1.txt"):
            with self.assertRaises(HAIContinuousStepError):
                self.ledger.authorize_value_file(path)

    def test_p2_p4_columns_rejected(self) -> None:
        for name in ("P2_A", "P4_A"):
            with self.assertRaises(HAIContinuousStepError):
                self.ledger.authorize_columns((name,))

    def test_public_leak_scan(self) -> None:
        with self.assertRaises(HAIContinuousStepError):
            assert_public_payload_safe_v1({"event_index": 10})

    def test_synthetic_process_execution(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("hai-train1.csv", "hai-train2.csv", "hai-train3.csv"):
                rows = ["timestamp,P1_A,P1_Y"]
                rows.extend(f"{index},{0.0},{float(index)}" for index in range(30))
                (root / name).write_text("\n".join(rows) + "\n", encoding="utf-8")
            header_hash = hashlib.sha256(
                json.dumps(["P1_A", "P1_Y"], separators=(",", ":")).encode()
            ).hexdigest()
            verified = tuple(
                VerifiedNormalFileV1(path, HASH, 1, 30, header_hash, path != "hai-23.05/hai-train4.csv")
                for path in (
                    "hai-23.05/hai-train1.csv",
                    "hai-23.05/hai-train2.csv",
                    "hai-23.05/hai-train3.csv",
                    "hai-23.05/hai-train4.csv",
                )
            )
            ledger = TASK039BR2DataAccessLedger({"P1": ("P1_A", "P1_Y"), "P3": ("P3_A",)})
            result = execute_process_v1(
                process_id="P1",
                process_name="Boiler",
                eligibility={
                    "sources": ({"variable_name": "P1_A", "metadata_record_hash": HASH, "morphology_record_hash": "b" * 64},),
                    "targets": ({"variable_name": "P1_Y", "metadata_record_hash": "c" * 64},),
                },
                data_root=root,
                verified_files=verified,
                ledger=ledger,
                creation_metadata=META,
            )
            self.assertFalse(result.feasibility.feasibility_gate_passed)


if __name__ == "__main__":
    unittest.main()
