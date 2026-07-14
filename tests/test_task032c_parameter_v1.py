from __future__ import annotations

import dataclasses
import json
import unittest
from pathlib import Path

from paperworks.contracts import (
    ParameterV1ModelError,
    calibration_parameter_to_dict,
    canonical_calibration_parameter_sha256,
    load_calibration_parameter,
    parse_calibration_parameter,
    with_computed_artifact_hash,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "fixtures/task032c"
PARAMETERS = ("parameter_lag_maximum.json", "parameter_tolerance.json", "parameter_duration.json", "parameter_support.json")


def parameter_document(name: str = "parameter_lag_maximum.json") -> dict:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


class Task032CParameterV1Tests(unittest.TestCase):
    def test_all_supported_parameter_fixtures_parse(self) -> None:
        expected = {"lag_maximum", "tolerance", "persistence_duration", "minimum_support"}
        observed = set()
        for name in PARAMETERS:
            parameter = load_calibration_parameter(FIXTURE_ROOT / name)
            observed.add(parameter.parameter_role)
            self.assertEqual(calibration_parameter_to_dict(parameter), parameter_document(name))
            self.assertEqual(canonical_calibration_parameter_sha256(parameter), parameter.artifact_hash)
            self.assertFalse(parameter.runtime_authorized)
            with self.assertRaises(dataclasses.FrozenInstanceError):
                parameter.value = 0  # type: ignore[misc]
        self.assertEqual(observed, expected)

    def test_unsupported_role_and_prefix_fail(self) -> None:
        role = parameter_document(); role["parameter_role"] = "baseline_level"
        prefix = parameter_document(); prefix["parameter_id"] = "PARAM-RATE-032"
        for document, code in ((role, "PARAMETER_V1_UNSUPPORTED_ROLE"), (prefix, "PARAMETER_V1_UNSUPPORTED_PREFIX")):
            with self.subTest(code=code), self.assertRaises(ParameterV1ModelError) as caught:
                parse_calibration_parameter(with_computed_artifact_hash(document))
            self.assertEqual(caught.exception.issue_code, code)

    def test_confidence_support_and_cardinality_fail(self) -> None:
        interval = parameter_document(); interval["confidence_interval"].update(lower=7, upper=6)
        support = parameter_document(); support["sample_support"].update(event_count=4, matched_count=5)
        cardinality = parameter_document(); cardinality["source_variables"].append("ActuatorC")
        for document, code in ((interval, "PARAMETER_V1_CONFIDENCE_ORDER"), (support, "PARAMETER_V1_SUPPORT_COUNTS"), (cardinality, "PARAMETER_V1_CARDINALITY")):
            with self.subTest(code=code), self.assertRaises(ParameterV1ModelError) as caught:
                parse_calibration_parameter(with_computed_artifact_hash(document))
            self.assertEqual(caught.exception.issue_code, code)

    def test_approval_and_stability_consistency(self) -> None:
        missing = parameter_document(); missing["approved_by"] = None; missing["approval_date"] = None
        with self.assertRaises(ParameterV1ModelError) as caught:
            parse_calibration_parameter(with_computed_artifact_hash(missing))
        self.assertEqual(caught.exception.issue_code, "PARAMETER_V1_APPROVER_MISSING")
        unstable = parameter_document("parameter_tolerance.json"); unstable["stability_summary"]["status"] = "unstable"
        with self.assertRaises(ParameterV1ModelError) as caught:
            parse_calibration_parameter(with_computed_artifact_hash(unstable))
        self.assertEqual(caught.exception.issue_code, "PARAMETER_V1_STATUS_STABILITY")


if __name__ == "__main__":
    unittest.main()
