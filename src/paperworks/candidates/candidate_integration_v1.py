"""TASK-039C three-arm candidate integration contracts and pure builders.

This module consumes frozen public arm results. It never opens HAI data or
private ledgers and delegates the actual set union to the C0-frozen
integrate_candidate_union_v1 helper.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from paperworks.v6.candidate_discovery_protocol_v1 import (
    ArmCandidateV1,
    CandidateUniversePolicyV1,
    integrate_candidate_union_v1,
)


SCHEMA_VERSION = "1.0.0"
TASK_ID = "TASK-039C-INTEGRATE"
PASS_STATUS = "passed_task039c_three_arm_candidate_cohort_freeze"
ARMS = ("META", "STAT", "GDN")
PRIMARY_K = 20
EXPECTED_PREVIEW_HASH = (
    "81a7b6e0dfffdd6ce1b49799721c3dfcfb484af247a194d87b0602e76ac551ff"
)
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
GIT_SHA_RE = re.compile(r"^[a-f0-9]{40}$")
ABSOLUTE_PATH_RE = re.compile(
    r"(?:[A-Za-z]:[\\/]|/home/|/Users/|\\\\[^\\]+\\[^\\]+)",
    re.IGNORECASE,
)


class CandidateIntegrationError(ValueError):
    """Raised when a frozen integration or authority boundary is violated."""


def stable_hash_v1(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _require_sha256(value: str, label: str) -> None:
    if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
        raise CandidateIntegrationError(f"{label} must be SHA-256")


def _require_git_sha(value: str, label: str) -> None:
    if not isinstance(value, str) or GIT_SHA_RE.fullmatch(value) is None:
        raise CandidateIntegrationError(f"{label} must be a Git SHA")


def _require_finite(value: float, label: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CandidateIntegrationError(f"{label} must be numeric")
    if not math.isfinite(float(value)):
        raise CandidateIntegrationError(f"{label} must be finite")


def _reject_unknown(data: Mapping[str, Any], expected: set[str], label: str) -> None:
    unknown = set(data) - expected
    missing = expected - set(data)
    if unknown or missing:
        raise CandidateIntegrationError(
            f"{label} fields differ: missing={sorted(missing)} unknown={sorted(unknown)}"
        )


def _hashed(payload: Mapping[str, Any]) -> dict[str, Any]:
    document = dict(payload)
    document["artifact_hash"] = stable_hash_v1(document)
    return document


def _verify_hashed(data: Mapping[str, Any], label: str) -> dict[str, Any]:
    payload = dict(data)
    try:
        supplied = payload.pop("artifact_hash")
    except KeyError as exc:
        raise CandidateIntegrationError(f"{label} lacks artifact_hash") from exc
    _require_sha256(str(supplied), f"{label} artifact_hash")
    if supplied != stable_hash_v1(payload):
        raise CandidateIntegrationError(f"{label} self-hash mismatch")
    return payload


def assert_public_payload_v1(value: Any) -> None:
    """Reject absolute paths and raw/private payload vocabulary recursively."""

    prohibited_keys = {
        "raw_rows",
        "raw_windows",
        "raw_time_series",
        "node_embeddings",
        "checkpoint",
        "state_dict",
        "private_ledger_contents",
        "attack_details",
        "label_values",
    }

    def visit(item: Any) -> None:
        if isinstance(item, Mapping):
            if prohibited_keys & set(item):
                raise CandidateIntegrationError("public payload contains prohibited key")
            for key, child in item.items():
                visit(key)
                visit(child)
        elif isinstance(item, (list, tuple)):
            for child in item:
                visit(child)
        elif isinstance(item, str) and ABSOLUTE_PATH_RE.search(item):
            raise CandidateIntegrationError("public payload contains an absolute path")
        elif isinstance(item, float) and not math.isfinite(item):
            raise CandidateIntegrationError("public payload contains non-finite number")

    visit(value)


@dataclass(frozen=True)
class TASK039CArmBindingV1:
    arm_id: str
    claim_boundary: str
    implementation_commit: str
    result_commit: str
    result_artifact_hash: str
    ranking_hash: str | None
    policy_hash: str
    evidence_binding_hashes: tuple[str, ...]
    data_access_audit_hash: str
    evaluated_count: int
    supported_count: int
    top20_count: int
    br2_pair_supervision_used: bool = False
    cross_arm_score_used: bool = False

    ARTIFACT_TYPE = "task039c_arm_binding_v1"

    def __post_init__(self) -> None:
        if self.arm_id not in ARMS:
            raise CandidateIntegrationError("unknown arm")
        if self.claim_boundary not in {
            "metadata candidate evidence",
            "lagged change-correlation candidate evidence",
            "learned-graph candidate evidence",
        }:
            raise CandidateIntegrationError("unknown arm claim boundary")
        _require_git_sha(self.implementation_commit, "implementation commit")
        _require_git_sha(self.result_commit, "result commit")
        for label, value in (
            ("result hash", self.result_artifact_hash),
            ("policy hash", self.policy_hash),
            ("access hash", self.data_access_audit_hash),
        ):
            _require_sha256(value, label)
        if self.ranking_hash is not None:
            _require_sha256(self.ranking_hash, "ranking hash")
        if not self.evidence_binding_hashes:
            raise CandidateIntegrationError("arm evidence bindings are empty")
        for value in self.evidence_binding_hashes:
            _require_sha256(value, "arm evidence binding")
        if (
            self.evaluated_count != 144
            or self.supported_count < 20
            or self.top20_count != 20
            or self.br2_pair_supervision_used
            or self.cross_arm_score_used
        ):
            raise CandidateIntegrationError("arm binding boundary changed")

    def _payload(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "artifact_type": self.ARTIFACT_TYPE,
            "arm_id": self.arm_id,
            "claim_boundary": self.claim_boundary,
            "implementation_commit": self.implementation_commit,
            "result_commit": self.result_commit,
            "result_artifact_hash": self.result_artifact_hash,
            "ranking_hash": self.ranking_hash,
            "policy_hash": self.policy_hash,
            "evidence_binding_hashes": list(self.evidence_binding_hashes),
            "data_access_audit_hash": self.data_access_audit_hash,
            "evaluated_count": self.evaluated_count,
            "supported_count": self.supported_count,
            "top20_count": self.top20_count,
            "br2_pair_supervision_used": self.br2_pair_supervision_used,
            "cross_arm_score_used": self.cross_arm_score_used,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._payload())

    def to_dict(self) -> dict[str, Any]:
        return _hashed(self._payload())

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "TASK039CArmBindingV1":
        payload = _verify_hashed(data, cls.ARTIFACT_TYPE)
        expected = {
            "schema_version", "artifact_type", "arm_id", "claim_boundary",
            "implementation_commit", "result_commit", "result_artifact_hash",
            "ranking_hash", "policy_hash", "evidence_binding_hashes",
            "data_access_audit_hash", "evaluated_count", "supported_count",
            "top20_count", "br2_pair_supervision_used", "cross_arm_score_used",
        }
        _reject_unknown(payload, expected, cls.ARTIFACT_TYPE)
        if payload["schema_version"] != SCHEMA_VERSION or payload["artifact_type"] != cls.ARTIFACT_TYPE:
            raise CandidateIntegrationError("arm binding identity changed")
        return cls(
            arm_id=str(payload["arm_id"]),
            claim_boundary=str(payload["claim_boundary"]),
            implementation_commit=str(payload["implementation_commit"]),
            result_commit=str(payload["result_commit"]),
            result_artifact_hash=str(payload["result_artifact_hash"]),
            ranking_hash=None if payload["ranking_hash"] is None else str(payload["ranking_hash"]),
            policy_hash=str(payload["policy_hash"]),
            evidence_binding_hashes=tuple(str(x) for x in payload["evidence_binding_hashes"]),
            data_access_audit_hash=str(payload["data_access_audit_hash"]),
            evaluated_count=int(payload["evaluated_count"]),
            supported_count=int(payload["supported_count"]),
            top20_count=int(payload["top20_count"]),
            br2_pair_supervision_used=bool(payload["br2_pair_supervision_used"]),
            cross_arm_score_used=bool(payload["cross_arm_score_used"]),
        )


@dataclass(frozen=True)
class OverlapBudgetV1:
    meta_count: int
    stat_count: int
    gdn_count: int
    meta_stat: int
    meta_gdn: int
    stat_gdn: int
    triple: int
    meta_only: int
    stat_only: int
    gdn_only: int
    meta_stat_only: int
    meta_gdn_only: int
    stat_gdn_only: int
    all_three: int
    union_count: int

    def to_dict(self) -> dict[str, int]:
        return {
            "meta_count": self.meta_count,
            "stat_count": self.stat_count,
            "gdn_count": self.gdn_count,
            "meta_stat": self.meta_stat,
            "meta_gdn": self.meta_gdn,
            "stat_gdn": self.stat_gdn,
            "triple": self.triple,
            "meta_only": self.meta_only,
            "stat_only": self.stat_only,
            "gdn_only": self.gdn_only,
            "meta_stat_only": self.meta_stat_only,
            "meta_gdn_only": self.meta_gdn_only,
            "stat_gdn_only": self.stat_gdn_only,
            "all_three": self.all_three,
            "union_count": self.union_count,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "OverlapBudgetV1":
        _reject_unknown(data, set(cls.__dataclass_fields__), "overlap budget")
        return cls(**{key: int(data[key]) for key in cls.__dataclass_fields__})


@dataclass(frozen=True)
class TASK039CThreeArmOverlapV1:
    top10: OverlapBudgetV1
    top20: OverlapBudgetV1
    sensitivity: OverlapBudgetV1
    top10_meta_stat_only_pairs: tuple[tuple[str, str], ...]
    top10_meta_gdn_only_pairs: tuple[tuple[str, str], ...]
    top10_stat_gdn_only_pairs: tuple[tuple[str, str], ...]
    sensitivity_meta_available_count: int = 30
    sensitivity_stat_count: int = 40
    sensitivity_gdn_available_count: int = 39
    meta_padded: bool = False
    gdn_padded: bool = False
    sensitivity_is_primary_cohort: bool = False

    ARTIFACT_TYPE = "task039c_three_arm_overlap_v1"

    def __post_init__(self) -> None:
        if self.top10.to_dict() != {
            "meta_count": 10, "stat_count": 10, "gdn_count": 10,
            "meta_stat": 1, "meta_gdn": 1, "stat_gdn": 0, "triple": 0,
            "meta_only": 8, "stat_only": 9, "gdn_only": 9,
            "meta_stat_only": 1, "meta_gdn_only": 1, "stat_gdn_only": 0,
            "all_three": 0, "union_count": 28,
        }:
            raise CandidateIntegrationError("top10 overlap mismatch")
        if self.top20.to_dict() != {
            "meta_count": 20, "stat_count": 20, "gdn_count": 20,
            "meta_stat": 11, "meta_gdn": 1, "stat_gdn": 1, "triple": 0,
            "meta_only": 8, "stat_only": 8, "gdn_only": 18,
            "meta_stat_only": 11, "meta_gdn_only": 1, "stat_gdn_only": 1,
            "all_three": 0, "union_count": 47,
        }:
            raise CandidateIntegrationError("top20 overlap mismatch")
        if (
            self.sensitivity.meta_count != 30
            or self.sensitivity.stat_count != 40
            or self.sensitivity.gdn_count != 39
            or self.sensitivity.meta_stat != 24
            or self.sensitivity.meta_gdn != 7
            or self.sensitivity.stat_gdn != 5
            or self.sensitivity.triple != 3
            or self.sensitivity.meta_only != 2
            or self.sensitivity.stat_only != 14
            or self.sensitivity.gdn_only != 30
            or self.sensitivity.union_count != 76
        ):
            raise CandidateIntegrationError("sensitivity overlap mismatch")
        if (
            self.top10_meta_stat_only_pairs != (("P1_FCV01D", "P1_FT02Z"),)
            or self.top10_meta_gdn_only_pairs != (("P1_FCV02D", "P1_TIT01"),)
            or self.top10_stat_gdn_only_pairs
            or self.meta_padded
            or self.gdn_padded
            or self.sensitivity_is_primary_cohort
        ):
            raise CandidateIntegrationError("overlap interpretation changed")

    def _payload(self) -> dict[str, Any]:
        pairs = lambda values: [{"source": a, "target": b} for a, b in values]
        return {
            "schema_version": SCHEMA_VERSION,
            "artifact_type": self.ARTIFACT_TYPE,
            "top10": self.top10.to_dict(),
            "top20": self.top20.to_dict(),
            "sensitivity": self.sensitivity.to_dict(),
            "top10_exactly_two_pairs": {
                "META_STAT": pairs(self.top10_meta_stat_only_pairs),
                "META_GDN": pairs(self.top10_meta_gdn_only_pairs),
                "STAT_GDN": pairs(self.top10_stat_gdn_only_pairs),
            },
            "sensitivity_arm_counts": {
                "META_available": self.sensitivity_meta_available_count,
                "STAT": self.sensitivity_stat_count,
                "GDN_available": self.sensitivity_gdn_available_count,
            },
            "meta_padded": self.meta_padded,
            "gdn_padded": self.gdn_padded,
            "sensitivity_is_primary_cohort": self.sensitivity_is_primary_cohort,
            "interpretation": (
                "descriptive overlap only; overlap is not correctness, quality, "
                "method superiority, or a selection rule"
            ),
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._payload())

    def to_dict(self) -> dict[str, Any]:
        return _hashed(self._payload())

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "TASK039CThreeArmOverlapV1":
        payload = _verify_hashed(data, cls.ARTIFACT_TYPE)
        expected = {
            "schema_version", "artifact_type", "top10", "top20",
            "sensitivity", "top10_exactly_two_pairs",
            "sensitivity_arm_counts", "meta_padded", "gdn_padded",
            "sensitivity_is_primary_cohort", "interpretation",
        }
        _reject_unknown(payload, expected, cls.ARTIFACT_TYPE)
        if payload["schema_version"] != SCHEMA_VERSION or payload["artifact_type"] != cls.ARTIFACT_TYPE:
            raise CandidateIntegrationError("overlap identity changed")
        pair_groups = payload["top10_exactly_two_pairs"]
        _reject_unknown(pair_groups, {"META_STAT", "META_GDN", "STAT_GDN"}, "overlap pairs")
        counts = payload["sensitivity_arm_counts"]
        _reject_unknown(counts, {"META_available", "STAT", "GDN_available"}, "sensitivity counts")
        pairs = lambda values: tuple((str(x["source"]), str(x["target"])) for x in values)
        return cls(
            top10=OverlapBudgetV1.from_dict(payload["top10"]),
            top20=OverlapBudgetV1.from_dict(payload["top20"]),
            sensitivity=OverlapBudgetV1.from_dict(payload["sensitivity"]),
            top10_meta_stat_only_pairs=pairs(pair_groups["META_STAT"]),
            top10_meta_gdn_only_pairs=pairs(pair_groups["META_GDN"]),
            top10_stat_gdn_only_pairs=pairs(pair_groups["STAT_GDN"]),
            sensitivity_meta_available_count=int(counts["META_available"]),
            sensitivity_stat_count=int(counts["STAT"]),
            sensitivity_gdn_available_count=int(counts["GDN_available"]),
            meta_padded=bool(payload["meta_padded"]),
            gdn_padded=bool(payload["gdn_padded"]),
            sensitivity_is_primary_cohort=bool(payload["sensitivity_is_primary_cohort"]),
        )


@dataclass(frozen=True)
class CandidateProfilingEntryV1:
    source: str
    target: str
    candidate_universe_hash: str
    origin_arms: tuple[str, ...]
    serialization_position: int
    meta_evidence: Mapping[str, Any] | None
    stat_evidence: Mapping[str, Any] | None
    gdn_evidence: Mapping[str, Any] | None
    global_rank: None = None
    global_score: None = None
    serialization_order_is_scientific_rank: bool = False
    relation_confirmation: str = "not_evaluated"
    rule_status: str = "not_created"

    ARTIFACT_TYPE = "candidate_profiling_entry_v1"

    def __post_init__(self) -> None:
        _require_sha256(self.candidate_universe_hash, "candidate universe hash")
        if not self.source or not self.target or self.serialization_position < 1:
            raise CandidateIntegrationError("invalid candidate identity or position")
        if not self.origin_arms or any(x not in ARMS for x in self.origin_arms):
            raise CandidateIntegrationError("invalid candidate origins")
        if tuple(x for x in ARMS if x in self.origin_arms) != self.origin_arms:
            raise CandidateIntegrationError("candidate origin order changed")
        evidence = {
            "META": self.meta_evidence,
            "STAT": self.stat_evidence,
            "GDN": self.gdn_evidence,
        }
        if any((arm in self.origin_arms) != (value is not None) for arm, value in evidence.items()):
            raise CandidateIntegrationError("candidate evidence does not match origins")
        if (
            self.global_rank is not None
            or self.global_score is not None
            or self.serialization_order_is_scientific_rank
            or self.relation_confirmation != "not_evaluated"
            or self.rule_status != "not_created"
        ):
            raise CandidateIntegrationError("candidate claim boundary changed")
        for value in evidence.values():
            if value is not None:
                assert_public_payload_v1(value)
        object.__setattr__(
            self,
            "meta_evidence",
            None if self.meta_evidence is None else MappingProxyType(dict(self.meta_evidence)),
        )
        object.__setattr__(
            self,
            "stat_evidence",
            None if self.stat_evidence is None else MappingProxyType(dict(self.stat_evidence)),
        )
        object.__setattr__(
            self,
            "gdn_evidence",
            None if self.gdn_evidence is None else MappingProxyType(dict(self.gdn_evidence)),
        )

    def _payload(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "artifact_type": self.ARTIFACT_TYPE,
            "source": self.source,
            "target": self.target,
            "candidate_universe_hash": self.candidate_universe_hash,
            "origin_arms": list(self.origin_arms),
            "serialization_position": self.serialization_position,
            "global_rank": self.global_rank,
            "global_score": self.global_score,
            "serialization_order_is_scientific_rank": self.serialization_order_is_scientific_rank,
            "relation_confirmation": self.relation_confirmation,
            "rule_status": self.rule_status,
            "META": None if self.meta_evidence is None else dict(self.meta_evidence),
            "STAT": None if self.stat_evidence is None else dict(self.stat_evidence),
            "GDN": None if self.gdn_evidence is None else dict(self.gdn_evidence),
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._payload())

    def to_dict(self) -> dict[str, Any]:
        return _hashed(self._payload())

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CandidateProfilingEntryV1":
        payload = _verify_hashed(data, cls.ARTIFACT_TYPE)
        expected = {
            "schema_version", "artifact_type", "source", "target",
            "candidate_universe_hash", "origin_arms", "serialization_position",
            "global_rank", "global_score",
            "serialization_order_is_scientific_rank", "relation_confirmation",
            "rule_status", "META", "STAT", "GDN",
        }
        _reject_unknown(payload, expected, cls.ARTIFACT_TYPE)
        if payload["schema_version"] != SCHEMA_VERSION or payload["artifact_type"] != cls.ARTIFACT_TYPE:
            raise CandidateIntegrationError("entry identity changed")
        return cls(
            source=str(payload["source"]),
            target=str(payload["target"]),
            candidate_universe_hash=str(payload["candidate_universe_hash"]),
            origin_arms=tuple(str(x) for x in payload["origin_arms"]),
            serialization_position=int(payload["serialization_position"]),
            meta_evidence=payload["META"],
            stat_evidence=payload["STAT"],
            gdn_evidence=payload["GDN"],
            global_rank=payload["global_rank"],
            global_score=payload["global_score"],
            serialization_order_is_scientific_rank=bool(payload["serialization_order_is_scientific_rank"]),
            relation_confirmation=str(payload["relation_confirmation"]),
            rule_status=str(payload["rule_status"]),
        )


@dataclass(frozen=True)
class CandidateProfilingCohortV1:
    c0_protocol_bundle_hash: str
    common_universe_hash: str
    source_identity_hash: str
    target_identity_hash: str
    arm_bindings: tuple[TASK039CArmBindingV1, ...]
    top20_overlap: OverlapBudgetV1
    candidates: tuple[CandidateProfilingEntryV1, ...]
    candidate_identity_list: tuple[tuple[str, str], ...]
    candidate_identity_list_hash: str
    final_gdn_audit_commit: str
    final_gdn_audit_hash: str
    status: str = PASS_STATUS
    task_id: str = TASK_ID
    selected_process: str = "P1"
    selected_process_name: str = "P1 Boiler"
    relation_family: str = "continuous_step_delayed_response_v1"
    primary_k: int = PRIMARY_K
    included_arms: tuple[str, ...] = ARMS
    provenance_complete: bool = True
    global_numerical_score_created: bool = False
    global_scientific_rank_created: bool = False
    br2_relation_outcomes_used: bool = False
    hai_feature_values_accessed_by_integration: bool = False
    private_ledgers_accessed_by_integration: bool = False
    relation_profiling_executed: bool = False

    ARTIFACT_TYPE = "candidate_profiling_cohort_v1"

    def __post_init__(self) -> None:
        for value in (
            self.c0_protocol_bundle_hash,
            self.common_universe_hash,
            self.source_identity_hash,
            self.target_identity_hash,
            self.candidate_identity_list_hash,
            self.final_gdn_audit_hash,
        ):
            _require_sha256(value, "cohort binding")
        _require_git_sha(self.final_gdn_audit_commit, "final GDN audit commit")
        if (
            self.status != PASS_STATUS
            or self.task_id != TASK_ID
            or self.selected_process != "P1"
            or self.selected_process_name != "P1 Boiler"
            or self.relation_family != "continuous_step_delayed_response_v1"
            or self.primary_k != 20
            or self.included_arms != ARMS
            or tuple(x.arm_id for x in self.arm_bindings) != ARMS
            or len(self.candidates) != 47
            or len(self.candidate_identity_list) != 47
            or len(set(self.candidate_identity_list)) != 47
            or self.top20_overlap.union_count != 47
        ):
            raise CandidateIntegrationError("candidate cohort identity changed")
        if tuple((x.source, x.target) for x in self.candidates) != self.candidate_identity_list:
            raise CandidateIntegrationError("identity list does not match cohort order")
        identity_payload = {
            "artifact_type": "candidate_profiling_identity_list_v1",
            "identities": [
                {"source": source, "target": target}
                for source, target in self.candidate_identity_list
            ],
        }
        if stable_hash_v1(identity_payload) != self.candidate_identity_list_hash:
            raise CandidateIntegrationError("candidate identity-list hash mismatch")
        if tuple(x.serialization_position for x in self.candidates) != tuple(range(1, 48)):
            raise CandidateIntegrationError("serialization positions are not contiguous")
        if (
            not self.provenance_complete
            or self.global_numerical_score_created
            or self.global_scientific_rank_created
            or self.br2_relation_outcomes_used
            or self.hai_feature_values_accessed_by_integration
            or self.private_ledgers_accessed_by_integration
            or self.relation_profiling_executed
        ):
            raise CandidateIntegrationError("candidate cohort authority changed")

    def _payload(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "artifact_type": self.ARTIFACT_TYPE,
            "task_id": self.task_id,
            "status": self.status,
            "selected_process": self.selected_process,
            "selected_process_name": self.selected_process_name,
            "relation_family": self.relation_family,
            "c0_protocol_bundle_hash": self.c0_protocol_bundle_hash,
            "common_universe_hash": self.common_universe_hash,
            "source_identity_hash": self.source_identity_hash,
            "target_identity_hash": self.target_identity_hash,
            "primary_k": self.primary_k,
            "included_arms": list(self.included_arms),
            "arm_bindings": [x.to_dict() for x in self.arm_bindings],
            "top20_counts_by_arm": {"META": 20, "STAT": 20, "GDN": 20},
            "pairwise_intersections": {
                "META_STAT": self.top20_overlap.meta_stat,
                "META_GDN": self.top20_overlap.meta_gdn,
                "STAT_GDN": self.top20_overlap.stat_gdn,
            },
            "triple_intersection": self.top20_overlap.triple,
            "origin_decomposition": {
                "META_only": self.top20_overlap.meta_only,
                "STAT_only": self.top20_overlap.stat_only,
                "GDN_only": self.top20_overlap.gdn_only,
                "META_STAT_only": self.top20_overlap.meta_stat_only,
                "META_GDN_only": self.top20_overlap.meta_gdn_only,
                "STAT_GDN_only": self.top20_overlap.stat_gdn_only,
                "all_three": self.top20_overlap.all_three,
            },
            "union_count": len(self.candidates),
            "candidates": [x.to_dict() for x in self.candidates],
            "candidate_identity_list": [
                {"source": source, "target": target}
                for source, target in self.candidate_identity_list
            ],
            "candidate_identity_list_hash": self.candidate_identity_list_hash,
            "final_gdn_audit_commit": self.final_gdn_audit_commit,
            "final_gdn_audit_hash": self.final_gdn_audit_hash,
            "provenance_complete": self.provenance_complete,
            "global_numerical_score_created": self.global_numerical_score_created,
            "global_scientific_rank_created": self.global_scientific_rank_created,
            "br2_relation_outcomes_used": self.br2_relation_outcomes_used,
            "hai_feature_values_accessed_by_integration": self.hai_feature_values_accessed_by_integration,
            "private_ledgers_accessed_by_integration": self.private_ledgers_accessed_by_integration,
            "relation_profiling_executed": self.relation_profiling_executed,
            "claim_boundary": "candidate profiling cohort",
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._payload())

    def to_dict(self) -> dict[str, Any]:
        document = _hashed(self._payload())
        assert_public_payload_v1(document)
        return document

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CandidateProfilingCohortV1":
        payload = _verify_hashed(data, cls.ARTIFACT_TYPE)
        expected = {
            "schema_version", "artifact_type", "task_id", "status",
            "selected_process", "selected_process_name", "relation_family",
            "c0_protocol_bundle_hash", "common_universe_hash",
            "source_identity_hash", "target_identity_hash", "primary_k",
            "included_arms", "arm_bindings", "top20_counts_by_arm",
            "pairwise_intersections", "triple_intersection",
            "origin_decomposition", "union_count", "candidates",
            "candidate_identity_list", "candidate_identity_list_hash",
            "final_gdn_audit_commit", "final_gdn_audit_hash",
            "provenance_complete", "global_numerical_score_created",
            "global_scientific_rank_created", "br2_relation_outcomes_used",
            "hai_feature_values_accessed_by_integration",
            "private_ledgers_accessed_by_integration",
            "relation_profiling_executed", "claim_boundary",
        }
        _reject_unknown(payload, expected, cls.ARTIFACT_TYPE)
        if payload["schema_version"] != SCHEMA_VERSION or payload["artifact_type"] != cls.ARTIFACT_TYPE:
            raise CandidateIntegrationError("cohort identity changed")
        pairwise = payload["pairwise_intersections"]
        decomposition = payload["origin_decomposition"]
        top20 = OverlapBudgetV1(
            meta_count=int(payload["top20_counts_by_arm"]["META"]),
            stat_count=int(payload["top20_counts_by_arm"]["STAT"]),
            gdn_count=int(payload["top20_counts_by_arm"]["GDN"]),
            meta_stat=int(pairwise["META_STAT"]),
            meta_gdn=int(pairwise["META_GDN"]),
            stat_gdn=int(pairwise["STAT_GDN"]),
            triple=int(payload["triple_intersection"]),
            meta_only=int(decomposition["META_only"]),
            stat_only=int(decomposition["STAT_only"]),
            gdn_only=int(decomposition["GDN_only"]),
            meta_stat_only=int(decomposition["META_STAT_only"]),
            meta_gdn_only=int(decomposition["META_GDN_only"]),
            stat_gdn_only=int(decomposition["STAT_GDN_only"]),
            all_three=int(decomposition["all_three"]),
            union_count=int(payload["union_count"]),
        )
        return cls(
            c0_protocol_bundle_hash=str(payload["c0_protocol_bundle_hash"]),
            common_universe_hash=str(payload["common_universe_hash"]),
            source_identity_hash=str(payload["source_identity_hash"]),
            target_identity_hash=str(payload["target_identity_hash"]),
            arm_bindings=tuple(TASK039CArmBindingV1.from_dict(x) for x in payload["arm_bindings"]),
            top20_overlap=top20,
            candidates=tuple(CandidateProfilingEntryV1.from_dict(x) for x in payload["candidates"]),
            candidate_identity_list=tuple((str(x["source"]), str(x["target"])) for x in payload["candidate_identity_list"]),
            candidate_identity_list_hash=str(payload["candidate_identity_list_hash"]),
            final_gdn_audit_commit=str(payload["final_gdn_audit_commit"]),
            final_gdn_audit_hash=str(payload["final_gdn_audit_hash"]),
            status=str(payload["status"]),
            task_id=str(payload["task_id"]),
            selected_process=str(payload["selected_process"]),
            selected_process_name=str(payload["selected_process_name"]),
            relation_family=str(payload["relation_family"]),
            primary_k=int(payload["primary_k"]),
            included_arms=tuple(str(x) for x in payload["included_arms"]),
            provenance_complete=bool(payload["provenance_complete"]),
            global_numerical_score_created=bool(payload["global_numerical_score_created"]),
            global_scientific_rank_created=bool(payload["global_scientific_rank_created"]),
            br2_relation_outcomes_used=bool(payload["br2_relation_outcomes_used"]),
            hai_feature_values_accessed_by_integration=bool(payload["hai_feature_values_accessed_by_integration"]),
            private_ledgers_accessed_by_integration=bool(payload["private_ledgers_accessed_by_integration"]),
            relation_profiling_executed=bool(payload["relation_profiling_executed"]),
        )


@dataclass(frozen=True)
class TASK039D0AuthorizationV1:
    candidate_cohort_hash: str
    candidate_identity_list_hash: str
    candidate_count: int = 47
    process: str = "P1"
    relation_family: str = "continuous_step_delayed_response_v1"
    source_arm_set: tuple[str, ...] = ARMS
    protocol_design_authorized: bool = True
    real_hai_profiling_authorized: bool = False
    train1_train2_profiling_execution_authorized: bool = False
    train3_confirmation_execution_authorized: bool = False
    train4_access_authorized: bool = False
    test_labels_attacks_authorized: bool = False
    rule_v2_authorized: bool = False
    agent_execution_authorized: bool = False
    detector_runtime_authorized: bool = False
    outer_sealed_authorized: bool = False

    ARTIFACT_TYPE = "task039d0_authorization_v1"

    def __post_init__(self) -> None:
        _require_sha256(self.candidate_cohort_hash, "cohort hash")
        _require_sha256(self.candidate_identity_list_hash, "identity-list hash")
        if (
            self.candidate_count != 47
            or self.process != "P1"
            or self.relation_family != "continuous_step_delayed_response_v1"
            or self.source_arm_set != ARMS
            or not self.protocol_design_authorized
            or any(
                (
                    self.real_hai_profiling_authorized,
                    self.train1_train2_profiling_execution_authorized,
                    self.train3_confirmation_execution_authorized,
                    self.train4_access_authorized,
                    self.test_labels_attacks_authorized,
                    self.rule_v2_authorized,
                    self.agent_execution_authorized,
                    self.detector_runtime_authorized,
                    self.outer_sealed_authorized,
                )
            )
        ):
            raise CandidateIntegrationError("TASK-039D0 authority boundary changed")

    def _payload(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "artifact_type": self.ARTIFACT_TYPE,
            "task_id": "TASK-039D0",
            "full_name": "Normal Relation Profiling and Calibration Protocol Freeze",
            "candidate_cohort_hash": self.candidate_cohort_hash,
            "candidate_identity_list_hash": self.candidate_identity_list_hash,
            "candidate_count": self.candidate_count,
            "process": self.process,
            "relation_family": self.relation_family,
            "source_arm_set": list(self.source_arm_set),
            "protocol_design_authorized": self.protocol_design_authorized,
            "real_hai_profiling_authorized": self.real_hai_profiling_authorized,
            "train1_train2_profiling_execution_authorized": self.train1_train2_profiling_execution_authorized,
            "train3_confirmation_execution_authorized": self.train3_confirmation_execution_authorized,
            "train4_access_authorized": self.train4_access_authorized,
            "test_labels_attacks_authorized": self.test_labels_attacks_authorized,
            "rule_v2_authorized": self.rule_v2_authorized,
            "agent_execution_authorized": self.agent_execution_authorized,
            "detector_runtime_authorized": self.detector_runtime_authorized,
            "outer_sealed_authorized": self.outer_sealed_authorized,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._payload())

    def to_dict(self) -> dict[str, Any]:
        return _hashed(self._payload())

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "TASK039D0AuthorizationV1":
        payload = _verify_hashed(data, cls.ARTIFACT_TYPE)
        expected = set(cls("0" * 64, "0" * 64)._payload())
        _reject_unknown(payload, expected, cls.ARTIFACT_TYPE)
        if payload["schema_version"] != SCHEMA_VERSION or payload["artifact_type"] != cls.ARTIFACT_TYPE:
            raise CandidateIntegrationError("authorization identity changed")
        return cls(
            candidate_cohort_hash=str(payload["candidate_cohort_hash"]),
            candidate_identity_list_hash=str(payload["candidate_identity_list_hash"]),
            candidate_count=int(payload["candidate_count"]),
            process=str(payload["process"]),
            relation_family=str(payload["relation_family"]),
            source_arm_set=tuple(str(x) for x in payload["source_arm_set"]),
            protocol_design_authorized=bool(payload["protocol_design_authorized"]),
            real_hai_profiling_authorized=bool(payload["real_hai_profiling_authorized"]),
            train1_train2_profiling_execution_authorized=bool(payload["train1_train2_profiling_execution_authorized"]),
            train3_confirmation_execution_authorized=bool(payload["train3_confirmation_execution_authorized"]),
            train4_access_authorized=bool(payload["train4_access_authorized"]),
            test_labels_attacks_authorized=bool(payload["test_labels_attacks_authorized"]),
            rule_v2_authorized=bool(payload["rule_v2_authorized"]),
            agent_execution_authorized=bool(payload["agent_execution_authorized"]),
            detector_runtime_authorized=bool(payload["detector_runtime_authorized"]),
            outer_sealed_authorized=bool(payload["outer_sealed_authorized"]),
        )


@dataclass(frozen=True)
class TASK039CIntegrationReceiptV1:
    integration_execution_code_commit: str
    c0_commit: str
    c0_protocol_bundle_hash: str
    meta_implementation_commit: str
    meta_result_commit: str
    stat_implementation_commit: str
    stat_result_commit: str
    gdn_execution_code_commit: str
    gdn_result_commit: str
    preliminary_review_commit: str
    final_gdn_audit_commit: str
    preliminary_review_hash: str
    final_gdn_audit_hash: str
    result_artifact_hashes: Mapping[str, str]
    ranking_hashes: Mapping[str, str | None]
    audited_preview_hash: str
    candidate_identity_list_hash: str
    candidate_cohort_hash: str
    overlap_artifact_hash: str
    task039d0_authorization_hash: str
    included_arms: tuple[str, ...] = ARMS
    candidate_count: int = 47
    hai_feature_access: bool = False
    private_ledger_access: bool = False
    merged_score_created: bool = False
    global_rank_created: bool = False
    br2_ground_truth_used: bool = False
    real_task039d_execution: bool = False

    ARTIFACT_TYPE = "task039c_integration_receipt_v1"

    def __post_init__(self) -> None:
        for value in (
            self.integration_execution_code_commit,
            self.c0_commit,
            self.meta_implementation_commit,
            self.meta_result_commit,
            self.stat_implementation_commit,
            self.stat_result_commit,
            self.gdn_execution_code_commit,
            self.gdn_result_commit,
            self.preliminary_review_commit,
            self.final_gdn_audit_commit,
        ):
            _require_git_sha(value, "receipt commit")
        for value in (
            *self.result_artifact_hashes.values(),
            *(x for x in self.ranking_hashes.values() if x is not None),
            self.audited_preview_hash,
            self.candidate_identity_list_hash,
            self.candidate_cohort_hash,
            self.overlap_artifact_hash,
            self.task039d0_authorization_hash,
            self.c0_protocol_bundle_hash,
            self.preliminary_review_hash,
            self.final_gdn_audit_hash,
        ):
            _require_sha256(value, "receipt hash")
        if (
            tuple(self.result_artifact_hashes) != ARMS
            or tuple(self.ranking_hashes) != ARMS
            or self.included_arms != ARMS
            or self.candidate_count != 47
            or any(
                (
                    self.hai_feature_access,
                    self.private_ledger_access,
                    self.merged_score_created,
                    self.global_rank_created,
                    self.br2_ground_truth_used,
                    self.real_task039d_execution,
                )
            )
        ):
            raise CandidateIntegrationError("integration receipt boundary changed")
        object.__setattr__(self, "result_artifact_hashes", MappingProxyType(dict(self.result_artifact_hashes)))
        object.__setattr__(self, "ranking_hashes", MappingProxyType(dict(self.ranking_hashes)))

    def _payload(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "artifact_type": self.ARTIFACT_TYPE,
            "task_id": TASK_ID,
            "status": PASS_STATUS,
            "integration_execution_code_commit": self.integration_execution_code_commit,
            "c0_commit": self.c0_commit,
            "c0_protocol_bundle_hash": self.c0_protocol_bundle_hash,
            "meta_implementation_commit": self.meta_implementation_commit,
            "meta_result_commit": self.meta_result_commit,
            "stat_implementation_commit": self.stat_implementation_commit,
            "stat_result_commit": self.stat_result_commit,
            "gdn_execution_code_commit": self.gdn_execution_code_commit,
            "gdn_result_commit": self.gdn_result_commit,
            "preliminary_review_commit": self.preliminary_review_commit,
            "final_gdn_audit_commit": self.final_gdn_audit_commit,
            "preliminary_review_hash": self.preliminary_review_hash,
            "final_gdn_audit_hash": self.final_gdn_audit_hash,
            "result_artifact_hashes": dict(self.result_artifact_hashes),
            "ranking_hashes": dict(self.ranking_hashes),
            "audited_preview_hash": self.audited_preview_hash,
            "candidate_identity_list_hash": self.candidate_identity_list_hash,
            "candidate_cohort_hash": self.candidate_cohort_hash,
            "overlap_artifact_hash": self.overlap_artifact_hash,
            "included_arms": list(self.included_arms),
            "candidate_count": self.candidate_count,
            "hai_feature_access": self.hai_feature_access,
            "private_ledger_access": self.private_ledger_access,
            "merged_score_created": self.merged_score_created,
            "global_rank_created": self.global_rank_created,
            "br2_ground_truth_used": self.br2_ground_truth_used,
            "task039d0_authorization_hash": self.task039d0_authorization_hash,
            "real_task039d_execution": self.real_task039d_execution,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._payload())

    def to_dict(self) -> dict[str, Any]:
        return _hashed(self._payload())

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "TASK039CIntegrationReceiptV1":
        payload = _verify_hashed(data, cls.ARTIFACT_TYPE)
        expected = {
            "schema_version", "artifact_type", "task_id", "status",
            "integration_execution_code_commit", "c0_commit",
            "c0_protocol_bundle_hash",
            "meta_implementation_commit", "meta_result_commit",
            "stat_implementation_commit", "stat_result_commit",
            "gdn_execution_code_commit", "gdn_result_commit",
            "preliminary_review_commit", "final_gdn_audit_commit",
            "preliminary_review_hash", "final_gdn_audit_hash",
            "result_artifact_hashes", "ranking_hashes",
            "audited_preview_hash", "candidate_identity_list_hash",
            "candidate_cohort_hash", "overlap_artifact_hash",
            "included_arms", "candidate_count", "hai_feature_access",
            "private_ledger_access", "merged_score_created",
            "global_rank_created", "br2_ground_truth_used",
            "task039d0_authorization_hash", "real_task039d_execution",
        }
        _reject_unknown(payload, expected, cls.ARTIFACT_TYPE)
        if payload["schema_version"] != SCHEMA_VERSION or payload["artifact_type"] != cls.ARTIFACT_TYPE:
            raise CandidateIntegrationError("receipt identity changed")
        return cls(
            integration_execution_code_commit=str(payload["integration_execution_code_commit"]),
            c0_commit=str(payload["c0_commit"]),
            c0_protocol_bundle_hash=str(payload["c0_protocol_bundle_hash"]),
            meta_implementation_commit=str(payload["meta_implementation_commit"]),
            meta_result_commit=str(payload["meta_result_commit"]),
            stat_implementation_commit=str(payload["stat_implementation_commit"]),
            stat_result_commit=str(payload["stat_result_commit"]),
            gdn_execution_code_commit=str(payload["gdn_execution_code_commit"]),
            gdn_result_commit=str(payload["gdn_result_commit"]),
            preliminary_review_commit=str(payload["preliminary_review_commit"]),
            final_gdn_audit_commit=str(payload["final_gdn_audit_commit"]),
            preliminary_review_hash=str(payload["preliminary_review_hash"]),
            final_gdn_audit_hash=str(payload["final_gdn_audit_hash"]),
            result_artifact_hashes=payload["result_artifact_hashes"],
            ranking_hashes=payload["ranking_hashes"],
            audited_preview_hash=str(payload["audited_preview_hash"]),
            candidate_identity_list_hash=str(payload["candidate_identity_list_hash"]),
            candidate_cohort_hash=str(payload["candidate_cohort_hash"]),
            overlap_artifact_hash=str(payload["overlap_artifact_hash"]),
            task039d0_authorization_hash=str(payload["task039d0_authorization_hash"]),
            included_arms=tuple(str(x) for x in payload["included_arms"]),
            candidate_count=int(payload["candidate_count"]),
            hai_feature_access=bool(payload["hai_feature_access"]),
            private_ledger_access=bool(payload["private_ledger_access"]),
            merged_score_created=bool(payload["merged_score_created"]),
            global_rank_created=bool(payload["global_rank_created"]),
            br2_ground_truth_used=bool(payload["br2_ground_truth_used"]),
            real_task039d_execution=bool(payload["real_task039d_execution"]),
        )


@dataclass(frozen=True)
class IntegrationBuildResultV1:
    overlap: TASK039CThreeArmOverlapV1
    cohort: CandidateProfilingCohortV1
    authorization: TASK039D0AuthorizationV1
    receipt: TASK039CIntegrationReceiptV1
    audited_preview_hash: str


def _pairs(records: Sequence[Mapping[str, Any]], arm: str) -> tuple[tuple[str, str], ...]:
    if arm == "META":
        return tuple((str(x["source_identity"]), str(x["target_identity"])) for x in records)
    return tuple((str(x["source"]), str(x["target"])) for x in records)


def _overlap_budget(
    meta: set[tuple[str, str]],
    stat: set[tuple[str, str]],
    gdn: set[tuple[str, str]],
) -> OverlapBudgetV1:
    triple = meta & stat & gdn
    return OverlapBudgetV1(
        meta_count=len(meta),
        stat_count=len(stat),
        gdn_count=len(gdn),
        meta_stat=len(meta & stat),
        meta_gdn=len(meta & gdn),
        stat_gdn=len(stat & gdn),
        triple=len(triple),
        meta_only=len(meta - stat - gdn),
        stat_only=len(stat - meta - gdn),
        gdn_only=len(gdn - meta - stat),
        meta_stat_only=len((meta & stat) - gdn),
        meta_gdn_only=len((meta & gdn) - stat),
        stat_gdn_only=len((stat & gdn) - meta),
        all_three=len(triple),
        union_count=len(meta | stat | gdn),
    )


def reconstruct_audited_preview_v1(
    *,
    universe_hash: str,
    meta_result: Mapping[str, Any],
    stat_result: Mapping[str, Any],
    gdn_result: Mapping[str, Any],
) -> dict[str, Any]:
    """Reproduce the final-audit preview without reading private ledgers."""

    meta_top = _pairs(meta_result["top20_identities"], "META")
    stat_top = _pairs(stat_result["top20"], "STAT")
    gdn_top = _pairs(gdn_result["top20"], "GDN")
    meta_map = {_pairs((x,), "META")[0]: x for x in meta_result["supported_ranking"]}
    stat_map = {_pairs((x,), "STAT")[0]: x for x in stat_result["supported_ranking"]}
    gdn_map = {_pairs((x,), "GDN")[0]: x for x in gdn_result["ranking"]}
    order: list[tuple[str, str]] = []
    origins: dict[tuple[str, str], list[str]] = {}
    for arm, records in (("META", meta_top), ("STAT", stat_top), ("GDN", gdn_top)):
        for pair in records:
            if pair not in origins:
                origins[pair] = []
                order.append(pair)
            origins[pair].append(arm)
    candidates: list[dict[str, Any]] = []
    for pair in order:
        item: dict[str, Any] = {
            "source": pair[0],
            "target": pair[1],
            "origin_arms": origins[pair],
            "universe_ref": "COMMON",
        }
        if pair in meta_map:
            source = meta_map[pair]
            item["META"] = {
                "rank": source["rank"],
                "tier": source["evidence_tier"],
                "evidence_refs": source["reference_identifiers"],
            }
        if pair in stat_map:
            source = stat_map[pair]
            item["STAT"] = {
                "rank": source["rank"],
                "horizon": source["selected_horizon_seconds"],
                "sign": source["correlation_sign"],
                "r_train1": source["r_train1"],
                "r_train2": source["r_train2"],
                "strength": source["stability_strength"],
                "evidence_ref": "STAT_LEDGER",
            }
        if pair in gdn_map:
            source = gdn_map[pair]
            item["GDN"] = {
                "rank": source["rank"],
                "frequency": source["edge_selection_frequency"],
                "similarity": source["median_upstream_graph_similarity"],
                "evidence_ref": "GDN_AGGREGATE",
            }
        candidates.append(item)
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_type": "task039c_gdn_final_audit_preview_v1",
        "budget": 20,
        "helper": "integrate_candidate_union_v1",
        "arm_order": list(ARMS),
        "dedupe": ["source", "target"],
        "unscored": True,
        "global_rank": False,
        "confirmed_relation": False,
        "evidence_catalog": {
            "COMMON": universe_hash,
            "STAT_LEDGER": stat_result["private_detailed_ledger_hash"],
            "GDN_AGGREGATE": {
                "result": gdn_result["artifact_hash"],
                "seed_ledgers": gdn_result["private_seed_ledger_hashes"],
            },
        },
        "count": len(candidates),
        "candidates": candidates,
    }


def _validate_input_self_hash(document: Mapping[str, Any], expected: str, label: str) -> None:
    payload = dict(document)
    supplied = payload.pop("artifact_hash", None)
    if supplied != expected or supplied != stable_hash_v1(payload):
        raise CandidateIntegrationError(f"{label} artifact mismatch")


def build_task039c_integration_v1(
    *,
    c0_bundle: Mapping[str, Any],
    meta_result: Mapping[str, Any],
    stat_result: Mapping[str, Any],
    gdn_result: Mapping[str, Any],
    preliminary_review: Mapping[str, Any],
    final_gdn_audit: Mapping[str, Any],
    integration_execution_code_commit: str,
) -> IntegrationBuildResultV1:
    """Build the final artifacts from merged public inputs only."""

    expected = {
        "c0": "41aab751d6bbbaadc72a95ef3289ea6440c26659fb38f640bf17fb0688836dff",
        "meta": "0e3b055df911c74bd0e0993b7b3bb122860b265192ad0cf91d54edc1e74635bf",
        "stat": "7351e295be7e5bdd2b1cb9677091426899e5a2616c60245f953ff6602d106950",
        "gdn": "2c58308d0d97d93cf671907064c805dbadcb01508ed8571090a448be6c855bfc",
        "review": "c2f3159a2ca5a0028ea5965c9aec0f69986110640403ffa29edf6f600f88f6b4",
        "audit": "8f40aec0dddd48b487c6ca503fc9b71791626aef2cb3b3cf8935b182a34e6357",
    }
    for document, name in (
        (c0_bundle, "c0"),
        (meta_result, "meta"),
        (stat_result, "stat"),
        (gdn_result, "gdn"),
        (preliminary_review, "review"),
        (final_gdn_audit, "audit"),
    ):
        _validate_input_self_hash(document, expected[name], name)
    _require_git_sha(integration_execution_code_commit, "integration execution commit")
    if (
        c0_bundle["status"] != "passed_task039c0_candidate_discovery_protocol_freeze"
        or preliminary_review["finding_counts"]["BLOCKING"] != 0
        or final_gdn_audit["status"] != "passed_task039c_gdn_final_audit"
        or final_gdn_audit["integration_readiness"] != "READY_FOR_THREE_ARM_INTEGRATION"
        or final_gdn_audit["findings_by_severity"]["BLOCKING"] != 0
    ):
        raise CandidateIntegrationError("review authority is not passing")
    universe_data = c0_bundle["universe_policy"]
    universe = CandidateUniversePolicyV1.from_dict(universe_data)
    universe_hash = universe_data["eligible_pair_universe_hash"]
    all_pairs = {
        (source, target)
        for source in universe_data["source_variables"]
        for target in universe_data["target_variables"]
    }
    meta_top = _pairs(meta_result["top20_identities"], "META")
    stat_top = _pairs(stat_result["top20"], "STAT")
    gdn_top = _pairs(gdn_result["top20"], "GDN")
    if (
        meta_top != _pairs(meta_result["supported_ranking"][:20], "META")
        or stat_top != _pairs(stat_result["supported_ranking"][:20], "STAT")
        or gdn_top != _pairs(gdn_result["ranking"][:20], "GDN")
    ):
        raise CandidateIntegrationError("arm top20 is not a ranking prefix")
    for records in (meta_top, stat_top, gdn_top):
        if len(records) != 20 or len(set(records)) != 20 or not set(records) <= all_pairs:
            raise CandidateIntegrationError("invalid arm top20")
    if (
        meta_result["cross_arm_score_used"]
        or meta_result["BR2_pair_supervision_used"]
        or stat_result["cross_arm_score_used"]
        or stat_result["br2_pair_supervision_used"]
        or gdn_result["br2_pair_supervision_used"]
        or gdn_result["meta_output_used"]
        or gdn_result["stat_output_used"]
    ):
        raise CandidateIntegrationError("cross-arm or BR2 supervision detected")
    preview = reconstruct_audited_preview_v1(
        universe_hash=universe_hash,
        meta_result=meta_result,
        stat_result=stat_result,
        gdn_result=gdn_result,
    )
    if (
        preview != final_gdn_audit["provisional_preview"]
        or stable_hash_v1(preview) != EXPECTED_PREVIEW_HASH
        or final_gdn_audit["provisional_union_hash"] != EXPECTED_PREVIEW_HASH
    ):
        raise CandidateIntegrationError("failed_task039c_three_arm_preview_hash")
    bindings = (
        TASK039CArmBindingV1(
            arm_id="META",
            claim_boundary="metadata candidate evidence",
            implementation_commit="2b3df4443619b8d0d19434bbcd1ded3b31a1b8ea",
            result_commit="b8a744c4b2cc70cd70bfc73ce45408c2ec8b5824",
            result_artifact_hash=meta_result["artifact_hash"],
            ranking_hash=None,
            policy_hash=meta_result["metadata_policy_hash"],
            evidence_binding_hashes=(meta_result["evidence_ledger_hash"], meta_result["artifact_hash"]),
            data_access_audit_hash="1a21a4c1a67c053c2be576299cc77584f0f9c4cc7e3e62d738cd083cf4025a68",
            evaluated_count=meta_result["evaluated_pair_count"],
            supported_count=meta_result["supported_count"],
            top20_count=len(meta_top),
        ),
        TASK039CArmBindingV1(
            arm_id="STAT",
            claim_boundary="lagged change-correlation candidate evidence",
            implementation_commit="629f022d35bb0db6130e7e69faaf48408b49aa9a",
            result_commit="9359a8b8085b1948bde23171ec886e996fbd37b3",
            result_artifact_hash=stat_result["artifact_hash"],
            ranking_hash=stat_result["ranking_hash"],
            policy_hash=stat_result["stat_policy_hash"],
            evidence_binding_hashes=(
                stat_result["private_detailed_ledger_hash"],
                stat_result["ranking_hash"],
                stat_result["artifact_hash"],
            ),
            data_access_audit_hash="9588682c8c6c52afdc4dea960c1ccfbe221501a7f756ff9de2893474eb0099e4",
            evaluated_count=stat_result["evaluated_pair_count"],
            supported_count=stat_result["supported_stable_count"],
            top20_count=len(stat_top),
        ),
        TASK039CArmBindingV1(
            arm_id="GDN",
            claim_boundary="learned-graph candidate evidence",
            implementation_commit="6790505e08ea06d6b3f6d34f9fd533d381696b1f",
            result_commit="1204ff4e6d790c2cd0e8268f778a8f071e5eea4b",
            result_artifact_hash=gdn_result["artifact_hash"],
            ranking_hash=gdn_result["ranking_hash"],
            policy_hash=gdn_result["gdn_policy_hash"],
            evidence_binding_hashes=(
                gdn_result["ranking_hash"],
                gdn_result["artifact_hash"],
                *(x["ledger_hash"] for x in gdn_result["private_seed_ledger_hashes"]),
            ),
            data_access_audit_hash=gdn_result["data_access_audit_hash"],
            evaluated_count=gdn_result["evaluated_candidate_count"],
            supported_count=gdn_result["supported_candidate_count"],
            top20_count=len(gdn_top),
        ),
    )
    meta_arm = tuple(ArmCandidateV1(a, b, bindings[0].evidence_binding_hashes) for a, b in meta_top)
    stat_arm = tuple(ArmCandidateV1(a, b, bindings[1].evidence_binding_hashes) for a, b in stat_top)
    gdn_arm = tuple(ArmCandidateV1(a, b, bindings[2].evidence_binding_hashes) for a, b in gdn_top)
    integrated = integrate_candidate_union_v1(
        universe=universe,
        meta_top20=meta_arm,
        stat_top20=stat_arm,
        gdn_top20=gdn_arm,
    )
    meta_map = {_pairs((x,), "META")[0]: x for x in meta_result["supported_ranking"]}
    stat_map = {_pairs((x,), "STAT")[0]: x for x in stat_result["supported_ranking"]}
    gdn_map = {_pairs((x,), "GDN")[0]: x for x in gdn_result["ranking"]}
    entries: list[CandidateProfilingEntryV1] = []
    for position, item in enumerate(integrated, start=1):
        pair = (item.source, item.target)
        meta_evidence = None
        stat_evidence = None
        gdn_evidence = None
        if "META" in item.origin_arms:
            source = meta_map[pair]
            meta_evidence = {
                "rank": source["rank"],
                "evidence_tier": source["evidence_tier"],
                "independent_official_reference_count": source["independent_official_reference_count"],
                "metadata_evidence_references": source["reference_identifiers"],
                "evidence_binding_hashes": list(bindings[0].evidence_binding_hashes),
                "result_artifact_hash": meta_result["artifact_hash"],
            }
        if "STAT" in item.origin_arms:
            source = stat_map[pair]
            for key in ("r_train1", "r_train2", "stability_strength"):
                _require_finite(source[key], f"STAT {key}")
            stat_evidence = {
                "rank": source["rank"],
                "selected_horizon_seconds": source["selected_horizon_seconds"],
                "correlation_sign": source["correlation_sign"],
                "r_train1": source["r_train1"],
                "r_train2": source["r_train2"],
                "stability_strength": source["stability_strength"],
                "ranking_hash": stat_result["ranking_hash"],
                "result_artifact_hash": stat_result["artifact_hash"],
            }
        if "GDN" in item.origin_arms:
            source = gdn_map[pair]
            for key in ("edge_selection_frequency", "median_upstream_graph_similarity"):
                _require_finite(source[key], f"GDN {key}")
            gdn_evidence = {
                "rank": source["rank"],
                "edge_selection_frequency": source["edge_selection_frequency"],
                "selected_seed_count": source["selected_seed_count"],
                "median_upstream_graph_similarity": source["median_upstream_graph_similarity"],
                "ranking_hash": gdn_result["ranking_hash"],
                "result_artifact_hash": gdn_result["artifact_hash"],
                "compatibility_closure_receipt_hash": gdn_result["compatibility_closure_receipt_hash"],
            }
        entries.append(
            CandidateProfilingEntryV1(
                source=item.source,
                target=item.target,
                candidate_universe_hash=universe_hash,
                origin_arms=item.origin_arms,
                serialization_position=position,
                meta_evidence=meta_evidence,
                stat_evidence=stat_evidence,
                gdn_evidence=gdn_evidence,
            )
        )
    meta20, stat20, gdn20 = set(meta_top), set(stat_top), set(gdn_top)
    meta10 = set(_pairs(meta_result["top10_identities"], "META"))
    stat10 = set(_pairs(stat_result["top10"], "STAT"))
    gdn10 = set(_pairs(gdn_result["top10"], "GDN"))
    meta_sensitivity = set(_pairs(meta_result["top40_identities"], "META"))
    stat_sensitivity = set(_pairs(stat_result["top40"], "STAT"))
    gdn_sensitivity = set(_pairs(gdn_result["top40"], "GDN"))
    top10 = _overlap_budget(meta10, stat10, gdn10)
    top20 = _overlap_budget(meta20, stat20, gdn20)
    sensitivity = _overlap_budget(meta_sensitivity, stat_sensitivity, gdn_sensitivity)
    overlap = TASK039CThreeArmOverlapV1(
        top10=top10,
        top20=top20,
        sensitivity=sensitivity,
        top10_meta_stat_only_pairs=tuple(sorted((meta10 & stat10) - gdn10)),
        top10_meta_gdn_only_pairs=tuple(sorted((meta10 & gdn10) - stat10)),
        top10_stat_gdn_only_pairs=tuple(sorted((stat10 & gdn10) - meta10)),
    )
    identities = tuple((x.source, x.target) for x in entries)
    identity_hash = stable_hash_v1(
        {
            "artifact_type": "candidate_profiling_identity_list_v1",
            "identities": [{"source": a, "target": b} for a, b in identities],
        }
    )
    cohort = CandidateProfilingCohortV1(
        c0_protocol_bundle_hash=c0_bundle["artifact_hash"],
        common_universe_hash=universe_hash,
        source_identity_hash=universe_data["source_identity_list_hash"],
        target_identity_hash=universe_data["target_identity_list_hash"],
        arm_bindings=bindings,
        top20_overlap=top20,
        candidates=tuple(entries),
        candidate_identity_list=identities,
        candidate_identity_list_hash=identity_hash,
        final_gdn_audit_commit="eab10dee0f08f419638154a9902304339b63c471",
        final_gdn_audit_hash=final_gdn_audit["artifact_hash"],
    )
    authorization = TASK039D0AuthorizationV1(
        candidate_cohort_hash=cohort.artifact_hash,
        candidate_identity_list_hash=identity_hash,
    )
    receipt = TASK039CIntegrationReceiptV1(
        integration_execution_code_commit=integration_execution_code_commit,
        c0_commit="b6522fb83c4cb92d355f98af778f9a6a3c73362f",
        c0_protocol_bundle_hash=c0_bundle["artifact_hash"],
        meta_implementation_commit="2b3df4443619b8d0d19434bbcd1ded3b31a1b8ea",
        meta_result_commit="b8a744c4b2cc70cd70bfc73ce45408c2ec8b5824",
        stat_implementation_commit="629f022d35bb0db6130e7e69faaf48408b49aa9a",
        stat_result_commit="9359a8b8085b1948bde23171ec886e996fbd37b3",
        gdn_execution_code_commit="6790505e08ea06d6b3f6d34f9fd533d381696b1f",
        gdn_result_commit="1204ff4e6d790c2cd0e8268f778a8f071e5eea4b",
        preliminary_review_commit="058b5e2023b66ccbf6704c5baf1f6c677f17b07a",
        final_gdn_audit_commit="eab10dee0f08f419638154a9902304339b63c471",
        preliminary_review_hash=preliminary_review["artifact_hash"],
        final_gdn_audit_hash=final_gdn_audit["artifact_hash"],
        result_artifact_hashes=MappingProxyType(
            {"META": meta_result["artifact_hash"], "STAT": stat_result["artifact_hash"], "GDN": gdn_result["artifact_hash"]}
        ),
        ranking_hashes=MappingProxyType(
            {"META": None, "STAT": stat_result["ranking_hash"], "GDN": gdn_result["ranking_hash"]}
        ),
        audited_preview_hash=EXPECTED_PREVIEW_HASH,
        candidate_identity_list_hash=identity_hash,
        candidate_cohort_hash=cohort.artifact_hash,
        overlap_artifact_hash=overlap.artifact_hash,
        task039d0_authorization_hash=authorization.artifact_hash,
    )
    for document in (overlap.to_dict(), cohort.to_dict(), authorization.to_dict(), receipt.to_dict()):
        assert_public_payload_v1(document)
    return IntegrationBuildResultV1(
        overlap=overlap,
        cohort=cohort,
        authorization=authorization,
        receipt=receipt,
        audited_preview_hash=EXPECTED_PREVIEW_HASH,
    )


PUBLIC_INPUT_FILES = MappingProxyType(
    {
        "c0_bundle": "docs/task_reports/TASK-039C0_PROTOCOL_BUNDLE.json",
        "meta_result": "docs/task_reports/TASK-039C_META_RESULT.json",
        "stat_result": "docs/task_reports/TASK-039C_STAT_RESULT.json",
        "gdn_result": "docs/task_reports/TASK-039C_GDN_RESULT.json",
        "preliminary_review": "docs/task_reports/TASK-039C_PARALLEL_REVIEW.json",
        "final_gdn_audit": "docs/task_reports/TASK-039C_GDN_FINAL_AUDIT.json",
    }
)


def load_merged_public_inputs_v1(repository_root: str | Path) -> dict[str, dict[str, Any]]:
    """Read only the six frozen public integration inputs."""

    root = Path(repository_root).resolve()
    loaded: dict[str, dict[str, Any]] = {}
    for key, relative in PUBLIC_INPUT_FILES.items():
        path = (root / relative).resolve()
        if root not in path.parents or path.suffix != ".json":
            raise CandidateIntegrationError("public input escaped repository")
        loaded[key] = json.loads(path.read_text(encoding="utf-8"))
    return loaded


__all__ = [
    "ARMS",
    "CandidateIntegrationError",
    "CandidateProfilingCohortV1",
    "CandidateProfilingEntryV1",
    "EXPECTED_PREVIEW_HASH",
    "IntegrationBuildResultV1",
    "OverlapBudgetV1",
    "PASS_STATUS",
    "TASK039CArmBindingV1",
    "TASK039CIntegrationReceiptV1",
    "TASK039CThreeArmOverlapV1",
    "TASK039D0AuthorizationV1",
    "assert_public_payload_v1",
    "build_task039c_integration_v1",
    "load_merged_public_inputs_v1",
    "reconstruct_audited_preview_v1",
    "stable_hash_v1",
]
