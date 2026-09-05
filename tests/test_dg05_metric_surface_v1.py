import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "artifacts/validation_v2/dg04_xver_prep/metric_source/af9e7aed35cfd160cbe0d04c8ec4c102502cb677"
DEPS = ROOT / "artifacts/validation_v2/dg04_xver_prep/metric_dependencies"
sys.path[:0] = [str(SOURCE), str(DEPS)]

from paperworks.validation_v2.dg05_execution_closure_v1 import FROZEN_METHOD_IDS_BY_PANEL_V1
from paperworks.validation_v2.dg05_metric_surface_v1 import (
    MetricSurfaceError,
    FROZEN_PANEL_ORDER,
    build_complete_metric_surface_v1,
    build_expected_result_surface_v1,
    build_metric_primitives_v1,
    build_metric_surface_contract_v1,
    canonical_bytes,
    persist_canonical_v1,
    result_surface_completeness_oracle_v1,
    self_hashed,
)
from paperworks.validation_v2.dg05_metric_surface_oracle_v1 import (
    MetricSurfaceOracleError,
    independent_supported_surface_ids_v1,
    verify_complete_metric_surface_from_paths_v1,
)
from paperworks.validation_v2.dg05_expected_surface_v1 import build_expected_result_surface_authority_v1
from paperworks.validation_v2.dg05_surface_completeness_v1 import (
    SurfaceCompletenessError,
    build_surface_support_declaration_v1,
    verify_static_surface_completeness_from_paths_v1,
)
from paperworks.validation_v2.etapr_exchange_v1 import OfficialEtaprV1
from paperworks.validation_v2.dg05_executable_v3 import (
    DG05ExecutableV3Error,
    initialize_dg05_executable_v3_preaccess,
    predecessor_v2_nested_repository_paths_v1,
)
from paperworks.validation_v2.dg05_connected_rehearsal_v3 import run_connected_synthetic_rehearsal_v3


H = "a" * 64
G = "b" * 40


def fixture(panel: str, *, no_scenarios: bool = False, incomplete: str | None = None):
    scenarios = [] if no_scenarios else [
        {"scenario_id": "S1", "file_id": "a.csv", "start": 2, "end": 4, "eligibility": "P1_ELIGIBLE",
         "scenario_authority_hash": "1" * 64, "eligibility_authority_hash": "2" * 64},
        {"scenario_id": "S2", "file_id": "a.csv", "start": 8, "end": 10, "eligibility": "P1_ELIGIBLE",
         "scenario_authority_hash": "3" * 64, "eligibility_authority_hash": "4" * 64},
        {"scenario_id": "S3", "file_id": "b.csv", "start": 3, "end": 5, "eligibility": "P1_ELIGIBLE",
         "scenario_authority_hash": "5" * 64, "eligibility_authority_hash": "6" * 64},
        {"scenario_id": "S4", "file_id": "b.csv", "start": 12, "end": 13, "eligibility": "OUT_OF_SCOPE",
         "scenario_authority_hash": "7" * 64, "eligibility_authority_hash": "8" * 64},
    ]
    alarms = {
        "M0_PCA_SPE": {"a.csv": [2], "b.csv": []},
        "M1_T0_RULE_ONLY": {"a.csv": [8, 9], "b.csv": [3]},
        "M2_T2_RULE_ONLY": {"a.csv": [8], "b.csv": [3, 5]},
        # Rule response S3 exists, but PCA+T0 recovers only S2.
        "M3_PCA_PLUS_T0": {"a.csv": [2, 8], "b.csv": []},
        # T2 responds to S2 and S3, but PCA+T2 recovers only S3.
        "M4_PCA_PLUS_T2": {"a.csv": [2], "b.csv": [3]},
        "ISOLATION_FOREST": {"a.csv": [4, 5], "b.csv": [17]},
        "ISOLATION_FOREST_PLUS_T2": {"a.csv": [4, 8], "b.csv": [3]},
        "V2A_RULE_ONLY_REFERENCE": {"a.csv": [10], "b.csv": []},
        "HISTORICAL_PCA_PLUS_V2A_CONTINUITY": {"a.csv": [2, 10], "b.csv": []},
    }
    methods = {}
    for ordinal, method in enumerate(FROZEN_METHOD_IDS_BY_PANEL_V1[panel]):
        values = alarms[method]
        traces = []
        if "RULE" in method or "PLUS" in method or method == "HISTORICAL_PCA_PLUS_V2A_CONTINUITY":
            traces = [{"opportunities": 10, "pass": 4, "fail": 3, "abstain": 2, "system_errors": 1,
                       "rule_ids": [f"R{ordinal}"], "physical_source_ids": [f"P1_S{ordinal}"],
                       "rule_alarm_episodes": 2}]
        methods[method] = {
            "status": "NOT_EVALUABLE_INCOMPLETE_PREDICTION_COVERAGE" if method == incomplete else "COMPLETE",
            "row_counts": {"a.csv": 20, "b.csv": 20}, "alarms_by_file": values,
            "normal_burden": {"authority_class": "GUARD_CONDITIONED_NORMAL" if "22" not in panel else "POST_FREEZE_NORMAL_AUDIT",
                              "opportunity_coverage": 1.0,
                              "components": [{"component_id": "normal-a", "false_seconds": ordinal,
                                              "false_episodes": min(ordinal, 2), "exposure_seconds": 3600,
                                              "abstain": 1, "opportunities": 100, "evaluated": 99}]},
            "runtime_traces": traces,
        }
    return build_metric_primitives_v1(panel_id=panel, dataset_version={FROZEN_PANEL_ORDER[0]: "23.05",
        FROZEN_PANEL_ORDER[1]: "22.04", FROZEN_PANEL_ORDER[2]: "21.03"}[panel], scenarios=scenarios,
        methods=methods, authority_hashes={"executable": H, "prediction_manifest": "c" * 64,
            "scenario": "d" * 64, "denominator": "e" * 64, "normal_burden": "f" * 64})


