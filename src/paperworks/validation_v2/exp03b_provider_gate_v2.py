"""Revised approval, per-phase reservations and receipt-first single writer."""
from dataclasses import dataclass
from decimal import Decimal
import re
from .exp03b_contract_v1 import require,digest,encoded
from .exp03b_custody_v1 import replay
from .exp03b_prompt_v2 import request_body


@dataclass(frozen=True)
class Reservation:
    index:int
    slot:str
    input_cap:int
    output_cap:int
    request_hash:str


class ProviderCallGate:
    def __init__(self,budget,approval,execution_freeze_hash):
        replay(budget)
        require(approval.get('gate')=='DG-03B_REVISED' and approval.get('status')=='APPROVED' and approval.get('budget_hash')==budget['self_hash'] and approval.get('execution_freeze_hash')==execution_freeze_hash,'DG03B_REVISED_USER_APPROVAL_REQUIRED')
        require(budget['model']=='gpt-5.4-mini-2026-03-17','EXACT_SNAPSHOT_REQUIRED')
        self.budget=budget;self.reservations=[];self.receipts=[];self.in_flight=None;self.one_call_pass=False
    def reserve(self,*,slot,request,input_upper_bound):
        import json
        match=re.fullmatch(r'(EXP03B-CAND-[0-9a-f]{20})\.(T1|T1-B|T2)\.R([123])\.C([123])',slot)
        require(match is not None,'CALL_SLOT_INVALID')
        cid,arm,repeat,draw=match.groups();draw=int(draw)
        require(cid in self.budget['candidate_ids'] and (arm!='T1' or draw==1),'CALL_SLOT_INVALID')
        content=json.loads(request['input'])
        require(content['evidence']['candidate_id']==cid and set(content)<= {'evidence','repair'},'REQUEST_PAIR_BINDING')
        repair=content.get('repair');require((repair is not None)==(arm=='T2' and draw>1),'STATELESS_OR_REPAIR_BOUNDARY')
        if repair is not None:require(repair['feedback']['remaining_call_budget']==4-draw,'REPAIR_CALL_BINDING')
        require(request==request_body(content['evidence'],repair=repair),'FROZEN_REQUEST_CONFIG')
        phase='repair' if repair is not None else 'initial';cap=self.budget['phase_input_caps'][phase]
        require(type(input_upper_bound) is int and len(encoded(request))+self.budget['framing_allowance']<=input_upper_bound<=cap,'CALL_INPUT_CAP')
        require(self.in_flight is None,'CONCURRENCY_ONE')
        require(not self.reservations or self.one_call_pass,'ONE_CALL_RECEIPT_FIRST')
        require(len(self.reservations)<self.budget['maximum_calls'] and slot not in [r.slot for r in self.reservations],'CALL_COUNT_OR_DUPLICATE')
        if draw>1:require(slot[:-1]+str(draw-1) in [r.slot for r in self.reservations],'CALL_SEQUENCE')
        output=self.budget['output_tokens_per_call_cap']
        reserved_input=sum(r.input_cap for r in self.reservations)+cap;reserved_output=sum(r.output_cap for r in self.reservations)+output
        require(reserved_input<=self.budget['maximum_input_tokens'] and reserved_output<=self.budget['maximum_output_tokens'],'TOTAL_RESERVATION_CAP')
        require((Decimal(reserved_input)*Decimal('.75')+Decimal(reserved_output)*Decimal('4.5'))/1000000<=Decimal(self.budget['standard_api_cost_ceiling_usd']),'COST_RESERVATION_CAP')
        r=Reservation(len(self.reservations)+1,slot,cap,output,digest(request));self.reservations.append(r);self.in_flight=r;return r
    def reconcile(self,*,input_tokens,output_tokens,response_hash,model,latency):
        r=self.in_flight;require(r is not None,'NO_INFLIGHT_CALL')
        require(type(input_tokens) is int and type(output_tokens) is int and 0<=input_tokens<=r.input_cap and 0<=output_tokens<=r.output_cap,'PROVIDER_USAGE_CAP')
        require(model==self.budget['model'] and re.fullmatch('[0-9a-f]{64}',response_hash) is not None,'PROVIDER_RESPONSE_IDENTITY')
        receipt={'index':r.index,'slot':r.slot,'request_hash':r.request_hash,'response_hash':response_hash,'input_tokens':input_tokens,'output_tokens':output_tokens,'latency_seconds':latency}
        self.receipts.append(receipt);self.in_flight=None;return receipt
    def accept_one_call_receipt(self,receipt_hash,*,persisted_and_replayed,privacy_pass,schema_pass):
        require(len(self.receipts)==1 and self.in_flight is None and digest(self.receipts[0])==receipt_hash and persisted_and_replayed and privacy_pass and schema_pass,'ONE_CALL_PROBE_FAILED')
        self.one_call_pass=True


def validate_call_inventory(runroot,maximum_calls):
    """Reject gaps/orphans BEFORE resumed transport, including a missing middle request."""
    groups={kind:set() for kind in ('request','response','receipt')}
    for path in (runroot/'calls').glob('*.json'):
        m=re.fullmatch(r'([0-9]{4})\.(request|response|receipt)\.json',path.name)
        require(m is not None and not path.is_symlink(),'CALL_LEDGER_FILENAME')
        index=int(m[1]);require(1<=index<=maximum_calls,'CALL_LEDGER_INDEX');groups[m[2]].add(index)
    indices=set().union(*groups.values())
    require(all(v==indices for v in groups.values()) and indices==set(range(1,len(indices)+1)),'UNRESOLVED_OR_NONCONTIGUOUS_CALL_LEDGER')
    return len(indices)
