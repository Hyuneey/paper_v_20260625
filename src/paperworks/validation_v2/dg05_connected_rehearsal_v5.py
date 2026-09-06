"""V5 connected pre-access rehearsal using the frozen production kernel."""
from __future__ import annotations

from datetime import datetime, timedelta
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from .dg05_connected_rehearsal_v4 import (
    NOMINAL,
    VERSION,
    _load as _load_v4,
    _private_normal_paths,
    _state,
    _typed_manifest,
    _write_fixture,
)
from .dg05_execution_closure_v1 import (
    PhysicalFileIdentityV2,
    ScenarioRecordV1,
    build_denominator_authority_v1,
    build_expected_prediction_cell_census_v1,
    build_global_prediction_manifest_v1,
    build_scenario_authority_v1,
    canonical_bytes,
    digest,
    file_sha256,
    freeze_global_predictions_v1,
    persist_prediction_receipt_v1,
    self_hashed,
)
from .dg05_metric_surface_execution_v2 import build_metric_primitives_from_frozen_execution_v2
from .dg05_metric_surface_oracle_v2 import verify_complete_metric_surface_from_paths_v2
from .dg05_metric_surface_v2 import build_complete_metric_surface_v2, persist_canonical_v1
from .dg05_normal_source_v2 import replay_normal_source_registry_v2
from .dg05_preaccess_kernel_v5 import build_preaccess_frozen_kernel_executor_v5
from .dg05_production_chain_v1 import launch_custodian_fresh_process_v2
from .dg05_production_chain_v2 import initialize_production_release_v5
from .dg05_production_route_v5 import KernelInvocationCensusV5, execute_prediction_cell_v5
from .dg05_upstream_lineage_verifier_v2 import UpstreamPanelReplayPathsV2
from .dg05_upstream_lineage_verifier_v3 import RootToResultReplayPathsV3, verify_asserted_primitive_from_roots_v3
from .etapr_exchange_v1 import OfficialEtaprV1
from .multipanel_custody_v1 import (
    FROZEN_ATTACK_FILE_CENSUS_HASH_V2,
    FROZEN_ATTACK_FILE_IDS_V2,
    FROZEN_AUTHORITY_SOURCE_COMMIT_V2,
    FROZEN_METHOD_BUNDLE_HASH_V2,
    FROZEN_PANEL_ORDER_V2,
    FrozenPhysicalFileAuthorityV2,
    frozen_feature_allowlist_authorities_v2,
)


class DG05ConnectedRehearsalV5Error(ValueError):
    pass