class MetricSurfaceV3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wrapper = OfficialEtaprV1(SOURCE)

    def test_contract_exact_surface_census_and_independent_support(self):
        contract = build_metric_surface_contract_v1(source_commit=G)
        expected = build_expected_result_surface_v1(contract)
        self.assertEqual(contract["required_surface_count"], 228)
        self.assertEqual(expected["surface_count"], 228)
        self.assertEqual(set(expected["surface_ids"]), set(independent_supported_surface_ids_v1()))
        self.assertEqual(len([v for v in contract["surfaces"] if v["metric_surface"] == "RULE_RUNTIME_CENSUS"]), 17)

    def test_static_completeness_oracle_is_preaccess_and_fails_on_omission(self):
        contract = build_metric_surface_contract_v1(source_commit=G)
        expected = build_expected_result_surface_authority_v1(metric_surface_contract_hash=contract["self_hash"])
        ids = independent_supported_surface_ids_v1()
        builder = build_surface_support_declaration_v1(role="PRODUCTION_BUILDER", surface_ids=list(ids), implementation_hash=H)
        verifier = build_surface_support_declaration_v1(role="INDEPENDENT_VERIFIER", surface_ids=list(ids), implementation_hash="b" * 64)
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            for name, value in (("contract", contract), ("expected", expected), ("builder", builder), ("verifier", verifier)):
                (root / f"{name}.json").write_bytes(canonical_bytes(value) + b"\n")
            audit = verify_static_surface_completeness_from_paths_v1(contract_path=root / "contract.json", expected_path=root / "expected.json",
                builder_support_path=root / "builder.json", verifier_support_path=root / "verifier.json")
            self.assertEqual((audit["status"], audit["data_access_capability"]), ("PASS", "PUBLIC_CONTRACTS_ONLY"))
            body = {k: v for k, v in verifier.items() if k != "self_hash"}; body["surface_ids"] = body["surface_ids"][:-1]
            body["surface_count"] -= 1; broken = self_hashed(body)
            (root / "verifier.json").write_bytes(canonical_bytes(broken) + b"\n")
            with self.assertRaises(SurfaceCompletenessError):
                verify_static_surface_completeness_from_paths_v1(contract_path=root / "contract.json", expected_path=root / "expected.json",
                    builder_support_path=root / "builder.json", verifier_support_path=root / "verifier.json")

    def test_all_panels_build_persist_and_independently_replay(self):
        contract = build_metric_surface_contract_v1(source_commit=G)
        results = []
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            persist_canonical_v1(root / "contract.json", contract)
            for index, panel in enumerate(FROZEN_PANEL_ORDER):
                primitive = fixture(panel)
                result = build_complete_metric_surface_v1(primitives=primitive, contract=contract,
                    executable_manifest_hash=H, wrapper=self.wrapper, source_commit=G)
                results.append(result)
                persist_canonical_v1(root / f"primitive-{index}.json", primitive)
                persist_canonical_v1(root / f"result-{index}.json", result)
                audit = verify_complete_metric_surface_from_paths_v1(primitive_path=root / f"primitive-{index}.json",
                    result_path=root / f"result-{index}.json", contract_path=root / "contract.json",
                    wrapper=self.wrapper, expected_executable_hash=H)
                self.assertEqual(audit["status"], "PASS")
            closure = result_surface_completeness_oracle_v1(contract=contract, result_documents=results,
                verifier_supported_surface_ids=independent_supported_surface_ids_v1())
            self.assertEqual((closure["status"], closure["expected_count"]), ("PASS", 228))

    def test_delay_recovery_pairing_and_runtime_distinctions(self):
        contract = build_metric_surface_contract_v1(source_commit=G)
        panel = FROZEN_PANEL_ORDER[0]
        result = build_complete_metric_surface_v1(primitives=fixture(panel), contract=contract,
            executable_manifest_hash=H, wrapper=self.wrapper, source_commit=G)
        rows = {v["surface_id"]: v for v in result["surfaces"]}
        delay = rows[f"{panel}|METHOD|M0_PCA_SPE|DETECTION_DELAY"]["payload"]
        self.assertEqual(delay, [{"scenario_id": "S1", "status": "PASS", "value": 0},
                                 {"scenario_id": "S2", "status": "NOT_DETECTED", "value": None},
                                 {"scenario_id": "S3", "status": "NOT_DETECTED", "value": None}])
        table = rows[f"{panel}|CONTRAST|C1|PAIRED_TABLE"]["payload"]
        self.assertEqual(sum(table[k] for k in ("both_hit", "a_only", "b_only", "neither")), table["eligible"])
        recovery = rows[f"{panel}|PANEL|RECOVERY|RULE_FUSION_RECOVERY"]["payload"]
        self.assertEqual(recovery["t0_rule_response_ids"], ["S2", "S3"])
        self.assertEqual(recovery["pca_t0_actual_recovery_ids"], ["S2"])
        census = rows[f"{panel}|METHOD|M1_T0_RULE_ONLY|RULE_RUNTIME_CENSUS"]["payload"]
        self.assertEqual((census["pass"], census["fail"], census["abstain"], census["system_errors"]), (4, 3, 2, 1))

    def test_typed_degenerate_and_incomplete_statuses(self):
        contract = build_metric_surface_contract_v1(source_commit=G)
        panel = FROZEN_PANEL_ORDER[1]
        empty = build_complete_metric_surface_v1(primitives=fixture(panel, no_scenarios=True), contract=contract,
            executable_manifest_hash=H, wrapper=self.wrapper, source_commit=G)
        statuses = {v["surface_id"]: v["status"] for v in empty["surfaces"]}
        self.assertEqual(statuses[f"{panel}|METHOD|M0_PCA_SPE|SCENARIO_RECALL"], "NOT_EVALUABLE")
        self.assertEqual(statuses[f"{panel}|METHOD|M0_PCA_SPE|ETAPR_VERSION_UNION"], "NOT_APPLICABLE")
        incomplete = build_complete_metric_surface_v1(primitives=fixture(panel, incomplete="M2_T2_RULE_ONLY"), contract=contract,
            executable_manifest_hash=H, wrapper=self.wrapper, source_commit=G)
        statuses = {v["surface_id"]: v for v in incomplete["surfaces"]}
        row = statuses[f"{panel}|METHOD|M2_T2_RULE_ONLY|SCENARIO_RECALL"]
        self.assertEqual((row["status"], row["payload"]), ("NOT_EVALUABLE_INCOMPLETE_PREDICTION_COVERAGE", None))
        self.assertEqual(statuses[f"{panel}|CONTRAST|C1|PAIRED_TABLE"]["status"], "NOT_EVALUABLE")

    def test_mutations_and_omissions_fail_closed(self):
        contract = build_metric_surface_contract_v1(source_commit=G)
        panel = FROZEN_PANEL_ORDER[2]
        primitive = fixture(panel)
        result = build_complete_metric_surface_v1(primitives=primitive, contract=contract,
            executable_manifest_hash=H, wrapper=self.wrapper, source_commit=G)
        with self.assertRaises(MetricSurfaceError):
            result_surface_completeness_oracle_v1(contract=contract, result_documents=[result],
                verifier_supported_surface_ids=independent_supported_surface_ids_v1())
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            for name, value in (("contract", contract), ("primitive", primitive), ("result", result)):
                (root / f"{name}.json").write_bytes(canonical_bytes(value) + b"\n")
            mutated = json.loads((root / "result.json").read_text())
            target = next(v for v in mutated["surfaces"] if v["surface_id"].endswith("|WILSON95"))
            target["payload"]["hits"] += 1
            mutated["self_hash"] = self_hashed({k: v for k, v in mutated.items() if k != "self_hash"})["self_hash"]
            (root / "result.json").write_bytes(canonical_bytes(mutated) + b"\n")
            with self.assertRaises(MetricSurfaceOracleError):
                verify_complete_metric_surface_from_paths_v1(primitive_path=root / "primitive.json", result_path=root / "result.json",
                    contract_path=root / "contract.json", wrapper=self.wrapper, expected_executable_hash=H)

    def test_twelve_mutation_classes_are_independently_rejected(self):
        contract = build_metric_surface_contract_v1(source_commit=G)
        panel = FROZEN_PANEL_ORDER[0]
        primitive = fixture(panel)
        result = build_complete_metric_surface_v1(primitives=primitive, contract=contract,
            executable_manifest_hash=H, wrapper=self.wrapper, source_commit=G)

        def rehash(value):
            return self_hashed({k: v for k, v in value.items() if k != "self_hash"})

        mutations = []
        # 1 omitted surface.
        value = json.loads(json.dumps(result)); value["surfaces"] = value["surfaces"][:-1]; value["surface_count"] -= 1
        mutations.append(("result", rehash(value)))
        suffixes = ("ETAPR_VERSION_UNION", "DETECTION_DELAY", "PAIRED_TABLE", "MCNEMAR_EXACT",
                    "RULE_FUSION_RECOVERY", "RULE_RUNTIME_CENSUS", "NORMAL_BURDEN")
        for suffix in suffixes:  # 2--8 primitive-derived payload mutations.
            value = json.loads(json.dumps(result))
            row = next(v for v in value["surfaces"] if v["surface_id"].endswith(suffix) and v["payload"] is not None)
            if suffix == "DETECTION_DELAY": row["payload"][0]["value"] = 99
            elif suffix == "PAIRED_TABLE": row["payload"]["both_hit"] += 1
            elif suffix == "MCNEMAR_EXACT": row["payload"]["p_value"] = 0.123
            elif suffix == "RULE_FUSION_RECOVERY": row["payload"]["pca_t0_actual_recovery_ids"] = []
            elif suffix == "RULE_RUNTIME_CENSUS": row["payload"]["system_errors"] += 1
            elif suffix == "NORMAL_BURDEN": row["payload"]["false_seconds_per_hour"] += 1
            else: row["payload"]["F1"] = 0.123
            mutations.append(("result", rehash(value)))
        # 9 denominator and 10 prediction authority mutations in an otherwise plausible result.
        for field in ("denominator", "prediction_manifest"):
            value = json.loads(json.dumps(result))
            for row in value["surfaces"]: row["authority_bindings"][field] = "9" * 64
            mutations.append(("result", rehash(value)))
        # 11 primitive scenario-coordinate mutation and 12 executable mutation.
        value = json.loads(json.dumps(primitive)); value["scenarios"][0]["start"] += 1
        mutations.append(("primitive", rehash(value)))
        value = json.loads(json.dumps(primitive)); value["authority_hashes"]["executable"] = "9" * 64
        mutations.append(("primitive", rehash(value)))
        self.assertEqual(len(mutations), 12)
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "contract.json").write_bytes(canonical_bytes(contract) + b"\n")
            for index, (kind, mutation) in enumerate(mutations):
                p = mutation if kind == "primitive" else primitive
                r = mutation if kind == "result" else result
                (root / "primitive.json").write_bytes(canonical_bytes(p) + b"\n")
                (root / "result.json").write_bytes(canonical_bytes(r) + b"\n")
                with self.subTest(index=index), self.assertRaises(MetricSurfaceOracleError):
                    verify_complete_metric_surface_from_paths_v1(primitive_path=root / "primitive.json", result_path=root / "result.json",
                        contract_path=root / "contract.json", wrapper=self.wrapper, expected_executable_hash=H)

    def test_invalid_normal_authority_and_nonfinite_rejected(self):
        panel = FROZEN_PANEL_ORDER[0]
        primitive = fixture(panel)
        body = {k: v for k, v in primitive.items() if k != "self_hash"}
        body["methods"]["M0_PCA_SPE"]["normal_burden"]["components"][0]["exposure_seconds"] = 0
        primitive = self_hashed(body)
        contract = build_metric_surface_contract_v1(source_commit=G)
        result = build_complete_metric_surface_v1(primitives=primitive, contract=contract,
            executable_manifest_hash=H, wrapper=self.wrapper, source_commit=G)
        row = next(v for v in result["surfaces"] if v["surface_id"].endswith("M0_PCA_SPE|NORMAL_BURDEN"))
        self.assertEqual((row["status"], row["payload"]), ("INVALID_AUTHORITY", None))
        with self.assertRaises(MetricSurfaceError):
            canonical_bytes({"value": float("nan")})

    def test_builder_oracle_hard_separation(self):
        oracle_source = (ROOT / "src/paperworks/validation_v2/dg05_metric_surface_oracle_v1.py").read_text()
        self.assertNotIn("dg05_metric_surface_v1", oracle_source)
        self.assertNotIn("multipanel_metrics_v1", oracle_source)
        self.assertNotIn("multipanel_etapr_v2", oracle_source)

    def test_v3_initializer_requires_exact_future_approval_hash(self):
        authority_root = ROOT / "research_control_center/validation_v2/dg05_metric_verifier_closure"
        predecessor_root = ROOT / "research_control_center/validation_v2/dg05_exec_closure"
        nested = {
            "contract": (authority_root / "METRIC_SURFACE_CONTRACT_V1.json", "metric_surface_contract_v1"),
            "expected": (authority_root / "EXPECTED_RESULT_SURFACE_V1.json", "expected_result_surface_authority_v1"),
            "builder_support": (authority_root / "BUILDER_SURFACE_SUPPORT_V1.json", "result_surface_support_declaration_v1"),
            "verifier_support": (authority_root / "VERIFIER_SURFACE_SUPPORT_V1.json", "result_surface_support_declaration_v1"),
            "completeness": (authority_root / "RESULT_SURFACE_COMPLETENESS_ORACLE_V1.json", "result_surface_completeness_oracle_v1"),
            "coverage": (authority_root / "RESULT_SURFACE_COVERAGE_MATRIX_V1.json", "result_surface_coverage_matrix_authority_v1"),
            "mutation": (authority_root / "MUTATION_EVIDENCE_V1.json", "dg05_metric_surface_mutation_receipt_v1"),
            "rehearsal": (authority_root / "SYNTHETIC_DG05_REHEARSAL_V2.json", "synthetic_dg05_rehearsal_v2"),
        }
        predecessor = {
            "predecessor_manifest_path": predecessor_root / "DG05_EXECUTABLE_AUTHORITY_MANIFEST_V1.json",
            "predecessor_closure_path": predecessor_root / "DG05_EXECUTABLE_CLOSURE_AUTHORITY_V1.json",
            "predecessor_bundle_path": predecessor_root / "NESTED_AUTHORITY_REPLAY_BUNDLE_V1.json",
            "predecessor_nested_paths": predecessor_v2_nested_repository_paths_v1(ROOT),
        }
        state = initialize_dg05_executable_v3_preaccess(manifest_path=authority_root / "DG05_EXECUTABLE_AUTHORITY_MANIFEST_V3.json",
            closure_path=authority_root / "DG05_EXECUTABLE_CLOSURE_AUTHORITY_V3.json", nested_paths=nested,
            approved_manifest_hash=None, **predecessor)
        self.assertEqual((state["state"], state["attack_access_authorized"]), ("DG05_V3_USER_REAPPROVAL_REQUIRED", False))
        self.assertEqual(state["predecessor_v2_replay"]["nested_artifact_count"], 34)
        with self.assertRaises(DG05ExecutableV3Error):
            initialize_dg05_executable_v3_preaccess(manifest_path=authority_root / "DG05_EXECUTABLE_AUTHORITY_MANIFEST_V3.json",
                closure_path=authority_root / "DG05_EXECUTABLE_CLOSURE_AUTHORITY_V3.json", nested_paths=nested,
                approved_manifest_hash="0" * 64, **predecessor)

    def test_connected_prediction_lease_metric_surface_rehearsal(self):
        contract = build_metric_surface_contract_v1(source_commit=G)
        with tempfile.TemporaryDirectory() as raw:
            evidence = run_connected_synthetic_rehearsal_v3(
                root=Path(raw), contract=contract, wrapper=self.wrapper, source_commit=G)
        self.assertEqual(evidence["derived_prediction_cells"], 72)
        self.assertEqual(evidence["successful_prediction_cells"], 72)
        self.assertEqual(evidence["synthetic_scenarios"], 146)
        self.assertEqual(evidence["verified_surface_count"], 228)
        self.assertEqual(evidence["lease_issue_count"], 1)
        self.assertEqual(evidence["lease_consume_count"], 1)
        self.assertEqual(evidence["final_state"], "RESULT_INTEGRITY_AUDITED")


if __name__ == "__main__":
    unittest.main()
