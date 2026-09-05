from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest

from paperworks.validation_v2.dg05_execution_closure_v1 import (
    DG05ClosureError, FROZEN_METHOD_IDS_BY_PANEL_V1, FullProcessPointV1,
    FullProcessScopeAuthorityV1, MethodDispatchEntryV1, MethodDispatchRegistryV1,
    StateTransitionEvidenceV1, build_etapr_coordinate_binding_v1, digest,
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
    value = json.loads((OUT / name).read_text(encoding="ascii"))
    assert value["self_hash"] == digest({k:v for k,v in value.items() if k != "self_hash"})
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

    def test_transition_requires_replayed_artifact(self):
        artifact = self_hashed({"schema":"global_prediction_freeze_v3"})
        StateTransitionEvidenceV1("GLOBAL_FREEZE",artifact["self_hash"],72,artifact).validate_for("GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED")
        with self.assertRaises(DG05ClosureError):
            StateTransitionEvidenceV1("GLOBAL_FREEZE",H,72,artifact).validate_for("GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED")

    def test_projection_bytes_replay_and_etapr_coordinates(self):
        authority = frozen_feature_allowlist_authorities_v2()[FROZEN_PANEL_ORDER_V2[0]]
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); source=root/"source.csv"; destination=root/"projection.jsonl"
            header=[authority.timestamp_id,*authority.feature_ids,"Attack"]
            source.write_text(",".join(header)+"\n"+",".join(["2026-01-01T00:00:00",*(["1"]*len(authority.feature_ids)),"opaque"])+"\n",encoding="utf-8")
            physical=PhysicalFileIdentityV2(authority.panel_id,"hai-test2.csv",file_sha256(source),H,H)
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
