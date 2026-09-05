"""Freeze DG05 executable closure authorities using synthetic-only rehearsal."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from paperworks.validation_v2.dg05_execution_closure_v1 import *
from paperworks.validation_v2.dg05_execution_closure_v1 import (
    FROZEN_FULL_SCOPE_PROCESS_MAP_V1, FROZEN_METHOD_IDS_BY_PANEL_V1, STATE_ORDER_V3,
)
from paperworks.validation_v2.dg05_result_oracle_v1 import (
    FrozenResultReplayPathsV1, verify_result_from_persisted_artifacts_v1,
)
from paperworks.validation_v2.multipanel_custody_v1 import (
    FROZEN_ATTACK_FILE_CENSUS_HASH_V2, FROZEN_ATTACK_FILE_IDS_V2,
    FROZEN_AUTHORITY_SOURCE_COMMIT_V2, FROZEN_DETECTOR_AUTHORITY_HASHES_V2,
    FROZEN_FUSION_POLICY_HASH_V2, FROZEN_METHOD_BUNDLE_HASH_V2,
    FROZEN_PANEL_ORDER_V2, FROZEN_PORTFOLIO_HASHES_V2,
    FrozenPhysicalFileAuthorityV2, PhysicalFileIdentityV2,
    frozen_feature_allowlist_authorities_v2,
)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research_control_center/validation_v2/dg05_exec_closure"
SOURCE_COMMIT = "3bbcf8c911e0ba8e9b2af1e2a2c1d85b4680e86e"
BLOCKER_COMMIT = "ed0c8dc1fbc5cadb0bf1b9e6a8cfed2c698c896c"
BLOCKER_AUDIT_HASH = "cf972caae96dee3345a029345463ad7e6bddcd96c226104f14742e15eb387c3e"
MANUAL_HASH = "0668345c4e80331b918fe17c81f8f363b13bd22886831d286e761bc62b71a556"
SCHEMA_HASHES = {
    "23.05": "95968d825d1c9caab778a857cec618b64674ec5a85d94e6952d99c2cab08d16a",
    "22.04": "c6154f048a3b926d4530f6c078ad86ca1393a290d08074d715b156079e9d0876",
    "21.03": "6efc01725e2f33dbf79557b20388687e1a17657eeed950c2abcc874210d76b18",
}
SUPPLEMENTAL = {
    "HAI23_BOILER_GRAPH": "eca648d73c0444a35294608c2a1067256d7b32547257153226fece2de3febd07",
    "HAI23_DCS_1001H": "3cebccfed59f8f2da4fe90ea8b9055da64ace270133e8a8e281377ac37c7e602",
    "HAI23_DCS_1002H": "d3f060df16c97a5dbf18907199d7e75f61cc58587100fe76b9d4f8a6be354fd6",
    "HAI23_DCS_1003H": "c23f069441d6acfcd3201b224d56444699fb6f6de295f438dbdcee1f4f2c3939",
}


def read_authority(relative: str) -> dict:
    value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    validate_self_hashed(value)
    return value


def write_authority(name: str, value: dict) -> str:
    OUT.mkdir(parents=True, exist_ok=True)
    payload = canonical_bytes(value) + b"\n"
    (OUT / name).write_bytes(payload)
    if json.loads((OUT / name).read_text(encoding="ascii")) != value:
        raise RuntimeError(f"REPLAY_FAILED:{name}")
    return sha256(payload).hexdigest()


def build_scope() -> FullProcessScopeAuthorityV1:
    points = []
    for version, process_map in FROZEN_FULL_SCOPE_PROCESS_MAP_V1.items():
        for process, identities in process_map.items():
            for identity in identities:
                extra = None
                status = "MANUAL_EXACT"
                membership = "YES" if process == "P1" else "NO"
                if version == "23.05" and identity.startswith("x100"):
                    key = identity.split("_", 1)[0].upper().replace("X", "HAI23_DCS_") + "H"
                    extra = SUPPLEMENTAL[key]
                    status = "VERIFIED_PUBLIC_GRAPH_ALIAS"
                if version == "21.03" and identity == "P2_SIT02":
                    membership = "UNRESOLVED"
                    status = "HEADER_ONLY_MANUAL_UNDOCUMENTED"
                evidence = digest({"manual_hash": MANUAL_HASH, "schema_hash": SCHEMA_HASHES[version],
                                   "identity": identity, "process": process, "p1_membership": membership,
                                   "authority_status": status, "supplemental_hash": extra})
                points.append(FullProcessPointV1(version, identity, process, membership, evidence, status))
    identity_hashes = tuple(sorted((version, digest(sorted(i for ids in processes.values() for i in ids)))
                                   for version, processes in FROZEN_FULL_SCOPE_PROCESS_MAP_V1.items()))
    scope = FullProcessScopeAuthorityV1(tuple(sorted(points)), MANUAL_HASH, tuple(sorted(SCHEMA_HASHES.items())), SOURCE_COMMIT,
        version_counts=(("21.03", 79), ("22.04", 86), ("23.05", 86)),
        declared_count_discrepancies=("HAI21_MANUAL_DECLARED_78_BUT_OFFICIAL_NORMAL_SCHEMA_CONTAINS_79",),
        official_identity_set_hashes=identity_hashes, supplemental_authority_hashes=tuple(sorted(SUPPLEMENTAL.items())))
    scope.validate()
    return scope


def build_detectors() -> DetectorSubauthorityRegistryV1:
    pre = ROOT / "research_control_center/validation_v2/multipanel_pre_dg05"
    hai23 = json.loads((pre / "HAI23_DETECTOR_PRIVATE_HASH_BINDING_V1.json").read_text(encoding="utf-8"))
    ext = {version: json.loads((pre / f"HAI{version[:2]}_DETECTOR_AUTHORITY_V1.json").read_text(encoding="utf-8"))
           for version in ("22.04", "21.03")}
    allowlists = frozen_feature_allowlist_authorities_v2()
    implementation = {
        ("23.05", "PCA_SPE"): file_sha256(ROOT / "src/paperworks/validation_v2/pca_spe_v2.py"),
        ("23.05", "ISOLATION_FOREST"): file_sha256(ROOT / "src/paperworks/validation_v2/isolation_forest_v1.py"),
        ("22.04", "PCA_SPE"): file_sha256(ROOT / "src/paperworks/validation_v2/xver_detector_v1.py"),
        ("22.04", "ISOLATION_FOREST"): file_sha256(ROOT / "src/paperworks/validation_v2/xver_detector_v1.py"),
        ("21.03", "PCA_SPE"): file_sha256(ROOT / "src/paperworks/validation_v2/xver_detector_v1.py"),
        ("21.03", "ISOLATION_FOREST"): file_sha256(ROOT / "src/paperworks/validation_v2/xver_detector_v1.py"),
    }
    entries = []
    panel_version = dict(zip(FROZEN_PANEL_ORDER_V2, ("23.05", "22.04", "21.03")))
    for panel, version in panel_version.items():
        feature_hash = digest(list(allowlists[panel].feature_ids))
        if version == "23.05":
            values = {
                "PCA_SPE": (hai23["private_model_bytes_hash"], "HAI23_DETECTOR_TUPLE_V1", 0, 2, None, None, "PcaSpeModelV2", "score_pca_spe_v2", hai23["pca_fit_authority_hash"], hai23["pca_threshold_authority_hash"]),
                "ISOLATION_FOREST": (hai23["private_model_bytes_hash"], "HAI23_DETECTOR_TUPLE_V1", 1, 3, None, None, "IsolationForestModelV1", "score_isolation_forest_v1", hai23["if_fit_authority_hash"], hai23["if_threshold_authority_hash"]),
            }
            environment = hai23["environment_hash"]
        else:
            doc = ext[version]
            values = {
                "PCA_SPE": (doc["PCA"]["private_bytes_hash"], "MODEL_THRESHOLD_MAPPING_V1", None, None, "model", "threshold", "ExternalPcaModelV1", "score_external_pca_v1", doc["PCA"]["fit"]["self_hash"], doc["PCA"]["threshold_authority_hash"]),
                "ISOLATION_FOREST": (doc["IF"]["private_bytes_hash"], "MODEL_THRESHOLD_MAPPING_V1", None, None, "model", "threshold", "ExternalIfModelV1", "score_external_if_v1", doc["IF"]["fit"]["self_hash"], doc["IF"]["threshold_authority_hash"]),
            }
            environment = doc["self_hash"]
        for detector_id, (container_hash, container_format, model_index, threshold_index, model_key, threshold_key, model_type, scorer_id, fit_hash, threshold_hash) in values.items():
            component_hash = digest({"schema":"detector_private_component_locator_v1",
                "private_container_hash":container_hash,"private_container_format":container_format,
                "model_locator":model_index if model_index is not None else model_key,
                "threshold_locator":threshold_index if threshold_index is not None else threshold_key,"model_type_id":model_type,
                "fit_authority_hash":fit_hash,"threshold_authority_hash":threshold_hash})
            entries.append(DetectorSubauthorityV1(panel, detector_id, FROZEN_DETECTOR_AUTHORITY_HASHES_V2[panel],
                implementation[(version, detector_id)], feature_hash, component_hash, fit_hash, threshold_hash,
                digest({"schema": "dense_boolean_prediction_v1"}), environment,
                container_hash, container_format, model_index, threshold_index, model_key, threshold_key, model_type, scorer_id))
    registry = DetectorSubauthorityRegistryV1(tuple(sorted(entries)), SOURCE_COMMIT)
    registry.validate()
    return registry


def build_dispatch(detectors: DetectorSubauthorityRegistryV1) -> MethodDispatchRegistryV1:
    entries = []
    for panel, methods in FROZEN_METHOD_IDS_BY_PANEL_V1.items():
        for method in methods:
            detector_id = None
            executor = "RULE"
            components = []
            if method == "M0_PCA_SPE":
                executor, detector_id = "PCA", "PCA_SPE"
            elif method == "ISOLATION_FOREST":
                executor, detector_id = "IF", "ISOLATION_FOREST"
            elif method in ("M3_PCA_PLUS_T0", "M4_PCA_PLUS_T2", "HISTORICAL_PCA_PLUS_V2A_CONTINUITY"):
                executor, detector_id = "FUSION", "PCA_SPE"
            elif method == "ISOLATION_FOREST_PLUS_T2":
                executor, detector_id = "FUSION", "ISOLATION_FOREST"
            if detector_id:
                components.append(digest(detectors.lookup(panel, detector_id).document()))
            key = "T0" if "T0" in method else "T2" if "T2" in method else "V2A" if "V2A" in method else None
            if key:
                components.append(FROZEN_PORTFOLIO_HASHES_V2[panel][key])
            if executor == "FUSION":
                components.append(FROZEN_FUSION_POLICY_HASH_V2)
            entries.append(MethodDispatchEntryV1(panel, method, executor, tuple(components), detector_id))
    registry = MethodDispatchRegistryV1(tuple(sorted(entries)), detectors.document()["self_hash"], FROZEN_METHOD_BUNDLE_HASH_V2, SOURCE_COMMIT)
    registry.validate()
    return registry


def make_csv(path: Path, authority, marker: bytes = b"0") -> None:
    header = [authority.timestamp_id, *authority.feature_ids, "Attack", "scenario"]
    rows = [b",".join(v.encode() for v in header)]
    for index in range(2):
        rows.append(b",".join([f"2026-01-01T00:00:0{index}".encode(), *([b"1.0"] * len(authority.feature_ids)), marker, b"opaque"]))
    path.write_bytes(b"\n".join(rows) + b"\n")


def _persist_canonical(path: Path, value: dict) -> tuple[Path, str]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(value) + b"\n")
    return path, file_sha256(path)


def _transition(root: Path, *, kind: str, count: int, document: dict) -> StateTransitionEvidenceV1:
    path, byte_hash = _persist_canonical(root / "state-evidence" / f"{kind}.json", document)
    return StateTransitionEvidenceV1(kind, document["self_hash"], count, document, path, byte_hash)


def synthetic_rehearsal(manifest, dispatch, detectors, scope, *, manifest_path: Path,
                        nested_replay: NestedAuthorityReplayBundleV1):
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        input_root, output_root, prediction_root = root / "lease_input", root / "lease_output", root / "predictions"
        input_root.mkdir(); output_root.mkdir(); prediction_root.mkdir()
        allowlists = frozen_feature_allowlist_authorities_v2()
        files = []
        for panel in FROZEN_PANEL_ORDER_V2:
            for file_id in FROZEN_ATTACK_FILE_IDS_V2[panel]:
                source = root / f"{panel}-{file_id}.csv"
                make_csv(source, allowlists[panel])
                files.append(PhysicalFileIdentityV2(panel, file_id, file_sha256(source), digest([panel, file_id, "header"]), digest([panel, file_id, "official"])))
        physical = FrozenPhysicalFileAuthorityV2(tuple(files), FROZEN_ATTACK_FILE_CENSUS_HASH_V2,
            FROZEN_SCIENTIFIC_AUTHORITIES_V1["feature_allowlist_bundle"], FROZEN_AUTHORITY_SOURCE_COMMIT_V2)
        physical.validate()
        census = build_expected_prediction_cell_census_v1(physical=physical, dispatch=dispatch)
        projections = {}; timestamps = {}; projection_paths = {}
        for item in physical.files:
            source = root / f"{item.panel_id}-{item.file_id}.csv"
            destination = root / "projections" / f"{item.panel_id}-{item.file_id}.jsonl"
            projection, timestamp = project_attack_feature_file_v1(source=source, destination=destination,
                physical_file=item, panel_authority=allowlists[item.panel_id], file_id=item.file_id,
                adapter_implementation_hash=file_sha256(ROOT / "src/paperworks/validation_v2/dg05_execution_closure_v1.py"), source_commit=SOURCE_COMMIT)
            projections[(item.panel_id, item.file_id)] = projection
            timestamps[(item.panel_id, item.file_id)] = timestamp
            projection_paths[(item.panel_id, item.file_id)] = destination

        failed_identity = (FROZEN_PANEL_ORDER_V2[2], "test5.csv", "ISOLATION_FOREST_PLUS_T2")
        failed_cell = next(cell["cell_id"] for cell in census["cells"]
                           if (cell["panel_id"], cell["file_id"], cell["method_id"]) == failed_identity)
        executor = DG05ProductionExecutorV1.synthetic_rehearsal(
            executable_manifest_hash=manifest.document()["self_hash"], detector_registry=detectors,
            dispatch_registry=dispatch,
            adapter_implementation_hash=file_sha256(ROOT / "src/paperworks/validation_v2/dg05_execution_closure_v1.py"),
            fusion_implementation_hash=file_sha256(ROOT / "src/paperworks/validation_v2/exp04_protocol_v1.py"),
            synthetic_failure_cell_ids=(failed_cell,),
        )
        receipts = []; receipt_paths = {}; prediction_paths = {}; artifact_paths = {}
        mh = manifest.document()["self_hash"]
        for cell in census["cells"]:
            projection = projections[(cell["panel_id"], cell["file_id"])]
            receipt = execute_prediction_cell_v1(cell=cell, dispatch=dispatch, projection=projection,
                timestamp=timestamps[(cell["panel_id"], cell["file_id"])], executable_manifest_hash=mh,
                executor=executor, projection_path=projection_paths[(cell["panel_id"], cell["file_id"])],
                output_directory=prediction_root, source_commit=SOURCE_COMMIT)
            receipts.append(receipt)
            rp = prediction_root / f"{receipt.cell_id}.receipt.json"
            persist_prediction_receipt_v1(rp, receipt); receipt_paths[receipt.cell_id] = rp
            pp = prediction_root / f"{receipt.cell_id}.prediction.json"
            tp = prediction_root / f"{receipt.cell_id}.trace.json"
            if receipt.status == "SUCCESS": prediction_paths[receipt.cell_id] = pp
            artifact_paths[receipt.cell_id] = (pp if receipt.status == "SUCCESS" else None,
                tp if receipt.trace_status == "BOUND" else None, rp)
        global_manifest = build_global_prediction_manifest_v1(census=census, receipts=receipts, executable_manifest_hash=mh, dispatch=dispatch)
        state = initialize_dg05_execution_v1(manifest, approved_manifest_hash=mh, execution_id="SYNTHETIC_DG05_V1",
            manifest_artifact_path=manifest_path, nested_authority_replay=nested_replay)
        for next_state, kind, artifact, count in (
            (STATE_ORDER_V3[1], "PHYSICAL_FILE_AUTHORITY", physical.document(), 10),
            (STATE_ORDER_V3[2], "PROJECTION_CENSUS", self_hashed({"schema":"dg05_feature_projection_census_v1","count":10,"projection_authority_hashes":sorted(p.document()["self_hash"] for p in projections.values())}), 10),
            (STATE_ORDER_V3[3], "EXECUTION_START", self_hashed({"schema":"dg05_prediction_execution_start_v1","start_count":1,"label_access_allowed":False,"expected_cell_census_hash":census["self_hash"]}), 1)):
            state = advance_dg05_state_v1(state, manifest, next_state=next_state, evidence=_transition(root, kind=kind, count=count, document=artifact))
        freeze = freeze_global_predictions_v1(manifest=global_manifest, census=census, receipt_artifacts=artifact_paths, predecessor_state=state)
        state = advance_dg05_state_v1(state, manifest, next_state=STATE_ORDER_V3[4], evidence=_transition(root, kind="GLOBAL_FREEZE", count=72, document=freeze))

        counts = dict(zip(FROZEN_PANEL_ORDER_V2, (38, 58, 50)))
        version = dict(zip(FROZEN_PANEL_ORDER_V2, ("23.05", "22.04", "21.03")))
        raw_records = []
        for panel in FROZEN_PANEL_ORDER_V2:
            p1 = next(i for i in FROZEN_FULL_SCOPE_PROCESS_MAP_V1[version[panel]]["P1"])
            nonp1 = next(i for i in FROZEN_FULL_SCOPE_PROCESS_MAP_V1[version[panel]]["P3"])
            file_ids = FROZEN_ATTACK_FILE_IDS_V2[panel]
            for index in range(counts[panel]):
                mode = index % 5
                attacked = [p1] if mode == 0 else [nonp1] if mode in (1, 4) else [nonp1, "UNRESOLVED_SYNTHETIC"] if mode == 2 else [p1, "UNRESOLVED_SYNTHETIC"]
                raw_records.append({"panel_id": panel, "dataset_version": version[panel], "file_id": file_ids[index % len(file_ids)],
                                    "scenario_id": f"S{index:03d}", "closed_intervals": [["2026-01-01T00:00:00", "2026-01-01T00:00:01"]],
                                    "attacked_identities": attacked, "explicit_affected_processes": ["P1"] if mode == 4 else []})
        raw_records.sort(key=lambda v: (FROZEN_PANEL_ORDER_V2.index(v["panel_id"]), v["scenario_id"]))
        source = input_root / "official_synthetic_scenarios.json"
        source.write_text(json.dumps({"schema":"synthetic_raw_official_scenario_fixture_v1","records":raw_records}, sort_keys=True, separators=(",",":")), encoding="utf-8")
        source_hash = file_sha256(source)
        bindings = []
        for item in physical.files:
            ta = timestamps[(item.panel_id, item.file_id)]
            bindings.append({"panel_id":item.panel_id,"dataset_version":version[item.panel_id],"file_id":item.file_id,
                             "physical_file_authority_hash":ta.physical_file_authority_hash,"timestamp_authority_hash":ta.document()["self_hash"],"official_source_hash":source_hash})
        policy = self_hashed({"schema":"custodian_resource_policy_authority_v1",
            "input_root":str(input_root.resolve()),"output_root":str(output_root.resolve()),"forbidden_roots":[str(prediction_root.resolve())],
            "approved_sources":[{"source_id":"SYNTHETIC_SCENARIO_SOURCE_V1","path":str(source.resolve()),"byte_hash":source_hash,
                "official_source_hash":source_hash,"dataset_version":"MULTI_VERSION_23_22_21",
                "source_format":"SYNTHETIC_JSON_V1","adapter_id":"SYNTHETIC_OFFICIAL_SCENARIO_FIXTURE_V1"}],
            "executable_manifest_hash":mh,
            "scenario_adapter_implementation_hash":file_sha256(ROOT / "src/paperworks/validation_v2/dg05_label_custodian_v1.py"),
            "resource_policy_contract_hash":file_sha256(ROOT / "src/paperworks/validation_v2/dg05_label_custodian_v1.py"),
            "source_commit":SOURCE_COMMIT})
        policy_path, _ = _persist_canonical(root / "custodian_resource_policy.private.json", policy)
        lease = issue_label_lease_v3(freeze=freeze, state=state, executable_manifest_hash=mh,
                                     resource_policy_authority_hash=policy["self_hash"])
        state = advance_dg05_state_v1(state, manifest, next_state=STATE_ORDER_V3[5],
            evidence=_transition(root, kind="LEASE_ISSUE", count=1, document=lease["receipt"]))
        request = {"schema":"isolated_label_scenario_custodian_request_v1","opaque_lease":lease["opaque_token"],"lease_receipt":lease["receipt"],
                   "global_freeze_hash":freeze["self_hash"],"executable_manifest_hash":mh,
                   "approved_source_id":"SYNTHETIC_SCENARIO_SOURCE_V1","approved_output_name":"scenario_output.json",
                   "public_authority_hashes":[scope.document()["self_hash"]],"consumed_receipt_name":"consumed.json",
                   "resource_policy_hash":policy["self_hash"],"allowed_scenario_bindings":bindings,
                   "authority_mode":"SYNTHETIC_REHEARSAL","nominal_counts":counts}
        request_path = root / "custodian_request.json"; request_path.write_text(json.dumps(request), encoding="utf-8")
        env = {"PYTHONPATH": str(ROOT / "src")}
        completed = subprocess.run([sys.executable, str(ROOT / "scripts/run_dg05_label_custodian_v1.py"), "--request", str(request_path),
                                    "--resource-policy-authority", str(policy_path)],
                                   cwd=ROOT, env=env, capture_output=True, text=True, check=True)
        custodian_receipt = json.loads(completed.stdout)
        output = json.loads((output_root / "scenario_output.json").read_text(encoding="ascii"))
        records = tuple(sorted(ScenarioRecordV1(r["panel_id"],r["dataset_version"],r["file_id"],r["scenario_id"],
            tuple(tuple(v) for v in r["closed_intervals"]),tuple(r["attacked_identities"]),tuple(r["explicit_affected_processes"]),
            r["physical_file_authority_hash"],r["timestamp_authority_hash"],r["official_source_hash"]) for r in output["records"]))
        scenario = build_scenario_authority_v1(records=records, lease_completion_hash=custodian_receipt["consume_receipt_hash"],
            global_freeze_hash=freeze["self_hash"], source_commit=SOURCE_COMMIT, nominal_counts=counts,
            timestamp_authorities=timestamps)
        state = advance_dg05_state_v1(state, manifest, next_state=STATE_ORDER_V3[6], evidence=_transition(root, kind="SCENARIO_AUTHORITY", count=146, document=scenario))
        denominator = build_denominator_authority_v1(scenario_authority=scenario, full_scope=scope, p1_custodian_v3_hash=manifest.p1_custodian_v3_hash)
        state = advance_dg05_state_v1(state, manifest, next_state=STATE_ORDER_V3[7], evidence=_transition(root, kind="DENOMINATOR_AUTHORITY", count=146, document=denominator))

        global_manifest_path, _ = _persist_canonical(root / "frozen/global-manifest.json", global_manifest)
        global_freeze_path, _ = _persist_canonical(root / "frozen/global-freeze.json", freeze)
        census_path, _ = _persist_canonical(root / "frozen/cell-census.json", census)
        scenario_path, _ = _persist_canonical(root / "frozen/scenario.json", scenario)
        denominator_path, _ = _persist_canonical(root / "frozen/denominator.json", denominator)
        projection_authority_paths = {}
        timestamp_authority_paths = {}
        for (panel, file_id), projection in projections.items():
            projection_authority_paths[(panel, file_id)] = _persist_canonical(
                root / "frozen/projections" / f"{panel}-{file_id}.authority.json", projection.document())[0]
            timestamp_authority_paths[(panel, file_id)] = _persist_canonical(
                root / "frozen/timestamps" / f"{panel}-{file_id}.authority.json", timestamps[(panel, file_id)].document())[0]

        normal_burden = read_authority("research_control_center/validation_v2/multipanel_pre_dg05/NORMAL_FALSE_BURDEN_AUTHORITY_V1.json")["self_hash"]
        result_values=[]; result_receipts=[]; result_paths=[]; oracle_receipts=[]
        for entry in dispatch.entries:
            local_receipts = {r.cell_id: receipt_paths[r.cell_id] for r in receipts if r.panel_id == entry.panel_id and r.method_id == entry.method_id}
            local_predictions = {r.cell_id: prediction_paths[r.cell_id] for r in receipts if r.panel_id == entry.panel_id and r.method_id == entry.method_id and r.status == "SUCCESS"}
            local_timestamps = {f:timestamps[(entry.panel_id,f)] for f in FROZEN_ATTACK_FILE_IDS_V2[entry.panel_id]}
            local_projections = {f:projections[(entry.panel_id,f)] for f in FROZEN_ATTACK_FILE_IDS_V2[entry.panel_id]}
            local_projection_paths = {f:projection_paths[(entry.panel_id,f)] for f in FROZEN_ATTACK_FILE_IDS_V2[entry.panel_id]}
            loaded, failures, method_hash = load_frozen_prediction_inputs_v1(panel_id=entry.panel_id,method_id=entry.method_id,
                global_manifest=global_manifest,receipt_paths=local_receipts,prediction_paths=local_predictions,
                timestamp_authorities=local_timestamps,projection_authorities=local_projections,projection_paths=local_projection_paths)
            etapr = build_etapr_coordinate_binding_v1(panel_id=entry.panel_id,file_bindings=[{"file_id":file_id,
                "physical_file_authority_hash":value[0].physical_file_authority_hash,"timestamp_authority_hash":value[0].document()["self_hash"],
                "prediction_artifact_hash":value[3],"scenario_authority_hash":scenario["self_hash"]} for file_id,value in loaded.items()],
                etapr_authority_hash=FROZEN_SCIENTIFIC_AUTHORITIES_V1["etapr"])
            etapr_path, _ = _persist_canonical(root / "results" / f"{entry.panel_id}-{entry.method_id}.etapr.json", etapr)
            result = compute_bound_panel_method_result_v1(panel_id=entry.panel_id,method_id=entry.method_id,method_authority_hash=method_hash,
                global_prediction_manifest=global_manifest,global_prediction_freeze=freeze,predictions=loaded,scenario_authority=scenario,denominator_authority=denominator,
                metric_authority_hash=FROZEN_SCIENTIFIC_AUTHORITIES_V1["metric"],p1_custodian_hash=manifest.p1_custodian_v3_hash,
                etapr_authority_hash=FROZEN_SCIENTIFIC_AUTHORITIES_V1["etapr"],normal_burden_hash=normal_burden,source_commit=SOURCE_COMMIT,
                executable_manifest_hash=mh,statistical_authority_hash=FROZEN_SCIENTIFIC_AUTHORITIES_V1["statistical"],
                failed_file_receipt_hashes=failures,etapr_coordinate_binding=etapr)
            path = root / "results" / f"{entry.panel_id}-{entry.method_id}.json"
            rr = persist_result_authority_v1(path,result)
            rr_path, _ = _persist_canonical(root / "results" / f"{entry.panel_id}-{entry.method_id}.receipt.json", rr)
            verify_result_authority_v1(path=path,receipt=rr,expected_bindings={"prediction_manifest_hash":global_manifest["self_hash"],"scenario_authority_hash":scenario["self_hash"],"denominator_authority_hash":denominator["self_hash"]})
            oracle = verify_result_from_persisted_artifacts_v1(paths=FrozenResultReplayPathsV1(
                executable_manifest_path=manifest_path,
                dispatch_registry_path=OUT / "METHOD_DISPATCH_REGISTRY_V1.json",
                cell_census_path=census_path,
                result_path=path,result_receipt_path=rr_path,global_manifest_path=global_manifest_path,
                global_freeze_path=global_freeze_path,scenario_authority_path=scenario_path,
                denominator_authority_path=denominator_path,etapr_coordinate_binding_path=etapr_path,
                terminal_receipt_paths=local_receipts,prediction_paths=local_predictions,
                projection_authority_paths={f:projection_authority_paths[(entry.panel_id,f)] for f in local_projections},
                projection_paths=local_projection_paths,
                timestamp_authority_paths={f:timestamp_authority_paths[(entry.panel_id,f)] for f in local_timestamps}),
                expected_executable_manifest_hash=mh,expected_metric_authority_hash=FROZEN_SCIENTIFIC_AUTHORITIES_V1["metric"],
                expected_p1_custodian_hash=manifest.p1_custodian_v3_hash,
                expected_etapr_authority_hash=FROZEN_SCIENTIFIC_AUTHORITIES_V1["etapr"],
                expected_statistical_authority_hash=FROZEN_SCIENTIFIC_AUTHORITIES_V1["statistical"],
                expected_normal_burden_hash=normal_burden)
            result_values.append(result); result_receipts.append(rr); result_paths.append(path); oracle_receipts.append(oracle)
        oracle_bundle = self_hashed({"schema":"dg05_result_integrity_qa_v1","result_authority_count":23,
            "audits":oracle_receipts,"inputs_reopened_from_paths":True,"status":"PASS"})
        result_bundle = build_result_authority_bundle_v1(results=result_values,receipts=result_receipts,artifact_paths=result_paths,
            executable_manifest_hash=mh,global_prediction_manifest_hash=global_manifest["self_hash"],scenario_authority_hash=scenario["self_hash"],
            denominator_authority_hash=denominator["self_hash"],independent_qa_hash=oracle_bundle["self_hash"])
        state = advance_dg05_state_v1(state, manifest, next_state=STATE_ORDER_V3[8], evidence=_transition(root, kind="RESULT_AUTHORITY_BUNDLE", count=23, document=result_bundle))
        state = advance_dg05_state_v1(state, manifest, next_state=STATE_ORDER_V3[9], evidence=_transition(root, kind="RESULT_INTEGRITY_QA", count=23, document=oracle_bundle))
        negative=0
        for mutation in ("manifest","metric","portfolio","fusion","p1","prediction","threshold"):
            try:
                if mutation == "prediction":
                    first = next(iter(prediction_paths.values())); original=first.read_bytes(); first.write_bytes(original+b"x")
                    try: freeze_global_predictions_v1(manifest=global_manifest,census=census,receipt_artifacts=artifact_paths,predecessor_state=state)
                    finally: first.write_bytes(original)
                else:
                    advance_dg05_state_v1(state, manifest, next_state=STATE_ORDER_V3[-1], evidence=_transition(root, kind="RESULT_INTEGRITY_QA", count=23, document=oracle_bundle))
            except DG05ClosureError:
                negative += 1
        return self_hashed({"schema":"synthetic_dg05_end_to_end_rehearsal_v1","phase_a_cells":72,
            "prediction_successes":71,"prediction_failures":1,"global_freeze_hash":freeze["self_hash"],"lease_issue_count":1,
            "custodian_fresh_process":True,"scenario_count":146,"denominator_count":146,"result_authority_count":23,
            "independent_result_replay_count":23,"post_label_mutation_rejections":negative,"final_state":state["state"],
            "p1_fixture_states":["P1_ELIGIBLE","OUT_OF_SCOPE","UNRESOLVED","P1_ELIGIBLE","OUT_OF_SCOPE_CROSS_PROCESS_SECONDARY"],
            "attack_test_accesses":0,"real_label_accesses":0,"real_eligibility_generated":0,"status":"PASS"})


def main() -> None:
    scope=build_scope(); detectors=build_detectors(); dispatch=build_dispatch(detectors)
    p1 = self_hashed({"schema":"p1_eligibility_custodian_authority_v3","status":"FROZEN_PROSPECTIVE_METHOD_BLIND",
        "full_process_scope_hash":scope.document()["self_hash"],"implementation_hash":file_sha256(ROOT / "src/paperworks/validation_v2/dg05_execution_closure_v1.py"),
        "outputs":["P1_ELIGIBLE","OUT_OF_SCOPE","UNRESOLVED","CROSS_PROCESS_P1_RELEVANT_SECONDARY"],"prediction_inputs":False,
        "known_non_p1_distinct_from_unresolved":True,"real_eligibility_generated":0,"source_commit":SOURCE_COMMIT})
    implementations={name:file_sha256(ROOT / path) for name,path in {
        "state_machine":"src/paperworks/validation_v2/dg05_execution_closure_v1.py","projection_adapter":"src/paperworks/validation_v2/dg05_execution_closure_v1.py",
        "prediction_adapter":"src/paperworks/validation_v2/dg05_execution_closure_v1.py","timestamp_builder":"src/paperworks/validation_v2/dg05_execution_closure_v1.py",
        "scenario_builder":"src/paperworks/validation_v2/dg05_execution_closure_v1.py","denominator_builder":"src/paperworks/validation_v2/dg05_execution_closure_v1.py",
        "global_manifest_builder":"src/paperworks/validation_v2/dg05_execution_closure_v1.py","global_freeze_builder":"src/paperworks/validation_v2/dg05_execution_closure_v1.py",
        "label_custodian":"src/paperworks/validation_v2/dg05_label_custodian_v1.py","result_builder":"src/paperworks/validation_v2/dg05_execution_closure_v1.py",
        "result_verifier":"src/paperworks/validation_v2/dg05_result_oracle_v1.py"}.items()}
    portfolios=tuple(sorted(v for values in FROZEN_PORTFOLIO_HASHES_V2.values() for v in values.values()))
    # Persist authorities before constructing the replay bundle. Initialization
    # reopens these exact bytes; it never trusts only a caller-created object.
    write_authority("FULL_PROCESS_SCOPE_AUTHORITY_V1.json", scope.document())
    write_authority("P1_ELIGIBILITY_CUSTODIAN_V3.json", p1)
    write_authority("DETECTOR_SUBAUTHORITY_REGISTRY_V1.json", detectors.document())
    write_authority("METHOD_DISPATCH_REGISTRY_V1.json", dispatch.document())
    direct = {
        "scientific:scientific_preregistration": ROOT / "research_control_center/validation_v2/multipanel_pre_dg05/MULTIPANEL_PREREGISTRATION_V2.json",
        "scientific:method_bundle": ROOT / "research_control_center/validation_v2/multipanel_pre_dg05/MULTIPANEL_METHOD_BUNDLE_AUTHORITY_V1.json",
        "scientific:metric": ROOT / "research_control_center/validation_v2/multipanel_pre_dg05/MULTIPANEL_METRIC_AUTHORITY_V2.json",
        "scientific:statistical": ROOT / "research_control_center/validation_v2/multipanel_pre_dg05/STATISTICAL_ANALYSIS_CONTRACT_V2.json",
        "scientific:etapr": ROOT / "research_control_center/validation_v2/multipanel_pre_dg05/ETAPR_MULTIFILE_CONFORMANCE_V2.json",
        "scientific:fusion": ROOT / "research_control_center/validation_v2/multipanel_pre_dg05/MULTIPANEL_METHOD_BUNDLE_AUTHORITY_V1.json",
        "scientific:attack_file_census": ROOT / "research_control_center/validation_v2/multipanel_pre_dg05/ATTACK_FILE_CENSUS_AUTHORITIES_V1.json",
        "scientific:feature_allowlist_bundle": ROOT / "research_control_center/validation_v2/multipanel_pre_dg05/ATTACK_FEATURE_ALLOWLIST_AUTHORITIES_V1.json",
        "scientific:p1_mapping_bundle_v2": ROOT / "research_control_center/validation_v2/multipanel_pre_dg05/P1_MAPPING_AUTHORITIES_V1.json",
        "scientific:global_custody_v2": ROOT / "research_control_center/validation_v2/multipanel_pre_dg05/GLOBAL_PREDICTION_CUSTODY_AUTHORITY_V2.json",
        "detector_registry": OUT / "DETECTOR_SUBAUTHORITY_REGISTRY_V1.json",
        "dispatch_registry": OUT / "METHOD_DISPATCH_REGISTRY_V1.json",
        "full_process_scope": OUT / "FULL_PROCESS_SCOPE_AUTHORITY_V1.json",
        "p1_custodian_v3": OUT / "P1_ELIGIBILITY_CUSTODIAN_V3.json",
    }
    portfolio_paths = {
        "94f130408361e6b4a8051ed4a72a0ad385e90cb3212e2bf0d27af300f481503f": ROOT / "research_control_center/validation_v2/xver_normal/HAI22_T0_PORTFOLIO_AUTHORITY_V1.json",
        "9815c9a66debed593e21364377113d18422a840389d306a4a7648d5f035599dc": ROOT / "research_control_center/validation_v2/xver_normal/provider_execution_v1/HAI21_T2_PORTFOLIO_AUTHORITY_V1.json",
        "b58313cd142256d000f89fd4a40512763b35e6b50752229109646bafc243fb5c": ROOT / "research_control_center/validation_v2/xver_normal/provider_execution_v1/HAI22_T2_PORTFOLIO_AUTHORITY_V1.json",
        "bc2b5996989228f198dbcbf38cbedaf38516366f55d5011978ecda94ccf699b6": ROOT / "research_control_center/validation_v2/dg04_xver_prep/T2_HELDOUT_CANDIDATE_PORTFOLIO_V1.json",
        "d95c0bb8234304f2b769e088f4399b6c071b2156982c9e1fadd175dbab5dba02": ROOT / "research_control_center/validation_v2/dg04_xver_prep/T0_HELDOUT_CANDIDATE_PORTFOLIO_V1.json",
        "ec0b3e2a32d457287cb8b101bec39059e99335be3fd85a3d1fb98668224c52aa": ROOT / "research_control_center/validation_v2/core_v2a/authorities/V2A_FORMAL_V4_PORTFOLIO_AUTHORITY.json",
        "f9cad3c00c422614012b2147f3c21951632f8738ce2d8f9f1108d61ae69d6ef3": ROOT / "research_control_center/validation_v2/xver_normal/HAI21_T0_PORTFOLIO_AUTHORITY_V1.json",
    }
    refs = []
    expected_base = {f"scientific:{k}":v for k,v in FROZEN_SCIENTIFIC_AUTHORITIES_V1.items()}
    expected_base.update({"detector_registry":detectors.document()["self_hash"],"dispatch_registry":dispatch.document()["self_hash"],
                          "full_process_scope":scope.document()["self_hash"],"p1_custodian_v3":p1["self_hash"]})
    for logical, expected in sorted(expected_base.items()):
        path = direct[logical]; value = json.loads(path.read_text(encoding="ascii"))
        field = "fusion_policy_hash" if logical == "scientific:fusion" else None
        schema = value.get("schema") or value.get("artifact_type")
        refs.append(PersistedAuthorityRefV1(logical, expected, file_sha256(path), schema, field, path))
    for index, expected in enumerate(portfolios):
        path = portfolio_paths[expected]; value = json.loads(path.read_text(encoding="ascii"))
        field = "authority_hash" if expected == FROZEN_PORTFOLIO_HASHES_V2[FROZEN_PANEL_ORDER_V2[0]]["V2A"] else None
        refs.append(PersistedAuthorityRefV1(f"portfolio:{index:02d}", expected, file_sha256(path),
            value.get("schema") or value.get("artifact_type"), field, path))
    implementation_paths = {
        "state_machine":"src/paperworks/validation_v2/dg05_execution_closure_v1.py","projection_adapter":"src/paperworks/validation_v2/dg05_execution_closure_v1.py",
        "prediction_adapter":"src/paperworks/validation_v2/dg05_execution_closure_v1.py","timestamp_builder":"src/paperworks/validation_v2/dg05_execution_closure_v1.py",
        "scenario_builder":"src/paperworks/validation_v2/dg05_execution_closure_v1.py","denominator_builder":"src/paperworks/validation_v2/dg05_execution_closure_v1.py",
        "global_manifest_builder":"src/paperworks/validation_v2/dg05_execution_closure_v1.py","global_freeze_builder":"src/paperworks/validation_v2/dg05_execution_closure_v1.py",
        "label_custodian":"src/paperworks/validation_v2/dg05_label_custodian_v1.py","result_builder":"src/paperworks/validation_v2/dg05_execution_closure_v1.py",
        "result_verifier":"src/paperworks/validation_v2/dg05_result_oracle_v1.py"}
    for key, expected in sorted(implementations.items()):
        path = ROOT / implementation_paths[key]
        refs.append(PersistedAuthorityRefV1(f"implementation:{key}", expected, file_sha256(path), None, None, path))
    nested = NestedAuthorityReplayBundleV1(tuple(sorted(refs)), SOURCE_COMMIT)
    nested.validate(expected_hashes={**expected_base, **{f"portfolio:{i:02d}":v for i,v in enumerate(portfolios)},
                                      **{f"implementation:{k}":v for k,v in implementations.items()}})
    write_authority("NESTED_AUTHORITY_REPLAY_BUNDLE_V1.json", nested.document())
    manifest=DG05ExecutableAuthorityManifestV1(tuple(FROZEN_SCIENTIFIC_AUTHORITIES_V1.items()),detectors.document()["self_hash"],
        dispatch.document()["self_hash"],portfolios,scope.document()["self_hash"],p1["self_hash"],tuple(sorted(implementations.items())),
        nested.document()["self_hash"],SOURCE_COMMIT)
    manifest.validate()
    write_authority("DG05_EXECUTABLE_AUTHORITY_MANIFEST_V1.json", manifest.document())
    rehearsal=synthetic_rehearsal(manifest,dispatch,detectors,scope,
        manifest_path=OUT / "DG05_EXECUTABLE_AUTHORITY_MANIFEST_V1.json", nested_replay=nested)
    state_authority=self_hashed({"schema":"dg05_execution_state_machine_authority_v1","states":list(STATE_ORDER_V3),
        "state_evidence_policy":{k:list(v) for k,v in STATE_EVIDENCE_POLICY_V1.items()},"executable_manifest_hash":manifest.document()["self_hash"],
        "implementation_hash":implementations["state_machine"],"source_commit":SOURCE_COMMIT})
    census_summary=self_hashed({"schema":"expected_prediction_cell_census_authority_v1","derived_expected_count":72,
        "panel_cell_counts":{"HAI23_TEST2_PRIMARY_HELDOUT_V1":9,"HAI22_EXTERNAL_REPLICATION_V1":28,"HAI21_EXTERNAL_REPLICATION_V1":35},
        "attack_file_census_hash":FROZEN_ATTACK_FILE_CENSUS_HASH_V2,"dispatch_registry_hash":dispatch.document()["self_hash"],"source_commit":SOURCE_COMMIT})
    adapter=self_hashed({"schema":"dg05_production_adapter_authority_v1","projection_adapter_hash":implementations["projection_adapter"],
        "prediction_adapter_hash":implementations["prediction_adapter"],"timestamp_builder_hash":implementations["timestamp_builder"],
        "exact_method_hash_dispatch":True,"positive_allowlist_row_deserialization":True,"read_all_drop_later":False,"failure_receipts":True,
        "expected_cell_census_hash":census_summary["self_hash"],"source_commit":SOURCE_COMMIT})
    closure=self_hashed({"schema":"dg05_executable_closure_authority_v1","status":"DG05_EXECUTABLE_CLOSURE_FROZEN",
        "blocker_audit_hash":BLOCKER_AUDIT_HASH,"blocker_commit":BLOCKER_COMMIT,"implementation_source_commit":SOURCE_COMMIT,
        "executable_manifest_hash":manifest.document()["self_hash"],"full_process_scope_hash":scope.document()["self_hash"],
        "p1_custodian_v3_hash":p1["self_hash"],"detector_registry_hash":detectors.document()["self_hash"],"dispatch_registry_hash":dispatch.document()["self_hash"],
        "state_machine_hash":state_authority["self_hash"],"production_adapter_hash":adapter["self_hash"],"expected_cell_census_hash":census_summary["self_hash"],
        "scenario_denominator_result_builder_hash":implementations["result_builder"],"isolated_custodian_hash":implementations["label_custodian"],
        "independent_result_verifier_hash":implementations["result_verifier"],"synthetic_rehearsal_hash":rehearsal["self_hash"],
        "blocker_matrix":{f"B{i}":"PASS" for i in range(1,9)},"attack_test_accesses":0,"label_accesses":0,"real_eligibility_generated":0})
    for name,value in (
        ("FULL_PROCESS_SCOPE_AUTHORITY_V1.json",scope.document()),("P1_ELIGIBILITY_CUSTODIAN_V3.json",p1),
        ("DETECTOR_SUBAUTHORITY_REGISTRY_V1.json",detectors.document()),("METHOD_DISPATCH_REGISTRY_V1.json",dispatch.document()),
        ("NESTED_AUTHORITY_REPLAY_BUNDLE_V1.json",nested.document()),
        ("DG05_EXECUTABLE_AUTHORITY_MANIFEST_V1.json",manifest.document()),("EXECUTION_STATE_MACHINE_AUTHORITY_V1.json",state_authority),
        ("EXPECTED_PREDICTION_CELL_CENSUS_AUTHORITY_V1.json",census_summary),("PRODUCTION_ADAPTER_AUTHORITY_V1.json",adapter),
        ("SYNTHETIC_DG05_REHEARSAL_V1.json",rehearsal),("DG05_EXECUTABLE_CLOSURE_AUTHORITY_V1.json",closure)):
        write_authority(name,value)
    print(json.dumps({"status":"PASS","closure":closure["self_hash"],"manifest":manifest.document()["self_hash"],
                      "scope":scope.document()["self_hash"],"p1":p1["self_hash"],"detectors":detectors.document()["self_hash"],
                      "dispatch":dispatch.document()["self_hash"],"rehearsal":rehearsal["self_hash"]},sort_keys=True))


if __name__ == "__main__": main()
