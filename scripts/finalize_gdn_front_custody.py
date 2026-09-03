"""Versioned private custody snapshots; no scientific producer or dataset reads."""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import subprocess

from paperworks.validation_v2.private_vault_v1 import (file_identity_v1,validate_private_path_v1,
    preserve_private_artifact_v1,public_artifact_record_v1,publish_private_bytes_v1)
from paperworks.validation_v2.gdn_sidecar_v1 import seal

V2=Path("research_control_center/validation_v2")

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--phase",choices=("prefeature","final"),required=True);args=parser.parse_args()
    root=Path.cwd();common=Path(subprocess.check_output(["git","rev-parse","--git-common-dir"],text=True).strip()).resolve()
    vault=common.parent.parent/"paper_v_20260625_private_vault"
    base=validate_private_path_v1(vault/"gdn-front-exp04-001",allowed_root=vault)
    output=root/V2/"local_custody"/f"PUBLIC_PRIVATE_ARTIFACT_INDEX_{args.phase.upper()}_V2.json"
    if output.is_file():
        from paperworks.validation_v2.gdn_sidecar_v1 import replay
        public=json.loads(output.read_text(encoding="utf-8"));replay(public)
        snapshot=json.loads((base/"snapshots"/(public["private_manifest_hash"]+".json")).read_text());replay(snapshot)
        for record in snapshot["records"]:
            for key in ("private_source","private_vault_object","private_restore_target"):
                if record.get(key) and file_identity_v1(Path(record[key]))!=(record["content_hash"],record["size"]):raise ValueError("SNAPSHOT_REPLAY_MISMATCH")
        print(json.dumps({"status":"EXISTING_SNAPSHOT_REPLAY_PASS","phase":args.phase,"records":len(snapshot["records"])}));return
    original=json.loads((base/"PRIVATE_ARTIFACT_MANIFEST.json").read_text())
    portfolio=json.loads((root/V2/"core_v2a/authorities/V2A_FORMAL_V4_PORTFOLIO_AUTHORITY.json").read_text())
    records=[]
    for record in original["records"]:
        row=dict(record)
        for key in ("private_source","private_vault_object","private_restore_target"):
            if row.get(key) and file_identity_v1(Path(row[key]))!=(row["content_hash"],row["size"]):
                raise ValueError("INITIAL_ARTIFACT_CHANGED")
        row.update(artifact_type="NUMERIC_AUTHORITY" if row["artifact_id"]=="V2A_NUMERIC_AUTHORITY" else "FUNCTIONAL_EVIDENCE",
            source_commit=portfolio["source_commit"] if row["artifact_id"]=="V2A_NUMERIC_AUTHORITY" else "UNKNOWN_SEE_FROZEN_EXP01C_FUNCTIONAL_RECEIPT",
            reproduction_importance="REQUIRED_CURRENT_RUNTIME" if row["artifact_id"]=="V2A_NUMERIC_AUTHORITY" else "REQUIRED_SIDECAR_DERIVATION")
        records.append(row)
    # Exact task-owned output namespace only; this tree never contains dataset or label files.
    if args.phase=="final":
        run=validate_private_path_v1(base/"scientific-run",allowed_root=vault)
        if not (run/"POST_LABEL_INTEGRITY_RECEIPT.json").is_file():raise ValueError("FINAL_EXECUTION_RECEIPT_REQUIRED")
        execution=json.loads((run/"V2_SCIENTIFIC_RUN_MANIFEST.json").read_text())["execution_commit"]
        for index,path in enumerate(sorted(run.rglob("*"))):
            validate_private_path_v1(path,allowed_root=run)
            if path.is_dir():continue
            digest,size=file_identity_v1(path)
            record=preserve_private_artifact_v1(source=path,vault=vault,artifact_id=f"FRONT_RESULT_{index:06d}",expected_hash=digest)
            record.update(artifact_type=path.parent.name.upper(),source_commit=execution,
                reproduction_importance="REQUIRED_FROZEN_REPLAY",producer_task="V2-GDN-FRONT-EXP04-001",tracking_state="OUTSIDE_GIT",
                required_consumer="EXP04_EXP05_INTEGRITY_AND_REPRODUCTION",last_verified=datetime.now(timezone.utc).isoformat())
            records.append(record)
    # Content-addressed snapshots are immutable and idempotent; never rewrite the initial ledger.
    private=seal({"schema":"private_custody_snapshot_v2","phase":args.phase,"records":records,
        "backup_status":"SINGLE_COPY_LOCAL_ONLY","independent_storage_verified":False})
    relative=Path("snapshots")/(private["self_hash"]+".json")
    publish_private_bytes_v1(base/relative,(json.dumps(private,sort_keys=True,indent=2)+"\n").encode())
    public=seal({"schema":"public_private_artifact_index_v2","phase":args.phase,
        "scope":"EXACT_NUMERIC_AND_GDN_RESTORATION_INPUTS" if args.phase=="prefeature" else "RESTORATION_INPUTS_AND_COMPLETED_EXECUTION_OUTPUTS",
        "records":[public_artifact_record_v1(r) for r in records],"private_manifest_hash":private["self_hash"],
        "missing_required_artifacts_in_this_scope":[],"dataset_payload_inventory":"AUTHORIZED_ADAPTER_AT_EXECUTION_ONLY_NOT_INSPECTED_BY_THIS_TOOL",
        "old_checkpoint_or_meta_reviewed_input":"NONBLOCKING_REPRODUCIBILITY_DEBT",
        "backup_status":"SINGLE_COPY_LOCAL_ONLY","restore_status":"EXACT_BYTE_REPLAY_PASS",
        "test1_dataset_accesses_by_this_tool":0,"test2_accesses":0,"label_file_accesses":0,"scientific_execution_by_this_tool":0})
    publish_private_bytes_v1(output,(json.dumps(public,sort_keys=True,indent=2,ensure_ascii=False)+"\n").encode())
    print(json.dumps({"status":"PASS","phase":args.phase,"records":len(records),"snapshot_hash":private["self_hash"]}))

if __name__=="__main__":
    try:main()
    except Exception as error:
        print(json.dumps({"status":"CUSTODY_FINALIZATION_FAILED","error_type":type(error).__name__}));raise SystemExit(1)
