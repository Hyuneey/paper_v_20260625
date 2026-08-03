from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from paperworks.feasibility.hai_source_diagnosis_v1 import (
    AUTHORIZED_TRAIN_FILES,
    HAIContinuousRouteReadinessV1,
    HAIEndRouteReadinessV1,
    HAISourceDiagnosisError,
    HAISourceExclusionRecordV1,
    HAISourceExclusionSummaryV1,
    RelationFamilyRouteDecisionV1,
    RuleV1CompatibilityRecordV1,
    TASK039BR0DataAccessLedger,
    build_continuous_route_readiness,
    classify_source_exclusion,
    decide_relation_family_route,
    diagnose_continuous_source_morphology,
)
from paperworks.v6.schema_registry_v1 import load_v6_schema_registry_v1


H = "a" * 64


def metadata(
    *,
    role: str,
    domain: str,
    reviewed: bool = True,
    eligible: bool = False,
    name: str = "P1_X",
) -> dict[str, object]:
    return {
        "variable_name": name,
        "process_id": name[:2],
        "semantic_role": role,
        "observed_value_domain": domain,
        "review_status": "reviewed" if reviewed else "unresolved",
        "metadata_confidence": "high" if reviewed else "insufficient",
        "source_eligibility": eligible,
        "manual_reference": [12] if reviewed else [],
    }


def source_summary() -> HAISourceExclusionSummaryV1:
    return HAISourceExclusionSummaryV1(
        task039b_result_commit="6543ca5b88779262d01c5e0c24e51216dd0835e9",
        task039b_selection_hash="544ff2f3f06e3cfc0b683509ee0ef7aa85fd1f858d62206c9ea93ee9873d403c",
        frozen_status="blocked_no_feasible_delayed_response_process",
        frozen_metrics=({}, {}),
        counts_by_process=({}, {}),
        private_detail_ledger_hash=H,
    )


def rule_record() -> RuleV1CompatibilityRecordV1:
    return RuleV1CompatibilityRecordV1(
        rule_schema_sha256=H,
        rule_parser_sha256=H,
        verifier_sha256=H,
        runtime_sha256=H,
        exactly_one_source=True,
        exactly_one_target=True,
        delayed_response_only=True,
        state_changes_to_only=True,
        literal_state_value_required=True,
        trigger_threshold_references_rejected=True,
        trigger_range_references_rejected=True,
        trigger_duration_references_rejected=True,
        increase_only=True,
        missing_expected_response_only=True,
        verifier_runtime_bound_to_semantics=True,
        continuous_source_route_classification="requires_versioned_rule_semantics",
    )


def haiend_record(*, complete: bool) -> HAIEndRouteReadinessV1:
    inventory = tuple(
        {
            "relative_path": f"haiend-23.05/file-{index}",
            "git_blob_sha": "b" * 40,
            "lfs_oid_sha256": H,
            "lfs_size_bytes": index + 1,
            "payload_materialized_or_opened": False,
        }
        for index in range(10)
    )
    return HAIEndRouteReadinessV1(
        official_repository="https://github.com/icsdataset/hai",
        snapshot_commit="2a814cebc9a66b06c9e5cd545e2d72e65d383737",
        official_directory="haiend-23.05",
        pointer_inventory=inventory,
        file_count=10,
        expected_point_count=225,
        train_file_count=4,
        test_file_count=2,
        normal_data_availability_documented=True,
        same_experiment_version_context_documented=True,
        boiler_internal_control_logic_documented=True,
        technical_manual_per_point_coverage_verified=False,
        official_graph_relevance="reference_only_non_scoring",
        license_and_citation_compatible=True,
        payload_downloaded_or_opened=False,
        binary_or_discrete_claim_made=False,
        row_synchronization_claim_made=False,
        complete_auditable_p1_candidate_route=complete,
        route_status="haiend_route_requires_separate_provenance_and_feasibility",
    )


def readiness(*, ready: tuple[str, ...]) -> HAIContinuousRouteReadinessV1:
    records = tuple(
        {
            "process_id": process,
            "route_status": (
                "continuous_step_route_ready_for_versioned_feasibility"
                if process in ready
                else "continuous_step_route_not_ready"
            ),
        }
        for process in ("P1", "P3")
    )
    return HAIContinuousRouteReadinessV1(
        process_records=records,
        readiness_definition="synthetic",
        ready_process_ids=ready,
        private_morphology_ledger_hash=H,
    )


