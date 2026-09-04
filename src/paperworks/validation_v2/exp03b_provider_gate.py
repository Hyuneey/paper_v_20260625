"""Receipt-first one-call and total reservation accounting. No network or secrets."""
from dataclasses import dataclass
from decimal import Decimal
from .exp03b_contract_v1 import require,digest


@dataclass(frozen=True)
class Reservation:
    index:int
    slot:str
    input_cap:int
    output_cap:int
    request_hash:str


class ProviderCallGate:
    def __init__(self, budget:dict, approval:dict, execution_freeze_hash:str):
        require(approval.get("gate")=="DG-03B" and approval.get("status")=="APPROVED" and approval.get("budget_hash")==budget["self_hash"] and approval.get("execution_freeze_hash")==execution_freeze_hash,"DG03B_USER_APPROVAL_REQUIRED")
        require(budget["model"]=="gpt-5.4-mini-2026-03-17","EXACT_SNAPSHOT_REQUIRED")
        self.budget=budget;self.reservations=[];self.receipts=[];self.in_flight=None;self.one_call_pass=False
    def reserve(self,*,slot:str,request:dict,input_upper_bound:int)->Reservation:
        require(self.in_flight is None,"CONCURRENCY_ONE")
        require(not self.reservations or self.one_call_pass,"ONE_CALL_RECEIPT_FIRST")
        require(len(self.reservations)<self.budget["maximum_calls"] and input_upper_bound<=self.budget["input_tokens_per_call_cap"],"CALL_OR_INPUT_CAP")
        require(request.get("model")==self.budget["model"] and request.get("max_output_tokens")==self.budget["output_tokens_per_call_cap"],"REQUEST_BINDING")
        require(slot not in [r.slot for r in self.reservations],"NO_DUPLICATE_CALL_SLOT")
        r=Reservation(len(self.reservations)+1,slot,self.budget["input_tokens_per_call_cap"],self.budget["output_tokens_per_call_cap"],digest(request))
        self.reservations.append(r);self.in_flight=r;return r
    def reconcile(self,*,input_tokens:int,output_tokens:int,response_hash:str,model:str,latency:float):
        r=self.in_flight;require(r is not None,"NO_INFLIGHT_CALL")
        require(type(input_tokens) is int and type(output_tokens) is int and 0<=input_tokens<=r.input_cap and 0<=output_tokens<=r.output_cap,"PROVIDER_USAGE_CAP")
        require(model==self.budget["model"] and len(response_hash)==64,"PROVIDER_RESPONSE_IDENTITY")
        receipt={"index":r.index,"slot":r.slot,"request_hash":r.request_hash,"response_hash":response_hash,"input_tokens":input_tokens,"output_tokens":output_tokens,"latency_seconds":latency}
        self.receipts.append(receipt);self.in_flight=None
        require(sum(x["input_tokens"] for x in self.receipts)<=self.budget["maximum_input_tokens"] and sum(x["output_tokens"] for x in self.receipts)<=self.budget["maximum_output_tokens"],"TOTAL_TOKEN_CAP")
        cost=sum(Decimal(x["input_tokens"])*Decimal(".75")+Decimal(x["output_tokens"])*Decimal("4.50") for x in self.receipts)/1000000
        require(cost<=Decimal(self.budget["standard_api_cost_ceiling_usd"]),"COST_CAP")
        return receipt
    def accept_one_call_receipt(self,receipt_hash:str,*,persisted_and_replayed:bool,privacy_pass:bool,schema_pass:bool):
        require(len(self.receipts)==1 and self.in_flight is None and digest(self.receipts[0])==receipt_hash and persisted_and_replayed and privacy_pass and schema_pass,"ONE_CALL_PROBE_FAILED")
        self.one_call_pass=True
