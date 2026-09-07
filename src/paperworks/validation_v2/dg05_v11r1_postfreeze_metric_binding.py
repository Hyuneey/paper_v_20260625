"""Mechanical V11R1 post-freeze binding of closed scenario/P1 authorities."""
from __future__ import annotations
from typing import Any, Mapping
from .dg05_production_chain_v11 import digest, self_hashed

class DG05V11R1PostfreezeBindingError(ValueError): pass

_PANELS={"HAI23_TEST2_PRIMARY_HELDOUT_V1":38,"HAI22_EXTERNAL_REPLICATION_V1":58,"HAI21_EXTERNAL_REPLICATION_V1":50}
_STATUS={"P1_ELIGIBLE":"P1_ELIGIBLE","P1_NOT_ELIGIBLE":"OUT_OF_SCOPE","OUT_OF_SCOPE":"OUT_OF_SCOPE","UNRESOLVED":"UNRESOLVED"}

def _doc(value: Any) -> Mapping[str,Any]:
    return value.document() if hasattr(value,"document") else value

def _valid(value: Mapping[str,Any], schema: str) -> None:
    if value.get("schema") != schema or value.get("self_hash") != digest({k:v for k,v in value.items() if k!="self_hash"}):
        raise DG05V11R1PostfreezeBindingError("SOURCE_AUTHORITY_REPLAY_FAILED")

def _metric_intervals(source_intervals: Any) -> list[list[Any]]:
    """Losslessly expose explicit frozen start/end objects as V2 ordered pairs."""
    if type(source_intervals) is not list or not source_intervals:
        raise DG05V11R1PostfreezeBindingError("SOURCE_CLOSED_INTERVALS_REQUIRED")
    if any(type(item) is not dict or set(item)!={"start","end"} for item in source_intervals):
        raise DG05V11R1PostfreezeBindingError("SOURCE_INTERVAL_SCHEMA_NOT_LOSSLESS")
    return [[item["start"],item["end"]] for item in source_intervals]

