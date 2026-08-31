from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

from paperworks.validation_v2.metric_contract_v1 import (
    BooleanAlarmInputV1,
    D1MetricOutcomeV1,
    D1OutcomeInputV1,
    LabelPointV1,
    MetricContractError,
    PredictionCoordinateV1,
    adapt_boolean_alarm_timeline_v1,
    adapt_d1_alarm_timeline_v1,
    aggregate_synthetic_common_evaluation_v1,
    build_common_metric_contract_v1,
    build_file_second_series_authority_v1,
    build_label_timeline_v1,
    compare_common_results_v1,
    derive_attack_event_units_v1,
    evaluate_common_timeline_v1,
    form_alarm_episodes_v1,
    validate_common_alarm_timeline_v1,
    validate_common_comparison_result_v1,
    validate_common_evaluation_bundle_v1,
    validate_common_evaluation_result_v1,
    validate_common_metric_contract_v1,
    validate_label_timeline_v1,
)
from paperworks.validation_v2.protocol_v1 import build_validation_protocol_v1
from paperworks.validation_v2.prediction_custody_v1 import (
    D1PredictionArtifactV2,
    D1PredictionRecordV2,
    persist_prediction_before_label_v1,
)
from paperworks.validation_v2.schema_registry_v1 import validate_validation_v2_document_v1
from paperworks.validation_v2.formal_v4_authority_v1 import canonical_document_hash_v1
from paperworks.validation_v2.runtime_v1 import FORMAL_V4_RUNTIME_VERSION, FormalV4RuntimeTraceV1


HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
HASH_D = "d" * 64
HASH_E = "e" * 64
COMMIT = "1" * 40


