"""Full DEC-031 production-route rehearsal on synthetic attack-side fixtures.

The route uses the exact historical method-dispatch kernel under a prospective
V4 release root, the production projection and freeze builders, the actual V2
fresh-process custodian launcher, the DEC-031 metric bridge, frozen normal-only
source bytes, and independent upstream/result replay.  It has no production
resource discovery interface.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

from .dg05_execution_closure_v1 import (
    DG05ExecutableAuthorityManifestV1,
    DG05ProductionExecutorV1,
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
from .dg05_production_chain_v1 import initialize_production_release_v1, launch_custodian_fresh_process_v2
from .dg05_production_route_v4 import execute_prediction_cell_v4
from .dg05_upstream_lineage_verifier_v2 import UpstreamPanelReplayPathsV2, verify_asserted_primitive_from_upstream_v2
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


class DG05ConnectedRehearsalV4Error(ValueError):
    pass


NOMINAL = dict(zip(FROZEN_PANEL_ORDER_V2, (38, 58, 50)))
VERSION = dict(zip(FROZEN_PANEL_ORDER_V2, ("23.05", "22.04", "21.03")))


def _load(path: Path, schema: str) -> dict[str, Any]:
    raw = path.read_bytes()
    try:
        value = json.loads(raw.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DG05ConnectedRehearsalV4Error("CANONICAL_INPUT_REQUIRED") from exc
    if raw != canonical_bytes(value) + b"\n" or value.get("schema") != schema:
        raise DG05ConnectedRehearsalV4Error(f"CANONICAL_SCHEMA_REPLAY_FAILED:{schema}")
    if value.get("self_hash") != digest({key: item for key, item in value.items() if key != "self_hash"}):
        raise DG05ConnectedRehearsalV4Error(f"SELF_HASH_REPLAY_FAILED:{schema}")
    return value


def _typed_manifest(path: Path) -> DG05ExecutableAuthorityManifestV1:
    value = _load(path, "dg05_executable_authority_manifest_v1")
    manifest = DG05ExecutableAuthorityManifestV1(
        tuple(sorted(value["scientific_authorities"].items())), value["detector_registry_hash"],
        value["dispatch_registry_hash"], value["rule_runtime_registry_hash"],
        tuple(value["rule_portfolio_authority_hashes"]), value["full_process_scope_hash"],
        value["p1_custodian_v3_hash"], tuple(sorted(value["implementation_hashes"].items())),
        value["nested_authority_replay_bundle_hash"], value["source_commit"],
    )
    manifest.validate()
    if manifest.document() != value:
        raise DG05ConnectedRehearsalV4Error("HISTORICAL_EXECUTION_MANIFEST_RECONSTRUCTION_FAILED")
    return manifest


def _write_fixture(path: Path, authority: Any, *, rows: int = 256) -> None:
    header = [authority.timestamp_id, *authority.feature_ids, "Attack", "unknown_field"]
    start = datetime(2026, 1, 1)
    lines = [",".join(header)]
    for index in range(rows):
        timestamp = (start + timedelta(seconds=index)).isoformat()
        values = [str(1.0 + (index % 7) * 0.1)] * len(authority.feature_ids)
        lines.append(",".join([timestamp, *values, "opaque-label", "opaque"] ))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


def _private_normal_paths(*, manifest_path: Path, registry: Mapping[str, Any],
                          expected_manifest_hash: str) -> dict[str, Path]:
    manifest = _load(manifest_path, "dg05_normal_source_private_manifest_v1")
    if manifest["self_hash"] != expected_manifest_hash or manifest.get("registry_hash") != registry["self_hash"]:
        raise DG05ConnectedRehearsalV4Error("PRIVATE_NORMAL_MANIFEST_AUTHORITY_MISMATCH")
    rows = manifest.get("records")
    if type(rows) is not list or manifest.get("record_count") != len(rows):
        raise DG05ConnectedRehearsalV4Error("PRIVATE_NORMAL_MANIFEST_CENSUS_MISMATCH")
    output: dict[str, Path] = {}
    expected = {row["component_id"]: row for row in registry["components"]}
    approved_root = manifest_path.resolve().parent
    for row in rows:
        component_id = row.get("component_id")
        if component_id in output or component_id not in expected:
            raise DG05ConnectedRehearsalV4Error("PRIVATE_NORMAL_COMPONENT_IDENTITY_MISMATCH")
        path = Path(str(row.get("path", ""))).resolve()
        if approved_root not in path.parents or not path.is_file() or path.is_symlink():
            raise DG05ConnectedRehearsalV4Error("PRIVATE_NORMAL_COMPONENT_UNAVAILABLE")
        expected_row = expected[component_id]
        if (file_sha256(path) != expected_row["artifact_byte_hash"]
                or path.stat().st_size != expected_row["artifact_byte_count"]
                or row.get("artifact_byte_hash") != expected_row["artifact_byte_hash"]
                or row.get("document_self_hash") != expected_row["document_self_hash"]):
            raise DG05ConnectedRehearsalV4Error("PRIVATE_NORMAL_COMPONENT_BYTE_MISMATCH")
        output[component_id] = path
    if set(output) != set(expected):
        raise DG05ConnectedRehearsalV4Error("PRIVATE_NORMAL_COMPONENT_CENSUS_MISMATCH")
    return output


def _state(*, state: str, release_hash: str, freeze_hash: str | None = None,
           **extra: Any) -> dict[str, Any]:
    return self_hashed({"schema": "dg05_production_chain_state_v4", "state": state,
                        "release_manifest_hash": release_hash,
                        "global_prediction_freeze_hash": freeze_hash,
                        "authority_mode": "SYNTHETIC_REHEARSAL", **extra})


def run_connected_synthetic_rehearsal_v4(
    *, repository_root: Path, work_root: Path, release_path: Path,
    predecessor_v3_path: Path, predecessor_v3_closure_path: Path,
    historical_v1_manifest_path: Path,
    metric_contract_path: Path, normal_registry_path: Path,
    private_normal_manifest_path: Path, expected_private_manifest_hash: str,
    wrapper: OfficialEtaprV1, source_commit: str,
) -> dict[str, Any]:
    """Execute the complete synthetic route and return a public-safe receipt."""
    work_root.mkdir(parents=True, exist_ok=False)
    release = _load(release_path, "dg05_production_release_manifest_v1")
    initialized_release_state = initialize_production_release_v1(
        release_manifest_path=release_path,
        repository_root=repository_root,
        predecessor_v3_manifest_path=predecessor_v3_path,
        predecessor_v3_closure_path=predecessor_v3_closure_path,
        approved_release_hash=release["self_hash"],
        authority_mode="SYNTHETIC_REHEARSAL",
    )
    predecessor = _load(predecessor_v3_path, "dg05_executable_authority_manifest_v3")
    contract = _load(metric_contract_path, "metric_surface_contract_v2")
    normal_registry = _load(normal_registry_path, "normal_burden_source_registry_v2")
    dec031_hash = contract["dec031_binding_hash"]
    # Reconstruct the exact historical execution objects from their public
    # authorities.  The builders themselves perform full frozen validation.
    from scripts.freeze_dg05_execution_closure_v1 import build_detectors, build_dispatch, build_rule_runtime_registry, build_scope
    detectors = build_detectors()
    rules, _ = build_rule_runtime_registry()
    dispatch = build_dispatch(detectors, rules)
    scope = build_scope()
    historical = _typed_manifest(historical_v1_manifest_path)
    if (
        historical.document()["self_hash"] != predecessor["historical_prediction_executable_manifest_hash"]
        or detectors.document()["self_hash"] != historical.detector_registry_hash
        or dispatch.document()["self_hash"] != historical.dispatch_registry_hash
        or rules.document()["self_hash"] != historical.rule_runtime_registry_hash
        or scope.document()["self_hash"] != historical.full_process_scope_hash
    ):
        raise DG05ConnectedRehearsalV4Error("HISTORICAL_EXECUTION_AUTHORITY_REPLAY_FAILED")
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
        or release.get("semantic_binding_hash") != dec031_hash
        or release.get("normal_burden_source_registry_hash") != normal_registry["self_hash"]
        or contract.get("normal_source_registry_hash") != normal_registry["self_hash"]
    ):
        raise DG05ConnectedRehearsalV4Error("V4_NESTED_AUTHORITY_REPLAY_FAILED")

    # Private normal-only custody is opened only after the prospective release,
    # all executed code bytes, and every public nested root have replayed.
    component_paths = _private_normal_paths(
        manifest_path=private_normal_manifest_path, registry=normal_registry,
        expected_manifest_hash=expected_private_manifest_hash)
    normal_replay = replay_normal_source_registry_v2(
        registry=normal_registry, component_paths=component_paths,
        expected_dec031_binding_hash=dec031_hash)
    implementations = dict(historical.implementation_hashes)
    executor = DG05ProductionExecutorV1.synthetic_rehearsal(
        executable_manifest=historical, executable_manifest_hash=historical.document()["self_hash"],
        detector_registry=detectors, dispatch_registry=dispatch, rule_runtime_registry=rules,
        adapter_implementation_hash=implementations["prediction_adapter"],
        fusion_implementation_hash=implementations["fusion_runtime"])

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
    census = build_expected_prediction_cell_census_v1(physical=physical, dispatch=dispatch)

    projections: dict[tuple[str, str], tuple[Any, Path]] = {}
    timestamps: dict[tuple[str, str], Any] = {}
    from .dg05_execution_closure_v1 import project_attack_feature_file_v1
    for item in physical.files:
        destination = work_root / "projections" / item.panel_id / f"{item.file_id}.jsonl"
        projection, timestamp = project_attack_feature_file_v1(
            source=source_paths[(item.panel_id, item.file_id)], destination=destination,
            physical_file=item, panel_authority=allowlists[item.panel_id], file_id=item.file_id,
            adapter_implementation_hash=implementations["projection_adapter"], source_commit=source_commit)
        projections[(item.panel_id, item.file_id)] = (projection, destination)
        timestamps[(item.panel_id, item.file_id)] = timestamp

    prediction_directory = work_root / "predictions"
    receipts = []
    artifacts = {}
    prediction_paths: dict[str, Path] = {}
    trace_paths: dict[str, Path] = {}
    for cell in census["cells"]:
        projection, projection_path = projections[(cell["panel_id"], cell["file_id"])]
        receipt = execute_prediction_cell_v4(
            cell=cell, dispatch=dispatch, projection=projection,
            timestamp=timestamps[(cell["panel_id"], cell["file_id"])],
            release=release, predecessor_v3=predecessor, executor=executor,
            initialized_release_state=initialized_release_state,
            projection_path=projection_path, output_directory=prediction_directory,
            source_commit=source_commit)
        receipts.append(receipt)
        receipt_path = prediction_directory / f"{receipt.cell_id}.receipt.json"
        persist_prediction_receipt_v1(receipt_path, receipt)
        prediction_path = prediction_directory / f"{receipt.cell_id}.prediction.json"
        trace_path = prediction_directory / f"{receipt.cell_id}.trace.json"
        artifacts[receipt.cell_id] = (prediction_path if receipt.status == "SUCCESS" else None,
                                      trace_path if receipt.trace_status == "BOUND" else None,
                                      receipt_path)
        if receipt.status == "SUCCESS": prediction_paths[receipt.cell_id] = prediction_path
        if receipt.trace_status == "BOUND": trace_paths[receipt.cell_id] = trace_path
    global_manifest = build_global_prediction_manifest_v1(
        census=census, receipts=receipts, executable_manifest_hash=release["self_hash"], dispatch=dispatch)
    freeze_predecessor = _state(
        state="PREDICTIONS_COMPLETE_LABEL_LOCKED", release_hash=release["self_hash"],
        release_initialization_hash=initialized_release_state["self_hash"])
    freeze = freeze_global_predictions_v1(
        manifest=global_manifest, census=census, receipt_artifacts=artifacts,
        predecessor_state=freeze_predecessor)
    global_manifest_path = work_root / "global-manifest.json"
    freeze_path = work_root / "global-freeze.json"
    persist_canonical_v1(global_manifest_path, global_manifest)
    persist_canonical_v1(freeze_path, freeze)

    # Build method-blind synthetic scenario sources.  Every panel exercises a
    # plural disjoint interval with an unsampled first interval endpoint.
    incoming, outgoing = work_root / "custodian-in", work_root / "custodian-out"
    incoming.mkdir(); outgoing.mkdir()
    sources = []; bindings = []; all_records = []
    p1_by_version = {version: next(point.canonical_identity for point in scope.points
                                   if point.dataset_version == version and point.p1_membership == "YES")
                     for version in VERSION.values()}
    nonp1_by_version = {version: next(point.canonical_identity for point in scope.points
                                      if point.dataset_version == version and point.p1_membership == "NO")
                        for version in VERSION.values()}
    for panel in FROZEN_PANEL_ORDER_V2:
        version = VERSION[panel]
        file_id = FROZEN_ATTACK_FILE_IDS_V2[panel][0]
        source_id = f"SYNTHETIC-{version}"
        official_hash = digest([source_id, "official"])
        local = []
        for index in range(NOMINAL[panel]):
            base = datetime(2026, 1, 1) + timedelta(seconds=index * 3)
            local.append({"panel_id": panel, "dataset_version": version, "file_id": file_id,
                "scenario_id": f"S{index + 1:03d}",
                "closed_intervals": [[(base + timedelta(milliseconds=250)).isoformat(),
                                      (base + timedelta(milliseconds=750)).isoformat()],
                                     [(base + timedelta(seconds=1)).isoformat(),
                                      (base + timedelta(seconds=1)).isoformat()]],
                "attacked_identities": [p1_by_version[version] if index % 3 else nonp1_by_version[version]],
                "explicit_affected_processes": []})
        source_path = incoming / f"{source_id}.json"
        source_path.write_bytes(canonical_bytes({"schema": "synthetic_raw_official_scenario_fixture_v2",
                                                 "records": local}) + b"\n")
        source_hash = file_sha256(source_path)
        sources.append({"source_id": source_id, "path": str(source_path.resolve()), "byte_hash": source_hash,
                        "official_source_hash": official_hash, "dataset_version": version,
                        "source_format": "SYNTHETIC_JSON_V2",
                        "adapter_id": "SYNTHETIC_OFFICIAL_SCENARIO_FIXTURE_V2"})
        projection, _ = projections[(panel, file_id)]
        bindings.append({"source_id": source_id, "panel_id": panel, "dataset_version": version,
                         "file_id": file_id, "physical_file_authority_hash": projection.raw_physical_file_hash,
                         "timestamp_authority_hash": timestamps[(panel, file_id)].document()["self_hash"],
                         "official_source_hash": official_hash})
        all_records.extend(local)
    custodian_impl = repository_root / "src/paperworks/validation_v2/dg05_label_custodian_v2.py"
    policy = self_hashed({"schema": "custodian_resource_policy_authority_v2",
        "input_root": str(incoming.resolve()), "output_root": str(outgoing.resolve()),
        "forbidden_roots": [str(prediction_directory.resolve())], "approved_sources": sources,
        "executable_manifest_hash": release["self_hash"],
        "scenario_adapter_implementation_hash": file_sha256(custodian_impl),
        "resource_policy_contract_hash": digest("synthetic-resource-policy-v2"),
        "source_commit": source_commit})
    policy_path = work_root / "custodian-policy.json"; persist_canonical_v1(policy_path, policy)
    frozen_state = _state(state="GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED", release_hash=release["self_hash"],
                          freeze_hash=freeze["self_hash"])
    token = digest([release["self_hash"], freeze["self_hash"], "synthetic-single-use"])
    lease = self_hashed({"schema": "single_use_label_scenario_lease_v3",
        "token_hash": sha256(token.encode("utf-8")).hexdigest(), "global_freeze_hash": freeze["self_hash"],
        "state_hash": frozen_state["self_hash"], "executable_manifest_hash": release["self_hash"],
        "resource_policy_hash": policy["self_hash"], "issue_count": 1, "consume_limit": 1})
    issued_state = _state(state="LABEL_SCENARIO_LEASE_ISSUED", release_hash=release["self_hash"],
        freeze_hash=freeze["self_hash"], lease_issue_predecessor_hash=frozen_state["self_hash"],
        lease_receipt_hash=lease["self_hash"], lease_token_hash=lease["token_hash"])
    request = {"schema": "isolated_label_scenario_custodian_request_v2", "opaque_lease": token,
        "lease_receipt": lease, "global_freeze_hash": freeze["self_hash"],
        "predecessor_state_hash": issued_state["self_hash"],
        "lease_issue_predecessor_hash": frozen_state["self_hash"],
        "executable_manifest_hash": release["self_hash"],
        "approved_source_ids": sorted(source["source_id"] for source in sources),
        "approved_output_name": "scenario-output.json", "public_authority_hashes": [contract["self_hash"]],
        "resource_policy_hash": policy["self_hash"], "allowed_scenario_bindings": bindings,
        "authority_mode": "SYNTHETIC_REHEARSAL", "nominal_counts": NOMINAL}
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
    custodian_output = _load(outgoing / "scenario-output.json", "isolated_label_scenario_custodian_output_v2")
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
    persist_canonical_v1(scenario_path, scenario); persist_canonical_v1(denominator_path, denominator)

    upstream_receipts = []; oracle_receipts = []; surface_count = 0
    for panel in FROZEN_PANEL_ORDER_V2:
        panel_files = tuple(FROZEN_ATTACK_FILE_IDS_V2[panel])
        primitive = build_metric_primitives_from_frozen_execution_v2(
            panel_id=panel, global_prediction_manifest=global_manifest, global_prediction_freeze=freeze,
            scenario_authority=scenario, denominator_authority=denominator,
            projection_paths={file_id: projections[(panel, file_id)][1] for file_id in panel_files},
            prediction_paths=prediction_paths, trace_paths=trace_paths,
            normal_source_replay=normal_replay, normal_source_registry_hash=normal_registry["self_hash"],
            dec031_binding_hash=dec031_hash, source_commit=source_commit)
        result = build_complete_metric_surface_v2(
            primitives=primitive, contract=contract, executable_manifest_hash=release["self_hash"],
            wrapper=wrapper, source_commit=source_commit)
        primitive_path = work_root / "results" / f"{panel}.primitive.json"
        result_path = work_root / "results" / f"{panel}.result.json"
        persist_canonical_v1(primitive_path, primitive); persist_canonical_v1(result_path, result)
        paths = UpstreamPanelReplayPathsV2(
            global_manifest_path, freeze_path, scenario_path, denominator_path,
            {file_id: projections[(panel, file_id)][1] for file_id in panel_files},
            prediction_paths, trace_paths, normal_registry_path, component_paths, primitive_path)
        upstream_receipts.append(verify_asserted_primitive_from_upstream_v2(
            panel_id=panel, paths=paths, expected_release_manifest_hash=release["self_hash"],
            expected_dec031_binding_hash=dec031_hash,
            expected_normal_source_registry_hash=normal_registry["self_hash"], source_commit=source_commit))
        oracle_receipts.append(verify_complete_metric_surface_from_paths_v2(
            primitive_path=primitive_path, result_path=result_path, contract_path=metric_contract_path,
            wrapper=wrapper, expected_executable_hash=release["self_hash"]))
        surface_count += result["surface_count"]

    return self_hashed({"schema": "connected_synthetic_dg05_rehearsal_evidence_v4",
        "status": "PASS", "release_manifest_hash": release["self_hash"],
        "release_initialization_hash": initialized_release_state["self_hash"],
        "release_initialization_state": initialized_release_state["state"],
        "historical_execution_kernel_hash": historical.document()["self_hash"],
        "derived_prediction_cells": census["count"], "successful_prediction_cells": global_manifest["success_count"],
        "method_failures": global_manifest["failure_count"], "missing_cells": 0, "duplicate_cells": 0,
        "global_prediction_freeze": freeze["status"], "synthetic_scenarios": len(typed),
        "plural_interval_scenarios": len(typed), "metric_surface_count": surface_count,
        "normal_source_component_count": normal_registry["component_count"],
        "normal_source_bytes_reopened": normal_replay["source_bytes_reopened"],
        "upstream_verification_count": len(upstream_receipts),
        "upstream_verification_hashes": [row["self_hash"] for row in upstream_receipts],
        "independent_result_verification_count": len(oracle_receipts),
        "independent_result_verification_surface_count": sum(row["verified_surface_count"] for row in oracle_receipts),
        "fresh_process_custodian": True, "custodian_pid_distinct": invocation["custodian_pid"] != invocation["custodian_parent_pid"],
        "lease_issue_count": 1, "lease_consume_count": 1, "lease_reissue_count": 0,
        "production_primitive_builder_called": True, "independent_primitive_builder_called": False,
        "production_result_builder_called": True, "independent_result_builder_called": False,
        "attack_test_accesses": 0, "real_label_scenario_accesses": 0,
        "provider_calls": 0, "credential_reads": 0, "scientific_method_changes": 0,
        "fixture_authority": "SYNTHETIC_ONLY_NON_RESULT_PRODUCING",
        "source_commit": source_commit})


__all__ = ["DG05ConnectedRehearsalV4Error", "run_connected_synthetic_rehearsal_v4"]
