from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest

from paperworks.validation_v2.dg05_execution_closure_v1 import (
    DG05ClosureError, DetectorSubauthorityV1, FROZEN_METHOD_IDS_BY_PANEL_V1, FullProcessPointV1,
    FullProcessScopeAuthorityV1, MethodDispatchEntryV1, MethodDispatchRegistryV1,
    RuleRuntimeSubauthorityV1, RuleRuntimeSubauthorityRegistryV1, StateTransitionEvidenceV1, build_etapr_coordinate_binding_v1, digest,
    file_sha256, project_attack_feature_file_v1, self_hashed,
)
from paperworks.validation_v2.multipanel_custody_v1 import (
    FROZEN_AUTHORITY_SOURCE_COMMIT_V2, FROZEN_PANEL_ORDER_V2,
    PhysicalFileIdentityV2, frozen_feature_allowlist_authorities_v2,
)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research_control_center/validation_v2/dg05_exec_closure"
H = "a" * 64
G = "a" * 40


def read(name: str) -> dict:
    raw = (OUT / name).read_bytes()
    value = json.loads(raw.decode("ascii"))
    assert value["self_hash"] == digest({k:v for k,v in value.items() if k != "self_hash"})
    assert raw == json.dumps(value, sort_keys=True, separators=(",",":"), ensure_ascii=True).encode("ascii") + b"\n"
    return value


