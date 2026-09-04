"""Append-only preparation custody; exact normal split capability, no provider API."""
from hashlib import sha256
from pathlib import Path
import json
import os
import subprocess
from .exp03b_contract_v1 import require, encoded, digest


def publish(path: Path, value: dict) -> str:
    payload=encoded(value)+b"\n"
    path.parent.mkdir(parents=True,exist_ok=True)
    require(not path.is_symlink(),"CUSTODY_SYMLINK")
    if path.exists():
        require(path.read_bytes()==payload,"APPEND_ONLY_ARTIFACT_CONFLICT")
        return sha256(payload).hexdigest()
    temp=path.with_suffix(path.suffix+".partial")
    with temp.open("xb") as stream:
        stream.write(payload);stream.flush();os.fsync(stream.fileno())
    os.rename(temp,path)
    require(path.read_bytes()==payload,"DURABLE_REPLAY_FAILED")
    return sha256(payload).hexdigest()


def seal(value: dict) -> dict:
    require("self_hash" not in value,"ALREADY_SEALED")
    return {**value,"self_hash":digest(value)}


def replay(value: dict) -> None:
    require(value.get("self_hash")==digest({k:v for k,v in value.items() if k!="self_hash"}),"SELF_HASH_REPLAY")


def registered_roots(root: Path) -> tuple[Path,...]:
    return tuple(Path(line[9:]) for line in subprocess.check_output(["git","worktree","list","--porcelain"],cwd=root,text=True).splitlines() if line.startswith("worktree "))


def normal_capability(root: Path):
    from .hai_feature_adapter_v1 import resolve_hai_feature_root_capability_v1, _binding_from_file
    roots=registered_roots(root)
    bindings={}
    # Only previously issued, exactly named normal-data locator records; no host search.
    for owner in roots:
        value=_binding_from_file(owner/".env.custody.local")
        if value:bindings.setdefault(str(Path(value).resolve()),owner)
    public=json.loads((root/"research_control_center/validation_v2/receipts/HAI_NORMAL_ONLY_MATERIALIZATION_RECEIPT_V2.json").read_text())
    replay(public)
    matched={}
    for value,owner in bindings.items():
        manifest=Path(value)/".validation_v2_normal_materialization_manifest.json"
        if manifest.is_file() and not manifest.is_symlink():
            document=json.loads(manifest.read_text());replay(document)
            if document["self_hash"]==public["private_manifest_hash"]:matched[value]=owner
    bindings=matched
    require(len(bindings)==1,"BLOCKED_REQUIRED_NORMAL_DATA_CUSTODY")
    owner=next(iter(bindings.values()))
    return resolve_hai_feature_root_capability_v1(owner)


def load_normal(root: Path, split: str, source_commit: str):
    from .hai_feature_adapter_v1 import HAIFeatureAccessLedgerV1,load_authorized_hai_feature_frame_for_operations_v1
    from .protocol_v1 import ProtocolExecutionGuardV1,ProtocolOperationV1,build_validation_protocol_v1
    require(split in ("train1","train2","train4"),"EXP03B_SPLIT_PROHIBITED")
    cap=normal_capability(root)
    guard=ProtocolExecutionGuardV1(build_validation_protocol_v1(source_commit=source_commit))
    ledger=HAIFeatureAccessLedgerV1(experiment_id="EXP03B-BIND-001")
    operations=(ProtocolOperationV1.RELATION_FIT,ProtocolOperationV1.NUMERIC_FIT) if split!="train4" else (ProtocolOperationV1.NORMAL_SANITY,)
    frame=load_authorized_hai_feature_frame_for_operations_v1(capability=cap,split_id=split,operations=operations,protocol_guard=guard,ledger=ledger)
    return frame.numeric_matrix(),frame.receipt.to_dict(),ledger.public_document()


def load_checkpoint(root: Path, split: str, seed: int):
    import io
    import torch
    from .exp01c_backend_v1 import _state_hash_v1
    from .gdn_corr_contract_v1 import Exp01CConfigV1
    from paperworks.v6.common import stable_hash_v1
    require(split in ("train1","train2") and seed in (11,23,37),"GDN_CUSTODY_SPLIT")
    public=root/"research_control_center/validation_v2/gdn_corr_001/exp01c_gdn_hai/receipts/EXP01C_CHECKPOINT_SET_RECEIPT.json"
    receipt=json.loads(public.read_text())
    require(receipt["receipt_hash"]==stable_hash_v1({k:v for k,v in receipt.items() if k!="receipt_hash"}),"GDN_RECEIPT_HASH")
    view=split.upper()+"_ONLY";record=next(r for r in receipt["runs"] if r["view"]==view and r["seed"]==seed)
    relative=Path("artifacts/validation_v2/gdn_corr_001/exp01c_gdn_hai/private/checkpoints")/f"exp01c-{split}-only-seed-{seed}.pt"
    found=[r/relative for r in registered_roots(root) if (r/relative).is_file()]
    require(len(found)==1 and not found[0].is_symlink(),"BLOCKED_REQUIRED_SPLIT_PURE_GDN_EVIDENCE_CUSTODY")
    payload=found[0].read_bytes();require(sha256(payload).hexdigest()==record["checkpoint_sha256"],"GDN_CHECKPOINT_HASH")
    checkpoint=torch.load(io.BytesIO(payload),map_location="cpu",weights_only=False)
    require(checkpoint["view"]==view and checkpoint["seed"]==seed and checkpoint["config_hash"]==Exp01CConfigV1().config_hash,"GDN_CHECKPOINT_IDENTITY")
    require(_state_hash_v1(checkpoint["state_dict"])==checkpoint["state_hash"]==record["state_hash"],"GDN_STATE_HASH")
    require(stable_hash_v1({"graph_edges":checkpoint["graph_edges"]})==record["graph_hash"],"GDN_GRAPH_HASH")
    return checkpoint,{"split":split,"seed":seed,"checkpoint_hash":record["checkpoint_sha256"],"bytes_read":len(payload)}
