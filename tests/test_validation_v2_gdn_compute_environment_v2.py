from __future__ import annotations

from types import SimpleNamespace
import unittest

from paperworks.gdn.upstream_candidate_backend_v1 import UpstreamGDNTrainingConfigV1
from paperworks.validation_v2.gdn_compute_environment_v2 import (
    GDNComputeEnvironmentError,
    build_gdn_compute_environment_receipt_v2,
)


class _Cuda:
    def __init__(self, available: bool) -> None:
        self.available = available

    def is_available(self) -> bool:
        return self.available

    def device_count(self) -> int:
        return 1 if self.available else 0

    def get_device_name(self, _index: int) -> str:
        return "SYNTHETIC GPU"


def _torch(available: bool):
    return SimpleNamespace(
        __version__="2.12.1+cpu" if not available else "2.12.1+cu130",
        version=SimpleNamespace(cuda=None if not available else "13.0"),
        cuda=_Cuda(available),
        backends=SimpleNamespace(cudnn=SimpleNamespace(deterministic=True, benchmark=False)),
        are_deterministic_algorithms_enabled=lambda: True,
    )


class ValidationV2GDNComputeEnvironmentTests(unittest.TestCase):
    def test_cpu_receipt_records_required_metadata_without_authorizing_retrain(self) -> None:
        receipt = build_gdn_compute_environment_receipt_v2(
            execution_id="V2-EXP01-NEXT",
            code_authority_hash="a" * 64,
            config=UpstreamGDNTrainingConfigV1(),
            torch_module=_torch(False),
        )
        document = receipt.to_document()
        self.assertEqual(document["compute_device"], "cpu")
        self.assertEqual(document["seed"], [11, 23, 37])
        self.assertEqual(document["dtype"], "float32")
        self.assertFalse(document["completed_checkpoint_retraining_authorized"])
        self.assertFalse(document["device_change_safe"])
        self.assertIn("CUDA_UNAVAILABLE", document["action"])

    def test_visible_gpu_does_not_silently_change_frozen_backend(self) -> None:
        receipt = build_gdn_compute_environment_receipt_v2(
            execution_id="V2-EXP01-NEXT",
            code_authority_hash="b" * 64,
            config=UpstreamGDNTrainingConfigV1(),
            torch_module=_torch(True),
            driver_version="610.47",
        )
        self.assertEqual(receipt.compute_device, "cpu")
        self.assertEqual(receipt.gpu_model, "SYNTHETIC GPU")
        self.assertIn("NEW_IDENTITY", receipt.action)
        self.assertFalse(receipt.device_change_safe)

    def test_invalid_identity_fails_closed(self) -> None:
        with self.assertRaisesRegex(GDNComputeEnvironmentError, "EXECUTION_ID"):
            build_gdn_compute_environment_receipt_v2(
                execution_id="contains space",
                code_authority_hash="a" * 64,
                config=UpstreamGDNTrainingConfigV1(),
                torch_module=_torch(False),
            )


if __name__ == "__main__":
    unittest.main()
