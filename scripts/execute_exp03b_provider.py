"""Future DG-03B execution only. Import/help never reads credentials or calls APIs."""
from pathlib import Path
from dataclasses import asdict
from hashlib import sha256
import argparse
import json
import time
from paperworks.validation_v2.exp03b_contract_v1 import require,encoded,digest,parse_proposal,proposal_document
from paperworks.validation_v2.exp03b_custody_v1 import publish,seal,replay
from paperworks.validation_v2.exp03b_prompt import request_body,ENDPOINT
from paperworks.validation_v2.exp03b_provider_gate import ProviderCallGate
from paperworks.validation_v2.exp03b_codec import structural
from paperworks.validation_v2.exp03b_verifier_v1 import Train2HiddenVerifierAuthorityV1,feedback,retrieval,select_t1b,VerifierResultV1
from paperworks.validation_v2.exp03b_admission_verifier import verify
from paperworks.validation_v2.exp03b_execution import admit

ROOT=Path(__file__).resolve().parents[1]
PUBLIC=ROOT/"research_control_center/validation_v2/exp03b"
PRIVATE=ROOT/"artifacts/validation_v2/exp03b/private"

class ParsedResponseFailure(ValueError):
    pass


def transport(body):
    # Reachable only after explicit DG-03B approval, source replay and reservation.
    import os
    from urllib.request import Request,urlopen
    key=os.environ.get("OPENAI_API_KEY")
    require(bool(key),"APPROVED_PROVIDER_CREDENTIAL_UNAVAILABLE")
    request=Request(ENDPOINT,data=encoded(body),headers={"Content-Type":"application/json","Authorization":"Bearer "+key},method="POST")
    with urlopen(request,timeout=60) as response:return json.loads(response.read())


def response_proposal(response):
    text="".join(part.get("text","") for item in response.get("output",[]) if item.get("type")=="message" for part in item.get("content",[]) if part.get("type")=="output_text")
    try:
        require(bool(text),"EMPTY_RESPONSE")
        return parse_proposal(json.loads(text))
    except (ValueError,TypeError,KeyError) as error:raise ParsedResponseFailure("PARSE_FAILURE") from error


