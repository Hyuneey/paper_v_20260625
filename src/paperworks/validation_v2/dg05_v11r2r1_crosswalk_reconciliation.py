"""Audit-only reconciliation of V11R1 and V11R2R1 crosswalk wrappers."""
from __future__ import annotations

from typing import Any, Mapping

from .dg05_production_chain_v11 import self_hashed

HISTORICAL_APPROVAL_WRAPPER_HASH = "9f2c0d442fd92fb09a8f56389aa7a2bfde7bad74657577bef5460e5beb2d9554"
HISTORICAL_QUALIFICATION_HASH = "244bf5a31d24a4202ef2ef1eed0c80de5756e9b9f47d09da2d2d07fdae799c6c"
HISTORICAL_PREFREEZE_HASH = "3ac58129089b1534508ecf57adb0a89c5bdbf93b8cb5fe47138fc93018d5de8c"


def crosswalk_semantic_projection(crosswalk: Mapping[str, Any]) -> dict[str, Any]:
    """Project only immutable roots and the complete source-to-file mapping."""
    entries = [{key: row[key] for key in (
        "panel_id", "dataset_version", "official_scenario_file_id",
        "frozen_physical_file_id", "canonical_test_ordinal", "mapping_reason",
    )} for row in crosswalk.get("entries", ())]
    if len(entries) != 10 or len({(x["panel_id"], x["official_scenario_file_id"]) for x in entries}) != 10:
        raise ValueError("CROSSWALK_SEMANTIC_CENSUS_REQUIRED")
    return self_hashed({
        "schema": "dg05_crosswalk_semantic_projection_v1",
        "mapping_semantic": crosswalk.get("mapping_semantic"),
        "source_unified_scenario_authority_hash": crosswalk.get("source_unified_scenario_authority_hash"),
        "physical_custody_hash": crosswalk.get("physical_custody_hash"),
        "frozen_attack_file_census_hash": crosswalk.get("frozen_attack_file_census_hash"),
        "entry_count": crosswalk.get("entry_count"),
        "entries": sorted(entries, key=lambda row: (row["panel_id"], row["official_scenario_file_id"])),
    })


def reconcile_crosswalk_lineage_v11r2r1(*, historical_qualification: Mapping[str, Any],
                                         historical_prefreeze: Mapping[str, Any],
                                         final_crosswalk: Mapping[str, Any]) -> dict[str, Any]:
    """Record wrapper divergence only after exact semantic equality is proven."""
    historical = crosswalk_semantic_projection(historical_qualification)
    prefreeze = crosswalk_semantic_projection(historical_prefreeze)
    final = crosswalk_semantic_projection(final_crosswalk)
    if historical != prefreeze or historical != final:
        raise ValueError("CROSSWALK_SEMANTIC_MAPPING_DIVERGENCE")
    if historical_qualification.get("self_hash") != HISTORICAL_QUALIFICATION_HASH:
        raise ValueError("HISTORICAL_QUALIFICATION_CROSSWALK_REPLAY_FAILED")
    if historical_prefreeze.get("self_hash") != HISTORICAL_PREFREEZE_HASH:
        raise ValueError("HISTORICAL_PREFREEZE_CROSSWALK_REPLAY_FAILED")
    return self_hashed({
        "schema": "dg05_v11r2r1_crosswalk_lineage_reconciliation_v1",
        "status": "PASS",
        "historical_approval_package_crosswalk_hash": HISTORICAL_APPROVAL_WRAPPER_HASH,
        "historical_qualification_crosswalk_hash": historical_qualification["self_hash"],
        "historical_prefreeze_crosswalk_hash": historical_prefreeze["self_hash"],
        "v11r2r1_crosswalk_hash": final_crosswalk["self_hash"],
        "semantic_projection_hash": final["self_hash"],
        "mapping": final["entries"],
        "classification": "RELEASE_WRAPPER_HASHES_DIFFER_SEMANTIC_MAPPING_IDENTICAL",
        "historical_v11r1_classification": "HISTORICAL_V11R1_RELEASE_CONTROL_BINDING_INCONSISTENCY",
        "scientific_semantics_changed": False,
        "heldout_rows_parsed": 0,
        "heldout_predictions": 0,
        "heldout_metrics": 0,
    })
