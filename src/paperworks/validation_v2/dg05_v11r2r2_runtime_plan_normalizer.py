"""V11R2R2 canonical ordering for private runtime resource plans.

The plan is a locator only.  This successor adapter preserves every entry and
changes solely list order so the downstream frozen physical authority receives
the immutable panel/file order it already requires.
"""
from __future__ import annotations

from typing import Any, Mapping

from .dg05_production_chain_v11 import digest, self_hashed
from .multipanel_custody_v1 import (
    FROZEN_ATTACK_FILE_CENSUS_HASH_V2,
    FROZEN_ATTACK_FILE_IDS_V2,
    FROZEN_PANEL_ORDER_V2,
)

SCHEMA = "dg05_v11r2r2_runtime_plan_order_normalization_receipt_v1"


class DG05V11R2R2RuntimePlanOrderError(ValueError):
    """Raised before a real execution may consume its one-shot ledger."""


def _identity(row: Mapping[str, Any]) -> tuple[str, str, str, int]:
    try:
        return (str(row["panel_id"]), str(row["file_id"]), str(row["sha256"]), int(row["size"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise DG05V11R2R2RuntimePlanOrderError("RUNTIME_PLAN_IDENTITY_REQUIRED") from exc


def _order_key(row: Mapping[str, Any]) -> tuple[int, int]:
    panel, file_id, _sha, _size = _identity(row)
    if panel not in FROZEN_PANEL_ORDER_V2:
        raise DG05V11R2R2RuntimePlanOrderError("RUNTIME_PLAN_UNKNOWN_PANEL")
    files = FROZEN_ATTACK_FILE_IDS_V2[panel]
    if file_id not in files:
        raise DG05V11R2R2RuntimePlanOrderError("RUNTIME_PLAN_UNKNOWN_FILE")
    return (FROZEN_PANEL_ORDER_V2.index(panel), files.index(file_id))


def canonical_runtime_plan_identities_v11r2r2() -> tuple[tuple[str, str], ...]:
    return tuple((panel, file_id) for panel in FROZEN_PANEL_ORDER_V2 for file_id in FROZEN_ATTACK_FILE_IDS_V2[panel])


def normalize_runtime_plan_to_frozen_panel_order_v11r2r2(
    *, verified_plan: Mapping[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return a self-hashed locator plan in exact frozen panel/file order."""
    if verified_plan.get("schema") != "dg05_v11r1_protected_resource_plan_v1":
        raise DG05V11R2R2RuntimePlanOrderError("RUNTIME_PLAN_SCHEMA_REQUIRED")
    rows = [dict(row) for row in verified_plan.get("files", ())]
    identities = [_identity(row) for row in rows]
    expected = canonical_runtime_plan_identities_v11r2r2()
    if len(rows) != len(expected) or len({identity[:2] for identity in identities}) != len(expected):
        raise DG05V11R2R2RuntimePlanOrderError("RUNTIME_PLAN_IDENTITY_BIJECTION_REQUIRED")
    if {identity[:2] for identity in identities} != set(expected):
        raise DG05V11R2R2RuntimePlanOrderError("RUNTIME_PLAN_FROZEN_CENSUS_REQUIRED")
    before = tuple((row["panel_id"], row["file_id"]) for row in rows)
    normalized_rows = sorted(rows, key=_order_key)
    after = tuple((row["panel_id"], row["file_id"]) for row in normalized_rows)
    if after != expected:
        raise DG05V11R2R2RuntimePlanOrderError("RUNTIME_PLAN_CANONICAL_ORDER_REQUIRED")
    before_set = sorted(identities)
    after_set = sorted(_identity(row) for row in normalized_rows)
    if before_set != after_set:
        raise DG05V11R2R2RuntimePlanOrderError("RUNTIME_PLAN_IDENTITY_MUTATION")
    normalized = self_hashed({
        "schema": "dg05_v11r1_protected_resource_plan_v1",
        "classification": verified_plan.get("classification"),
        "physical_custody_hash": verified_plan.get("physical_custody_hash"),
        "files": normalized_rows,
        "runtime_order_authority": "FROZEN_PANEL_ORDER_V2_THEN_FROZEN_ATTACK_FILE_IDS_V2",
    })
    receipt = self_hashed({
        "schema": SCHEMA,
        "status": "PASS_CANONICAL_FROZEN_PANEL_ORDER",
        "input_plan_hash": verified_plan.get("self_hash"),
        "normalized_plan_hash": normalized["self_hash"],
        "physical_custody_hash": verified_plan.get("physical_custody_hash"),
        "frozen_attack_file_census_hash": FROZEN_ATTACK_FILE_CENSUS_HASH_V2,
        "frozen_panel_order_hash": digest(list(FROZEN_PANEL_ORDER_V2)),
        "before_order_identity_sequence_hash": digest(before),
        "after_order_identity_sequence_hash": digest(after),
        "unordered_identity_set_hash_before": digest(before_set),
        "unordered_identity_set_hash_after": digest(after_set),
        "entry_count": len(rows),
        "identity_changed": False,
        "payload_bytes_changed": False,
        "private_paths_published": False,
        "heldout_parser_calls": 0,
    })
    return normalized, receipt


def verify_runtime_plan_canonical_order_v11r2r2(*, plan: Mapping[str, Any]) -> dict[str, Any]:
    """Read-only preflight assertion; no containers or CSVs are opened."""
    normalized, receipt = normalize_runtime_plan_to_frozen_panel_order_v11r2r2(verified_plan=plan)
    if normalized != dict(plan):
        raise DG05V11R2R2RuntimePlanOrderError("RUNTIME_PLAN_NOT_CANONICAL_BEFORE_CONTACT")
    return receipt


__all__ = ["SCHEMA", "DG05V11R2R2RuntimePlanOrderError", "canonical_runtime_plan_identities_v11r2r2", "normalize_runtime_plan_to_frozen_panel_order_v11r2r2", "verify_runtime_plan_canonical_order_v11r2r2"]
