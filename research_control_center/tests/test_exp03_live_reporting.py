"""Public-only scientific reporting integrity; no provider or private I/O."""
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import unittest

RCC = Path(__file__).resolve().parents[1]
EXP = RCC / "validation_v2/exp03/execution_v1"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(value):
    return sha256(json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


class LiveReportingTests(unittest.TestCase):
    def test_exact_approved_snapshot_and_caps(self):
        approval = read(RCC / "validation_v2/exp03/DG03_FIXED_SNAPSHOT_APPROVAL_V1.json")
        self.assertEqual("gpt-5.4-mini-2026-03-17", approval["model_snapshot"])
        self.assertEqual((819, 3354624, 1677312, 5031936, "10.07", 1), tuple(approval[k] for k in (
            "maximum_generation_calls", "maximum_input_tokens", "maximum_output_tokens", "maximum_total_tokens", "maximum_standard_api_usd", "scientific_concurrency")))
        self.assertFalse(approval["fallback_allowed"])

    def test_result_qa_and_freeze_hash_binding(self):
        result = read(EXP / "EXP03_NATURAL_RESULTS_V1.json")
        qa = read(EXP / "INDEPENDENT_RESULT_QA_V1.json")
        freeze = read(EXP / "EXP03_EXECUTION_FREEZE_V1.json")
        for document in (result, qa, freeze):
            self.assertEqual(document["self_hash"], digest({k: v for k, v in document.items() if k != "self_hash"}))
        self.assertEqual("PASS", qa["status"])
        self.assertEqual(result["self_hash"], qa["results_hash"])
        self.assertEqual(freeze["self_hash"], result["execution_freeze_hash"])
        self.assertEqual(390, result["terminal_count"])
        self.assertEqual(result["total_tokens"], result["input_tokens"] + result["output_tokens"])
        expected_cost = (Decimal("0.75") * result["input_tokens"] + Decimal("4.50") * result["output_tokens"]) / 1000000
        self.assertEqual(expected_cost, Decimal(result["standard_api_cost_upper_bound_usd"]))
        self.assertLessEqual(expected_cost, Decimal("10.07"))
        self.assertLessEqual(result["actual_calls"], 819)

    def test_current_state_requires_dg04_and_preserves_other_gates(self):
        state = read(RCC / "registry/current_state.yaml")
        program = read(RCC / "validation_v2/PROGRAM_STATE.json")
        self.assertIn("DG-04", state["exact_next_task"])
        self.assertEqual("COMPLETE_QA_PASS", state["exp03_execution"]["status"])
        executed=bool(state.get('exp03b_execution'))
        if state.get('dg04_method_lock'):
            self.assertEqual(state['dg04_method_lock']['decision_id'],'DEC-025')
            self.assertEqual('APPROVED_WITH_SCOPED_AGENTIC_CLAIM',program['decision_gates']['DG-04'])
            self.assertIsNone(state['xver_preparation']['exact_provider_budget'])
        else:
            self.assertEqual("USER_DECISION_REQUIRED" if executed else "DEFERRED_UNTIL_EXP03B", program["decision_gates"]["DG-04"])
        self.assertEqual("SUPERSEDED_BY_DG03B_REVISED", program["decision_gates"]["DG-03B"])
        self.assertEqual("APPROVED_EXECUTED" if executed else "USER_DECISION_REQUIRED", program["decision_gates"]["DG-03B_REVISED"])
        self.assertEqual("PREPARED_DG03B_REVISED_PENDING",state['exp03b_preparation']['status'])
        self.assertFalse(program["held_out_authorized"])
        self.assertEqual("PENDING_MANDATORY", program["decision_gates"]["DG-05"])
        self.assertEqual("PENDING", program["decision_gates"]["DG-06"])

    def test_no_dataset_access_or_runtime_mutation_claim(self):
        result = read(EXP / "EXP03_NATURAL_RESULTS_V1.json")
        for field in ("test1_accesses", "test2_accesses", "heldout_accesses", "dataset_payload_reads", "numeric_values_sent", "portfolio_changes"):
            self.assertEqual(0, result[field])
        report = (EXP / "EXP03_RESULTS_REPORT_V1.md").read_text(encoding="utf-8")
        for required in ("DG-04", "synthetic stress", "PILOT V1", "reference", "독립 scientific sample"):
            self.assertIn(required, report)

    def test_new_dashboard_result_section_and_historical_results_present(self):
        page = (RCC / "dashboard/index.html").read_text(encoding="utf-8")
        self.assertIn('id="exp03-live-heading"', page)
        self.assertIn("gpt-5.4-mini-2026-03-17", page)
        self.assertIn("PILOT V1", page)
        self.assertIn("DEVELOPMENT_ONLY", page)
        for path in (RCC / "generated/CURRENT_STATUS.md", RCC / "generated/GPT_BRIEF.md", RCC / "MY_TODO.md", RCC / "DECISION_INBOX.md"):
            self.assertNotIn("다음: DG-03 provider 예산·승인 검토", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
