"""Deterministic source-file to frozen-physical-file identity normalization.

This is a release-engineering authority.  It maps two already frozen naming
namespaces solely when their frozen dataset version and explicitly encoded
test ordinal form a bijection; it never opens a feature container.
"""
from __future__ import annotations

import re
from typing import Any, Mapping

from .dg05_production_chain_v11 import digest, self_hashed
from .multipanel_custody_v1 import (
    FROZEN_ATTACK_FILE_CENSUS_HASH_V2, FROZEN_ATTACK_FILE_IDS_V2,
    FROZEN_PANEL_ORDER_V2, frozen_feature_allowlist_authorities_v2,
)


class DG05V11R1SourceFileCrosswalkError(ValueError):
    pass


_SOURCE = re.compile(r"^HAI(21|22|23)_TEST([1-9][0-9]*)$")
_PHYSICAL = re.compile(r"^(?:hai-)?test([1-9][0-9]*)\.csv$")


def _valid(value: Mapping[str, Any], schema: str) -> None:
    if value.get("schema") != schema or value.get("self_hash") != digest({k:v for k,v in value.items() if k!="self_hash"}):
        raise DG05V11R1SourceFileCrosswalkError("CROSSWALK_SOURCE_AUTHORITY_REPLAY_FAILED")


def _version_key(dataset_version: str) -> str:
    match=re.match(r"^(21|22|23)\.",dataset_version)
    if match is None:
        raise DG05V11R1SourceFileCrosswalkError("UNRECOGNIZED_FROZEN_DATASET_VERSION")
    return match.group(1)


def _source_identity(*, panel_id: str, dataset_version: str, official_file_id: str) -> tuple[str, int]:
    match=_SOURCE.fullmatch(official_file_id)
    if match is None or match.group(1)!=_version_key(dataset_version):
        raise DG05V11R1SourceFileCrosswalkError("UNRECOGNIZED_OFFICIAL_SOURCE_FILE_NAMESPACE")
    return dataset_version,int(match.group(2))


def _physical_identity(*, panel_id: str, dataset_version: str, physical_file_id: str) -> tuple[str, int]:
    match=_PHYSICAL.fullmatch(physical_file_id)
    if match is None:
        raise DG05V11R1SourceFileCrosswalkError("UNRECOGNIZED_FROZEN_PHYSICAL_FILE_NAMESPACE")
    # The observed panel/version binding is itself frozen by the allowlist
    # authority.  The filename parser extracts only the ordinal.
    return dataset_version,int(match.group(1))


def _source_files(unified_scenario: Mapping[str, Any]) -> dict[tuple[str,str,str], tuple[str,int]]:
    rows: dict[tuple[str,str,str],tuple[str,int]]={}
    for record in unified_scenario.get("canonical_records",()):
        panel=str(record["panel_id"]); version=str(record["dataset_version"]); official=str(record["physical_file_id"])
        key=(panel,version,official); identity=_source_identity(panel_id=panel,dataset_version=version,official_file_id=official)
        if key in rows and rows[key]!=identity:
            raise DG05V11R1SourceFileCrosswalkError("OFFICIAL_SOURCE_IDENTITY_CONFLICT")
        rows[key]=identity
    if len(rows)!=10:
        raise DG05V11R1SourceFileCrosswalkError("SOURCE_FILE_CENSUS_10_REQUIRED")
    return rows


def _physical_files() -> tuple[dict[tuple[str,str,str],tuple[str,int]], str]:
    allowlists=frozen_feature_allowlist_authorities_v2(); rows: dict[tuple[str,str,str],tuple[str,int]]={}
    panel_versions=[]
    for panel in FROZEN_PANEL_ORDER_V2:
        version=str(allowlists[panel].dataset_version); panel_versions.append((panel,version))
        for physical in FROZEN_ATTACK_FILE_IDS_V2[panel]:
            key=(panel,version,physical)
            rows[key]=_physical_identity(panel_id=panel,dataset_version=version,physical_file_id=physical)
    if len(rows)!=10:
        raise DG05V11R1SourceFileCrosswalkError("PHYSICAL_FILE_CENSUS_10_REQUIRED")
    return rows,digest(sorted(panel_versions))


