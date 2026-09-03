from __future__ import annotations
import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

RCC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RCC / "scripts"))
from build_dashboard import load_registry, registry_digest
from dashboard_v2 import build_dashboard_view_model, render_dashboard_v2
from front_results_view import load_front_results


class FrontReportingTests(unittest.TestCase):
    def setUp(self):
        self.data = load_registry(RCC)
        self.front = self.data["front_results"]

    def test_exact_five_frozen_rows_without_scientific_runtime(self):
        self.assertEqual([(11, 7), (5, 25), (11, 533), (11, 9), (5, 27)],
                         [(r["recall"]["numerator"], r["normal_false_episodes"]) for r in self.front["rows"]])
        self.assertTrue(all(r["recall"]["denominator"] == 14 and r["normal_exposure_seconds"] == 51019 for r in self.front["rows"]))
        self.assertEqual("DEVELOPMENT_ONLY", self.front["result"]["status"])
        self.assertFalse(self.front["result"]["post_result_tuning"])

    def test_hash_mutation_fails_closed(self):
        mutated = copy.deepcopy(self.data["state"])
        mutated["front_execution"]["result_hash"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "identity mismatch"):
            load_front_results(RCC.parent, mutated)

    def test_private_or_traversal_locator_rejected(self):
        for ref in ("../private.json", "artifacts/private.json", "research_control_center/validation_v2/gdn_front_exp04_001/results/../private.json"):
            state = copy.deepcopy(self.data["state"])
            state["front_execution"]["result_ref"] = ref
            with self.assertRaisesRegex(ValueError, "Unsafe"):
                load_front_results(RCC.parent, state)

    def test_full_trace_and_sidecar_claims_bound(self):
        trace = self.front["trace"]
        self.assertEqual(6418, trace["unit_count"])
        self.assertEqual(6418, trace["fidelity_unit_count"])
        self.assertEqual(26, len(trace["full_unit_batch_hashes"]))
        self.assertEqual(130, trace["annotated_unit_count"])
        self.assertEqual({"PASS": 4561, "FAIL": 681, "ABSTAIN": 1176}, trace["native_outcomes"])
        self.assertEqual("UNVALIDATED", trace["human_usefulness"])

    def test_old_pilot_and_new_development_are_not_overwritten(self):
        vm = build_dashboard_view_model(self.data, registry_digest(RCC), RCC)
        self.assertEqual(13, next(r for r in vm["pilot_results"] if r["method"] == "D1")["detected"])
        self.assertEqual(11, self.front["rows"][2]["recall"]["numerator"])
        page = render_dashboard_v2(self.data, registry_digest(RCC), RCC)
        for phrase in ("VALIDATION V2 · DEVELOPMENT_ONLY", "PILOT V1", "GDN", "LEARNED_GRAPH_SUPPORTING", "DG-03", "최종 검증 아님"):
            self.assertIn(phrase, page)

    def test_executed_gates_preserve_future_decision_boundaries(self):
        state = self.data["state"]
        for exp in ("EXP-04", "EXP-05"):
            self.assertEqual("COMPLETE", state["pre_validation_readiness"]["experiment_gates"][exp])
        self.assertEqual("BLOCKED", state["pre_validation_readiness"]["experiment_gates"]["EXP-03"])
        self.assertEqual("BLOCKED", state["pre_validation_readiness"]["experiment_gates"]["NEW_HELD_OUT"])
        self.assertEqual(0, self.front["test1_labels_before_freeze"])
        self.assertEqual(0, self.front["test2_accesses"])
        self.assertEqual(0, self.front["provider_calls"])

    def test_no_post_feature_scientific_source_changes(self):
        import subprocess
        changed = subprocess.run(["git", "diff", "--name-only", self.front["execution_commit"], "--", "src", "configs"],
                                 cwd=RCC.parent, capture_output=True, text=True, check=True).stdout
        self.assertEqual("", changed.strip())
