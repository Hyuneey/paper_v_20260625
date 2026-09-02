from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
V2 = ROOT / "research_control_center" / "validation_v2"


class ValidationV2ProgramTests(unittest.TestCase):
    def test_program_state_preserves_v1_and_held_out_boundary(self) -> None:
        state = json.loads((V2 / "PROGRAM_STATE.json").read_text(encoding="utf-8"))
        self.assertEqual(state["pilot_v1_status"], "IMMUTABLE")
        self.assertEqual(state["validation_v2_authority_policy"], "FORMAL_V4")
        self.assertEqual(state["test1_role"], "DEVELOPMENT_ONLY")
        self.assertFalse(state["held_out_authorized"])
        self.assertEqual(state["safety_counters"]["test2_accesses"], 0)
        self.assertEqual(state["program_status"], "NORMAL_ONLY_TRACKS_COMPLETE_EXP04_NEXT")
        self.assertEqual(
            state["experiment_status"]["EXP-01B"],
            "COMPLETE_NORMAL_ONLY_GDN_ABLATION_ONLY",
        )
        self.assertEqual(
            state["experiment_status"]["EXP-04"],
            "READY_LABEL_BLIND_PREDICTION_FREEZE",
        )
        self.assertEqual(state["safety_counters"]["scientific_executions"], 3)
        self.assertEqual(state["authority_decision_receipt"], "APPROVED_FORMAL_V4")
        self.assertEqual(state["decision_gates"]["DG-01"], "RESOLVED_BY_USER")
        self.assertEqual(state["canonical_to_v4_bridge_status"], "NOT_SELECTED")
        self.assertEqual(
            state["fresh_machine_synthetic"]["status"],
            "PASS_CLEAN_CHECKOUT_FRESH_ENVIRONMENT_SYNTHETIC",
        )
        self.assertEqual(state["dataset_acquisition_policy"]["policy_id"], "DATA-POLICY-001")
        self.assertEqual(state["dataset_acquisition_policy"]["next_action"], "NORMAL_ONLY_EXPERIMENT_EXECUTION")
        self.assertFalse(state["dataset_acquisition_policy"]["user_local_path_required"])
        self.assertEqual(state["historical_execution_blocker"]["code"], "BLOCKED_NORMAL_DATA_NOT_FOUND")
        self.assertEqual(
            state["historical_execution_blocker"]["disposition"],
            "HAI_CODE_MATERIALIZATION_POLICY_NOT_PROPAGATED_TO_V2_RECOVERY_LOGIC",
        )

    def test_task_branches_do_not_conflict_with_integration_ref(self) -> None:
        with (V2 / "TASK_INDEX.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        branches = {row["branch"] for row in rows}
        self.assertIn("validation-v2", branches)
        self.assertTrue(all("validation-v2/" not in branch for branch in branches))

    def test_decision_gates_record_user_choices(self) -> None:
        text = (V2 / "DECISION_GATES.md").read_text(encoding="utf-8")
        self.assertIn("RESOLVED_BY_USER", text)
        self.assertIn("APPROVED_FORMAL_V4", text)
        self.assertIn("RESOLVED_ISOLATION_FOREST", text)
        self.assertIn("DG-05", text)

    def test_pilot_v1_preservation_verifier_passes(self) -> None:
        python = Path(__import__("sys").executable)
        completed = subprocess.run(
            [
                str(python),
                str(
                    ROOT
                    / "research_control_center"
                    / "scripts"
                    / "verify_validation_v2_pilot_preservation.py"
                ),
                "--repo-root",
                str(ROOT),
            ],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertIn("PILOT_V1_PRESERVATION_PASS", completed.stdout)

    def test_fresh_machine_receipt_is_synthetic_and_zero_access(self) -> None:
        receipt = json.loads(
            (V2 / "reports" / "V2_FRESH_MACHINE_SYNTHETIC_REHEARSAL_RECEIPT.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(receipt["status"], "PASS_CLEAN_CHECKOUT_FRESH_ENVIRONMENT_SYNTHETIC")
        self.assertFalse(receipt["scientific_data_required"])
        for key in (
            "scientific_executions",
            "test1_accesses",
            "test2_accesses",
            "heldout_accesses",
            "provider_calls",
            "private_exposures",
        ):
            self.assertEqual(receipt[key], 0)

    def test_program_status_evidence_self_hash(self) -> None:
        evidence = json.loads(
            (V2 / "reports" / "V2_PROGRAM_STATUS_EVIDENCE.json").read_text(encoding="utf-8")
        )
        expected = evidence.pop("self_hash")
        actual = hashlib.sha256(
            json.dumps(
                evidence,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        self.assertEqual(expected, actual)

    def test_normal_custody_blocker_receipt_is_self_hashed_and_zero_access(self) -> None:
        receipt = json.loads(
            (V2 / "receipts" / "HAI_NORMAL_ONLY_CUSTODY_RECEIPT_V2.json").read_text(
                encoding="utf-8"
            )
        )
        expected = receipt.pop("receipt_self_hash")
        actual = hashlib.sha256(
            json.dumps(
                receipt,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        self.assertEqual(expected, actual)
        self.assertEqual(receipt["status"], "BLOCKED_NORMAL_DATA_NOT_FOUND")
        self.assertFalse(receipt["binding_issued"])
        self.assertEqual(receipt["bound_split_ids"], [])
        self.assertEqual(
            receipt["missing_symbolic_split_ids"],
            ["HAI_TRAIN1", "HAI_TRAIN2", "HAI_TRAIN3", "HAI_TRAIN4"],
        )
        self.assertFalse(receipt["locator"]["approved_locator_configured"])
        for value in receipt["access_accounting"].values():
            self.assertEqual(value, 0)

    def test_data_policy_uses_code_materialization_before_user_path(self) -> None:
        policy = json.loads((V2 / "policies" / "DATA_POLICY_001.json").read_text(encoding="utf-8"))
        self.assertEqual(policy["acquisition_mode"], "CODE_MATERIALIZED_OFFICIAL_DISTRIBUTION")
        self.assertEqual(policy["official_distribution"], "icsdataset/hai-security-dataset")
        self.assertEqual(policy["identity_authority"], "PINNED_OFFICIAL_GIT_SNAPSHOT_AND_GIT_LFS_OBJECTS")
        self.assertFalse(policy["user_local_path_required"])
        self.assertEqual(policy["missing_data_next_action"], "CODE_BASED_MATERIALIZATION")
        self.assertEqual(policy["authorized_scope"], ["HAI_TRAIN1", "HAI_TRAIN2", "HAI_TRAIN3", "HAI_TRAIN4"])

    def test_normal_only_materialization_and_custody_receipts_are_self_hashed(self) -> None:
        for name in (
            "HAI_NORMAL_ONLY_MATERIALIZATION_RECEIPT_V2.json",
            "HAI_NORMAL_ONLY_CUSTODY_BINDING_V2.json",
        ):
            receipt = json.loads((V2 / "receipts" / name).read_text(encoding="utf-8"))
            expected = receipt.pop("self_hash")
            actual = hashlib.sha256(
                json.dumps(receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
            self.assertEqual(expected, actual)
            if name.endswith("MATERIALIZATION_RECEIPT_V2.json"):
                self.assertEqual(receipt["access_counters"]["private_exposures"], 0)
            else:
                self.assertEqual(receipt["private_exposures"], 0)
        binding = json.loads((V2 / "receipts" / "HAI_NORMAL_ONLY_CUSTODY_BINDING_V2.json").read_text(encoding="utf-8"))
        self.assertEqual(binding["status"], "NORMAL_ONLY_CUSTODY_READY")
        self.assertEqual(binding["bound_split_ids"], ["HAI_TRAIN1", "HAI_TRAIN2", "HAI_TRAIN3", "HAI_TRAIN4"])
        self.assertEqual(binding["test1_accesses"], 0)
        self.assertEqual(binding["test2_accesses"], 0)
        self.assertEqual(binding["label_accesses"], 0)

    def test_exp01_exp02_readiness_fail_closed_before_scientific_read(self) -> None:
        expected = {
            "EXP01_EXECUTION_READINESS_V2.json": "GDN_CONTRIBUTION_UNRESOLVED_FAIL_CLOSED",
            "EXP02_EXECUTION_READINESS_V2.json": "BLOCKED_EXP02_SCIENTIFIC_RUNNER_AND_COHORT_AUTHORITY",
        }
        for name, status in expected.items():
            receipt = json.loads((V2 / "reports" / name).read_text(encoding="utf-8"))
            self_hash = receipt.pop("self_hash")
            actual = hashlib.sha256(
                json.dumps(receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
            self.assertEqual(self_hash, actual)
            self.assertEqual(receipt["status"], status)
            self.assertFalse(receipt["disposition"].get("scientific_result_exists", False))
            for key, value in receipt["access_counters"].items():
                if key != "scientific_executions":
                    self.assertEqual(value, 0, key)
            self.assertEqual(receipt["access_counters"]["scientific_executions"], 0)

    def test_current_recovery_outputs_do_not_request_manual_hai_path(self) -> None:
        current = (
            ROOT / "research_control_center" / "MY_TODO.md",
            ROOT / "research_control_center" / "generated" / "GPT_BRIEF.md",
            V2 / "PROGRAM_STATE.json",
            V2 / "reports" / "V2_NORMAL_CUSTODY_RECOVERY_REPORT.md",
            ROOT / "research_control_center" / "SESSION_HANDOFF.md",
        )
        for path in current:
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("HAI_NORMAL_ROOT", text, path.name)
        recovery = (V2 / "reports" / "V2_NORMAL_CUSTODY_RECOVERY_REPORT.md").read_text(encoding="utf-8")
        self.assertIn("CODE_BASED_MATERIALIZATION", recovery)
        self.assertIn("NORMAL_ONLY_CUSTODY_READY", recovery)

    def test_frozen_preregistrations_remain_unchanged(self) -> None:
        expected = {
            "EXP01_PREREGISTRATION_V2.json": "6da75dd0d8a21ae8fe3fd85286beca93536c8cea6eac6ff35d620192063661cc",
            "EXP02_PREREGISTRATION_V2.json": "62b5de353a55560855e55cdeac3233505975377f354cbec3b66f1ba193570721",
        }
        for name, digest in expected.items():
            document = json.loads((V2 / "preregistration" / name).read_text(encoding="utf-8"))
            self.assertEqual(document["preregistration_hash"], digest)

    def test_professor_readiness_package_is_complete_and_qualified(self) -> None:
        package = ROOT / "docs" / "professor_experiment_update_v2"
        expected = {
            *(f"{index:02d}_{name}.md" for index, name in (
                (1, "ONE_PAGE_SUMMARY"),
                (2, "WHAT_CHANGED_SINCE_PILOT_V1"),
                (3, "VALIDATION_V2_METHOD"),
                (4, "EXP01_GDN_RESULTS"),
                (5, "EXP02_NUMERIC_RESULTS"),
                (6, "EXP03_AGENTIC_RESULTS"),
                (7, "EXP04_DETECTION_RESULTS"),
                (8, "EXP05_EXPLANATION_RESULTS"),
                (9, "CLAIM_AND_LIMITATION_MATRIX"),
                (10, "HELDOUT_NEXT_PLAN"),
                (11, "PROFESSOR_DECISION_AGENDA"),
                (12, "EMAIL_DRAFT"),
                (13, "SLIDE_OUTLINE"),
            )),
            "PROFESSOR_EXPERIMENT_UPDATE_V2.html",
        }
        self.assertEqual(expected, {path.name for path in package.iterdir() if path.is_file()})
        summary = (package / "01_ONE_PAGE_SUMMARY.md").read_text(encoding="utf-8")
        self.assertIn("EXP-01·EXP-01B 및 EXP-02 정상 데이터 실행을 완료", summary)
        self.assertIn("test1·공격 label·test2·held-out 접근", summary)


if __name__ == "__main__":
    unittest.main()
