from copy import deepcopy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "artifacts/validation_v2/dg04_xver_prep/metric_source/af9e7aed35cfd160cbe0d04c8ec4c102502cb677"
DEPS = ROOT / "artifacts/validation_v2/dg04_xver_prep/metric_dependencies"
sys.path[:0] = [str(SOURCE), str(DEPS)]

from paperworks.validation_v2.dg05_execution_closure_v1 import FROZEN_METHOD_IDS_BY_PANEL_V1
from paperworks.validation_v2.dg05_metric_surface_v1 import FROZEN_PANEL_ORDER, self_hashed
from paperworks.validation_v2.dg05_metric_surface_v2 import (
    MetricSurfaceV2Error,
    build_complete_metric_surface_v2,
    build_metric_primitives_v2,
    build_metric_surface_contract_v2,
)
from paperworks.validation_v2.dg05_metric_surface_oracle_v2 import (
    MetricSurfaceOracleV2Error,
    verify_complete_metric_surface_from_paths_v2,
)
from paperworks.validation_v2.dg05_upstream_lineage_verifier_v2 import (
    DG05UpstreamVerifierV2Error,
    UpstreamPanelReplayPathsV2,
    reconstruct_metric_primitive_from_upstream_v2,
)
from paperworks.validation_v2.etapr_exchange_v1 import OfficialEtaprV1


H = "a" * 64
G = "b" * 40


def runtime_census(rule_id: str, alarming: bool = True) -> dict:
    return {
        "opportunities": 1, "pass": 0 if alarming else 1, "fail": 1 if alarming else 0,
        "abstain": 0, "system_errors": 0, "evaluation_invocations": 1,
        "evaluated_system_errors": 0,
        "configured_rule_ids": [rule_id], "configured_rule_count": 1,
        "formed_rule_ids": [rule_id], "formed_rule_count": 1,
        "evaluated_rule_ids": [rule_id], "evaluated_rule_count": 1,
        "alarming_rule_ids": [rule_id] if alarming else [], "alarming_rule_count": int(alarming),
        "system_error_rule_ids": [], "system_error_rule_count": 0,
        "configured_source_identities": ["P1_SRC"], "formed_source_identities": ["P1_SRC"],
        "evaluated_source_identities": ["P1_SRC"],
        "alarming_source_identities": ["P1_SRC"] if alarming else [],
        "physical_union_alarm_seconds": int(alarming),
        "physical_union_alarm_episodes": int(alarming),
        "unqualified_participating_rules_field": "PROHIBITED",
    }


def fixture(panel: str) -> dict:
    timestamps = [f"2026-01-01T00:00:{index:02d}" for index in range(20)]
    scenarios = [
        {"scenario_id": "S1", "file_id": "F1", "closed_intervals": [
            ["2026-01-01T00:00:00.500000", "2026-01-01T00:00:01.500000"],
            ["2026-01-01T00:00:09.500000", "2026-01-01T00:00:11.500000"],
        ], "eligibility": "P1_ELIGIBLE", "scenario_authority_hash": "1" * 64,
         "eligibility_authority_hash": "2" * 64},
        {"scenario_id": "S2", "file_id": "F1", "closed_intervals": [
            ["2026-01-01T00:00:14", "2026-01-01T00:00:15"]],
         "eligibility": "P1_ELIGIBLE", "scenario_authority_hash": "3" * 64,
         "eligibility_authority_hash": "4" * 64},
    ]
    methods = {}
    for ordinal, method_id in enumerate(FROZEN_METHOD_IDS_BY_PANEL_V1[panel]):
        alarm_rows = [10] if ordinal % 2 == 0 else [2]
        normal = {"panel_id": panel, "method_id": method_id,
                  "authority_class": "GUARD_CONDITIONED_NORMAL",
                  "components": [{"component_id": f"N-{method_id}", "panel_id": panel,
                                  "method_id": method_id, "file_id": "NORMAL", "component_role": "GUARD",
                                  "authority_class": "GUARD_CONDITIONED_NORMAL", "false_seconds": ordinal,
                                  "false_episodes": int(ordinal > 0), "exposure_seconds": 3600,
                                  "runtime_census": None, "source_artifact_byte_hash": "5" * 64}],
                  "false_seconds": ordinal, "false_episodes": int(ordinal > 0), "exposure_seconds": 3600,
                  "false_seconds_per_hour": float(ordinal), "false_episodes_per_hour": float(ordinal > 0)}
        methods[method_id] = {
            "status": "COMPLETE", "timestamps_by_file": {"F1": timestamps},
            "alarm_rows_by_file": {"F1": alarm_rows},
            "alarm_timestamps_by_file": {"F1": [timestamps[index] for index in alarm_rows]},
            "normal_burden": normal,
            "runtime_census": runtime_census(f"R-{method_id}") if ("RULE" in method_id or "PLUS" in method_id) else None,
        }
    return build_metric_primitives_v2(panel_id=panel, dataset_version="23.05", scenarios=scenarios,
        methods=methods, authority_hashes={"executable": H, "prediction_manifest": "c" * 64,
            "scenario": "d" * 64, "denominator": "e" * 64, "normal_burden": "f" * 64,
            "dec031": "9" * 64})


