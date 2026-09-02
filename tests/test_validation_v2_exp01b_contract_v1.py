from __future__ import annotations

import unittest

from paperworks.validation_v2.exp01b_contract_v1 import (
    ComputeBackend,
    Exp01BContractError,
    Exp01BTrainingConfigV1,
    build_environment_freeze_v1,
    preregistration_document_v1,
    validate_environment_schedule_v1,
)


class Exp01BContractTests(unittest.TestCase):
    def _environment(self, *, backend: ComputeBackend = ComputeBackend.CUDA):
        return build_environment_freeze_v1(
            backend=backend,
            python_version="3.12.0",
            torch_version="2.12.1+cu130" if backend is ComputeBackend.CUDA else "2.12.1+cpu",
            cuda_build="13.0" if backend is ComputeBackend.CUDA else "NONE_CPU_BUILD",
            driver_version="610.47",
            gpu_model="NVIDIA GeForce RTX 5060 Laptop GPU" if backend is ComputeBackend.CUDA else "NONE",
            deterministic_flags={"cudnn_benchmark": False, "deterministic_algorithms": True},
            synthetic_smoke_passed=True,
            model_device="cuda" if backend is ComputeBackend.CUDA else "cpu",
            tensor_device="cuda" if backend is ComputeBackend.CUDA else "cpu",
        )

    def test_preregistration_freezes_exact_nine_run_schedule(self) -> None:
        document = preregistration_document_v1()
        self.assertEqual(document["experiment_id"], "EXP-01B-GDN-XAI-V1")
        self.assertEqual(document["run_count"], 9)
        self.assertEqual(document["primary_budget"], 29)
        self.assertFalse(document["post_result_change_allowed"])
        self.assertEqual(document["test_accesses_authorized"], 0)
        self.assertEqual(len(document["preregistration_hash"]), 64)
        self.assertEqual(Exp01BTrainingConfigV1().seeds, (11, 23, 37))

    def test_environment_schedule_rejects_backend_mixing(self) -> None:
        cuda = self._environment()
        schedule = {
            (view, seed): cuda
            for view in ("TRAIN1_TRAIN2_COMBINED", "TRAIN1_ONLY", "TRAIN2_ONLY")
            for seed in (11, 23, 37)
        }
        validate_environment_schedule_v1(schedule)
        schedule[("TRAIN2_ONLY", 37)] = self._environment(backend=ComputeBackend.CPU_FALLBACK)
        with self.assertRaisesRegex(Exp01BContractError, "mix"):
            validate_environment_schedule_v1(schedule)

    def test_cuda_receipt_requires_model_and_tensor_on_cuda(self) -> None:
        with self.assertRaisesRegex(Exp01BContractError, "model and tensors"):
            build_environment_freeze_v1(
                backend=ComputeBackend.CUDA,
                python_version="3.12.0",
                torch_version="2.12.1+cu130",
                cuda_build="13.0",
                driver_version="610.47",
                gpu_model="NVIDIA GeForce RTX 5060 Laptop GPU",
                deterministic_flags={"cudnn_benchmark": False, "deterministic_algorithms": True},
                synthetic_smoke_passed=True,
                model_device="cuda",
                tensor_device="cpu",
            )


if __name__ == "__main__":
    unittest.main()
