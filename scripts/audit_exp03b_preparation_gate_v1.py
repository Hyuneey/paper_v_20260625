"""Read-only, public-authority EXP03B preflight. Not an evidence/provider runner."""
from __future__ import annotations

from hashlib import sha1, sha256
import json
from pathlib import Path
import subprocess

BASE = "4cbd13cec2e439f352adaf5b4e37163c6f18a485"
ROOT = Path(__file__).resolve().parents[1]
PREFIX = "research_control_center/validation_v2/"
PROTECTED = (
    PREFIX + "core_v2a", PREFIX + "exp03", PREFIX + "gdn_corr_001",
    PREFIX + "gdn_front_exp04_001", PREFIX + "gdn_rule_evidence",
    PREFIX + "exp01b_gdn_xai", PREFIX + "meta_lineage",
    PREFIX + "preregistration", PREFIX + "policies", PREFIX + "results",
    PREFIX + "evaluation_expansion",
)


def require(condition: bool, code: str) -> None:
    if not condition:
        raise ValueError(code)


def canonical_hash(value: object) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def verify_document(document: dict, field: str) -> None:
    require(document[field] == canonical_hash({k: v for k, v in document.items() if k != field}),
            "AUTHORITY_SELF_HASH_MISMATCH")


def call_budget(pair_count: int, repeats: int = 3) -> dict[str, int]:
    require(type(pair_count) is int and pair_count > 0, "COHORT_COUNT_INVALID")
    require(type(repeats) is int and repeats == 3, "REPEAT_CONTRACT_INVALID")
    return {"T0": 0, "T1": pair_count * repeats, "T1-B": pair_count * repeats * 3,
            "T2": pair_count * repeats * 3, "total": pair_count * repeats * 7}


def audit(root: Path = ROOT) -> dict:
    # Only explicitly named tracked public authority trees; never enumerate a data/vault root.
    listing = subprocess.check_output(["git", "ls-tree", "-rz", BASE, "--", *PROTECTED], cwd=root)
    entries = []
    for record in listing.split(b"\0"):
        if not record:
            continue
        metadata, name = record.split(b"\t", 1)
        mode, kind, oid = metadata.decode().split()
        require(kind == "blob" and mode in {"100644", "100755"}, "UNSUPPORTED_PUBLIC_ENTRY")
        relative = name.decode("utf-8")
        path = root / relative
        require(not path.is_symlink() and path.resolve().is_relative_to(root.resolve()), "UNSAFE_PUBLIC_PATH")
        data = path.read_bytes()
        actual = sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        require(actual == oid, "FROZEN_PUBLIC_BYTES_CHANGED")
        entries.append({"path": relative, "git_blob": oid})
    require(bool(entries), "EMPTY_PRESERVATION_SCOPE")

    def read(relative: str) -> dict:
        return json.loads((root / PREFIX / relative).read_text(encoding="utf-8"))

    union = read("core_v2a/authorities/VALIDATION_V2_META_STAT_CANDIDATE_UNION_AUTHORITY_V1.json")
    verify_document(union, "authority_hash")
    pairs = {(row["source"], row["target"]) for row in union["candidates"]}
    require(len(pairs) == len(union["candidates"]), "DUPLICATE_PAIR")
    cohort = read("core_v2a/authorities/V2A_CONFIRMED_COHORT_AUTHORITY.json")
    verify_document(cohort, "cohort_hash")
    confirmed_pairs = {(row["source"], row["target"]) for row in cohort["relations"]}
    require(confirmed_pairs <= pairs, "COHORT_OUTSIDE_UNION")
    binding = read("core_v2a/authorities/V2A_CONFIRMED_COHORT_BINDING.json")
    verify_document(binding, "binding_hash")
    require(binding["cohort_hash"] == cohort["cohort_hash"] and binding["candidate_authority_hash"] == union["authority_hash"], "BINDING_MISMATCH")
    require(binding["confirmed_pair_count"] == len(confirmed_pairs) and binding["confirmed_directional_relation_count"] == len(cohort["relations"]), "COHORT_COUNT_MISMATCH")
    result = read("exp03/execution_v1/EXP03_NATURAL_RESULTS_V1.json")
    verify_document(result, "self_hash")
    qa = read("exp03/execution_v1/INDEPENDENT_RESULT_QA_V1.json")
    verify_document(qa, "self_hash")
    require(qa["results_hash"] == result["self_hash"] and qa["status"] == "PASS", "EXP03_QA_BINDING_MISMATCH")
    body = {
        "schema": "exp03b_preparation_authority_replay_v1", "base_commit": BASE,
        "authority_replay": "PASS", "protected_public_blob_count": len(entries),
        "protected_public_inventory_hash": canonical_hash(entries),
        "candidate_pair_count": len(pairs), "candidate_authority_hash": union["authority_hash"],
        "confirmed_pair_count": len(confirmed_pairs), "directional_relation_count": len(cohort["relations"]),
        "cohort_hash": cohort["cohort_hash"], "exp03_v1_result_hash": result["self_hash"],
        "maximum_generation_calls": call_budget(len(pairs)),
        "execution_readiness": "BLOCKED_UNDEFINED_SCIENTIFIC_BINDINGS",
        "input_tokens": "NOT_FROZEN", "output_tokens": "NOT_FROZEN", "cost_ceiling": "NOT_FROZEN",
        "provider_calls": 0, "credential_reads": 0, "scientific_data_reads": 0,
        "private_payload_reads": 0, "writes": 0,
    }
    return {**body, "self_hash": canonical_hash(body)}


if __name__ == "__main__":
    try:
        print(json.dumps(audit(), sort_keys=True))
    except Exception:
        print('{"authority_replay":"FAIL_CLOSED"}')
        raise SystemExit(2)
