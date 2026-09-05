"""Synthetic-only connected rehearsal for the DG-05 V3 executable path."""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

from paperworks.validation_v2.dg05_execution_closure_v1 import (
    DG05ExecutableAuthorityManifestV1,
    DG05ProductionExecutorV1,
    DetectorSubauthorityRegistryV1,
    DetectorSubauthorityV1,
    FullProcessPointV1,
    FullProcessScopeAuthorityV1,
    MethodDispatchEntryV1,
    MethodDispatchRegistryV1,
    NestedAuthorityReplayBundleV1,
    PersistedAuthorityRefV1,
    RuleRuntimeSubauthorityRegistryV1,
    RuleRuntimeSubauthorityV1,
    ScenarioRecordV1,
    StateTransitionEvidenceV1,
    STATE_ORDER_V3,
    advance_dg05_state_v1,
    build_denominator_authority_v1,
    build_expected_prediction_cell_census_v1,
    build_global_prediction_manifest_v1,
    build_scenario_authority_v1,
    canonical_bytes,
    digest,
    execute_prediction_cell_v1,
    file_sha256,
    freeze_global_predictions_v1,
    initialize_dg05_execution_v1,
    issue_label_lease_v3,
    project_attack_feature_file_v1,
    self_hashed,
)
from paperworks.validation_v2.dg05_label_custodian_v1 import consume_and_extract_v1
from paperworks.validation_v2.dg05_metric_surface_execution_v1 import (
    build_metric_primitives_from_frozen_execution_v1,
    close_complete_metric_results_v1,
)
from paperworks.validation_v2.dg05_metric_surface_v1 import (
    FROZEN_PANEL_ORDER,
    build_complete_metric_surface_v1,
    persist_canonical_v1,
)
from paperworks.validation_v2.multipanel_custody_v1 import (
    FROZEN_ATTACK_FILE_CENSUS_HASH_V2,
    FROZEN_ATTACK_FILE_IDS_V2,
    FROZEN_AUTHORITY_SOURCE_COMMIT_V2,
    FROZEN_DETECTOR_AUTHORITY_HASHES_V2,
    FROZEN_FUSION_POLICY_HASH_V2,
    FROZEN_METHOD_BUNDLE_HASH_V2,
    FROZEN_PANEL_ORDER_V2,
    FROZEN_PORTFOLIO_HASHES_V2,
    FrozenPhysicalFileAuthorityV2,
    PhysicalFileIdentityV2,
    frozen_feature_allowlist_authorities_v2,
)


H = "a" * 64
G = "a" * 40
NOMINAL = {FROZEN_PANEL_ORDER_V2[0]: 38, FROZEN_PANEL_ORDER_V2[1]: 58,
           FROZEN_PANEL_ORDER_V2[2]: 50}


def _detectors() -> DetectorSubauthorityRegistryV1:
    entries = []
    for panel in FROZEN_PANEL_ORDER_V2:
        for detector in ("PCA_SPE", "ISOLATION_FOREST"):
            salt = digest([panel, detector])
            entries.append(DetectorSubauthorityV1(panel, detector, FROZEN_DETECTOR_AUTHORITY_HASHES_V2[panel],
                                                   salt, salt, salt, salt, salt, salt, salt))
    return DetectorSubauthorityRegistryV1(tuple(sorted(entries)), G)


def _rules() -> RuleRuntimeSubauthorityRegistryV1:
    entries = []
    for panel in FROZEN_PANEL_ORDER_V2:
        for role, portfolio_hash in FROZEN_PORTFOLIO_HASHES_V2[panel].items():
            body = {"schema": "dg05_phase_a_rule_runtime_use_authority_v1",
                    "status": "PENDING_RENEWED_DG05_V2_APPROVAL", "panel_id": panel,
                    "portfolio_role": role, "candidate_portfolio_hash": portfolio_hash,
                    "portfolio_container_hash": H, "relation_authority_hash": H,
                    "numeric_authority_hash": H, "retained_rule_identity_hash": H,
                    "retained_rule_count": 1, "formal_v4_semantics_hash": H,
                    "dg05_runtime_adapter_hash": H, "source_commit": G}
            entries.append(RuleRuntimeSubauthorityV1(panel, role, portfolio_hash, H, H, H, 1,
                                                       H, H, H, digest(body), G))
    return RuleRuntimeSubauthorityRegistryV1(tuple(sorted(entries)), G)


