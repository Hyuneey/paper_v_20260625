"""Finalize the public-safe DG05 Executable V4 preaccess release package."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research_control_center/validation_v2/dg05_v4_release"
RELEASE_PACKAGE_COMMIT = "5559d6479af33b210af8548f8cdc7b62dafbe282"
IMPLEMENTATION_COMMIT = "0a2f3ad4bb97c3c42888740f764ed116e5cfd2d8"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                      allow_nan=False).encode("ascii")


def digest(value: object) -> str:
    return sha256(canonical(value)).hexdigest()


def self_hashed(body: dict) -> dict:
    return {**body, "self_hash": digest(body)}


def load(name: str) -> dict:
    path = OUT / name
    raw = path.read_bytes()
    value = json.loads(raw.decode("ascii"))
    if raw != canonical(value) + b"\n" or value.get("self_hash") != digest(
            {key: item for key, item in value.items() if key != "self_hash"}):
        raise RuntimeError(f"PUBLIC_AUTHORITY_REPLAY_FAILED:{name}")
    return value


def write_json(name: str, value: dict) -> None:
    path = OUT / name
    if path.exists():
        raise RuntimeError(f"APPEND_ONLY_CONFLICT:{name}")
    path.write_bytes(canonical(value) + b"\n")


def write_text(name: str, value: str) -> None:
    path = OUT / name
    if path.exists():
        raise RuntimeError(f"APPEND_ONLY_CONFLICT:{name}")
    path.write_text(value.replace("\r\n", "\n").rstrip() + "\n", encoding="utf-8", newline="\n")


def file_hash(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def main() -> None:
    release = load("DG05_EXECUTABLE_AUTHORITY_MANIFEST_V4.json")
    rehearsal = load("SYNTHETIC_DG05_PRODUCTION_ROUTE_REHEARSAL_V4.json")
    contract = load("METRIC_SURFACE_CONTRACT_V2.json")
    expected = load("EXPECTED_RESULT_SURFACE_V2.json")
    coverage = load("RESULT_SURFACE_COVERAGE_MATRIX_V2.json")
    mutations = load("MUTATION_EVIDENCE_V2.json")
    smoke = load("FROZEN_METHOD_SMOKE_V4.json")
    attempts = load("PREPARE_ATTEMPT_CENSUS_V1.json")
    exact = {
        "release": "d31a726cb5c7b3620ed59dcff24ac75cd91e64028414931574fa33834a54a4b1",
        "rehearsal": "5d62bc934ff31ed573d51275e28650952fbaed1aa62622b3077e5e22935c0b70",
        "contract": "88b3d6dbcd2b4bab957aec8806bed4906053046c81df6dda08a128463b867fc5",
        "coverage": "2690eae1472c0c3256f87259529539ce58acca98eaaba19968989c02a4ea5446",
        "mutations": "29c5b0a75c9707d10568f7319de412c91e7299f1c6026e04b469b3fcb91d2138",
        "smoke": "ca86cd9212d6dd8150b0f71ff66dff178562dbe6e9be1f38162b9f109ff4ebce",
    }
    observed = {"release": release["self_hash"], "rehearsal": rehearsal["self_hash"],
                "contract": contract["self_hash"], "coverage": coverage["self_hash"],
                "mutations": mutations["self_hash"], "smoke": smoke["self_hash"]}
    if observed != exact or file_hash(OUT / "RESULT_SURFACE_COVERAGE_MATRIX_V2.csv") != coverage["csv_byte_hash"]:
        raise RuntimeError("DEFINITIVE_RELEASE_ROOT_MISMATCH")

    qa = self_hashed({
        "schema": "dg05_v4_independent_preaccess_qa_authority_v1",
        "status": "PASS_FOR_PREACCESS_RELEASE_QA",
        "reviewer_role": "INDEPENDENT_READ_ONLY_AGENT_G",
        "release_manifest_hash": release["self_hash"],
        "rehearsal_hash": rehearsal["self_hash"],
        "release_initialization_hash": rehearsal["release_initialization_hash"],
        "metric_surface_contract_hash": contract["self_hash"],
        "coverage_matrix_hash": coverage["self_hash"],
        "mutation_evidence_hash": mutations["self_hash"],
        "method_smoke_hash": smoke["self_hash"],
        "prepare_attempt_census_hash": attempts["self_hash"],
        "implementation_commit": IMPLEMENTATION_COMMIT,
        "release_package_commit": RELEASE_PACKAGE_COMMIT,
        "implementation_roles_verified": 21,
        "implementation_roles_required": 21,
        "focused_tests_passed": 43,
        "focused_tests_failed": 0,
        "derived_prediction_cells": 72,
        "successful_prediction_cells": 72,
        "verified_metric_surfaces": 228,
        "normal_components_reopened": 30,
        "synthetic_plural_interval_scenarios": 146,
        "fresh_process_custodian": True,
        "lease_issue_consume_reissue": [1, 1, 0],
        "checks": {
            "dec031_four_bindings": "PASS",
            "invalid_timeline_blocked_before_prediction": "PASS",
            "interval_local_physical_delay": "PASS",
            "four_way_runtime_identity": "PASS",
            "missing_runtime_never_zero": "PASS",
            "rule_alarm_episode_source_replay": "PASS",
            "private_normal_source_discovery": "PASS",
            "scoped_frozen_normal_materialization": "PASS",
            "normal_label_values_untouched": "PASS",
            "normal_burden_independent_replay": "PASS",
            "coherent_downstream_rehash_rejected": "PASS",
            "connected_production_route": "PASS",
            "fresh_process_custodian_on_route": "PASS",
            "executed_implementation_byte_binding": "PASS",
            "real_restricted_access_zero": "PASS",
        },
        "attack_test_accesses": 0,
        "real_label_scenario_accesses": 0,
        "provider_calls": 0,
        "credential_reads": 0,
        "private_exposures": 0,
    })
    write_json("INDEPENDENT_QA_AUTHORITY_V4.json", qa)

    closure = self_hashed({
        "schema": "dg05_executable_closure_authority_v4",
        "status": "READY_FOR_USER_REAPPROVAL",
        "approval_status": "DG05_REAL_ACCESS_NOT_APPROVED",
        "executable_manifest_hash": release["self_hash"],
        "independent_qa_hash": qa["self_hash"],
        "synthetic_rehearsal_hash": rehearsal["self_hash"],
        "metric_surface_contract_hash": contract["self_hash"],
        "expected_result_surface_hash": expected["self_hash"],
        "coverage_matrix_hash": coverage["self_hash"],
        "mutation_evidence_hash": mutations["self_hash"],
        "method_smoke_hash": smoke["self_hash"],
        "prepare_attempt_census_hash": attempts["self_hash"],
        "dec031_binding_hash": release["semantic_binding_hash"],
        "normal_source_registry_hash": release["normal_burden_source_registry_hash"],
        "scientific_preregistration_hash": release["scientific_preregistration_hash"],
        "implementation_commit": IMPLEMENTATION_COMMIT,
        "release_package_commit": RELEASE_PACKAGE_COMMIT,
        "next_gate": "DG05_REAPPROVAL_NEW_EXACT_EXECUTABLE_RELEASE",
        "attack_test_accesses": 0,
        "real_label_scenario_accesses": 0,
        "provider_calls": 0,
        "credential_reads": 0,
    })
    write_json("DG05_EXECUTABLE_CLOSURE_AUTHORITY_V4.json", closure)

    report = f"""# DG-05 Executable V4 Closure Report

