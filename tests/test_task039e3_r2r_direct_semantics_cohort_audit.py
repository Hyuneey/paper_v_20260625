from __future__ import annotations

import ast
from dataclasses import replace
import hashlib
from pathlib import Path
import subprocess
import unittest

from paperworks.v6.task039e3_execution_prep_v1 import (
    ConstructionInputViewV1,
    MockProviderEventV1,
    MockProviderTransportV1,
    ProviderCallLedgerV1,
)
from paperworks.v6.task039e3_orchestration_v1 import (
    ConstructionOutcomeLedgerV1,
    ConstructionProposalLedgerV1,
)
from paperworks.v6.task039e3_r2r_execution_v1 import (
    R2R_ARM_RUNNERS_V1,
    run_injected_r2r_scientific_cohort_v1,
)
from paperworks.v6.task039e3_recovery_science_v2 import ScientificLedgersV2
from task039e3_support import direct_number_payload, make_evidence, valid_core_document


ROOT = Path(__file__).resolve().parents[1]
FORENSIC_B = "4712eeea87f0f60b51f4db9414fb589391c899d1"
REMEDIATION_A = "5dca2d0431d60ef2f2bdfc907ebfe3fe18521f16"


def _blob(commit: str, path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def _function_hash(commit: str, path: str, name: str) -> str:
    source = _blob(commit, path).decode("utf-8")
    tree = ast.parse(source)
    node = next(
        item
        for item in ast.walk(tree)
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == name
    )
    segment = ast.get_source_segment(source, node)
    if segment is None:
        raise AssertionError(f"source segment missing: {path}:{name}")
    return hashlib.sha256(segment.encode()).hexdigest()


class AliasFaithfulEvidence:
    def __init__(self, index: int) -> None:
        base = make_evidence(index)
        self.relation = base.relation
        self.numeric_evidence = base.numeric_evidence
        self.numeric_bindings = tuple(
            replace(item, evidence_identity=item.reference)
            for item in base.numeric_bindings
        )
        self.approved_evidence_identities = tuple(
            item.reference for item in self.numeric_bindings
        )
        self.semantic_process_metadata = base.semantic_process_metadata

    def render_view(self) -> ConstructionInputViewV1:
        return ConstructionInputViewV1(
            relation_identity=self.relation.relation_identity,
            source=self.relation.source,
            source_step_direction=self.relation.source_step_direction,
            target=self.relation.target,
            target_response_direction=self.relation.target_response_direction,
            selected_delay_horizon_seconds=self.relation.selected_delay_horizon_seconds,
            numeric_bindings=self.numeric_bindings,
            approved_evidence_identities=self.approved_evidence_identities,
            semantic_process_metadata=self.semantic_process_metadata,
        )


class _DirectLedger:
    def __init__(self) -> None:
        self._records: list[object] = []

    @property
    def records(self) -> tuple[object, ...]:
        return tuple(self._records)

    def append(self, record: object) -> None:
        self._records.append(record)


class DirectScientificSemanticsCohortAudit(unittest.TestCase):
    def test_only_direct_renderer_and_accounting_surfaces_changed(self) -> None:
        unchanged_files = (
            "src/paperworks/v6/task039e3_orchestration_v1.py",
            "src/paperworks/v6/task039e3_recovery_science_v2.py",
            "src/paperworks/v6/task039e3_scientific_execution_v1.py",
            "src/paperworks/v6/task039e3_r2r_request_contract_v1.py",
            "src/paperworks/v6/task039e3_execution_prep_v1.py",
            "src/paperworks/v6/task039e2_execution_freeze_prep_v1.py",
        )
        for path in unchanged_files:
            with self.subTest(path=path):
                self.assertEqual(_blob(FORENSIC_B, path), _blob(REMEDIATION_A, path))
        configuration = "src/paperworks/v6/task039e2_execution_configuration_v1.py"
        for name in (
            "render_main_initial_model_content_v1",
            "render_t2_followup_model_content_v1",
        ):
            self.assertEqual(
                _function_hash(FORENSIC_B, configuration, name),
                _function_hash(REMEDIATION_A, configuration, name),
            )
        self.assertNotEqual(
            _function_hash(FORENSIC_B, configuration, "render_direct_number_model_content_v1"),
            _function_hash(REMEDIATION_A, configuration, "render_direct_number_model_content_v1"),
        )

    def test_alias_faithful_full_cohort_completes_at_minimum_budget(self) -> None:
        evidence = tuple(AliasFaithfulEvidence(index) for index in range(1, 43))
        events: list[MockProviderEventV1] = []
        for item in evidence:
            events.extend(
                MockProviderEventV1("valid_proposal", valid_core_document(item))
                for _ in range(5)
            )
            events.append(MockProviderEventV1("valid_direct_number", direct_number_payload()))
        transport = MockProviderTransportV1(tuple(events))
        provider = ProviderCallLedgerV1()
        proposal = ConstructionProposalLedgerV1()
        outcome = ConstructionOutcomeLedgerV1()
        direct = _DirectLedger()
        result = run_injected_r2r_scientific_cohort_v1(
            relation_identities=tuple(item.relation.relation_identity for item in evidence),
            evidence_records=evidence,
            transport=transport,
            ledgers=ScientificLedgersV2(provider, proposal, outcome, direct),
            progress=lambda _message: None,
        )
        self.assertEqual(result.relation_count, 42)
        self.assertEqual(result.t0_outcomes, 42)
        self.assertEqual(result.t1_logical_calls, 42)
        self.assertEqual(result.t1b_logical_calls, 126)
        self.assertEqual(result.t2_logical_calls, 42)
        self.assertEqual(result.direct_number_logical_calls, 42)
        self.assertEqual(result.scientific_logical_calls, 252)
        self.assertEqual(result.scientific_concurrency, 1)
        self.assertEqual(result.scientific_generation_retries, 0)
        self.assertEqual(transport.calls, 252)
        self.assertEqual(len(provider.records), 252)
        self.assertEqual(len(proposal.records), 252)
        self.assertEqual(len(outcome.records), 168)
        self.assertEqual(len(direct.records), 42)

    def test_t2_three_call_fixture_preserves_126_and_336_ceilings(self) -> None:
        evidence = make_evidence(43)
        transport = MockProviderTransportV1(
            tuple(
                MockProviderEventV1("valid_proposal", valid_core_document(evidence))
                for _ in range(3)
            )
        )
        provider = ProviderCallLedgerV1()
        result = R2R_ARM_RUNNERS_V1.t2(
            relation_schedule_index=0,
            evidence=evidence,
            transport=transport,
            call_ledger=provider,
            proposal_ledger=ConstructionProposalLedgerV1(),
            outcome_ledger=ConstructionOutcomeLedgerV1(),
            retrieval_identity=evidence.approved_evidence_identities[0],
            synthetic_validity_faults=(
                "SYNTHETIC_REPAIRABLE_RETRIEVE",
                "SYNTHETIC_REPAIRABLE_RETRIEVE",
                "SYNTHETIC_REPAIRABLE_RETRIEVE",
            ),
        )
        self.assertEqual(result.outcome, "no_rule")
        self.assertEqual(result.generation_calls_consumed, 3)
        self.assertEqual(result.retrieval_count, 1)
        self.assertEqual(transport.calls, 3)
        self.assertEqual(len(provider.records), 3)
        self.assertEqual(42 * 3, 126)
        self.assertEqual(42 + 126 + 126 + 42, 336)


if __name__ == "__main__":
    unittest.main()
