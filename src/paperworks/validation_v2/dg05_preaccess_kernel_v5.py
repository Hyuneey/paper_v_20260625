"""Pre-access executor that separates resource authority from method semantics.

The wrapped V1 executor is validated in its exact frozen production-kernel
configuration, including the immutable detector and Rule assets.  This wrapper
only removes protected attack/test discovery capability: callers must provide
an already-authorized projection matrix explicitly.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .dg05_execution_closure_v1 import (
    DG05ExecutableAuthorityManifestV1,
    DG05ProductionExecutorV1,
    DetectorSubauthorityRegistryV1,
    MethodDispatchRegistryV1,
    RuleRuntimeSubauthorityRegistryV1,
)


PREACCESS_EXECUTION_MODE_V5 = "PREACCESS_FROZEN_KERNEL_REHEARSAL"
PREACCESS_DATA_ACCESS_MODE_V5 = "SYNTHETIC_ONLY_NO_PROTECTED_DISCOVERY"


class DG05PreaccessKernelV5Error(ValueError):
    """Raised when a pre-access executor is not the frozen production kernel."""


@dataclass(frozen=True)
class PreaccessFrozenKernelExecutorV5:
    """Capability-reduced facade over an exact frozen production executor."""

    frozen: DG05ProductionExecutorV1
    authority_mode: str = PREACCESS_EXECUTION_MODE_V5
    data_access_mode: str = PREACCESS_DATA_ACCESS_MODE_V5
    protected_access_authorized: bool = False

    def validate(self) -> None:
        if (
            self.authority_mode != PREACCESS_EXECUTION_MODE_V5
            or self.data_access_mode != PREACCESS_DATA_ACCESS_MODE_V5
            or self.protected_access_authorized is not False
            or self.frozen.authority_mode != "PRODUCTION"
            or self.frozen.synthetic_failure_cell_ids
        ):
            raise DG05PreaccessKernelV5Error("PREACCESS_CAPABILITY_SEPARATION_FAILED")
        self.frozen.validate()

    def __getattr__(self, name: str) -> Any:
        if name.startswith("synthetic") or name in {"execute"}:
            raise AttributeError(name)
        return getattr(self.frozen, name)


def build_preaccess_frozen_kernel_executor_v5(
    *,
    repository_root: Path,
    executable_manifest: DG05ExecutableAuthorityManifestV1,
    detector_registry: DetectorSubauthorityRegistryV1,
    dispatch_registry: MethodDispatchRegistryV1,
    rule_runtime_registry: RuleRuntimeSubauthorityRegistryV1,
    rule_sources: dict[tuple[str, str], tuple[Path, Path, Path]],
) -> PreaccessFrozenKernelExecutorV5:
    """Load the existing immutable assets without granting data discovery."""
    from scripts.materialize_dg05_normal_sources_v2 import (
        HISTORICAL_EXECUTOR,
        _detector_assets,
        _rule_assets,
        _vault_root,
    )
    from .dg05_execution_closure_v1 import file_sha256

    vault = _vault_root()
    frozen = DG05ProductionExecutorV1(
        executable_manifest_hash=executable_manifest.document()["self_hash"],
        detector_registry=detector_registry,
        dispatch_registry=dispatch_registry,
        rule_runtime_registry=rule_runtime_registry,
        authority_mode="PRODUCTION",
        detector_assets=_detector_assets(vault, detector_registry),
        rule_assets=_rule_assets(rule_sources),
        fusion_implementation_hash=file_sha256(HISTORICAL_EXECUTOR),
        adapter_implementation_hash=file_sha256(HISTORICAL_EXECUTOR),
        repository_root=repository_root,
        executable_manifest=executable_manifest,
    )
    value = PreaccessFrozenKernelExecutorV5(frozen)
    value.validate()
    return value


__all__ = [
    "DG05PreaccessKernelV5Error",
    "PREACCESS_DATA_ACCESS_MODE_V5",
    "PREACCESS_EXECUTION_MODE_V5",
    "PreaccessFrozenKernelExecutorV5",
    "build_preaccess_frozen_kernel_executor_v5",
]