def build_freeze_bound_authorities(*, unified_scenario: Mapping[str,Any], unified_p1: Mapping[str,Any],
                                   global_freeze: Mapping[str,Any], physical: Any,
                                   timestamps: Mapping[tuple[str,str],Any], release_hash: str,
                                   crosswalk: Mapping[str,Any], adapter_hash: str,
                                   source_commit: str) -> tuple[dict[str,Any],dict[str,Any]]:
    _valid(unified_scenario,"hai_official_source_triangulated_scenario_authority_private_v1")
    _valid(unified_p1,"hai_p1_direct_target_denominator_authority_v2")
    if global_freeze.get("self_hash") != digest({k:v for k,v in global_freeze.items() if k!="self_hash"}): raise DG05V11R1PostfreezeBindingError("GLOBAL_FREEZE_REPLAY_FAILED")
    _valid(crosswalk,"v11r1_source_file_identity_crosswalk_authority_v1")
    if crosswalk.get("source_unified_scenario_authority_hash") != unified_scenario["self_hash"]:
        raise DG05V11R1PostfreezeBindingError("SOURCE_FILE_CROSSWALK_ROOT_MISMATCH")
    physical_doc=_doc(physical); physical_hash=physical_doc.get("self_hash")
    if len(unified_scenario.get("canonical_records",())) != 146 or len(unified_p1.get("decisions",())) != 146: raise DG05V11R1PostfreezeBindingError("SOURCE_146_CENSUS_REQUIRED")
    tdocs={key:_doc(value) for key,value in timestamps.items()}
    decisions={(str(x["dataset_version"]),str(x["scenario_id"])):x for x in unified_p1["decisions"]}
    crosswalk_entries={(str(x["panel_id"]),str(x["dataset_version"]),str(x["official_scenario_file_id"])):x for x in crosswalk["entries"]}
    if len(decisions)!=146: raise DG05V11R1PostfreezeBindingError("P1_DECISION_BIJECTION_REQUIRED")
    records=[]
    for source in unified_scenario["canonical_records"]:
        panel,official_file_id=str(source["panel_id"]),str(source["physical_file_id"])
        entry=crosswalk_entries.get((panel,str(source["dataset_version"]),official_file_id))
        if entry is None: raise DG05V11R1PostfreezeBindingError("SCENARIO_SOURCE_FILE_CROSSWALK_REQUIRED")
        file_id=str(entry["frozen_physical_file_id"]); key=(panel,file_id)
        timestamp=tdocs.get(key)
        if timestamp is None or timestamp.get("physical_file_authority_hash") is None: raise DG05V11R1PostfreezeBindingError("SCENARIO_TIMESTAMP_BINDING_REQUIRED")
        record=self_hashed({"schema":"v11r1_freeze_bound_scenario_record_v1","panel_id":panel,"dataset_version":source["dataset_version"],"file_id":file_id,"source_official_file_id":official_file_id,"frozen_physical_file_id":file_id,"source_file_crosswalk_entry_hash":entry["self_hash"],"scenario_id":source["scenario_id"],"source_closed_intervals":source["closed_intervals"],"closed_intervals":_metric_intervals(source["closed_intervals"]),"interval_schema_translation":"EXPLICIT_FROZEN_START_END_TO_V2_ORDERED_PAIR","attacked_identities":source["attacked_identities"],"explicit_affected_processes":source["explicit_affected_processes"],"physical_file_authority_hash":timestamp["physical_file_authority_hash"],"timestamp_authority_hash":timestamp["self_hash"],"official_source_hash":unified_scenario["version_roots"][str(source["dataset_version"])],"source_unified_scenario_authority_hash":unified_scenario["self_hash"],"source_scenario_record_hash":digest(source)})
        records.append(record)
    if len(records)!=146 or len({(r["panel_id"],r["scenario_id"]) for r in records})!=146: raise DG05V11R1PostfreezeBindingError("SCENARIO_BIJECTION_REQUIRED")
    counts={p:sum(r["panel_id"]==p for r in records) for p in _PANELS}
    if counts!=_PANELS: raise DG05V11R1PostfreezeBindingError("SCENARIO_PANEL_CENSUS_REQUIRED")
    timestamp_hash=digest(sorted((p,f,x["self_hash"]) for (p,f),x in tdocs.items()))
    scenario=self_hashed({"schema":"v11r1_freeze_bound_scenario_authority_v1","status":"FREEZE_BOUND","source_unified_scenario_authority_hash":unified_scenario["self_hash"],"source_file_crosswalk_hash":crosswalk["self_hash"],"global_freeze_hash":global_freeze["self_hash"],"v11r1_release_hash":release_hash,"physical_authority_hash":physical_hash,"timestamp_authority_aggregate_hash":timestamp_hash,"records":sorted(records,key=lambda r:(r["panel_id"],r["file_id"],r["scenario_id"])),"panel_counts":counts,"adapter_implementation_hash":adapter_hash,"source_commit":source_commit,"prediction_inputs":False})
    denom=[]
    for record in scenario["records"]:
        source=decisions.get((str(record["dataset_version"]),str(record["scenario_id"])))
        if source is None or source.get("eligibility_status") not in _STATUS: raise DG05V11R1PostfreezeBindingError("P1_DECISION_LOOKUP_REQUIRED")
        denom.append(self_hashed({"schema":"v11r1_freeze_bound_p1_record_v1","panel_id":record["panel_id"],"scenario_id":record["scenario_id"],"scenario_record_hash":record["self_hash"],"primary_status":_STATUS[source["eligibility_status"]],"source_p1_decision_hash":digest(source),"source_unified_p1_authority_hash":unified_p1["self_hash"],"provenance":"FROZEN_UNIFIED_P1_DECISION_DIRECT_TRANSLATION"}))
    census={s:sum(r["primary_status"]==s for r in denom) for s in ("P1_ELIGIBLE","OUT_OF_SCOPE","UNRESOLVED")}
    if census!={"P1_ELIGIBLE":116,"OUT_OF_SCOPE":30,"UNRESOLVED":0}: raise DG05V11R1PostfreezeBindingError("P1_CENSUS_PRESERVATION_FAILED")
    denominator=self_hashed({"schema":"v11r1_freeze_bound_p1_denominator_authority_v1","status":"FREEZE_BOUND","scenario_authority_hash":scenario["self_hash"],"source_unified_p1_authority_hash":unified_p1["self_hash"],"global_freeze_hash":global_freeze["self_hash"],"v11r1_release_hash":release_hash,"records":sorted(denom,key=lambda r:(r["panel_id"],r["scenario_id"])),"classification_counts":census,"prediction_inputs":False,"adapter_implementation_hash":adapter_hash,"source_commit":source_commit})
    return scenario,denominator

