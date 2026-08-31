from __future__ import annotations

from pathlib import Path
import importlib.util
import json
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch
import sys

from paperworks.validation_v2.exp01_checkpoint_v2 import Exp01CheckpointReceiptV2
from paperworks.validation_v2.exp01_execution_v2 import (
    Exp01ExecutionError, Exp01ViewInputV2, _primary_mask, execute_exp01_matrix_v2,
)
from paperworks.validation_v2.exp01_relation_confirmation_v2 import ArmBlindConfirmationOutcomeV2
from paperworks.validation_v2.exp01_scientific_v1 import PAIR_UNIVERSE, ArmId, ViewId
from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_r2r_d0_detector_design_v1 import P1_FEATURE_ORDER


def _graph(corrected: bool) -> tuple[tuple[str, str], ...]:
    features = tuple(P1_FEATURE_ORDER)
    offset = 1 if corrected else 0
    return tuple(
        (features[(target_index + offset + rank) % len(features)], target)
        for target_index, target in enumerate(features)
        for rank in range(5)
    )


class Exp01ExecutionV2Tests(unittest.TestCase):
    def test_cli_replays_exact_tracked_meta_stat_authorities(self) -> None:
        script_path = Path("scripts/run_validation_v2_exp01.py").resolve()
        spec = importlib.util.spec_from_file_location("run_validation_v2_exp01", script_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        meta, stat = module._load_frozen_comparator_results(Path.cwd())
        self.assertEqual(20, len(meta))
        self.assertEqual(20, len(stat))
        source = script_path.read_text(encoding="utf-8")
        self.assertNotIn("--meta-stat-reference", source)
        self.assertIn("META_RESULT_HASH", source)
        self.assertIn("STAT_RESULT_HASH", source)

    def test_cli_rejects_mutated_meta_authority(self) -> None:
        script_path = Path("scripts/run_validation_v2_exp01.py").resolve()
        spec = importlib.util.spec_from_file_location("run_validation_v2_exp01_mutation", script_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "docs/task_reports"
            target.mkdir(parents=True)
            meta = json.loads(Path("docs/task_reports/TASK-039C_META_RESULT.json").read_text(encoding="utf-8"))
            stat = json.loads(Path("docs/task_reports/TASK-039C_STAT_RESULT.json").read_text(encoding="utf-8"))
            meta["top20_identities"][0]["target_identity"] = "P1_TIT03"
            (target / "TASK-039C_META_RESULT.json").write_text(json.dumps(meta), encoding="utf-8")
            (target / "TASK-039C_STAT_RESULT.json").write_text(json.dumps(stat), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "META_AUTHORITY_REPLAY_REJECTED"):
                module._load_frozen_comparator_results(root)

    def test_cli_rejects_comparator_before_any_data_capability_resolution(self) -> None:
        script_path = Path("scripts/run_validation_v2_exp01.py").resolve()
        spec = importlib.util.spec_from_file_location("run_validation_v2_exp01_order", script_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        capability_calls = 0

        def forbidden_capability(_root):
            nonlocal capability_calls
            capability_calls += 1
            raise AssertionError("data capability resolved before comparator replay")

        with tempfile.TemporaryDirectory() as directory:
            private_root = Path(directory) / "checkpoints"
            private_ledger = Path(directory) / "relations.json"
            argv = [
                str(script_path), "--repository-root", str(Path.cwd()),
                "--expected-source-commit", "a" * 40,
                "--private-checkpoint-root", str(private_root),
                "--private-relation-ledger", str(private_ledger),
                "--public-receipt", str(Path(directory) / "receipt.json"),
            ]
            with patch.object(sys, "argv", argv), patch.object(
                module, "_git_head", return_value="a" * 40,
            ), patch.object(
                module, "_git_worktree_is_clean", return_value=True,
            ), patch.object(
                module, "_load_frozen_comparator_results",
                side_effect=RuntimeError("EXP01_FROZEN_META_AUTHORITY_REPLAY_REJECTED"),
            ), patch.object(
                module, "resolve_hai_feature_root_capability_v1", side_effect=forbidden_capability,
            ):
                with self.assertRaisesRegex(RuntimeError, "META_AUTHORITY_REPLAY_REJECTED"):
                    module.main()
        self.assertEqual(0, capability_calls)

    def test_cli_requires_exact_clean_commit_before_data_access(self) -> None:
        source = Path("scripts/run_validation_v2_exp01.py").read_text(encoding="utf-8")
        self.assertIn("--expected-source-commit", source)
        self.assertIn("EXP01_EXPECTED_SOURCE_COMMIT_MISMATCH", source)
        self.assertIn("EXP01_DIRTY_WORKTREE_REJECTED", source)

    def test_cli_output_freeze_rejects_existing_or_partial_target(self) -> None:
        script_path = Path("scripts/run_validation_v2_exp01.py").resolve()
        spec = importlib.util.spec_from_file_location("run_validation_v2_exp01_freeze", script_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "receipt.json"
            module._write_atomic(target, {"status": "FIRST"})
            self.assertTrue(target.exists())
            with self.assertRaisesRegex(RuntimeError, "EXISTING_OUTPUT_REJECTED"):
                module._write_atomic(target, {"status": "SECOND"})
            target.unlink()
            target.with_suffix(".json.partial").write_text("partial", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "EXISTING_OUTPUT_REJECTED"):
                module._write_atomic(target, {"status": "THIRD"})

    def test_two_of_three_mask_contract_conflict_fails_closed_without_narrowing(self) -> None:
        pair = PAIR_UNIVERSE[0]
        seeds = tuple(
            SimpleNamespace(
                arm_id=ArmId.CORRECTED_SELF_EXCLUDED.value,
                view_id=ViewId.COMBINED.value,
                seed=seed,
                graph_edges=((pair,) if index < 2 else ()),
            )
            for index, seed in enumerate((11, 23, 37))
        )
        aggregates = (
            SimpleNamespace(arm_id=ArmId.FROZEN_SELF_ELIGIBLE.value, view_id=ViewId.COMBINED.value, top20=()),
            SimpleNamespace(arm_id=ArmId.CORRECTED_SELF_EXCLUDED.value, view_id=ViewId.COMBINED.value, top20=(pair,)),
            SimpleNamespace(arm_id=ArmId.CORRECTED_SELF_EXCLUDED.value, view_id=ViewId.TRAIN1_ONLY.value, top20=(pair,)),
            SimpleNamespace(arm_id=ArmId.CORRECTED_SELF_EXCLUDED.value, view_id=ViewId.TRAIN2_ONLY.value, top20=(pair,)),
        )
        with self.assertRaisesRegex(
            Exp01ExecutionError,
            "EXP01_FROZEN_CONTRACT_CONFLICT_PRIMARY_MASK_2_OF_3_VS_SHARED_ALL_SEEDS",
        ):
            _primary_mask(
                checkpoint_set=SimpleNamespace(seed_receipts=seeds), aggregates=aggregates,
                confirmed_pairs=(pair,), meta_top20=(), stat_top20=(),
            )

    def test_cli_has_no_precomputed_confirmation_prerequisite(self) -> None:
        source = Path("scripts/run_validation_v2_exp01.py").read_text(encoding="utf-8")
        self.assertNotIn("--arm-blind-confirmation", source)
        self.assertIn('split_id="train3"', source)
        self.assertIn("fit_and_confirm_arbitrary_union_v2", source)

    def test_exact_schedule_and_public_zero_access_boundary(self) -> None:
        row = tuple(float(index) for index in range(37))
        segment = tuple(row for _ in range(8))
        views = {
            ViewId.COMBINED: Exp01ViewInputV2(ViewId.COMBINED, (segment, segment), ("1" * 64, "2" * 64)),
            ViewId.TRAIN1_ONLY: Exp01ViewInputV2(ViewId.TRAIN1_ONLY, (segment,), ("1" * 64,)),
            ViewId.TRAIN2_ONLY: Exp01ViewInputV2(ViewId.TRAIN2_ONLY, (segment,), ("2" * 64,)),
        }
        calls: list[tuple[str, int]] = []

        def fake_train(**kwargs):
            arm = kwargs["arm_id"]
            seed = kwargs["seed"]
            calls.append((arm.value, seed))
            edges = _graph(arm is ArmId.CORRECTED_SELF_EXCLUDED)
            digest = stable_hash_v1({"graph_edges": edges})
            return SimpleNamespace(
                best_state_dict={}, graph_edges=edges,
                forward_graph_hash=digest, extraction_graph_hash=digest,
            )

        checkpoint_counter = 0

        def fake_persist(**kwargs):
            nonlocal checkpoint_counter
            checkpoint_counter += 1
            receipt = Exp01CheckpointReceiptV2(
                run_id=kwargs["run_id"], arm_id=kwargs["arm_id"], view_id=kwargs["view_id"],
                seed=kwargs["seed"], code_authority_hash=kwargs["code_authority_hash"],
                training_config_hash=kwargs["training_config_hash"], state_hash=f"{checkpoint_counter:064x}",
                file_sha256="a" * 64, byte_size=1, reopened=True, receipt_hash=f"{checkpoint_counter + 100:064x}",
            )
            return Path(f"checkpoint_{checkpoint_counter}.pt"), receipt

        def evaluator(pairs):
            evaluator.calls += 1
            return ArmBlindConfirmationOutcomeV2(
                pair_decisions=tuple((source, target, False) for source, target in pairs),
                private_decision_ledger_hash="a" * 64,
                train3_read_receipt_hash="b" * 64,
            )
        evaluator.calls = 0
        train4_calls = 0

        def train4_provider():
            nonlocal train4_calls
            train4_calls += 1
            self.assertEqual(evaluator.calls, 1)
            return (segment,), "4" * 64

        with tempfile.TemporaryDirectory() as directory, patch(
            "paperworks.validation_v2.exp01_execution_v2.train_exp01_seed_v2", side_effect=fake_train,
        ), patch(
            "paperworks.validation_v2.exp01_execution_v2.persist_private_checkpoint_v2", side_effect=fake_persist,
        ), patch(
            "paperworks.validation_v2.exp01_execution_v2.reopen_private_checkpoint_v2", return_value={"state_dict": {}},
        ), patch(
            "paperworks.validation_v2.exp01_execution_v2.evaluate_fixed_checkpoint_mse_v2", return_value=1.0,
        ):
            result = execute_exp01_matrix_v2(
                views=views,
                train4_provider=train4_provider,
                feature_order=P1_FEATURE_ORDER, private_checkpoint_root=Path(directory),
                code_authority_hash="c" * 64, confirmation_evaluator=evaluator,
                meta_top20=PAIR_UNIVERSE[:20], stat_top20=PAIR_UNIVERSE[20:40],
            )
        self.assertEqual(len(calls), 12)
        self.assertEqual(checkpoint_counter, 12)
        self.assertEqual(evaluator.calls, 1)
        self.assertEqual(train4_calls, 1)
        self.assertEqual(result.access_counters["train3_opens"], 1)
        self.assertEqual(result.access_counters["test1_accesses"], 0)
        self.assertEqual(result.access_counters["test2_accesses"], 0)
        self.assertEqual(result.access_counters["label_accesses"], 0)
        self.assertEqual(result.public_document()["status"], "COMPLETE_PENDING_INDEPENDENT_QA")


if __name__ == "__main__":
    unittest.main()
