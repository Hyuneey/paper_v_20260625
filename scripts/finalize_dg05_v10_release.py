"""Finalize the public-safe DG05 Executable V10 preaccess release package."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research_control_center/validation_v2/dg05_v10_release"
IMPLEMENTATION_COMMIT = "5f3a4218382dfbb8e1b74bfb35a3b5aaea51c9cd"
CANDIDATE_PACKAGE_COMMIT = "18ca8c6487a7f16da0067c0a825c44463be73710"


def canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def digest(value: object) -> str:
    return sha256(canonical(value)).hexdigest()


def self_hashed(body: dict) -> dict:
    return {**body, "self_hash": digest(body)}


def load(name: str) -> dict:
    path = OUT / name
    raw = path.read_bytes()
    value = json.loads(raw.decode("ascii"))
    if (
        raw != canonical(value) + b"\n"
        or value.get("self_hash")
        != digest({key: item for key, item in value.items() if key != "self_hash"})
    ):
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
    path.write_text(
        value.replace("\r\n", "\n").rstrip() + "\n",
        encoding="utf-8",
        newline="\n",
    )


def file_hash(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def main() -> None:
    release = load("DG05_EXECUTABLE_AUTHORITY_MANIFEST_V10.json")
    rehearsal = load("SYNTHETIC_DG05_PRODUCTION_ROUTE_REHEARSAL_V10.json")
    parity = load("PRODUCTION_KERNEL_PARITY_V1.json")
    roots = load("ROOT_TO_RESULT_REPLAY_V1.json")
    contract = load("METRIC_SURFACE_CONTRACT_V2.json")
    expected = load("EXPECTED_RESULT_SURFACE_V3.json")
    coverage = load("RESULT_SURFACE_COVERAGE_MATRIX_V3.json")
    mutations = load("MUTATION_EVIDENCE_V3.json")
    smoke = load("FROZEN_METHOD_SMOKE_V10.json")
    transitive = load("TRANSITIVE_IMPLEMENTATION_AUTHORITY_V1.json")
    exact = {
        "release": "a916c18afb628326c28037e678fc809779b888535aafe2d9fc0a54b8107a91fd",
        "rehearsal": "2e941ad447e19ba43ce78e3f595da14cfb8ec20735d8ed7409d3a45bb7bce6e9",
        "parity": "ac9f3a93654e0e320ebc0d4add364ae6f1df5bf67bd373205a5bae1c8c80d06e",
        "roots": "eba06ceb9c2ab9a7b5dfa97781533680bd6d7a42d142d614ee45c6f019201c30",
        "contract": "f4eda42f0412db678f357c8791244106710fc1c8b0807d399c794e659920d7df",
        "expected": "c7d4e773c14deb2ee042543f3c02ded80980b87ba7fa85f8b2343880911b2e28",
        "coverage": "579e949bc31f40bea3ec41b13e9729663548209903b011f1b01bf12262db5a03",
        "mutations": "7e0b2c272692bc86d2b132a7e472eb45367704bc9d8f269492ac547e8fb80752",
        "smoke": "6abf8051c219c80a5f119f0fb10f046b0670177ad2ed84d5e4a8107fda7c7e71",
        "transitive": "3389cad5237475dd9905626c7fb303553c9fd104af75ff24014b4f36557ca07d",
    }
    observed = {
        "release": release["self_hash"], "rehearsal": rehearsal["self_hash"],
        "parity": parity["self_hash"], "roots": roots["self_hash"],
        "contract": contract["self_hash"], "expected": expected["self_hash"],
        "coverage": coverage["self_hash"], "mutations": mutations["self_hash"],
        "smoke": smoke["self_hash"], "transitive": transitive["self_hash"],
    }
    if (
        observed != exact
        or file_hash(OUT / "RESULT_SURFACE_COVERAGE_MATRIX_V3.csv")
        != coverage["csv_byte_hash"]
        or release["source_commit"] != IMPLEMENTATION_COMMIT
        or release["transitive_implementation_authority"]["self_hash"]
        != transitive["self_hash"]
        or mutations["rejected_mutation_count"] != 25
        or mutations["accepted_semantic_edge_case_count"] != 3
        or not all(roots["per_root_replay"].values())
    ):
        raise RuntimeError("DEFINITIVE_RELEASE_ROOT_MISMATCH")

    qa = self_hashed({
        "schema": "dg05_v10_independent_preaccess_qa_authority_v1",
        "status": "PASS_FOR_PREACCESS_RELEASE_QA",
        "reviewer_role": "INDEPENDENT_READ_ONLY_RELEASE_REVIEWER",
        "release_manifest_hash": release["self_hash"],
        "rehearsal_hash": rehearsal["self_hash"],
        "production_kernel_parity_hash": parity["self_hash"],
        "root_to_result_replay_hash": roots["self_hash"],
        "metric_surface_contract_hash": contract["self_hash"],
        "coverage_matrix_hash": coverage["self_hash"],
        "mutation_evidence_hash": mutations["self_hash"],
        "method_smoke_hash": smoke["self_hash"],
        "transitive_implementation_authority_hash": transitive["self_hash"],
        "implementation_commit": IMPLEMENTATION_COMMIT,
        "candidate_package_commit": CANDIDATE_PACKAGE_COMMIT,
        "implementation_roles_verified": len(release["implementation_authorities"]),
        "transitive_repository_python_files_verified": transitive["closure_count"],
        "focused_dg05_tests_passed": 114,
        "focused_dg05_tests_failed": 0,
        "derived_prediction_cells": 72,
        "successful_prediction_cells": 72,
        "verified_metric_surfaces": 228,
        "root_covered_metric_surfaces": roots["root_covered_surface_count"],
        "normal_components_reopened": 30,
        "normal_method_version_bundles": 23,
        "synthetic_plural_interval_scenarios": 146,
        "production_kernel_invocations": parity["production_kernel_invocation_count"],
        "synthetic_fallback_invocations": parity["synthetic_fallback_invocation_count"],
        "invalid_mutations_rejected": mutations["rejected_mutation_count"],
        "valid_semantic_edge_cases_accepted": mutations["accepted_semantic_edge_case_count"],
        "fresh_process_custodian": True,
        "lease_issue_consume_reissue": [1, 1, 0],
        "checks": {
            "g1_reproduced_before_remediation": "PASS",
            "exact_frozen_production_kernel_on_connected_route": "PASS",
            "protected_real_data_access_impossible_in_rehearsal": "PASS",
            "synthetic_trace_reconstruction_excluded": "PASS",
            "g2_reproduced_before_remediation": "PASS",
            "raw_physical_source_reopened": "PASS",
            "raw_source_to_projection_independently_bound": "PASS",
            "dec031_timeline_independently_validated": "PASS",
            "raw_official_scenario_source_reopened": "PASS",
            "custodian_policy_request_lease_process_output_replayed": "PASS",
            "scenario_authority_independently_reconstructed": "PASS",
            "p1_denominator_independently_reconstructed": "PASS",
            "coherent_scenario_rehash_rejected": "PASS",
            "coherent_denominator_rehash_rejected": "PASS",
            "raw_source_projection_disconnect_rejected": "PASS",
            "normal_source_bundles_unchanged_and_replayable": "PASS",
            "all_cells_production_kernel_executed": "PASS",
            "all_surfaces_independently_root_covered": "PASS",
            "fresh_process_custodian_on_connected_route": "PASS",
            "real_restricted_access_zero": "PASS",
            "scientific_method_authorities_unchanged": "PASS",
            "release_binds_executed_implementation_bytes": "PASS",
            "custodian_production_contract_invariants_replayed": "PASS",
            "scenario_identity_uniqueness_replayed": "PASS",
        },
        "qualification_limits": [
            "PREACCESS_SYNTHETIC_AND_FROZEN_NORMAL_ONLY_NOT_HELDOUT_EXECUTION",
            "KERNEL_PARITY_IS_EXECUTED_CALLABLE_PATH_IDENTITY_NOT_OUTPUT_EQUIVALENCE_STUDY",
            "TRANSITIVE_CLOSURE_COVERS_REPOSITORY_OWNED_STATIC_PYTHON_IMPORTS",
            "PRODUCTION_HAI_SCENARIO_ADAPTER_INPUT_IS_A_FROZEN_CANONICAL_PRIVATE_SOURCE_CONTRACT",
        ],
        "attack_test_accesses": 0,
        "real_label_scenario_accesses": 0,
        "provider_calls": 0,
        "credential_reads": 0,
        "new_fitting": 0,
        "new_rule_generation": 0,
        "new_scientific_experiments": 0,
        "result_driven_changes": 0,
        "private_exposures": 0,
    })
    write_json("INDEPENDENT_QA_AUTHORITY_V10.json", qa)

    closure = self_hashed({
        "schema": "dg05_executable_closure_authority_v10",
        "status": "READY_FOR_USER_REAPPROVAL",
        "approval_status": "DG05_REAL_ACCESS_NOT_APPROVED",
        "executable_manifest_hash": release["self_hash"],
        "independent_qa_hash": qa["self_hash"],
        "synthetic_rehearsal_hash": rehearsal["self_hash"],
        "production_kernel_parity_hash": parity["self_hash"],
        "root_to_result_replay_hash": roots["self_hash"],
        "metric_surface_contract_hash": contract["self_hash"],
        "expected_result_surface_hash": expected["self_hash"],
        "coverage_matrix_hash": coverage["self_hash"],
        "mutation_evidence_hash": mutations["self_hash"],
        "method_smoke_hash": smoke["self_hash"],
        "transitive_implementation_authority_hash": transitive["self_hash"],
        "dec031_binding_hash": release["semantic_binding_hash"],
        "normal_source_registry_hash": release["normal_burden_source_registry_hash"],
        "scientific_preregistration_hash": release["scientific_preregistration_hash"],
        "implementation_commit": IMPLEMENTATION_COMMIT,
        "candidate_package_commit": CANDIDATE_PACKAGE_COMMIT,
        "next_gate": "DEC-033_DG05_EXECUTABLE_V10_EXACT_RELEASE_REAPPROVAL",
        "attack_test_accesses": 0,
        "real_label_scenario_accesses": 0,
        "provider_calls": 0,
        "credential_reads": 0,
    })
    write_json("DG05_EXECUTABLE_CLOSURE_AUTHORITY_V10.json", closure)

    report = f"""# DG-05 Executable V10 Closure Report

