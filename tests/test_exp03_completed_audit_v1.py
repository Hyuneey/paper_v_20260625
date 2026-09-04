"""Reuse synthetic complete schedules; no actual run/vault/network access."""
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch
import unittest

import test_exp03_live_execution_v1 as fixtures

spec = importlib.util.spec_from_file_location("completed_audit", Path(__file__).resolve().parents[1] / "scripts/audit_exp03_completed_v1.py")
audit_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit_module)


class CompletedAuditTests(unittest.TestCase):
    def test_all_eight_synthetic_outcome_schedules_and_hash_mutation(self):
        original = fixtures.runner.run
        checks = []
        def run_then_audit():
            original()
            root = fixtures.runner.ROOT
            descriptor, _, _ = fixtures.setup()
            fixtures.runner.write(root / "research_control_center/validation_v2/core_v2a/authorities/V2A_FORMAL_V4_PORTFOLIO_AUTHORITY.json", {"descriptors": [descriptor.to_dict()]})
            private = root / "private/exp03-provider-exec-001"
            # Injected fake transport has no real dispatch permit: materialize
            # its expected synthetic markers, never touch a live namespace.
            for row in audit_module.replay_ledger(private / "CALL_OUTPUT_COST_LATENCY_LEDGER.jsonl"):
                if row["kind"] == "CALL_RESERVED":
                    fixtures.runner.write(private / (row["payload"]["slot"] + "-dispatch.once"), {"reservation_hash": row["self_hash"]})
            with patch.object(audit_module, "ROOT", root), patch.object(audit_module, "PUBLIC", root / fixtures.runner.PUBLIC), patch.object(audit_module, "vault_root", return_value=root / "private"):
                result = audit_module.audit()
                self.assertEqual(result["status"], "PASS")
                checks.append(result)
                public = root / fixtures.runner.PUBLIC / "EXP03_NATURAL_RESULTS_V1.json"
                frozen_public = json.loads(public.read_bytes())
                private_result = private / "RESULTS_V1.json"
                # Self-consistent public/private aggregate mutations must still
                # fail against the raw calls, full census and frozen authority.
                for kind in ("total", "arm", "freeze"):
                    changed = json.loads(json.dumps(frozen_public))
                    if kind == "total":
                        changed["total_tokens"] += 1
                    elif kind == "arm":
                        changed["arm_metrics"].pop()
                    else:
                        changed["execution_freeze_hash"] = "0" * 64
                    changed.pop("self_hash")
                    changed = fixtures.runner.seal(changed)
                    public.write_text(json.dumps(changed), encoding="utf-8")
                    private_result.write_text(json.dumps(changed), encoding="utf-8")
                    with self.assertRaises(AssertionError):
                        audit_module.audit()
                    public.write_text(json.dumps(frozen_public), encoding="utf-8")
                    private_result.write_text(json.dumps(frozen_public), encoding="utf-8")
                path = root / "private/exp03-provider-exec-001/0001-1-response.json"
                document = json.loads(path.read_bytes())
                document["model"] = "wrong"
                path.write_text(json.dumps(document), encoding="utf-8")
                with self.assertRaises(AssertionError):
                    audit_module.audit()
        with patch.object(fixtures.runner, "run", side_effect=run_then_audit):
            fixtures.CompleteSyntheticRunnerTests().test_full_schedule_and_real_contract_objects()
        self.assertEqual(len(checks), 8)


if __name__ == "__main__":
    unittest.main()
