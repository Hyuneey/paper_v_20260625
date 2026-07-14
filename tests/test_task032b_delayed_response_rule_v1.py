from __future__ import annotations

import copy
import dataclasses
import json
import unittest
from pathlib import Path

from paperworks.contracts import (
    DelayedResponseRuleV1,
    RuleV1ModelError,
    assess_legacy_artifact_file,
    canonical_rule_document_bytes,
    canonical_rule_document_sha256,
    delayed_response_rule_to_dict,
    load_delayed_response_rule,
    load_schema_registry,
    parse_delayed_response_rule,
    serialize_delayed_response_rule,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = REPO_ROOT / "fixtures/task032b"
FIXTURES = (
    "delayed_response_candidate.json",
    "delayed_response_fixed_lag.json",
    "delayed_response_interval_lag.json",
)


def read_fixture(name: str = "delayed_response_candidate.json") -> dict:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


def assert_model_error(test: unittest.TestCase, document: dict, expected_code: str) -> RuleV1ModelError:
    with test.assertRaises(RuleV1ModelError) as caught:
        parse_delayed_response_rule(document)
    test.assertEqual(caught.exception.issue_code, expected_code)
    test.assertRegex(caught.exception.structural_report_hash, r"^[a-f0-9]{64}$")
    return caught.exception


class Task032BDelayedResponseRuleV1Tests(unittest.TestCase):
    def test_all_fixtures_are_structurally_valid_and_typed(self) -> None:
        registry = load_schema_registry()
        for name in FIXTURES:
            document = read_fixture(name)
            self.assertEqual(registry.validate_artifact("rule_dsl", document).status, "valid")
            rule = parse_delayed_response_rule(document, registry=registry)
            self.assertIsInstance(rule, DelayedResponseRuleV1)
            self.assertTrue(dataclasses.is_dataclass(rule))
            self.assertEqual(rule.relation_type, "delayed_response")
            self.assertFalse(rule.runtime_authorized)
            with self.assertRaises(dataclasses.FrozenInstanceError):
                rule.status = "accepted"  # type: ignore[misc]

    def test_round_trip_preserves_all_schema_information(self) -> None:
        for name in FIXTURES:
            source = read_fixture(name)
            first = parse_delayed_response_rule(source)
            dictionary = delayed_response_rule_to_dict(first)
            second = parse_delayed_response_rule(json.loads(serialize_delayed_response_rule(first)))
            self.assertEqual(dictionary, source)
            self.assertEqual(first, second)
            self.assertNotIn("runtime_authorized", dictionary)

    def test_canonical_bytes_and_document_hash_are_stable(self) -> None:
        rule = load_delayed_response_rule(FIXTURE_ROOT / FIXTURES[0])
        first_bytes = canonical_rule_document_bytes(rule)
        second_bytes = canonical_rule_document_bytes(rule)
        self.assertEqual(first_bytes, second_bytes)
        self.assertEqual(first_bytes.decode("utf-8"), serialize_delayed_response_rule(rule))
        self.assertEqual(canonical_rule_document_sha256(rule), canonical_rule_document_sha256(rule))
        self.assertNotEqual(canonical_rule_document_sha256(rule), rule.verified_rule_hash)
        self.assertNotIn(b"NaN", first_bytes)

    def test_input_dictionary_and_file_remain_unchanged(self) -> None:
        document = read_fixture()
        before = copy.deepcopy(document)
        parse_delayed_response_rule(document)
        self.assertEqual(document, before)

        path = FIXTURE_ROOT / FIXTURES[0]
        file_before = path.read_bytes()
        load_delayed_response_rule(path)
        self.assertEqual(path.read_bytes(), file_before)

    def test_unknown_and_executable_fields_fail_structurally(self) -> None:
        for field in ("unknown_property", "python"):
            with self.subTest(field=field):
                document = read_fixture()
                document[field] = "synthetic marker"
                error = assert_model_error(self, document, "RULE_V1_STRUCTURAL_INVALID")
                self.assertIn("SCHEMA_ADDITIONALPROPERTIES", error.message)
                self.assertNotIn("synthetic marker", str(error))

    def test_relation_cardinality_and_self_relation_constraints(self) -> None:
        cases = []
        relation = read_fixture()
        relation["relation_type"] = "persistence"
        cases.append((relation, "RULE_V1_UNSUPPORTED_RELATION"))

        sources = read_fixture()
        sources["source_variables"].append("A2")
        cases.append((sources, "RULE_V1_SOURCE_CARDINALITY"))

        targets = read_fixture()
        targets["target_variables"].append("S2")
        targets["expected_effect"]["target_variables"].append("S2")
        cases.append((targets, "RULE_V1_TARGET_CARDINALITY"))

        self_relation = read_fixture()
        self_relation["target_variables"] = ["A1"]
        self_relation["expected_effect"]["target_variables"] = ["A1"]
        cases.append((self_relation, "RULE_V1_SELF_RELATION"))

        for document, code in cases:
            with self.subTest(code=code):
                assert_model_error(self, document, code)

    def test_trigger_constraints(self) -> None:
        cases = []
        trigger_type = read_fixture()
        trigger_type["trigger"]["trigger_type"] = "state_equals"
        cases.append((trigger_type, "RULE_V1_TRIGGER_TYPE"))

        mismatch = read_fixture()
        mismatch["trigger"]["variable"] = "A2"
        cases.append((mismatch, "RULE_V1_TRIGGER_SOURCE_MISMATCH"))

        missing_state = read_fixture()
        missing_state["trigger"]["state_value"] = None
        cases.append((missing_state, "RULE_V1_TRIGGER_STATE_MISSING"))

        parameterized = read_fixture()
        parameterized["trigger"]["threshold_parameter_ref"] = "PARAM-TOL-101"
        cases.append((parameterized, "RULE_V1_TRIGGER_PARAMETER_REFERENCE"))

        for document, code in cases:
            with self.subTest(code=code):
                assert_model_error(self, document, code)

    def test_expected_effect_constraints(self) -> None:
        cases = []
        effect_type = read_fixture()
        effect_type["expected_effect"]["effect_type"] = "directional_change"
        cases.append((effect_type, "RULE_V1_EFFECT_TYPE"))

        direction = read_fixture()
        direction["expected_effect"]["direction"] = "decrease"
        cases.append((direction, "RULE_V1_EFFECT_DIRECTION"))

        target = read_fixture()
        target["expected_effect"]["target_variables"] = ["S2"]
        cases.append((target, "RULE_V1_EFFECT_TARGET_MISMATCH"))

        for document, code in cases:
            with self.subTest(code=code):
                assert_model_error(self, document, code)

    def test_output_constraints(self) -> None:
        output_type = read_fixture()
        output_type["output_semantics"]["output_type"] = "violation_score"
        assert_model_error(self, output_type, "RULE_V1_OUTPUT_TYPE")

        direction = read_fixture()
        direction["output_semantics"]["violation_direction"] = "excessive_response"
        assert_model_error(self, direction, "RULE_V1_VIOLATION_DIRECTION")

    def test_lag_constraints(self) -> None:
        cases = []
        unsupported = read_fixture()
        unsupported["lag"]["lag_type"] = "calibrated_distribution"
        cases.append((unsupported, "RULE_V1_LAG_TYPE"))

        order = read_fixture()
        order["lag"]["minimum"] = 6
        order["lag"]["maximum"] = 5
        cases.append((order, "RULE_V1_LAG_ORDER"))

        fixed = read_fixture("delayed_response_fixed_lag.json")
        fixed["lag"]["maximum"] = 4
        cases.append((fixed, "RULE_V1_FIXED_LAG_MISMATCH"))

        interval = read_fixture("delayed_response_interval_lag.json")
        interval["lag"]["maximum"] = interval["lag"]["minimum"]
        cases.append((interval, "RULE_V1_INTERVAL_LAG_EMPTY"))

        for document, code in cases:
            with self.subTest(code=code):
                assert_model_error(self, document, code)

    def test_window_and_persistence_constraints(self) -> None:
        window = read_fixture()
        window["window"]["window_type"] = "rolling"
        assert_model_error(self, window, "RULE_V1_WINDOW_TYPE")

        for enabled, reference in ((True, None), (False, "PARAM-DURATION-101")):
            with self.subTest(enabled=enabled, reference=reference):
                persistence = read_fixture()
                persistence["persistence"]["enabled"] = enabled
                persistence["persistence"]["duration_parameter_ref"] = reference
                assert_model_error(self, persistence, "RULE_V1_PERSISTENCE_REFERENCE")

    def test_parameter_reference_closure_and_support_extension(self) -> None:
        missing = read_fixture()
        missing["parameter_refs"].remove("PARAM-SEVERITY-101")
        assert_model_error(self, missing, "RULE_V1_PARAMETER_REFERENCE_MISSING")

        rule = parse_delayed_response_rule(read_fixture())
        self.assertIn("PARAM-SUPPORT-101", rule.parameter_refs)
        self.assertIn("PARAM-SUPPORT-101", delayed_response_rule_to_dict(rule)["parameter_refs"])

    def test_accepted_status_and_serialized_hash_grant_no_authority(self) -> None:
        document = read_fixture()
        document["status"] = "accepted"
        document["verified_rule_hash"] = "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
        rule = parse_delayed_response_rule(document)
        self.assertEqual(rule.status, "accepted")
        self.assertIsNotNone(rule.verified_rule_hash)
        self.assertFalse(rule.runtime_authorized)
        self.assertNotEqual(canonical_rule_document_sha256(rule), rule.verified_rule_hash)

    def test_task032a_legacy_adapter_still_creates_no_target(self) -> None:
        assessment = assess_legacy_artifact_file(
            REPO_ROOT / "fixtures/task032a/legacy_supported_delayed_response.json"
        )
        self.assertFalse(assessment.target_artifact_created)
        self.assertEqual(assessment.status, "convertible_delayed_response_pending_context")


if __name__ == "__main__":
    unittest.main()
