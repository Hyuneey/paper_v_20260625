from __future__ import annotations

import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
EXECUTION = ROOT / "src/paperworks/v6/task039e3_recovery_execution_v2.py"
SCIENCE = ROOT / "src/paperworks/v6/task039e3_recovery_science_v2.py"
RUNNER = ROOT / "scripts/run_task039e3_recovery_execution_v2.py"
HISTORICAL = ROOT / "src/paperworks/v6/task039e3_scientific_execution_v1.py"

REQUIRED_TERMINAL_OUTPUTS = {
    "custody",
    "private_bindings",
    "construction_metrics",
    "direct_metrics",
    "summary",
    "access",
    "receipt",
}


def _function(tree: ast.Module, name: str) -> ast.FunctionDef:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"function not found: {name}")


def _string_constants(node: ast.AST) -> set[str]:
    return {
        item.value
        for item in ast.walk(node)
        if isinstance(item, ast.Constant) and isinstance(item.value, str)
    }


class R1CResultCompletenessAuditTests(unittest.TestCase):
    """Independent negative oracle for the active V2 terminal materialization."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.execution_text = EXECUTION.read_text(encoding="utf-8")
        cls.science_text = SCIENCE.read_text(encoding="utf-8")
        cls.runner_text = RUNNER.read_text(encoding="utf-8")
        cls.historical_text = HISTORICAL.read_text(encoding="utf-8")
        cls.execution_tree = ast.parse(cls.execution_text)
        cls.runner_tree = ast.parse(cls.runner_text)

    def test_historical_terminal_contract_contains_required_artifact_families(self) -> None:
        historical_keys = {
            key
            for key in REQUIRED_TERMINAL_OUTPUTS
            if f'"{key}"' in self.historical_text
        }
        self.assertEqual(historical_keys, REQUIRED_TERMINAL_OUTPUTS)
        self.assertIn("aggregate_construction_metrics_v1", self.historical_text)
        self.assertIn("aggregate_direct_number_metrics_v1", self.historical_text)
        self.assertIn("_final_private_ledger", self.historical_text)

    def test_active_success_return_is_counts_and_hashes_not_full_result_contract(self) -> None:
        function = _function(self.execution_tree, "run_capability_then_science_v2")
        constants = _string_constants(function)
        self.assertTrue(
            {
                "scientific_result",
                "scientific_provider_ledger_hash",
                "typed_accounting",
            }.issubset(constants)
        )
        self.assertTrue(REQUIRED_TERMINAL_OUTPUTS.isdisjoint(constants))
        self.assertNotIn("aggregate_construction_metrics_v1", self.execution_text)
        self.assertNotIn("aggregate_direct_number_metrics_v1", self.execution_text)
        self.assertNotIn("_final_private_ledger", self.execution_text)

    def test_active_path_only_creates_unfinalized_scientific_jsonl_ledgers(self) -> None:
        for leaf in (
            "scientific_provider_v2.jsonl",
            "proposals_v2.jsonl",
            "outcomes_v2.jsonl",
            "direct_v2.jsonl",
        ):
            self.assertIn(leaf, self.execution_text)
        for artifact in (
            "TASK-039E3_PROVIDER_CUSTODY_BINDING.json",
            "TASK-039E3_PRIVATE_LEDGER_BINDINGS.json",
            "TASK-039E3_CONSTRUCTION_METRICS.json",
            "TASK-039E3_DIRECT_NUMBER_METRICS.json",
            "TASK-039E3_EXECUTION_SUMMARY.json",
            "TASK-039E3_DATA_ACCESS_AUDIT.json",
            "TASK-039E3_EXECUTION_RECEIPT.json",
        ):
            self.assertNotIn(artifact, self.execution_text)
            self.assertNotIn(artifact, self.runner_text)

    def test_post_capability_result_carries_no_outcomes_metrics_or_final_bindings(self) -> None:
        tree = ast.parse(self.science_text)
        result = next(
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef)
            and node.name == "PostCapabilityScientificResultV2"
        )
        annotations = {
            node.target.id
            for node in result.body
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
        }
        self.assertEqual(
            annotations,
            {
                "relation_count",
                "t0_outcomes",
                "t1_logical_calls",
                "t1b_logical_calls",
                "t2_logical_calls",
                "direct_number_logical_calls",
                "scientific_logical_calls",
                "scientific_concurrency",
                "scientific_generation_retries",
                "local_compatibility_slots",
            },
        )
        self.assertFalse(
            any(
                marker in annotations
                for marker in (
                    "construction_metrics",
                    "direct_number_metrics",
                    "proposal_ledger_hash",
                    "outcome_ledger_hash",
                    "direct_number_ledger_hash",
                    "execution_receipt_hash",
                )
            )
        )

    def test_runner_stdout_and_exit_code_do_not_materialize_terminal_results(self) -> None:
        main = _function(self.runner_tree, "main")
        prints = [node for node in ast.walk(main) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print"]
        self.assertEqual(len(prints), 1)
        printed_constants = _string_constants(prints[0])
        self.assertEqual(printed_constants, {"status"})
        self.assertNotIn("write_public_artifact_atomic_v1", self.runner_text)
        self.assertNotIn("finalize_public_artifact_v1", self.runner_text)


if __name__ == "__main__":
    unittest.main()