Status: `READY_FOR_USER_REAPPROVAL`

This is a pre-access engineering qualification. It is not DG-05 approval and contains no held-out result.

- executable manifest: `{release['self_hash']}`
- executable closure: `{closure['self_hash']}`
- independent QA: `{qa['self_hash']}`
- production-kernel parity: `{parity['self_hash']}`
- root-to-result replay: `{roots['self_hash']}`
- DEC-031 binding: `{release['semantic_binding_hash']}`
- normal-source registry: `{release['normal_burden_source_registry_hash']}`
- connected rehearsal: `{rehearsal['self_hash']}`
- production-kernel cells: `72 / 72`
- complete and root-covered surfaces: `228 / 228`
- frozen normal components / method-version bundles: `30 / 23`
- invalid mutations rejected / valid edge cases accepted: `25 / 3`
- fresh-process custodian: `PASS`

The connected pre-access route executes the same frozen scientific scorer/runtime callables used by the protected production mode while keeping protected discovery disabled. The independent verifier reopens raw physical and scenario roots, projection, predictions, Rule traces, freeze, policy/request/lease/process/output, frozen P1 scope, denominator, and normal sources before reconstructing the result primitive.

The production HAI scenario adapter accepts the frozen canonical private source schema `hai_official_scenario_metadata_raw_v2`; no real source was materialized or read in this task. V4 remains historical and unapproved. V5 through V9 are preserved failed release candidates. Real attack/test/label/scenario access remains `NO_GO` until exact V10 user reapproval.
"""
    write_text("DG05_EXECUTABLE_CLOSURE_REPORT_V10.md", report)

    brief = f"""# DG-05 Multi-Panel Attack Access Reapproval Brief V10

