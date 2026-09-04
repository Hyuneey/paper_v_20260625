"""Synthetic/public-only audit regressions; no scientific or provider execution."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("exp03b_gate", ROOT / "scripts/audit_exp03b_preparation_gate_v1.py")
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


class PreparationGateTests(unittest.TestCase):
    def test_budget_derived(self):
        self.assertEqual(gate.call_budget(29), {"T0": 0, "T1": 87, "T1-B": 261, "T2": 261, "total": 609})
        self.assertEqual(gate.call_budget(17)["total"], 357)

    def test_invalid_count(self):
        for value in (True, 0, -1, 2.5, "29"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                gate.call_budget(value)

    def test_repeats_frozen(self):
        with self.assertRaises(ValueError):
            gate.call_budget(29, 4)

    def test_hash_mutation_rejected(self):
        body = {"evidence": "synthetic"}
        document = {**body, "self_hash": gate.canonical_hash(body)}
        gate.verify_document(document, "self_hash")
        document["evidence"] = "mutated"
        with self.assertRaises(ValueError):
            gate.verify_document(document, "self_hash")

    def test_nonfinite_rejected(self):
        with self.assertRaises(ValueError):
            gate.canonical_hash({"x": float("nan")})

    def test_scientific_readiness_not_inferred_from_replay(self):
        receipt = gate.audit()
        self.assertEqual(receipt["authority_replay"], "PASS")
        self.assertEqual(receipt["execution_readiness"], "BLOCKED_UNDEFINED_SCIENTIFIC_BINDINGS")
        self.assertEqual(receipt["input_tokens"], "NOT_FROZEN")
        self.assertEqual(receipt["output_tokens"], "NOT_FROZEN")
        self.assertEqual(receipt["cost_ceiling"], "NOT_FROZEN")
        for field in ("provider_calls", "credential_reads", "scientific_data_reads", "private_payload_reads", "writes"):
            self.assertEqual(receipt[field], 0)


if __name__ == "__main__":
    unittest.main()