class SourceExclusionTests(unittest.TestCase):
    def test_every_closed_exclusion_category(self) -> None:
        cases = (
            (metadata(role="control_command", domain="binary", eligible=True), {}, "eligible_under_failed_discrete_policy"),
            (metadata(role="control_command", domain="continuous"), {}, "documented_continuous_control_command"),
            (metadata(role="actuator_feedback", domain="continuous"), {}, "documented_continuous_actuator_feedback"),
            (metadata(role="setpoint", domain="continuous"), {}, "documented_setpoint"),
            (metadata(role="process_sensor", domain="continuous"), {}, "documented_process_sensor"),
            (metadata(role="status_or_alarm", domain="binary"), {}, "documented_status_or_alarm"),
            (metadata(role="derived_or_internal", domain="continuous"), {}, "documented_internal_or_derived"),
            (metadata(role="unknown", domain="binary"), {}, "discrete_but_not_control_semantics"),
            (metadata(role="control_command", domain="constant"), {}, "control_semantics_but_constant"),
            (metadata(role="control_command", domain="discrete"), {"source_change_count": 1}, "control_semantics_but_insufficient_changes"),
            (metadata(role="control_command", domain="binary", reviewed=False), {}, "semantic_role_unresolved"),
            (metadata(role="control_command", domain="unknown"), {}, "value_domain_unresolved"),
            (metadata(role="control_command", domain="continuous"), {"manual_data_conflict": True}, "manual_and_data_evidence_conflict"),
            (metadata(role="unknown", domain="continuous"), {}, "excluded_other"),
        )
        for record, kwargs, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(classify_source_exclusion(record, **kwargs), expected)

    def test_exclusion_record_hash_is_deterministic(self) -> None:
        record = HAISourceExclusionRecordV1(
            variable_name="P1_X",
            process_id="P1",
            documented_semantic_role="control_command",
            observed_domain="continuous",
            task039b_source_eligibility=False,
            primary_exclusion_reason="documented_continuous_control_command",
            secondary_exclusion_reasons=(),
            manual_reference=(12,),
            official_graph_references=(),
            aggregate_domain_diagnostic_ref=H,
            review_status="reviewed",
            metadata_confidence="high",
        )
        self.assertEqual(record.to_dict(), record.to_dict())
        self.assertEqual(len(record.artifact_hash), 64)


class MorphologyTests(unittest.TestCase):
    def _write_files(self, root: Path) -> None:
        header = ["timestamp", "P1_A", "P1_B", "P1_SENSOR", "P3_A", "P3_B", "P2_X", "P4_X"]
        sequences = {
            "P1_A": [0, 0, 0, 10, 10, 10, 0, 0, 0],
            "P1_B": [5, 5, 5, 15, 15, 15, 5, 5, 5],
            "P1_SENSOR": [1, 2, 3, 4, 5, 6, 7, 8, 9],
            "P3_A": [0, 0, 0, 20, 20, 20, 0, 0, 0],
            "P3_B": [2, 2, 2, 12, 12, 12, 2, 2, 2],
        }
        for relative in AUTHORIZED_TRAIN_FILES:
            path = root / Path(relative).name
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(header)
                for index in range(9):
                    writer.writerow(
                        [
                            f"t{index}",
                            sequences["P1_A"][index],
                            sequences["P1_B"][index],
                            sequences["P1_SENSOR"][index],
                            sequences["P3_A"][index],
                            sequences["P3_B"][index],
                            999,
                            888,
                        ]
                    )

    def test_continuous_morphology_and_route_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._write_files(root)
            records = []
            ledger = TASK039BR0DataAccessLedger()
            for process in ("P1", "P3"):
                records.extend(
                    diagnose_continuous_source_morphology(
                        data_root=root,
                        process_id=process,
                        metadata_records=(
                            metadata(role="control_command", domain="continuous", name=f"{process}_A"),
                            metadata(role="actuator_feedback", domain="continuous", name=f"{process}_B"),
                            metadata(role="process_sensor", domain="continuous", name="P1_SENSOR"),
                        ),
                        ledger=ledger,
                    )
                )
            self.assertEqual(len(records), 4)
            self.assertTrue(all(all(item.repeated_bounded_changes for item in record.file_summaries) for record in records))
            result = build_continuous_route_readiness(records, private_morphology_ledger_hash=H)
            self.assertEqual(result.ready_process_ids, ("P1", "P3"))
            audit = ledger.freeze()
            self.assertFalse(audit.p2_p4_feature_values_accessed)
            self.assertFalse(audit.normal_guard_feature_values_accessed)

    def test_data_behavior_cannot_invent_control_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._write_files(root)
            result = diagnose_continuous_source_morphology(
                data_root=root,
                process_id="P1",
                metadata_records=(metadata(role="process_sensor", domain="continuous", name="P1_SENSOR"),),
                ledger=TASK039BR0DataAccessLedger(),
            )
            self.assertEqual(result, ())


