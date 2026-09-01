from __future__ import annotations

import inspect
import json
import pickle
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

from paperworks.profiling.task039d1_execution_optimization_v1 import (
    audit_event_semantic_parity_v1,
    audit_isolation_semantic_parity_v1,
    audit_structural_complexity_v1,
    classify_all_source_isolation_indexed_v1,
    extract_sustained_step_events_linear_v1,
)
from paperworks.validation_v2 import exp01_relation_confirmation_v2 as confirmation
from paperworks.validation_v2.exp01_execution_v2 import resume_exp01_postprocessing_v2
from paperworks.validation_v2.exp01_checkpoint_v2 import (
    Exp01CheckpointError,
    Exp01CheckpointReceiptV2,
    canonical_state_hash_v2,
    recover_existing_private_checkpoint_v2,
)
from paperworks.validation_v2.exp01_recovery_v2 import (
    INTERRUPTED_ACCESS_COUNTERS,
    ORIGIN_TRAINING_CODE_AUTHORITY_HASH,
    ORIGIN_TRAINING_CONFIG_HASH,
    build_interrupted_checkpoint_recovery_receipt_v2,
    cumulative_access_counters_v2,
    verify_interrupted_checkpoint_recovery_receipt_v2,
)
from paperworks.validation_v2.exp01_scientific_v1 import EXPECTED_SCHEDULE
from paperworks.v6.common import stable_hash_v1


class _FakeTensor:
    def __init__(self, values) -> None:
        self._values = np.asarray(values, dtype=np.float32)

    @property
    def dtype(self):
        return self._values.dtype

    @property
    def shape(self):
        return self._values.shape

    def detach(self):
        return self

    def cpu(self):
        return self

    def contiguous(self):
        return self

    def numpy(self):
        return self._values


def _fake_torch():
    def load(path, **_kwargs):
        with Path(path).open("rb") as handle:
            return pickle.load(handle)

    return SimpleNamespace(load=load)