def _dispatch(detectors: DetectorSubauthorityRegistryV1,
              rules: RuleRuntimeSubauthorityRegistryV1) -> MethodDispatchRegistryV1:
    base = {
        "M0_PCA_SPE": ("PCA", "PCA_SPE", "PCA"),
        "M1_T0_RULE_ONLY": ("RULE", None, "T0"),
        "M2_T2_RULE_ONLY": ("RULE", None, "T2"),
        "M3_PCA_PLUS_T0": ("FUSION", "PCA_SPE", "T0"),
        "M4_PCA_PLUS_T2": ("FUSION", "PCA_SPE", "T2"),
        "ISOLATION_FOREST": ("IF", "ISOLATION_FOREST", "IF"),
        "ISOLATION_FOREST_PLUS_T2": ("FUSION", "ISOLATION_FOREST", "T2"),
    }
    entries = []
    for panel in FROZEN_PANEL_ORDER_V2:
        methods = dict(base)
        if panel == FROZEN_PANEL_ORDER_V2[0]:
            methods.update({"V2A_RULE_ONLY_REFERENCE": ("RULE", None, "V2A"),
                            "HISTORICAL_PCA_PLUS_V2A_CONTINUITY": ("FUSION", "PCA_SPE", "V2A")})
        for method, (kind, detector, portfolio) in methods.items():
            components = []
            if detector:
                components.append(digest(detectors.lookup(panel, detector).document()))
            if portfolio in ("T0", "T2", "V2A"):
                components.extend((FROZEN_PORTFOLIO_HASHES_V2[panel][portfolio],
                                   digest(rules.lookup(panel, portfolio).document())))
            if kind == "FUSION":
                components.append(FROZEN_FUSION_POLICY_HASH_V2)
            entries.append(MethodDispatchEntryV1(panel, method, kind, tuple(components), detector))
    return MethodDispatchRegistryV1(tuple(sorted(entries)), detectors.document()["self_hash"],
                                    FROZEN_METHOD_BUNDLE_HASH_V2, G)


def _scope() -> FullProcessScopeAuthorityV1:
    points = []
    for version in ("21.03", "22.04", "23.05"):
        points.extend((FullProcessPointV1(version, "P1_EXACT", "P1", "YES", H),
                       FullProcessPointV1(version, "P2_EXACT", "P2", "NO", H)))
    return FullProcessScopeAuthorityV1(tuple(sorted(points)), H,
        tuple((version, H) for version in ("21.03", "22.04", "23.05")), G,
        version_counts=tuple((version, 2) for version in ("21.03", "22.04", "23.05")),
        authority_mode="SYNTHETIC_REHEARSAL")


def _manifest(dispatch: MethodDispatchRegistryV1, detectors: DetectorSubauthorityRegistryV1,
              rules: RuleRuntimeSubauthorityRegistryV1,
              scope: FullProcessScopeAuthorityV1) -> DG05ExecutableAuthorityManifestV1:
    implementations = tuple(sorted((name, digest(name)) for name in (
        "state_machine", "projection_adapter", "prediction_adapter", "timestamp_builder",
        "scenario_builder", "denominator_builder", "global_manifest_builder", "global_freeze_builder",
        "label_custodian", "result_builder", "result_verifier", "fusion_runtime")))
    portfolios = tuple(sorted(value for values in FROZEN_PORTFOLIO_HASHES_V2.values()
                              for value in values.values()))
    provisional = DG05ExecutableAuthorityManifestV1(
        tuple(__import__("paperworks.validation_v2.dg05_execution_closure_v1", fromlist=["FROZEN_SCIENTIFIC_AUTHORITIES_V1"])
              .FROZEN_SCIENTIFIC_AUTHORITIES_V1.items()), detectors.document()["self_hash"],
        dispatch.document()["self_hash"], rules.document()["self_hash"], portfolios,
        scope.document()["self_hash"], digest("p1-custodian-v3"), implementations, H, G)
    return provisional


