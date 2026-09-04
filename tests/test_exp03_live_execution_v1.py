"""Synthetic only: no provider, credential, dataset or private authority read."""
from decimal import Decimal
from hashlib import sha256
import importlib.util
import json
import platform
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from paperworks.validation_v2 import exp03_live_contract_v1 as c
from paperworks.validation_v2 import exp03_construction_v1 as e
from paperworks.validation_v2.exp03_live_custody_v1 import SingleWriterLedger, ProviderCustodyStop, encoded, replay_ledger, official_transport
from paperworks.validation_v2.formal_v4_authority_v1 import FormalV4RuleDescriptorV1, NumericReferenceBindingV1, V4_NUMERIC_ROLES

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("exp03_runner", ROOT / "scripts/run_exp03_provider_exec_v1.py")
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)
H = "a" * 64


def setup():
    descriptor = FormalV4RuleDescriptorV1("synthetic-relation", H, H, "S", "T", "step_up", "increase", 5,
        tuple(NumericReferenceBindingV1(role, "ref-" + str(i), H) for i, role in enumerate(V4_NUMERIC_ROLES)), H)
    projection = c.projection_payload(descriptor, H)
    auth = e.build_provider_execution_authorization_v1(dg03_approved=True, approval_reference="synthetic-approval",
        provider_id="OPENAI_RESPONSES", model_snapshot=c.MODEL, natural_relation_count=1,
        maximum_input_tokens_per_call=4096, maximum_output_tokens_per_call=2048,
        maximum_total_tokens=21 * 6144, config_hash=H, evidence_projection_hash=H,
        model_policy_hash=H, template_hash=H, privacy_assessment_hash=H, expected_artifact_hash=H)
    return descriptor, projection, auth


