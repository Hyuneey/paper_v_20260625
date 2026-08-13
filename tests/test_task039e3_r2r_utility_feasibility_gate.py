from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest

from paperworks.data.contracts_v2 import (
    CreationMetadataV2,
    ProvenanceStatusV2,
    RawRangeV2,
    SealedAccessStatusV2,
    SplitManifestV2,
    SplitRoleV2,
)
from paperworks.data.splits_v2 import (
    DataOperationV2,
    SplitPermissionV2Error,
    assert_operation_permitted_v2,
)


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "task039e3_utility_gate",
    ROOT / "scripts/audit_task039e3_r2r_utility_gate_v1.py",
)
assert SPEC is not None and SPEC.loader is not None
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


def split(role: SplitRoleV2, sealed: SealedAccessStatusV2) -> SplitManifestV2:
    return SplitManifestV2(
        dataset_manifest_id="a" * 64,
        data_view_id="b" * 64,
        role=role,
        raw_ranges=(RawRangeV2(0, 100),),
        event_ids=None,
        purge_gap_samples=20,
        process_scope=("P1",),
        seed=None,
        creation_policy="synthetic_metadata_only",
        provenance_status=ProvenanceStatusV2.VERIFIED,
        sealed_access_status=sealed,
        split_before_windowing=True,
        creation_metadata=CreationMetadataV2(
            created_at="2026-08-13T00:00:00+09:00",
            created_by="test",
            code_commit="a" * 40,
            config_hash="c" * 64,
        ),
    )


class UtilityGatePureTests(unittest.TestCase):
    def test_exact_utility_split_permissions(self) -> None:
        snapshot = gate.verify_utility_operation_permissions()
        self.assertTrue(snapshot["verified"])
        self.assertEqual(
            snapshot["operation_permissions"],
            {
                "assess_rule_utility": ["inner_utility"],
                "select_rule_or_no_op": ["inner_utility"],
                "replay_outer": ["outer_validation"],
                "run_sealed_evaluation": ["sealed_evaluation"],
            },
        )

    def test_sealed_evaluation_fails_closed_without_approval(self) -> None:
        awaiting = split(
            SplitRoleV2.SEALED_EVALUATION,
            SealedAccessStatusV2.APPROVAL_REQUIRED,
        )
        with self.assertRaisesRegex(SplitPermissionV2Error, "explicit approval"):
            assert_operation_permitted_v2(
                awaiting, DataOperationV2.RUN_SEALED_EVALUATION
            )
        approved = split(
            SplitRoleV2.SEALED_EVALUATION,
            SealedAccessStatusV2.APPROVED,
        )
        assert_operation_permitted_v2(
            approved, DataOperationV2.RUN_SEALED_EVALUATION
        )

    def test_metadata_boundary_allows_label_schema_but_rejects_values(self) -> None:
        gate.assert_metadata_only(
            {
                "label_specification": {
                    "field_name": "label",
                    "encoding": {"normal": 0, "attack": 1},
                },
                "label_availability": "available",
            }
        )
        for key in ("label_values", "attack_intervals", "utility_results", "predictions"):
            with self.subTest(key=key), self.assertRaises(gate.UtilityGateError):
                gate.assert_metadata_only({key: [0, 1]})

    def test_metric_definition_completeness_is_fail_closed(self) -> None:
        self.assertEqual(
            gate.classify_metric_definition(None, precommitted=False),
            "NOT_PRECOMMITTED",
        )
        self.assertEqual(
            gate.classify_metric_definition({"formula": "x"}, precommitted=True),
            "PRECOMMITTED_BUT_INCOMPLETE",
        )
        exact = {
            "formula": "frozen",
            "denominator": "frozen",
            "unit_of_analysis": "relation",
            "aggregation": "frozen",
            "threshold_policy": "normal_only",
            "direction": "higher",
        }
        self.assertEqual(
            gate.classify_metric_definition(exact, precommitted=True),
            "PRECOMMITTED_AND_EXACT",
        )
        self.assertEqual(
            gate.classify_metric_definition(exact, precommitted=True, compatible=False),
            "INCOMPATIBLE_WITH_CURRENT_TASK",
        )

    def test_gate_requires_no_rule_arm_agnostic_and_direct_isolation(self) -> None:
        requirements = set(gate.UTILITY_PROTOCOL_REQUIREMENTS)
        self.assertIn("freeze_no_rule_coverage_and_denominator_semantics", requirements)
        self.assertIn("freeze_paired_arm_agnostic_comparison_and_statistical_reporting", requirements)
        source = (ROOT / "scripts/audit_task039e3_r2r_utility_gate_v1.py").read_text(encoding="utf-8")
        self.assertNotIn("run_direct_number", source)
        self.assertNotIn("OPENAI_API_KEY", source)


class UtilityGateRepositoryTests(unittest.TestCase):
    def test_repository_snapshot_is_metadata_only_and_requires_protocol_freeze(self) -> None:
        snapshot = gate.audit_repository(ROOT)
        self.assertEqual(snapshot["input_authority"]["utility_necessity"], "ESSENTIAL")
        self.assertEqual(
            snapshot["split_collection"]["materialized_roles"],
            ["normal_candidate_fit", "normal_guard", "normal_relation_calibration"],
        )
        for role in ("inner_utility", "outer_validation", "sealed_evaluation"):
            self.assertFalse(
                snapshot["split_collection"]["utility_role_readiness"][role]["ready"]
            )
            self.assertFalse(
                snapshot["split_collection"]["utility_role_readiness"][role]["manifest_exists"]
            )
        self.assertEqual(
            snapshot["split_collection"]["utility_role_readiness"]["sealed_evaluation"],
            {
                "manifest_exists": False,
                "manifest_count": 0,
                "ready": False,
                "label_metadata_available_at_dataset_level": True,
                "sealed_access_status": "not_materialized",
                "required_sealed_status_before_access": "approved",
            },
        )
        self.assertEqual(
            snapshot["decision"]["protocol_readiness_classification"],
            "UTILITY_PROTOCOL_FREEZE_REQUIRED",
        )
        self.assertFalse(snapshot["decision"]["utility_execution_authorization_ready"])
        self.assertFalse(snapshot["label_boundary"]["label_values_accessed"])
        self.assertFalse(snapshot["label_boundary"]["utility_values_computed"])

    def test_public_input_self_hashes_and_temporal_query(self) -> None:
        for relative in (
            gate.SPLIT_COLLECTION_PATH,
            gate.ANALYSIS_CLAIMS_PATH,
            gate.ANALYSIS_RECEIPT_PATH,
        ):
            document = json.loads((ROOT / relative).read_text(encoding="utf-8"))
            gate.verify_self_hash(document)
        self.assertTrue(
            gate.temporal_precommitment(
                ROOT,
                candidate_commit="59715458d1635cb3a673a640262d3343ddaeb3cb",
                result_boundary_commit=gate.RESULT_OBSERVATION_BOUNDARY,
            )
        )


if __name__ == "__main__":
    unittest.main()