def _initialize(root: Path, dispatch: MethodDispatchRegistryV1,
                detectors: DetectorSubauthorityRegistryV1,
                rules: RuleRuntimeSubauthorityRegistryV1,
                scope: FullProcessScopeAuthorityV1):
    provisional = _manifest(dispatch, detectors, rules, scope)
    entries = []
    for logical_name, authority_hash in sorted(provisional.required_nested_hashes().items()):
        path = root / "nested" / f"{digest(logical_name)}.bin"
        path.parent.mkdir(parents=True, exist_ok=True)
        if logical_name.startswith("implementation:"):
            path.write_bytes(logical_name.encode("ascii"))
            authority_hash = file_sha256(path)
            schema = field = None
        else:
            document = self_hashed({"schema": "synthetic_bound_authority_v1",
                                    "bound_authority_hash": authority_hash})
            path.write_bytes(canonical_bytes(document) + b"\n")
            schema, field = "synthetic_bound_authority_v1", "bound_authority_hash"
        entries.append(PersistedAuthorityRefV1(logical_name, authority_hash, file_sha256(path),
                                                schema, field, path))
    implementation_hashes = tuple((name, next(entry.expected_authority_hash for entry in entries
                                               if entry.logical_name == f"implementation:{name}"))
                                  for name, _ in provisional.implementation_hashes)
    final = replace(provisional, implementation_hashes=tuple(sorted(implementation_hashes)))
    expected = final.required_nested_hashes()
    bundle = NestedAuthorityReplayBundleV1(tuple(sorted(replace(entry, expected_authority_hash=expected[entry.logical_name])
                                                        for entry in entries)), G)
    final = replace(final, nested_authority_replay_bundle_hash=bundle.document()["self_hash"])
    manifest_path = root / "synthetic-v2-manifest.json"
    manifest_path.write_bytes(canonical_bytes(final.document()) + b"\n")
    return final, bundle, manifest_path


def _transition(root: Path, kind: str, count: int, document: Mapping[str, Any], *,
                next_state: str, current_state: Mapping[str, Any],
                manifest: DG05ExecutableAuthorityManifestV1) -> StateTransitionEvidenceV1:
    path = root / "states" / f"{kind}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(document) + b"\n")
    body = {"schema": "dg05_state_transition_binding_v1", "next_state": next_state,
            "evidence_kind": kind, "evidence_authority_hash": document["self_hash"],
            "evidence_artifact_byte_hash": file_sha256(path), "evidence_item_count": count,
            "predecessor_state_hash": current_state["self_hash"],
            "executable_approval_manifest_hash": manifest.document()["self_hash"],
            "execution_id": current_state["execution_id"], "source_commit": manifest.source_commit}
    binding = self_hashed(body)
    binding_path = root / "states" / f"{kind}.binding.json"
    binding_path.write_bytes(canonical_bytes(binding) + b"\n")
    return StateTransitionEvidenceV1(kind, document["self_hash"], count, document, path, file_sha256(path),
                                     binding, binding_path, file_sha256(binding_path))


def _write_csv(path: Path, authority: Any, rows: int = 128) -> None:
    header = [authority.timestamp_id, *authority.feature_ids, "Attack", "unknown_field"]
    lines = [b",".join(value.encode() for value in header)]
    start = datetime(2026, 1, 1)
    for index in range(rows):
        timestamp = (start + timedelta(seconds=index)).isoformat().encode()
        values = [str(1.0 + (index % 3) * .1).encode()] * len(authority.feature_ids)
        lines.append(b",".join([timestamp, *values, b"opaque-label", b"opaque"]))
    path.write_bytes(b"\n".join(lines) + b"\n")