def verify_freeze_bound_authorities(*, scenario: Mapping[str,Any], denominator: Mapping[str,Any],
                                   unified_scenario: Mapping[str,Any], unified_p1: Mapping[str,Any],
                                   global_freeze: Mapping[str,Any], physical: Any,
                                   timestamps: Mapping[tuple[str,str],Any], crosswalk: Mapping[str,Any],
                                   release_hash: str) -> dict[str,Any]:
    """Independently replay every source-to-freeze binding from immutable inputs.

    This deliberately does not call ``build_freeze_bound_authorities``.  The
    canonical source-record binding is ``digest(source_canonical_record)``;
    it is a digest of the immutable source record alone, never of a derived
    wrapper or a document which contains a mutable ``self_hash`` field.
    """
    _valid(scenario,"v11r1_freeze_bound_scenario_authority_v1")
    _valid(denominator,"v11r1_freeze_bound_p1_denominator_authority_v1")
    _valid(unified_scenario,"hai_official_source_triangulated_scenario_authority_private_v1")
    _valid(unified_p1,"hai_p1_direct_target_denominator_authority_v2")
    _valid(crosswalk,"v11r1_source_file_identity_crosswalk_authority_v1")
    if global_freeze.get("self_hash") != digest({k:v for k,v in global_freeze.items() if k!="self_hash"}):
        raise DG05V11R1PostfreezeBindingError("GLOBAL_FREEZE_REPLAY_FAILED")
    physical_doc=_doc(physical)
    tdocs={key:_doc(value) for key,value in timestamps.items()}
    if scenario.get("source_unified_scenario_authority_hash")!=unified_scenario["self_hash"] or scenario.get("source_file_crosswalk_hash")!=crosswalk["self_hash"] or denominator.get("source_unified_p1_authority_hash")!=unified_p1["self_hash"] or scenario.get("global_freeze_hash")!=global_freeze["self_hash"] or denominator.get("global_freeze_hash")!=global_freeze["self_hash"] or denominator.get("scenario_authority_hash")!=scenario["self_hash"] or scenario.get("physical_authority_hash")!=physical_doc.get("self_hash") or scenario.get("v11r1_release_hash")!=release_hash or denominator.get("v11r1_release_hash")!=release_hash:
        raise DG05V11R1PostfreezeBindingError("FREEZE_BOUND_ROOT_MISMATCH")
    if len(unified_scenario.get("canonical_records",()))!=146 or len(unified_p1.get("decisions",()))!=146 or len(scenario.get("records",()))!=146 or len(denominator.get("records",()))!=146:
        raise DG05V11R1PostfreezeBindingError("FREEZE_BOUND_CENSUS_MISMATCH")
    derived_scenarios={(str(x["panel_id"]),str(x["scenario_id"])):x for x in scenario["records"]}
    derived_denominators={(str(x["panel_id"]),str(x["scenario_id"])):x for x in denominator["records"]}
    source_scenarios={(str(x["panel_id"]),str(x["scenario_id"])):x for x in unified_scenario["canonical_records"]}
    decisions={(str(x["dataset_version"]),str(x["scenario_id"])):x for x in unified_p1["decisions"]}
    crosswalk_entries={(str(x["panel_id"]),str(x["dataset_version"]),str(x["official_scenario_file_id"])):x for x in crosswalk["entries"]}
    if len(derived_scenarios)!=146 or len(derived_denominators)!=146 or len(source_scenarios)!=146 or len(decisions)!=146 or set(derived_scenarios)!=set(source_scenarios) or set(derived_denominators)!=set(source_scenarios):
        raise DG05V11R1PostfreezeBindingError("FREEZE_BOUND_BIJECTION_MISMATCH")
    for key, source in source_scenarios.items():
        record=derived_scenarios[key]
        panel,official_file_id=key[0],str(source["physical_file_id"])
        entry=crosswalk_entries.get((panel,str(source["dataset_version"]),official_file_id))
        if entry is None: raise DG05V11R1PostfreezeBindingError("REPLAY_SOURCE_FILE_CROSSWALK_REQUIRED")
        file_id=str(entry["frozen_physical_file_id"])
        timestamp=tdocs.get((panel,file_id))
        if timestamp is None:
            raise DG05V11R1PostfreezeBindingError("REPLAY_TIMESTAMP_BINDING_REQUIRED")
        expected={
            "panel_id":panel,"dataset_version":source["dataset_version"],"file_id":file_id,
            "source_official_file_id":official_file_id,"frozen_physical_file_id":file_id,
            "source_file_crosswalk_entry_hash":entry["self_hash"],
            "scenario_id":source["scenario_id"],"source_closed_intervals":source["closed_intervals"],"closed_intervals":_metric_intervals(source["closed_intervals"]),"interval_schema_translation":"EXPLICIT_FROZEN_START_END_TO_V2_ORDERED_PAIR",
            "attacked_identities":source["attacked_identities"],
            "explicit_affected_processes":source["explicit_affected_processes"],
            "physical_file_authority_hash":timestamp.get("physical_file_authority_hash"),
            "timestamp_authority_hash":timestamp.get("self_hash"),
            "official_source_hash":unified_scenario["version_roots"][str(source["dataset_version"])],
            "source_unified_scenario_authority_hash":unified_scenario["self_hash"],
            "source_scenario_record_hash":digest(source),
        }
        if any(record.get(name)!=value for name,value in expected.items()):
            raise DG05V11R1PostfreezeBindingError("FREEZE_BOUND_SCENARIO_REPLAY_MISMATCH")
        decision=decisions.get((str(source["dataset_version"]),str(source["scenario_id"])))
        denominator_record=derived_denominators[key]
        if decision is None or decision.get("eligibility_status") not in _STATUS:
            raise DG05V11R1PostfreezeBindingError("REPLAY_P1_DECISION_LOOKUP_REQUIRED")
        if denominator_record.get("scenario_record_hash")!=record.get("self_hash") or denominator_record.get("primary_status")!=_STATUS[decision["eligibility_status"]] or denominator_record.get("source_p1_decision_hash")!=digest(decision) or denominator_record.get("source_unified_p1_authority_hash")!=unified_p1["self_hash"]:
            raise DG05V11R1PostfreezeBindingError("FREEZE_BOUND_P1_REPLAY_MISMATCH")
    timestamp_hash=digest(sorted((p,f,x["self_hash"]) for (p,f),x in tdocs.items()))
    if scenario.get("timestamp_authority_aggregate_hash")!=timestamp_hash or scenario.get("panel_counts")!=_PANELS or denominator.get("classification_counts")!={"P1_ELIGIBLE":116,"OUT_OF_SCOPE":30,"UNRESOLVED":0}:
        raise DG05V11R1PostfreezeBindingError("FREEZE_BOUND_AGGREGATE_REPLAY_MISMATCH")
    return self_hashed({"schema":"v11r1_freeze_bound_authority_independent_replay_v1","status":"PASS","scenario_authority_hash":scenario["self_hash"],"denominator_authority_hash":denominator["self_hash"],"source_unified_scenario_authority_hash":unified_scenario["self_hash"],"source_unified_p1_authority_hash":unified_p1["self_hash"],"source_file_crosswalk_hash":crosswalk["self_hash"],"records":146,"classification_counts":denominator["classification_counts"],"global_freeze_hash":global_freeze["self_hash"],"legacy_full_scope_recomputation_used":False})
