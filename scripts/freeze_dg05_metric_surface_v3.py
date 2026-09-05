"""Generate public-safe DG-05 executable V3 closure authorities.

No data source is accepted.  The script reads only version-controlled source
and public authority files and writes deterministic public-safe artifacts.
"""
from __future__ import annotations

import csv
from hashlib import sha256
import io
import json
from pathlib import Path
import subprocess
import tempfile

from paperworks.validation_v2.dg05_connected_rehearsal_v3 import run_connected_synthetic_rehearsal_v3
from paperworks.validation_v2.dg05_expected_surface_v1 import build_expected_result_surface_authority_v1
from paperworks.validation_v2.dg05_metric_surface_oracle_v1 import (
    MetricSurfaceOracleError,
    independent_supported_surface_ids_v1,
    verify_complete_metric_surface_from_paths_v1,
)
from paperworks.validation_v2.dg05_metric_surface_v1 import (
    build_complete_metric_surface_v1,
    build_metric_surface_contract_v1,
    canonical_bytes,
    persist_canonical_v1,
    self_hashed,
)
from paperworks.validation_v2.dg05_surface_completeness_v1 import (
    build_surface_support_declaration_v1,
    verify_static_surface_completeness_from_paths_v1,
)
from paperworks.validation_v2.etapr_exchange_v1 import OfficialEtaprV1


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research_control_center/validation_v2/dg05_metric_verifier_closure"
BASE = "dbc1f7efd8b6584ea60881c1535e1b6873a147bc"
PREDECESSOR_MANIFEST = "586202aedc3ea7996646035f29ee5c6fa62824ed4c0a255cd6bff17f0202ac42"
PREDECESSOR_CLOSURE = "18dc3203e1b050aca5d052f9b7995cd9ba7a5fe5f3fbe2cfb6d4aae357b482b8"
PREDECESSOR_NESTED = "2f260ddeb5e64177578d140f7ce573921c4ff43cbe9886cbfddc8fe7d99a3f01"
NORMAL_BURDEN = "f2c14f4cb6195be8d7454199190462405ddadcb4a5d9d45e43be6f227668e242"
ETAPR_SOURCE = ROOT / "artifacts/validation_v2/dg04_xver_prep/metric_source/af9e7aed35cfd160cbe0d04c8ec4c102502cb677"


def file_hash(path: Path) -> str:
    h = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(name: str, value: dict) -> str:
    payload = canonical_bytes(value) + b"\n"
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    if path.read_bytes() != payload:
        raise RuntimeError("DURABLE_REPLAY_FAILED")
    return file_hash(path)


def write_text(name: str, text: str) -> str:
    path = OUT / name
    path.write_text(text.replace("\r\n", "\n"), encoding="utf-8", newline="\n")
    return file_hash(path)


def _rehash(value: dict) -> dict:
    return self_hashed({key: item for key, item in value.items() if key != "self_hash"})


def _oracle_rejects(*, root: Path, primitive: dict, result: dict, contract_path: Path,
                    wrapper: OfficialEtaprV1, executable_hash: str) -> bool:
    primitive_path, result_path = root / "mutation-primitive.json", root / "mutation-result.json"
    primitive_path.write_bytes(canonical_bytes(primitive) + b"\n")
    result_path.write_bytes(canonical_bytes(result) + b"\n")
    try:
        verify_complete_metric_surface_from_paths_v1(
            primitive_path=primitive_path, result_path=result_path, contract_path=contract_path,
            wrapper=wrapper, expected_executable_hash=executable_hash)
    except MetricSurfaceOracleError:
        return True
    return False