def derive_source_file_identity_crosswalk_v11r1(*, unified_scenario: Mapping[str, Any],
                                                 physical_custody_hash: str, implementation_hash: str,
                                                 source_commit: str) -> dict[str, Any]:
    """Derive, then freeze, the complete version-and-ordinal bijection."""
    _valid(unified_scenario,"hai_official_source_triangulated_scenario_authority_private_v1")
    if type(physical_custody_hash) is not str or len(physical_custody_hash)!=64 or type(implementation_hash) is not str or len(implementation_hash)!=64:
        raise DG05V11R1SourceFileCrosswalkError("CROSSWALK_ROOT_HASH_REQUIRED")
    source=_source_files(unified_scenario); physical,panel_version_hash=_physical_files()
    physical_by_identity: dict[tuple[str,int],list[tuple[str,str,str]]]={}
    for key,identity in physical.items(): physical_by_identity.setdefault(identity,[]).append(key)
    entries=[]
    for source_key,identity in sorted(source.items()):
        candidates=physical_by_identity.get(identity,[])
        if len(candidates)!=1:
            raise DG05V11R1SourceFileCrosswalkError("V11R1_SOURCE_FILE_CROSSWALK_NOT_DETERMINISTIC")
        panel,version,official=source_key; mapped_panel,mapped_version,physical_id=candidates[0]
        if (panel,version)!=(mapped_panel,mapped_version):
            raise DG05V11R1SourceFileCrosswalkError("V11R1_SOURCE_FILE_CROSSWALK_NOT_DETERMINISTIC")
        entries.append(self_hashed({"schema":"v11r1_source_file_identity_crosswalk_entry_v1","panel_id":panel,
            "dataset_version":version,"official_scenario_file_id":official,"frozen_physical_file_id":physical_id,
            "canonical_test_ordinal":identity[1],"source_file_identity_hash":digest(list(source_key)),
            "physical_file_identity_hash":digest(list(candidates[0])),"mapping_reason":"EXACT_VERSION_AND_TEST_ORDINAL_MATCH"}))
    if len({x["official_scenario_file_id"]+"|"+x["panel_id"] for x in entries})!=10 or len({x["frozen_physical_file_id"]+"|"+x["panel_id"] for x in entries})!=10:
        raise DG05V11R1SourceFileCrosswalkError("CROSSWALK_BIJECTION_REQUIRED")
    return self_hashed({"schema":"v11r1_source_file_identity_crosswalk_authority_v1","status":"PASS",
        "mapping_semantic":"EXACT_VERSION_AND_TEST_ORDINAL_BIJECTION",
        "source_unified_scenario_authority_hash":unified_scenario["self_hash"],"physical_custody_hash":physical_custody_hash,
        "frozen_attack_file_census_hash":FROZEN_ATTACK_FILE_CENSUS_HASH_V2,"panel_version_authority_hash":panel_version_hash,
        "entry_count":10,"entries":entries,"adapter_implementation_hash":implementation_hash,"source_commit":source_commit,
        "scientific_semantics_changed":False,"heldout_rows_accessed":0,"predictions_observed":0,"metrics_observed":0})


def verify_source_file_identity_crosswalk_v11r1(*, crosswalk: Mapping[str, Any], unified_scenario: Mapping[str, Any],
                                                 physical_custody_hash: str) -> dict[str, Any]:
    """Independently rederive the mapping; frozen entries are comparison only."""
    _valid(crosswalk,"v11r1_source_file_identity_crosswalk_authority_v1")
    expected=derive_source_file_identity_crosswalk_v11r1(unified_scenario=unified_scenario,
        physical_custody_hash=physical_custody_hash,implementation_hash=crosswalk["adapter_implementation_hash"],source_commit=crosswalk["source_commit"])
    fields=("mapping_semantic","source_unified_scenario_authority_hash","physical_custody_hash","frozen_attack_file_census_hash","panel_version_authority_hash","entry_count","entries","scientific_semantics_changed","heldout_rows_accessed","predictions_observed","metrics_observed")
    if any(crosswalk.get(field)!=expected.get(field) for field in fields):
        raise DG05V11R1SourceFileCrosswalkError("CROSSWALK_INDEPENDENT_REPLAY_MISMATCH")
    return self_hashed({"schema":"v11r1_source_file_identity_crosswalk_independent_replay_v1","status":"PASS",
        "crosswalk_hash":crosswalk["self_hash"],"entries":10,"source_mapped":10,"physical_mapped":10,
        "ambiguous":0,"unmapped":0,"duplicates":0,"heldout_rows_accessed":0})


__all__=["DG05V11R1SourceFileCrosswalkError","derive_source_file_identity_crosswalk_v11r1","verify_source_file_identity_crosswalk_v11r1"]
