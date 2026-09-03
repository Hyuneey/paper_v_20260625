"""Single-writer, exact recorded-artifact recovery and non-authoritative mapping.

No datasets, label files or checkpoint contents are read by this command.
Only exact artifact relative paths within registered Git worktrees are checked.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

from paperworks.validation_v2.gdn_sidecar_v1 import project_gdn_evidence_v1, replay, seal
from paperworks.validation_v2.private_vault_v1 import (
    file_identity_v1, preserve_private_artifact_v1, public_artifact_record_v1, publish_private_bytes_v1,
)

V2 = Path("research_control_center/validation_v2")
GDN = V2 / "gdn_corr_001/exp01c_gdn_hai"
PRIVATE = Path("artifacts/validation_v2/gdn_front_exp04_001/private")


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if type(value) is not dict:
        raise ValueError("OBJECT_REQUIRED")
    return value


def write_public(root: Path, relative: Path, document: dict) -> None:
    payload = (json.dumps(document, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    publish_private_bytes_v1(root / relative, payload)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", type=Path, required=True)
    args = parser.parse_args()
    root = Path.cwd().resolve()
    common = Path(subprocess.check_output(["git", "rev-parse", "--git-common-dir"], text=True).strip()).resolve()
    repository = common.parent
    vault = args.vault.resolve()
    if vault == repository or repository in vault.parents or args.vault.is_symlink():
        raise ValueError("VAULT_MUST_BE_OUTSIDE_REPOSITORY")
    old_manifest=vault/"gdn-front-exp04-001/PRIVATE_ARTIFACT_MANIFEST.json"
    if old_manifest.is_file():
        document=load(old_manifest)
        for record in document["records"]:
            for key in ("private_source","private_vault_object","private_restore_target"):
                if record.get(key) and file_identity_v1(Path(record[key]))!=(record["content_hash"],record["size"]):
                    raise ValueError("EXISTING_CUSTODY_REPLAY_FAILED")
        print(json.dumps({"status":"EXISTING_IMMUTABLE_INITIAL_CUSTODY_REPLAY_PASS","records":len(document["records"]),
            "next":"finalize_gdn_front_custody.py --phase prefeature"}))
        return
    roots = [Path(line[9:]) for line in subprocess.check_output(["git", "worktree", "list", "--porcelain"], text=True).splitlines() if line.startswith("worktree ")]
    portfolio = load(root / V2 / "core_v2a/authorities/V2A_FORMAL_V4_PORTFOLIO_AUTHORITY.json")
    disposition = load(root / GDN / "results/EXP01C_DISPOSITION.json")
    functional = load(root / GDN / "receipts/EXP01C_FUNCTIONAL_RECEIPT.json")
    reference = load(root / V2 / "exp01b_gdn_xai/receipts/EXP01B_REFERENCE_SET_RECEIPT.json")
    for value, field in ((portfolio,"authority_hash"), (disposition,"result_hash"), (functional,"receipt_hash"), (reference,"receipt_hash")):
        replay(value, field)
    specs = [("V2A_NUMERIC_AUTHORITY", Path(portfolio["numeric_authority_binding"]["relative_path"]), portfolio["numeric_authority_binding"]["content_sha256"], "V2A_RUNTIME")]
    for item in functional["private_evidence_hashes"]:
        token = item["view"].lower().replace("_", "-")
        name = f"exp01c-{token}-seed-{item['seed']}.json"
        relative = Path("artifacts/validation_v2/gdn_corr_001/exp01c_gdn_hai/private/evidence") / name
        specs.append((f"EXP01C_{item['view']}_{item['seed']}", relative, item["sha256"], "GDN_RULE_MAPPING"))
    records, evidence = [], []
    for artifact_id, relative, expected, consumer in specs:
        sources = [r / relative for r in roots if (r / relative).is_file() and not (r / relative).is_symlink()]
        if not sources:
            raise ValueError(f"BLOCKING_REQUIRED_EXECUTION_CUSTODY:{artifact_id}")
        matching = [p for p in sources if file_identity_v1(p)[0] == expected]
        if not matching:
            raise ValueError(f"BLOCKING_REQUIRED_EXECUTION_IDENTITY:{artifact_id}")
        source = sorted(matching)[0]
        source_root = next(r for r in roots if r / relative == source)
        ignored = subprocess.run(["git", "check-ignore", "--quiet", str(relative)], cwd=source_root).returncode == 0
        tracked = subprocess.run(["git", "ls-files", "--error-unmatch", str(relative)], cwd=source_root, capture_output=True).returncode == 0
        if tracked or not ignored:
            raise ValueError("PRIVATE_TRACKING_POLICY_FAILED")
        record = preserve_private_artifact_v1(source=source, vault=vault, artifact_id=artifact_id,
                                              expected_hash=expected, restore_target=root / relative)
        record.update(tracking_state="GIT_IGNORED_UNTRACKED", required_consumer=consumer,
                      last_verified=datetime.now(timezone.utc).isoformat(), producer_task="V2A" if consumer == "V2A_RUNTIME" else "EXP01C")
        records.append(record)
        if consumer == "GDN_RULE_MAPPING":
            evidence.append(load(root / relative))
    bindings = {"functional_receipt_hash": functional["receipt_hash"], "disposition_hash": disposition["result_hash"],
                "reference_hash": reference["receipt_hash"], "portfolio_hash": portfolio["authority_hash"],
                "descriptor_set_hash": portfolio["descriptor_set_hash"]}
    mapping, sidecar = project_gdn_evidence_v1(reference=reference, portfolio=portfolio, evidence=evidence,
                                            expected_stable_count=disposition["stable_positive_event_edgemask_pair_count"], bindings=bindings)
    write_public(root, V2 / "gdn_rule_evidence/GDN_TO_V2A_RULE_EVIDENCE_MAP_V1.json", mapping)
    write_public(root, V2 / "gdn_rule_evidence/GDN_LEARNED_GRAPH_EVIDENCE_SIDECAR_V1.json", sidecar)
    classes = [p["classification"] for p in mapping["pairs"]]
    eligibility = ("GDN_ASSISTED_TITLE_STRONG" if "PAIR_AND_HORIZON_CORROBORATION" in classes else
                   "GDN_ASSISTED_TITLE_QUALIFIED" if "PAIR_ONLY_CORROBORATION" in classes else "GDN_ASSISTED_TITLE_NOT_SUPPORTED")
    write_public(root, V2 / "gdn_rule_evidence/GDN_TITLE_ELIGIBILITY_V1.json", seal({"eligibility":eligibility,
                 "mapping_hash":mapping["self_hash"], "documentation_only": True, "final_title_gate":"DG-04"}))
    timestamp = datetime.now(timezone.utc).isoformat()
    private_manifest = {"schema":"private_artifact_manifest_v1", "records":records, "created":timestamp}
    for name, doc in (("PRIVATE_ARTIFACT_MANIFEST.json", private_manifest),
                      ("PRIVATE_RESTORE_MANIFEST.json", {"records":records, "restore_status":"EXACT_BYTE_REPLAY_PASS"}),
                      ("PRIVATE_BACKUP_STATUS.json", {"backup_status":"SINGLE_COPY_LOCAL_ONLY", "independent_second_storage_verified":False})):
        publish_private_bytes_v1(vault / "gdn-front-exp04-001" / name, (json.dumps(doc, sort_keys=True, indent=2)+"\n").encode())
    public = seal({"schema":"public_private_artifact_index_v1", "records":[public_artifact_record_v1(r) for r in records],
                   "registered_worktrees_checked":len(roots), "missing_required_artifacts":[],
                   "historical_meta_reviewed_input":"NONBLOCKING_REPRODUCIBILITY_DEBT",
                   "backup_status":"SINGLE_COPY_LOCAL_ONLY", "test1_accesses":0,"label_accesses":0,"test2_accesses":0,
                   "heldout_accesses":0,"scientific_producers_executed":0,"private_exposures":0})
    write_public(root, V2 / "local_custody/PUBLIC_PRIVATE_ARTIFACT_INDEX_V1.json", public)
    runtime = [r / ".venv/validation-v2/Scripts/python.exe" for r in roots if (r / ".venv/validation-v2/Scripts/python.exe").is_file()]
    if len(runtime) != 1:
        raise ValueError("FROZEN_DETECTOR_ENVIRONMENT_LOCATOR_AMBIGUOUS")
    # The root layout is the already-approved normal materializer cache, not a search.
    cache = Path(os.environ["LOCALAPPDATA"]) / "paper_v_20260625/official_hai_2305/snapshot_2a814cebc9a6_validation_v2_normal_only"
    context = {"private_vault":str(vault), "detector_python":str(runtime[0]), "normal_materialization_root":str(cache)}
    publish_private_bytes_v1(root / PRIVATE / "LOCAL_CONTEXT.json", (json.dumps(context,sort_keys=True,indent=2)+"\n").encode())
    print(json.dumps({"status":"EXACT_REQUIRED_ARTIFACT_RESTORE_PASS", "private_artifacts":len(records),
                      "stable_pairs":len(mapping["pairs"]), "classifications":classes,"title_eligibility":eligibility,
                      "mapping_hash":mapping["self_hash"],"sidecar_hash":sidecar["self_hash"]}))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(json.dumps({"status":"BLOCKING_REQUIRED_EXECUTION_CUSTODY", "error_type":type(error).__name__}), file=sys.stderr)
        raise SystemExit(1)
