"""Candidate-universe construction and mask utilities."""

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

__all__ = [
    "CandidatePair",
    "CandidatePolicy",
    "CandidateTargetStatus",
    "CandidateUniverseArtifact",
    "CandidateUniverseError",
    "build_candidate_universe",
    "candidate_mask",
    "indexed_candidates_by_target",
]