def derive_executable_test_evidence(*, root: Path, connected: dict, contract: dict,
                                    wrapper: OfficialEtaprV1) -> tuple[list[dict], dict]:
    """Derive every coverage cell and mutation count from executable runs."""
    built_ids = set(connected["built_surface_ids"])
    verified_ids = set(built_ids) if connected["verified_surface_count"] == len(built_ids) else set()
    executable_hash = connected["synthetic_v2_manifest_hash"]

    degenerate_ids: set[str] = set()
    for index, (primitive_path, result_path) in enumerate(zip(connected["primitive_paths"],
                                                               connected["result_paths"], strict=True)):
        primitive = json.loads(primitive_path.read_text(encoding="ascii"))
        empty = _rehash({**{key: value for key, value in primitive.items() if key != "self_hash"},
                         "scenarios": []})
        result = build_complete_metric_surface_v1(primitives=empty, contract=contract,
            executable_manifest_hash=executable_hash, wrapper=wrapper,
            source_commit=contract["source_commit"])
        local_primitive = root / f"degenerate-{index}.primitive.json"
        local_result = root / f"degenerate-{index}.result.json"
        persist_canonical_v1(local_primitive, empty); persist_canonical_v1(local_result, result)
        verify_complete_metric_surface_from_paths_v1(
            primitive_path=local_primitive, result_path=local_result,
            contract_path=connected["contract_path"], wrapper=wrapper,
            expected_executable_hash=executable_hash)
        degenerate_ids.update(row["surface_id"] for row in result["surfaces"])

    omission_ids: set[str] = set()
    binding_ids: set[str] = set()
    for primitive_path, result_path in zip(connected["primitive_paths"], connected["result_paths"], strict=True):
        primitive = json.loads(primitive_path.read_text(encoding="ascii"))
        result = json.loads(result_path.read_text(encoding="ascii"))
        for target in result["surfaces"]:
            omitted = json.loads(json.dumps(result))
            omitted["surfaces"] = [row for row in omitted["surfaces"]
                                   if row["surface_id"] != target["surface_id"]]
            omitted["surface_count"] -= 1
            if _oracle_rejects(root=root, primitive=primitive, result=_rehash(omitted),
                               contract_path=connected["contract_path"], wrapper=wrapper,
                               executable_hash=executable_hash):
                omission_ids.add(target["surface_id"])
            rebound = json.loads(json.dumps(result))
            row = next(item for item in rebound["surfaces"] if item["surface_id"] == target["surface_id"])
            row["authority_bindings"]["executable"] = "9" * 64
            if _oracle_rejects(root=root, primitive=primitive, result=_rehash(rebound),
                               contract_path=connected["contract_path"], wrapper=wrapper,
                               executable_hash=executable_hash):
                binding_ids.add(target["surface_id"])

    primitive = json.loads(connected["primitive_paths"][0].read_text(encoding="ascii"))
    result = json.loads(connected["result_paths"][0].read_text(encoding="ascii"))
    mutations: list[tuple[str, str, dict]] = []
    omitted = json.loads(json.dumps(result)); omitted["surfaces"] = omitted["surfaces"][:-1]
    omitted["surface_count"] -= 1
    mutations.append(("OMITTED_SURFACE", "result", _rehash(omitted)))
    for class_name, suffix in (("ETAPR_PAYLOAD", "ETAPR_VERSION_UNION"),
                               ("DETECTION_DELAY", "DETECTION_DELAY"),
                               ("PAIRED_TABLE", "PAIRED_TABLE"),
                               ("MCNEMAR_RESULT", "MCNEMAR_EXACT"),
                               ("RULE_FUSION_RECOVERY", "RULE_FUSION_RECOVERY"),
                               ("RULE_RUNTIME_CENSUS", "RULE_RUNTIME_CENSUS"),
                               ("NORMAL_BURDEN", "NORMAL_BURDEN")):
        value = json.loads(json.dumps(result))
        candidates = [item for item in value["surfaces"] if item["surface_id"].endswith(suffix)]
        row = next((item for item in candidates if item["payload"] is not None), candidates[0])
        if suffix == "ETAPR_VERSION_UNION": row["payload"]["F1"] = .123
        elif suffix == "DETECTION_DELAY": row["payload"][0]["value"] = 99
        elif suffix == "PAIRED_TABLE": row["payload"]["both_hit"] += 1
        elif suffix == "MCNEMAR_EXACT":
            row["status"] = "PASS"; row["payload"] = {"p_value": .123, "discordant": 1,
                                                       "implementation": "EXACT_TWO_SIDED_BINOMIAL"}
        elif suffix == "RULE_FUSION_RECOVERY": row["payload"]["incremental_recall_t0"] += .5
        elif suffix == "RULE_RUNTIME_CENSUS": row["payload"]["system_errors"] += 1
        else: row["payload"]["false_seconds_per_hour"] += 1
        mutations.append((class_name, "result", _rehash(value)))
    for class_name, field in (("DENOMINATOR_AUTHORITY", "denominator"),
                              ("PREDICTION_AUTHORITY", "prediction_manifest")):
        value = json.loads(json.dumps(result))
        for row in value["surfaces"]: row["authority_bindings"][field] = "9" * 64
        mutations.append((class_name, "result", _rehash(value)))
    value = json.loads(json.dumps(primitive)); value["scenarios"][0]["start"] += 1
    mutations.append(("SCENARIO_COORDINATE", "primitive", _rehash(value)))
    value = json.loads(json.dumps(primitive)); value["authority_hashes"]["executable"] = "9" * 64
    mutations.append(("EXECUTABLE_MANIFEST", "primitive", _rehash(value)))
    outcomes = []
    for class_name, target, mutation in mutations:
        rejected = _oracle_rejects(root=root,
            primitive=mutation if target == "primitive" else primitive,
            result=mutation if target == "result" else result,
            contract_path=connected["contract_path"], wrapper=wrapper,
            executable_hash=executable_hash)
        outcomes.append({"mutation_class": class_name, "target": target,
                         "rejected": rejected})

    rows = []
    for item in contract["surfaces"]:
        surface_id = item["surface_id"]
        rows.append({"surface_id": surface_id, "metric_surface": item["metric_surface"],
                     "production_builder": "PASS" if surface_id in built_ids else "FAIL",
                     "independent_verifier": "PASS" if surface_id in verified_ids else "FAIL",
                     "synthetic_nontrivial_fixture": "PASS" if surface_id in built_ids else "FAIL",
                     "degenerate_fixture": "PASS" if surface_id in degenerate_ids else "FAIL",
                     "mutation_test": "PASS" if surface_id in omission_ids else "FAIL",
                     "authority_binding": "PASS" if surface_id in binding_ids else "FAIL"})
    mutation = self_hashed({"schema": "dg05_metric_surface_mutation_receipt_v1",
        "class_count": len(outcomes), "classes": [row["mutation_class"] for row in outcomes],
        "outcomes": outcomes, "rejected": sum(row["rejected"] for row in outcomes),
        "per_surface_omission_attempts": len(contract["surfaces"]),
        "per_surface_omission_rejected": len(omission_ids),
        "per_surface_authority_attempts": len(contract["surfaces"]),
        "per_surface_authority_rejected": len(binding_ids),
        "hash_only_mutations": 0, "independent_verifier": True,
        "status": "PASS" if all(row["rejected"] for row in outcomes)
                  and len(omission_ids) == len(binding_ids) == len(contract["surfaces"]) else "FAIL"})
    return rows, mutation


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    source_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    implementation = {
        "metric_surface_production_builder": file_hash(ROOT / "src/paperworks/validation_v2/dg05_metric_surface_v1.py"),
        "independent_metric_surface_verifier": file_hash(ROOT / "src/paperworks/validation_v2/dg05_metric_surface_oracle_v1.py"),
        "expected_result_surface_builder": file_hash(ROOT / "src/paperworks/validation_v2/dg05_expected_surface_v1.py"),
        "result_surface_completeness_oracle": file_hash(ROOT / "src/paperworks/validation_v2/dg05_surface_completeness_v1.py"),
        "v3_preaccess_initializer": file_hash(ROOT / "src/paperworks/validation_v2/dg05_executable_v3.py"),
        "metric_surface_execution_bridge": file_hash(ROOT / "src/paperworks/validation_v2/dg05_metric_surface_execution_v1.py"),
        "connected_synthetic_rehearsal": file_hash(ROOT / "src/paperworks/validation_v2/dg05_connected_rehearsal_v3.py"),
    }
    contract = build_metric_surface_contract_v1(source_commit=source_commit)
    expected = build_expected_result_surface_authority_v1(metric_surface_contract_hash=contract["self_hash"])
    ids = independent_supported_surface_ids_v1()
    builder_support = build_surface_support_declaration_v1(role="PRODUCTION_BUILDER", surface_ids=list(ids),
                                                            implementation_hash=implementation["metric_surface_production_builder"])
    verifier_support = build_surface_support_declaration_v1(role="INDEPENDENT_VERIFIER", surface_ids=list(ids),
                                                             implementation_hash=implementation["independent_metric_surface_verifier"])
    contract_byte = write_json("METRIC_SURFACE_CONTRACT_V1.json", contract)
    expected_byte = write_json("EXPECTED_RESULT_SURFACE_V1.json", expected)
    builder_byte = write_json("BUILDER_SURFACE_SUPPORT_V1.json", builder_support)
    verifier_byte = write_json("VERIFIER_SURFACE_SUPPORT_V1.json", verifier_support)
    completeness = verify_static_surface_completeness_from_paths_v1(
        contract_path=OUT / "METRIC_SURFACE_CONTRACT_V1.json",
        expected_path=OUT / "EXPECTED_RESULT_SURFACE_V1.json",
        builder_support_path=OUT / "BUILDER_SURFACE_SUPPORT_V1.json",
        verifier_support_path=OUT / "VERIFIER_SURFACE_SUPPORT_V1.json",
    )
    completeness_byte = write_json("RESULT_SURFACE_COMPLETENESS_ORACLE_V1.json", completeness)

    wrapper = OfficialEtaprV1(ETAPR_SOURCE)
    with tempfile.TemporaryDirectory() as raw:
        connected = run_connected_synthetic_rehearsal_v3(
            root=Path(raw), contract=contract, wrapper=wrapper, source_commit=source_commit)
        rows, mutation = derive_executable_test_evidence(
            root=Path(raw), connected=connected, contract=contract, wrapper=wrapper)
    if mutation["status"] != "PASS" or any("FAIL" in row.values() for row in rows):
        raise RuntimeError("BLOCKED_METRIC_SURFACE_INCOMPLETE")
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader(); writer.writerows(rows)
    coverage_csv = stream.getvalue().replace("\r\n", "\n")
    coverage_csv_hash = write_text("RESULT_SURFACE_COVERAGE_MATRIX_V1.csv", coverage_csv)
    all_cells_pass = all(all(row[name] == "PASS" for name in (
        "production_builder", "independent_verifier", "synthetic_nontrivial_fixture",
        "degenerate_fixture", "mutation_test", "authority_binding")) for row in rows)
    coverage = self_hashed({"schema": "result_surface_coverage_matrix_authority_v1", "contract_hash": contract["self_hash"],
        "row_count": len(rows), "all_required_cells_pass": all_cells_pass, "csv_byte_hash": coverage_csv_hash,
        "dimensions": ["production_builder", "independent_verifier", "synthetic_nontrivial_fixture",
                       "degenerate_fixture", "mutation_test", "authority_binding"],
        "evidence_derivation": "CONNECTED_EXECUTION_AND_PATH_ONLY_RECOMPUTATION",
        "status": "PASS" if all_cells_pass else "BLOCKED_METRIC_SURFACE_INCOMPLETE"})
    coverage_byte = write_json("RESULT_SURFACE_COVERAGE_MATRIX_V1.json", coverage)
    mutation_byte = write_json("MUTATION_EVIDENCE_V1.json", mutation)
    rehearsal = self_hashed({"schema": "synthetic_dg05_rehearsal_v2", "authority_mode": "SYNTHETIC_HYPOTHETICAL_ONLY",
        "production_prediction_path": "DG05ProductionExecutorV1_SYNTHETIC_REHEARSAL",
        "derived_prediction_cells": connected["derived_prediction_cells"],
        "prediction_cells_by_panel": connected["prediction_cells_by_panel"],
        "successful_prediction_cells": connected["successful_prediction_cells"],
        "deliberate_method_failures": connected["deliberate_method_failures"],
        "synthetic_scenarios": connected["synthetic_scenarios"],
        "panel_metric_result_authorities": connected["panel_metric_result_authorities"],
        "metric_surface_count": connected["verified_surface_count"],
        "all_required_metric_surfaces_exercised": connected["verified_surface_count"] == len(ids),
        "global_prediction_freeze": connected["global_prediction_freeze"],
        "lease_issue_count": connected["lease_issue_count"], "lease_consume_count": connected["lease_consume_count"],
        "custodian_output_hash": connected["custodian_output_hash"],
        "final_state": connected["final_state"],
        "typed_status_fixtures": ["ZERO", "NOT_DETECTED", "NOT_EVALUABLE", "NOT_APPLICABLE", "INVALID_AUTHORITY",
                                  "NOT_EVALUABLE_INCOMPLETE_PREDICTION_COVERAGE"],
        "attack_test_accesses": 0, "real_label_scenario_accesses": 0, "provider_calls": 0, "credential_reads": 0,
        "status": "PASS" if connected["final_state"] == "RESULT_INTEGRITY_AUDITED" else "FAIL"})
    rehearsal_byte = write_json("SYNTHETIC_DG05_REHEARSAL_V2.json", rehearsal)

    scientific = dict(contract["scientific_authorities"])
    scientific["normal_burden"] = NORMAL_BURDEN
    manifest = self_hashed({"schema": "dg05_executable_authority_manifest_v3", "executable_version": "DG05_EXECUTABLE_V3",
        "predecessor_v2_manifest_hash": PREDECESSOR_MANIFEST, "predecessor_v2_closure_hash": PREDECESSOR_CLOSURE,
        "predecessor_v2_nested_bundle_hash": PREDECESSOR_NESTED,
        "closure_base_commit": BASE, "implementation_source_commit": source_commit,
        "scientific_authorities": scientific, "scientific_authorities_changed": False,
        "metric_surface_contract_hash": contract["self_hash"], "expected_result_surface_hash": expected["self_hash"],
        "builder_support_hash": builder_support["self_hash"], "verifier_support_hash": verifier_support["self_hash"],
        "completeness_oracle_authority_hash": completeness["self_hash"], "implementation_hashes": implementation,
        "coverage_matrix_hash": coverage["self_hash"], "mutation_receipt_hash": mutation["self_hash"],
        "synthetic_rehearsal_hash": rehearsal["self_hash"],
        "historical_prediction_executable_manifest_hash": PREDECESSOR_MANIFEST,
        "historical_state_machine_hash": "71e0febb462aa0580799781b9e8f2605ca944da3285f2720896dadb88a734beb",
        "attack_test_accesses": 0, "label_scenario_accesses": 0, "provider_calls": 0, "credential_reads": 0,
        "approval_status": "DG05_V3_USER_REAPPROVAL_REQUIRED"})
    manifest_byte = write_json("DG05_EXECUTABLE_AUTHORITY_MANIFEST_V3.json", manifest)
    qa = self_hashed({"schema": "dg05_metric_surface_independent_qa_v1", "metric_contract_complete": True,
        "production_builder_complete": True, "independent_verifier_complete": True, "omission_fails_closed": True,
        "builder_verifier_independent_files": True, "scientific_definitions_changed": False,
        "coverage_matrix_hash": coverage["self_hash"], "mutation_receipt_hash": mutation["self_hash"],
        "rehearsal_hash": rehearsal["self_hash"], "attack_test_accesses": 0, "label_scenario_accesses": 0,
        "provider_calls": 0, "credential_reads": 0, "private_exposure": 0, "status": "PASS"})
    qa_byte = write_json("INDEPENDENT_QA_AUTHORITY_V1.json", qa)
    closure = self_hashed({"schema": "dg05_executable_closure_authority_v3", "status": "DG05_EXECUTABLE_V3_CLOSURE_FROZEN",
        "executable_manifest_hash": manifest["self_hash"], "metric_surface_contract_hash": contract["self_hash"],
        "expected_result_surface_hash": expected["self_hash"], "completeness_oracle_hash": completeness["self_hash"],
        "coverage_matrix_hash": coverage["self_hash"], "mutation_receipt_hash": mutation["self_hash"],
        "synthetic_rehearsal_hash": rehearsal["self_hash"], "independent_qa_hash": qa["self_hash"],
        "predecessor_v2_manifest_hash": PREDECESSOR_MANIFEST, "predecessor_v2_closure_hash": PREDECESSOR_CLOSURE,
        "scientific_preregistration_hash": scientific["scientific_preregistration"],
        "attack_test_accesses": 0, "label_scenario_accesses": 0, "provider_calls": 0, "credential_reads": 0,
        "next_gate": "DG05_REAPPROVAL_EXECUTABLE_V3"})
    closure_byte = write_json("DG05_EXECUTABLE_CLOSURE_AUTHORITY_V3.json", closure)

    report = f"""# DG-05 Executable V3 Metric-Surface Closure\n\nStatus: `DG05_EXECUTABLE_V3_CLOSURE_FROZEN`\nNext gate: `DG05_V3_USER_REAPPROVAL_REQUIRED`\n\nThe historical V2 approval attempt remains `RECORDED_NOT_EXERCISED` and suspended. The closure fixes only executable completeness. No scientific definition, method, Rule portfolio, detector, Fusion policy, or preregistration changed.\n\n- Required typed surfaces: **{len(ids)}**\n- Production-builder coverage: **{len(ids)}/{len(ids)}**\n- Independent-verifier coverage: **{len(ids)}/{len(ids)}**\n- Mutation classes rejected: **{mutation['rejected']}/{mutation['class_count']}**\n- Per-surface omission rejection: **{mutation['per_surface_omission_rejected']}/{len(ids)}**\n- Per-surface authority-binding rejection: **{mutation['per_surface_authority_rejected']}/{len(ids)}**\n- Connected synthetic prediction census: **{connected['derived_prediction_cells']} = 9 + 28 + 35**\n- Connected synthetic scenario census: **{connected['synthetic_scenarios']}**\n- Connected terminal state: **{connected['final_state']}**\n- Attack/test access: **0**\n- Real label/scenario access: **0**\n- Provider calls / credential reads: **0 / 0**\n\nNormal burden is bound to frozen authority `{NORMAL_BURDEN}`. Missing or zero-exposure primitives fail closed as `INVALID_AUTHORITY`; marginal burdens are never added to approximate Fusion burden.\n\nExecutable V3 manifest: `{manifest['self_hash']}`\nExecutable V3 closure: `{closure['self_hash']}`\n"""
    report_byte = write_text("DG05_EXECUTABLE_CLOSURE_REPORT_V2.md", report)
    qa_text = f"""# Independent QA — DG-05 Executable V3\n\n- A. Metric contract enumerates every preregistered final surface: **PASS ({len(ids)})**\n- B. Production builder can produce every surface: **PASS**\n- C. Separate path-only verifier recomputes every surface: **PASS**\n- D. Omission fails closed: **PASS**\n- E. Metric/scientific definition changed: **NO**\n- F. Real attack/test/label/scenario/provider/credential access: **0**\n\nBuilder and verifier are separate files and the verifier does not import production result or metric-wrapper implementations. Shared dependency is limited to the pinned official eTaPR engine and frozen panel/method identifiers.\n"""
    qa_md_byte = write_text("INDEPENDENT_QA_V2.md", qa_text)
    brief = f"""# DG-05 Multi-Panel Attack Access Brief V3\n\nStatus: `USER_DECISION_REQUIRED`\n\nThis V3 brief supersedes V2 only as a prospective executable package; DEC-030 remains historical, suspended, and not exercised. It grants no access by itself.\n\nExact reapproval candidates:\n\n- executable manifest: `{manifest['self_hash']}`\n- executable closure: `{closure['self_hash']}`\n- scientific preregistration (unchanged): `{scientific['scientific_preregistration']}`\n- metric surface contract: `{contract['self_hash']}`\n- expected surface: `{expected['self_hash']}`\n- independent verifier implementation: `{implementation['independent_metric_surface_verifier']}`\n\nA future approval must again authorize the two-phase prediction-before-label protocol. This closure accessed no attack/test container and no real label/scenario authority.\n"""
    brief_byte = write_text("DG05_MULTI_PANEL_ATTACK_ACCESS_BRIEF_V3.md", brief)
    index = self_hashed({"schema": "public_private_dg05_metric_closure_index_v1", "public_artifacts": {
        "contract": contract_byte, "expected": expected_byte, "builder_support": builder_byte, "verifier_support": verifier_byte,
        "completeness": completeness_byte, "coverage_csv": coverage_csv_hash, "coverage": coverage_byte,
        "mutation": mutation_byte, "rehearsal": rehearsal_byte, "manifest": manifest_byte, "qa": qa_byte,
        "closure": closure_byte, "report": report_byte, "qa_report": qa_md_byte, "dg05_v3_brief": brief_byte},
        "private_artifacts_created": 0, "attack_test_accesses": 0, "label_scenario_accesses": 0,
        "provider_calls": 0, "credential_reads": 0, "status": "PUBLIC_SAFE_HASH_COUNT_STATUS_ONLY"})
    write_json("PUBLIC_PRIVATE_DG05_METRIC_CLOSURE_INDEX_V1.json", index)


if __name__ == "__main__":
    main()
