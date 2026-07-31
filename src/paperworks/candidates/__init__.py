"""Candidate-universe construction and mask utilities."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from paperworks.candidates.universe import (
    CandidatePair,
    CandidatePolicy,
    CandidateTargetStatus,
    CandidateUniverseArtifact,
    CandidateUniverseError,
    build_candidate_universe,
    candidate_mask,
    indexed_candidates_by_target,
)
_SMOKE_EXPORTS = frozenset(
    {
        "CandidateSmokeError",
        "CandidateSmokeReport",
        "run_task005_smoke",
        "validate_task005_smoke_report",
    }
)


def __getattr__(name: str) -> Any:
    if name not in _SMOKE_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module("paperworks.candidates.smoke")
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | _SMOKE_EXPORTS)

__all__ = [
    "CandidatePair",
    "CandidatePolicy",
    "CandidateTargetStatus",
    "CandidateUniverseArtifact",
    "CandidateUniverseError",
    "CandidateSmokeError",
    "CandidateSmokeReport",
    "build_candidate_universe",
    "candidate_mask",
    "indexed_candidates_by_target",
    "run_task005_smoke",
    "validate_task005_smoke_report",
]
