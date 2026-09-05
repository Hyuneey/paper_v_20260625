from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

from paperworks.validation_v2.dg05_label_custodian_v2 import (
    CustodianV2Error,
    canonical_bytes_v2,
    consume_and_extract_v2,
    self_hashed_v2,
)
from paperworks.validation_v2.dg05_normal_burden_replay_v1 import (
    NormalBurdenReplayError,
    replay_method_normal_burden_v1,
)
from paperworks.validation_v2.dg05_production_chain_v1 import (
    DG05ProductionChainError,
    build_production_release_manifest_v1,
    canonical_bytes_v1,
    derive_runtime_census_strict_v1,
    file_sha256_v1,
    initialize_production_release_v1,
    launch_custodian_fresh_process_v2,
    scenario_hit_any_interval_v1,
    self_hashed_v1,
    validate_strict_one_second_coordinates_v1,
    REQUIRED_IMPLEMENTATION_ROLES_V1,
    REQUIRED_NESTED_AUTHORITY_ROLES_V1,
)
from paperworks.validation_v2.dg05_execution_closure_v1 import FROZEN_METHOD_IDS_BY_PANEL_V1
from paperworks.validation_v2.dg05_upstream_lineage_verifier_v1 import (
    DG05UpstreamVerifierError,
    UpstreamPanelReplayPathsV1,
    reconstruct_metric_primitive_from_upstream_v1,
    verify_asserted_primitive_from_upstream_v1,
)


ROOT = Path(__file__).resolve().parents[1]
H = "a" * 64
G = "b" * 40
PANELS = {
    "HAI23_TEST2_PRIMARY_HELDOUT_V1": "23.05",
    "HAI22_EXTERNAL_REPLICATION_V1": "22.04",
    "HAI21_EXTERNAL_REPLICATION_V1": "21.03",
}


def persist(path: Path, value: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes_v1(value) + b"\n")
    return path


