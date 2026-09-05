import csv
import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
AUTH = ROOT / "research_control_center/validation_v2/dg05_metric_verifier_closure"


def canonical_hash(payload: dict) -> str:
    body = dict(payload)
    body.pop("self_hash", None)
    encoded = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class DG05MetricSurfaceAuthorityTests(unittest.TestCase):
    def read(self, name: str) -> dict:
        return json.loads((AUTH / name).read_text(encoding="utf-8"))

    def assert_self_hash(self, name: str) -> dict:
        payload = self.read(name)
        self.assertEqual(canonical_hash(payload), payload["self_hash"], name)
        return payload

    def test_frozen_authority_chain_and_scientific_hashes(self) -> None:
        manifest = self.assert_self_hash("DG05_EXECUTABLE_AUTHORITY_MANIFEST_V3.json")
        closure = self.assert_self_hash("DG05_EXECUTABLE_CLOSURE_AUTHORITY_V3.json")
        contract = self.assert_self_hash("METRIC_SURFACE_CONTRACT_V1.json")
        oracle = self.assert_self_hash("RESULT_SURFACE_COMPLETENESS_ORACLE_V1.json")
        rehearsal = self.assert_self_hash("SYNTHETIC_DG05_REHEARSAL_V2.json")
        qa = self.assert_self_hash("INDEPENDENT_QA_AUTHORITY_V1.json")

        self.assertEqual("7ea1e4c22336a9c9dd65fd96492cb6a1163b9436a0e9eb27d7c2284b206f98f3", manifest["self_hash"])
        self.assertEqual("5b3f0a297f72a958a2db49dda6abd96a5b15ba293e972d7630cb3be1bdb439db", closure["self_hash"])
        self.assertEqual("48f72f68bf26a2593fe6f9a53134df97b6243b849ec97b05233497b7d988a649", contract["self_hash"])
        self.assertEqual("a9c148525d59226956354848dfe57baa19ed17175013fc5e9d077d8f1aca8d72", oracle["self_hash"])
        self.assertEqual("b8a714f22a2a60a45c508bfc5d991f554cef0f9d9022dd6ab22aa81f51dd9c66", rehearsal["self_hash"])
        self.assertEqual("PASS", qa["status"])

        self.assertEqual("cffa6f00dadee1bdd400cdbee545eb9cccd93dcf5da8c6bab3f67809644e8c61", manifest["scientific_authorities"]["scientific_preregistration"])
        self.assertEqual("dab320da47489e5093862b7c4675523c3e6b710faceb753e7f39c8e56f002fe2", manifest["scientific_authorities"]["method_bundle"])
        self.assertEqual("1222d0c7431376dbfa77451875f811123f41af881ae1472b30cd4a2e0f1f0776", manifest["scientific_authorities"]["metric"])
        self.assertEqual("5381ceb1f19f25354a8feb36488dfaa85d3f2945770dc352f2bf8c18fd86cae4", manifest["scientific_authorities"]["etapr"])
        self.assertEqual("cf90fee47e9294873e09aa516df8163328ee924d756c66b18a811c4ea2f9b463", manifest["scientific_authorities"]["statistical"])
        self.assertEqual("587868f42fbdaedbd802541763e0390c09d2f04e4ba5944c45ad7e6e6593cbcc", manifest["scientific_authorities"]["fusion"])
        self.assertFalse(manifest["scientific_authorities_changed"])

    def test_complete_coverage_and_zero_access(self) -> None:
        contract = self.read("METRIC_SURFACE_CONTRACT_V1.json")
        oracle = self.read("RESULT_SURFACE_COMPLETENESS_ORACLE_V1.json")
        mutations = self.assert_self_hash("MUTATION_EVIDENCE_V1.json")
        rehearsal = self.read("SYNTHETIC_DG05_REHEARSAL_V2.json")
        private_index = self.assert_self_hash("PUBLIC_PRIVATE_DG05_METRIC_CLOSURE_INDEX_V1.json")

        self.assertEqual(228, contract["required_surface_count"])
        self.assertEqual(228, oracle["surface_count"])
        self.assertTrue(oracle["exact_set_equality"])
        self.assertEqual(12, mutations["class_count"])
        self.assertEqual(12, mutations["rejected"])
        self.assertEqual(228, mutations["per_surface_omission_rejected"])
        self.assertEqual(228, mutations["per_surface_authority_rejected"])
        self.assertEqual(72, rehearsal["derived_prediction_cells"])
        self.assertEqual(72, rehearsal["successful_prediction_cells"])
        self.assertTrue(rehearsal["all_required_metric_surfaces_exercised"])
        self.assertEqual("RESULT_INTEGRITY_AUDITED", rehearsal["final_state"])
        self.assertEqual(146, rehearsal["synthetic_scenarios"])
        for key in ("attack_test_accesses", "label_scenario_accesses", "provider_calls", "credential_reads"):
            self.assertEqual(0, private_index[key])

        with (AUTH / "RESULT_SURFACE_COVERAGE_MATRIX_V1.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(228, len(rows))
        for row in rows:
            self.assertTrue(all(row[name] == "PASS" for name in (
                "production_builder", "independent_verifier", "synthetic_nontrivial_fixture",
                "degenerate_fixture", "mutation_test", "authority_binding",
            )))


if __name__ == "__main__":
    unittest.main()
