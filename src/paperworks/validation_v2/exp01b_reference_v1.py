"""Arm-blind normal relation-reference contracts for EXP-01B."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from paperworks.validation_v2.exp01_scientific_v1 import (
    PAIR_UNIVERSE,
    PAIR_UNIVERSE_HASH,
    SOURCE_VARIABLES,
    TARGET_VARIABLES,
)
from paperworks.validation_v2.formal_v4_authority_v1 import V4_HORIZONS_SECONDS
from paperworks.v6.common import require_sha256, stable_hash_v1


class Exp01BReferenceError(ValueError):
    """Fail-closed relation-reference contract error."""


@dataclass(frozen=True)
class NormalConfirmedDirectionalRelationV1:
    relation_id: str
    source: str
    target: str
    source_direction: str
    target_direction: str
    selected_horizon_seconds: int
    relation_binding_hash: str

    def __post_init__(self) -> None:
        if (self.source, self.target) not in PAIR_UNIVERSE:
            raise Exp01BReferenceError("relation lies outside the frozen 144-pair universe")
        if self.source_direction not in {"step_up", "step_down"}:
            raise Exp01BReferenceError("source direction is invalid")
        if self.target_direction not in {"increase", "decrease"}:
            raise Exp01BReferenceError("target direction is invalid")
        if self.selected_horizon_seconds not in V4_HORIZONS_SECONDS:
            raise Exp01BReferenceError("relation horizon is outside the frozen protocol")
        require_sha256(self.relation_binding_hash, "relation_binding_hash")
        expected = directional_relation_id_v1(
            source=self.source,
            target=self.target,
            source_direction=self.source_direction,
            target_direction=self.target_direction,
            selected_horizon_seconds=self.selected_horizon_seconds,
            confirmation_authority_hash=self.relation_binding_hash,
        )
        if self.relation_id != expected:
            raise Exp01BReferenceError("directional relation identity mismatch")


def directional_relation_id_v1(
    *, source: str, target: str, source_direction: str,
    target_direction: str, selected_horizon_seconds: int,
    confirmation_authority_hash: str,
) -> str:
    require_sha256(confirmation_authority_hash, "confirmation_authority_hash")
    body = {
        "namespace": "EXP01B_NORMAL_CONFIRMED_DIRECTIONAL_RELATIONS_V1",
        "source": source,
        "target": target,
        "source_direction": source_direction,
        "target_direction": target_direction,
        "selected_horizon_seconds": selected_horizon_seconds,
        "confirmation_authority_hash": confirmation_authority_hash,
    }
    return f"EXP01B-REL-{stable_hash_v1(body)[:24]}"


def full_arm_blind_pair_reference_v1() -> tuple[tuple[str, str], ...]:
    result = tuple((source, target) for source in SOURCE_VARIABLES for target in TARGET_VARIABLES)
    if result != PAIR_UNIVERSE or len(result) != 144 or len(set(result)) != 144:
        raise Exp01BReferenceError("exact complete 144-pair reference required")
    if set(SOURCE_VARIABLES) & set(TARGET_VARIABLES):
        raise Exp01BReferenceError("role overlap would require an explicit self-pair policy")
    return result


def build_reference_receipt_v1(
    *, directional_relations: Iterable[NormalConfirmedDirectionalRelationV1],
    confirmation_authority_hash: str,
    train1_receipt_hash: str,
    train2_receipt_hash: str,
    train3_receipt_hash: str,
) -> dict[str, object]:
    for name, digest in (
        ("confirmation_authority_hash", confirmation_authority_hash),
        ("train1_receipt_hash", train1_receipt_hash),
        ("train2_receipt_hash", train2_receipt_hash),
        ("train3_receipt_hash", train3_receipt_hash),
    ):
        require_sha256(digest, name)
    relations = tuple(directional_relations)
    identities = tuple(relation.relation_id for relation in relations)
    if len(identities) != len(set(identities)):
        raise Exp01BReferenceError("directional relation identities must be unique")
    body: dict[str, object] = {
        "schema": "paperworks.validation_v2.exp01b_normal_reference_receipt_v1",
        "schema_version": "1.0.0",
        "experiment_id": "EXP-01B-GDN-XAI-V1",
        "pair_universe_hash": PAIR_UNIVERSE_HASH,
        "pair_count": 144,
        "profile_splits": ["train1", "train2"],
        "confirmation_split": "train3",
        "confirmation_arm_blind": True,
        "normal_only": True,
        "wording": "normal-confirmed relation reference",
        "causal_ground_truth": False,
        "directional_relation_count": len(relations),
        "directional_relation_identity_hash": stable_hash_v1({"relation_ids": list(identities)}),
        "confirmation_authority_hash": confirmation_authority_hash,
        "input_receipt_hashes": [train1_receipt_hash, train2_receipt_hash, train3_receipt_hash],
        "test1_accesses": 0,
        "label_accesses": 0,
        "test2_accesses": 0,
        "heldout_accesses": 0,
    }
    return {**body, "receipt_hash": stable_hash_v1(body)}


__all__ = [
    "Exp01BReferenceError", "NormalConfirmedDirectionalRelationV1",
    "build_reference_receipt_v1", "directional_relation_id_v1",
    "full_arm_blind_pair_reference_v1",
]
