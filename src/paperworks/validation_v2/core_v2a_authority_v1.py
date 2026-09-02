"""Deterministic META+STAT and confirmed-cohort authorities for V2A.

The builders in this module consume only committed, public-safe authority
documents.  They never open HAI feature values or labels.  Numeric fitting is
deliberately downstream of the authorities materialized here.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence

from paperworks.validation_v2.exp01_scientific_v1 import (
    META_RESULT_HASH,
    PAIR_UNIVERSE,
    STAT_RESULT_HASH,
)
from paperworks.validation_v2.numeric_policy_v1 import (
    ConfirmedCohortAuthorityV1,
    ConfirmedRelationIdentityV1,
    build_confirmed_cohort_authority_v1,
)


V2A_AUTHORITY_VERSION = "VALIDATION_V2A_META_STAT_AUTHORITY_V1"
V2A_CANDIDATE_AUTHORITY_ID = "VALIDATION_V2_META_STAT_CANDIDATE_UNION_AUTHORITY_V1"
V2A_CONFIRMED_COHORT_ID = "SEPARATE_SELF_HASHED_V2A_CONFIRMED_COHORT_V1"


class CoreV2AAuthorityError(ValueError):
    pass


def _fail(code: str) -> None:
    raise CoreV2AAuthorityError(code)


def _canonical_bytes(document: Mapping[str, Any]) -> bytes:
    return json.dumps(
        dict(document), sort_keys=True, separators=(",", ":"),
        ensure_ascii=True, allow_nan=False,
    ).encode("utf-8")


def _hash(document: Mapping[str, Any]) -> str:
    return sha256(_canonical_bytes(document)).hexdigest()


def _sha(value: object, code: str) -> str:
    if type(value) is not str or len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        _fail(code)
    return value


def _commit(value: object) -> str:
    if type(value) is not str or len(value) != 40 or any(ch not in "0123456789abcdef" for ch in value):
        _fail("V2A_SOURCE_COMMIT_INVALID")
    return value


def _top20(document: Mapping[str, Any], *, arm: str) -> tuple[tuple[str, str], ...]:
    expected_hash = META_RESULT_HASH if arm == "META" else STAT_RESULT_HASH
    if document.get("artifact_hash") != expected_hash or document.get("arm_id") != arm:
        _fail(f"V2A_{arm}_AUTHORITY_MISMATCH")
    key = "top20_identities" if arm == "META" else "top20"
    rows = document.get(key)
    if type(rows) is not list or len(rows) != 20:
        _fail(f"V2A_{arm}_TOP20_INVALID")
    pairs: list[tuple[str, str]] = []
    for row in rows:
        if type(row) is not dict:
            _fail(f"V2A_{arm}_ROW_INVALID")
        source_key = "source_identity" if arm == "META" else "source"
        target_key = "target_identity" if arm == "META" else "target"
        pair = (row.get(source_key), row.get(target_key))
        if pair not in PAIR_UNIVERSE:
            _fail(f"V2A_{arm}_PAIR_OUTSIDE_UNIVERSE")
        pairs.append((str(pair[0]), str(pair[1])))
    if len(set(pairs)) != 20:
        _fail(f"V2A_{arm}_PAIR_DUPLICATE")
    return tuple(pairs)


@dataclass(frozen=True)
class MetaStatCandidateV1:
    source: str
    target: str
    provenance: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"source": self.source, "target": self.target, "provenance": list(self.provenance)}


@dataclass(frozen=True)
class MetaStatCandidateUnionAuthorityV1:
    authority_id: str
    source_commit: str
    meta_artifact_hash: str
    stat_artifact_hash: str
    candidates: tuple[MetaStatCandidateV1, ...]
    labels_accessed: bool
    test1_accessed: bool
    test2_accessed: bool
    authority_hash: str

    def body_dict(self) -> dict[str, Any]:
        return {
            "artifact_type": "validation_v2a_meta_stat_candidate_union_authority_v1",
            "authority_id": self.authority_id,
            "candidates": [item.to_dict() for item in self.candidates],
            "labels_accessed": self.labels_accessed,
            "meta_artifact_hash": self.meta_artifact_hash,
            "schema_version": "1.0.0",
            "source_commit": self.source_commit,
            "stat_artifact_hash": self.stat_artifact_hash,
            "test1_accessed": self.test1_accessed,
            "test2_accessed": self.test2_accessed,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.body_dict(), "authority_hash": self.authority_hash}


def build_meta_stat_candidate_union_authority_v1(
    *, meta_document: Mapping[str, Any], stat_document: Mapping[str, Any],
    source_commit: str,
) -> MetaStatCandidateUnionAuthorityV1:
    _commit(source_commit)
    meta_ordered = _top20(meta_document, arm="META")
    stat_ordered = _top20(stat_document, arm="STAT")
    meta = set(meta_ordered)
    stat = set(stat_ordered)
    # Preserve the already-audited candidate-integration ordering: META
    # encounter order followed by STAT-only encounter order.  Sorting here
    # would create a new V2A ordering contract without scientific benefit.
    union_ordered = meta_ordered + tuple(pair for pair in stat_ordered if pair not in meta)
    rows = tuple(
        MetaStatCandidateV1(
            source=source,
            target=target,
            provenance=tuple(arm for arm, values in (("META", meta), ("STAT", stat)) if (source, target) in values),
        )
        for source, target in union_ordered
    )
    if not rows or any(not item.provenance for item in rows):
        _fail("V2A_META_STAT_UNION_EMPTY")
    provisional = MetaStatCandidateUnionAuthorityV1(
        authority_id=V2A_CANDIDATE_AUTHORITY_ID,
        source_commit=source_commit,
        meta_artifact_hash=META_RESULT_HASH,
        stat_artifact_hash=STAT_RESULT_HASH,
        candidates=rows,
        labels_accessed=False,
        test1_accessed=False,
        test2_accessed=False,
        authority_hash="",
    )
    return replace(provisional, authority_hash=_hash(provisional.body_dict()))


def validate_meta_stat_candidate_union_authority_v1(
    value: MetaStatCandidateUnionAuthorityV1,
    *, meta_document: Mapping[str, Any], stat_document: Mapping[str, Any],
) -> str:
    if type(value) is not MetaStatCandidateUnionAuthorityV1:
        _fail("V2A_CANDIDATE_AUTHORITY_TYPE_INVALID")
    expected = build_meta_stat_candidate_union_authority_v1(
        meta_document=meta_document, stat_document=stat_document,
        source_commit=value.source_commit,
    )
    if value != expected:
        _fail("V2A_CANDIDATE_AUTHORITY_REPLAY_MISMATCH")
    return value.authority_hash


@dataclass(frozen=True)
class V2AConfirmedCohortBindingV1:
    candidate_authority_hash: str
    directional_confirmation_artifact_hash: str
    source_commit: str
    confirmed_pair_count: int
    confirmed_directional_relation_count: int
    cohort_hash: str
    pilot_v1_authority_aliased: bool
    labels_accessed: bool
    test1_accessed: bool
    test2_accessed: bool
    binding_hash: str

    def body_dict(self) -> dict[str, Any]:
        return {
            "artifact_type": "validation_v2a_confirmed_cohort_binding_v1",
            **{key: value for key, value in self.__dict__.items() if key != "binding_hash"},
            "schema_version": "1.0.0",
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.body_dict(), "binding_hash": self.binding_hash}


def build_v2a_confirmed_cohort_v1(
    *, candidate_authority: MetaStatCandidateUnionAuthorityV1,
    directional_confirmation_document: Mapping[str, Any], source_commit: str,
) -> tuple[ConfirmedCohortAuthorityV1, V2AConfirmedCohortBindingV1]:
    _commit(source_commit)
    if source_commit != candidate_authority.source_commit:
        _fail("V2A_COHORT_COMMIT_MISMATCH")
    if candidate_authority.authority_hash != _hash(candidate_authority.body_dict()):
        _fail("V2A_CANDIDATE_AUTHORITY_MUTATED")
    confirmation_hash = _sha(
        directional_confirmation_document.get("artifact_hash"),
        "V2A_CONFIRMATION_HASH_INVALID",
    )
    if directional_confirmation_document.get("status") != "frozen_task039d2_directional_confirmation_summary":
        _fail("V2A_CONFIRMATION_STATUS_INVALID")
    rows = directional_confirmation_document.get("relations")
    if type(rows) is not list:
        _fail("V2A_CONFIRMATION_ROWS_INVALID")
    selected_pairs = {(item.source, item.target) for item in candidate_authority.candidates}
    relations: list[ConfirmedRelationIdentityV1] = []
    for row in rows:
        if type(row) is not dict or row.get("confirmation_status") != "calibration_confirmed":
            continue
        pair = (row.get("source"), row.get("target"))
        if pair not in selected_pairs:
            continue
        direction_record_hash = _sha(
            row.get("d1_directional_record_hash"), "V2A_DIRECTION_RECORD_HASH_INVALID"
        )
        identity = {
            "cohort_namespace": V2A_CONFIRMED_COHORT_ID,
            "confirmation_artifact_hash": confirmation_hash,
            "direction_record_hash": direction_record_hash,
            "selected_horizon_seconds": row.get("selected_horizon_seconds"),
            "source": row.get("source"),
            "source_direction": row.get("source_step_direction"),
            "target": row.get("target"),
            "target_direction": row.get("target_response_direction"),
        }
        relation_binding_hash = _hash(identity)
        relations.append(
            ConfirmedRelationIdentityV1(
                relation_id=f"V2A-REL-{relation_binding_hash[:24]}",
                source=str(row.get("source")),
                target=str(row.get("target")),
                source_direction=str(row.get("source_step_direction")),
                target_direction=str(row.get("target_response_direction")),
                selected_horizon_seconds=int(row.get("selected_horizon_seconds")),
                relation_binding_hash=relation_binding_hash,
            )
        )
    if not relations:
        _fail("V2A_CONFIRMED_COHORT_EMPTY")
    cohort = build_confirmed_cohort_authority_v1(
        cohort_id=V2A_CONFIRMED_COHORT_ID,
        source_commit=source_commit,
        confirmation_artifact_hash=confirmation_hash,
        relations=relations,
    )
    pair_count = len({(item.source, item.target) for item in cohort.relations})
    provisional = V2AConfirmedCohortBindingV1(
        candidate_authority_hash=candidate_authority.authority_hash,
        directional_confirmation_artifact_hash=confirmation_hash,
        source_commit=source_commit,
        confirmed_pair_count=pair_count,
        confirmed_directional_relation_count=len(cohort.relations),
        cohort_hash=cohort.cohort_hash,
        pilot_v1_authority_aliased=False,
        labels_accessed=False,
        test1_accessed=False,
        test2_accessed=False,
        binding_hash="",
    )
    return cohort, replace(provisional, binding_hash=_hash(provisional.body_dict()))


__all__ = [
    "CoreV2AAuthorityError", "MetaStatCandidateUnionAuthorityV1",
    "MetaStatCandidateV1", "V2AConfirmedCohortBindingV1",
    "V2A_AUTHORITY_VERSION", "V2A_CANDIDATE_AUTHORITY_ID",
    "V2A_CONFIRMED_COHORT_ID", "build_meta_stat_candidate_union_authority_v1",
    "build_v2a_confirmed_cohort_v1",
    "validate_meta_stat_candidate_union_authority_v1",
]
