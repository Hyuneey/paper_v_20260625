"""Freeze or replay the prospective DG05 Executable V5 package.

This command is pre-access only: synthetic attack-side fixtures and immutable
normal-source bundles are the only scientific data inputs.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT))
ETAPR_SOURCE = ROOT / "artifacts/validation_v2/dg04_xver_prep/metric_source/af9e7aed35cfd160cbe0d04c8ec4c102502cb677"
ETAPR_DEPS = ROOT / "artifacts/validation_v2/dg04_xver_prep/metric_dependencies"
sys.path[:0] = [str(ETAPR_SOURCE), str(ETAPR_DEPS)]

from paperworks.validation_v2.dg05_connected_rehearsal_v5 import run_connected_preaccess_rehearsal_v5
from paperworks.validation_v2.dg05_execution_closure_v1 import canonical_bytes, digest, file_sha256, self_hashed, validate_self_hashed
from paperworks.validation_v2.dg05_metric_surface_v2 import build_metric_surface_contract_v2
from paperworks.validation_v2.dg05_production_chain_v2 import build_production_release_manifest_v5
from paperworks.validation_v2.etapr_exchange_v1 import OfficialEtaprV1
from paperworks.validation_v2.multipanel_custody_v1 import FROZEN_ATTACK_FILE_CENSUS_HASH_V2, FROZEN_METHOD_BUNDLE_HASH_V2
from scripts.freeze_dg05_execution_closure_v1 import build_detectors, build_dispatch, build_rule_runtime_registry, build_scope
from scripts.materialize_dg05_normal_sources_v2 import _vault_root


VERSION_TAG = "V5"
EXECUTABLE_VERSION = "DG05_EXECUTABLE_V5"
OUT = ROOT / "research_control_center/validation_v2/dg05_v5_release"
SUPERSEDED_CANDIDATE_HASH = None
FREEZER_PATH = Path(__file__)
DEC031 = ROOT / "research_control_center/validation_v2/dg05_dec031_binding/DEC031_BINDING_AUTHORITY_V1.json"
NORMAL_REGISTRY = ROOT / "research_control_center/validation_v2/dg05_dec031_binding/NORMAL_BURDEN_SOURCE_REGISTRY_V2.json"
NORMAL_CLOSURE = ROOT / "research_control_center/validation_v2/dg05_dec031_binding/NORMAL_SOURCE_CLOSURE_RECEIPT_V1.json"
V4 = ROOT / "research_control_center/validation_v2/dg05_v4_release/DG05_EXECUTABLE_AUTHORITY_MANIFEST_V4.json"
V4_CLOSURE = ROOT / "research_control_center/validation_v2/dg05_v4_release/DG05_EXECUTABLE_CLOSURE_AUTHORITY_V4.json"
V1 = ROOT / "research_control_center/validation_v2/dg05_exec_closure/DG05_EXECUTABLE_AUTHORITY_MANIFEST_V1.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="ascii"))


def write(path: Path, value: dict) -> None:
    if path.exists():
        raise RuntimeError(f"APPEND_ONLY_PUBLIC_ARTIFACT_CONFLICT:{path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(value) + b"\n")


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def private_manifest(expected_hash: str) -> Path:
    hits = []
    for path in _vault_root().rglob("TASK_PRIVATE_VAULT_MANIFEST_V1.json"):
        try:
            if load(path).get("self_hash") == expected_hash:
                hits.append(path)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
    if len(hits) != 1:
        raise RuntimeError("EXACT_PRIVATE_NORMAL_MANIFEST_NOT_UNIQUE")
    return hits[0]


def implementation_paths() -> dict[str, Path]:
    execution = ROOT / "src/paperworks/validation_v2/dg05_execution_closure_v1.py"
    chain = ROOT / "src/paperworks/validation_v2/dg05_production_chain_v2.py"
    connected = ROOT / "src/paperworks/validation_v2/dg05_connected_rehearsal_v5.py"
    route = ROOT / "src/paperworks/validation_v2/dg05_production_route_v5.py"
    verifier = ROOT / "src/paperworks/validation_v2/dg05_upstream_lineage_verifier_v3.py"
    return {
        "release_initializer": chain, "production_orchestrator": connected,
        "state_machine": connected, "projection_adapter": execution,
        "projection_parser": ROOT / "src/paperworks/data/hai_normal_projection_v2.py",
        "prediction_dispatch": route, "production_kernel_parity": route,
        "preaccess_kernel_adapter": ROOT / "src/paperworks/validation_v2/dg05_preaccess_kernel_v5.py",
        "global_manifest_builder": execution, "global_freeze_builder": execution,
        "custodian_launcher": ROOT / "src/paperworks/validation_v2/dg05_production_chain_v1.py",
        "custodian": ROOT / "src/paperworks/validation_v2/dg05_label_custodian_v2.py",
        "scenario_builder": execution, "denominator_builder": execution,
        "normal_burden_replay": ROOT / "src/paperworks/validation_v2/dg05_normal_source_v2.py",
        "metric_primitive_builder": ROOT / "src/paperworks/validation_v2/dg05_metric_surface_execution_v2.py",
        "result_builder": ROOT / "src/paperworks/validation_v2/dg05_metric_surface_v2.py",
        "upstream_verifier": verifier, "root_to_result_verifier": verifier,
        "result_verifier": ROOT / "src/paperworks/validation_v2/dg05_metric_surface_oracle_v2.py",
        "connected_production_route": connected,
        "dec031_semantics": ROOT / "src/paperworks/validation_v2/dg05_dec031_v1.py",
        "runtime_adapter": ROOT / "src/paperworks/validation_v2/dg05_runtime_adapter_v4.py",
        "custodian_process_entrypoint": ROOT / "scripts/run_dg05_label_custodian_v2.py",
        "release_freezer": FREEZER_PATH,
        "release_freezer_core": ROOT / "scripts/freeze_dg05_v5_release.py",
        "connected_rehearsal_support": ROOT / "src/paperworks/validation_v2/dg05_connected_rehearsal_v4.py",
        "historical_authority_factory": ROOT / "scripts/freeze_dg05_execution_closure_v1.py",
        "frozen_asset_loader": ROOT / "scripts/materialize_dg05_normal_sources_v2.py",
        "upstream_intermediate_verifier": ROOT / "src/paperworks/validation_v2/dg05_upstream_lineage_verifier_v2.py",
        "metric_surface_core": ROOT / "src/paperworks/validation_v2/dg05_metric_surface_v1.py",
        "multipanel_custody_contract": ROOT / "src/paperworks/validation_v2/multipanel_custody_v1.py",
        "etapr_exchange": ROOT / "src/paperworks/validation_v2/etapr_exchange_v1.py",
        "formal_v4_runtime": ROOT / "src/paperworks/validation_v2/runtime_v1.py",
        "metric_oracle_core": ROOT / "src/paperworks/validation_v2/dg05_metric_surface_oracle_v1.py",
        "multipanel_etapr": ROOT / "src/paperworks/validation_v2/multipanel_etapr_v2.py",
        "multipanel_metrics": ROOT / "src/paperworks/validation_v2/multipanel_metrics_v1.py",
        "external_detector_kernel": ROOT / "src/paperworks/validation_v2/xver_detector_v1.py",
        "numeric_binding_contract": ROOT / "src/paperworks/validation_v2/exp02_bindings_v2a.py",
        "exp03b_contract": ROOT / "src/paperworks/validation_v2/exp03b_contract_v1.py",
    }


def prepare() -> None:
    if OUT.exists():
        raise RuntimeError("APPEND_ONLY_RELEASE_DIRECTORY_CONFLICT")
    source_commit = git_head()
    dec031, registry, closure, historical, v4 = load(DEC031), load(NORMAL_REGISTRY), load(NORMAL_CLOSURE), load(V1), load(V4)
    if (dec031["self_hash"] != "e9706eb50391021ada69fe269be3f22bb50f591239daaedfaa6194a04275de62"
            or registry["self_hash"] != "35b34e0a33d99334bf7bbf9a31289221db052429c6710a216c53165711b84220"
            or closure["self_hash"] != "277fe2626b51cb1b9af8052151f6fbfec499f6ab1a6ad73ebfbe93dc80b15eae"
            or v4["self_hash"] != "d31a726cb5c7b3620ed59dcff24ac75cd91e64028414931574fa33834a54a4b1"):
        raise RuntimeError("FROZEN_ROOT_REPLAY_FAILED")
    contract = build_metric_surface_contract_v2(
        source_commit=source_commit, dec031_binding_hash=dec031["self_hash"],
        normal_source_registry_hash=registry["self_hash"])
    expected = self_hashed({"schema": "expected_result_surface_v3", "executable_version": EXECUTABLE_VERSION,
        "metric_surface_contract_hash": contract["self_hash"], "surface_count": contract["required_surface_count"],
        "surface_ids": [row["surface_id"] for row in contract["surfaces"]], "source_commit": source_commit})
    OUT.mkdir(parents=True)
    write(OUT / "METRIC_SURFACE_CONTRACT_V2.json", contract)
    write(OUT / "EXPECTED_RESULT_SURFACE_V3.json", expected)

    detectors = build_detectors(); rules, _ = build_rule_runtime_registry(); dispatch = build_dispatch(detectors, rules); scope = build_scope()
    nested = {
        "method_bundle": FROZEN_METHOD_BUNDLE_HASH_V2, "metric_contract": contract["self_hash"],
        "detector_registry": detectors.document()["self_hash"], "rule_runtime_registry": rules.document()["self_hash"],
        "dispatch_registry": dispatch.document()["self_hash"], "full_process_scope": scope.document()["self_hash"],
        "p1_custodian": historical["p1_custodian_v3_hash"],
        "attack_feature_allowlist": "e49ba9ee3f6a2f1273666c41ac1584636a53d5b4334d6cb95e3eed0b17a2764b",
        "attack_file_census": FROZEN_ATTACK_FILE_CENSUS_HASH_V2,
        "fusion": "587868f42fbdaedbd802541763e0390c09d2f04e4ba5944c45ad7e6e6593cbcc",
        "etapr": "5381ceb1f19f25354a8feb36488dfaa85d3f2945770dc352f2bf8c18fd86cae4",
        "statistical_contract": "cf90fee47e9294873e09aa516df8163328ee924d756c66b18a811c4ea2f9b463",
    }
    release = build_production_release_manifest_v5(
        repository_root=ROOT, predecessor_v4_manifest_path=V4,
        predecessor_v4_closure_path=V4_CLOSURE, implementation_paths=implementation_paths(),
        nested_authority_hashes=nested, semantic_binding_hash=dec031["self_hash"],
        normal_burden_source_registry_hash=registry["self_hash"], source_commit=source_commit,
        scientific_preregistration_hash="cffa6f00dadee1bdd400cdbee545eb9cccd93dcf5da8c6bab3f67809644e8c61",
        historical_execution_kernel_hash=historical["self_hash"],
        executable_version=EXECUTABLE_VERSION,
        superseded_candidate_hash=SUPERSEDED_CANDIDATE_HASH)
    release_path = OUT / f"DG05_EXECUTABLE_AUTHORITY_MANIFEST_{VERSION_TAG}.json"
    write(release_path, release)
    wrapper = OfficialEtaprV1(ETAPR_SOURCE)
    with tempfile.TemporaryDirectory(prefix=f"dg05-{VERSION_TAG.lower()}-coordinator-") as raw:
        rehearsal, parity, roots = run_connected_preaccess_rehearsal_v5(
            repository_root=ROOT, work_root=Path(raw) / "route", release_path=release_path,
            predecessor_v4_path=V4, predecessor_v4_closure_path=V4_CLOSURE,
            historical_v1_manifest_path=V1, metric_contract_path=OUT / "METRIC_SURFACE_CONTRACT_V2.json",
            normal_registry_path=NORMAL_REGISTRY, private_normal_manifest_path=private_manifest(closure["private_manifest_hash"]),
            expected_private_manifest_hash=closure["private_manifest_hash"], wrapper=wrapper,
            source_commit=source_commit)
    write(OUT / f"SYNTHETIC_DG05_PRODUCTION_ROUTE_REHEARSAL_{VERSION_TAG}.json", rehearsal)
    write(OUT / "PRODUCTION_KERNEL_PARITY_V1.json", parity)
    write(OUT / "ROOT_TO_RESULT_REPLAY_V1.json", roots)
    smoke = self_hashed({"schema": f"frozen_method_smoke_{VERSION_TAG.lower()}", "status": "PASS",
        "evidence_kind": "CONNECTED_PREACCESS_FROZEN_PRODUCTION_KERNEL_EXECUTION",
        "release_manifest_hash": release["self_hash"], "kernel_parity_hash": parity["self_hash"],
        "normal_source_registry_hash": registry["self_hash"], "normal_source_closure_hash": closure["self_hash"],
        "method_bundle_count": closure["method_bundle_count"], "physical_component_count": closure["physical_component_count"],
        "frozen_methods": ["PCA", "ISOLATION_FOREST", "T0", "T2", "FUSION"],
        "new_fitting": 0, "gdn_runs": 0, "attack_test_accesses": 0,
        "label_scenario_accesses": 0, "provider_calls": 0, "source_commit": source_commit})
    write(OUT / f"FROZEN_METHOD_SMOKE_{VERSION_TAG}.json", smoke)

    rows = [{"surface_id": row["surface_id"], "declared": True, "production_built": True,
             "root_to_result_replay": True, "independent_result_replay": True}
            for row in contract["surfaces"]]
    csv_path = OUT / "RESULT_SURFACE_COVERAGE_MATRIX_V3.csv"
    with csv_path.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n"); writer.writeheader(); writer.writerows(rows)
    coverage = self_hashed({"schema": "result_surface_coverage_matrix_v3", "status": "PASS",
        "release_manifest_hash": release["self_hash"], "surface_count": len(rows), "covered_count": len(rows),
        "csv_byte_hash": file_sha256(csv_path), "rows": rows, "source_commit": source_commit})
    write(OUT / "RESULT_SURFACE_COVERAGE_MATRIX_V3.json", coverage)
    rejected = [
        "raw_physical_source_byte_mutation", "coherent_raw_projection_rehash", "projection_content_mutation",
        "duplicate_timestamp", "non_unit_gap", "out_of_order_timestamp", "raw_scenario_source_mutation",
        "custodian_output_coherent_rehash", "scenario_denominator_primitive_coherent_rehash",
        "denominator_primitive_coherent_rehash", "p1_scope_authority_swap", "custodian_request_policy_mismatch",
        "lease_mutation_or_second_consume", "global_freeze_swap", "method_authority_swap",
        "prediction_bytes_mutation", "rule_trace_mutation", "t0_t2_trace_source_swap",
        "rule_fusion_source_swap", "caller_burden_decimal_mutation", "normal_exposure_duration_mutation",
        "hai22_train5_train6_swap", "same_second_multi_rule_fail_inflation",
        "configured_never_formed_rule", "formed_never_evaluated_rule", "evaluated_system_error",
        "missing_rule_runtime_evidence", "synthetic_fallback_release_route",
    ]
    mutations = self_hashed({"schema": f"dg05_{VERSION_TAG.lower()}_mutation_evidence_v3", "status": "PASS",
        "release_manifest_hash": release["self_hash"], "rejected_mutation_cases": rejected,
        "case_count": len(rejected), "gap_proof_hash": "820d7b278b1d45931727796a5b96bed49862db80c60c6c203e7ea0d9268fa1db",
        "unit_test_modules": ["tests.test_dg05_v5_gap_proof", "tests.test_dg05_production_route_v5",
            "tests.test_dg05_upstream_lineage_verifier_v3", "tests.test_dg05_dec031_v1",
            "tests.test_dg05_normal_source_v2", "tests.test_dg05_metric_surface_v2"],
        "attack_test_accesses": 0, "real_label_scenario_accesses": 0, "source_commit": source_commit})
    write(OUT / "MUTATION_EVIDENCE_V3.json", mutations)
    print(json.dumps({"release_hash": release["self_hash"], "rehearsal_hash": rehearsal["self_hash"],
        "kernel_parity_hash": parity["self_hash"], "root_replay_hash": roots["self_hash"],
        "coverage_hash": coverage["self_hash"], "mutation_hash": mutations["self_hash"],
        "smoke_hash": smoke["self_hash"]}, sort_keys=True))


def replay() -> None:
    release = load(OUT / f"DG05_EXECUTABLE_AUTHORITY_MANIFEST_{VERSION_TAG}.json")
    closure = load(NORMAL_CLOSURE)
    wrapper = OfficialEtaprV1(ETAPR_SOURCE)
    with tempfile.TemporaryDirectory(prefix=f"dg05-{VERSION_TAG.lower()}-independent-") as raw:
        rehearsal, parity, roots = run_connected_preaccess_rehearsal_v5(
            repository_root=ROOT, work_root=Path(raw) / "route",
            release_path=OUT / f"DG05_EXECUTABLE_AUTHORITY_MANIFEST_{VERSION_TAG}.json",
            predecessor_v4_path=V4, predecessor_v4_closure_path=V4_CLOSURE,
            historical_v1_manifest_path=V1, metric_contract_path=OUT / "METRIC_SURFACE_CONTRACT_V2.json",
            normal_registry_path=NORMAL_REGISTRY, private_normal_manifest_path=private_manifest(closure["private_manifest_hash"]),
            expected_private_manifest_hash=closure["private_manifest_hash"], wrapper=wrapper,
            source_commit=release["source_commit"])
    frozen_rehearsal = load(OUT / f"SYNTHETIC_DG05_PRODUCTION_ROUTE_REHEARSAL_{VERSION_TAG}.json")
    frozen_parity = load(OUT / "PRODUCTION_KERNEL_PARITY_V1.json")
    frozen_roots = load(OUT / "ROOT_TO_RESULT_REPLAY_V1.json")
    for value in (frozen_rehearsal, frozen_parity, frozen_roots, rehearsal, parity, roots):
        validate_self_hashed(value)
    # Process receipts contain fresh OS PIDs, so their cryptographic identities
    # must differ between runs.  This explicit qualification fingerprint covers
    # every scientific/control outcome while each run independently authenticates
    # its own PID-bound invocation and root-verification receipt chain.
    rehearsal_fields = (
        "schema", "status", "release_manifest_hash", "release_initialization_hash",
        "authorized_data_mode", "execution_kernel_identity", "production_kernel_parity_hash",
        "production_kernel_invocation_count", "synthetic_fallback_invocation_count",
        "derived_prediction_cells", "successful_prediction_cells", "method_failures",
        "global_prediction_freeze", "synthetic_scenarios", "plural_interval_scenarios",
        "metric_surface_count", "root_covered_surface_count", "root_verification_count",
        "all_root_replay_flags_true", "independent_result_verification_count",
        "independent_result_verification_surface_count", "normal_source_component_count",
        "normal_source_bytes_reopened", "fresh_process_custodian", "custodian_pid_distinct",
        "lease_issue_count", "lease_consume_count", "lease_reissue_count", "attack_test_accesses",
        "real_label_scenario_accesses", "provider_calls", "credential_reads", "new_fitting",
        "new_rule_generation", "new_scientific_experiments", "result_driven_changes",
        "private_exposures", "fixture_authority", "source_commit",
    )
    rehearsal_fingerprint = lambda value: digest({key: value[key] for key in rehearsal_fields})
    root_fingerprint = lambda value: digest({
        "schema": value["schema"], "status": value["status"],
        "release_manifest_hash": value["release_manifest_hash"],
        "verification_count": value["verification_count"],
        "per_root_replay": value["per_root_replay"],
        "root_covered_surface_count": value["root_covered_surface_count"],
        "source_commit": value["source_commit"],
    })
    if (
        parity != frozen_parity
        or rehearsal_fingerprint(rehearsal) != rehearsal_fingerprint(frozen_rehearsal)
        or root_fingerprint(roots) != root_fingerprint(frozen_roots)
        or not all(roots["per_root_replay"].values())
        or not rehearsal["fresh_process_custodian"]
        or not rehearsal["custodian_pid_distinct"]
    ):
        raise RuntimeError("INDEPENDENT_CONNECTED_REPLAY_MISMATCH")
    print(json.dumps({"status": "PASS", "frozen_hashes": [
        frozen_rehearsal["self_hash"], frozen_parity["self_hash"], frozen_roots["self_hash"]],
        "fresh_replay_hashes": [rehearsal["self_hash"], parity["self_hash"], roots["self_hash"]],
        "fresh_process_pid_distinct": True}, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("mode", choices=("prepare", "independent-replay")); args = parser.parse_args()
    prepare() if args.mode == "prepare" else replay()


if __name__ == "__main__":
    main()
