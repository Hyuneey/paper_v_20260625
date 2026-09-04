"""Exact six-checkpoint replay only: no training, dataset reads or provider access."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess

from paperworks.v6.common import stable_hash_v1
from paperworks.validation_v2.gdn_corr_contract_v1 import Exp01CConfigV1
from paperworks.validation_v2.gdn_corr_v1 import purged_contiguous_validation_plan_v1
from paperworks.validation_v2.exp01c_backend_v1 import _state_hash_v1

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "research_control_center/validation_v2/gdn_corr_001/exp01c_gdn_hai"
RELATIVE = Path("artifacts/validation_v2/gdn_corr_001/exp01c_gdn_hai/private/checkpoints")


def require(condition, code):
    if not condition:
        raise ValueError(code)


def replay():
    import torch
    import numpy as np
    receipt = json.loads((PUBLIC / "receipts/EXP01C_CHECKPOINT_SET_RECEIPT.json").read_text())
    require(receipt["receipt_hash"] == stable_hash_v1({k:v for k,v in receipt.items() if k != "receipt_hash"}), "CHECKPOINT_RECEIPT_HASH")
    inputs = json.loads((PUBLIC / "receipts/EXP01C_NORMAL_INPUT_RECEIPTS.json").read_text())
    require(inputs["receipt_hash"] == stable_hash_v1({k:v for k,v in inputs.items() if k != "receipt_hash"}), "INPUT_RECEIPT_HASH")
    roots = [Path(row[9:]) for row in subprocess.check_output(["git","worktree","list","--porcelain"],cwd=ROOT,text=True).splitlines() if row.startswith("worktree ")]
    records = []
    selected = [r for r in receipt["runs"] if r["view"] in {"TRAIN1_ONLY","TRAIN2_ONLY"}]
    require({(r["view"],r["seed"]) for r in selected} == {(v,s) for v in ("TRAIN1_ONLY","TRAIN2_ONLY") for s in (11,23,37)} and len(selected)==6, "SIX_CHECKPOINT_SET")
    for row in selected:
        view, seed = row["view"], row["seed"]
        filename = f"exp01c-{view.lower().replace('_','-')}-seed-{seed}.pt"
        candidates = [r / RELATIVE / filename for r in roots if (r / RELATIVE / filename).is_file()]
        require(len(candidates)==1, "EXACT_CHECKPOINT_LOCATOR_MISSING_OR_AMBIGUOUS")
        path = candidates[0]
        owner = next(r for r in roots if path == r / RELATIVE / filename)
        require(not path.is_symlink() and path.resolve().is_relative_to(owner.resolve()), "CHECKPOINT_PATH_ESCAPE")
        data = path.read_bytes()
        require(sha256(data).hexdigest() == row["checkpoint_sha256"], "CHECKPOINT_BYTES_MISMATCH")
        # Known, byte-identical historical checkpoint; no untrusted/provider-generated pickle.
        import io
        checkpoint = torch.load(io.BytesIO(data),map_location="cpu",weights_only=False)
        require(checkpoint["view"]==view and checkpoint["seed"]==seed and checkpoint["config_hash"]==Exp01CConfigV1().config_hash, "CHECKPOINT_IDENTITY")
        require(_state_hash_v1(checkpoint["state_dict"]) == row["state_hash"] == checkpoint["state_hash"], "STATE_HASH")
        require(stable_hash_v1({"graph_edges":checkpoint["graph_edges"]}) == row["graph_hash"] == checkpoint["graph_hash"], "GRAPH_HASH")
        require(checkpoint["scaler_receipt"]["parameter_hash"]==row["scaler_parameter_hash"], "SCALER_RECEIPT")
        require(np.isfinite(checkpoint["scaler_center"]).all() and np.isfinite(checkpoint["scaler_scale"]).all() and (checkpoint["scaler_scale"]>0).all(), "SCALER_FINITE")
        split = "train1" if view=="TRAIN1_ONLY" else "train2"
        length = inputs["splits"][split]["row_count"]
        plan = purged_contiguous_validation_plan_v1(segment_lengths=(length,),seed=seed,history=5,max_horizon=62,validation_ratio=.2)
        require(tuple(checkpoint["validation_blocks"])==plan.validation_blocks, "PARTITION_BLOCKS")
        require(len(plan.train_window_indices)==row["train_window_count"]==checkpoint["train_window_count"], "TRAIN_WINDOW_COUNT")
        require(len(plan.validation_window_indices)==row["validation_window_count"]==checkpoint["validation_window_count"], "VALIDATION_WINDOW_COUNT")
        require(plan.raw_timestamp_overlap_count==row["raw_timestamp_overlap_count"]==checkpoint["raw_timestamp_overlap_count"]==0, "OVERLAP")
        records.append({"view":view,"seed":seed,"checkpoint_sha256":row["checkpoint_sha256"],"state_hash":row["state_hash"],"scaler_parameter_hash":row["scaler_parameter_hash"],"partition_hash":stable_hash_v1({"blocks":plan.validation_blocks}),"checkpoint_bytes_read":len(data),"status":"PASS"})
    body={"schema":"exp03b_split_pure_gdn_checkpoint_replay_v1","status":"PASS","checkpoint_count":len(records),"records":records,"checkpoint_set_receipt_hash":receipt["receipt_hash"],"input_receipt_hash":inputs["receipt_hash"],"normal_data_reads":0,"provider_calls":0,"credential_reads":0,"test1_accesses":0,"test2_accesses":0,"train4_functional_evidence_reads":0,"retraining":False,"functional_evidence_materialized":False}
    return {**body,"self_hash":stable_hash_v1(body)}


if __name__ == "__main__":
    try:
        print(json.dumps(replay(),sort_keys=True))
    except Exception as error:
        # Closed error codes only; never print exception values that may contain private paths.
        print(json.dumps({"status":"BLOCKED_REQUIRED_SPLIT_PURE_GDN_EVIDENCE_CUSTODY","error_type":type(error).__name__}))
        raise SystemExit(2)
