"""Independent synthetic audit of R2R science, fairness, and accounting."""

from __future__ import annotations

import ast
from dataclasses import dataclass
import inspect
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_execution_prep_v1 import (
    MockProviderEventV1,
    MockProviderTransportV1,
    ProviderCallLedgerV1,
    build_direct_number_request_v1,
)
from paperworks.v6.task039e3_orchestration_v1 import (
    ConstructionOutcomeLedgerV1,
    ConstructionProposalLedgerV1,
    run_direct_number_v1,
)
from paperworks.v6.task039e3_r2r_execution_v1 import (
    EXPECTED_EMPTY_LEDGER_KINDS,
    FreshLedgerObservationR2RV1,
    R2R_ARM_RUNNERS_V1,
    TASK039E3R2RExecutionError,
    build_lifetime_accounting_v1,
    run_fresh_r2r_cohort_v1,
    validate_empty_fresh_cohort_ledgers_v1,
)
from paperworks.v6.task039e3_r2r_request_contract_v1 import (
    DIRECT_NUMBER_PROVIDER_SCHEMA_V1_HASH,
    RECOVERY_MAIN_PROVIDER_SCHEMA_V2_HASH,
    build_r2r_direct_number_request_v1,
    build_r2r_main_request_v1,
)
from paperworks.v6.task039e3_recovery_science_v2 import (
    PostCapabilityAuthorityV2,
    SCIENTIFIC_CONCURRENCY,
    SCIENTIFIC_GENERATION_RETRIES,
    ScientificLedgersV2,
    _FrozenArmRunnersV2,
    _run_post_capability_scientific_execution_v2,
)
from task039e3_support import make_evidence, valid_core_document


ROOT = Path(__file__).resolve().parents[1]
AUTHORIZATION_SCHEMA = (
    ROOT
    / "schemas"
    / "v6"
    / "task039e3_r2r_execution_authorization_v1_schema.json"
)


class _RecordingTransport(MockProviderTransportV1):
    def __init__(self, events: tuple[MockProviderEventV1, ...]) -> None:
        super().__init__(events)
        self.requests: list[object] = []

    def send(self, request):
        self.requests.append(request)
        return super().send(request)


def _events(evidence, count: int) -> tuple[MockProviderEventV1, ...]:
    return tuple(
        MockProviderEventV1("valid_proposal", valid_core_document(evidence))
        for _ in range(count)
    )


def _run_t1_document(document: dict[str, object]):
    evidence = make_evidence()
    return R2R_ARM_RUNNERS_V1.t1(
        relation_schedule_index=0,
        evidence=evidence,
        transport=MockProviderTransportV1(
            (MockProviderEventV1("valid_proposal", document),)
        ),
        call_ledger=ProviderCallLedgerV1(),
        proposal_ledger=ConstructionProposalLedgerV1(),
        outcome_ledger=ConstructionOutcomeLedgerV1(),
    )


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


def _synthetic_full_cohort(t2_calls_per_relation: int):
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
        for _ in range(t2_calls_per_relation):
            kwargs["call_ledger"].append(_ProviderRecord(_Slot("T2")))
        kwargs["outcome_ledger"].append(_Outcome("T2"))

    def direct_number(**kwargs):
        kwargs["call_ledger"].append(
            _ProviderRecord(_Slot("T1-DIRECT-NUMBER"))
        )
        return SimpleNamespace(relation_identity="synthetic")

    result = _run_post_capability_scientific_execution_v2(
        authority=PostCapabilityAuthorityV2("PASS", True, True, "a" * 64),
        relation_identities=schedule,
        evidence_loader=lambda _schedule: evidence,
        transport=object(),
        ledgers=ScientificLedgersV2(provider, proposal, outcome, direct),
        runners=_FrozenArmRunnersV2(t0, t1, t1b, t2, direct_number),
        progress=lambda _message: None,
    )
    return result, provider.records, outcome.records, direct.records


