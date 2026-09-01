"""Prospective GDN compute-backend receipt for new VALIDATION V2 executions.

This module does not authorize retraining and is not retrofitted onto completed
EXP-01 checkpoints.  It records the actual backend before a *new* execution so
CPU/GPU numerical differences cannot be hidden behind an unchanged identity.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
import json
import re
from typing import Any, Mapping

from paperworks.gdn.upstream_candidate_backend_v1 import (
    FROZEN_SEEDS,
    UpstreamGDNTrainingConfigV1,
)


_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}\Z")


class GDNComputeEnvironmentError(RuntimeError):
    """Fail-closed compute receipt error."""


def _canonical(document: Mapping[str, Any]) -> bytes:
    return json.dumps(
        dict(document), sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


@dataclass(frozen=True)
class GDNComputeEnvironmentReceiptV2:
    execution_id: str
    code_authority_hash: str
    training_config_hash: str
    compute_device: str
    gpu_model: str
    cuda_version: str
    torch_version: str
    driver_version: str
    seed: tuple[int, ...]
    dtype: str
    deterministic_flags: tuple[tuple[str, bool], ...]
    cuda_available: bool
    cuda_device_count: int
    device_change_safe: bool
    action: str
    backend_identity: str
    receipt_hash: str = ""

    def body_document(self) -> dict[str, Any]:
        return {
            "schema": "paperworks.validation_v2.gdn_compute_environment_receipt_v2",
            "schema_version": "2.0.0",
            "execution_id": self.execution_id,
            "code_authority_hash": self.code_authority_hash,
            "training_config_hash": self.training_config_hash,
            "compute_device": self.compute_device,
            "gpu_model": self.gpu_model,
            "cuda_version": self.cuda_version,
            "torch_version": self.torch_version,
            "driver_version": self.driver_version,
            "seed": list(self.seed),
            "dtype": self.dtype,
            "deterministic_flags": dict(self.deterministic_flags),
            "cuda_available": self.cuda_available,
            "cuda_device_count": self.cuda_device_count,
            "device_change_safe": self.device_change_safe,
            "action": self.action,
            "backend_identity": self.backend_identity,
            "completed_checkpoint_retraining_authorized": False,
            "scientific_configuration_changed": False,
            "test2_accesses": 0,
            "heldout_accesses": 0,
        }

    def to_document(self) -> dict[str, Any]:
        return {**self.body_document(), "receipt_hash": self.receipt_hash}


def build_gdn_compute_environment_receipt_v2(
    *, execution_id: str, code_authority_hash: str,
    config: UpstreamGDNTrainingConfigV1, torch_module: Any,
    driver_version: str = "UNKNOWN_NOT_QUERIED",
) -> GDNComputeEnvironmentReceiptV2:
    """Observe a backend without changing the frozen training configuration."""

    if _TOKEN.fullmatch(execution_id) is None:
        raise GDNComputeEnvironmentError("GDN_COMPUTE_EXECUTION_ID_REJECTED")
    if _HEX64.fullmatch(code_authority_hash) is None:
        raise GDNComputeEnvironmentError("GDN_COMPUTE_CODE_AUTHORITY_REJECTED")
    if type(config) is not UpstreamGDNTrainingConfigV1:
        raise GDNComputeEnvironmentError("GDN_COMPUTE_CONFIG_TYPE_REJECTED")
    if config.device != "cpu":
        raise GDNComputeEnvironmentError("GDN_COMPUTE_FROZEN_DEVICE_CHANGED")
    if type(driver_version) is not str or not driver_version:
        raise GDNComputeEnvironmentError("GDN_COMPUTE_DRIVER_VERSION_REJECTED")

    cuda_available = bool(torch_module.cuda.is_available())
    device_count = int(torch_module.cuda.device_count()) if cuda_available else 0
    gpu_model = (
        str(torch_module.cuda.get_device_name(0))
        if cuda_available and device_count > 0
        else "NONE_AVAILABLE_OR_SELECTED"
    )
    cuda_version_value = getattr(getattr(torch_module, "version", None), "cuda", None)
    cuda_version = "NONE_CPU_BUILD" if cuda_version_value is None else str(cuda_version_value)
    cudnn = getattr(getattr(torch_module, "backends", None), "cudnn", None)
    deterministic_flags = tuple(sorted({
        "cudnn_benchmark": bool(getattr(cudnn, "benchmark", False)),
        "cudnn_deterministic": bool(getattr(cudnn, "deterministic", False)),
        "deterministic_algorithms": bool(torch_module.are_deterministic_algorithms_enabled()),
    }.items()))
    action = (
        "KEEP_FROZEN_CPU_COMPLETED_CHECKPOINTS_NO_RETRAIN_GPU_REQUIRES_NEW_IDENTITY"
        if cuda_available
        else "KEEP_FROZEN_CPU_CUDA_UNAVAILABLE"
    )
    backend_body = {
        "code_authority_hash": code_authority_hash,
        "compute_device": config.device,
        "cuda_version": cuda_version,
        "deterministic_flags": dict(deterministic_flags),
        "driver_version": driver_version,
        "dtype": "float32",
        "execution_id": execution_id,
        "gpu_model": gpu_model,
        "seed": list(FROZEN_SEEDS),
        "torch_version": str(torch_module.__version__),
        "training_config_hash": config.hyperparameter_hash,
    }
    backend_identity = sha256(_canonical(backend_body)).hexdigest()
    provisional = GDNComputeEnvironmentReceiptV2(
        execution_id=execution_id,
        code_authority_hash=code_authority_hash,
        training_config_hash=config.hyperparameter_hash,
        compute_device=config.device,
        gpu_model=gpu_model,
        cuda_version=cuda_version,
        torch_version=str(torch_module.__version__),
        driver_version=driver_version,
        seed=FROZEN_SEEDS,
        dtype="float32",
        deterministic_flags=deterministic_flags,
        cuda_available=cuda_available,
        cuda_device_count=device_count,
        device_change_safe=False,
        action=action,
        backend_identity=backend_identity,
    )
    return replace(
        provisional,
        receipt_hash=sha256(_canonical(provisional.body_document())).hexdigest(),
    )


__all__ = [
    "GDNComputeEnvironmentError",
    "GDNComputeEnvironmentReceiptV2",
    "build_gdn_compute_environment_receipt_v2",
]
