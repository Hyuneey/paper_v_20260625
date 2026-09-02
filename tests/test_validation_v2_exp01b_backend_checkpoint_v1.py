from __future__ import annotations

from dataclasses import dataclass
import pickle
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

from paperworks.validation_v2.exp01b_backend_v1 import (
    AttentionArmUnavailableError,
    Exp01BDeviceTrainingConfigV1,
    aggregate_attention_from_augmented_edges_v1,
    aggregate_attention_from_augmented_tensors_v2,
    configure_and_smoke_exp01b_backend_v1,
    disjoint_variant_offset_plan_v1,
    stack_occluded_history_batch_v1,
)
from paperworks.validation_v2.exp01b_contract_v1 import Exp01BTrainingConfigV1
from paperworks.validation_v2.exp01b_checkpoint_v1 import (
    checkpoint_set_receipt_v1,
    persist_private_checkpoint_v1,
)


class _Tensor:
    def __init__(self, values):
        self._values = np.asarray(values, dtype=np.float32)

    def detach(self):
        return self

    def cpu(self):
        return self

    def contiguous(self):
        return self

    def numpy(self):
        return self._values

    @property
    def dtype(self):
        return self._values.dtype

    @property
    def shape(self):
        return self._values.shape


class _Torch:
    @staticmethod
    def save(payload, stream):
        pickle.dump(payload, stream)

    @staticmethod
    def load(stream, **_kwargs):
        return pickle.load(stream)


class _SmokeTensor:
    def __init__(self, device="cuda"): self.device = device
    def reshape(self, *_shape): return self
    def __truediv__(self, _value): return self


class _SmokeLoss:
    def backward(self): self.backward_called = True


class _SmokeModel:
    def __init__(self, *_args): self._device = "cpu"
    def to(self, device): self._device = device; return self
    def parameters(self): return iter((SimpleNamespace(device=self._device),))
    def __call__(self, _x, _edges): return _SmokeTensor(self._device)
    def eval(self): return self


class _SmokeOptimizer:
    def zero_grad(self): pass
    def step(self): pass


class _SmokeMSE:
    def __init__(self, **_kwargs): pass
    def __call__(self, _prediction, _target): return _SmokeLoss()


class _SmokeTorch:
    float32 = "float32"
    long = "long"
    deterministic = False
    backends = SimpleNamespace(
        cudnn=SimpleNamespace(deterministic=False, benchmark=True, allow_tf32=True),
        cuda=SimpleNamespace(matmul=SimpleNamespace(allow_tf32=True)),
    )
    optim = SimpleNamespace(Adam=lambda *_args, **_kwargs: _SmokeOptimizer())
    @classmethod
    def use_deterministic_algorithms(cls, value): cls.deterministic = value
    @classmethod
    def are_deterministic_algorithms_enabled(cls): return cls.deterministic
    @staticmethod
    def arange(*_args, device, dtype): return _SmokeTensor(device)
    @staticmethod
    def tensor(_value, *, dtype, device): return _SmokeTensor(device)
    @staticmethod
    def isfinite(_value): return True


class _SmokeNN:
    MSELoss = _SmokeMSE