class R2RIndependentAuditScienceTests(unittest.TestCase):
    def test_t1_t1b_and_t2_share_exact_v2_while_direct_number_remains_v1(self) -> None:
        evidence = make_evidence()
        expected_main = build_r2r_main_request_v1(evidence.render_view())

        t1_transport = _RecordingTransport(_events(evidence, 1))
        R2R_ARM_RUNNERS_V1.t1(
            relation_schedule_index=0,
            evidence=evidence,
            transport=t1_transport,
            call_ledger=ProviderCallLedgerV1(),
            proposal_ledger=ConstructionProposalLedgerV1(),
            outcome_ledger=ConstructionOutcomeLedgerV1(),
        )
        self.assertEqual(t1_transport.request_hashes, (expected_main.request_hash,))

        t1b_transport = _RecordingTransport(_events(evidence, 3))
        t1b = R2R_ARM_RUNNERS_V1.t1b(
            relation_schedule_index=0,
            evidence=evidence,
            transport=t1b_transport,
            call_ledger=ProviderCallLedgerV1(),
            proposal_ledger=ConstructionProposalLedgerV1(),
            outcome_ledger=ConstructionOutcomeLedgerV1(),
        )
        self.assertEqual(t1b.generation_calls_consumed, 3)
        self.assertEqual(t1b_transport.request_hashes, (expected_main.request_hash,) * 3)

        t2_transport = _RecordingTransport(_events(evidence, 2))
        t2 = R2R_ARM_RUNNERS_V1.t2(
            relation_schedule_index=0,
            evidence=evidence,
            transport=t2_transport,
            call_ledger=ProviderCallLedgerV1(),
            proposal_ledger=ConstructionProposalLedgerV1(),
            outcome_ledger=ConstructionOutcomeLedgerV1(),
            retrieval_identity=evidence.approved_evidence_identities[0],
            synthetic_validity_faults=("SYNTHETIC_REPAIRABLE_REVISE", None, None),
        )
        self.assertEqual(t2.generation_calls_consumed, 2)
        self.assertEqual(
            [request.provider_schema_hash for request in t2_transport.requests],
            [RECOVERY_MAIN_PROVIDER_SCHEMA_V2_HASH] * 2,
        )
        for request in (
            *t1_transport.requests,
            *t1b_transport.requests,
            *t2_transport.requests,
        ):
            self.assertEqual(
                request.provider_schema_hash, RECOVERY_MAIN_PROVIDER_SCHEMA_V2_HASH
            )

        recovery_direct = build_r2r_direct_number_request_v1(evidence.render_view())
        original_direct = build_direct_number_request_v1(evidence.render_view())
        self.assertEqual(recovery_direct.to_dict(), original_direct.to_dict())
        self.assertEqual(
            recovery_direct.provider_schema_hash,
            DIRECT_NUMBER_PROVIDER_SCHEMA_V1_HASH,
        )
        self.assertIs(R2R_ARM_RUNNERS_V1.direct_number, run_direct_number_v1)

    def test_provider_v2_relaxation_does_not_relax_deterministic_validity(self) -> None:
        evidence = make_evidence()
        valid = valid_core_document(evidence)
        invalid_documents: dict[str, dict[str, object]] = {}

        def mutation(name: str, **updates: object) -> None:
            invalid_documents[name] = {**valid, **updates}

        mutation("empty_relation", relation_identity="")
        mutation("wrong_source", source="UNSUPPORTED_SOURCE")
        mutation("wrong_target", target="UNSUPPORTED_TARGET")
        mutation("wrong_source_direction", source_step_direction="step_down")
        mutation("wrong_target_direction", target_response_direction="decrease")
        mutation("wrong_horizon", selected_delay_horizon_seconds=60)
        mutation("bad_threshold_reference", source_threshold_reference="not-a-hash")
        mutation("duplicate_variables", variables=[valid["source"], valid["source"]])
        mutation("one_variable", variables=[valid["source"]])
        mutation(
            "unsupported_variable", variables=[valid["source"], "UNSUPPORTED_VARIABLE"]
        )
        mutation("wrong_runtime_logic", runtime_logic_family="other_runtime")

        for name, document in invalid_documents.items():
            with self.subTest(case=name):
                outcome = _run_t1_document(document)
                self.assertEqual(outcome.outcome, "no_rule")
                self.assertIn(
                    outcome.no_rule_reason,
                    {
                        "verifier_rejection",
                        "scientific_response:schema_parse_failure",
                    },
                )
                self.assertIsNone(outcome.accepted_call_index)

    def test_fresh_full_cohort_minimum_and_maximum_budgets_are_exact(self) -> None:
        for t2_per_relation, expected_total in ((1, 252), (3, 336)):
            with self.subTest(t2_calls_per_relation=t2_per_relation):
                result, provider, outcomes, direct = _synthetic_full_cohort(
                    t2_per_relation
                )
                self.assertEqual(result.relation_count, 42)
                self.assertEqual(result.t0_outcomes, 42)
                self.assertEqual(result.t1_logical_calls, 42)
                self.assertEqual(result.t1b_logical_calls, 126)
                self.assertEqual(result.t2_logical_calls, 42 * t2_per_relation)
                self.assertEqual(result.direct_number_logical_calls, 42)
                self.assertEqual(result.scientific_logical_calls, expected_total)
                self.assertEqual(len(provider), expected_total)
                self.assertEqual(len(outcomes), 42 * 4)
                self.assertEqual(len(direct), 42)
                self.assertEqual(
                    sum(record.slot.arm == "T1-B" for record in provider), 126
                )
                self.assertEqual(
                    SCIENTIFIC_GENERATION_RETRIES,
                    0,
                )
                self.assertEqual(SCIENTIFIC_CONCURRENCY, 1)

    def test_lifetime_accounting_keeps_aborted_r2_separate_from_r2r(self) -> None:
        for r2r_calls, lifetime_calls in ((252, 253), (336, 337)):
            with self.subTest(r2r_calls=r2r_calls):
                accounting = build_lifetime_accounting_v1(r2r_calls)
                self.assertEqual(
                    accounting.historical_aborted_r2_scientific_logical_calls, 1
                )
                self.assertEqual(
                    accounting.recovery_cohort_scientific_logical_calls, r2r_calls
                )
                self.assertEqual(
                    accounting.lifetime_scientific_logical_call_attempts,
                    lifetime_calls,
                )
        for invalid in (251, 337, True):
            with self.assertRaises(TASK039E3R2RExecutionError):
                build_lifetime_accounting_v1(invalid)

    def test_every_fresh_ledger_must_be_empty_before_e1(self) -> None:
        empty = tuple(
            FreshLedgerObservationR2RV1(kind, 0, None)
            for kind in EXPECTED_EMPTY_LEDGER_KINDS
        )
        validate_empty_fresh_cohort_ledgers_v1(empty)
        for index, kind in enumerate(EXPECTED_EMPTY_LEDGER_KINDS):
            with self.subTest(ledger=kind):
                observed = list(empty)
                observed[index] = FreshLedgerObservationR2RV1(
                    kind, 1, stable_hash_v1({"historical": kind})
                )
                with self.assertRaises(TASK039E3R2RExecutionError):
                    validate_empty_fresh_cohort_ledgers_v1(tuple(observed))

    def test_execution_order_reuses_capability_then_checks_ledgers_before_e1(self) -> None:
        events: list[str] = []
        empty = tuple(
            FreshLedgerObservationR2RV1(kind, 0, None)
            for kind in EXPECTED_EMPTY_LEDGER_KINDS
        )
        authorization = SimpleNamespace(implementation_commit_a="a" * 40)
        capability = SimpleNamespace(
            additional_capability_probes=0,
            capability_transport_reachable=False,
        )
        module = inspect.getmodule(run_fresh_r2r_cohort_v1)
        assert module is not None
        with patch.object(
            module, "validate_r2r_authorization_v1", return_value=authorization
        ), patch.object(
            module, "validate_capability_reuse_v1", return_value=capability
        ):
            result = run_fresh_r2r_cohort_v1(
                authorization_document={},
                private_capability_receipt={},
                capability_ledger_observation=SimpleNamespace(),
                fresh_ledger_observations_loader=lambda: events.append("ledgers")
                or empty,
                e1_loader=lambda: events.append("e1") or "synthetic-evidence",
                scientific_runner=lambda evidence: events.append("science") or evidence,
                stage_sink=events.append,
            )
        self.assertEqual(result.capability_probe_calls, 0)
        self.assertEqual(result.capability_transport_calls, 0)
        self.assertEqual(result.prior_partial_records_reused, 0)
        self.assertLess(events.index("durable_capability_pass_reused"), events.index("ledgers"))
        self.assertLess(events.index("fresh_full_cohort_ledgers_empty"), events.index("e1"))
        self.assertLess(events.index("e1"), events.index("science"))

    def test_nonempty_fresh_ledger_blocks_e1_and_science(self) -> None:
        events: list[str] = []
        observed = tuple(
            FreshLedgerObservationR2RV1(
                kind,
                1 if index == 0 else 0,
                "a" * 64 if index == 0 else None,
            )
            for index, kind in enumerate(EXPECTED_EMPTY_LEDGER_KINDS)
        )
        module = inspect.getmodule(run_fresh_r2r_cohort_v1)
        assert module is not None
        with patch.object(
            module, "validate_r2r_authorization_v1", return_value=object()
        ), patch.object(module, "validate_capability_reuse_v1", return_value=object()):
            with self.assertRaises(TASK039E3R2RExecutionError):
                run_fresh_r2r_cohort_v1(
                    authorization_document={},
                    private_capability_receipt={},
                    capability_ledger_observation=SimpleNamespace(),
                    fresh_ledger_observations_loader=lambda: observed,
                    e1_loader=lambda: events.append("e1"),
                    scientific_runner=lambda _evidence: events.append("science"),
                )
        self.assertEqual(events, [])

    def test_capability_probe_and_downstream_authorities_remain_impossible(self) -> None:
        schema = json.loads(AUTHORIZATION_SCHEMA.read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(set(schema["required"]), set(schema["properties"]))
        for field in (
            "capability_probe_authorized",
            "provider_diagnostic_call_authorized",
            "resume_authorized",
            "historical_partial_result_reuse_authorized",
            "rule_v2_authorized",
            "runtime_authority",
            "utility_evaluation_authorized",
            "winner_selected",
        ):
            self.assertIs(schema["properties"][field]["const"], False)
        self.assertEqual(schema["properties"]["scientific_concurrency"]["const"], 1)
        self.assertEqual(
            schema["properties"]["scientific_generation_retries"]["const"], 0
        )
        signature = inspect.signature(run_fresh_r2r_cohort_v1)
        self.assertNotIn("capability_transport", signature.parameters)
        self.assertNotIn("capability_probe", signature.parameters)
        source = Path(inspect.getsourcefile(run_fresh_r2r_cohort_v1)).read_text(
            encoding="utf-8"
        )
        tree = ast.parse(source)
        imported_modules = {
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        } | {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        self.assertFalse(
            imported_modules
            & {"os", "socket", "urllib", "urllib.request", "requests", "openai"}
        )


if __name__ == "__main__":
    unittest.main()
