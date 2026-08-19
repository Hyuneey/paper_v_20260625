from __future__ import annotations

import inspect
import json
from pathlib import Path
import unittest

from paperworks.v6.task039e3_r2r_utility_protocol_v3 import (
    ApplicableRuleEvaluationOpportunityRecordV3,
    ApplicableRuleEvaluationOpportunityV3,
    FullCensusEnumerationV3,
    OpportunityCustodyV3,
    RetainedSourceEventV3,
    TargetEvaluationOutcomeV3,
    UTILITY_OPPORTUNITY_SAMPLING_POLICY,
    UTILITY_SOURCE_UNIVERSE_V3,
    UtilityProtocolV3Error,
    abstention_rate_from_custody_v3,
    accepted_relation_binding_v3,
    build_opportunity_custody_v3,
    derive_retained_source_events_v3,
    enumerate_full_census_from_timeline_v3,
    executable_authority_v3,
    no_rule_diagnostic_v3,
    opportunity_record_v3,
)


ROOT = Path(__file__).resolve().parents[1]
H = "a" * 64
J = "b" * 64


def load(name: str) -> dict[str, object]:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


class OpportunityCustodyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.authority = executable_authority_v3(
            load("docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_EXECUTABLE_EQUIVALENCE.json")
        )
        cls.relation_hashes = tuple(sorted(cls.authority.signatures_by_relation))
        cls.common_relations = tuple(
            accepted_relation_binding_v3(cls.authority, relation, "COMMON-42")
            for relation in cls.relation_hashes
        )

    def _enumeration(self, count: int = 5) -> FullCensusEnumerationV3:
        opportunities = tuple(
            sorted(
                (
                    ApplicableRuleEvaluationOpportunityV3(
                        relation.relation_binding_hash,
                        relation.executable_signature_hash,
                        relation.portfolio_identity,
                        "hai-test1.csv",
                        relation.source,
                        relation.target,
                        100 + index,
                        relation.selected_horizon_seconds,
                    )
                    for index, relation in enumerate(self.common_relations[:count])
                ),
                key=lambda item: item.logical_key,
            )
        )
        return FullCensusEnumerationV3(
            opportunities,
            self.relation_hashes,
            (),
            "COMMON-42",
            "hai-test1.csv",
            54_000,
            H,
        )

    def _custody(self) -> OpportunityCustodyV3:
        enumeration = self._enumeration()
        outcomes = (
            TargetEvaluationOutcomeV3("evaluated_expected_response", enumeration.opportunities[0].source_event_physical_index + enumeration.opportunities[0].selected_horizon_seconds + 2, False, None),
            TargetEvaluationOutcomeV3("evaluated_anomaly", enumeration.opportunities[1].source_event_physical_index + enumeration.opportunities[1].selected_horizon_seconds + 2, True, None),
            TargetEvaluationOutcomeV3("evaluated_expected_response", enumeration.opportunities[2].source_event_physical_index + enumeration.opportunities[2].selected_horizon_seconds + 2, False, None),
            TargetEvaluationOutcomeV3("abstain", None, False, "file_boundary"),
            TargetEvaluationOutcomeV3("abstain", None, False, "split_boundary"),
        )
        records = tuple(
            opportunity_record_v3(opportunity, outcome)
            for opportunity, outcome in zip(enumeration.opportunities, outcomes, strict=True)
        )
        return build_opportunity_custody_v3(
            enumeration=enumeration,
            records=records,
            split_identity="30a7c88d6e0af5c37493237cc83b9520cbcd6f43c2dee7bb50ec3cac2668e7d0",
            source_event_policy_hash=H,
            target_evaluation_policy_hash=J,
        )

    def test_five_records_derive_two_over_five(self) -> None:
        custody = self._custody()
        self.assertEqual(custody.record_count, 5)
        self.assertEqual(custody.evaluated_count, 3)
        self.assertEqual(custody.abstained_count, 2)
        self.assertEqual(custody.anomaly_count, 1)
        self.assertEqual(custody.expected_response_count, 2)
        result = abstention_rate_from_custody_v3(custody)
        self.assertEqual(result["numerator"], 2)
        self.assertEqual(result["denominator"], 5)
        self.assertEqual(result["value"], 0.4)
        self.assertEqual(result["opportunity_custody_hash"], custody.artifact_hash)
        self.assertFalse(result["no_rule_cells_included"])
        self.assertFalse(result["source_not_formed_included"])

    def test_free_count_path_is_absent(self) -> None:
        signature = inspect.signature(abstention_rate_from_custody_v3)
        self.assertEqual(tuple(signature.parameters), ("custody",))
        with self.assertRaises(TypeError):
            abstention_rate_from_custody_v3(1, 999)  # type: ignore[call-arg]

    def test_zero_opportunity_is_na_not_zero(self) -> None:
        enumeration = self._enumeration(0)
        custody = build_opportunity_custody_v3(
            enumeration=enumeration,
            records=(),
            split_identity="30a7c88d6e0af5c37493237cc83b9520cbcd6f43c2dee7bb50ec3cac2668e7d0",
            source_event_policy_hash=H,
            target_evaluation_policy_hash=J,
        )
        result = abstention_rate_from_custody_v3(custody)
        self.assertIsNone(result["value"])
        self.assertFalse(result["defined"])
        self.assertEqual(result["undefined_reason"], "no_applicable_opportunities")

    def test_custody_roundtrip_and_summary_tampering_reject(self) -> None:
        custody = self._custody()
        document = custody.to_dict()
        self.assertEqual(OpportunityCustodyV3.from_mapping(document), custody)
        for key in ("record_count", "abstained_count", "evaluated_count", "anomaly_count", "expected_response_count"):
            changed = {**document, key: document[key] + 1}
            with self.subTest(key=key), self.assertRaises(UtilityProtocolV3Error):
                OpportunityCustodyV3.from_mapping(changed)

    def test_record_removal_duplicate_state_and_id_tampering_reject(self) -> None:
        document = self._custody().to_dict()
        mutations = []
        removed = dict(document)
        removed["records"] = document["records"][:-1]
        mutations.append(removed)
        duplicate = dict(document)
        duplicate["records"] = [*document["records"], document["records"][0]]
        mutations.append(duplicate)
        changed_state = json.loads(json.dumps(document))
        changed_state["records"][0]["target_evaluation_state"] = "abstain"
        mutations.append(changed_state)
        changed_id = json.loads(json.dumps(document))
        changed_id["records"][0]["opportunity_id"] = "f" * 64
        mutations.append(changed_id)
        for index, mutation in enumerate(mutations):
            with self.subTest(index=index), self.assertRaises(UtilityProtocolV3Error):
                OpportunityCustodyV3.from_mapping(mutation)

    def test_terminal_records_must_exactly_cover_enumeration(self) -> None:
        custody = self._custody()
        enumeration = self._enumeration()
        with self.assertRaises(UtilityProtocolV3Error):
            build_opportunity_custody_v3(
                enumeration=enumeration,
                records=custody.records[:-1],
                split_identity=custody.split_identity,
                source_event_policy_hash=H,
                target_evaluation_policy_hash=J,
            )

    def test_no_rule_pseudo_opportunity_rejects(self) -> None:
        accepted = self.relation_hashes[:39]
        no_rule = self.relation_hashes[39:]
        relation = accepted_relation_binding_v3(self.authority, no_rule[0], "T2")
        opportunity = ApplicableRuleEvaluationOpportunityV3(
            relation.relation_binding_hash,
            relation.executable_signature_hash,
            "T2",
            "hai-test1.csv",
            relation.source,
            relation.target,
            100,
            relation.selected_horizon_seconds,
        )
        record = opportunity_record_v3(
            opportunity,
            TargetEvaluationOutcomeV3("abstain", None, False, "file_boundary"),
        )
        with self.assertRaises(UtilityProtocolV3Error):
            OpportunityCustodyV3(
                (record,), accepted, no_rule, "T2",
                "30a7c88d6e0af5c37493237cc83b9520cbcd6f43c2dee7bb50ec3cac2668e7d0",
                "hai-test1.csv", H, J, H,
            )
        self.assertEqual(no_rule_diagnostic_v3()["opportunity_records"], 0)

    def test_full_census_known_timeline_has_no_count_override(self) -> None:
        row_count = 54_000
        step_source = self.common_relations[0].source
        series = {
            source: tuple([0.0] * row_count)
            for source in UTILITY_SOURCE_UNIVERSE_V3
        }
        series[step_source] = tuple([0.0] * 100 + [2.0] * (row_count - 100))
        thresholds = {source: 0.5 for source in UTILITY_SOURCE_UNIVERSE_V3}
        tolerances = {source: 0.0 for source in UTILITY_SOURCE_UNIVERSE_V3}
        retained = derive_retained_source_events_v3(series, thresholds, tolerances)
        self.assertEqual(len(retained[step_source]), 1)
        event = retained[step_source][0]
        expected = sum(
            relation.source == step_source
            and relation.expected_source_direction == event.direction
            for relation in self.common_relations
        )
        enumeration = enumerate_full_census_from_timeline_v3(
            accepted_relations=self.common_relations,
            no_rule_relation_binding_hashes=(),
            source_series_by_source=series,
            source_step_thresholds=thresholds,
            source_stability_tolerances=tolerances,
            authority=self.authority,
            file_identity="hai-test1.csv",
            physical_row_count=row_count,
        )
        self.assertEqual(len(enumeration.opportunities), expected)
        self.assertEqual(UTILITY_OPPORTUNITY_SAMPLING_POLICY, "FULL_CENSUS_NO_FIXED_SAMPLE_SIZE")
        self.assertNotIn("sample_size", inspect.signature(enumerate_full_census_from_timeline_v3).parameters)
        self.assertNotIn("opportunity_count", inspect.signature(enumerate_full_census_from_timeline_v3).parameters)


if __name__ == "__main__":
    unittest.main()
