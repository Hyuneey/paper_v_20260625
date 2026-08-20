from __future__ import annotations

import copy
from dataclasses import replace
import inspect
import json
from pathlib import Path
import unittest

from paperworks.v6 import task039e3_r2r_utility_evaluator_authority_v1 as evaluator_authority
from paperworks.v6 import task039e3_r2r_utility_inner_d1_execution_v1 as bridge
from paperworks.v6 import task039e3_r2r_utility_source_census_supplement_v1 as supplement


ROOT = Path(__file__).resolve().parents[1]
DIFFERENTIAL_CASES = 32
STATIC_INVALID_CASES = 28


def value_for(role: str) -> int | float:
    if role == "source_step_threshold":
        return 1.0
    if role == "source_stability_tolerance":
        return 0.0
    if role == "target_noise_scale":
        return 0.5
    return {
        "source_pre_window_seconds": 5,
        "source_post_window_seconds": 5,
        "minimum_source_stability_fraction": 0.8,
        "source_refractory_seconds": 10,
        "cross_source_isolation_radius_seconds": 2,
        "target_baseline_window_seconds": 5,
        "target_response_window_seconds": 3,
    }[role]


class InnerD1ExecutionBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.authority, cls.bundle = bridge._load_public_authorities_v1()
        cls.main_records = tuple(
            evaluator_authority.SyntheticNumericRecordV1(
                "SYNTHETIC_MAIN_420",
                rule.source,
                rule.relation_binding_hash,
                role,
                reference,
                value_for(role),
            )
            for rule in cls.authority.rule_descriptors
            for role, reference in rule.numeric_reference_bindings
        )
        cls.supplement_records = tuple(
            evaluator_authority.SyntheticNumericRecordV1(
                evaluator_authority.SUPPLEMENT_PURPOSE,
                source,
                None,
                role,
                supplement.supplement_reference_identity_v1(source, role),
                value_for(role),
            )
            for source in evaluator_authority.SUPPLEMENT_SOURCES
            for role in evaluator_authority.SOURCE_CENSUS_ROLES
        )
        cls.rule = cls.authority.rule_descriptors[0]
        cls.other_source = next(
            source
            for source in cls.authority.feature_schema.source_features
            if source != cls.rule.source
        )

    def rows(
        self,
        *,
        length: int = 80,
        event_index: int | None = 20,
        response_delta: float = 0.0,
        other_event_index: int | None = None,
        amplitude: float = 2.0,
    ) -> tuple[tuple[float, ...], ...]:
        ordered = self.authority.feature_schema.union_features
        output: list[tuple[float, ...]] = []
        response_start = (
            event_index + self.rule.selected_horizon_seconds
            if event_index is not None
            else -1
        )
        signed_amplitude = (
            amplitude if self.rule.source_direction == "step_up" else -amplitude
        )
        for index in range(length):
            values = {feature: 0.0 for feature in ordered}
            if event_index is not None and index >= event_index:
                values[self.rule.source] = signed_amplitude
            if other_event_index is not None and index >= other_event_index:
                values[self.other_source] = amplitude
            if (
                event_index is not None
                and response_start <= index < response_start + 3
            ):
                values[self.rule.target] = (
                    response_delta
                    if self.rule.target_direction == "increase"
                    else -response_delta
                )
            output.append(tuple(float(values[feature]) for feature in ordered))
        return tuple(output)

    def test_committed_grant_replays_exact_five_artifact_graph(self) -> None:
        grant = bridge.issue_committed_inner_d1_execution_grant_v1()
        self.assertEqual(
            bridge.validate_committed_inner_d1_execution_grant_v1(grant),
            grant.grant_hash,
        )
        self.assertEqual(grant.authorization_hash, bridge.AUTHORIZATION_HASH)
        self.assertEqual(grant.custody_preflight_hash, bridge.CUSTODY_PREFLIGHT_HASH)
        self.assertEqual(grant.receipt_hash, bridge.RECEIPT_HASH)
        self.assertEqual(grant.authorization_scope, bridge.AUTHORIZATION_SCOPE)
        self.assertTrue(grant.d1_authorized)
        self.assertFalse(grant.d0_authorized)
        self.assertFalse(grant.d2_authorized)
        self.assertFalse(grant.detector_authorized)
        self.assertFalse(grant.outer_authorized)

    def test_grant_reconstruction_copy_replace_and_self_rehash_reject(self) -> None:
        grant = bridge.issue_committed_inner_d1_execution_grant_v1()
        candidates = (
            bridge.CommittedInnerD1ExecutionGrantV1(**grant.__dict__),
            copy.copy(grant),
            copy.deepcopy(grant),
            replace(grant),
            replace(grant, grant_hash="f" * 64),
        )
        for candidate in candidates:
            with self.subTest(candidate=id(candidate)), self.assertRaises(
                bridge.InnerD1ExecutionV1Error
            ):
                bridge.validate_committed_inner_d1_execution_grant_v1(candidate)

    def test_committed_graph_mutations_and_self_rehash_reject_18(self) -> None:
        documents = bridge._load_committed_artifact_set_v1()
        cases: list[tuple[str, str, object]] = [
            ("authorization", "authorization_scope", "OUTER"),
            ("authorization", "d0_authorized", True),
            ("authorization", "d2_authorized", True),
            ("authorization", "detector_authorized", True),
            ("authorization", "outer_authorized", True),
            ("authorization", "test2_authorized", True),
            ("authorization", "common_relation_count", 41),
            ("authorization", "main_private_registry_expected_hash", "a" * 64),
            ("authorization", "supplement_private_registry_expected_hash", "a" * 64),
            ("preflight", "test2_touched", True),
            ("preflight", "scientific_parsing_performed", True),
            ("preflight", "private_paths_exposed", 1),
            ("preflight", "private_numeric_values_exposed", 1),
            ("readiness", "authorization_hash", "a" * 64),
            ("bundle", "preflight_hash", "a" * 64),
            ("receipt", "bundle_hash", "a" * 64),
            ("receipt", "REAL_UTILITY_EXECUTION_AUTHORIZED", True),
            ("receipt", "utility_inner_d1_executed", True),
        ]
        for document_name, key, value in cases:
            mutated = copy.deepcopy(documents)
            mutated[document_name][key] = value
            payload = {
                item: member
                for item, member in mutated[document_name].items()
                if item != "artifact_hash"
            }
            mutated[document_name]["artifact_hash"] = bridge.stable_hash_v1(payload)
            with self.subTest(document=document_name, key=key), self.assertRaises(
                bridge.InnerD1ExecutionV1Error
            ):
                bridge._validate_committed_artifact_set_v1(mutated)

    def test_real_entrypoint_has_no_caller_scientific_knobs_10(self) -> None:
        self.assertEqual(tuple(inspect.signature(bridge.execute_authorized_inner_d1_v1).parameters), ())
        for keyword in (
            "relation_subset",
            "source_subset",
            "threshold",
            "tolerance",
            "target_scale",
            "denominator",
            "test2",
            "d0",
            "d2",
            "detector",
        ):
            with self.subTest(keyword=keyword), self.assertRaises(TypeError):
                bridge.execute_authorized_inner_d1_v1(**{keyword: object()})

    def test_private_resolver_is_redacted_factory_custodied_and_closed(self) -> None:
        resolver = bridge.build_differential_numeric_resolver_v1(
            self.bundle, self.main_records, self.supplement_records
        )
        self.assertEqual(
            bridge.validate_real_private_numeric_resolver_v1(resolver, self.bundle),
            resolver.resolver_identity,
        )
        self.assertEqual(repr(resolver), "<RealPrivateNumericResolverV1 validated=True values=REDACTED>")
        with self.assertRaises(bridge.InnerD1ExecutionV1Error):
            copy.deepcopy(resolver)
        forged = object.__new__(bridge.RealPrivateNumericResolverV1)
        for name in (
            "_bundle",
            "_relation_values",
            "_relation_references",
            "_source_values",
            "resolver_identity",
        ):
            object.__setattr__(forged, name, getattr(resolver, name))
        with self.assertRaises(bridge.InnerD1ExecutionV1Error):
            bridge.validate_real_private_numeric_resolver_v1(forged, self.bundle)

    def test_32_differential_semantic_cases_have_zero_divergence(self) -> None:
        cases = [self.rows(event_index=None)]
        cases.extend(
            self.rows(
                event_index=20 + (index % 3),
                response_delta=(0.0, 0.5, 0.5000001, 1.0)[index % 4],
                amplitude=(1.0, 2.0, 3.0)[index % 3],
                length=80 - (index % 5),
            )
            for index in range(25)
        )
        cases.extend(
            (
                self.rows(other_event_index=22),
                self.rows(other_event_index=23),
                self.rows(event_index=6, length=25),
                self.rows(event_index=20, length=25),
                self.rows(event_index=30, length=40),
                self.rows(event_index=15, response_delta=2.0),
            )
        )
        self.assertEqual(len(cases), DIFFERENTIAL_CASES)
        for index, rows in enumerate(cases):
            with self.subTest(case=index):
                result = bridge.run_differential_equivalence_case_v1(
                    rows, self.main_records, self.supplement_records
                )
                self.assertTrue(result["semantic_equal"])
                self.assertEqual(result["semantic_divergences"], 0)
                self.assertEqual(result["v4_authority_hash"], bridge.V4_AUTHORITY_HASH)

    def test_prediction_records_have_exact_public_allowlist(self) -> None:
        allowed = {
            "opportunity_id",
            "source_event_identity_hash",
            "relation_binding_hash",
            "final_state",
            "alarm_emitted",
            "decision_physical_row_index",
            "numeric_reference_identities",
            "computation_identity",
            "trace_hash",
        }
        result = bridge.RealRuleExecutionResultV1(
            bridge.DIFFERENTIAL_MODE,
            "a" * 64,
            "b" * 64,
            "c" * 64,
            "evaluated_anomaly",
            True,
            10,
            tuple(str(index) for index in range(10)),
            "d" * 64,
            "e" * 64,
        )
        record = result.to_prediction_record()
        self.assertEqual(set(record), allowed)
        serialized = json.dumps(record, sort_keys=True)
        for prohibited in ("label", "attack_event", "threshold_value", "tolerance_value", "noise_scale_value"):
            self.assertNotIn(prohibited, serialized)

    def test_frozen_modules_are_not_named_as_bridge_outputs(self) -> None:
        source = (ROOT / "src/paperworks/v6/task039e3_r2r_utility_inner_d1_execution_v1.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("REAL_UTILITY_EXECUTION_AUTHORIZED = True", source)
        self.assertNotIn("hai-test2.csv", source)
        self.assertNotIn("label-test2.csv", source)
        self.assertEqual(bridge.BRIDGE_SEMANTIC_POLICY["common_relation_count"], 42)
        self.assertFalse(bridge.BRIDGE_SEMANTIC_POLICY["d0_authorized"])
        self.assertFalse(bridge.BRIDGE_SEMANTIC_POLICY["d2_authorized"])


if __name__ == "__main__":
    unittest.main()
