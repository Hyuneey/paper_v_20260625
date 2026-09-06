"""Successor wiring for the already-frozen production executor assembly."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .dg05_preaccess_kernel_v5 import build_preaccess_frozen_kernel_executor_v5


class DG05V11R1ProductionExecutorError(ValueError):
    pass


def build_frozen_production_executor_v11r1(*, repository_root: Path,
                                            executable_manifest: Any,
                                            detector_registry: Any,
                                            dispatch_registry: Any,
                                            rule_runtime_registry: Any,
                                            rule_sources: dict[tuple[str, str], tuple[Path, Path, Path]]) -> Any:
    """Return the existing validated PRODUCTION executor, never its facade.

    The historic helper is used solely as the frozen asset assembly mechanism.
    Its returned facade is discarded; the V11R1 caller receives the validated
    ``DG05ProductionExecutorV1(authority_mode='PRODUCTION')`` object.
    """
    facade=build_preaccess_frozen_kernel_executor_v5(
        repository_root=repository_root, executable_manifest=executable_manifest,
        detector_registry=detector_registry, dispatch_registry=dispatch_registry,
        rule_runtime_registry=rule_runtime_registry, rule_sources=rule_sources)
    executor=facade.frozen
    executor.validate()
    if executor.authority_mode != "PRODUCTION" or executor.synthetic_failure_cell_ids:
        raise DG05V11R1ProductionExecutorError("V11R1_PRODUCTION_EXECUTOR_REQUIRED")
    return executor