class Exp01BBackendCheckpointTests(unittest.TestCase):
    def test_device_adapter_changes_only_frozen_backend(self) -> None:
        cuda = Exp01BDeviceTrainingConfigV1(device="cuda")
        cpu = Exp01BDeviceTrainingConfigV1(device="cpu")
        cuda_doc, cpu_doc = cuda.to_document(), cpu.to_document()
        self.assertEqual({key: value for key, value in cuda_doc.items() if key != "device"},
                         {key: value for key, value in cpu_doc.items() if key != "device"})
        self.assertEqual(cuda.device, "cuda")
        self.assertEqual(cuda.hyperparameter_hash, Exp01BTrainingConfigV1().training_config_hash)
        self.assertEqual(cpu.hyperparameter_hash, Exp01BTrainingConfigV1().training_config_hash)
        self.assertNotEqual(cuda.execution_backend_hash, cpu.execution_backend_hash)

    def test_attention_maps_explicit_augmented_edges_and_excludes_self_loops(self) -> None:
        # Batch 2, graph edges deliberately interleaved with appended self loops.
        mapped = aggregate_attention_from_augmented_edges_v1(
            augmented_edges=((1, 2), (0, 2), (4, 5), (3, 5), (0, 0), (5, 5)),
            alpha_values=(0.2, 0.4, 0.6, 0.8, 99.0, 99.0),
            node_count=3,
            feature_order=("S0", "S1", "T"),
            graph_edges=(("S0", "T"), ("S1", "T")),
            batch_size=2,
        )
        self.assertAlmostEqual(mapped[("S0", "T")], 0.6)
        self.assertAlmostEqual(mapped[("S1", "T")], 0.4)

    def test_vectorized_attention_is_exactly_equivalent_to_explicit_mapping(self) -> None:
        try:
            import torch
        except ImportError:
            self.skipTest("Torch is optional")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        augmented = ((1, 2), (0, 2), (4, 5), (3, 5), (0, 0), (5, 5))
        alpha = (0.2, 0.4, 0.6, 0.8, 99.0, 99.0)
        explicit = aggregate_attention_from_augmented_edges_v1(
            augmented_edges=augmented, alpha_values=alpha,
            node_count=3, feature_order=("S0", "S1", "T"),
            graph_edges=(("S0", "T"), ("S1", "T")), batch_size=2,
        )
        optimized = aggregate_attention_from_augmented_tensors_v2(
            torch_module=torch,
            augmented_edges=torch.tensor(augmented, dtype=torch.long, device=device).T.contiguous(),
            alpha_values=torch.tensor(alpha, dtype=torch.float32, device=device).reshape(-1, 1),
            node_count=3, feature_order=("S0", "S1", "T"),
            graph_edges=(("S0", "T"), ("S1", "T")), batch_size=2,
        )
        for edge in explicit:
            self.assertEqual(optimized[edge], explicit[edge])

        reordered = aggregate_attention_from_augmented_tensors_v2(
            torch_module=torch,
            augmented_edges=torch.tensor(augmented, dtype=torch.long, device=device).T.contiguous(),
            alpha_values=torch.tensor(alpha, dtype=torch.float32, device=device).reshape(-1, 1),
            node_count=3, feature_order=("S0", "S1", "T"),
            graph_edges=(("S1", "T"), ("S0", "T")), batch_size=2,
        )
        self.assertEqual(reordered[("S0", "T")], explicit[("S0", "T")])
        self.assertEqual(reordered[("S1", "T")], explicit[("S1", "T")])

    def test_vectorized_attention_rejects_incomplete_and_nonfinite_edges(self) -> None:
        try:
            import torch
        except ImportError:
            self.skipTest("Torch is optional")
        base = {
            "torch_module": torch,
            "node_count": 3,
            "feature_order": ("S0", "S1", "T"),
            "graph_edges": (("S0", "T"), ("S1", "T")),
            "batch_size": 2,
        }
        with self.assertRaises(AttentionArmUnavailableError):
            aggregate_attention_from_augmented_tensors_v2(
                **base,
                augmented_edges=torch.tensor(((1, 2), (0, 2), (4, 5)), dtype=torch.long).T,
                alpha_values=torch.tensor((0.2, 0.4, 0.6), dtype=torch.float32),
            )
        with self.assertRaises(AttentionArmUnavailableError):
            aggregate_attention_from_augmented_tensors_v2(
                **base,
                augmented_edges=torch.tensor(
                    ((1, 2), (0, 2), (4, 5), (3, 5), (0, 0), (5, 5)), dtype=torch.long,
                ).T,
                alpha_values=torch.tensor(
                    (0.2, float("nan"), 0.6, 0.8, 99.0, 99.0), dtype=torch.float32,
                ),
            )

    def test_full_smoke_enforces_launch_determinism_and_one_train_step(self) -> None:
        config = Exp01BDeviceTrainingConfigV1(device="cuda")
        with patch.dict(
            "os.environ",
            {"CUBLAS_WORKSPACE_CONFIG": ":4096:8", "PYTHONHASHSEED": "0"},
        ), patch(
            "paperworks.validation_v2.exp01b_backend_v1._load_runtime_types_v2",
            return_value=(_SmokeTorch, _SmokeNN, _SmokeModel),
        ), patch(
            "paperworks.validation_v2.exp01b_backend_v1._verify_torch_functional_batch_equivalence_v1",
            return_value=True,
        ):
            receipt = configure_and_smoke_exp01b_backend_v1(
                torch_module=_SmokeTorch, config=config,
            )
        self.assertTrue(receipt["synthetic_smoke_passed"])
        self.assertTrue(receipt["deterministic_algorithms"])
        self.assertFalse(receipt["matmul_tf32"])
        self.assertTrue(receipt["functional_batch_equivalence_passed"])
        self.assertEqual(receipt["scientific_training_config_hash"], Exp01BTrainingConfigV1().training_config_hash)

    def test_disjoint_variant_plan_matches_scalar_graph_evaluation(self) -> None:
        graphs = (
            ((0, 2), (1, 2)),
            ((0, 2),),
        )
        batch = (
            (1.0, 2.0, 0.0),
            (3.0, 4.0, 0.0),
        )
        scalar = [
            [sum(row[source] for source, target in graph if target == 2) for row in batch]
            for graph in graphs
        ]
        offsets = disjoint_variant_offset_plan_v1(variant_count=2, batch_size=2, node_count=3)
        flattened = [value for _variant in range(2) for row in batch for value in row]
        disjoint = []
        for variant, graph in enumerate(graphs):
            values = []
            for offset in offsets[variant]:
                values.append(sum(flattened[offset + source] for source, target in graph if target == 2))
            disjoint.append(values)
        np.testing.assert_allclose(disjoint, scalar, rtol=0.0, atol=0.0)

    def test_stacked_occlusion_matches_scalar_history_variants(self) -> None:
        baseline = np.arange(2 * 3 * 2, dtype=np.float32).reshape(2, 3, 2)
        columns = {0: tuple(float(value) for value in range(10, 16)), 1: tuple(float(value) for value in range(20, 26))}
        stacked = stack_occluded_history_batch_v1(
            baseline_batch=baseline, permuted_source_columns=columns,
            sample_offset=1, window=2,
        )
        expected0 = baseline.copy(); expected0[:, 0, :] = ((11.0, 12.0), (12.0, 13.0))
        expected1 = baseline.copy(); expected1[:, 1, :] = ((21.0, 22.0), (22.0, 23.0))
        np.testing.assert_allclose(stacked[0], expected0, rtol=0.0, atol=0.0)
        np.testing.assert_allclose(stacked[1], expected1, rtol=0.0, atol=0.0)

    def test_atomic_checkpoint_replays_and_set_closes_nine_runs(self) -> None:
        receipts = []
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            for view in ("TRAIN1_TRAIN2_COMBINED", "TRAIN1_ONLY", "TRAIN2_ONLY"):
                for seed in (11, 23, 37):
                    _, receipt = persist_private_checkpoint_v1(
                        torch_module=_Torch, private_root=root,
                        run_id=f"run-{view.lower()}-{seed}", view=view, seed=seed,
                        state_dict={"weight": _Tensor([seed, seed + 1])},
                        training_config_hash="a" * 64,
                        environment_hash="b" * 64,
                        graph_hash="c" * 64,
                    )
                    receipts.append(receipt)
            bundle = checkpoint_set_receipt_v1(receipts)
            self.assertEqual(bundle["checkpoint_count"], 9)
            self.assertFalse(bundle["private_paths_disclosed"])
            self.assertEqual(len(list(root.glob("*.pt"))), 9)


if __name__ == "__main__":
    unittest.main()
