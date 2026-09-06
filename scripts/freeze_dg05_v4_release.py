"""Freeze or independently replay the prospective DG05 Executable V4 release.

This command is pre-access only.  Its connected rehearsal uses synthetic
attack-side fixtures and already-frozen normal-only source bundles.
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
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))
ETAPR_SOURCE = ROOT / "artifacts/validation_v2/dg04_xver_prep/metric_source/af9e7aed35cfd160cbe0d04c8ec4c102502cb677"
ETAPR_DEPS = ROOT / "artifacts/validation_v2/dg04_xver_prep/metric_dependencies"
sys.path[:0] = [str(ETAPR_SOURCE), str(ETAPR_DEPS)]

from paperworks.validation_v2.dg05_connected_rehearsal_v4 import run_connected_synthetic_rehearsal_v4
from paperworks.validation_v2.dg05_execution_closure_v1 import canonical_bytes, file_sha256, self_hashed
from paperworks.validation_v2.dg05_metric_surface_v2 import build_metric_surface_contract_v2
from paperworks.validation_v2.dg05_production_chain_v1 import build_production_release_manifest_v1
from paperworks.validation_v2.etapr_exchange_v1 import OfficialEtaprV1
from paperworks.validation_v2.multipanel_custody_v1 import FROZEN_ATTACK_FILE_CENSUS_HASH_V2, FROZEN_METHOD_BUNDLE_HASH_V2
from scripts.freeze_dg05_execution_closure_v1 import build_detectors, build_dispatch, build_rule_runtime_registry, build_scope


OUT = ROOT / "research_control_center/validation_v2/dg05_v4_release"
DEC031 = ROOT / "research_control_center/validation_v2/dg05_dec031_binding/DEC031_BINDING_AUTHORITY_V1.json"
NORMAL_REGISTRY = ROOT / "research_control_center/validation_v2/dg05_dec031_binding/NORMAL_BURDEN_SOURCE_REGISTRY_V2.json"
NORMAL_CLOSURE = ROOT / "research_control_center/validation_v2/dg05_dec031_binding/NORMAL_SOURCE_CLOSURE_RECEIPT_V1.json"
V3 = ROOT / "research_control_center/validation_v2/dg05_metric_verifier_closure/DG05_EXECUTABLE_AUTHORITY_MANIFEST_V3.json"
V3_CLOSURE = ROOT / "research_control_center/validation_v2/dg05_metric_verifier_closure/DG05_EXECUTABLE_CLOSURE_AUTHORITY_V3.json"
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


def implementation_paths() -> dict[str, Path]:
    execution = ROOT / "src/paperworks/validation_v2/dg05_execution_closure_v1.py"
    chain = ROOT / "src/paperworks/validation_v2/dg05_production_chain_v1.py"
    connected = ROOT / "src/paperworks/validation_v2/dg05_connected_rehearsal_v4.py"
    return {
        "release_initializer": chain,
        "production_orchestrator": connected,
        "state_machine": connected,
        "projection_adapter": execution,
        "prediction_dispatch": ROOT / "src/paperworks/validation_v2/dg05_production_route_v4.py",
        "global_manifest_builder": execution,
        "global_freeze_builder": execution,
        "custodian_launcher": chain,
        "custodian": ROOT / "src/paperworks/validation_v2/dg05_label_custodian_v2.py",
        "scenario_builder": execution,
        "denominator_builder": execution,
        "normal_burden_replay": ROOT / "src/paperworks/validation_v2/dg05_normal_source_v2.py",
        "metric_primitive_builder": ROOT / "src/paperworks/validation_v2/dg05_metric_surface_execution_v2.py",
        "result_builder": ROOT / "src/paperworks/validation_v2/dg05_metric_surface_v2.py",
        "upstream_verifier": ROOT / "src/paperworks/validation_v2/dg05_upstream_lineage_verifier_v2.py",
        "result_verifier": ROOT / "src/paperworks/validation_v2/dg05_metric_surface_oracle_v2.py",
        "connected_production_route": connected,
        "dec031_semantics": ROOT / "src/paperworks/validation_v2/dg05_dec031_v1.py",
        "runtime_adapter": ROOT / "src/paperworks/validation_v2/dg05_runtime_adapter_v4.py",
        "custodian_process_entrypoint": ROOT / "scripts/run_dg05_label_custodian_v2.py",
        "release_freezer": Path(__file__),
    }


def prepare(private_manifest: Path) -> None:
    if OUT.exists():
        raise RuntimeError("APPEND_ONLY_RELEASE_DIRECTORY_CONFLICT")
    source_commit = git_head()
    dec031, registry, closure, historical = load(DEC031), load(NORMAL_REGISTRY), load(NORMAL_CLOSURE), load(V1)
    if (dec031["self_hash"] != "e9706eb50391021ada69fe269be3f22bb50f591239daaedfaa6194a04275de62"
            or registry["self_hash"] != "35b34e0a33d99334bf7bbf9a31289221db052429c6710a216c53165711b84220"
            or closure["self_hash"] != "277fe2626b51cb1b9af8052151f6fbfec499f6ab1a6ad73ebfbe93dc80b15eae"):
        raise RuntimeError("DEC031_OR_NORMAL_SOURCE_ROOT_REPLAY_FAILED")
    contract = build_metric_surface_contract_v2(
        source_commit=source_commit, dec031_binding_hash=dec031["self_hash"],
        normal_source_registry_hash=registry["self_hash"])
    expected = self_hashed({"schema": "expected_result_surface_v2", "executable_version": "DG05_EXECUTABLE_V4",
        "metric_surface_contract_hash": contract["self_hash"], "surface_count": contract["required_surface_count"],
        "surface_ids": [row["surface_id"] for row in contract["surfaces"]], "source_commit": source_commit})
    OUT.mkdir(parents=True)
    write(OUT / "METRIC_SURFACE_CONTRACT_V2.json", contract)
    write(OUT / "EXPECTED_RESULT_SURFACE_V2.json", expected)

    detectors = build_detectors(); rules, _ = build_rule_runtime_registry(); dispatch = build_dispatch(detectors, rules); scope = build_scope()
    nested = {
        "method_bundle": FROZEN_METHOD_BUNDLE_HASH_V2,
        "metric_contract": contract["self_hash"],
        "detector_registry": detectors.document()["self_hash"],
        "rule_runtime_registry": rules.document()["self_hash"],
        "dispatch_registry": dispatch.document()["self_hash"],
        "full_process_scope": scope.document()["self_hash"],
        "p1_custodian": historical["p1_custodian_v3_hash"],
        "attack_feature_allowlist": "e49ba9ee3f6a2f1273666c41ac1584636a53d5b4334d6cb95e3eed0b17a2764b",
        "attack_file_census": FROZEN_ATTACK_FILE_CENSUS_HASH_V2,
        "fusion": "587868f42fbdaedbd802541763e0390c09d2f04e4ba5944c45ad7e6e6593cbcc",
        "etapr": "5381ceb1f19f25354a8feb36488dfaa85d3f2945770dc352f2bf8c18fd86cae4",
        "statistical_contract": "cf90fee47e9294873e09aa516df8163328ee924d756c66b18a811c4ea2f9b463",
    }
    release = build_production_release_manifest_v1(
        repository_root=ROOT, predecessor_v3_manifest_path=V3,
        predecessor_v3_closure_path=V3_CLOSURE, implementation_paths=implementation_paths(),
        nested_authority_hashes=nested, semantic_binding_status="APPROVED",
        semantic_binding_hash=dec031["self_hash"], normal_burden_source_status="COMPLETE",
        normal_burden_source_registry_hash=registry["self_hash"], source_commit=source_commit,
        executable_version="DG05_EXECUTABLE_V4")
    release = self_hashed({**{key: value for key, value in release.items() if key != "self_hash"},
        "decision_binding": "DEC-031",
        "scientific_preregistration_hash": "cffa6f00dadee1bdd400cdbee545eb9cccd93dcf5da8c6bab3f67809644e8c61",
        "historical_execution_kernel_hash": historical["self_hash"]})
    release_path = OUT / "DG05_EXECUTABLE_AUTHORITY_MANIFEST_V4.json"
    write(release_path, release)

    wrapper = OfficialEtaprV1(ETAPR_SOURCE)
    with tempfile.TemporaryDirectory(prefix="dg05-v4-coordinator-") as raw:
        rehearsal = run_connected_synthetic_rehearsal_v4(
            repository_root=ROOT, work_root=Path(raw) / "route", release_path=release_path,
            predecessor_v3_path=V3, predecessor_v3_closure_path=V3_CLOSURE,
            historical_v1_manifest_path=V1,
            metric_contract_path=OUT / "METRIC_SURFACE_CONTRACT_V2.json", normal_registry_path=NORMAL_REGISTRY,
            private_normal_manifest_path=private_manifest,
            expected_private_manifest_hash=closure["private_manifest_hash"], wrapper=wrapper,
            source_commit=source_commit)
    write(OUT / "SYNTHETIC_DG05_PRODUCTION_ROUTE_REHEARSAL_V4.json", rehearsal)
    smoke = self_hashed({"schema": "frozen_method_smoke_v4", "status": "PASS",
        "evidence_kind": "AUTHORIZED_NORMAL_ONLY_FROZEN_METHOD_MATERIALIZATION_REPLAY",
        "normal_source_registry_hash": registry["self_hash"], "normal_source_closure_hash": closure["self_hash"],
        "method_bundle_count": closure["method_bundle_count"], "physical_component_count": closure["physical_component_count"],
        "frozen_methods": ["PCA", "ISOLATION_FOREST", "T0", "T2", "FUSION"],
        "new_fitting": closure["new_fitting"], "gdn_runs": closure["gdn_runs"],
        "attack_test_accesses": 0, "label_scenario_accesses": 0, "provider_calls": 0,
        "source_commit": source_commit})
    write(OUT / "FROZEN_METHOD_SMOKE_V4.json", smoke)

    rows = [{"surface_id": row["surface_id"], "declared": True, "production_built": True,
             "independent_upstream_replay": True, "independent_result_replay": True}
            for row in contract["surfaces"]]
    csv_path = OUT / "RESULT_SURFACE_COVERAGE_MATRIX_V2.csv"
    with csv_path.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    coverage = self_hashed({"schema": "result_surface_coverage_matrix_v2", "status": "PASS",
        "release_manifest_hash": release["self_hash"], "surface_count": len(rows),
        "covered_count": sum(all(value for key, value in row.items() if key != "surface_id") for row in rows),
        "csv_byte_hash": file_sha256(csv_path), "rows": rows, "source_commit": source_commit})
    write(OUT / "RESULT_SURFACE_COVERAGE_MATRIX_V2.json", coverage)
    mutations = self_hashed({"schema": "dg05_v4_mutation_evidence_v2", "status": "PASS",
        "release_manifest_hash": release["self_hash"],
        "rejected_mutation_cases": ["duplicate_timestamp", "non_unit_gap", "out_of_order_timestamp",
            "missing_rule_alarm_episodes",
            "caller_burden_decimal_mutation", "coherent_upstream_primitive_rehash",
            "exposure_duration_mutation", "method_authority_swap", "t0_t2_bundle_swap",
            "rule_fusion_bundle_swap", "hai22_train5_train6_swap"],
        "validated_semantic_edge_cases": ["alarm_in_inactive_interval_gap", "hit_in_second_interval",
            "overlapping_intervals", "configured_never_formed", "formed_never_evaluated",
            "evaluated_system_error", "alarming_rule", "multiple_rules_same_second"],
        "evidence_interpretation": "PASS_MEANS_EXPECTED_ACCEPT_OR_REJECT_BEHAVIOR_WAS_ASSERTED_BY_NAMED_TESTS",
        "unit_test_modules": ["tests.test_dg05_dec031_v1", "tests.test_dg05_normal_source_v2",
            "tests.test_dg05_metric_surface_v2", "tests.test_dg05_production_route_v4"],
        "attack_test_accesses": 0, "real_label_scenario_accesses": 0, "source_commit": source_commit})
    write(OUT / "MUTATION_EVIDENCE_V2.json", mutations)
    print(json.dumps({"release_hash": release["self_hash"], "rehearsal_hash": rehearsal["self_hash"],
                      "contract_hash": contract["self_hash"], "coverage_hash": coverage["self_hash"],
                      "mutation_hash": mutations["self_hash"], "smoke_hash": smoke["self_hash"]}, sort_keys=True))


def replay(private_manifest: Path) -> None:
    wrapper = OfficialEtaprV1(ETAPR_SOURCE)
    closure = load(NORMAL_CLOSURE)
    with tempfile.TemporaryDirectory(prefix="dg05-v4-independent-") as raw:
        receipt = run_connected_synthetic_rehearsal_v4(
            repository_root=ROOT, work_root=Path(raw) / "route",
            release_path=OUT / "DG05_EXECUTABLE_AUTHORITY_MANIFEST_V4.json",
            predecessor_v3_path=V3, predecessor_v3_closure_path=V3_CLOSURE,
            historical_v1_manifest_path=V1,
            metric_contract_path=OUT / "METRIC_SURFACE_CONTRACT_V2.json", normal_registry_path=NORMAL_REGISTRY,
            private_normal_manifest_path=private_manifest,
            expected_private_manifest_hash=closure["private_manifest_hash"], wrapper=wrapper,
            source_commit=load(OUT / "DG05_EXECUTABLE_AUTHORITY_MANIFEST_V4.json")["source_commit"])
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "independent-replay"))
    parser.add_argument("--private-normal-manifest", type=Path, required=True)
    args = parser.parse_args()
    if args.mode == "prepare": prepare(args.private_normal_manifest)
    else: replay(args.private_normal_manifest)


if __name__ == "__main__":
    main()