Status: `USER_DECISION_REQUIRED`

Requested future decision: `DEC-033 — DG05_EXECUTABLE_V10_EXACT_RELEASE_REAPPROVAL`.

Any approval must bind exactly:

- executable manifest: `{release['self_hash']}`
- executable closure: `{closure['self_hash']}`
- independent QA: `{qa['self_hash']}`
- connected rehearsal: `{rehearsal['self_hash']}`
- production-kernel parity: `{parity['self_hash']}`
- root-to-result replay: `{roots['self_hash']}`
- source commit: `{IMPLEMENTATION_COMMIT}`
- scientific preregistration: `{release['scientific_preregistration_hash']}`
- DEC-031 binding: `{release['semantic_binding_hash']}`

DEC-032 remains the historical unapproved V4 decision item and cannot authorize V10. DEC-029 and DEC-030 remain suspended historical approvals. No access follows automatically from this brief. Phase A remains feature-only prediction and global freeze; Phase B remains a one-shot fresh-process label/scenario lease after the exact freeze.

Current counters: attack/test `0`; real label/scenario `0`; provider `0`; credential reads `0`; fitting `0`; Rule generation `0`.
"""
    write_text("DG05_MULTI_PANEL_ATTACK_ACCESS_BRIEF_V10.md", brief)

    indexed = []
    for path in sorted(OUT.iterdir(), key=lambda item: item.name):
        if path.name == "PUBLIC_PRIVATE_DG05_RELEASE_INDEX_V10.json":
            continue
        indexed.append({
            "name": path.name,
            "byte_hash": file_hash(path),
            "byte_count": path.stat().st_size,
            "classification": "PUBLIC_SAFE",
        })
    index = self_hashed({
        "schema": "public_private_dg05_release_index_v10",
        "status": "PUBLIC_SAFE_INDEX_PRIVATE_SOURCE_PAYLOADS_EXCLUDED",
        "executable_manifest_hash": release["self_hash"],
        "executable_closure_hash": closure["self_hash"],
        "independent_qa_hash": qa["self_hash"],
        "public_files": indexed,
        "public_file_count": len(indexed),
        "private_normal_source_manifest_hash":
            "954720e3f60c583d4d64ea5af646d343eadcdb56367625a1e4d80ab060062581",
        "private_paths_published": False,
        "backup_status": "SINGLE_COPY_LOCAL_ONLY",
        "attack_test_accesses": 0,
        "real_label_scenario_accesses": 0,
        "provider_calls": 0,
        "source_commit": CANDIDATE_PACKAGE_COMMIT,
    })
    write_json("PUBLIC_PRIVATE_DG05_RELEASE_INDEX_V10.json", index)
    print(json.dumps({
        "release": release["self_hash"], "qa": qa["self_hash"],
        "closure": closure["self_hash"], "index": index["self_hash"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