class ProductionChainClosureTests(unittest.TestCase):
    def _predecessor(self, root: Path):
        manifest = self_hashed_v1({"schema": "dg05_executable_authority_manifest_v3", "name": "historical-v3"})
        closure = self_hashed_v1(
            {
                "schema": "dg05_executable_closure_authority_v3",
                "executable_manifest_hash": manifest["self_hash"],
            }
        )
        return persist(root / "v3-manifest.json", manifest), persist(root / "v3-closure.json", closure)

    def test_release_root_is_exact_and_predecessor_hash_cannot_substitute(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            predecessor_manifest, predecessor_closure = self._predecessor(root)
            implementation = ROOT / "src/paperworks/validation_v2/dg05_production_chain_v1.py"
            release = build_production_release_manifest_v1(
                repository_root=ROOT,
                predecessor_v3_manifest_path=predecessor_manifest,
                predecessor_v3_closure_path=predecessor_closure,
                implementation_paths={name: implementation for name in REQUIRED_IMPLEMENTATION_ROLES_V1},
                nested_authority_hashes={name: H for name in REQUIRED_NESTED_AUTHORITY_ROLES_V1},
                semantic_binding_status="APPROVED",
                semantic_binding_hash=H,
                normal_burden_source_status="COMPLETE",
                normal_burden_source_registry_hash=H,
                source_commit=G,
            )
            release_path = persist(root / "release.json", release)
            state = initialize_production_release_v1(
                release_manifest_path=release_path,
                repository_root=ROOT,
                predecessor_v3_manifest_path=predecessor_manifest,
                predecessor_v3_closure_path=predecessor_closure,
                approved_release_hash=release["self_hash"],
                authority_mode="SYNTHETIC_REHEARSAL",
            )
            self.assertEqual(state["release_manifest_hash"], release["self_hash"])
            self.assertNotEqual(state["release_manifest_hash"], release["predecessor_v3_manifest_hash"])
            with self.assertRaisesRegex(DG05ProductionChainError, "EXACT_SYNTHETIC_RELEASE_HASH_REQUIRED"):
                initialize_production_release_v1(
                    release_manifest_path=release_path,
                    repository_root=ROOT,
                    predecessor_v3_manifest_path=predecessor_manifest,
                    predecessor_v3_closure_path=predecessor_closure,
                    approved_release_hash=release["predecessor_v3_manifest_hash"],
                    authority_mode="SYNTHETIC_REHEARSAL",
                )

    def _custodian_fixture(self, root: Path):
        incoming, outgoing, forbidden = root / "incoming", root / "outgoing", root / "predictions"
        incoming.mkdir(); outgoing.mkdir(); forbidden.mkdir()
        sources = []
        bindings = []
        nominal = {}
        for index, (panel, version) in enumerate(PANELS.items()):
            source_id = f"SOURCE-{version}"
            official = sha256(source_id.encode()).hexdigest()
            file_id = f"file-{index}.csv"
            record = {
                "panel_id": panel,
                "dataset_version": version,
                "file_id": file_id,
                "scenario_id": f"S-{index}",
                "closed_intervals": [["2026-01-01T00:00:00", "2026-01-01T00:00:01"]],
                "attacked_identities": ["P1_SYNTHETIC"],
                "explicit_affected_processes": [],
            }
            source_path = incoming / f"{source_id}.json"
            source_path.write_bytes(canonical_bytes_v2({"schema": "synthetic_raw_official_scenario_fixture_v2", "records": [record]}) + b"\n")
            sources.append(
                {
                    "source_id": source_id,
                    "path": str(source_path.resolve()),
                    "byte_hash": file_sha256_v1(source_path),
                    "official_source_hash": official,
                    "dataset_version": version,
                    "source_format": "SYNTHETIC_JSON_V2",
                    "adapter_id": "SYNTHETIC_OFFICIAL_SCENARIO_FIXTURE_V2",
                }
            )
            bindings.append(
                {
                    "source_id": source_id,
                    "panel_id": panel,
                    "dataset_version": version,
                    "file_id": file_id,
                    "physical_file_authority_hash": sha256(f"physical-{index}".encode()).hexdigest(),
                    "timestamp_authority_hash": sha256(f"timestamp-{index}".encode()).hexdigest(),
                    "official_source_hash": official,
                }
            )
            nominal[panel] = 1
        module_path = ROOT / "src/paperworks/validation_v2/dg05_label_custodian_v2.py"
        policy = self_hashed_v2(
            {
                "schema": "custodian_resource_policy_authority_v2",
                "input_root": str(incoming.resolve()),
                "output_root": str(outgoing.resolve()),
                "forbidden_roots": [str(forbidden.resolve())],
                "approved_sources": sources,
                "executable_manifest_hash": H,
                "scenario_adapter_implementation_hash": file_sha256_v1(module_path),
                "resource_policy_contract_hash": H,
                "source_commit": G,
            }
        )
        policy_path = persist(root / "policy.json", policy)
        token = "single-use-token"
        freeze_state = self_hashed_v1({
            "schema": "dg05_production_chain_state_v1",
            "state": "GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED",
            "release_manifest_hash": H,
            "global_prediction_freeze_hash": H,
            "authority_mode": "SYNTHETIC_REHEARSAL",
        })
        lease = self_hashed_v2(
            {
                "schema": "single_use_label_scenario_lease_v3",
                "token_hash": sha256(token.encode()).hexdigest(),
                "global_freeze_hash": H,
                "state_hash": freeze_state["self_hash"],
                "executable_manifest_hash": H,
                "resource_policy_hash": policy["self_hash"],
                "issue_count": 1,
                "consume_limit": 1,
            }
        )
        request = {
            "schema": "isolated_label_scenario_custodian_request_v2",
            "opaque_lease": token,
            "lease_receipt": lease,
            "global_freeze_hash": H,
            "predecessor_state_hash": None,
            "lease_issue_predecessor_hash": freeze_state["self_hash"],
            "executable_manifest_hash": H,
            "approved_source_ids": sorted(source["source_id"] for source in sources),
            "approved_output_name": "scenario-output.json",
            "public_authority_hashes": [H],
            "resource_policy_hash": policy["self_hash"],
            "allowed_scenario_bindings": bindings,
            "authority_mode": "SYNTHETIC_REHEARSAL",
            "nominal_counts": nominal,
        }
        predecessor = self_hashed_v1({
            "schema": "dg05_production_chain_state_v1",
            "state": "LABEL_SCENARIO_LEASE_ISSUED",
            "release_manifest_hash": H,
            "global_prediction_freeze_hash": H,
            "authority_mode": "SYNTHETIC_REHEARSAL",
            "lease_issue_predecessor_hash": freeze_state["self_hash"],
            "lease_receipt_hash": lease["self_hash"],
            "lease_token_hash": lease["token_hash"],
        })
        request["predecessor_state_hash"] = predecessor["self_hash"]
        request_path = persist(root / "request.json", request)
        return request_path, policy_path, predecessor, outgoing, policy

    def test_fresh_process_multisource_and_token_keyed_single_consume(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            request, policy, predecessor, outgoing, policy_doc = self._custodian_fixture(root)
            launcher = ROOT / "scripts/run_dg05_label_custodian_v2.py"
            receipt = launch_custodian_fresh_process_v2(
                request_path=request,
                resource_policy_path=policy,
                launcher_path=launcher,
                repository_root=ROOT,
                expected_launcher_hash=file_sha256_v1(launcher),
                expected_resource_policy_hash=policy_doc["self_hash"],
                expected_custodian_implementation_hash=policy_doc["scenario_adapter_implementation_hash"],
                predecessor_state=predecessor,
                expected_global_freeze_hash=H,
                expected_release_manifest_hash=H,
            )
            self.assertNotEqual(receipt["custodian_pid"], receipt["custodian_parent_pid"])
            self.assertEqual(receipt["isolation_mechanism"], "FRESH_PROCESS_PLUS_APPLICATION_PATH_CAPABILITY_GUARDS")
            self.assertFalse(receipt["os_sandbox_claimed"])
            output = json.loads((outgoing / "scenario-output.json").read_text())
            self.assertEqual(len(output["records"]), 3)
            # Changing the caller-controlled output name cannot reissue the same token.
            changed = json.loads(request.read_text())
            changed["approved_output_name"] = "different-output.json"
            persist(request, changed)
            with self.assertRaisesRegex(DG05ProductionChainError, "SINGLE_CONSUME_OR_APPEND_ONLY_CONFLICT"):
                launch_custodian_fresh_process_v2(
                    request_path=request,
                    resource_policy_path=policy,
                    launcher_path=launcher,
                    repository_root=ROOT,
                    expected_launcher_hash=file_sha256_v1(launcher),
                    expected_resource_policy_hash=policy_doc["self_hash"],
                    expected_custodian_implementation_hash=policy_doc["scenario_adapter_implementation_hash"],
                    predecessor_state=predecessor,
                    expected_global_freeze_hash=H,
                    expected_release_manifest_hash=H,
                )

    def test_premature_custodian_launch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            request, policy, predecessor, _outgoing, policy_doc = self._custodian_fixture(root)
            body = {key: value for key, value in predecessor.items() if key != "self_hash"}
            body["state"] = "PREDICTIONS_IN_PROGRESS_LABEL_LOCKED"
            premature = self_hashed_v1(body)
            launcher = ROOT / "scripts/run_dg05_label_custodian_v2.py"
            with self.assertRaisesRegex(DG05ProductionChainError, "LABEL_LEASE_ISSUED_PREDECESSOR_REQUIRED"):
                launch_custodian_fresh_process_v2(
                    request_path=request,
                    resource_policy_path=policy,
                    launcher_path=launcher,
                    repository_root=ROOT,
                    expected_launcher_hash=file_sha256_v1(launcher),
                    expected_resource_policy_hash=policy_doc["self_hash"],
                    expected_custodian_implementation_hash=policy_doc["scenario_adapter_implementation_hash"],
                    predecessor_state=premature,
                    expected_global_freeze_hash=H,
                    expected_release_manifest_hash=H,
                )

    def test_custodian_rejects_cross_mode_adapter_before_consume(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            request_path, policy_path, _predecessor, outgoing, _policy = self._custodian_fixture(root)
            request = json.loads(request_path.read_text())
            request["authority_mode"] = "PRODUCTION"
            with self.assertRaisesRegex(CustodianV2Error, "SOURCE_ADAPTER_AUTHORITY_MODE_MISMATCH"):
                consume_and_extract_v2(request, resource_policy_authority_path=policy_path)
            self.assertEqual(list(outgoing.iterdir()), [])

    def test_custodian_source_failure_consumes_lease_and_cannot_replay(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            request_path, policy_path, _predecessor, outgoing, _policy = self._custodian_fixture(root)
            request = json.loads(request_path.read_text())
            source_path = next((root / "incoming").glob("*.json"))
            source_path.write_bytes(source_path.read_bytes() + b"x")
            with self.assertRaisesRegex(CustodianV2Error, "LEASED_SOURCE_BYTE_HASH_MISMATCH"):
                consume_and_extract_v2(request, resource_policy_authority_path=policy_path)
            self.assertEqual(len(list(outgoing.glob("lease-consumed-*.json"))), 1)
            with self.assertRaisesRegex(CustodianV2Error, "SINGLE_CONSUME_OR_APPEND_ONLY_CONFLICT"):
                consume_and_extract_v2(request, resource_policy_authority_path=policy_path)

    def test_launcher_rejects_release_and_lease_substitution(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            request, policy, predecessor, _outgoing, policy_doc = self._custodian_fixture(root)
            launcher = ROOT / "scripts/run_dg05_label_custodian_v2.py"
            with self.assertRaisesRegex(DG05ProductionChainError, "GLOBAL_FREEZE_RELEASE_BINDING_REQUIRED"):
                launch_custodian_fresh_process_v2(
                    request_path=request,
                    resource_policy_path=policy,
                    launcher_path=launcher,
                    repository_root=ROOT,
                    expected_launcher_hash=file_sha256_v1(launcher),
                    expected_resource_policy_hash=policy_doc["self_hash"],
                    expected_custodian_implementation_hash=policy_doc["scenario_adapter_implementation_hash"],
                    predecessor_state=predecessor,
                    expected_global_freeze_hash=H,
                    expected_release_manifest_hash="c" * 64,
                )
            changed = json.loads(request.read_text())
            changed["lease_receipt"]["state_hash"] = "c" * 64
            changed["lease_receipt"] = self_hashed_v2({key: value for key, value in changed["lease_receipt"].items() if key != "self_hash"})
            persist(request, changed)
            with self.assertRaisesRegex(DG05ProductionChainError, "CUSTODIAN_REQUEST_FREEZE_MISMATCH"):
                launch_custodian_fresh_process_v2(
                    request_path=request,
                    resource_policy_path=policy,
                    launcher_path=launcher,
                    repository_root=ROOT,
                    expected_launcher_hash=file_sha256_v1(launcher),
                    expected_resource_policy_hash=policy_doc["self_hash"],
                    expected_custodian_implementation_hash=policy_doc["scenario_adapter_implementation_hash"],
                    predecessor_state=predecessor,
                    expected_global_freeze_hash=H,
                    expected_release_manifest_hash=H,
                )

    def test_plural_interval_hit_and_endpoint_need_not_be_sampled(self) -> None:
        self.assertTrue(
            scenario_hit_any_interval_v1(
                alarm_timestamps=["2026-01-01T00:00:04"],
                closed_intervals=[
                    ["2026-01-01T00:00:00.500000", "2026-01-01T00:00:01.500000"],
                    ["2026-01-01T00:00:03.500000", "2026-01-01T00:00:04.500000"],
                ],
            )
        )
        self.assertFalse(
            scenario_hit_any_interval_v1(
                alarm_timestamps=["2026-01-01T00:00:02"],
                closed_intervals=[
                    ["2026-01-01T00:00:00.500000", "2026-01-01T00:00:01.500000"],
                    ["2026-01-01T00:00:03.500000", "2026-01-01T00:00:04.500000"],
                ],
            )
        )

    def test_duplicate_and_gap_require_binding(self) -> None:
        with self.assertRaisesRegex(DG05ProductionChainError, "DUPLICATE_TIMESTAMP_BINDING_REQUIRED"):
            validate_strict_one_second_coordinates_v1(["2026-01-01T00:00:00", "2026-01-01T00:00:00"])
        with self.assertRaisesRegex(DG05ProductionChainError, "NON_UNIT_TIMESTAMP_GAP_BINDING_REQUIRED"):
            validate_strict_one_second_coordinates_v1(["2026-01-01T00:00:00", "2026-01-01T00:00:02"])

    def test_runtime_missing_is_not_zero_and_identities_are_separate(self) -> None:
        with self.assertRaisesRegex(DG05ProductionChainError, "EVIDENCE_MISSING"):
            derive_runtime_census_strict_v1([{"opportunities": 0, "pass": 0, "fail": 0, "abstain": 0, "system_errors": 0}])
        trace = {
            "opportunities": 4,
            "pass": 1,
            "fail": 1,
            "abstain": 2,
            "system_errors": 0,
            "file_id": "F0",
            "rule_alarm_rows": [9],
            "per_rule_runtime": [
                {"rule_id": "R0", "source_id": "S0", "opportunities": 0, "pass": 0, "fail": 0, "abstain": 0, "system_errors": 0},
                {"rule_id": "R1", "source_id": "S1", "opportunities": 2, "pass": 0, "fail": 0, "abstain": 2, "system_errors": 0},
                {"rule_id": "R2", "source_id": "S2", "opportunities": 1, "pass": 1, "fail": 0, "abstain": 0, "system_errors": 0},
                {"rule_id": "R3", "source_id": "S3", "opportunities": 1, "pass": 0, "fail": 1, "abstain": 0, "system_errors": 0},
            ],
        }
        result = derive_runtime_census_strict_v1([trace])
        self.assertEqual(result["configured_rules"], ["R0", "R1", "R2", "R3"])
        self.assertEqual(result["formed_rules"], ["R1", "R2", "R3"])
        self.assertEqual(result["evaluated_rules"], ["R2", "R3"])
        self.assertEqual(result["alarming_rules"], ["R3"])

    def test_runtime_census_rejects_contradictory_or_missing_evidence(self) -> None:
        with self.assertRaisesRegex(DG05ProductionChainError, "EVIDENCE_MISSING"):
            derive_runtime_census_strict_v1([])
        invalid = {
            "file_id": "F0", "opportunities": 1, "pass": 0, "fail": 1,
            "abstain": 0, "system_errors": 0, "rule_alarm_rows": [],
            "per_rule_runtime": [
                {"rule_id": "R0", "source_id": "S0", "opportunities": 1,
                 "pass": 0, "fail": 1, "abstain": 0, "system_errors": 0}
            ],
        }
        with self.assertRaisesRegex(DG05ProductionChainError, "RUNTIME_ALARM_FAIL_COUNT_MISMATCH"):
            derive_runtime_census_strict_v1([invalid])
        invalid["rule_alarm_rows"] = [3]
        invalid["per_rule_runtime"][0]["fail"] = -1
        with self.assertRaisesRegex(DG05ProductionChainError, "INVALID_PER_RULE_RUNTIME_COUNT"):
            derive_runtime_census_strict_v1([invalid])

    def test_normal_burden_replayed_and_source_mutation_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            prediction = {"schema": "dense_boolean_normal_prediction_v1", "alarms": [False, True, True, False, True]}
            timestamps = {"schema": "normal_timestamp_vector_v1", "timestamps": [f"2026-01-01T00:00:0{i}" for i in range(5)]}
            coverage = {"schema": "normal_method_coverage_v1", "component_id": "C0", "opportunities": 5, "evaluated": 4, "abstain": 1}
            paths = {
                "prediction": persist(root / "prediction.json", prediction),
                "timestamp": persist(root / "timestamp.json", timestamps),
                "coverage": persist(root / "coverage.json", coverage),
            }
            component = {
                "component_id": "C0",
                "panel_id": "HAI23_TEST2_PRIMARY_HELDOUT_V1",
                "method_id": "M1_T0_RULE_ONLY",
                "file_id": "normal-1",
                "prediction_byte_hash": file_sha256_v1(paths["prediction"]),
                "timestamp_byte_hash": file_sha256_v1(paths["timestamp"]),
                "coverage_byte_hash": file_sha256_v1(paths["coverage"]),
                "method_authority_hash": H,
                "physical_file_authority_hash": H,
                "authority_class": "GUARD_CONDITIONED_NORMAL",
            }
            registry = self_hashed_v1(
                {
                    "schema": "normal_burden_source_registry_v1",
                    "time_binding_status": "APPROVED",
                    "time_binding_hash": H,
                    "components": [component],
                }
            )
            result = replay_method_normal_burden_v1(
                source_registry=registry,
                prediction_paths={"C0": paths["prediction"]},
                timestamp_paths={"C0": paths["timestamp"]},
                coverage_paths={"C0": paths["coverage"]},
                approved_time_binding_hash=H,
            )
            method = result["methods"][0]
            self.assertEqual((method["false_seconds"], method["false_episodes"], method["exposure_seconds"]), (3, 2, 5))
            paths["prediction"].write_bytes(paths["prediction"].read_bytes() + b"x")
            with self.assertRaisesRegex(NormalBurdenReplayError, "SOURCE_ARTIFACT_BYTE_HASH_MISMATCH"):
                replay_method_normal_burden_v1(
                    source_registry=registry,
                    prediction_paths={"C0": paths["prediction"]},
                    timestamp_paths={"C0": paths["timestamp"]},
                    coverage_paths={"C0": paths["coverage"]},
                    approved_time_binding_hash=H,
                )

    def _upstream_fixture(self, root: Path):
        panel = "HAI21_EXTERNAL_REPLICATION_V1"
        file_id = "synthetic-file"
        projection = root / "projection.jsonl"
        projection.write_bytes(
            b'["timestamp","P1_X"]\n'
            b'["2026-01-01T00:00:00",1.0]\n'
            b'["2026-01-01T00:00:01",1.0]\n'
            b'["2026-01-01T00:00:02",1.0]\n'
        )
        receipts = []
        prediction_paths = {}
        trace_paths = {}
        methods = FROZEN_METHOD_IDS_BY_PANEL_V1[panel]
        for ordinal, method_id in enumerate(methods):
            cell_id = sha256(method_id.encode()).hexdigest()
            prediction = {
                "schema": "dense_boolean_prediction_v1",
                "cell_id": cell_id,
                "row_count": 3,
                "alarms": [False, method_id not in ("M0_PCA_SPE", "ISOLATION_FOREST"), False],
            }
            prediction_path = persist(root / f"{cell_id}.prediction.json", prediction)
            prediction_paths[cell_id] = prediction_path
            trace_status = "NONE"
            trace_hash = None
            if method_id not in ("M0_PCA_SPE", "ISOLATION_FOREST"):
                trace = self_hashed_v1(
                    {
                        "schema": "rule_trace_artifact_v2",
                        "cell_id": cell_id,
                        "prediction_hash": file_sha256_v1(prediction_path),
                        "file_id": file_id,
                        "opportunities": 1,
                        "pass": 0,
                        "fail": 1,
                        "abstain": 0,
                        "system_errors": 0,
                        "rule_alarm_rows": [1],
                        "per_rule_runtime": [
                            {"rule_id": f"R-{method_id}", "source_id": "P1_X", "opportunities": 1,
                             "pass": 0, "fail": 1, "abstain": 0, "system_errors": 0}
                        ],
                    }
                )
                trace_path = persist(root / f"{cell_id}.trace.json", trace)
                trace_paths[cell_id] = trace_path
                trace_status, trace_hash = "BOUND", file_sha256_v1(trace_path)
            receipts.append(
                self_hashed_v1(
                    {
                        "schema": "prediction_terminal_receipt_v1",
                        "cell_id": cell_id,
                        "panel_id": panel,
                        "file_id": file_id,
                        "method_id": method_id,
                        "status": "SUCCESS",
                        "projection_hash": file_sha256_v1(projection),
                        "row_count": 3,
                        "prediction_artifact_hash": file_sha256_v1(prediction_path),
                        "trace_status": trace_status,
                        "trace_artifact_hash": trace_hash,
                    }
                )
            )
        manifest = self_hashed_v1(
            {"schema": "global_prediction_manifest_v3", "executable_approval_manifest_hash": H,
             "receipts": receipts}
        )
        freeze = self_hashed_v1(
            {"schema": "global_prediction_freeze_v3", "manifest_hash": manifest["self_hash"],
             "executable_approval_manifest_hash": H}
        )
        scenario_record = self_hashed_v1(
            {"panel_id": panel, "scenario_id": "S1", "file_id": file_id,
             "closed_intervals": [["2026-01-01T00:00:00", "2026-01-01T00:00:02"]]}
        )
        scenario = self_hashed_v1(
            {"schema": "frozen_scenario_authority_v1", "global_freeze_hash": freeze["self_hash"],
             "records": [scenario_record]}
        )
        eligibility = self_hashed_v1(
            {"panel_id": panel, "scenario_id": "S1", "scenario_record_hash": scenario_record["self_hash"],
             "primary_status": "P1_ELIGIBLE"}
        )
        denominator = self_hashed_v1(
            {"schema": "denominator_authority_v1", "scenario_authority_hash": scenario["self_hash"],
             "records": [eligibility]}
        )
        normal_components = []
        normal_predictions = {}
        normal_timestamps = {}
        normal_coverages = {}
        for ordinal, method_id in enumerate(methods):
            component_id = f"N{ordinal}"
            pred = persist(root / f"{component_id}.normal-prediction.json",
                           {"schema": "dense_boolean_normal_prediction_v1", "alarms": [False, False, False]})
            stamp = persist(root / f"{component_id}.normal-timestamp.json",
                            {"schema": "normal_timestamp_vector_v1", "timestamps": [
                                "2026-02-01T00:00:00", "2026-02-01T00:00:01", "2026-02-01T00:00:02"]})
            coverage = persist(root / f"{component_id}.normal-coverage.json",
                               {"schema": "normal_method_coverage_v1", "component_id": component_id,
                                "opportunities": 3, "evaluated": 3, "abstain": 0})
            normal_predictions[component_id] = pred
            normal_timestamps[component_id] = stamp
            normal_coverages[component_id] = coverage
            normal_components.append(
                {"component_id": component_id, "panel_id": panel, "method_id": method_id,
                 "file_id": "normal-file", "prediction_byte_hash": file_sha256_v1(pred),
                 "timestamp_byte_hash": file_sha256_v1(stamp), "coverage_byte_hash": file_sha256_v1(coverage),
                 "method_authority_hash": H, "physical_file_authority_hash": H,
                 "authority_class": "GUARD_CONDITIONED_NORMAL"}
            )
        normal_registry = self_hashed_v1(
            {"schema": "normal_burden_source_registry_v1", "time_binding_status": "APPROVED",
             "time_binding_hash": H, "components": normal_components}
        )
        paths = UpstreamPanelReplayPathsV1(
            global_manifest_path=persist(root / "manifest.json", manifest),
            global_freeze_path=persist(root / "freeze.json", freeze),
            scenario_authority_path=persist(root / "scenario.json", scenario),
            denominator_authority_path=persist(root / "denominator.json", denominator),
            projection_paths={file_id: projection}, prediction_paths=prediction_paths,
            trace_paths=trace_paths,
            normal_source_registry_path=persist(root / "normal-registry.json", normal_registry),
            normal_prediction_paths=normal_predictions, normal_timestamp_paths=normal_timestamps,
            normal_coverage_paths=normal_coverages, asserted_primitive_path=root / "primitive.json",
        )
        return panel, paths

    def test_upstream_verifier_rejects_coherently_rehashed_primitive_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            panel, paths = self._upstream_fixture(root)
            primitive = reconstruct_metric_primitive_from_upstream_v1(
                panel_id=panel, paths=paths, expected_release_manifest_hash=H,
                approved_semantic_binding_hash=H)
            persist(paths.asserted_primitive_path, primitive)
            receipt = verify_asserted_primitive_from_upstream_v1(
                panel_id=panel, paths=paths, expected_release_manifest_hash=H,
                approved_semantic_binding_hash=H)
            self.assertEqual(receipt["status"], "PASS")
            body = {key: value for key, value in primitive.items() if key != "self_hash"}
            body["methods"]["M0_PCA_SPE"]["alarms_by_file"]["synthetic-file"] = [2]
            persist(paths.asserted_primitive_path, self_hashed_v1(body))
            with self.assertRaisesRegex(DG05UpstreamVerifierError, "DISAGREES_WITH_FROZEN_UPSTREAM"):
                verify_asserted_primitive_from_upstream_v1(
                    panel_id=panel, paths=paths, expected_release_manifest_hash=H,
                    approved_semantic_binding_hash=H)


if __name__ == "__main__":
    unittest.main()
