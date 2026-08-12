from __future__ import annotations

import ast
from dataclasses import dataclass
import importlib.util
import io
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from paperworks.v6.task039e3_r2r_execution_v1 import (
    R2R_ARM_RUNNERS_V1,
    build_lifetime_accounting_v1,
)
from paperworks.v6.task039e3_r2r_request_contract_v1 import (
    RECOVERY_MAIN_PROVIDER_SCHEMA_V2_HASH,
    build_r2r_main_request_v1,
    build_r2r_t2_followup_request_v1,
)
from paperworks.v6.task039e3_recovery_science_v2 import (
    PostCapabilityAuthorityV2,
    ScientificLedgersV2,
    _FrozenArmRunnersV2,
    _run_post_capability_scientific_execution_v2,
)


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_task039e3_r2r_scientific_execution_v1.py"


class _Ledger:
    def __init__(self) -> None:
        self.records: list[object] = []

    def append(self, value: object) -> None:
        self.records.append(value)


@dataclass(frozen=True)
class _Slot:
    arm: str
    scientific: bool = True


@dataclass(frozen=True)
class _ProviderRecord:
    slot: _Slot


@dataclass(frozen=True)
class _Outcome:
    arm: str


class _Evidence:
    def __init__(self, identity: str) -> None:
        self.relation = SimpleNamespace(relation_identity=identity)
        self.approved_evidence_identities = (f"evidence:{identity}",)


class R2RIntegrationTests(unittest.TestCase):
    def test_exact_r2r_arm_builder_bindings(self) -> None:
        self.assertIsInstance(R2R_ARM_RUNNERS_V1.t0.__module__, str)
        self.assertIsInstance(R2R_ARM_RUNNERS_V1.direct_number.__module__, str)
        self.assertIsNot(R2R_ARM_RUNNERS_V1.t1, R2R_ARM_RUNNERS_V1.t2)
        self.assertEqual(
            build_r2r_main_request_v1.__module__,
            "paperworks.v6.task039e3_r2r_request_contract_v1",
        )
        self.assertEqual(
            build_r2r_t2_followup_request_v1.__module__,
            "paperworks.v6.task039e3_r2r_request_contract_v1",
        )

    def test_synthetic_42_relation_r2r_budget_and_lifetime_accounting(self) -> None:
        schedule = tuple(f"relation-{index:02d}" for index in range(42))
        evidence = tuple(_Evidence(identity) for identity in schedule)
        provider, proposal, outcome, direct = (_Ledger() for _ in range(4))

        def t0(**kwargs):
            kwargs["outcome_ledger"].append(_Outcome("T0"))

        def t1(**kwargs):
            kwargs["call_ledger"].append(_ProviderRecord(_Slot("T1")))
            kwargs["outcome_ledger"].append(_Outcome("T1"))

        def t1b(**kwargs):
            for _ in range(3):
                kwargs["call_ledger"].append(_ProviderRecord(_Slot("T1-B")))
            kwargs["outcome_ledger"].append(_Outcome("T1-B"))

        def t2(**kwargs):
            kwargs["call_ledger"].append(_ProviderRecord(_Slot("T2")))
            kwargs["outcome_ledger"].append(_Outcome("T2"))

        def direct_number(**kwargs):
            kwargs["call_ledger"].append(
                _ProviderRecord(_Slot("T1-DIRECT-NUMBER"))
            )
            return SimpleNamespace(relation_identity="synthetic")

        result = _run_post_capability_scientific_execution_v2(
            authority=PostCapabilityAuthorityV2(
                "PASS", True, True, "a" * 64
            ),
            relation_identities=schedule,
            evidence_loader=lambda _schedule: evidence,
            transport=object(),
            ledgers=ScientificLedgersV2(provider, proposal, outcome, direct),
            runners=_FrozenArmRunnersV2(t0, t1, t1b, t2, direct_number),
            progress=lambda _message: None,
        )
        self.assertEqual(result.scientific_logical_calls, 252)
        self.assertEqual((result.t1_logical_calls, result.t1b_logical_calls), (42, 126))
        self.assertEqual((result.t2_logical_calls, result.direct_number_logical_calls), (42, 42))
        lifetime = build_lifetime_accounting_v1(result.scientific_logical_calls)
        self.assertEqual(lifetime.lifetime_scientific_logical_call_attempts, 253)

    def test_runner_self_check_is_offline_and_live_credential_is_singular(self) -> None:
        spec = importlib.util.spec_from_file_location("r2r_runner", RUNNER)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        output = io.StringIO()
        with patch("sys.stdout", output):
            self.assertEqual(module.main(["--offline-self-check"]), 0)
        document = output.getvalue()
        self.assertIn(RECOVERY_MAIN_PROVIDER_SCHEMA_V2_HASH, document)
        self.assertIn('"provider_contact_authorized":false', document)
        self.assertIn('"capability_probe_authorized":false', document)

        source = RUNNER.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        } | {
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        self.assertFalse(imported & {"socket", "urllib", "requests", "openai"})
        self.assertIn("os", imported)
        self.assertEqual(source.count('os.environ.get("OPENAI_API_KEY")'), 1)
        self.assertNotIn("urlopen", source)


if __name__ == "__main__":
    unittest.main()
