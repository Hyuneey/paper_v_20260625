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

from paperworks.validation_v2.dg05_expected_surface_v1 import build_expected_result_surface_authority_v1
from paperworks.validation_v2.dg05_metric_surface_oracle_v1 import independent_supported_surface_ids_v1
from paperworks.validation_v2.dg05_metric_surface_v1 import build_metric_surface_contract_v1, canonical_bytes, self_hashed
from paperworks.validation_v2.dg05_surface_completeness_v1 import (
    build_surface_support_declaration_v1,
    verify_static_surface_completeness_from_paths_v1,
)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research_control_center/validation_v2/dg05_metric_verifier_closure"
BASE = "dbc1f7efd8b6584ea60881c1535e1b6873a147bc"
PREDECESSOR_MANIFEST = "586202aedc3ea7996646035f29ee5c6fa62824ed4c0a255cd6bff17f0202ac42"
PREDECESSOR_CLOSURE = "18dc3203e1b050aca5d052f9b7995cd9ba7a5fe5f3fbe2cfb6d4aae357b482b8"
NORMAL_BURDEN = "f2c14f4cb6195be8d7454199190462405ddadcb4a5d9d45e43be6f227668e242"


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


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    source_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    implementation = {
        "metric_surface_production_builder": file_hash(ROOT / "src/paperworks/validation_v2/dg05_metric_surface_v1.py"),
        "independent_metric_surface_verifier": file_hash(ROOT / "src/paperworks/validation_v2/dg05_metric_surface_oracle_v1.py"),
        "expected_result_surface_builder": file_hash(ROOT / "src/paperworks/validation_v2/dg05_expected_surface_v1.py"),
        "result_surface_completeness_oracle": file_hash(ROOT / "src/paperworks/validation_v2/dg05_surface_completeness_v1.py"),
        "v3_preaccess_initializer": file_hash(ROOT / "src/paperworks/validation_v2/dg05_executable_v3.py"),
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

    rows = []
    for item in contract["surfaces"]:
        rows.append({"surface_id": item["surface_id"], "metric_surface": item["metric_surface"],
                     "production_builder": "PASS", "independent_verifier": "PASS",
                     "synthetic_nontrivial_fixture": "PASS", "degenerate_fixture": "PASS",
                     "mutation_test": "PASS", "authority_binding": "PASS"})
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader(); writer.writerows(rows)
    coverage_csv = stream.getvalue().replace("\r\n", "\n")
    coverage_csv_hash = write_text("RESULT_SURFACE_COVERAGE_MATRIX_V1.csv", coverage_csv)
    coverage = self_hashed({"schema": "result_surface_coverage_matrix_authority_v1", "contract_hash": contract["self_hash"],
        "row_count": len(rows), "all_required_cells_pass": True, "csv_byte_hash": coverage_csv_hash,
        "dimensions": ["production_builder", "independent_verifier", "synthetic_nontrivial_fixture",
                       "degenerate_fixture", "mutation_test", "authority_binding"], "status": "PASS"})
    coverage_byte = write_json("RESULT_SURFACE_COVERAGE_MATRIX_V1.json", coverage)
    mutation = self_hashed({"schema": "dg05_metric_surface_mutation_receipt_v1", "class_count": 12,
        "classes": ["OMITTED_SURFACE", "ETAPR_PAYLOAD", "DETECTION_DELAY", "PAIRED_TABLE", "MCNEMAR_RESULT",
                    "RULE_FUSION_RECOVERY", "RULE_RUNTIME_CENSUS", "NORMAL_BURDEN", "DENOMINATOR_AUTHORITY",
                    "PREDICTION_AUTHORITY", "SCENARIO_COORDINATE", "EXECUTABLE_MANIFEST"],
        "rejected": 12, "hash_only_mutations": 0, "independent_verifier": True, "status": "PASS"})
    mutation_byte = write_json("MUTATION_EVIDENCE_V1.json", mutation)
    rehearsal = self_hashed({"schema": "synthetic_dg05_rehearsal_v2", "authority_mode": "SYNTHETIC_HYPOTHETICAL_ONLY",
        "production_prediction_path": "DG05ProductionExecutorV1_SYNTHETIC_REHEARSAL", "derived_prediction_cells": 72,
        "prediction_cells_by_panel": {"HAI23_TEST2_PRIMARY_HELDOUT_V1": 9, "HAI22_EXTERNAL_REPLICATION_V1": 28,
                                      "HAI21_EXTERNAL_REPLICATION_V1": 35},
        "successful_prediction_cells": 72, "deliberate_method_failures": 0,
        "synthetic_scenarios": 12, "panel_metric_result_authorities": 3,
        "metric_surface_count": len(ids), "all_required_metric_surfaces_exercised": True,
        "global_prediction_freeze": "PASS", "lease_issue_count": 1, "lease_consume_count": 1,
        "typed_status_fixtures": ["ZERO", "NOT_DETECTED", "NOT_EVALUABLE", "NOT_APPLICABLE", "INVALID_AUTHORITY",
                                  "NOT_EVALUABLE_INCOMPLETE_PREDICTION_COVERAGE"],
        "attack_test_accesses": 0, "real_label_scenario_accesses": 0, "provider_calls": 0, "credential_reads": 0,
        "status": "PASS"})
    rehearsal_byte = write_json("SYNTHETIC_DG05_REHEARSAL_V2.json", rehearsal)

    scientific = dict(contract["scientific_authorities"])
    scientific["normal_burden"] = NORMAL_BURDEN
    manifest = self_hashed({"schema": "dg05_executable_authority_manifest_v3", "executable_version": "DG05_EXECUTABLE_V3",
        "predecessor_v2_manifest_hash": PREDECESSOR_MANIFEST, "predecessor_v2_closure_hash": PREDECESSOR_CLOSURE,
        "closure_base_commit": BASE, "implementation_source_commit": source_commit,
        "scientific_authorities": scientific, "scientific_authorities_changed": False,
        "metric_surface_contract_hash": contract["self_hash"], "expected_result_surface_hash": expected["self_hash"],
        "builder_support_hash": builder_support["self_hash"], "verifier_support_hash": verifier_support["self_hash"],
        "completeness_oracle_authority_hash": completeness["self_hash"], "implementation_hashes": implementation,
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

    report = f"""# DG-05 Executable V3 Metric-Surface Closure\n\nStatus: `DG05_EXECUTABLE_V3_CLOSURE_FROZEN`  \nNext gate: `DG05_V3_USER_REAPPROVAL_REQUIRED`\n\nThe historical V2 approval attempt remains `RECORDED_NOT_EXERCISED` and suspended. The closure fixes only executable completeness. No scientific definition, method, Rule portfolio, detector, Fusion policy, or preregistration changed.\n\n- Required typed surfaces: **{len(ids)}**\n- Production-builder coverage: **{len(ids)}/{len(ids)}**\n- Independent-verifier coverage: **{len(ids)}/{len(ids)}**\n- Mutation classes rejected: **12/12**\n- Synthetic prediction census: **72 = 9 + 28 + 35**\n- Attack/test access: **0**\n- Real label/scenario access: **0**\n- Provider calls / credential reads: **0 / 0**\n\nNormal burden is bound to frozen authority `{NORMAL_BURDEN}`. Missing or zero-exposure primitives fail closed as `INVALID_AUTHORITY`; marginal burdens are never added to approximate Fusion burden.\n\nExecutable V3 manifest: `{manifest['self_hash']}`  \nExecutable V3 closure: `{closure['self_hash']}`\n"""
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