def main(approval_path:Path,probe_only:bool):
    budget=json.loads((PUBLIC/"EXP03B_PROVIDER_BUDGET_V1.json").read_text());replay(budget)
    freeze=json.loads((PUBLIC/"EXP03B_FINAL_PREPARATION_FREEZE_V2.json").read_text());replay(freeze)
    for relative,expected in freeze["implementation_hashes"].items():require(sha256((ROOT/relative).read_bytes()).hexdigest()==expected,"EXECUTION_CODE_CHANGED")
    approval=json.loads(approval_path.read_text());replay(approval)
    gate=ProviderCallGate(budget,approval,freeze["self_hash"])
    require(freeze["status"]=="PREPARED_DG03B_PENDING","FULL_PREPARATION_REQUIRED")
    for name,h in freeze['private_input_hashes'].items():
        if name.split('/')[0] in ('train1','train2'):
            require(sha256((PRIVATE/name).read_bytes()).hexdigest()==h,'PROVIDER_INPUT_CUSTODY_CHANGED')
    # Exact known records, no dataset/label/test discovery.
    for split in ("train1","train2"):
        receipt=json.loads((PUBLIC/f"EXP03B_{split.upper()}_EVIDENCE_RECEIPT_V1.json").read_text());replay(receipt)
        for record in receipt["records"]:
            p=PRIVATE/split/("provider" if split=="train1" else "structural")/(record["candidate_id"]+".json")
            value=p.read_bytes()
            actual=sha256(value).hexdigest() if split=="train1" else digest(json.loads(value))
            require(actual==record["content_hash"],"EVIDENCE_CUSTODY_CHANGED")
    runroot=PRIVATE/"provider_execution_v1";runroot.mkdir(parents=True,exist_ok=True)
    lock=runroot/"SINGLE_WRITER.lock"
    with lock.open("x") as stream:stream.write("EXP03B_SINGLE_WRITER")
    try:
        # A pending unmatched request is never automatically retried.
        for index in range(1,budget["maximum_calls"]+1):
            reservation=runroot/"calls"/f"{index:04d}.request.json"
            if not reservation.exists():break
            saved=json.loads(reservation.read_text());replay(saved)
            responsepath=runroot/"calls"/f"{index:04d}.response.json"
            require(responsepath.exists(),"UNRESOLVED_PROVIDER_REQUEST_NO_AUTORETRY")
            response=json.loads(responsepath.read_text());replay(response)
            require(response['request_hash']==digest(saved['request'])==saved['reservation']['request_hash'],'CALL_RESPONSE_REQUEST_BINDING')
            rr=gate.reserve(slot=saved["slot"],request=saved["request"],input_upper_bound=saved["input_upper_bound"])
            require(asdict(rr)==saved['reservation'],'RESERVATION_REPLAY_CHANGED')
            item=gate.reconcile(input_tokens=response["usage"]["input_tokens"],output_tokens=response["usage"]["output_tokens"],response_hash=digest(response["response"]),model=response["response"]["model"],latency=response["latency_seconds"])
            persisted=json.loads((runroot/'calls'/f'{index:04d}.receipt.json').read_text());replay(persisted)
            require(persisted==seal(item),'CALL_RECEIPT_REPLAY_CHANGED')
            if index==1:
                probe=json.loads((runroot/"ONE_CALL_CAPABILITY_RECEIPT.json").read_text());replay(probe)
                require(probe["status"]=="PASS" and probe["call_receipt_hash"]==digest(item) and probe["budget_hash"]==budget["self_hash"],"ONE_CALL_RECEIPT_REPLAY")
                response_proposal(response["response"])
                gate.accept_one_call_receipt(digest(item),persisted_and_replayed=True,privacy_pass=True,schema_pass=True)
        existing={r.slot:r.index for r in gate.reservations}
        if probe_only and gate.one_call_pass:
            raise StopIteration
        def call(slot,body):
            if slot in existing:
                saved=json.loads((runroot/'calls'/f'{existing[slot]:04d}.request.json').read_text())
                require(digest(body)==digest(saved['request']),'RESUMED_PROMPT_CHANGED')
                response=json.loads((runroot/"calls"/f"{existing[slot]:04d}.response.json").read_text())
                return response_proposal(response["response"])
            bound=len(encoded(body))+budget["framing_allowance"]
            reservation=gate.reserve(slot=slot,request=body,input_upper_bound=bound)
            publish(runroot/"calls"/f"{reservation.index:04d}.request.json",seal({"slot":slot,"reservation":asdict(reservation),"request":body,"input_upper_bound":bound}))
            start=time.perf_counter();response=transport(body);elapsed=time.perf_counter()-start
            usage=response.get("usage",{})
            document=seal({"response":response,"usage":usage,"latency_seconds":elapsed,"request_hash":digest(body)})
            publish(runroot/"calls"/f"{reservation.index:04d}.response.json",document)
            receipt=gate.reconcile(input_tokens=usage["input_tokens"],output_tokens=usage["output_tokens"],response_hash=digest(response),model=response["model"],latency=elapsed)
            publish(runroot/"calls"/f"{reservation.index:04d}.receipt.json",seal(receipt))
            try:proposal=response_proposal(response)
            except ParsedResponseFailure:
                if reservation.index==1:raise RuntimeError("ONE_CALL_SCHEMA_PROBE_FAILED")
                raise
            if reservation.index==1:
                gate.accept_one_call_receipt(digest(receipt),persisted_and_replayed=True,privacy_pass=True,schema_pass=True)
                publish(runroot/"ONE_CALL_CAPABILITY_RECEIPT.json",seal({"status":"PASS","call_receipt_hash":digest(receipt),"request_hash":digest(body),"budget_hash":budget["self_hash"]}))
                if probe_only:raise StopIteration
            return proposal
        cohort=json.loads((PUBLIC/"EXP03B_COHORT_AUTHORITY_V1.json").read_text());replay(cohort)
        terminals=[]
        for pair in cohort["pairs"]:
            cid=pair["candidate_id"]
            e=json.loads((PRIVATE/"train1/provider"/(cid+".json")).read_text())
            hidden=structural(json.loads((PRIVATE/"train2/structural"/(cid+".json")).read_text()),"train2")
            ids=frozenset([r[7] for r in e["structural_rows"]]+[r[11] for r in e["option_rows"]])
            authority=Train2HiddenVerifierAuthorityV1(hidden,ids)
            for arm in ("T1","T1-B","T2"):
                for repeat in (1,2,3):
                    draws=[];repair=None;retrieval_ids=frozenset();fbs=[]
                    for draw in range(1,2 if arm=="T1" else 4):
                        slot=f"{cid}.{arm}.R{repeat}.C{draw}"
                        try:p=call(slot,request_body(e,repair=repair))
                        except ParsedResponseFailure:
                            # No response/provider failure is a scientific NO_RULE.
                            p=None;v=VerifierResultV1("REJECTED",((-1,"PARSE_FAILURE"),),0)
                        else:v=verify(p,authority,retrieval_ids=retrieval_ids)
                        draws.append((p,v))
                        if arm=="T2":
                            if v.status!="NEEDS_REPAIR" or draw==3:break
                            f=feedback(p,v,draw);q=retrieval(authority,p,v);fbs.append(f)
                            retrieval_ids|=frozenset(x["evidence_slice_id"] for x in q["alternatives"])
                            repair={"previous_proposal":proposal_document(p),"feedback":f,"retrieval":q}
                    selected=select_t1b(draws) if arm=="T1-B" else len(draws)-1
                    p,v=draws[selected];accepted=None
                    if v.status=="ACCEPTED":accepted=admit(p,authority,implementation_hash=freeze["implementation_bundle_hash"],config_hash=budget["config_hash"],retrieval_ids=retrieval_ids).receipt
                    terminal="ACCEPTED_RULE_SET" if accepted and p.rules else "INTENTIONAL_NO_RULE" if accepted else "NEEDS_REPAIR_BUDGET_EXHAUSTED" if arm=="T2" and v.status=="NEEDS_REPAIR" else "VERIFIER_REJECTION"
                    if not accepted and p is None:terminal="ALL_DRAWS_FAILED" if arm=="T1-B" and all(x is None for x,_ in draws) else "PARSE_FAILURE"
                    row=seal({"candidate_id":cid,"arm":arm,"repeat":repeat,"raw":[proposal_document(x) if x else None for x,_ in draws],"verifier_results":[asdict(x) for _,x in draws],"selected_draw":selected+1,"admission_receipt":accepted,"terminal":terminal,"feedback":fbs})
                    publish(runroot/"outputs"/f"{cid}.{arm}.R{repeat}.json",row);terminals.append(row["self_hash"])
        publish(runroot/"ALL_ARM_OUTPUTS_FROZEN.json",seal({"terminal_hashes":terminals,"count":len(terminals),"calls":len(gate.receipts),"budget_hash":budget["self_hash"],"train3_evaluation_allowed":True,"train4_guard_after_train3_only":True,"test_access_allowed":False}))
        print(json.dumps({"status":"ALL_PROVIDER_OUTPUTS_FROZEN","next":"HIDDEN_TRAIN3_AND_TRAIN4_LOCAL_EVALUATION_THEN_DG04"}))
    except StopIteration:print(json.dumps({"status":"ONE_CALL_RECEIPT_PASS","full_schedule_started":False}))
    finally:lock.unlink()


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--approval",type=Path,required=True);parser.add_argument("--probe-only",action="store_true");args=parser.parse_args()
    try:main(args.approval,args.probe_only)
    except Exception as error:
        print(json.dumps({"status":"FAIL_CLOSED","error_type":type(error).__name__}));raise SystemExit(2)