class AccessBoundaryTests(unittest.TestCase):
    def test_test_label_summary_and_guard_are_rejected(self) -> None:
        ledger = TASK039BR0DataAccessLedger()
        for path in (
            "hai-23.05/hai-test1.csv",
            "hai-23.05/label-test1.csv",
            "hai-23.05/summary_label1.txt",
            "hai-23.05/hai-train4.csv",
        ):
            with self.subTest(path=path), self.assertRaisesRegex(
                HAISourceDiagnosisError, "TASK039BR0_PROHIBITED_DATA_ACCESS"
            ):
                ledger.reject_path(path)

    def test_p2_p4_scope_rejected(self) -> None:
        ledger = TASK039BR0DataAccessLedger()
        for process, variable in (("P2", "P2_X"), ("P4", "P4_X")):
            with self.subTest(process=process), self.assertRaises(HAISourceDiagnosisError):
                ledger.authorize_feature_access(AUTHORIZED_TRAIN_FILES[0], process, (variable,))


class RouteDecisionTests(unittest.TestCase):
    def _decide(
        self, ready: tuple[str, ...], *, haiend_complete: bool, conflict: bool = False
    ) -> RelationFamilyRouteDecisionV1:
        return decide_relation_family_route(
            continuous=readiness(ready=ready),
            haiend=haiend_record(complete=haiend_complete),
            rule_v1=rule_record(),
            source_summary=source_summary(),
            evidence_conflict=conflict,
        )

    def test_route_1(self) -> None:
        result = self._decide(("P1",), haiend_complete=True)
        self.assertEqual(result.recommended_route, "versioned_continuous_step_delayed_response_on_HAI")
        self.assertEqual(result.next_task, "TASK-039BR1")
        self.assertFalse(result.process_selected)

    def test_route_2(self) -> None:
        result = self._decide((), haiend_complete=True)
        self.assertEqual(result.recommended_route, "audit_HAIEnd_P1_control_logic")

    def test_route_3(self) -> None:
        result = self._decide((), haiend_complete=False)
        self.assertEqual(result.recommended_route, "reopen_primary_dataset_decision")

    def test_indeterminate(self) -> None:
        result = self._decide(("P1",), haiend_complete=True, conflict=True)
        self.assertEqual(result.recommended_route, "blocked_relation_family_decision_indeterminate")

    def test_official_graph_is_not_a_decision_input(self) -> None:
        result = self._decide((), haiend_complete=False)
        self.assertNotIn("graph", " ".join(result.decision_reasons).lower())


class ContractAndSchemaTests(unittest.TestCase):
    def test_rule_v1_continuous_route_requires_versioned_semantics(self) -> None:
        record = rule_record()
        self.assertEqual(record.continuous_source_route_classification, "requires_versioned_rule_semantics")
        self.assertFalse(record.rule_v1_modified)

    def test_haiend_claim_boundary(self) -> None:
        record = haiend_record(complete=True)
        self.assertFalse(record.payload_downloaded_or_opened)
        self.assertFalse(record.binary_or_discrete_claim_made)
        self.assertFalse(record.row_synchronization_claim_made)

    def test_schema_registry_contains_task_artifacts(self) -> None:
        registry = load_v6_schema_registry_v1(repository_root=Path(__file__).resolve().parents[1])
        expected = {
            "hai_source_exclusion_record_v1",
            "hai_source_exclusion_summary_v1",
            "hai_continuous_source_morphology_v1",
            "hai_continuous_route_readiness_v1",
            "haiend_route_readiness_v1",
            "rule_v1_compatibility_record_v1",
            "relation_family_route_decision_v1",
            "task039br0_data_access_audit_v1",
        }
        self.assertTrue(expected.issubset(set(registry.artifact_types)))

    def test_config_is_self_hashed_and_graph_is_non_scoring(self) -> None:
        path = Path(__file__).resolve().parents[1] / "configs/v6/task039br0_source_eligibility_diagnosis.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        observed = payload.pop("config_hash")
        from paperworks.v6.common import stable_hash_v1

        self.assertEqual(observed, stable_hash_v1(payload))
        self.assertFalse(payload["official_graph_used_for_route_score"])


if __name__ == "__main__":
    unittest.main()
