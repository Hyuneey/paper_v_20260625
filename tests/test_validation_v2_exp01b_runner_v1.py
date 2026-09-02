from __future__ import annotations

from dataclasses import dataclass
import pickle
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

import numpy as np

from paperworks.validation_v2.exp01_relation_confirmation_v2 import (
    ArmBlindConfirmationOutcomeV2,
    ArmBlindRelationExecutionV2,
)
from paperworks.validation_v2.exp01_scientific_v1 import PAIR_UNIVERSE
from paperworks.validation_v2.exp01b_backend_v1 import Exp01BCheckpointEvidenceV1
from paperworks.validation_v2.exp01b_contract_v1 import (
    ComputeBackend, REQUIRED_DETERMINISTIC_FLAGS, build_environment_freeze_v1,
)
from paperworks.validation_v2.exp01b_reference_v1 import (
    Exp01BReferenceError,
    NormalConfirmedDirectionalRelationV1,
    directional_relation_id_v1,
)
from paperworks.validation_v2.exp01b_runner_v1 import (
    Exp01BScientificInputsV1,
    FormalV4RuleConversionInputV1,
    run_exp01b_v1,
    write_sanitized_exp01b_outputs_v1,
)


class _Tensor:
    def __init__(self, values):
        self._values = np.asarray(values, dtype=np.float32)
    def detach(self): return self
    def cpu(self): return self
    def contiguous(self): return self
    def numpy(self): return self._values
    @property
    def dtype(self): return self._values.dtype
    @property
    def shape(self): return self._values.shape


class _Torch:
    @staticmethod
    def save(payload, stream): pickle.dump(payload, stream)
    @staticmethod
    def load(stream, **_kwargs): return pickle.load(stream)


class Exp01BRunnerTests(unittest.TestCase):
    def test_reference_uses_actual_formal_v4_horizon_set(self) -> None:
        binding = "d" * 64
        relation_id = directional_relation_id_v1(
            source=PAIR_UNIVERSE[0][0], target=PAIR_UNIVERSE[0][1],
            source_direction="step_up", target_direction="increase",
            selected_horizon_seconds=30, confirmation_authority_hash=binding,
        )
        NormalConfirmedDirectionalRelationV1(
            relation_id=relation_id, source=PAIR_UNIVERSE[0][0], target=PAIR_UNIVERSE[0][1],
            source_direction="step_up", target_direction="increase",
            selected_horizon_seconds=30, relation_binding_hash=binding,
        )
        bad_id = directional_relation_id_v1(
            source=PAIR_UNIVERSE[0][0], target=PAIR_UNIVERSE[0][1],
            source_direction="step_up", target_direction="increase",
            selected_horizon_seconds=2, confirmation_authority_hash=binding,
        )
        with self.assertRaisesRegex(Exp01BReferenceError, "horizon"):
            NormalConfirmedDirectionalRelationV1(
                relation_id=bad_id, source=PAIR_UNIVERSE[0][0], target=PAIR_UNIVERSE[0][1],
                source_direction="step_up", target_direction="increase",
                selected_horizon_seconds=2, relation_binding_hash=binding,
            )

    def test_full_runner_uses_nine_runs_and_normal_only_sanitized_result(self) -> None:
        calls = []
        def trainer(**kwargs):
            calls.append((len(kwargs["segments"]), kwargs["seed"], kwargs["config"].device))
            return SimpleNamespace(
                best_state_dict={"weight": _Tensor([kwargs["seed"]])},
                graph_edges=tuple(PAIR_UNIVERSE),
                forward_graph_hash="c" * 64,
            )
        def evaluator(**kwargs):
            seed = kwargs["seed"]
            edge = {pair: float(144 - index + (seed / 1000.0)) for index, pair in enumerate(PAIR_UNIVERSE)}
            attention = {pair: float(144 - index) for index, pair in enumerate(PAIR_UNIVERSE)}
            occlusion = {pair: 0.01 for pair in PAIR_UNIVERSE}
            return Exp01BCheckpointEvidenceV1(edge, attention, edge, edge, occlusion, True)
        def confirmer(**_kwargs):
            directional = [
                {"source": source, "target": target, "source_direction": "step_up",
                 "target_direction": "increase", "horizon": 30, "confirmed": True}
                for source, target in PAIR_UNIVERSE[:50]
            ]
            outcome = ArmBlindConfirmationOutcomeV2(
                pair_decisions=tuple((source, target, index < 50) for index, (source, target) in enumerate(PAIR_UNIVERSE)),
                private_decision_ledger_hash="e" * 64,
                train3_read_receipt_hash="f" * 64,
            )
            return ArmBlindRelationExecutionV2(
                outcome=outcome,
                private_ledger={"directional_confirmation": directional},
            )
        environment = build_environment_freeze_v1(
            backend=ComputeBackend.CPU_FALLBACK, python_version="3.12",
            torch_version="2.12.1+cpu", cuda_build="NONE_CPU_BUILD",
            driver_version="610.47", gpu_model="NONE",
            deterministic_flags=dict(REQUIRED_DETERMINISTIC_FLAGS),
            synthetic_smoke_passed=True, model_device="cpu", tensor_device="cpu",
        )
        matrix = np.zeros((20, 37), dtype=np.float64)
        inputs = Exp01BScientificInputsV1(
            train1=matrix, train2=matrix, train3=matrix, train4=matrix,
            receipt_hashes={name: str(index) * 64 for index, name in enumerate(("train1", "train2", "train3", "train4"), start=1)},
        )
        meta = PAIR_UNIVERSE[:20]
        stat = PAIR_UNIVERSE[:11] + PAIR_UNIVERSE[20:29]
        with tempfile.TemporaryDirectory() as directory:
            result = run_exp01b_v1(
                scientific_inputs=inputs, environment=environment,
                private_checkpoint_root=Path(directory).resolve(),
                meta_ranking=meta, stat_ranking=stat,
                rule_conversion=FormalV4RuleConversionInputV1(
                    authority_hash="9" * 64, executable_pairs=PAIR_UNIVERSE[:50],
                ),
                torch_module=_Torch, trainer=trainer, evaluator=evaluator, confirmer=confirmer,
            )
            public_root = (Path(directory) / "public").resolve()
            write_sanitized_exp01b_outputs_v1(result=result, output_root=public_root)
            self.assertEqual(
                {path.name for path in public_root.iterdir()},
                {
                    "EXP01B_DISPOSITION.json",
                    "EXP01B_CHECKPOINT_SET_RECEIPT.json",
                    "EXP01B_RANKING_RESULTS.csv",
                    "EXP01B_STABILITY_RESULTS.csv",
                    "EXP01B_FUNCTIONAL_RESULTS.csv",
                    "EXP01B_RULE_CONVERSION_RESULTS.csv",
                },
            )
        self.assertEqual(len(calls), 9)
        self.assertEqual(sum(length == 2 for length, _, _ in calls), 3)
        self.assertEqual(result.public_document["run_count"], 9)
        self.assertEqual(result.public_document["test1_accesses"], 0)
        self.assertEqual(result.public_document["label_accesses"], 0)
        self.assertEqual(result.public_document["test2_accesses"], 0)
        self.assertFalse(result.public_document["private_paths_disclosed"])
        self.assertIn(result.disposition.value, {
            "GDN_PRIMARY_AUGMENTATION", "GDN_SUPPORTING_EVIDENCE", "GDN_ABLATION_ONLY",
        })


if __name__ == "__main__":
    unittest.main()
