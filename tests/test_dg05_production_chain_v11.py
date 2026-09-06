from __future__ import annotations
import json
from pathlib import Path
import tempfile
import unittest

from paperworks.validation_v2.dg05_production_chain_v11 import (
    DG05ProductionChainV11Error, PREACCESS_MODE, REAL_MODE, build_v11_candidate_manifest,
    canonical_bytes, initialize_v11_candidate, self_hashed,
)
from paperworks.validation_v2.dg05_v11_root_verifier_v1 import (
    DG05V11RootVerifierError, verify_v11_roots,
)


ROOT = Path(__file__).resolve().parents[1]


class ProductionChainV11Test(unittest.TestCase):
    @staticmethod
    def _paths() -> dict[str, Path]:
        return {
            "scenario_adapter": ROOT / "src/paperworks/validation_v2/dg05_hai_scenario_adapter_v1.py",
            "custodian": ROOT / "src/paperworks/validation_v2/dg05_label_custodian_v3.py",
            "production_route": ROOT / "src/paperworks/validation_v2/dg05_production_route_v11.py",
            "frozen_v5_kernel": ROOT / "src/paperworks/validation_v2/dg05_production_route_v5.py",
            "fresh_process_launcher": ROOT / "scripts/run_dg05_v11_preaccess_launcher.py",
            "root_verifier": ROOT / "src/paperworks/validation_v2/dg05_v11_root_verifier_v1.py",
            "release_gate": ROOT / "src/paperworks/validation_v2/dg05_production_chain_v11.py",
        }

    def test_exact_mode_and_byte_replay_are_fail_closed(self) -> None:
        paths = self._paths()
        roots = {name: "a" * 64 for name in ("physical_custody", "normal_registry", "scenario_authority", "unified_p1", "dec031", "dec034", "dec035", "dec036", "dec037", "scientific_preregistration")}
        qual = {name: "b" * 64 for name in ("root_replay", "kernel_parity", "fresh_process", "independent_qa", "privacy", "adversarial", "rehearsal")}
        manifest = build_v11_candidate_manifest(repository_root=ROOT, source_commit="0" * 40,
                                                authority_hashes=roots, implementation_paths=paths,
                                                qualification_hashes=qual)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            path.write_bytes(canonical_bytes(manifest) + b"\n")
            state = initialize_v11_candidate(manifest_path=path, repository_root=ROOT,
                                             expected_hash=manifest["self_hash"], mode=PREACCESS_MODE)
            self.assertFalse(state["protected_access_authorized"])
            with self.assertRaises(DG05ProductionChainV11Error):
                initialize_v11_candidate(manifest_path=path, repository_root=ROOT,
                                         expected_hash=manifest["self_hash"], mode=REAL_MODE)
            with self.assertRaises(DG05ProductionChainV11Error):
                initialize_v11_candidate(manifest_path=path, repository_root=ROOT,
                                         expected_hash="0" * 64, mode=PREACCESS_MODE)

    def test_root_verifier_rejects_coherent_downstream_scenario_rehash(self) -> None:
        records = [{"scenario_id": f"S{i:03d}"} for i in range(146)]
        scenario = self_hashed({"schema": "hai_official_source_triangulated_scenario_authority_private_v1",
                                "canonical_records": records})
        decisions = [{"scenario_id": f"S{i:03d}", "eligibility_status": "P1_ELIGIBLE"} for i in range(146)]
        p1 = self_hashed({"schema": "hai_p1_direct_target_denominator_authority_v2", "decisions": decisions})
        roots = {name: "a" * 64 for name in ("physical_custody", "normal_registry", "dec031", "dec034", "dec035", "dec036", "dec037", "scientific_preregistration")}
        roots.update({"scenario_authority": scenario["self_hash"], "unified_p1": p1["self_hash"]})
        qual = {name: "b" * 64 for name in ("root_replay", "kernel_parity", "fresh_process", "independent_qa", "privacy", "adversarial", "rehearsal")}
        manifest = build_v11_candidate_manifest(repository_root=ROOT, source_commit="0" * 40,
                                                authority_hashes=roots, implementation_paths=self._paths(),
                                                qualification_hashes=qual)
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            manifest_path, scenario_path, p1_path = (temp_path / "manifest.json", temp_path / "scenario.json", temp_path / "p1.json")
            for path, value in ((manifest_path, manifest), (scenario_path, scenario), (p1_path, p1)):
                path.write_bytes(canonical_bytes(value) + b"\n")
            receipt = verify_v11_roots(repository_root=ROOT, manifest_path=manifest_path,
                                       scenario_path=scenario_path, p1_path=p1_path,
                                       expected_hash=manifest["self_hash"])
            self.assertEqual(receipt["coverage_percent"], 100)
            scenario["canonical_records"][0]["scenario_id"] = "MUTATED"
            mutated = self_hashed({k: v for k, v in scenario.items() if k != "self_hash"})
            scenario_path.write_bytes(canonical_bytes(mutated) + b"\n")
            with self.assertRaises(DG05V11RootVerifierError):
                verify_v11_roots(repository_root=ROOT, manifest_path=manifest_path,
                                 scenario_path=scenario_path, p1_path=p1_path,
                                 expected_hash=manifest["self_hash"])
