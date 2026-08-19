from __future__ import annotations

import copy
import inspect
import json
import math
from pathlib import Path
import statistics
import unittest

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_r2r_utility_protocol_v3 import (
    ApplicableRuleEvaluationOpportunityRecordV3,
    ApplicableRuleEvaluationOpportunityV3,
    FullCensusEnumerationV3,
    OpportunityCustodyV3,
    TargetEvaluationOutcomeV3,
    UTILITY_OPPORTUNITY_SAMPLING_POLICY,
    UTILITY_SOURCE_UNIVERSE_V3,
    UtilityProtocolV3Error,
    abstention_rate_from_custody_v3,
    accepted_relation_binding_v3,
    build_opportunity_custody_v3,
    enumerate_full_census_from_timeline_v3,
    executable_authority_v3,
    no_rule_diagnostic_v3,
    opportunity_record_v3,
)


ROOT = Path(__file__).resolve().parents[1]
EQUIVALENCE_PATH = ROOT / "docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_EXECUTABLE_EQUIVALENCE.json"
V3_SOURCE_PATH = ROOT / "src/paperworks/v6/task039e3_r2r_utility_protocol_v3.py"
OPPORTUNITY_POLICY_PATH = ROOT / "docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_V3_OPPORTUNITY_POLICY.json"
INNER_SPLIT = "30a7c88d6e0af5c37493237cc83b9520cbcd6f43c2dee7bb50ec3cac2668e7d0"
ROW_COUNT = 54_000
H = "a" * 64
J = "b" * 64


def load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def independent_step_series(events: list[tuple[int, float]]) -> tuple[float, ...]:
    changes = dict(events)
    level = 0.0
    values: list[float] = []
    for index in range(ROW_COUNT):
        level += changes.get(index, 0.0)
        values.append(float(level))
    return tuple(values)


def independent_scan_and_cluster(
    series: tuple[float, ...], threshold: float, tolerance: float
) -> tuple[tuple[int, str, float], ...]:
    """Audit oracle derived from the frozen 5/5, .8, gap<=10 policy."""

    candidates: list[tuple[int, str, float]] = []
    for index in range(5, len(series) - 4):
        pre = series[index - 5:index]
        post = series[index:index + 5]
        pre_level = float(statistics.median(pre))
        post_level = float(statistics.median(post))
        amplitude = post_level - pre_level
        pre_fraction = sum(abs(value - pre_level) <= tolerance for value in pre) / 5
        post_fraction = sum(abs(value - post_level) <= tolerance for value in post) / 5
        if (
            amplitude != 0
            and abs(amplitude) >= threshold
            and pre_fraction >= 0.8
            and post_fraction >= 0.8
        ):
            candidates.append(
                (index, "step_up" if amplitude > 0 else "step_down", amplitude)
            )

    clusters: list[list[tuple[int, str, float]]] = []
    for candidate in candidates:
        if not clusters or candidate[0] - clusters[-1][-1][0] > 10:
            clusters.append([candidate])
        else:
            clusters[-1].append(candidate)
    return tuple(
        min(cluster, key=lambda item: (-abs(item[2]), item[0]))
        for cluster in clusters
    )


def independent_isolated(
    source: str,
    index: int,
    retained: dict[str, tuple[tuple[int, str, float], ...]],
) -> bool:
    return not any(
        abs(index - other[0]) <= 2
        for other_source, events in retained.items()
        if other_source != source
        for other in events
    )


def independent_opportunity_id(
    relation_hash: str,
    signature_hash: str,
    portfolio: str,
    file_identity: str,
    event_index: int,
    horizon: int,
) -> str:
    return stable_hash_v1(
        {
            "executable_signature_hash": signature_hash,
            "file_identity": file_identity,
            "portfolio_identity": portfolio,
            "relation_binding_hash": relation_hash,
            "selected_horizon_seconds": horizon,
            "source_event_physical_index": event_index,
        }
    )


class IndependentOpportunityAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.equivalence = load(EQUIVALENCE_PATH)
        cls.authority = executable_authority_v3(cls.equivalence)
        cls.relation_records = tuple(cls.equivalence["relation_records"])
        cls.relation_hashes = tuple(
            sorted(record["relation_binding_hash"] for record in cls.relation_records)
        )
        cls.common_relations = tuple(
            accepted_relation_binding_v3(cls.authority, relation, "COMMON-42")
            for relation in cls.relation_hashes
        )

    def _timeline(self) -> dict[str, tuple[float, ...]]:
        events = {
            "P1_FCV01D": [(100, 2.0), (106, 3.0), (200, -4.0)],
            "P1_FCV01Z": [(107, 4.0)],
            "P1_FCV02D": [(300, 2.0)],
            "P1_FCV03D": [(303, 2.0)],
            "P1_FCV03Z": [(400, -2.0)],
            "P1_LCV01D": [(500, 2.0), (506, -5.0)],
            "P1_LCV01Z": [(600, 2.0)],
            "P1_PCV01D": [(602, 2.0)],
            "P1_PCV01Z": [(700, -2.0)],
        }
        return {
            source: independent_step_series(events.get(source, []))
            for source in UTILITY_SOURCE_UNIVERSE_V3
        }

    def _independent_expected(self) -> tuple[set[tuple[object, ...]], dict[str, object]]:
        timeline = self._timeline()
        retained = {
            source: independent_scan_and_cluster(timeline[source], 0.5, 0.0)
            for source in UTILITY_SOURCE_UNIVERSE_V3
        }
        expected: set[tuple[object, ...]] = set()
        for record in self.relation_records:
            signature = record["executable_signature"]
            source = signature["source"]
            for event_index, direction, _amplitude in retained[source]:
                if direction != signature["source_step_direction"]:
                    continue
                if not independent_isolated(source, event_index, retained):
                    continue
                expected.add(
                    (
                        record["relation_binding_hash"],
                        record["semantic_execution_hash"],
                        "COMMON-42",
                        "hai-test1.csv",
                        source,
                        signature["target"],
                        event_index,
                        signature["selected_delay_horizon_seconds"],
                    )
                )
        diagnostics = {
            "raw_retained_by_source": {
                source: tuple((event[0], event[1]) for event in retained[source])
                for source in UTILITY_SOURCE_UNIVERSE_V3
            },
            "expected_count": len(expected),
        }
        return expected, diagnostics

    def _observed_enumeration(self) -> FullCensusEnumerationV3:
        return enumerate_full_census_from_timeline_v3(
            accepted_relations=self.common_relations,
            no_rule_relation_binding_hashes=(),
            source_series_by_source=self._timeline(),
            source_step_thresholds={source: 0.5 for source in UTILITY_SOURCE_UNIVERSE_V3},
            source_stability_tolerances={source: 0.0 for source in UTILITY_SOURCE_UNIVERSE_V3},
            authority=self.authority,
            file_identity="hai-test1.csv",
            physical_row_count=ROW_COUNT,
        )

    def _five_record_custody(self) -> OpportunityCustodyV3:
        opportunities = tuple(
            sorted(
                (
                    ApplicableRuleEvaluationOpportunityV3(
                        relation.relation_binding_hash,
                        relation.executable_signature_hash,
                        "COMMON-42",
                        "hai-test1.csv",
                        relation.source,
                        relation.target,
                        1000 + index,
                        relation.selected_horizon_seconds,
                    )
                    for index, relation in enumerate(self.common_relations[:5])
                ),
                key=lambda value: value.logical_key,
            )
        )
        enumeration = FullCensusEnumerationV3(
            opportunities,
            self.relation_hashes,
            (),
            "COMMON-42",
            "hai-test1.csv",
            ROW_COUNT,
            H,
        )
        states = (
            "evaluated_expected_response",
            "evaluated_anomaly",
            "evaluated_expected_response",
            "abstain",
            "abstain",
        )
        reasons = (None, None, None, "file_boundary", "split_boundary")
        records = []
        for opportunity, state, reason in zip(opportunities, states, reasons, strict=True):
            evaluated = state != "abstain"
            outcome = TargetEvaluationOutcomeV3(
                state,
                opportunity.source_event_physical_index
                + opportunity.selected_horizon_seconds
                + 2
                if evaluated
                else None,
                state == "evaluated_anomaly",
                reason,
            )
            records.append(opportunity_record_v3(opportunity, outcome))
        return build_opportunity_custody_v3(
            enumeration=enumeration,
            records=tuple(records),
            split_identity=INNER_SPLIT,
            source_event_policy_hash=H,
            target_evaluation_policy_hash=J,
        )

    def test_full_census_matches_independent_oracle_exactly(self) -> None:
        expected, diagnostics = self._independent_expected()
        observed = self._observed_enumeration()
        observed_keys = {item.logical_key for item in observed.opportunities}
        self.assertEqual(diagnostics["expected_count"], 14)
        self.assertEqual(len(observed.opportunities), 14)
        self.assertEqual(observed_keys, expected)
        self.assertNotIn(100, {key[6] for key in expected})
        self.assertNotIn(106, {key[6] for key in expected})
        self.assertNotIn(107, {key[6] for key in expected})
        self.assertNotIn(500, {key[6] for key in expected})
        self.assertNotIn(600, {key[6] for key in expected})
        self.assertNotIn(602, {key[6] for key in expected})

    def test_opportunity_ids_match_independent_preimages(self) -> None:
        observed = self._observed_enumeration()
        for item in observed.opportunities:
            expected = independent_opportunity_id(
                item.relation_binding_hash,
                item.executable_signature_hash,
                item.portfolio_identity,
                item.file_identity,
                item.source_event_physical_index,
                item.selected_horizon_seconds,
            )
            self.assertEqual(item.opportunity_id, expected)

    def test_identity_mutations_change_identity_or_fail_closed(self) -> None:
        item = self._observed_enumeration().opportunities[0]
        baseline = item.opportunity_id
        fields = {
            "relation_binding_hash": "c" * 64,
            "executable_signature_hash": "d" * 64,
            "file_identity": "hai-test2.csv",
            "source_event_physical_index": item.source_event_physical_index + 1,
            "selected_horizon_seconds": 5 if item.selected_horizon_seconds != 5 else 10,
        }
        values = {
            "relation_binding_hash": item.relation_binding_hash,
            "executable_signature_hash": item.executable_signature_hash,
            "portfolio_identity": item.portfolio_identity,
            "file_identity": item.file_identity,
            "source": item.source,
            "target": item.target,
            "source_event_physical_index": item.source_event_physical_index,
            "selected_horizon_seconds": item.selected_horizon_seconds,
        }
        for field, replacement in fields.items():
            changed = {**values, field: replacement}
            with self.subTest(field=field):
                try:
                    mutated = ApplicableRuleEvaluationOpportunityV3(**changed)
                except UtilityProtocolV3Error:
                    continue
                self.assertNotEqual(mutated.opportunity_id, baseline)

    def test_duplicate_ids_and_logical_keys_reject(self) -> None:
        observed = self._observed_enumeration()
        duplicated = tuple((*observed.opportunities, observed.opportunities[0]))
        with self.assertRaises(UtilityProtocolV3Error):
            FullCensusEnumerationV3(
                duplicated,
                observed.accepted_relation_binding_hashes,
                observed.no_rule_relation_binding_hashes,
                observed.portfolio_identity,
                observed.file_identity,
                observed.physical_row_count,
                observed.retained_source_event_census_hash,
            )

    def test_no_fixed_sample_size_or_count_override(self) -> None:
        self.assertEqual(UTILITY_OPPORTUNITY_SAMPLING_POLICY, "FULL_CENSUS_NO_FIXED_SAMPLE_SIZE")
        enumeration_signature = inspect.signature(enumerate_full_census_from_timeline_v3)
        for name in (
            "sample_size",
            "max_opportunities",
            "desired_opportunities",
            "opportunity_denominator",
            "manual_denominator",
            "abstention_denominator_override",
        ):
            self.assertNotIn(name, enumeration_signature.parameters)
        source = V3_SOURCE_PATH.read_text(encoding="utf-8")
        self.assertNotIn("abstention_rate_v2", source)
        policy = load(OPPORTUNITY_POLICY_PATH)
        self.assertIsNone(policy["fixed_sample_size"])
        self.assertFalse(policy["caller_count_override"])

    def test_custody_counts_and_abstention_metric_are_record_derived(self) -> None:
        custody = self._five_record_custody()
        independent_states = tuple(record.target_evaluation_state for record in custody.records)
        independent_abstained = sum(state == "abstain" for state in independent_states)
        independent_evaluated = sum(state != "abstain" for state in independent_states)
        independent_anomalies = sum(state == "evaluated_anomaly" for state in independent_states)
        independent_expected = sum(
            state == "evaluated_expected_response" for state in independent_states
        )
        self.assertEqual((len(independent_states), independent_evaluated, independent_abstained), (5, 3, 2))
        self.assertEqual(independent_evaluated, independent_anomalies + independent_expected)
        self.assertEqual(custody.record_count, 5)
        self.assertEqual(custody.evaluated_count, 3)
        self.assertEqual(custody.abstained_count, 2)
        self.assertEqual(OpportunityCustodyV3.from_mapping(custody.to_dict()), custody)
        signature = inspect.signature(abstention_rate_from_custody_v3)
        self.assertEqual(tuple(signature.parameters), ("custody",))
        metric = abstention_rate_from_custody_v3(custody)
        self.assertEqual((metric["numerator"], metric["denominator"], metric["value"]), (2, 5, 0.4))
        with self.assertRaises(TypeError):
            abstention_rate_from_custody_v3(1, 999)  # type: ignore[call-arg]

    def test_all_required_custody_mutations_fail_closed(self) -> None:
        custody = self._five_record_custody()
        document = custody.to_dict()
        mutations: list[dict[str, object]] = []
        for field in (
            "record_count",
            "evaluated_count",
            "abstained_count",
            "anomaly_count",
            "expected_response_count",
        ):
            changed = copy.deepcopy(document)
            changed[field] += 1
            mutations.append(changed)
        changed = copy.deepcopy(document)
        changed["records"][0]["record_hash"] = "c" * 64
        mutations.append(changed)
        changed = copy.deepcopy(document)
        changed["records"][0]["opportunity_id"] = "d" * 64
        mutations.append(changed)
        changed = copy.deepcopy(document)
        changed["records"][0]["target_evaluation_state"] = "abstain"
        mutations.append(changed)
        changed = copy.deepcopy(document)
        changed["records"] = changed["records"][:-1]
        mutations.append(changed)
        changed = copy.deepcopy(document)
        changed["records"].append(copy.deepcopy(changed["records"][0]))
        mutations.append(changed)
        changed = copy.deepcopy(document)
        changed["records"][0]["relation_binding_hash"] = self.relation_hashes[-1]
        mutations.append(changed)
        changed = copy.deepcopy(document)
        changed["records"][0]["relation_binding_hash"] = "e" * 64
        mutations.append(changed)
        changed = copy.deepcopy(document)
        changed["file_identity"] = "hai-test2.csv"
        mutations.append(changed)
        changed = copy.deepcopy(document)
        changed["split_identity"] = "9d76358ff109e4a6d2a712a1ff679c199d08e9cc92239160c8016e9efa063203"
        mutations.append(changed)
        changed = copy.deepcopy(document)
        changed["retained_source_event_census_hash"] = "f" * 64
        mutations.append(changed)
        self.assertEqual(len(mutations), 15)
        for index, mutation in enumerate(mutations):
            with self.subTest(mutation=index), self.assertRaises(UtilityProtocolV3Error):
                OpportunityCustodyV3.from_mapping(mutation)

    def test_no_rule_is_diagnostic_only_and_excluded_from_custody(self) -> None:
        diagnostic = no_rule_diagnostic_v3()
        self.assertEqual(
            (
                diagnostic["interpreter_instances"],
                diagnostic["opportunity_records"],
                diagnostic["alarms"],
                diagnostic["abstentions"],
            ),
            (0, 0, 0, 0),
        )
        self.assertTrue(diagnostic["construction_coverage_denominator_membership"])
        self.assertFalse(diagnostic["substitution_allowed"])
        custody = self._five_record_custody()
        metric = abstention_rate_from_custody_v3(custody)
        self.assertFalse(metric["no_rule_cells_included"])
        self.assertFalse(metric["source_not_formed_included"])

    def test_foreign_no_rule_relation_fails_closed(self) -> None:
        """Independent oracle: the frozen 42-relation union cannot include a foreign hash."""

        accepted = self.relation_hashes[:39]
        no_rule_with_foreign = tuple(sorted((*self.relation_hashes[39:41], "f" * 64)))
        with self.assertRaises(UtilityProtocolV3Error):
            FullCensusEnumerationV3(
                (),
                accepted,
                no_rule_with_foreign,
                "T2",
                "hai-test1.csv",
                ROW_COUNT,
                H,
            )

    def test_record_target_must_match_bound_executable_signature(self) -> None:
        custody = self._five_record_custody()
        original = custody.records[0]
        alternate_target = next(
            value
            for value in {item.target for item in self.common_relations}
            if value != original.target
        )
        mutated = ApplicableRuleEvaluationOpportunityRecordV3(
            original.opportunity_id,
            original.relation_binding_hash,
            original.executable_signature_hash,
            original.portfolio_identity,
            original.file_identity,
            original.source,
            alternate_target,
            original.source_event_physical_index,
            original.selected_horizon_seconds,
            original.target_evaluation_state,
            original.decision_index,
            original.alarm_emitted,
            original.abstention_reason,
        )
        records = (mutated, *custody.records[1:])
        enumeration = FullCensusEnumerationV3(
            tuple(
                ApplicableRuleEvaluationOpportunityV3(
                    item.relation_binding_hash,
                    item.executable_signature_hash,
                    item.portfolio_identity,
                    item.file_identity,
                    item.source,
                    original.target if index == 0 else item.target,
                    item.source_event_physical_index,
                    item.selected_horizon_seconds,
                )
                for index, item in enumerate(custody.records)
            ),
            custody.accepted_relation_binding_hashes,
            custody.no_rule_relation_binding_hashes,
            custody.portfolio_identity,
            custody.file_identity,
            ROW_COUNT,
            custody.retained_source_event_census_hash,
        )
        with self.assertRaises(UtilityProtocolV3Error):
            build_opportunity_custody_v3(
                enumeration=enumeration,
                records=records,
                split_identity=INNER_SPLIT,
                source_event_policy_hash=H,
                target_evaluation_policy_hash=J,
            )

    def test_caller_thresholds_cannot_change_bound_census(self) -> None:
        low = self._observed_enumeration()
        high = enumerate_full_census_from_timeline_v3(
            accepted_relations=self.common_relations,
            no_rule_relation_binding_hashes=(),
            source_series_by_source=self._timeline(),
            source_step_thresholds={source: 10.0 for source in UTILITY_SOURCE_UNIVERSE_V3},
            source_stability_tolerances={source: 0.0 for source in UTILITY_SOURCE_UNIVERSE_V3},
            authority=self.authority,
            file_identity="hai-test1.csv",
            physical_row_count=ROW_COUNT,
        )
        self.assertEqual(len(low.opportunities), len(high.opportunities))

    def test_directly_fabricated_census_cannot_become_metric_custody(self) -> None:
        fabricated = FullCensusEnumerationV3(
            (), self.relation_hashes, (), "COMMON-42", "hai-test1.csv", ROW_COUNT, H
        )
        with self.assertRaises(UtilityProtocolV3Error):
            build_opportunity_custody_v3(
                enumeration=fabricated,
                records=(),
                split_identity=INNER_SPLIT,
                source_event_policy_hash=H,
                target_evaluation_policy_hash=J,
            )


if __name__ == "__main__":
    unittest.main()