def response(proposal, *, model=c.MODEL, tokens=100):
    return encoded({"model": model, "status": "completed", "usage": {"input_tokens": tokens, "output_tokens": 100, "total_tokens": tokens + 100},
        "output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps(proposal)}]}]})


class PureContractTests(unittest.TestCase):
    def setUp(self):
        self.descriptor, self.projection, self.auth = setup()

    def test_template_accepted_exact_projection(self):
        result = c.verify_proposal(c.template_proposal(self.projection), self.descriptor)
        self.assertEqual(result["projection_hash"], self.descriptor.descriptor_hash)
        self.assertFalse(result["runtime_authority_granted"])

    def test_every_proposal_field_mutation_rejected_not_repaired(self):
        for key in c.FIELDS:
            proposal = c.template_proposal(self.projection)
            proposal[key] = 60 if key == "selected_horizon_seconds" else ["foreign"] if key == "numeric_reference_ids" else "foreign"
            result = c.verify_proposal(proposal, self.descriptor)
            self.assertEqual(result["status"], "VERIFIER_REJECTION", key)
            self.assertIsNone(result["projection_hash"])

    def test_duplicate_keys_extra_fields_bool_and_number_refs_fail(self):
        with self.assertRaises(ValueError):
            c.strict_parse('{"decision":"RULE","decision":"NO_RULE"}')
        for extra in ({"raw_rows": []}, {"selected_horizon_seconds": True}, {"numeric_reference_ids": [1]}):
            with self.assertRaises(ValueError):
                c.strict_parse(json.dumps({**c.template_proposal(self.projection), **extra}))

    def test_closed_no_rule_reason(self):
        for reason in c.NO_RULE_REASONS:
            value = {"decision": "NO_RULE", "reason": reason, **{k: None for k in c.FIELDS}}
            self.assertEqual(c.verify_proposal(value, self.descriptor)["status"], "INTENTIONAL_NO_RULE")
        with self.assertRaises(ValueError):
            c.strict_parse(json.dumps({**value, "reason": "provider error"}))

    def test_input_projection_rejects_every_prohibited_field(self):
        for key in ("rows", "numeric_values", "labels", "test1", "path", "credential", "other_arm_result"):
            with self.assertRaises(ValueError):
                c.request_document({**self.projection, key: "prohibited"}, self.auth)

    def test_stateless_fair_initial_request(self):
        request = c.request_document(self.projection, self.auth)
        self.assertEqual(request["model"], c.MODEL)
        self.assertEqual(request["temperature"], 0.7)
        self.assertNotIn("previous_response_id", request)
        self.assertNotIn("arm", json.loads(request["input"]))
        self.assertFalse(request["store"])
        self.assertLess(c.input_upper_bound(request), 4096)

    def test_feedback_retrieval_and_nonrepairable_boundary(self):
        verdict = {"status": "VERIFIER_REJECTION", "issues": ["NUMERIC_REFERENCE_MISMATCH"]}
        self.assertEqual(c.feedback_for(verdict, False, self.projection)["action"], "retrieve")
        self.assertEqual(c.feedback_for(verdict, True, self.projection)["action"], "revise")
        for issue in ("RELATION_FIELD_MISMATCH:source", "RELATION_FIELD_MISMATCH:source_direction", "RELATION_FIELD_MISMATCH:target_direction", "RELATION_FIELD_MISMATCH:selected_horizon_seconds", "UNKNOWN"):
            with self.assertRaises(ValueError):
                c.feedback_for({**verdict, "issues": [issue]}, False, self.projection)
        with self.assertRaises(ValueError):
            c.feedback_for({**verdict, "issues": ["NUMERIC_REFERENCE_MISMATCH", "RELATION_FIELD_MISMATCH:target_direction"]}, False, self.projection)

    def test_every_approval_safety_mutation_rejected(self):
        doc = json.loads((ROOT / "research_control_center/validation_v2/exp03/DG03_FIXED_SNAPSHOT_APPROVAL_V1.json").read_bytes())
        c.validate_approval(doc)
        for key in ("labels_allowed", "private_numeric_payload_allowed", "test1_allowed", "test2_allowed", "fallback_allowed", "cross_arm_outcomes_allowed"):
            with self.assertRaises(ValueError):
                c.validate_approval({**doc, key: True})

    def test_all_budget_axes(self):
        c.budget_guard(819, 3354624, 1677312, c.cost(3354624, 1677312))
        for args in ((820, 0, 0, Decimal(0)), (1, 3354625, 0, Decimal(0)), (1, 0, 1677313, Decimal(0)), (1, 0, 0, Decimal("10.0701")), (1, 0, 0, Decimal("NaN"))):
            with self.assertRaises(ValueError):
                c.budget_guard(*args)
        self.assertEqual(c.cost(3354624, 1677312), Decimal("10.063872"))


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.descriptor, self.projection, self.auth = setup()
        self.request = c.request_document(self.projection, self.auth)
        self.key = (self.descriptor.relation_id, "T2", 1)

    def create(self, directory, transport=None, key=None):
        transport = transport or (lambda req: (200, response(c.template_proposal(self.projection)), 1.0))
        return SingleWriterLedger(Path(directory) / "run", allowed_root=Path(directory), contract_hash=H, schedule=[key or self.key],
            projections={self.descriptor.relation_id: self.projection}, authorization=self.auth, transport=transport)

    def test_raw_input_and_foreign_safe_projection_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = self.create(directory, lambda _: self.fail("unexpected contact"))
            for payload in ({"raw_rows": [1, 2]}, {"relation": {**self.projection, "source_id": "foreign"}}):
                with self.assertRaises(ValueError):
                    ledger.call(self.key, 1, {**self.request, "input": json.dumps(payload)})

    def test_direct_transport_without_receipt_cannot_read_credentials(self):
        with patch("paperworks.validation_v2.exp03_live_custody_v1.os.environ.get", side_effect=AssertionError("credential access")):
            with self.assertRaises(ProviderCustodyStop):
                official_transport(self.request)

    def test_valid_line_rollback_and_deletion_blocked(self):
        for delete in (False, True):
            with tempfile.TemporaryDirectory() as directory:
                ledger = self.create(directory, lambda _: self.fail("unexpected contact"))
                if delete:
                    ledger.path.unlink()
                else:
                    ledger.path.write_bytes(b"")
                with self.assertRaises(ProviderCustodyStop):
                    ledger.call(self.key, 1, self.request)

    def test_reservation_precedes_transport_and_restart_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            def transport(req):
                rows = replay_ledger(Path(directory) / "run/CALL_OUTPUT_COST_LATENCY_LEDGER.jsonl")
                self.assertEqual(rows[-1]["kind"], "CALL_RESERVED")
                return 200, response(c.template_proposal(self.projection)), 1.0
            ledger = self.create(directory, transport)
            ledger.call(self.key, 1, self.request)
            with self.assertRaises(FileExistsError):
                self.create(directory, transport)

    def test_alias_and_changed_sampling_no_contact(self):
        with tempfile.TemporaryDirectory() as directory:
            def forbidden(req):
                self.fail("unexpected contact")
            ledger = self.create(directory, forbidden)
            for mutation in ({"model": "gpt-5.4-mini"}, {"temperature": 1.0}, {"tools": [{"type": "web_search"}]}):
                with self.assertRaises(ProviderCustodyStop):
                    ledger.call(self.key, 1, {**self.request, **mutation})
            self.assertEqual(ledger.calls, 0)

    def test_timeout_and_missing_usage_hold_full_reservation(self):
        for mode in ("timeout", "usage"):
            with tempfile.TemporaryDirectory() as directory:
                def transport(req):
                    if mode == "timeout":
                        raise ProviderCustodyStop("UNCERTAIN_PROVIDER_TRANSPORT")
                    return 200, encoded({"model": c.MODEL}), 1.0
                ledger = self.create(directory, transport)
                with self.assertRaises(ProviderCustodyStop):
                    ledger.call(self.key, 1, self.request)
                self.assertIsNotNone(ledger.outstanding)
                with self.assertRaises(ProviderCustodyStop):
                    ledger.call(self.key, 1, self.request)
                self.assertEqual(ledger.calls, 1)
                self.assertEqual(replay_ledger(ledger.path)[-1]["payload"]["maximum_input_liability"], 4096)

    def test_accept_stops_t2_and_fourth_forbidden(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = self.create(directory)
            ledger.call(self.key, 1, self.request)
            ledger.verdict(self.key, {"status": "ACCEPTED_PROPOSAL"}, continue_t2=False)
            for index in (1, 2, 4):
                with self.assertRaises(ProviderCustodyStop):
                    ledger.call(self.key, index, self.request)

    def test_t1b_cannot_early_stop(self):
        with tempfile.TemporaryDirectory() as directory:
            key = (self.descriptor.relation_id, "T1-B", 1)
            ledger = self.create(directory, key=key)
            ledger.call(key, 1, self.request)
            with self.assertRaises(ProviderCustodyStop):
                ledger.terminal(key, {"outcome": "ACCEPTED_PROPOSAL"})

    def test_partial_and_mutated_ledger(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = self.create(directory)
            raw = ledger.path.read_bytes()
            ledger.path.write_bytes(raw[:-1])
            with self.assertRaises(ProviderCustodyStop):
                replay_ledger(ledger.path)
            ledger.path.write_bytes(raw.replace(b"RUN_STARTED", b"RUN_CHANGED"))
            with self.assertRaises(ProviderCustodyStop):
                replay_ledger(ledger.path)

    def test_failed_persistence_no_contact(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = self.create(directory, lambda _: self.fail("unexpected contact"))
            with patch.object(ledger, "append", side_effect=OSError):
                with self.assertRaises(OSError):
                    ledger.call(self.key, 1, self.request)

    def test_actual_usage_excess_and_wrong_response_model_stop(self):
        for kwargs in ({"model": "gpt-5.4-mini"}, {"tokens": 4097}):
            with tempfile.TemporaryDirectory() as directory:
                ledger = self.create(directory, lambda _: (200, response(c.template_proposal(self.projection), **kwargs), 1.0))
                with self.assertRaises(ProviderCustodyStop):
                    ledger.call(self.key, 1, self.request)


class CompleteSyntheticRunnerTests(unittest.TestCase):
    def test_full_schedule_and_real_contract_objects(self):
        for behavior in ("accept", "repair", "no_rule", "parse", "nonrepairable", "horizon", "direction", "exhaust"):
            with self.subTest(behavior=behavior), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                descriptor, projection, auth = setup()
                schedule = e.build_natural_schedule_v1(relation_ids=[descriptor.relation_id], cohort_hash=H, config_hash=H, evidence_projection_hash=H)
                bundle = runner.seal({"bindings": {}, "configuration": {}, "authorization": auth.to_dict(), "schedule": schedule.to_dict(), "projections": [projection], "environment": {"python": platform.python_version(), "os": platform.system()}})
                runner.write(root / runner.PUBLIC / "EXP03_EXECUTION_FREEZE_V1.json", bundle)
                runner.write(root / runner.PUBLIC / "PREEXECUTION_QA_V1.json", runner.seal({"status": "PASS", "execution_freeze_hash": bundle["self_hash"]}))
                calls = []
                def transport(request):
                    calls.append(request)
                    user = json.loads(request["input"])
                    proposal = c.template_proposal(projection)
                    # First call always satisfies receipt-first schema gate.
                    if len(calls) > 1:
                        if behavior in ("repair", "exhaust") and ("feedback" not in user or behavior == "exhaust"):
                            proposal["numeric_reference_ids"] = ["foreign"]
                        if behavior == "nonrepairable":
                            proposal["source"] = "foreign"
                        if behavior == "horizon":
                            proposal["selected_horizon_seconds"] = 60
                        if behavior == "direction":
                            proposal["source_direction"] = "step_down"
                        if behavior == "no_rule":
                            proposal = {"decision": "NO_RULE", "reason": c.NO_RULE_REASONS[0], **{k: None for k in c.FIELDS}}
                        if behavior == "parse":
                            proposal = {"unexpected": True}
                    return 200, response(proposal), 1.0
                def factory(*args, **kwargs):
                    return SingleWriterLedger(*args, **kwargs, transport=transport)
                with patch.object(runner, "ROOT", root), patch.object(runner, "vault_root", return_value=root / "private"), patch.object(runner, "git", return_value=""), patch.object(runner, "verify_source_commit"), patch.object(runner, "build_bundle", return_value=((descriptor,), [projection], {}, auth, schedule, 3000)), patch.object(runner, "SingleWriterLedger", side_effect=factory):
                    runner.run()
                result = json.loads((root / runner.PUBLIC / "EXP03_NATURAL_RESULTS_V1.json").read_bytes())
                self.assertEqual(result["terminal_count"], 10)
                self.assertLessEqual(result["actual_calls"], 21)
                self.assertEqual(result["arm_metrics"][2]["calls"], 9)
                if behavior in ("accept", "horizon", "direction", "nonrepairable"):
                    self.assertEqual(result["actual_calls"], 15)
                    self.assertEqual(result["arm_metrics"][3]["feedback_activated"], 0)


if __name__ == "__main__":
    unittest.main()