def _normal_burden(panel: str, methods: tuple[str, ...], files: tuple[str, ...]) -> dict[str, Any]:
    output = {}
    for ordinal, method in enumerate(methods):
        output[method] = {
            "authority_class": "POST_FREEZE_NORMAL_AUDIT" if panel == FROZEN_PANEL_ORDER_V2[1]
                               else "GUARD_CONDITIONED_NORMAL",
            "opportunity_coverage": 1.0,
            "components": [{"component_id": f"{file_id}:{method}", "false_seconds": ordinal,
                            "false_episodes": min(ordinal, 2), "exposure_seconds": 3600,
                            "abstain": 1, "opportunities": 100, "evaluated": 99}
                           for file_id in files],
        }
    return output


def run_connected_synthetic_rehearsal_v3(*, root: Path, contract: Mapping[str, Any],
                                         wrapper: Any, source_commit: str) -> dict[str, Any]:
    """Run projection through path-only metric verification using synthetic bytes."""
    root.mkdir(parents=True, exist_ok=True)
    detectors, rules, scope = _detectors(), _rules(), _scope()
    dispatch = _dispatch(detectors, rules)
    manifest, nested, manifest_path = _initialize(root, dispatch, detectors, rules, scope)
    manifest_hash = manifest.document()["self_hash"]
    state = initialize_dg05_execution_v1(manifest, approved_manifest_hash=manifest_hash,
        execution_id="SYNTHETIC_DG05_V3_CONNECTED", manifest_artifact_path=manifest_path,
        nested_authority_replay=nested)
    executor = DG05ProductionExecutorV1.synthetic_rehearsal(
        executable_manifest=manifest, executable_manifest_hash=manifest_hash,
        detector_registry=detectors, dispatch_registry=dispatch, rule_runtime_registry=rules,
        adapter_implementation_hash=dict(manifest.implementation_hashes)["prediction_adapter"],
        fusion_implementation_hash=dict(manifest.implementation_hashes)["fusion_runtime"])

    allowlists = frozen_feature_allowlist_authorities_v2()
    physical_rows = []
    source_paths: dict[tuple[str, str], Path] = {}
    for panel in FROZEN_PANEL_ORDER_V2:
        for file_id in FROZEN_ATTACK_FILE_IDS_V2[panel]:
            path = root / "synthetic_containers" / f"{panel}-{file_id}.csv"
            path.parent.mkdir(parents=True, exist_ok=True)
            _write_csv(path, allowlists[panel])
            header_hash = digest([allowlists[panel].timestamp_id, *allowlists[panel].feature_ids,
                                  "Attack", "unknown_field"])
            physical_rows.append(PhysicalFileIdentityV2(panel, file_id, file_sha256(path), header_hash,
                                                        digest([panel, file_id, "synthetic-official"])))
            source_paths[(panel, file_id)] = path
    physical = FrozenPhysicalFileAuthorityV2(tuple(physical_rows), FROZEN_ATTACK_FILE_CENSUS_HASH_V2,
                                              H, FROZEN_AUTHORITY_SOURCE_COMMIT_V2)
    census = build_expected_prediction_cell_census_v1(physical=physical, dispatch=dispatch)
    state = advance_dg05_state_v1(state, manifest, next_state=STATE_ORDER_V3[1],
        evidence=_transition(root, "PHYSICAL_FILE_AUTHORITY", 10, physical.document(),
                             next_state=STATE_ORDER_V3[1], current_state=state, manifest=manifest))

    projections: dict[tuple[str, str], tuple[Any, Path]] = {}
    timestamps: dict[tuple[str, str], Any] = {}
    for item in physical.files:
        destination = root / "projections" / f"{item.panel_id}-{item.file_id}.jsonl"
        projection, timestamp = project_attack_feature_file_v1(
            source=source_paths[(item.panel_id, item.file_id)], destination=destination,
            physical_file=item, panel_authority=allowlists[item.panel_id], file_id=item.file_id,
            adapter_implementation_hash=H, source_commit=G)
        projections[(item.panel_id, item.file_id)] = (projection, destination)
        timestamps[(item.panel_id, item.file_id)] = timestamp
    projection_census = self_hashed({"schema": "dg05_feature_projection_census_v1", "count": 10,
        "projection_authority_hashes": [value[0].document()["self_hash"] for value in projections.values()]})
    state = advance_dg05_state_v1(state, manifest, next_state=STATE_ORDER_V3[2],
        evidence=_transition(root, "PROJECTION_CENSUS", 10, projection_census,
                             next_state=STATE_ORDER_V3[2], current_state=state, manifest=manifest))
    execution_start = self_hashed({"schema": "dg05_prediction_execution_start_v1", "start_count": 1,
                                   "label_access_allowed": False, "census_hash": census["self_hash"]})
    state = advance_dg05_state_v1(state, manifest, next_state=STATE_ORDER_V3[3],
        evidence=_transition(root, "EXECUTION_START", 1, execution_start,
                             next_state=STATE_ORDER_V3[3], current_state=state, manifest=manifest))

    receipts = []
    artifacts = {}
    prediction_paths: dict[str, Path] = {}
    trace_paths: dict[str, Path] = {}
    output = root / "predictions"
    for cell in census["cells"]:
        projection, projection_path = projections[(cell["panel_id"], cell["file_id"])]
        receipt = execute_prediction_cell_v1(cell=cell, dispatch=dispatch, projection=projection,
            timestamp=timestamps[(cell["panel_id"], cell["file_id"])],
            executable_manifest_hash=manifest_hash, executor=executor, projection_path=projection_path,
            output_directory=output, source_commit=G)
        receipts.append(receipt)
        receipt_path = output / f"{receipt.cell_id}.receipt.json"
        receipt_path.write_bytes(canonical_bytes(receipt.document()) + b"\n")
        prediction_path = output / f"{receipt.cell_id}.prediction.json"
        trace_path = output / f"{receipt.cell_id}.trace.json"
        artifacts[receipt.cell_id] = (prediction_path, trace_path if receipt.trace_status == "BOUND" else None,
                                      receipt_path)
        prediction_paths[receipt.cell_id] = prediction_path
        if receipt.trace_status == "BOUND":
            trace_paths[receipt.cell_id] = trace_path
    global_manifest = build_global_prediction_manifest_v1(census=census, receipts=receipts,
        executable_manifest_hash=manifest_hash, dispatch=dispatch)
    freeze = freeze_global_predictions_v1(manifest=global_manifest, census=census,
                                           receipt_artifacts=artifacts, predecessor_state=state)
    state = advance_dg05_state_v1(state, manifest, next_state=STATE_ORDER_V3[4],
        evidence=_transition(root, "GLOBAL_FREEZE", census["count"], freeze,
                             next_state=STATE_ORDER_V3[4], current_state=state, manifest=manifest))

    # The synthetic custodian consumes the one-shot lease before reading the
    # hypothetical scenario source and has no prediction-root capability.
    scenario_records = []
    for panel in FROZEN_PANEL_ORDER_V2:
        first_file = FROZEN_ATTACK_FILE_IDS_V2[panel][0]
        for index in range(NOMINAL[panel]):
            # Alternate even/odd rows so the real synthetic executor yields
            # both HIT and MISS observations without outcome-dependent setup.
            moment = (datetime(2026, 1, 1) + timedelta(seconds=index * 2 + index % 2)).isoformat()
            identity = "P1_EXACT" if index % 3 else "P2_EXACT"
            scenario_records.append({"panel_id": panel,
                "dataset_version": {FROZEN_PANEL_ORDER_V2[0]: "23.05", FROZEN_PANEL_ORDER_V2[1]: "22.04",
                                    FROZEN_PANEL_ORDER_V2[2]: "21.03"}[panel],
                "file_id": first_file, "scenario_id": f"S{index + 1:03d}",
                "closed_intervals": [[moment, moment]], "attacked_identities": [identity],
                "explicit_affected_processes": ["P1"] if identity == "P2_EXACT" and index % 2 else []})
    incoming, custodian = root / "custodian_input", root / "custodian_output"
    incoming.mkdir(); custodian.mkdir()
    source = incoming / "synthetic_scenarios.json"
    source.write_bytes(canonical_bytes({"schema": "synthetic_raw_official_scenario_fixture_v1",
                                        "records": scenario_records}) + b"\n")
    source_hash = file_sha256(source)
    policy = self_hashed({"schema": "custodian_resource_policy_authority_v1",
        "input_root": str(incoming.resolve()), "output_root": str(custodian.resolve()),
        "forbidden_roots": [str(output.resolve())],
        "approved_sources": [{"source_id": "SYNTHETIC", "path": str(source.resolve()),
            "byte_hash": source_hash, "official_source_hash": source_hash,
            "dataset_version": "MULTI_VERSION_23_22_21", "source_format": "SYNTHETIC_JSON_V1",
            "adapter_id": "SYNTHETIC_OFFICIAL_SCENARIO_FIXTURE_V1"}],
        "executable_manifest_hash": manifest_hash, "scenario_adapter_implementation_hash": H,
        "resource_policy_contract_hash": H, "source_commit": G})
    policy_path = root / "custodian-policy.json"
    policy_path.write_bytes(canonical_bytes(policy) + b"\n")
    lease = issue_label_lease_v3(freeze=freeze, state=state, executable_manifest_hash=manifest_hash,
                                 resource_policy_authority_hash=policy["self_hash"])
    state = advance_dg05_state_v1(state, manifest, next_state=STATE_ORDER_V3[5],
        evidence=_transition(root, "LEASE_ISSUE", 1, lease["receipt"], next_state=STATE_ORDER_V3[5],
                             current_state=state, manifest=manifest))
    bindings = []
    for item in physical.files:
        bindings.append({"panel_id": item.panel_id,
            "dataset_version": {FROZEN_PANEL_ORDER_V2[0]: "23.05", FROZEN_PANEL_ORDER_V2[1]: "22.04",
                                FROZEN_PANEL_ORDER_V2[2]: "21.03"}[item.panel_id],
            "file_id": item.file_id, "physical_file_authority_hash": digest(item.document()),
            "timestamp_authority_hash": timestamps[(item.panel_id, item.file_id)].document()["self_hash"],
            "official_source_hash": source_hash})
    request = {"schema": "isolated_label_scenario_custodian_request_v1",
        "opaque_lease": lease["opaque_token"], "lease_receipt": lease["receipt"],
        "global_freeze_hash": freeze["self_hash"], "executable_manifest_hash": manifest_hash,
        "approved_source_id": "SYNTHETIC", "approved_output_name": "scenario-output.json",
        "public_authority_hashes": [contract["self_hash"]], "consumed_receipt_name": "consumed.json",
        "resource_policy_hash": policy["self_hash"], "allowed_scenario_bindings": bindings,
        "authority_mode": "SYNTHETIC_REHEARSAL", "nominal_counts": NOMINAL}
    consume = consume_and_extract_v1(request, resource_policy_authority_path=policy_path)
    custodian_output = json.loads((custodian / "scenario-output.json").read_text(encoding="ascii"))
    typed_records = tuple(sorted(ScenarioRecordV1(
        row["panel_id"], row["dataset_version"], row["file_id"], row["scenario_id"],
        tuple(tuple(value) for value in row["closed_intervals"]), tuple(row["attacked_identities"]),
        tuple(row["explicit_affected_processes"]), row["physical_file_authority_hash"],
        row["timestamp_authority_hash"], row["official_source_hash"])
        for row in custodian_output["records"]))
    scenario = build_scenario_authority_v1(records=typed_records,
        lease_completion_hash=custodian_output["self_hash"], global_freeze_hash=freeze["self_hash"],
        source_commit=G, nominal_counts=NOMINAL, authority_mode="SYNTHETIC_REHEARSAL")
    state = advance_dg05_state_v1(state, manifest, next_state=STATE_ORDER_V3[6],
        evidence=_transition(root, "SCENARIO_AUTHORITY", sum(NOMINAL.values()), scenario,
                             next_state=STATE_ORDER_V3[6], current_state=state, manifest=manifest))
    denominator = build_denominator_authority_v1(scenario_authority=scenario, full_scope=scope,
                                                  p1_custodian_v3_hash=manifest.p1_custodian_v3_hash)
    state = advance_dg05_state_v1(state, manifest, next_state=STATE_ORDER_V3[7],
        evidence=_transition(root, "DENOMINATOR_AUTHORITY", sum(NOMINAL.values()), denominator,
                             next_state=STATE_ORDER_V3[7], current_state=state, manifest=manifest))

    contract_path = root / "metric-contract.json"
    persist_canonical_v1(contract_path, contract)
    primitive_paths = []
    result_paths = []
    built_surface_ids = []
    for panel in FROZEN_PANEL_ORDER:
        panel_files = tuple(FROZEN_ATTACK_FILE_IDS_V2[panel])
        methods = tuple(__import__("paperworks.validation_v2.dg05_execution_closure_v1", fromlist=["FROZEN_METHOD_IDS_BY_PANEL_V1"])
                        .FROZEN_METHOD_IDS_BY_PANEL_V1[panel])
        primitive = build_metric_primitives_from_frozen_execution_v1(
            panel_id=panel, global_prediction_manifest=global_manifest, global_prediction_freeze=freeze,
            scenario_authority=scenario, denominator_authority=denominator,
            projection_paths={file_id: projections[(panel, file_id)][1] for file_id in panel_files},
            prediction_paths=prediction_paths, trace_paths=trace_paths,
            method_normal_burden=_normal_burden(panel, methods, panel_files),
            normal_burden_authority_hash=H)
        result = build_complete_metric_surface_v1(primitives=primitive, contract=contract,
            executable_manifest_hash=manifest_hash, wrapper=wrapper, source_commit=source_commit)
        primitive_path = root / "metric" / f"{panel}.primitive.json"
        result_path = root / "metric" / f"{panel}.result.json"
        primitive_path.parent.mkdir(parents=True, exist_ok=True)
        persist_canonical_v1(primitive_path, primitive); persist_canonical_v1(result_path, result)
        primitive_paths.append(primitive_path); result_paths.append(result_path)
        built_surface_ids.extend(row["surface_id"] for row in result["surfaces"])
    final_state = close_complete_metric_results_v1(predecessor_state=state,
        executable_manifest_hash=manifest_hash, contract_path=contract_path,
        primitive_paths=primitive_paths, result_paths=result_paths, wrapper=wrapper)
    return {"schema": "connected_synthetic_dg05_rehearsal_evidence_v3",
        "derived_prediction_cells": census["count"], "prediction_cells_by_panel": {
            panel: sum(row["panel_id"] == panel for row in census["cells"]) for panel in FROZEN_PANEL_ORDER},
        "successful_prediction_cells": global_manifest["success_count"],
        "deliberate_method_failures": global_manifest["failure_count"],
        "synthetic_scenarios": len(typed_records), "panel_metric_result_authorities": len(result_paths),
        "built_surface_ids": sorted(built_surface_ids),
        "verified_surface_count": final_state["verified_surface_count"],
        "global_prediction_freeze": freeze["status"], "lease_issue_count": lease["receipt"]["issue_count"],
        "lease_consume_count": 1, "custodian_output_hash": consume["output_self_hash"],
        "final_state": final_state["state"], "attack_test_accesses": 0,
        "real_label_scenario_accesses": 0, "provider_calls": 0, "credential_reads": 0,
        "primitive_paths": primitive_paths, "result_paths": result_paths, "contract_path": contract_path,
        "synthetic_v2_manifest_hash": manifest_hash}


__all__ = ["run_connected_synthetic_rehearsal_v3"]
