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
        exp03 = state.get("exp03_execution")
        if exp03:
            self.assertEqual("COMPLETE_QA_PASS", exp03["status"])
            self.assertEqual("COMPLETE", state["pre_validation_readiness"]["experiment_gates"]["EXP-03"])
            self.assertEqual("DG-04", exp03["next_gate"])
        else:
            self.assertEqual("BLOCKED", state["pre_validation_readiness"]["experiment_gates"]["EXP-03"])
        self.assertEqual("BLOCKED", state["pre_validation_readiness"]["experiment_gates"]["NEW_HELD_OUT"])
        self.assertEqual(0, self.front["test1_labels_before_freeze"])
        self.assertEqual(0, self.front["test2_accesses"])
        self.assertEqual(0, self.front["provider_calls"])

    def test_no_post_feature_scientific_source_changes(self):
        import subprocess
        changed = subprocess.run(["git", "diff", "--name-only", self.front["execution_commit"], "--", "src", "configs"],
                                 cwd=RCC.parent, capture_output=True, text=True, check=True).stdout
        prep=json.loads((RCC/'validation_v2/exp03b/EXP03B_FINAL_PREPARATION_FREEZE_V2.json').read_text())
        additions={p for p in prep['implementation_hashes'] if p.startswith('src/paperworks/validation_v2/exp03b_')}
        for p in additions:
            self.assertEqual(prep['implementation_hashes'][p],hashlib.sha256((RCC.parent/p).read_bytes()).hexdigest())
            self.assertEqual('',subprocess.run(['git','ls-tree',self.front['execution_commit'],'--',p],cwd=RCC.parent,capture_output=True,text=True,check=True).stdout)
        revised=json.loads((RCC/'validation_v2/exp03b/EXP03B_SEMANTIC_PREPARATION_FREEZE_V2.json').read_text())
        for p,h in revised['implementation_hashes'].items():
            if p.startswith('src/paperworks/validation_v2/exp03b_'):
                self.assertEqual(h,hashlib.sha256((RCC.parent/p).read_bytes()).hexdigest())
                self.assertEqual('',subprocess.run(['git','ls-tree',self.front['execution_commit'],'--',p],cwd=RCC.parent,capture_output=True,text=True,check=True).stdout)
                additions.add(p)
        prospective={
            'src/paperworks/data/hai_xver_normal_v1.py',
            'src/paperworks/validation_v2/final_method_lock_v1.py',
            'src/paperworks/validation_v2/heldout_candidate_portfolio_v1.py',
            'src/paperworks/validation_v2/etapr_exchange_v1.py',
            'src/paperworks/validation_v2/p1_eligibility_design_v1.py',
        }
        for p in prospective:
            frozen=subprocess.check_output(['git','show','f7ce07955e56ce0140b30faea201e7f8ac11f8a3:'+p],cwd=RCC.parent)
            self.assertEqual(frozen,(RCC.parent/p).read_bytes())
            self.assertEqual('',subprocess.run(['git','ls-tree',self.front['execution_commit'],'--',p],cwd=RCC.parent,capture_output=True,text=True,check=True).stdout)
        additions |= prospective
        projection='src/paperworks/data/hai_normal_projection_v2.py'
        frozen_projection=subprocess.check_output(['git','show','1b6195c3:'+projection],cwd=RCC.parent)
        self.assertEqual(frozen_projection,(RCC.parent/projection).read_bytes())
        contract=json.loads((RCC/'validation_v2/dg04_xver_prep/NORMAL_SCHEMA_ONLY_PROJECTION_CONTRACT_V2.json').read_text())
        self.assertEqual(contract['approval'],'NORMAL_DATA_CUSTODY_SCHEMA_ONLY_ALLOWLIST_PROJECTION')
        self.assertEqual(contract['implementation_hashes'][projection],hashlib.sha256(frozen_projection).hexdigest())
        self.assertEqual('',subprocess.run(['git','ls-tree',self.front['execution_commit'],'--',projection],cwd=RCC.parent,capture_output=True,text=True,check=True).stdout)
        additions.add(projection)
        # User-approved prospective separated-role helpers: exact freeze, no old kernel edits.
        binding=json.loads((RCC/'validation_v2/xver_normal/GDN_SEPARATED_EVIDENCE_BINDING_V1.json').read_text())
        self.assertEqual(binding['status'],'APPROVED_WITH_SEPARATED_GDN_EVIDENCE_ROLES')
        for name in ('xver_gdn_roles_v1.py','xver_gdn_provider_v1.py'):
            path='src/paperworks/validation_v2/'+name
            self.assertEqual(binding['implementation_hashes'][path],hashlib.sha256((RCC.parent/path).read_bytes()).hexdigest())
            self.assertEqual('',subprocess.run(['git','ls-tree',self.front['execution_commit'],'--',path],cwd=RCC.parent,capture_output=True,text=True,check=True).stdout)
            additions.add(path)
        # Explicitly authorized external execution adapters; old scientific kernels
        # above are still exact-byte checked. Only these five new source files enter.
        for authority_name, names in (
            ('GDN_EXECUTION_AUTHORITY_V2.json', ('xver_gdn_execution_v1.py',)),
            ('SEMANTIC_EXECUTION_AUTHORITY_V1.json', ('xver_structural_v1.py','xver_confirmation_v1.py','xver_numeric_closure_v1.py')),
            ('XVER_PROVIDER_SERIALIZER_FREEZE_V1.json', ('xver_prompt_v1.py',)),
        ):
            authority=json.loads((RCC/'validation_v2/xver_normal'/authority_name).read_text())
            for name in names:
                path='src/paperworks/validation_v2/'+name
                self.assertEqual(authority['implementation_hashes'][path],hashlib.sha256((RCC.parent/path).read_bytes()).hexdigest())
                self.assertEqual('',subprocess.run(['git','ls-tree',self.front['execution_commit'],'--',path],cwd=RCC.parent,capture_output=True,text=True,check=True).stdout)
                additions.add(path)
        provider_freeze=json.loads((RCC/'validation_v2/xver_normal/provider_execution_v1/XVER_T2_PROVIDER_EXECUTION_FREEZE_V3.json').read_text())
        for name in ('xver_provider_execution_v1.py','xver_t2_closure_v1.py'):
            path='src/paperworks/validation_v2/'+name
            self.assertEqual(provider_freeze['implementation_hashes'][path],hashlib.sha256((RCC.parent/path).read_bytes()).hexdigest())
            self.assertEqual('',subprocess.run(['git','ls-tree',self.front['execution_commit'],'--',path],cwd=RCC.parent,capture_output=True,text=True,check=True).stdout)
            additions.add(path)
        self.assertEqual(
            {"src/paperworks/validation_v2/evaluation_expansion_v1.py",
             "src/paperworks/validation_v2/exp03_live_contract_v1.py",
             "src/paperworks/validation_v2/exp03_live_custody_v1.py"}|additions,
            set(changed.splitlines()),
        )
        # New DG-03 namespace is authorized independently; no pre-existing
        # detection source/config may change. Bind additions to pre-call freeze.
        freeze = json.loads((RCC / "validation_v2/exp03/execution_v1/EXP03_EXECUTION_FREEZE_V1.json").read_text(encoding="utf-8"))
        for name in ("exp03_live_contract_v1.py", "exp03_live_custody_v1.py"):
            relative = "src/paperworks/validation_v2/" + name
            self.assertEqual(freeze["bindings"][relative], hashlib.sha256((RCC.parent / relative).read_bytes()).hexdigest())
        helper = (RCC.parent / "src/paperworks/validation_v2/evaluation_expansion_v1.py").read_text(encoding="utf-8")
        for prohibited_io in ("open(", "read_text(", "read_bytes(", "requests", "urllib", "openai"):
            self.assertNotIn(prohibited_io, helper.lower())
