"""V11 authority-gated production route entrypoint.

The scientific prediction kernel remains the existing frozen V5 route; this
entrypoint adds no scorer and no fallback.  It admits a schedule only after the
V11 scenario/P1 custodian preflight succeeds.
"""
from __future__ import annotations
from typing import Any,Mapping
from .dg05_label_custodian_v3 import prepare_custodian_input_v3
from .dg05_production_chain_v11 import resolve_frozen_kernel_v11
from pathlib import Path
class DG05ProductionRouteV11Error(ValueError):pass
def initialize_prediction_schedule_v11(*,unified_scenario:Mapping[str,Any],unified_p1:Mapping[str,Any],state:Mapping[str,Any],repository_root:Path|None=None)->dict[str,Any]:
 try:input_doc=prepare_custodian_input_v3(unified_scenario=unified_scenario,unified_p1=unified_p1,predecessor_state=state)
 except Exception as exc:raise DG05ProductionRouteV11Error(str(exc)) from exc
 root=repository_root or Path(__file__).resolve().parents[3]
 kernel=resolve_frozen_kernel_v11(root)
 return {'schema':'dg05_production_route_v11_initialization_v1','state':'V11_SCENARIO_AND_P1_AUTHORITY_READY_NO_PREDICTION_EXECUTED','scenario_authority_hash':input_doc['scenario_authority_hash'],'p1_authority_hash':input_doc['p1_authority_hash'],'scientific_kernel_route':'dg05_production_route_v5.execute_prediction_schedule_v5','resolved_kernel':kernel,'alternate_scientific_route':False,'synthetic_fallback_authorized':False,'heldout_prediction_cells':0,'metric_cells':0}