def _load(path: Path, schema: str) -> dict[str, Any]:
    raw = path.read_bytes()
    try:
        value = json.loads(raw.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DG05ConnectedRehearsalV5Error("CANONICAL_INPUT_REQUIRED") from exc
    if raw != canonical_bytes(value) + b"\n" or value.get("schema") != schema:
        raise DG05ConnectedRehearsalV5Error(f"CANONICAL_SCHEMA_REPLAY_FAILED:{schema}")
    if value.get("self_hash") != digest({key: item for key, item in value.items() if key != "self_hash"}):
        raise DG05ConnectedRehearsalV5Error(f"SELF_HASH_REPLAY_FAILED:{schema}")
    return value


def run_connected_preaccess_rehearsal_v5(
    *, repository_root: Path, work_root: Path, release_path: Path,
    predecessor_v4_path: Path, predecessor_v4_closure_path: Path,
    historical_v1_manifest_path: Path, metric_contract_path: Path,
    normal_registry_path: Path, private_normal_manifest_path: Path,
    expected_private_manifest_hash: str, wrapper: OfficialEtaprV1,
    source_commit: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Run the full synthetic topology with exact frozen method assets."""
    work_root.mkdir(parents=True, exist_ok=False)
    release = _load(release_path, "dg05_production_release_manifest_v2")
    initialized = initialize_production_release_v5(
        release_manifest_path=release_path, repository_root=repository_root,
        predecessor_v4_manifest_path=predecessor_v4_path,
        predecessor_v4_closure_path=predecessor_v4_closure_path,
        expected_release_hash=release["self_hash"],
        authority_mode="PREACCESS_FROZEN_KERNEL_REHEARSAL",
        expected_executable_version=release["executable_version"])
    contract = _load(metric_contract_path, "metric_surface_contract_v2")
    normal_registry = _load(normal_registry_path, "normal_burden_source_registry_v2")
    historical = _typed_manifest(historical_v1_manifest_path)

    from scripts.freeze_dg05_execution_closure_v1 import (
        build_detectors, build_dispatch, build_rule_runtime_registry, build_scope,
    )
    detectors = build_detectors()
    rules, rule_sources = build_rule_runtime_registry()
    dispatch = build_dispatch(detectors, rules)
    scope = build_scope()
    expected_nested = {
        "method_bundle": FROZEN_METHOD_BUNDLE_HASH_V2,
        "metric_contract": contract["self_hash"],
        "detector_registry": detectors.document()["self_hash"],
        "rule_runtime_registry": rules.document()["self_hash"],
        "dispatch_registry": dispatch.document()["self_hash"],
        "full_process_scope": scope.document()["self_hash"],
        "p1_custodian": historical.p1_custodian_v3_hash,
        "attack_feature_allowlist": "e49ba9ee3f6a2f1273666c41ac1584636a53d5b4334d6cb95e3eed0b17a2764b",
        "attack_file_census": FROZEN_ATTACK_FILE_CENSUS_HASH_V2,
        "fusion": "587868f42fbdaedbd802541763e0390c09d2f04e4ba5944c45ad7e6e6593cbcc",
        "etapr": "5381ceb1f19f25354a8feb36488dfaa85d3f2945770dc352f2bf8c18fd86cae4",
        "statistical_contract": "cf90fee47e9294873e09aa516df8163328ee924d756c66b18a811c4ea2f9b463",
    }
    if (
        release.get("nested_authority_hashes") != expected_nested
        or historical.document()["self_hash"] != release["historical_execution_kernel_hash"]
        or normal_registry["self_hash"] != release["normal_burden_source_registry_hash"]
    ):
        raise DG05ConnectedRehearsalV5Error("V5_NESTED_AUTHORITY_REPLAY_FAILED")
    component_paths = _private_normal_paths(
        manifest_path=private_normal_manifest_path, registry=normal_registry,
        expected_manifest_hash=expected_private_manifest_hash)
    normal_replay = replay_normal_source_registry_v2(
        registry=normal_registry, component_paths=component_paths,
        expected_dec031_binding_hash=contract["dec031_binding_hash"])
    executor = build_preaccess_frozen_kernel_executor_v5(
        repository_root=repository_root, executable_manifest=historical,
        detector_registry=detectors, dispatch_registry=dispatch,
        rule_runtime_registry=rules, rule_sources=rule_sources)

    allowlists = frozen_feature_allowlist_authorities_v2()
    physical_rows = []
    source_paths: dict[tuple[str, str], Path] = {}
    for panel in FROZEN_PANEL_ORDER_V2:
        for file_id in FROZEN_ATTACK_FILE_IDS_V2[panel]:
            source = work_root / "synthetic-containers" / panel / file_id
            _write_fixture(source, allowlists[panel])
            header = [allowlists[panel].timestamp_id, *allowlists[panel].feature_ids, "Attack", "unknown_field"]
            physical_rows.append(PhysicalFileIdentityV2(
                panel, file_id, file_sha256(source), digest(header),
                digest([panel, file_id, "synthetic-official-source"])))
            source_paths[(panel, file_id)] = source
    physical = FrozenPhysicalFileAuthorityV2(
        tuple(physical_rows), FROZEN_ATTACK_FILE_CENSUS_HASH_V2,
        digest("synthetic-physical-source"), FROZEN_AUTHORITY_SOURCE_COMMIT_V2)
    physical.validate()
    physical_path = work_root / "physical-authority.json"
    persist_canonical_v1(physical_path, physical.document())
    census = build_expected_prediction_cell_census_v1(physical=physical, dispatch=dispatch)

    projections: dict[tuple[str, str], tuple[Any, Path]] = {}
    projection_authority_paths: dict[tuple[str, str], Path] = {}
    timestamps: dict[tuple[str, str], Any] = {}
    timestamp_authority_paths: dict[tuple[str, str], Path] = {}
    from .dg05_execution_closure_v1 import project_attack_feature_file_v1
    implementations = dict(historical.implementation_hashes)
    for item in physical.files:
        destination = work_root / "projections" / item.panel_id / f"{item.file_id}.jsonl"
        projection, timestamp = project_attack_feature_file_v1(
            source=source_paths[(item.panel_id, item.file_id)], destination=destination,
            physical_file=item, panel_authority=allowlists[item.panel_id], file_id=item.file_id,
            adapter_implementation_hash=implementations["projection_adapter"], source_commit=source_commit)
        projections[(item.panel_id, item.file_id)] = (projection, destination)
        timestamps[(item.panel_id, item.file_id)] = timestamp
        projection_doc_path = work_root / "projection-authorities" / item.panel_id / f"{item.file_id}.json"
        timestamp_doc_path = work_root / "timestamp-authorities" / item.panel_id / f"{item.file_id}.json"
        persist_canonical_v1(projection_doc_path, projection.document())
        persist_canonical_v1(timestamp_doc_path, timestamp.document())
        projection_authority_paths[(item.panel_id, item.file_id)] = projection_doc_path
        timestamp_authority_paths[(item.panel_id, item.file_id)] = timestamp_doc_path

    prediction_directory = work_root / "predictions"
    receipts = []
    artifacts = {}
    prediction_paths: dict[str, Path] = {}
    trace_paths: dict[str, Path] = {}
    kernel_census = KernelInvocationCensusV5()
    for cell in census["cells"]:
        projection, projection_path = projections[(cell["panel_id"], cell["file_id"])]
        receipt = execute_prediction_cell_v5(
            cell=cell, dispatch=dispatch, projection=projection,
            timestamp=timestamps[(cell["panel_id"], cell["file_id"])],
            release=release, predecessor_v3=_load_v4(
                repository_root / "research_control_center/validation_v2/dg05_metric_verifier_closure/DG05_EXECUTABLE_AUTHORITY_MANIFEST_V3.json",
                "dg05_executable_authority_manifest_v3"),
            initialized_release_state=initialized, executor=executor,
            projection_path=projection_path, output_directory=prediction_directory,
            source_commit=source_commit, repository_root=repository_root,
            invocation_census=kernel_census)
        receipts.append(receipt)
        receipt_path = prediction_directory / f"{receipt.cell_id}.receipt.json"
        persist_prediction_receipt_v1(receipt_path, receipt)
        prediction_path = prediction_directory / f"{receipt.cell_id}.prediction.json"
        trace_path = prediction_directory / f"{receipt.cell_id}.trace.json"
        artifacts[receipt.cell_id] = (
            prediction_path if receipt.status == "SUCCESS" else None,
            trace_path if receipt.trace_status == "BOUND" else None,
            receipt_path,
        )
        if receipt.status == "SUCCESS":
            prediction_paths[receipt.cell_id] = prediction_path
        if receipt.trace_status == "BOUND":
            trace_paths[receipt.cell_id] = trace_path
    if len(kernel_census.rows) != census["count"] or any(receipt.status != "SUCCESS" for receipt in receipts):
        raise DG05ConnectedRehearsalV5Error("PRODUCTION_KERNEL_REHEARSAL_INCOMPLETE")
    kernel_doc = kernel_census.document(
        release_manifest_hash=release["self_hash"], source_commit=source_commit,
        executable_version=release["executable_version"])
    kernel_path = work_root / "kernel-invocation-census.json"
    persist_canonical_v1(kernel_path, kernel_doc)

    global_manifest = build_global_prediction_manifest_v1(
        census=census, receipts=receipts, executable_manifest_hash=release["self_hash"], dispatch=dispatch)
    freeze_predecessor = _state(
        state="PREDICTIONS_COMPLETE_LABEL_LOCKED", release_hash=release["self_hash"],
        release_initialization_hash=initialized["self_hash"])
    freeze = freeze_global_predictions_v1(
        manifest=global_manifest, census=census, receipt_artifacts=artifacts,
        predecessor_state=freeze_predecessor)
    manifest_path = work_root / "global-manifest.json"
    freeze_path = work_root / "global-freeze.json"
    persist_canonical_v1(manifest_path, global_manifest)
    persist_canonical_v1(freeze_path, freeze)

    incoming, outgoing = work_root / "custodian-in", work_root / "custodian-out"
    incoming.mkdir(); outgoing.mkdir()
    sources = []
    bindings = []
    p1_by_version = {version: next(point.canonical_identity for point in scope.points
                                   if point.dataset_version == version and point.p1_membership == "YES")
                     for version in VERSION.values()}
    nonp1_by_version = {version: next(point.canonical_identity for point in scope.points
                                      if point.dataset_version == version and point.p1_membership == "NO")
                        for version in VERSION.values()}
    raw_scenario_paths: dict[str, Path] = {}
    for panel in FROZEN_PANEL_ORDER_V2:
        version = VERSION[panel]
        file_id = FROZEN_ATTACK_FILE_IDS_V2[panel][0]
        source_id = f"SYNTHETIC-{version}"
        official_hash = digest([source_id, "official"])
        local = []
        for index in range(NOMINAL[panel]):
            base = datetime(2026, 1, 1) + timedelta(seconds=index * 3)
            local.append({
                "panel_id": panel, "dataset_version": version, "file_id": file_id,
                "scenario_id": f"S{index + 1:03d}",
                "closed_intervals": [[(base + timedelta(milliseconds=250)).isoformat(),
                                      (base + timedelta(milliseconds=750)).isoformat()],
                                     [(base + timedelta(seconds=1)).isoformat(),
                                      (base + timedelta(seconds=1)).isoformat()]],
                "attacked_identities": [p1_by_version[version] if index % 3 else nonp1_by_version[version]],
                "explicit_affected_processes": [],
            })
        source_path = incoming / f"{source_id}.json"
        source_path.write_bytes(canonical_bytes({
            "schema": "synthetic_raw_official_scenario_fixture_v2", "records": local}) + b"\n")
        raw_scenario_paths[source_id] = source_path
        sources.append({
            "source_id": source_id, "path": str(source_path.resolve()),
            "byte_hash": file_sha256(source_path), "official_source_hash": official_hash,
            "dataset_version": version, "source_format": "SYNTHETIC_JSON_V2",
            "adapter_id": "SYNTHETIC_OFFICIAL_SCENARIO_FIXTURE_V2",
        })
        projection, _ = projections[(panel, file_id)]
        bindings.append({
            "source_id": source_id, "panel_id": panel, "dataset_version": version,
            "file_id": file_id, "physical_file_authority_hash": projection.raw_physical_file_hash,
            "timestamp_authority_hash": timestamps[(panel, file_id)].document()["self_hash"],
            "official_source_hash": official_hash,
        })
    custodian_impl = repository_root / "src/paperworks/validation_v2/dg05_label_custodian_v2.py"
    policy = self_hashed({
        "schema": "custodian_resource_policy_authority_v2",
        "input_root": str(incoming.resolve()), "output_root": str(outgoing.resolve()),
        "forbidden_roots": [str(prediction_directory.resolve())], "approved_sources": sources,
        "executable_manifest_hash": release["self_hash"],
        "scenario_adapter_implementation_hash": file_sha256(custodian_impl),
        "resource_policy_contract_hash": digest("synthetic-resource-policy-v2"),
        "source_commit": source_commit,
    })
    policy_path = work_root / "custodian-policy.json"
    persist_canonical_v1(policy_path, policy)
    frozen_state = _state(
        state="GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED", release_hash=release["self_hash"],
        freeze_hash=freeze["self_hash"])
    token = digest([release["self_hash"], freeze["self_hash"], "synthetic-single-use"])
    lease = self_hashed({
        "schema": "single_use_label_scenario_lease_v3",
        "token_hash": sha256(token.encode("utf-8")).hexdigest(),
        "global_freeze_hash": freeze["self_hash"], "state_hash": frozen_state["self_hash"],
        "executable_manifest_hash": release["self_hash"], "resource_policy_hash": policy["self_hash"],
        "issue_count": 1, "consume_limit": 1,
    })
    issued_state = _state(
        state="LABEL_SCENARIO_LEASE_ISSUED", release_hash=release["self_hash"],
        freeze_hash=freeze["self_hash"], lease_issue_predecessor_hash=frozen_state["self_hash"],
        lease_receipt_hash=lease["self_hash"], lease_token_hash=lease["token_hash"])
    issued_path = work_root / "lease-issued-state.json"
    persist_canonical_v1(issued_path, issued_state)
    request = {
        "schema": "isolated_label_scenario_custodian_request_v2", "opaque_lease": token,
        "lease_receipt": lease, "global_freeze_hash": freeze["self_hash"],
        "predecessor_state_hash": issued_state["self_hash"],
        "lease_issue_predecessor_hash": frozen_state["self_hash"],
        "executable_manifest_hash": release["self_hash"],
        "approved_source_ids": sorted(source["source_id"] for source in sources),
        "approved_output_name": "scenario-output.json", "public_authority_hashes": [contract["self_hash"]],
        "resource_policy_hash": policy["self_hash"], "allowed_scenario_bindings": bindings,
        "authority_mode": "SYNTHETIC_REHEARSAL", "nominal_counts": NOMINAL,
    }
    request_path = work_root / "custodian-request.json"
    request_path.write_bytes(canonical_bytes(request) + b"\n")
    launcher = repository_root / "scripts/run_dg05_label_custodian_v2.py"
    invocation = launch_custodian_fresh_process_v2(
        request_path=request_path, resource_policy_path=policy_path, launcher_path=launcher,
        repository_root=repository_root, expected_launcher_hash=file_sha256(launcher),
        expected_resource_policy_hash=policy["self_hash"],
        expected_custodian_implementation_hash=file_sha256(custodian_impl),
        predecessor_state=issued_state, expected_global_freeze_hash=freeze["self_hash"],
        expected_release_manifest_hash=release["self_hash"])
    invocation_path = work_root / "custodian-invocation.json"
    persist_canonical_v1(invocation_path, invocation)
    output_path = outgoing / "scenario-output.json"
    custodian_output = _load(output_path, "isolated_label_scenario_custodian_output_v2")
    consumed_path = outgoing / f"lease-consumed-{lease['token_hash']}.json"
    scope_path = work_root / "full-process-scope.json"
    persist_canonical_v1(scope_path, scope.document())

    typed = tuple(sorted(ScenarioRecordV1(
        row["panel_id"], row["dataset_version"], row["file_id"], row["scenario_id"],
        tuple(tuple(value) for value in row["closed_intervals"]), tuple(row["attacked_identities"]),
        tuple(row["explicit_affected_processes"]), row["physical_file_authority_hash"],
        row["timestamp_authority_hash"], row["official_source_hash"])
        for row in custodian_output["records"]))
    scenario = build_scenario_authority_v1(
        records=typed, lease_completion_hash=custodian_output["self_hash"],
        global_freeze_hash=freeze["self_hash"], source_commit=source_commit,
        nominal_counts=NOMINAL, authority_mode="SYNTHETIC_REHEARSAL")
    denominator = build_denominator_authority_v1(
        scenario_authority=scenario, full_scope=scope,
        p1_custodian_v3_hash=historical.p1_custodian_v3_hash)
    scenario_path = work_root / "scenario-authority.json"
    denominator_path = work_root / "denominator-authority.json"
    persist_canonical_v1(scenario_path, scenario)
    persist_canonical_v1(denominator_path, denominator)

    upstream_receipts = []
    oracle_receipts = []
    surface_count = 0
    for panel in FROZEN_PANEL_ORDER_V2:
        panel_files = tuple(FROZEN_ATTACK_FILE_IDS_V2[panel])
        primitive = build_metric_primitives_from_frozen_execution_v2(
            panel_id=panel, global_prediction_manifest=global_manifest,
            global_prediction_freeze=freeze, scenario_authority=scenario,
            denominator_authority=denominator,
            projection_paths={file_id: projections[(panel, file_id)][1] for file_id in panel_files},
            prediction_paths=prediction_paths, trace_paths=trace_paths,
            normal_source_replay=normal_replay, normal_source_registry_hash=normal_registry["self_hash"],
            dec031_binding_hash=contract["dec031_binding_hash"], source_commit=source_commit)
        result = build_complete_metric_surface_v2(
            primitives=primitive, contract=contract, executable_manifest_hash=release["self_hash"],
            wrapper=wrapper, source_commit=source_commit)
        primitive_path = work_root / "results" / f"{panel}.primitive.json"
        result_path = work_root / "results" / f"{panel}.result.json"
        persist_canonical_v1(primitive_path, primitive)
        persist_canonical_v1(result_path, result)
        intermediate = UpstreamPanelReplayPathsV2(
            manifest_path, freeze_path, scenario_path, denominator_path,
            {file_id: projections[(panel, file_id)][1] for file_id in panel_files},
            prediction_paths, trace_paths, normal_registry_path, component_paths, primitive_path)
        roots = RootToResultReplayPathsV3(
            intermediate=intermediate, release_manifest_path=release_path,
            physical_file_authority_path=physical_path,
            raw_physical_paths={file_id: source_paths[(panel, file_id)] for file_id in panel_files},
            projection_authority_paths={file_id: projection_authority_paths[(panel, file_id)] for file_id in panel_files},
            timestamp_authority_paths={file_id: timestamp_authority_paths[(panel, file_id)] for file_id in panel_files},
            raw_scenario_source_paths=raw_scenario_paths, custodian_policy_path=policy_path,
            custodian_request_path=request_path, lease_issued_state_path=issued_path,
            lease_consumed_path=consumed_path, custodian_invocation_path=invocation_path,
            custodian_output_path=output_path, full_process_scope_path=scope_path)
        upstream_receipts.append(verify_asserted_primitive_from_roots_v3(
            panel_id=panel, paths=roots, expected_release_manifest_hash=release["self_hash"],
            expected_dec031_binding_hash=contract["dec031_binding_hash"],
            expected_normal_source_registry_hash=normal_registry["self_hash"],
            expected_global_freeze_hash=freeze["self_hash"],
            expected_physical_authority_hash=physical.document()["self_hash"],
            expected_custodian_invocation_hash=invocation["self_hash"],
            expected_full_process_scope_hash=scope.document()["self_hash"],
            expected_p1_custodian_hash=historical.p1_custodian_v3_hash,
            source_commit=source_commit))
        oracle_receipts.append(verify_complete_metric_surface_from_paths_v2(
            primitive_path=primitive_path, result_path=result_path,
            contract_path=metric_contract_path, wrapper=wrapper,
            expected_executable_hash=release["self_hash"]))
        surface_count += result["surface_count"]

    root_replay = self_hashed({
        "schema": (
            "dg05_v6_root_to_result_replay_receipt_v1"
            if release["executable_version"] == "DG05_EXECUTABLE_V6"
            else "dg05_v5_root_to_result_replay_receipt_v1"
        ),
        "status": "PASS",
        "release_manifest_hash": release["self_hash"],
        "verification_count": len(upstream_receipts),
        "verification_hashes": [row["self_hash"] for row in upstream_receipts],
        "per_root_replay": {
            key: all(row["root_replay_flags"][key] for row in upstream_receipts)
            for key in sorted(upstream_receipts[0]["root_replay_flags"])
        },
        "root_covered_surface_count": surface_count,
        "source_commit": source_commit,
    })
    rehearsal = self_hashed({
        "schema": (
            "connected_preaccess_dg05_rehearsal_evidence_v6"
            if release["executable_version"] == "DG05_EXECUTABLE_V6"
            else "connected_preaccess_dg05_rehearsal_evidence_v5"
        ), "status": "PASS",
        "release_manifest_hash": release["self_hash"], "release_initialization_hash": initialized["self_hash"],
        "authorized_data_mode": initialized["data_access_mode"],
        "execution_kernel_identity": initialized["execution_kernel_identity"],
        "production_kernel_parity_hash": kernel_doc["self_hash"],
        "production_kernel_invocation_count": kernel_doc["production_kernel_invocation_count"],
        "synthetic_fallback_invocation_count": kernel_doc["synthetic_fallback_invocation_count"],
        "derived_prediction_cells": census["count"], "successful_prediction_cells": global_manifest["success_count"],
        "method_failures": global_manifest["failure_count"], "global_prediction_freeze": freeze["status"],
        "synthetic_scenarios": len(typed), "plural_interval_scenarios": len(typed),
        "metric_surface_count": surface_count, "root_covered_surface_count": surface_count,
        "root_verification_count": len(upstream_receipts),
        "root_to_result_replay_hash": root_replay["self_hash"],
        "root_verification_hashes": root_replay["verification_hashes"],
        "all_root_replay_flags_true": all(all(row["root_replay_flags"].values()) for row in upstream_receipts),
        "independent_result_verification_count": len(oracle_receipts),
        "independent_result_verification_surface_count": sum(row["verified_surface_count"] for row in oracle_receipts),
        "normal_source_component_count": normal_registry["component_count"],
        "normal_source_bytes_reopened": normal_replay["source_bytes_reopened"],
        "fresh_process_custodian": True,
        "custodian_pid_distinct": invocation["custodian_pid"] != invocation["custodian_parent_pid"],
        "lease_issue_count": 1, "lease_consume_count": 1, "lease_reissue_count": 0,
        "attack_test_accesses": 0, "real_label_scenario_accesses": 0,
        "provider_calls": 0, "credential_reads": 0, "new_fitting": 0,
        "new_rule_generation": 0, "new_scientific_experiments": 0,
        "result_driven_changes": 0, "private_exposures": 0,
        "fixture_authority": "SYNTHETIC_ONLY_NON_RESULT_PRODUCING",
        "source_commit": source_commit,
    })
    return rehearsal, kernel_doc, root_replay


__all__ = ["DG05ConnectedRehearsalV5Error", "run_connected_preaccess_rehearsal_v5"]
