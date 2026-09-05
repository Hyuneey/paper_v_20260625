"""Global all-panel prediction-before-any-label custody contracts.

The module is prospective and synthetic-testable.  It cannot read datasets;
callers must present hash-only receipts from the existing durable custody layer.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
import secrets
from typing import Any, Mapping, Sequence


class MultiPanelCustodyError(ValueError): pass
def _canon(value: Mapping[str,Any]) -> bytes:return json.dumps(dict(value),sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()
def _hash(value: Mapping[str,Any])->str:return sha256(_canon(value)).hexdigest()
def _sha(value: str, field: str)->None:
    if type(value) is not str or len(value)!=64 or any(c not in '0123456789abcdef' for c in value):raise MultiPanelCustodyError(f'{field} must be sha256')


class GlobalPredictionStateV1(str,Enum):
    ATTACK_CONTAINER_CUSTODIED_LABEL_LOCKED='ATTACK_CONTAINER_CUSTODIED_LABEL_LOCKED'
    ATTACK_FEATURE_PROJECTION_READY_LABEL_LOCKED='ATTACK_FEATURE_PROJECTION_READY_LABEL_LOCKED'
    PREDICTIONS_IN_PROGRESS_LABEL_LOCKED='PREDICTIONS_IN_PROGRESS_LABEL_LOCKED'
    GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED='GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED'
    LABEL_SCENARIO_LEASE_OPEN='LABEL_SCENARIO_LEASE_OPEN'
    RESULTS_COMPUTED='RESULTS_COMPUTED'


@dataclass(frozen=True)
class PredictionCellReceiptV1:
    panel_id:str; file_id:str; method_id:str; method_authority_hash:str
    feature_projection_hash:str; prediction_artifact_hash:str; row_count:int
    timestamp_range_hash:str; alarm_count:int; system_error_count:int
    runtime_milliseconds:int; source_commit:str
    def document(self)->dict[str,Any]:return dict(self.__dict__)
    def validate(self)->None:
        for field in ('panel_id','file_id','method_id','source_commit'):
            if not isinstance(getattr(self,field),str) or not getattr(self,field):raise MultiPanelCustodyError('invalid prediction identity')
        for field in ('method_authority_hash','feature_projection_hash','prediction_artifact_hash','timestamp_range_hash'):_sha(getattr(self,field),field)
        if type(self.row_count) is not int or self.row_count<=0 or any(type(getattr(self,f)) is not int or getattr(self,f)<0 for f in ('alarm_count','system_error_count','runtime_milliseconds')):raise MultiPanelCustodyError('invalid prediction census')
        if self.alarm_count>self.row_count:raise MultiPanelCustodyError('alarm count exceeds rows')


@dataclass(frozen=True)
class GlobalPredictionManifestV1:
    expected_cells:tuple[tuple[str,str,str],...]
    receipts:tuple[PredictionCellReceiptV1,...]
    evaluation_policy_hash:str; metric_authority_hash:str; dg05_authorization_hash:str
    state:GlobalPredictionStateV1=GlobalPredictionStateV1.GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED
    def document(self)->dict[str,Any]:
        body={'schema':'multipanel_global_prediction_manifest_v1','expected_cells':[list(v) for v in self.expected_cells],
              'receipts':[v.document() for v in self.receipts],'evaluation_policy_hash':self.evaluation_policy_hash,
              'metric_authority_hash':self.metric_authority_hash,'dg05_authorization_hash':self.dg05_authorization_hash,
              'state':self.state.value}
        return {**body,'self_hash':_hash(body)}
    def validate(self)->None:
        for value,name in ((self.evaluation_policy_hash,'evaluation_policy_hash'),(self.metric_authority_hash,'metric_authority_hash'),(self.dg05_authorization_hash,'dg05_authorization_hash')):_sha(value,name)
        if self.state is not GlobalPredictionStateV1.GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED:raise MultiPanelCustodyError('global freeze state required')
        if not self.expected_cells or tuple(sorted(set(self.expected_cells)))!=self.expected_cells:raise MultiPanelCustodyError('expected cells must be exact sorted unique authority')
        for item in self.receipts:item.validate()
        actual=tuple(sorted((r.panel_id,r.file_id,r.method_id) for r in self.receipts))
        if actual!=self.expected_cells:raise MultiPanelCustodyError('GLOBAL_PREDICTION_CELL_CENSUS_INCOMPLETE')
        if len({(r.panel_id,r.file_id,r.prediction_artifact_hash) for r in self.receipts})!=len(self.receipts):raise MultiPanelCustodyError('prediction receipt alias')


class LabelScenarioLeaseV1:
    __slots__=('__token','manifest_hash','used')
    def __init__(self,manifest_hash:str):self.__token=secrets.token_hex(32);self.manifest_hash=manifest_hash;self.used=False
    def __repr__(self)->str:return 'LabelScenarioLeaseV1(<opaque>)'


def issue_label_scenario_lease_v1(manifest:GlobalPredictionManifestV1)->LabelScenarioLeaseV1:
    if type(manifest) is not GlobalPredictionManifestV1:raise MultiPanelCustodyError('typed manifest required')
    manifest.validate();return LabelScenarioLeaseV1(manifest.document()['self_hash'])


def consume_label_scenario_lease_v1(lease:LabelScenarioLeaseV1,manifest:GlobalPredictionManifestV1,reader):
    if type(lease) is not LabelScenarioLeaseV1 or lease.used:raise MultiPanelCustodyError('invalid or consumed label lease')
    manifest.validate()
    if manifest.document()['self_hash']!=lease.manifest_hash:raise MultiPanelCustodyError('manifest mutated before label access')
    if not callable(reader):raise MultiPanelCustodyError('label reader must be callable')
    lease.used=True;return reader()


def validate_attack_feature_projection_contract_v1(document:Mapping[str,Any])->None:
    required={'panel_id','file_id','timestamp_id','approved_feature_ids','projection_hash','row_count','label_values_parsed','scenario_values_parsed'}
    if set(document)!=required or document['label_values_parsed'] is not False or document['scenario_values_parsed'] is not False:raise MultiPanelCustodyError('feature projection contract tainted')
    if not document['approved_feature_ids'] or any(not x.startswith('P1_') for x in document['approved_feature_ids']):raise MultiPanelCustodyError('positive feature allowlist required')
    _sha(document['projection_hash'],'projection_hash')


__all__=['GlobalPredictionStateV1','PredictionCellReceiptV1','GlobalPredictionManifestV1','LabelScenarioLeaseV1',
         'issue_label_scenario_lease_v1','consume_label_scenario_lease_v1','validate_attack_feature_projection_contract_v1','MultiPanelCustodyError']