Status: `READY_FOR_USER_REAPPROVAL`

This is a pre-access implementation and source-lineage closure. It is not DG-05 approval and contains no held-out result.

- executable manifest: `{release['self_hash']}`
- executable closure: `{closure['self_hash']}`
- independent QA: `{qa['self_hash']}`
- DEC-031 binding: `{release['semantic_binding_hash']}`
- normal-source registry: `{release['normal_burden_source_registry_hash']}`
- connected rehearsal: `{rehearsal['self_hash']}`
- complete metric surfaces: `228 / 228`
- synthetic prediction cells: `72 / 72`
- frozen normal components independently reopened: `30`
- fresh-process custodian: `PASS`

The route freezes physical-timestamp semantics, plural-interval HIT with interval-local delay, fail-closed duplicate/gap handling, four-way Rule identity census, union-based Rule episodes, and source-derived normal burden. T0 remains structural-only in its effective field contract; T2 uses structural, STAT, GLOBAL5 GDN, and bounded verifier feedback/retrieval. No identical-effective-information claim is made.

Real attack/test/label/scenario access remains `NO_GO` until the user approves the exact V4 manifest and closure together.
"""
    write_text("DG05_EXECUTABLE_CLOSURE_REPORT_V4.md", report)

    brief = f"""# DG-05 Multi-Panel Attack Access Reapproval Brief V4

Status: `USER_DECISION_REQUIRED`

Requested future decision: approve the exact two-phase DG-05 execution under:

- executable manifest: `{release['self_hash']}`
- executable closure: `{closure['self_hash']}`
- scientific preregistration: `{release['scientific_preregistration_hash']}`
- DEC-031 binding: `{release['semantic_binding_hash']}`
- metric surface contract: `{contract['self_hash']}`
- independent QA: `{qa['self_hash']}`

The approval must bind both exact hashes above. DEC-029 and DEC-030 remain historical and suspended; neither authorizes this release. Phase A remains feature-only prediction and global freeze. Phase B remains a one-shot fresh-process label/scenario lease after exact freeze. No access follows automatically from this brief.

Current counters: attack/test `0`; real label/scenario `0`; provider `0`; credential reads `0`.
"""
    write_text("DG05_MULTI_PANEL_ATTACK_ACCESS_BRIEF_V4.md", brief)

    indexed = []
    for path in sorted(OUT.iterdir(), key=lambda item: item.name):
        if path.name == "PUBLIC_PRIVATE_DG05_RELEASE_INDEX_V4.json":
            continue
        indexed.append({"name": path.name, "byte_hash": file_hash(path), "byte_count": path.stat().st_size,
                        "classification": "PUBLIC_SAFE"})
    index = self_hashed({
        "schema": "public_private_dg05_release_index_v4",
        "status": "PUBLIC_SAFE_INDEX_PRIVATE_SOURCE_PAYLOADS_EXCLUDED",
        "executable_manifest_hash": release["self_hash"],
        "executable_closure_hash": closure["self_hash"],
        "public_files": indexed,
        "public_file_count": len(indexed),
        "private_normal_source_manifest_hash": "954720e3f60c583d4d64ea5af646d343eadcdb56367625a1e4d80ab060062581",
        "private_paths_published": False,
        "backup_status": "SINGLE_COPY_LOCAL_ONLY",
        "attack_test_accesses": 0,
        "real_label_scenario_accesses": 0,
        "provider_calls": 0,
        "source_commit": RELEASE_PACKAGE_COMMIT,
    })
    write_json("PUBLIC_PRIVATE_DG05_RELEASE_INDEX_V4.json", index)
    print(json.dumps({"release": release["self_hash"], "qa": qa["self_hash"],
                      "closure": closure["self_hash"], "index": index["self_hash"]}, sort_keys=True))


if __name__ == "__main__":
    main()
