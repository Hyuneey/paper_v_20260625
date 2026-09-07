"""Successor wiring for the already-frozen production executor assembly."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .dg05_execution_closure_v1 import DG05ProductionExecutorV1, file_sha256


class DG05V11R1ProductionExecutorError(ValueError):
    pass


def build_frozen_production_executor_v11r1(*, repository_root: Path,
                                            executable_manifest: Any,
                                            detector_registry: Any,
                                            dispatch_registry: Any,
                                            rule_runtime_registry: Any,
                                            rule_sources: dict[tuple[str, str], tuple[Path, Path, Path]]) -> Any:
    """Assemble the existing production executor directly from frozen loaders."""
    from scripts.materialize_dg05_normal_sources_v2 import (
        HISTORICAL_EXECUTOR, _detector_assets, _rule_assets, _vault_root,
    )
    executor = DG05ProductionExecutorV1(
        executable_manifest_hash=executable_manifest.document()["self_hash"],
        detector_registry=detector_registry, dispatch_registry=dispatch_registry,
        rule_runtime_registry=rule_runtime_registry, authority_mode="PRODUCTION",
        detector_assets=_detector_assets(_vault_root(), detector_registry),
        rule_assets=_rule_assets(rule_sources),
        fusion_implementation_hash=file_sha256(HISTORICAL_EXECUTOR),
        adapter_implementation_hash=file_sha256(HISTORICAL_EXECUTOR),
        repository_root=repository_root, executable_manifest=executable_manifest,
    )
    executor.validate()
    if executor.authority_mode != "PRODUCTION" or executor.synthetic_failure_cell_ids:
        raise DG05V11R1ProductionExecutorError("V11R1_PRODUCTION_EXECUTOR_REQUIRED")
    return executor
