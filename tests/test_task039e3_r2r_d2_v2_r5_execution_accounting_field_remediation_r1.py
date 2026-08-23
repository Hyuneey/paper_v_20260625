from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/remediate_task039e3_r2r_d2_v2_r5_execution_accounting_field_r1.py"
SPEC = importlib.util.spec_from_file_location("accounting_r1_subject", SCRIPT)
assert SPEC and SPEC.loader
subject = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = subject
SPEC.loader.exec_module(subject)


def synthetic_accounting() -> dict[str, object]:
    document: dict[str, object] = {
        "artifact_type": "D2V2ExecutionAccountingV1", "schema_version": "1.0.0",
        "created_at_utc": "2026-01-01T00:00:00Z", "task_id": "task",
        "execution_run_hash": "a" * 64, **subject.CORE_EXPECTED,
        "push_attempted": False, "remote_egress_status": "LOCAL_ONLY_NOT_PUSHED",
    }
    document["artifact_hash"] = subject.stable_hash(document)
    return document


def producer_source() -> str:
    lines = ["def producer():", "    accounting_core = {"]
    lines.extend(f'        "{key}": 0,' for key in subject.CORE_EXPECTED)
    lines.extend(["    }", "    accounting_identity = None"])
    return "\n".join(lines)


def validate_synthetic(document: dict[str, object]) -> subject.AccountingSchemaAudit:
    return subject.validate_accounting(document, producer_source(), str(document["artifact_hash"]))


class AccountingFieldRemediationTests(unittest.TestCase):
    def test_canonical_field_and_explicit_correction(self) -> None:
        audit = validate_synthetic(synthetic_accounting())
        self.assertEqual(subject.CANONICAL_FIELD, "d1_metric_artifact_reads")
        self.assertEqual(subject.R5_EXPECTED_TO_CANONICAL["d1_metric_reads"], subject.CANONICAL_FIELD)
        self.assertEqual(audit.schema_proven_name_corrections, 1)

    def test_fuzzy_and_injected_alias_rejected(self) -> None:
        for alias in ("d1_metric_read", "d1_metrics_reads", "d1_metric_reads"):
            document = synthetic_accounting(); document[alias] = 0
            document["artifact_hash"] = subject.stable_hash({k: v for k, v in document.items() if k != "artifact_hash"})
            with self.assertRaises(subject.AccountingRemediationError):
                validate_synthetic(document)

    def test_missing_wrong_type_and_wrong_value_rejected(self) -> None:
        mutations = []
        missing = synthetic_accounting(); missing.pop(subject.CANONICAL_FIELD); mutations.append(missing)
        wrong_type = synthetic_accounting(); wrong_type[subject.CANONICAL_FIELD] = False; mutations.append(wrong_type)
        wrong_value = synthetic_accounting(); wrong_value[subject.CANONICAL_FIELD] = 1; mutations.append(wrong_value)
        for document in mutations:
            document["artifact_hash"] = subject.stable_hash({k: v for k, v in document.items() if k != "artifact_hash"})
            with self.assertRaises(subject.AccountingRemediationError):
                validate_synthetic(document)

    def test_all_prohibited_execution_counters_rejected(self) -> None:
        for key in ("scientific_v2_execution_attempts", "scientific_v2_execution_retries",
                    "d0_executions", "d1_executions", "d2_v1_executions",
                    "d1_metric_artifact_reads", "d0_score_accesses", "d1_rule_reevaluations",
                    "test1_feature_accesses", "test2_accesses", "outer_executions"):
            document = synthetic_accounting(); document[key] = 2 if key == "scientific_v2_execution_attempts" else 1
            document["artifact_hash"] = subject.stable_hash({k: v for k, v in document.items() if k != "artifact_hash"})
            with self.subTest(key=key), self.assertRaises(subject.AccountingRemediationError):
                validate_synthetic(document)

    def test_result_driven_change_rejected(self) -> None:
        document = synthetic_accounting(); document["result_driven_changes"] = True
        document["artifact_hash"] = subject.stable_hash({k: v for k, v in document.items() if k != "artifact_hash"})
        with self.assertRaises(subject.AccountingRemediationError):
            validate_synthetic(document)

    def test_incomplete_blocker_snapshot_is_ineligible(self) -> None:
        document = {"artifact_hash": "", "status": "blocked_task039e3_r2r_utility_inner_d2_v2_result_integrity_audit_harness_remediation_r5",
                    "blocker_code": "D2_V2_R5_EXECUTION_ACCOUNTING_REJECTED", "metric_oracle_completed": True,
                    "fusion_evidence_v2_hash_match": True, "combined_prediction_v2_hash_match": True,
                    "metric_evidence_v2_hash_match": True, "prediction_before_label_pass": True,
                    "prediction_divergences": 0, "d0_preservation_violations": 0,
                    "trigger_class_violations": 0, "post_result_freeze_mutations": 0}
        document["artifact_hash"] = subject.stable_hash({k: v for k, v in document.items() if k != "artifact_hash"})
        old = subject.R5_BLOCKER_HASH
        try:
            subject.R5_BLOCKER_HASH = document["artifact_hash"]
            self.assertGreater(len(subject.validate_r5_blocker(document)), 0)
        finally:
            subject.R5_BLOCKER_HASH = old

    def test_control_flow_rejects_accounting_before_completion_gates(self) -> None:
        source = """def run_audit():
    if metric_document != expected_metric(): pass
    validate_public_metrics()
    validate_result_accounting()
    guard.require_exact()
    leakage = leakage_audit()
    attacks, accepted = adversarial()
    reports, markdown = build_reports()
def main(): pass
"""
        audit = subject.r5_control_flow(source)
        self.assertFalse(audit["completion_order_pass"])
        self.assertTrue(audit["accounting_before_leakage"])

    def test_scientific_paths_absent(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        forbidden = ("D0_DETECTOR_PREDICTION_ARTIFACT", "D1_RULE_PREDICTION_ARTIFACT",
                     "COMBINED_PREDICTION_ARTIFACT", "label-test1.csv", "FUSION_EVIDENCE_V2.json",
                     "METRIC_EVIDENCE_V2.json")
        for token in forbidden:
            self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()