class ValidationV2MetricContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.protocol = build_validation_protocol_v1(source_commit=COMMIT)
        self.contract = build_common_metric_contract_v1(self.protocol)

    def coordinates(self, lengths: tuple[int, ...] = (8, 3)) -> tuple[PredictionCoordinateV1, ...]:
        values: list[PredictionCoordinateV1] = []
        for file_number, length in enumerate(lengths):
            file_id = f"file-{chr(ord('a') + file_number)}"
            file_hash = (chr(ord("a") + file_number) * 64)
            start = 1000 * (file_number + 1)
            values.extend(
                PredictionCoordinateV1(file_id, file_hash, index, start + index)
                for index in range(length)
            )
        return tuple(values)

    def boolean_records(self, alarms: tuple[bool, ...], *, lengths: tuple[int, ...] = (8, 3)):
        coordinates = self.coordinates(lengths)
        self.assertEqual(len(coordinates), len(alarms))
        return tuple(BooleanAlarmInputV1(coordinate, alarm) for coordinate, alarm in zip(coordinates, alarms))

    def file_series(self, lengths: tuple[int, ...] = (8, 3)):
        return build_file_second_series_authority_v1(
            dataset_id="SYNTHETIC-DATASET", sampling_contract_hash=HASH_E,
            coordinates=self.coordinates(lengths),
        )

    def prediction(self, alarms: tuple[bool, ...], *, method: str = "D0", lengths: tuple[int, ...] = (8, 3)):
        return adapt_boolean_alarm_timeline_v1(
            method_id=method,
            config_id=f"{method}-CONFIG",
            source_prediction_sha256=HASH_A,
            prediction_freeze_receipt_sha256=HASH_B,
            contract=self.contract, protocol=self.protocol,
            file_series=self.file_series(lengths),
            records=self.boolean_records(alarms, lengths=lengths),
        )

    def labels(self, values: tuple[int, ...], *, lengths: tuple[int, ...] = (8, 3)):
        coordinates = self.coordinates(lengths)
        self.assertEqual(len(coordinates), len(values))
        return build_label_timeline_v1(
            dataset_id="SYNTHETIC-DATASET",
            label_authority_sha256=HASH_C,
            file_series=self.file_series(lengths),
            points=tuple(LabelPointV1(coordinate, label) for coordinate, label in zip(coordinates, values)),
        )

    def d1_outcome(
        self,
        coordinate: PredictionCoordinateV1,
        outcome: D1MetricOutcomeV1,
        *, opportunity: str = "OP-1",
        rule: str = "RULE-1",
        authorization_hash: str = HASH_D,
        execution_context_hash: str = HASH_E,
    ) -> D1OutcomeInputV1:
        if coordinate.row_index < 1:
            raise ValueError("synthetic D1 outcome requires a post-horizon row")
        payload = {
            "alarm_emitted": outcome is D1MetricOutcomeV1.FAIL,
            "authorization_hash": authorization_hash,
            "descriptor_hash": HASH_A,
            "execution_context_hash": execution_context_hash,
            "final_outcome": outcome.value,
            "opportunity_id": opportunity,
            "reason": f"SYNTHETIC_{outcome.value}",
            "relation_id": rule,
            "runtime_version": FORMAL_V4_RUNTIME_VERSION,
        }
        trace = FormalV4RuntimeTraceV1(
            opportunity_id=opportunity, relation_id=rule, descriptor_hash=HASH_A,
            authorization_hash=authorization_hash, execution_context_hash=execution_context_hash,
            final_outcome=outcome.value, reason=payload["reason"],
            alarm_emitted=payload["alarm_emitted"], trace_hash=canonical_document_hash_v1(payload),
        )
        return D1OutcomeInputV1(
            file_id=coordinate.file_id,
            feature_file_sha256=coordinate.feature_file_sha256,
            event_row_index=coordinate.row_index - 1,
            target_response_start_index=coordinate.row_index,
            response_window_seconds=1,
            selected_horizon_seconds=1,
            decision_row_index=coordinate.row_index,
            decision_timestamp_second=coordinate.timestamp_second,
            trace=trace,
        )

    def d1_artifact(
        self, coordinates: tuple[PredictionCoordinateV1, ...], outcomes: tuple[D1OutcomeInputV1, ...],
    ) -> D1PredictionArtifactV2:
        grouped: dict[tuple[str, int], list[D1OutcomeInputV1]] = {}
        for item in outcomes:
            grouped.setdefault((item.file_id, item.decision_row_index), []).append(item)
        records = []
        for coordinate in coordinates:
            fail = tuple(item for item in grouped.get((coordinate.file_id, coordinate.row_index), ()) if item.trace.final_outcome == "FAIL")
            records.append(D1PredictionRecordV2(
                file_id=coordinate.file_id, file_content_sha256=coordinate.feature_file_sha256,
                row_index=coordinate.row_index, alarm=bool(fail),
                contributing_rule_ids=tuple(sorted({item.trace.relation_id for item in fail})),
                trace_hashes=tuple(sorted({item.trace.trace_hash for item in fail})),
            ))
        return D1PredictionArtifactV2(
            method_id="D1", config_id="D1-CONFIG", experiment_id="SYNTHETIC-EXP",
            dataset_id="SYNTHETIC-DATASET", split_role="DEVELOPMENT_TEST1",
            authority_hash=HASH_A, runtime_authorization_hash=HASH_D,
            execution_context_hash=HASH_E, source_commit=COMMIT,
            portfolio_hash=HASH_B, file_contract_hash=HASH_C, records=tuple(records),
        )

    def freeze_receipt(self, artifact: D1PredictionArtifactV2):
        with tempfile.TemporaryDirectory() as root:
            return persist_prediction_before_label_v1(
                artifact, artifact_root=Path(root).resolve(),
                prediction_relative_path="prediction.json", receipt_relative_path="receipt.json",
            )

    def test_contract_replays_and_protocol_mutation_is_rejected(self) -> None:
        self.assertEqual(validate_common_metric_contract_v1(self.contract, protocol=self.protocol), self.contract.contract_hash)
        validate_validation_v2_document_v1("common_metric_contract_v1.schema.json", self.contract.to_dict())
        with self.assertRaisesRegex(MetricContractError, "METRIC_CONTRACT_REPLAY_MISMATCH"):
            validate_common_metric_contract_v1(replace(self.contract, sampling_seconds=2), protocol=self.protocol)

    def test_public_adapter_rejects_rehashed_forged_contract(self) -> None:
        forged = replace(self.contract, sampling_seconds=2, contract_hash="")
        forged = replace(forged, contract_hash=sha256(json.dumps(
            forged.body_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        ).encode("utf-8")).hexdigest())
        with self.assertRaisesRegex(MetricContractError, "METRIC_CONTRACT_REPLAY_MISMATCH"):
            adapt_boolean_alarm_timeline_v1(
                method_id="D0", config_id="C", source_prediction_sha256=HASH_A,
                prediction_freeze_receipt_sha256=HASH_B, contract=forged, protocol=self.protocol,
                file_series=self.file_series((1,)), records=self.boolean_records((False,), lengths=(1,)),
            )

    def test_dense_boolean_adapter_requires_exact_boolean_and_complete_sorted_grid(self) -> None:
        timeline = self.prediction((False,) * 11)
        self.assertEqual(validate_common_alarm_timeline_v1(timeline, file_series=self.file_series()), timeline.self_hash)
        coordinate = self.coordinates((1,))[0]
        with self.assertRaisesRegex(MetricContractError, "INVALID_BOOLEAN_ALARM"):
            BooleanAlarmInputV1(coordinate, 0)  # type: ignore[arg-type]
        records = self.boolean_records((False, False), lengths=(2,))
        with self.assertRaisesRegex(MetricContractError, "BOOLEAN_PREDICTION_FILE_SERIES_COVERAGE_MISMATCH"):
            adapt_boolean_alarm_timeline_v1(
                method_id="D0", config_id="C", source_prediction_sha256=HASH_A,
                prediction_freeze_receipt_sha256=HASH_B, contract=self.contract, protocol=self.protocol,
                file_series=self.file_series((2,)),
                records=tuple(reversed(records)),
            )

    def test_coordinate_contract_rejects_gap_offset_duplicate_and_non_second_time(self) -> None:
        base = self.coordinates((2,))
        invalid_sets = (
            (replace(base[0], row_index=1), replace(base[1], row_index=2)),
            (base[0], replace(base[1], row_index=0)),
            (base[0], replace(base[1], timestamp_second=base[0].timestamp_second + 2)),
        )
        for coordinates in invalid_sets:
            with self.subTest(coordinates=coordinates), self.assertRaises(MetricContractError):
                adapt_boolean_alarm_timeline_v1(
                    method_id="D0", config_id="C", source_prediction_sha256=HASH_A,
                    prediction_freeze_receipt_sha256=HASH_B, contract=self.contract, protocol=self.protocol,
                    file_series=build_file_second_series_authority_v1(
                        dataset_id="SYNTHETIC-DATASET", sampling_contract_hash=HASH_E,
                        coordinates=coordinates,
                    ),
                    records=tuple(BooleanAlarmInputV1(item, False) for item in coordinates),
                )

    def test_file_hash_must_be_stable_within_file(self) -> None:
        base = self.coordinates((2,))
        with self.assertRaisesRegex(MetricContractError, "INCONSISTENT_FEATURE_FILE_HASH"):
            adapt_boolean_alarm_timeline_v1(
                method_id="D0", config_id="C", source_prediction_sha256=HASH_A,
                prediction_freeze_receipt_sha256=HASH_B, contract=self.contract, protocol=self.protocol,
                file_series=build_file_second_series_authority_v1(
                    dataset_id="SYNTHETIC-DATASET", sampling_contract_hash=HASH_E,
                    coordinates=(base[0], replace(base[1], feature_file_sha256=HASH_B)),
                ),
                records=(BooleanAlarmInputV1(base[0], False), BooleanAlarmInputV1(replace(base[1], feature_file_sha256=HASH_B), False)),
            )

    def test_authoritative_file_series_rejects_prefix_missing_and_extra_files(self) -> None:
        authority = self.file_series((3, 2))
        full = tuple(BooleanAlarmInputV1(item, False) for item in authority.coordinates)
        variants = (
            full[:2] + full[3:],
            full[:3],
            full + (BooleanAlarmInputV1(PredictionCoordinateV1("file-c", "c" * 64, 0, 3000), False),),
        )
        for records in variants:
            with self.subTest(record_count=len(records)), self.assertRaisesRegex(
                MetricContractError, "BOOLEAN_PREDICTION_FILE_SERIES_COVERAGE_MISMATCH"
            ):
                adapt_boolean_alarm_timeline_v1(
                    method_id="D0", config_id="C", source_prediction_sha256=HASH_A,
                    prediction_freeze_receipt_sha256=HASH_B, contract=self.contract, protocol=self.protocol,
                    file_series=authority, records=records,
                )
        with self.assertRaisesRegex(MetricContractError, "LABEL_FILE_SERIES_COVERAGE_MISMATCH"):
            build_label_timeline_v1(
                dataset_id="S", label_authority_sha256=HASH_C, file_series=authority,
                points=tuple(LabelPointV1(item.coordinate, 0) for item in full[:-1]),
            )

    def test_file_local_episode_and_event_runs_never_merge_across_files(self) -> None:
        prediction = self.prediction((True, True), lengths=(1, 1))
        labels = self.labels((1, 1), lengths=(1, 1))
        file_series = self.file_series((1, 1))
        self.assertEqual(len(form_alarm_episodes_v1(prediction, file_series=file_series)), 2)
        self.assertEqual(len(derive_attack_event_units_v1(labels, file_series=file_series)), 2)
        self.assertEqual({item.file_id for item in form_alarm_episodes_v1(prediction, file_series=file_series)}, {"file-a", "file-b"})

    def test_d1_native_outcomes_reconcile_fail_only_to_durable_boolean(self) -> None:
        coordinates = self.coordinates((4,))
        outcomes = (
            self.d1_outcome(coordinates[1], D1MetricOutcomeV1.PASS),
            self.d1_outcome(coordinates[2], D1MetricOutcomeV1.FAIL),
            self.d1_outcome(coordinates[2], D1MetricOutcomeV1.PASS, opportunity="OP-2", rule="RULE-2"),
            self.d1_outcome(coordinates[3], D1MetricOutcomeV1.ABSTAIN),
        )
        artifact = self.d1_artifact(coordinates, outcomes)
        timeline = adapt_d1_alarm_timeline_v1(
            prediction_artifact=artifact, freeze_receipt=self.freeze_receipt(artifact),
            contract=self.contract, protocol=self.protocol, file_series=self.file_series((4,)), outcomes=outcomes,
        )
        self.assertEqual(tuple(point.alarm for point in timeline.points), (False, False, True, False))
        self.assertIn(("FAIL", 1), timeline.native_state_counts)
        self.assertIn(("PASS", 2), timeline.native_state_counts)
        self.assertIn(("ABSTAIN", 1), timeline.native_state_counts)

    def test_d1_no_outcome_is_explicit_no_opportunity(self) -> None:
        coordinates = self.coordinates((2,))
        artifact = self.d1_artifact(coordinates, ())
        timeline = adapt_d1_alarm_timeline_v1(
            prediction_artifact=artifact, freeze_receipt=self.freeze_receipt(artifact),
            contract=self.contract, protocol=self.protocol, file_series=self.file_series((2,)), outcomes=(),
        )
        self.assertEqual(timeline.native_state_counts, (("ABSTAIN", 0), ("FAIL", 0), ("NO_OPPORTUNITY", 2), ("PASS", 0)))

    def test_d1_rejects_system_error_unknown_type_duplicate_and_boolean_mismatch(self) -> None:
        coordinates = self.coordinates((2,))
        coordinate = coordinates[1]
        fail = self.d1_outcome(coordinate, D1MetricOutcomeV1.FAIL)
        correct_artifact = self.d1_artifact(coordinates, (fail,))
        kwargs = dict(
            prediction_artifact=correct_artifact, freeze_receipt=self.freeze_receipt(correct_artifact),
            contract=self.contract, protocol=self.protocol,
            file_series=self.file_series((2,)),
        )
        with self.assertRaisesRegex(MetricContractError, "D1_SYSTEM_ERROR"):
            self.d1_outcome(coordinate, D1MetricOutcomeV1.SYSTEM_ERROR)
        with self.assertRaisesRegex(MetricContractError, "DUPLICATE_D1_TRACE_OUTCOME"):
            adapt_d1_alarm_timeline_v1(**kwargs, outcomes=(fail, fail))
        false_artifact = self.d1_artifact(coordinates, ())
        with self.assertRaisesRegex(MetricContractError, "D1_BOOLEAN_NATIVE_OUTCOME_MISMATCH"):
            adapt_d1_alarm_timeline_v1(
                **{**kwargs, "prediction_artifact": false_artifact, "freeze_receipt": self.freeze_receipt(false_artifact)},
                outcomes=(fail,),
            )

    def test_d1_rejects_inferred_or_mismatched_decision_and_authority(self) -> None:
        coordinates = self.coordinates((2,))
        coordinate = coordinates[1]
        valid = self.d1_outcome(coordinate, D1MetricOutcomeV1.PASS)
        artifact = self.d1_artifact(coordinates, (valid,))
        kwargs = dict(
            prediction_artifact=artifact, freeze_receipt=self.freeze_receipt(artifact),
            contract=self.contract, protocol=self.protocol,
            file_series=self.file_series((2,)),
        )
        for outcome in (
            replace(valid, decision_timestamp_second=999),
            replace(valid, feature_file_sha256=HASH_B),
        ):
            with self.subTest(outcome=outcome), self.assertRaisesRegex(MetricContractError, "D1_DECISION_COORDINATE_BINDING_MISMATCH"):
                adapt_d1_alarm_timeline_v1(**kwargs, outcomes=(outcome,))
        wrong_authority = self.d1_outcome(coordinate, D1MetricOutcomeV1.PASS, authorization_hash=HASH_A)
        with self.assertRaisesRegex(MetricContractError, "D1_RUNTIME_AUTHORITY_MISMATCH"):
            adapt_d1_alarm_timeline_v1(**kwargs, outcomes=(wrong_authority,))
        with self.assertRaisesRegex(MetricContractError, "D1_HORIZON_BINDING_MISMATCH"):
            replace(valid, target_response_start_index=0)

    def test_d1_reconciles_rule_and_trace_provenance_exactly(self) -> None:
        coordinates = self.coordinates((2,))
        fail = self.d1_outcome(coordinates[1], D1MetricOutcomeV1.FAIL)
        artifact = self.d1_artifact(coordinates, (fail,))
        wrong_record = replace(artifact.records[1], contributing_rule_ids=("WRONG-RULE",))
        wrong_artifact = replace(artifact, records=(artifact.records[0], wrong_record))
        with self.assertRaisesRegex(MetricContractError, "D1_PREDICTION_PROVENANCE_RECONCILIATION_MISMATCH"):
            adapt_d1_alarm_timeline_v1(
                prediction_artifact=wrong_artifact, freeze_receipt=self.freeze_receipt(wrong_artifact),
                contract=self.contract, protocol=self.protocol,
                file_series=self.file_series((2,)), outcomes=(fail,),
            )
        with self.assertRaisesRegex(MetricContractError, "D1_FREEZE_RECEIPT_ARTIFACT_BINDING_MISMATCH"):
            adapt_d1_alarm_timeline_v1(
                prediction_artifact=replace(artifact, config_id="OTHER-CONFIG"),
                freeze_receipt=self.freeze_receipt(artifact), contract=self.contract,
                protocol=self.protocol, file_series=self.file_series((2,)), outcomes=(fail,),
            )

    def test_labels_are_strict_binary_integers(self) -> None:
        coordinate = self.coordinates((1,))[0]
        for value in (True, 0.0, "0", 2):
            with self.subTest(value=value), self.assertRaisesRegex(MetricContractError, "INVALID_STRICT_BINARY_LABEL"):
                LabelPointV1(coordinate, value)  # type: ignore[arg-type]

    def test_recall_far_and_count_levels_use_exact_contract(self) -> None:
        labels = self.labels((0, 1, 1, 0, 0, 1, 0, 0, 1, 0, 0))
        prediction = self.prediction((False, True, False, True, False, False, True, False, False, False, False))
        result = evaluate_common_timeline_v1(contract=self.contract, protocol=self.protocol, file_series=self.file_series(), prediction=prediction, labels=labels)
        self.assertEqual(len(result.attack_events), 3)
        self.assertEqual(sum(detected for _, detected in result.attack_detection), 1)
        self.assertEqual(result.recall.value_decimal, "0.3333333333333333333333333333333333")
        self.assertEqual(result.alarm_seconds, 3)
        self.assertEqual(len(result.alarm_episodes), 3)
        self.assertEqual(result.normal_false_episodes, 2)
        self.assertEqual(result.normal_exposure_seconds, 7)
        self.assertEqual(result.far_per_hour.value_decimal, "1028.571428571428571428571428571429")

    def test_mixed_episode_is_excluded_whole_but_normal_exposure_remains(self) -> None:
        labels = self.labels((0, 1, 1, 0), lengths=(4,))
        prediction = self.prediction((False, False, True, True), lengths=(4,))
        result = evaluate_common_timeline_v1(contract=self.contract, protocol=self.protocol, file_series=self.file_series((4,)), prediction=prediction, labels=labels)
        self.assertEqual(result.normal_false_episodes, 0)
        self.assertEqual(result.normal_exposure_seconds, 2)
        self.assertEqual(result.recall.value_decimal, "1")

    def test_one_alarm_episode_may_hit_multiple_attack_units(self) -> None:
        labels = self.labels((1, 0, 1), lengths=(3,))
        prediction = self.prediction((True, True, True), lengths=(3,))
        result = evaluate_common_timeline_v1(contract=self.contract, protocol=self.protocol, file_series=self.file_series((3,)), prediction=prediction, labels=labels)
        self.assertEqual(len(result.alarm_episodes), 1)
        self.assertEqual(result.recall.value_decimal, "1")
        self.assertEqual(sum(detected for _, detected in result.attack_detection), 2)

    def test_half_open_touching_boundary_without_shared_row_is_not_overlap(self) -> None:
        labels = self.labels((1, 0), lengths=(2,))
        prediction = self.prediction((False, True), lengths=(2,))
        result = evaluate_common_timeline_v1(contract=self.contract, protocol=self.protocol, file_series=self.file_series((2,)), prediction=prediction, labels=labels)
        self.assertEqual(result.recall.value_decimal, "0")
        self.assertEqual(result.normal_false_episodes, 1)

    def test_undefined_metrics_are_explicit_not_zero(self) -> None:
        no_events = evaluate_common_timeline_v1(
            contract=self.contract, protocol=self.protocol,
            file_series=self.file_series((2,)),
            prediction=self.prediction((False, False), lengths=(2,)),
            labels=self.labels((0, 0), lengths=(2,)),
        )
        self.assertFalse(no_events.recall.defined)
        self.assertEqual(no_events.recall.undefined_reason, "NO_ATTACK_EVENTS")
        no_normal = evaluate_common_timeline_v1(
            contract=self.contract, protocol=self.protocol,
            file_series=self.file_series((2,)),
            prediction=self.prediction((False, False), lengths=(2,)),
            labels=self.labels((1, 1), lengths=(2,)),
        )
        self.assertFalse(no_normal.far_per_hour.defined)
        self.assertEqual(no_normal.far_per_hour.undefined_reason, "NO_NORMAL_EXPOSURE")

    def test_prediction_label_alignment_requires_exact_file_hash_time_and_rows(self) -> None:
        prediction = self.prediction((False, False), lengths=(2,))
        mismatched_coordinates = tuple(
            replace(coordinate, feature_file_sha256=HASH_B)
            for coordinate in self.coordinates((2,))
        )
        labels = build_label_timeline_v1(
            dataset_id="S", label_authority_sha256=HASH_C,
            file_series=build_file_second_series_authority_v1(
                dataset_id="S", sampling_contract_hash=HASH_E,
                coordinates=mismatched_coordinates,
            ),
            points=tuple(LabelPointV1(coordinate, 0) for coordinate in mismatched_coordinates),
        )
        with self.assertRaisesRegex(MetricContractError, "LABEL_TIMELINE_FILE_SERIES_COVERAGE_MISMATCH"):
            evaluate_common_timeline_v1(contract=self.contract, protocol=self.protocol, file_series=self.file_series((2,)), prediction=prediction, labels=labels)

    def test_comparison_overlap_recovery_and_negative_increment_are_exact(self) -> None:
        labels = self.labels((1, 0, 1, 0), lengths=(4,))
        baseline = evaluate_common_timeline_v1(
            contract=self.contract, protocol=self.protocol, file_series=self.file_series((4,)), prediction=self.prediction((True, False, False, True), method="BASE", lengths=(4,)), labels=labels,
        )
        candidate = evaluate_common_timeline_v1(
            contract=self.contract, protocol=self.protocol, file_series=self.file_series((4,)), prediction=self.prediction((False, False, True, False), method="CAND", lengths=(4,)), labels=labels,
        )
        comparison = compare_common_results_v1(contract=self.contract, protocol=self.protocol, baseline=baseline, candidate=candidate)
        self.assertEqual((comparison.both, comparison.baseline_only, comparison.candidate_only, comparison.neither), (0, 1, 1, 0))
        self.assertEqual(comparison.baseline_miss_recovery.value_decimal, "1")
        self.assertEqual(comparison.incremental_detected_units, 0)
        self.assertEqual(comparison.incremental_false_episodes, -1)
        self.assertEqual(comparison.incremental_far_per_hour.value_decimal, "-1800")

    def test_zero_baseline_misses_makes_recovery_undefined(self) -> None:
        labels = self.labels((1, 0), lengths=(2,))
        baseline = evaluate_common_timeline_v1(
            contract=self.contract, protocol=self.protocol, file_series=self.file_series((2,)), prediction=self.prediction((True, False), method="BASE", lengths=(2,)), labels=labels,
        )
        candidate = evaluate_common_timeline_v1(
            contract=self.contract, protocol=self.protocol, file_series=self.file_series((2,)), prediction=self.prediction((True, False), method="CAND", lengths=(2,)), labels=labels,
        )
        comparison = compare_common_results_v1(contract=self.contract, protocol=self.protocol, baseline=baseline, candidate=candidate)
        self.assertFalse(comparison.baseline_miss_recovery.defined)
        self.assertEqual(comparison.baseline_miss_recovery.undefined_reason, "NO_BASELINE_MISSED_ATTACK_EVENTS")

    def test_cross_method_comparison_rejects_different_label_authority(self) -> None:
        labels = self.labels((1, 0), lengths=(2,))
        baseline = evaluate_common_timeline_v1(
            contract=self.contract, protocol=self.protocol, file_series=self.file_series((2,)), prediction=self.prediction((True, False), method="BASE", lengths=(2,)), labels=labels,
        )
        different_labels = build_label_timeline_v1(
            dataset_id="SYNTHETIC-DATASET", label_authority_sha256=HASH_D,
            file_series=self.file_series((2,)), points=labels.points,
        )
        candidate = evaluate_common_timeline_v1(
            contract=self.contract, protocol=self.protocol, file_series=self.file_series((2,)), prediction=self.prediction((True, False), method="CAND", lengths=(2,)), labels=different_labels,
        )
        with self.assertRaisesRegex(MetricContractError, "CROSS_METHOD_AUTHORITY_MISMATCH"):
            compare_common_results_v1(contract=self.contract, protocol=self.protocol, baseline=baseline, candidate=candidate)

    def test_self_hash_and_replay_validators_reject_mutation(self) -> None:
        labels = self.labels((1, 0), lengths=(2,))
        prediction = self.prediction((True, False), lengths=(2,))
        result = evaluate_common_timeline_v1(contract=self.contract, protocol=self.protocol, file_series=self.file_series((2,)), prediction=prediction, labels=labels)
        comparison = compare_common_results_v1(contract=self.contract, protocol=self.protocol, baseline=result, candidate=result)
        bundle = aggregate_synthetic_common_evaluation_v1(contract=self.contract, protocol=self.protocol, results=(result,), comparisons=(comparison,))
        validate_validation_v2_document_v1("file_second_series_authority_v1.schema.json", self.file_series((2,)).to_dict())
        validate_validation_v2_document_v1("common_alarm_timeline_v1.schema.json", prediction.to_dict())
        validate_validation_v2_document_v1("label_timeline_v1.schema.json", labels.to_dict())
        validate_validation_v2_document_v1("common_evaluation_result_v1.schema.json", result.to_dict())
        validate_validation_v2_document_v1("common_comparison_result_v1.schema.json", comparison.to_dict())
        self.assertEqual(validate_label_timeline_v1(labels, file_series=self.file_series((2,))), labels.self_hash)
        self.assertEqual(validate_common_evaluation_result_v1(result, contract=self.contract, protocol=self.protocol, file_series=self.file_series((2,)), prediction=prediction, labels=labels), result.self_hash)
        self.assertEqual(validate_common_comparison_result_v1(comparison, contract=self.contract, protocol=self.protocol, baseline=result, candidate=result), comparison.self_hash)
        self.assertEqual(validate_common_evaluation_bundle_v1(bundle, contract=self.contract, protocol=self.protocol, results=(result,), comparisons=(comparison,)), bundle.self_hash)
        with self.assertRaisesRegex(MetricContractError, "ALARM_TIMELINE_SELF_HASH_MISMATCH"):
            validate_common_alarm_timeline_v1(replace(prediction, self_hash=HASH_D), file_series=self.file_series((2,)))
        forged_point = replace(prediction.points[0], alarm=True, native_states=("NO_ALARM",))
        forged_timeline = replace(prediction, points=(forged_point,) + prediction.points[1:], self_hash="")
        forged_timeline = replace(forged_timeline, self_hash=sha256(json.dumps(
            forged_timeline.body_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        ).encode("utf-8")).hexdigest())
        with self.assertRaisesRegex(MetricContractError, "DENSE_BOOLEAN_NATIVE_STATE_MISMATCH"):
            validate_common_alarm_timeline_v1(forged_timeline, file_series=self.file_series((2,)))
        truncated_prediction = replace(prediction, points=prediction.points[:1], self_hash="")
        truncated_prediction = replace(truncated_prediction, self_hash=sha256(json.dumps(
            truncated_prediction.body_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        ).encode("utf-8")).hexdigest())
        with self.assertRaisesRegex(MetricContractError, "ALARM_TIMELINE_FILE_SERIES_COVERAGE_MISMATCH"):
            validate_common_alarm_timeline_v1(truncated_prediction, file_series=self.file_series((2,)))
        truncated_labels = replace(labels, points=labels.points[:1], self_hash="")
        truncated_labels = replace(truncated_labels, self_hash=sha256(json.dumps(
            truncated_labels.body_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        ).encode("utf-8")).hexdigest())
        with self.assertRaisesRegex(MetricContractError, "LABEL_TIMELINE_FILE_SERIES_COVERAGE_MISMATCH"):
            validate_label_timeline_v1(truncated_labels, file_series=self.file_series((2,)))
        with self.assertRaisesRegex(MetricContractError, "EVALUATION_RESULT_REPLAY_MISMATCH"):
            validate_common_evaluation_result_v1(replace(result, normal_false_episodes=99), contract=self.contract, protocol=self.protocol, file_series=self.file_series((2,)), prediction=prediction, labels=labels)
        with self.assertRaisesRegex(MetricContractError, "BUNDLE_RESULT_SELF_HASH_MISMATCH"):
            aggregate_synthetic_common_evaluation_v1(
                contract=self.contract, protocol=self.protocol,
                results=(replace(result, self_hash=HASH_E),),
            )

    def test_tracked_bundle_is_synthetic_only_and_deterministic(self) -> None:
        labels = self.labels((1, 0), lengths=(2,))
        result = evaluate_common_timeline_v1(
            contract=self.contract, protocol=self.protocol, file_series=self.file_series((2,)), prediction=self.prediction((True, False), lengths=(2,)), labels=labels,
        )
        first = aggregate_synthetic_common_evaluation_v1(contract=self.contract, protocol=self.protocol, results=(result,))
        second = aggregate_synthetic_common_evaluation_v1(contract=self.contract, protocol=self.protocol, results=(result,))
        self.assertEqual(first, second)
        self.assertEqual(first.execution_scope, "SYNTHETIC_CONTRACT_ONLY")
        self.assertFalse(first.scientific_eligible)
        validate_validation_v2_document_v1("common_evaluation_bundle_v1.schema.json", first.to_dict())


if __name__ == "__main__":
    unittest.main()
