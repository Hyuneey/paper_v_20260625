"""Synthetic-only regressions for external T2 provider execution."""
from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest
from unittest.mock import patch

import test_xver_prompt_v1 as prompt_fixtures
from paperworks.validation_v2.exp03b_contract_v1 import digest, encoded
from paperworks.validation_v2.exp03b_custody_v1 import publish, seal
from paperworks.validation_v2.exp03b_semantic_v2 import proposal_document, t0
from paperworks.validation_v2.xver_prompt_v1 import request_body
from paperworks.validation_v2 import xver_provider_execution_v1 as gate_module
from paperworks.validation_v2.xver_provider_execution_v1 import (
    COMBINED_LIMITS, XverCombinedProviderGateV1, validate_call_inventory,
    validate_serialized_request,
)


class XverProviderExecutionTests(unittest.TestCase):
    def fixture(self):
        evidence, repair = prompt_fixtures.ExternalPromptTests().fixture()
        candidate_id = evidence["candidate_id"]
        profile = seal({
            "schema": "synthetic", "version": "22.04", "N": 1,
            "profiles": [{
                "candidate_id": candidate_id, "provider_pack_hash": "a" * 64,
                "retrieval_pack_hash": "b" * 64,
            }],
        })
        config = {
            "model": "gpt-5.4-mini-2026-03-17", "endpoint": "https://api.openai.com/v1/responses",
            "reasoning": {"effort": "none"}, "temperature": 0.7, "top_p": 1.0,
            "store": False, "service_tier": "default", "timeout_seconds": 60,
            "automatic_retries": 0, "scientific_concurrency": 1, "tools": [],
            "event_evidence_allowed": False,
        }
        budgets = {}
        profiles = {}
        hashes = {}
        for version in ("22.04", "21.03"):
            value = seal({
                "version": version, "model": config["model"], "gate": "DG-XVER-PROVIDER",
                "maximum_calls": 87, "maximum_input_tokens": 1_633_280,
                "maximum_output_tokens": 178_176, "maximum_total_tokens": 1_811_456,
                "prospective_standard_price_ceiling_usd": "2.03", "config": config,
                "N": 29, "profile_hash": profile["self_hash"],
                "hard_phase_input_caps": {"initial": 7168, "repair": 24576},
                "framing_allowance": 512, "output_cap_per_call": 2048,
                "prompt_hash": "c" * 64, "output_schema_hash": "d" * 64,
                "config_hash": "e" * 64,
            })
            # Patch the profile to carry the real frozen N while retaining one
            # synthetic candidate row for direct reservation tests.
            p = dict(profile); p["version"] = version; p["N"] = 29
            p["profiles"] = [p["profiles"][0]] * 29
            # Each duplicate must collapse in the index; gate checks N via row count.
            p["profiles"] = [dict(p["profiles"][0], candidate_id=(candidate_id if i == 0 else f"EXP03B-CAND-{i:020x}")) for i in range(29)]
            p = seal({k: v for k, v in p.items() if k != "self_hash"})
            value = seal({**{k: v for k, v in value.items() if k not in ("self_hash", "profile_hash")}, "profile_hash": p["self_hash"]})
            budgets[version] = value; profiles[version] = p; hashes[version] = value["self_hash"]
        approval = seal({
            "gate": "DG-XVER-PROVIDER", "status": "APPROVED",
            "integration_baseline": "be3ff48bd2abfafc81544357af0daff69a6721a2",
            "model": config["model"], "execution_freeze_hash": "f" * 64,
            "budget_hashes": hashes, "combined_limits": COMBINED_LIMITS,
            "retry": 0, "concurrency": 1, "provider_tools": False,
            "fallback": False, "attack_access": False,
        })
        return evidence, repair, budgets, profiles, approval

    def gate(self):
        evidence, repair, budgets, profiles, approval = self.fixture()
        hashes = {version: budget["self_hash"] for version, budget in budgets.items()}
        with patch.object(gate_module, "EXPECTED_BUDGET_HASHES", hashes):
            gate = XverCombinedProviderGateV1(budgets, profiles, approval, "f" * 64)
        return evidence, repair, budgets, profiles, approval, gate, hashes

    def reserve(self, gate, evidence, repair=None, *, version="22.04", ordinal=1):
        body = request_body(evidence, repair=repair)
        return gate.reserve(
            version=version, candidate_id=evidence["candidate_id"], call_ordinal=ordinal,
            request=body, provider_pack_hash="a" * 64, retrieval_pack_hash="b" * 64,
            input_upper_bound=len(encoded(body)) + 512, evidence=evidence, repair=repair,
        )

    def test_version_bound_slot_and_receipt_first(self):
        evidence, repair, budgets, profiles, approval, gate, hashes = self.gate()
        reservation = self.reserve(gate, evidence)
        self.assertTrue(reservation.slot.startswith("HAI22."))
        with self.assertRaises(ValueError):
            self.reserve(gate, evidence, version="21.03")
        receipt = gate.reconcile(
            input_tokens=10, output_tokens=5, response_hash="0" * 64,
            response_id="resp_test", model="gpt-5.4-mini-2026-03-17",
            latency_seconds=0.1, no_tool_invocation=True,
        )
        gate.accept_one_call_receipt(digest(receipt), persisted_and_replayed=True, privacy_pass=True, schema_pass=True)
        other = self.reserve(gate, evidence, version="21.03")
        self.assertTrue(other.slot.startswith("HAI21."))

    def test_pack_and_version_alias_rejected(self):
        evidence, repair, budgets, profiles, approval, gate, hashes = self.gate()
        body = request_body(evidence)
        with self.assertRaises(ValueError):
            gate.reserve(
                version="22.04", candidate_id=evidence["candidate_id"], call_ordinal=1,
                request=body, provider_pack_hash="9" * 64, retrieval_pack_hash="b" * 64,
                input_upper_bound=len(encoded(body)) + 512, evidence=evidence, repair=None,
            )

    def test_firewall_rejects_event_and_hidden_fields(self):
        evidence, _, *_ = self.fixture()
        for key in ("event10", "train3", "numeric_policy", "meta_rank", "t0_output"):
            body = request_body(evidence)
            content = json.loads(body["input"]); content[key] = []
            body["input"] = json.dumps(content)
            with self.assertRaises(ValueError):
                validate_serialized_request(body)

    def test_no_fourth_call_and_no_failure_to_no_rule(self):
        evidence, repair, budgets, profiles, approval, gate, hashes = self.gate()
        self.reserve(gate, evidence)
        receipt = gate.reconcile(
            input_tokens=10, output_tokens=5, response_hash="0" * 64,
            response_id="resp_test", model="gpt-5.4-mini-2026-03-17",
            latency_seconds=0.1, no_tool_invocation=True,
        )
        gate.accept_one_call_receipt(digest(receipt), persisted_and_replayed=True, privacy_pass=True, schema_pass=True)
        for ordinal in (2, 3):
            current = json.loads(json.dumps(repair))
            current["feedback"]["remaining_call_budget"] = 3 - ordinal + 1
            self.reserve(gate, evidence, current, ordinal=ordinal)
            gate.reconcile(
                input_tokens=10, output_tokens=5, response_hash=str(ordinal) * 64,
                response_id=f"resp_{ordinal}", model="gpt-5.4-mini-2026-03-17",
                latency_seconds=0.1, no_tool_invocation=True,
            )
        with self.assertRaises(ValueError):
            self.reserve(gate, evidence, repair, ordinal=4)
        source = Path("scripts/execute_xver_t2_provider_v1.py").read_text(encoding="utf-8")
        self.assertIn('terminal = "PARSE_FAILURE"', source)
        self.assertNotIn('terminal = "INTENTIONAL_NO_RULE" if proposal is None', source)

    def test_append_only_inventory_rejects_pending(self):
        with TemporaryDirectory(dir=".") as temporary:
            root = Path(temporary)
            publish(root / "calls/0001.request.json", seal({"x": 1}))
            with self.assertRaises(ValueError):
                validate_call_inventory(root)


if __name__ == "__main__":
    unittest.main()
