"""Independent authority-custody attacks for Utility Evaluator V1.

Expectations are reconstructed from committed lower public authorities.  No
implementation-test helper or private authority is imported or opened.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import fields, replace
import json
from pathlib import Path
import unittest

from paperworks.v6 import task039e3_r2r_utility_protocol_v4 as v4
from paperworks.v6.task039e3_r2r_utility_evaluator_authority_v1 import (
    EvaluatorAuthorityBundleV1,
    build_evaluator_authority_bundle_v1,
    validate_evaluator_authority_bundle_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_types_v1 import UtilityEvaluatorV1Error
from paperworks.v6.task039e3_r2r_utility_evaluator_v1 import (
    EvaluatorImplementationAuthorityV1,
    build_evaluator_implementation_authority_v1,
    validate_evaluator_implementation_authority_v1,
)


ROOT = Path(__file__).resolve().parents[1]
INDEPENDENT_SEMANTIC_ATTACK_CLASSES = 2
RAW_AUTHORITY_RECONSTRUCTION_ATTACKS = 6
EXPECTED_ACCEPTED_INVALID_CASES = 0


def load_public(relative_path: str) -> dict[str, object]:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def build_lower_v4_authority() -> v4.UtilityProtocolV4CanonicalAuthority:
    authority = v4.build_utility_protocol_v4_canonical_authority(
        executable_equivalence=load_public(
            "docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_EXECUTABLE_EQUIVALENCE.json"
        ),
        evidence_manifest=load_public(
            "docs/task_reports/TASK-039E1_CONSTRUCTION_EVIDENCE_MANIFEST.json"
        ),
        dataset_manifest=load_public("docs/task_reports/TASK-039A_DATASET_MANIFEST_V2.json"),
        csv_structure_report=load_public(
            "docs/task_reports/TASK-039A_CSV_STRUCTURE_REPORT.json"
        ),
        c0_config=load_public("configs/v6/task039c0_candidate_discovery_protocol.json"),
        br2_config=load_public("configs/v6/task039br2_hai_continuous_step_feasibility.json"),
        materialized_audit_receipt=load_public(
            "docs/task_reports/TASK-039E3_R2R_UTILITY_NORMAL_ONLY_AUTHORITY_V1_MATERIALIZED_RECEIPT.json"
        ),
    )
    if authority.authority_hash != "1a6200adce791ddd9be8d87b566d47b65e78c1735829d0f91f4ea22127ad1343":
        raise AssertionError("AUDIT_LOWER_V4_REPLAY")
    if len(authority.rule_descriptors) != 42:
        raise AssertionError("AUDIT_COMMON_RELATION_COUNT")
    return authority


def exact_reconstruction(value: object) -> object:
    return type(value)(**{field.name: getattr(value, field.name) for field in fields(value)})


class IndependentAuthorityCustodyAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.v4_authority = build_lower_v4_authority()
        cls.bundle = build_evaluator_authority_bundle_v1(cls.v4_authority)
        cls.implementation = build_evaluator_implementation_authority_v1(cls.bundle)
        if cls.bundle.bundle_hash != "0510da125dd8a799c988927ba49ecb784cad5ea12b05b41e31406effe23051c9":
            raise AssertionError("AUDIT_EVALUATOR_BUNDLE_REPLAY")

    def test_caller_reconstructed_bundle_must_not_gain_canonical_custody(self) -> None:
        attacks = (
            exact_reconstruction(self.bundle),
            deepcopy(self.bundle),
            replace(self.bundle),
        )
        for candidate in attacks:
            with self.subTest(kind=type(candidate).__name__), self.assertRaises(
                UtilityEvaluatorV1Error
            ):
                validate_evaluator_authority_bundle_v1(candidate)  # type: ignore[arg-type]

    def test_caller_reconstructed_implementation_authority_must_reject(self) -> None:
        attacks = (
            exact_reconstruction(self.implementation),
            deepcopy(self.implementation),
            replace(self.implementation),
        )
        for candidate in attacks:
            with self.subTest(kind=type(candidate).__name__), self.assertRaises(
                UtilityEvaluatorV1Error
            ):
                validate_evaluator_implementation_authority_v1(
                    candidate, self.bundle  # type: ignore[arg-type]
                )


if __name__ == "__main__":
    unittest.main()