class Exp01PerformanceRemediationTests(unittest.TestCase):
    def test_candidate_policy_freeze_binds_complete_negative_exp01_result(self) -> None:
        policy_path = Path(
            "research_control_center/validation_v2/policies/CANDIDATE_POLICY_FREEZE_V2.json"
        )
        result_path = Path(
            "research_control_center/validation_v2/results/EXP01_EXECUTION_RECEIPT_V2.json"
        )
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        result = json.loads(result_path.read_text(encoding="utf-8"))
        expected_hash = policy.pop("policy_self_hash")
        self.assertEqual(stable_hash_v1(policy), expected_hash)
        self.assertEqual(policy["source_result_hash"], result["result_hash"])
        self.assertEqual(
            policy["source_result_public_receipt_hash"], result["public_receipt_hash"]
        )
        self.assertEqual(result["primary_mask_pair_count"], 0)
        self.assertEqual(
            policy["decision"], "DEMOTE_GDN_TO_ABLATION_AND_USE_META_STAT"
        )
        self.assertEqual(policy["primary_discovery_arms"], ["META", "STAT"])
        self.assertTrue(
            all(value == 0 for value in policy["access_counters"].values())
        )

    def test_resume_path_never_calls_training(self) -> None:
        source = inspect.getsource(resume_exp01_postprocessing_v2)
        self.assertNotIn("train_exp01_seed_v2(", source)
        self.assertIn("recover_existing_private_checkpoint_v2(", source)
        self.assertIn("replay_exp01_checkpoint_graph_v2(", source)

    def test_exp01_routes_to_audited_linear_event_adapter(self) -> None:
        self.assertIs(
            confirmation.extract_sustained_step_events_linear_v1,
            extract_sustained_step_events_linear_v1,
        )
        source = inspect.getsource(confirmation.fit_and_confirm_arbitrary_union_v2)
        self.assertNotIn("extract_sustained_step_events_v1(", source)
        self.assertIn("extract_sustained_step_events_linear_v1(", source)

    def test_exp01_routes_to_audited_indexed_isolation_adapter(self) -> None:
        self.assertIs(
            confirmation.classify_all_source_isolation_indexed_v1,
            classify_all_source_isolation_indexed_v1,
        )
        source = inspect.getsource(confirmation.fit_and_confirm_arbitrary_union_v2)
        self.assertNotIn("classify_all_source_isolation_v1(", source)
        self.assertIn("classify_all_source_isolation_indexed_v1(", source)

    def test_existing_semantic_parity_audits_pass(self) -> None:
        audit_event_semantic_parity_v1()
        audit_isolation_semantic_parity_v1()
        complexity = audit_structural_complexity_v1()
        self.assertEqual(complexity["event_extraction_complexity_class"], "linear_in_sequence_length")
        self.assertEqual(
            complexity["isolation_complexity_class"],
            "O(E log E)_with_fixed_12_source_context",
        )

    def test_interrupted_recovery_receipt_binds_exact_schedule_and_counters(self) -> None:
        receipts = []
        for order, (arm, view, seed) in enumerate(EXPECTED_SCHEDULE, start=1):
            values = {
                "run_id": f"run_{order:02d}_{arm}_{view}_seed_{seed}",
                "arm_id": arm,
                "view_id": view,
                "seed": seed,
                "code_authority_hash": ORIGIN_TRAINING_CODE_AUTHORITY_HASH,
                "training_config_hash": ORIGIN_TRAINING_CONFIG_HASH,
                "state_hash": f"{order:064x}",
                "file_sha256": f"{order + 20:064x}",
                "byte_size": order,
                "reopened": True,
            }
            provisional = Exp01CheckpointReceiptV2(**values)
            receipts.append(Exp01CheckpointReceiptV2(
                **values,
                receipt_hash=stable_hash_v1(provisional.to_dict(include_hash=False)),
            ))
        document = build_interrupted_checkpoint_recovery_receipt_v2(
            checkpoint_receipts=tuple(receipts),
            snapshot_source_commit="a" * 40,
            issued_at_utc="2026-09-01T00:00:00Z",
        )
        self.assertEqual(
            verify_interrupted_checkpoint_recovery_receipt_v2(document),
            document["receipt_self_hash"],
        )
        self.assertEqual(
            document["interrupted_attempt_access_counters"],
            dict(INTERRUPTED_ACCESS_COUNTERS),
        )
        mutated = dict(document)
        mutated["training_reexecuted"] = True
        with self.assertRaisesRegex(Exception, "self-hash mismatch"):
            verify_interrupted_checkpoint_recovery_receipt_v2(mutated)

    def test_cumulative_access_accounting_keeps_both_attempts(self) -> None:
        resumed = {
            "train1_opens": 1,
            "train2_opens": 1,
            "train3_opens": 1,
            "train4_opens": 1,
            "test1_accesses": 0,
            "test2_accesses": 0,
            "heldout_accesses": 0,
            "label_accesses": 0,
            "provider_calls": 0,
        }
        total = cumulative_access_counters_v2(resumed)
        self.assertEqual(total["train1_opens"], 2)
        self.assertEqual(total["train2_opens"], 2)
        self.assertEqual(total["train3_opens"], 2)
        self.assertEqual(total["train4_opens"], 1)
        self.assertEqual(total["test1_accesses"], 0)

    def test_resume_cli_is_postprocessing_only_and_records_cpu_environment(self) -> None:
        source = Path("scripts/resume_validation_v2_exp01_postprocessing.py").read_text(encoding="utf-8")
        self.assertNotIn("execute_exp01_matrix_v2", source)
        self.assertNotIn("train_exp01_seed_v2", source)
        self.assertIn("resume_exp01_postprocessing_v2", source)
        self.assertIn('"compute_device": "cpu"', source)
        self.assertIn('"training_reexecuted": False', source)
        self.assertIn('"host_gpu_available"', source)
        self.assertIn('"driver_version"', source)
        self.assertIn('"driver_reported_cuda_version"', source)
        self.assertIn("_load_optimization_authority(root)", source)
        self.assertIn('"semantic_preserving_implementation_change": True', source)
        self.assertIn('"scientific_formulas_changed": False', source)
        self.assertIn('"test1_accesses": 0', source)
        self.assertIn('"test2_accesses": 0', source)

    def test_checkpoint_recovery_replays_existing_bytes_without_rewrite(self) -> None:
        state = {"weight": _FakeTensor([[1.0, 2.0], [3.0, 4.0]])}
        state_hash = canonical_state_hash_v2(state)
        code_hash = "a" * 64
        config_hash = "b" * 64
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "run_01_ARM_VIEW_seed_11.pt"
            payload = {
                "schema": "paperworks.validation_v2.exp01_private_checkpoint_v2",
                "schema_version": "2.0.0",
                "run_id": "run_01_ARM_VIEW_seed_11",
                "arm_id": "ARM",
                "view_id": "VIEW",
                "seed": 11,
                "code_authority_hash": code_hash,
                "training_config_hash": config_hash,
                "state_hash": state_hash,
                "state_dict": state,
            }
            with path.open("wb") as handle:
                pickle.dump(payload, handle)
            before = path.read_bytes()
            with patch.dict(sys.modules, {"torch": _fake_torch()}):
                recovered_path, receipt, reopened = recover_existing_private_checkpoint_v2(
                    private_root=root,
                    run_id="run_01_ARM_VIEW_seed_11",
                    arm_id="ARM",
                    view_id="VIEW",
                    seed=11,
                    expected_code_authority_hash=code_hash,
                    expected_training_config_hash=config_hash,
                )
            self.assertEqual(recovered_path, path)
            self.assertEqual(receipt.state_hash, state_hash)
            self.assertEqual(reopened["state_hash"], state_hash)
            self.assertEqual(path.read_bytes(), before)

    def test_checkpoint_recovery_rejects_wrong_authority_and_partial(self) -> None:
        state = {"weight": _FakeTensor([1.0])}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "run_01_ARM_VIEW_seed_11.pt"
            payload = {
                "schema": "paperworks.validation_v2.exp01_private_checkpoint_v2",
                "schema_version": "2.0.0",
                "run_id": "run_01_ARM_VIEW_seed_11",
                "arm_id": "ARM",
                "view_id": "VIEW",
                "seed": 11,
                "code_authority_hash": "a" * 64,
                "training_config_hash": "b" * 64,
                "state_hash": canonical_state_hash_v2(state),
                "state_dict": state,
            }
            with path.open("wb") as handle:
                pickle.dump(payload, handle)
            with patch.dict(sys.modules, {"torch": _fake_torch()}):
                with self.assertRaises(Exp01CheckpointError):
                    recover_existing_private_checkpoint_v2(
                        private_root=root,
                        run_id="run_01_ARM_VIEW_seed_11",
                        arm_id="ARM",
                        view_id="VIEW",
                        seed=11,
                        expected_code_authority_hash="c" * 64,
                        expected_training_config_hash="b" * 64,
                    )
            path.with_suffix(".pt.partial").write_bytes(b"partial")
            with patch.dict(sys.modules, {"torch": _fake_torch()}):
                with self.assertRaises(Exp01CheckpointError):
                    recover_existing_private_checkpoint_v2(
                        private_root=root,
                        run_id="run_01_ARM_VIEW_seed_11",
                        arm_id="ARM",
                        view_id="VIEW",
                        seed=11,
                        expected_code_authority_hash="a" * 64,
                        expected_training_config_hash="b" * 64,
                    )


if __name__ == "__main__":
    unittest.main()