class MetricSurfaceV4Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wrapper = OfficialEtaprV1(SOURCE)

    def test_plural_interval_hit_has_interval_local_physical_delay(self):
        panel = FROZEN_PANEL_ORDER[0]
        contract = build_metric_surface_contract_v2(source_commit=G, dec031_binding_hash="9" * 64,
                                                     normal_source_registry_hash="f" * 64)
        result = build_complete_metric_surface_v2(primitives=fixture(panel), contract=contract,
            executable_manifest_hash=H, wrapper=self.wrapper, source_commit=G)
        rows = {row["surface_id"]: row for row in result["surfaces"]}
        hit = rows[f"{panel}|METHOD|M0_PCA_SPE|SCENARIO_HIT_MISS"]["payload"][0]
        self.assertTrue(hit["hit"])
        self.assertEqual(hit["containing_interval_index"], 1)
        self.assertEqual(hit["interval_local_delay_seconds"], "0.500000")
        self.assertEqual(result["surface_count"], len([row for row in contract["surfaces"] if row["panel_id"] == panel]))

    def test_alarm_in_inactive_gap_is_not_hit(self):
        panel = FROZEN_PANEL_ORDER[0]
        primitive = fixture(panel)
        body = {key: value for key, value in primitive.items() if key != "self_hash"}
        for method in body["methods"].values():
            method["alarm_rows_by_file"]["F1"] = [5]
            method["alarm_timestamps_by_file"]["F1"] = ["2026-01-01T00:00:05"]
        primitive = self_hashed(body)
        contract = build_metric_surface_contract_v2(source_commit=G, dec031_binding_hash="9" * 64,
                                                     normal_source_registry_hash="f" * 64)
        result = build_complete_metric_surface_v2(primitives=primitive, contract=contract,
            executable_manifest_hash=H, wrapper=self.wrapper, source_commit=G)
        rows = {row["surface_id"]: row for row in result["surfaces"]}
        self.assertFalse(rows[f"{panel}|METHOD|M0_PCA_SPE|SCENARIO_HIT_MISS"]["payload"][0]["hit"])

    def test_caller_burden_mutation_and_ambiguous_runtime_rejected(self):
        panel = FROZEN_PANEL_ORDER[0]
        contract = build_metric_surface_contract_v2(source_commit=G, dec031_binding_hash="9" * 64,
                                                     normal_source_registry_hash="f" * 64)
        primitive = fixture(panel)
        body = deepcopy({key: value for key, value in primitive.items() if key != "self_hash"})
        body["methods"]["M0_PCA_SPE"]["normal_burden"]["false_seconds_per_hour"] += 1
        with self.assertRaisesRegex(MetricSurfaceV2Error, "NORMAL_SOURCE_RATE_REPLAY_MISMATCH"):
            build_complete_metric_surface_v2(primitives=self_hashed(body), contract=contract,
                executable_manifest_hash=H, wrapper=self.wrapper, source_commit=G)

    def test_independent_oracle_recomputes_every_surface_and_rejects_rehash(self):
        import json
        import tempfile
        from paperworks.validation_v2.dg05_metric_surface_v1 import canonical_bytes
        panel = FROZEN_PANEL_ORDER[0]
        contract = build_metric_surface_contract_v2(source_commit=G, dec031_binding_hash="9" * 64,
                                                     normal_source_registry_hash="f" * 64)
        primitive = fixture(panel)
        result = build_complete_metric_surface_v2(primitives=primitive, contract=contract,
            executable_manifest_hash=H, wrapper=self.wrapper, source_commit=G)
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            for name, value in (("contract", contract), ("primitive", primitive), ("result", result)):
                (root / f"{name}.json").write_bytes(canonical_bytes(value) + b"\n")
            receipt = verify_complete_metric_surface_from_paths_v2(
                primitive_path=root / "primitive.json", result_path=root / "result.json",
                contract_path=root / "contract.json", wrapper=self.wrapper, expected_executable_hash=H)
            self.assertEqual(receipt["verified_surface_count"], result["surface_count"])
            changed = json.loads((root / "result.json").read_text(encoding="ascii"))
            target = next(row for row in changed["surfaces"] if row["surface_id"].endswith("|SCENARIO_RECALL"))
            target["payload"]["hits"] += 1
            changed = self_hashed({key: value for key, value in changed.items() if key != "self_hash"})
            (root / "result.json").write_bytes(canonical_bytes(changed) + b"\n")
            with self.assertRaisesRegex(MetricSurfaceOracleV2Error, "RECOMPUTED_SURFACE_MISMATCH"):
                verify_complete_metric_surface_from_paths_v2(
                    primitive_path=root / "primitive.json", result_path=root / "result.json",
                    contract_path=root / "contract.json", wrapper=self.wrapper, expected_executable_hash=H)
        body = deepcopy({key: value for key, value in primitive.items() if key != "self_hash"})
        body["methods"]["M1_T0_RULE_ONLY"]["runtime_census"].pop("unqualified_participating_rules_field")
        with self.assertRaisesRegex(MetricSurfaceV2Error, "FOUR_WAY_RUNTIME_CENSUS_REQUIRED"):
            build_complete_metric_surface_v2(primitives=self_hashed(body), contract=contract,
                executable_manifest_hash=H, wrapper=self.wrapper, source_commit=G)

    def test_coherently_rehashed_upstream_freeze_rejected_by_pinned_root(self):
        import tempfile
        from paperworks.validation_v2.dg05_metric_surface_v1 import canonical_bytes

        manifest = self_hashed({"schema": "global_prediction_manifest_v3",
                                "executable_approval_manifest_hash": H, "receipts": []})
        original_freeze = self_hashed({"schema": "global_prediction_freeze_v3",
                                       "manifest_hash": manifest["self_hash"],
                                       "executable_approval_manifest_hash": H})
        changed_freeze = self_hashed({**{key: value for key, value in original_freeze.items()
                                        if key != "self_hash"}, "coherent_downstream_rehash": True})
        scenario = self_hashed({"schema": "frozen_scenario_authority_v1",
                                "global_freeze_hash": changed_freeze["self_hash"], "records": []})
        denominator = self_hashed({"schema": "denominator_authority_v1",
                                   "scenario_authority_hash": scenario["self_hash"], "records": []})
        registry = self_hashed({"schema": "normal_burden_source_registry_v2",
                                "status": "COMPLETE_SOURCE_LINEAGE", "dec031_binding_hash": "9" * 64,
                                "required_components": [], "components": [], "component_count": 0})
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            docs = {"manifest": manifest, "freeze": changed_freeze, "scenario": scenario,
                    "denominator": denominator, "registry": registry}
            for name, value in docs.items():
                (root / f"{name}.json").write_bytes(canonical_bytes(value) + b"\n")
            paths = UpstreamPanelReplayPathsV2(
                root / "manifest.json", root / "freeze.json", root / "scenario.json",
                root / "denominator.json", {}, {}, {}, root / "registry.json", {}, root / "asserted.json")
            with self.assertRaisesRegex(DG05UpstreamVerifierV2Error, "UPSTREAM_ROOT_AUTHORITY_MISMATCH"):
                reconstruct_metric_primitive_from_upstream_v2(
                    panel_id=FROZEN_PANEL_ORDER[0], paths=paths,
                    expected_release_manifest_hash=H, expected_dec031_binding_hash="9" * 64,
                    expected_normal_source_registry_hash=registry["self_hash"],
                    expected_global_freeze_hash=original_freeze["self_hash"], source_commit=G)


if __name__ == "__main__":
    unittest.main()