class DG05ClosureAuthorityTest(unittest.TestCase):
    def test_public_authorities_replay_and_matrix_is_8_of_8(self):
        closure = read("DG05_EXECUTABLE_CLOSURE_AUTHORITY_V1.json")
        self.assertEqual(closure["blocker_matrix"], {f"B{i}": "PASS" for i in range(1,9)})
        self.assertEqual((closure["attack_test_accesses"], closure["label_accesses"], closure["real_eligibility_generated"]), (0,0,0))
        rehearsal = read("SYNTHETIC_DG05_REHEARSAL_V1.json")
        self.assertEqual((rehearsal["phase_a_cells"], rehearsal["scenario_count"], rehearsal["result_authority_count"]), (72,146,23))
        self.assertEqual(rehearsal["final_state"], "RESULT_INTEGRITY_AUDITED")

    def test_full_scope_exact_counts_and_hai21_discrepancy(self):
        raw = read("FULL_PROCESS_SCOPE_AUTHORITY_V1.json")
        points = tuple(FullProcessPointV1(**p) for p in raw["points"])
        scope = FullProcessScopeAuthorityV1(points, raw["official_manual_hash"], tuple(sorted(raw["official_schema_hashes"])),
            raw["source_commit"], tuple(sorted(raw["version_counts"].items())), tuple(raw["declared_count_discrepancies"]),
            tuple(sorted(raw["official_identity_set_hashes"].items())), tuple(sorted(raw["supplemental_authority_hashes"].items())), raw["authority_mode"])
        scope.validate()
        self.assertEqual(raw["version_counts"], {"21.03":79,"22.04":86,"23.05":86})
        self.assertEqual(scope.classify("21.03", "P2_SIT02"), "UNRESOLVED")
        self.assertEqual(scope.classify("21.03", "P3_FIT01"), "KNOWN_NON_P1")
        x = next(p for p in points if p.canonical_identity == "x1001_05_SETPOINT_OUT")
        self.assertEqual(x.authority_status, "VERIFIED_PUBLIC_GRAPH_ALIAS")

    def test_exact_23_dispatch_entries(self):
        raw = read("METHOD_DISPATCH_REGISTRY_V1.json")
        entries = tuple(MethodDispatchEntryV1(e["panel_id"],e["method_id"],e["executor_class"],tuple(e["component_hashes"]),e["detector_id"]) for e in raw["entries"])
        registry = MethodDispatchRegistryV1(entries,raw["detector_registry_hash"],raw["method_bundle_hash"],raw["source_commit"])
        registry.validate()
        self.assertEqual(len(entries), 23)
        with self.assertRaises(DG05ClosureError):
            replace(registry, entries=entries[:-1]).validate()

    def test_detector_locators_are_explicit_and_hai23_pca_if_are_distinct(self):
        raw = read("DETECTOR_SUBAUTHORITY_REGISTRY_V1.json")
        entries = tuple(DetectorSubauthorityV1(**row) for row in raw["entries"])
        for entry in entries:
            entry.validate()
        hai23 = {entry.detector_id: entry for entry in entries if entry.panel_id == FROZEN_PANEL_ORDER_V2[0]}
        self.assertEqual(hai23["PCA_SPE"].implementation_hash, hai23["ISOLATION_FOREST"].implementation_hash)
        self.assertNotEqual(hai23["PCA_SPE"].scorer_callable_id, hai23["ISOLATION_FOREST"].scorer_callable_id)
        self.assertNotEqual(hai23["PCA_SPE"].fitted_model_hash, hai23["ISOLATION_FOREST"].fitted_model_hash)
        self.assertEqual((hai23["PCA_SPE"].model_component_index, hai23["PCA_SPE"].threshold_component_index), (0, 2))
        self.assertEqual((hai23["ISOLATION_FOREST"].model_component_index, hai23["ISOLATION_FOREST"].threshold_component_index), (1, 3))

    def test_nested_replay_bundle_has_exact_manifest_authority_set(self):
        manifest = read("DG05_EXECUTABLE_AUTHORITY_MANIFEST_V1.json")
        nested = read("NESTED_AUTHORITY_REPLAY_BUNDLE_V1.json")
        expected = {f"scientific:{key}": value for key, value in manifest["scientific_authorities"].items()}
        expected.update({"detector_registry": manifest["detector_registry_hash"],
                         "dispatch_registry": manifest["dispatch_registry_hash"],
                         "rule_runtime_registry": manifest["rule_runtime_registry_hash"],
                         "full_process_scope": manifest["full_process_scope_hash"],
                         "p1_custodian_v3": manifest["p1_custodian_v3_hash"]})
        expected.update({f"portfolio:{index:02d}": value for index, value in enumerate(manifest["rule_portfolio_authority_hashes"])})
        expected.update({f"implementation:{key}": value for key, value in manifest["implementation_hashes"].items()})
        observed = {row["logical_name"]: row["expected_authority_hash"] for row in nested["entries"]}
        self.assertEqual(observed, expected)
        self.assertEqual(nested["self_hash"], manifest["nested_authority_replay_bundle_hash"])

    def test_transition_requires_replayed_artifact(self):
        current = self_hashed({"schema":"dg05_execution_state_v3","state":"PREDICTION_EXECUTION_STARTED_LABEL_LOCKED",
            "previous_state_hash":H,"executable_approval_manifest_hash":H,"execution_id":"SYNTHETIC","source_commit":G,"evidence_hashes":[]})
        artifact = self_hashed({"schema":"global_prediction_freeze_v3", "manifest_hash":H, "census_hash":H,
            "predecessor_state_hash":current["self_hash"], "executable_approval_manifest_hash":H,
            "status":"GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED"})
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw); path = root / "freeze.json"
            path.write_bytes(json.dumps(artifact, sort_keys=True, separators=(",",":"), ensure_ascii=True).encode("ascii") + b"\n")
            byte_hash = file_sha256(path)
            binding = self_hashed({"schema":"dg05_state_transition_binding_v1","next_state":"GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED",
                "evidence_kind":"GLOBAL_FREEZE","evidence_authority_hash":artifact["self_hash"],"evidence_artifact_byte_hash":byte_hash,
                "evidence_item_count":72,"predecessor_state_hash":current["self_hash"],"executable_approval_manifest_hash":H,
                "execution_id":"SYNTHETIC","source_commit":G})
            binding_path=root/"binding.json"; binding_path.write_bytes(json.dumps(binding,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode("ascii")+b"\n")
            evidence = StateTransitionEvidenceV1("GLOBAL_FREEZE",artifact["self_hash"],72,artifact,path,byte_hash,binding,binding_path,file_sha256(binding_path))
            evidence.validate_for("GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED",current_state=current,executable_manifest_hash=H,source_commit=G)
            with self.assertRaises(DG05ClosureError):
                replace(evidence,authority_hash=H).validate_for("GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED",current_state=current,executable_manifest_hash=H,source_commit=G)
            path.write_bytes(path.read_bytes() + b"x")
            with self.assertRaises(DG05ClosureError):
                evidence.validate_for("GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED",current_state=current,executable_manifest_hash=H,source_commit=G)

    def test_projection_bytes_replay_and_etapr_coordinates(self):
        authority = frozen_feature_allowlist_authorities_v2()[FROZEN_PANEL_ORDER_V2[0]]
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); source=root/"source.csv"; destination=root/"projection.jsonl"
            header=[authority.timestamp_id,*authority.feature_ids,"Attack"]
            source.write_text(",".join(header)+"\n"+",".join(["2026-01-01T00:00:00",*(["1"]*len(authority.feature_ids)),"opaque"])+"\n",encoding="utf-8")
            physical=PhysicalFileIdentityV2(authority.panel_id,"hai-test2.csv",file_sha256(source),digest(header),H)
            projection,timestamp=project_attack_feature_file_v1(source=source,destination=destination,physical_file=physical,
                panel_authority=authority,file_id="hai-test2.csv",adapter_implementation_hash=H,source_commit=G)
            projection.validate(); timestamp.validate()
            binding=build_etapr_coordinate_binding_v1(panel_id=authority.panel_id,file_bindings=[{"file_id":"hai-test2.csv",
                "physical_file_authority_hash":timestamp.physical_file_authority_hash,"timestamp_authority_hash":timestamp.document()["self_hash"],
                "prediction_artifact_hash":H,"scenario_authority_hash":H}],etapr_authority_hash=H)
            self.assertFalse(binding["cross_file_anonymous_ranges"])
            destination.write_bytes(destination.read_bytes()+b"x")
            self.assertNotEqual(file_sha256(destination),projection.projection_hash)


if __name__ == "__main__": unittest.main()
