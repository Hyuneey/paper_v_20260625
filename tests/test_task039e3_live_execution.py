from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e0_rule_construction_prep_v1 import (
    ApprovedNumericEvidenceBundleV1,
    ConfirmedRelationPrimitiveV1,
)
from paperworks.v6.task039e2_execution_configuration_v1 import (
    CALIBRATED_NUMERIC_ROLES,
    WINDOW_NUMERIC_ROLES,
)
from paperworks.v6.task039e3_scientific_execution_v1 import (
    project_real_evidence_v1,
    run_real_t0_v1,
    validate_private_roots_v1,
)
from paperworks.v6.task039e3_orchestration_v1 import (
    ConstructionOutcomeLedgerV1,
    ConstructionProposalLedgerV1,
)


def _hash(label: str) -> str:
    return stable_hash_v1({"test": label})


class LiveExecutionBoundaryTests(unittest.TestCase):
    def test_real_e1_projection_uses_same_bounded_prep_view(self) -> None:
        references = {
            role: _hash(role) for role in (
                *CALIBRATED_NUMERIC_ROLES,
                "selected_delay_horizon_seconds",
                *WINDOW_NUMERIC_ROLES,
            )
        }
        relation = ConfirmedRelationPrimitiveV1(
            relation_identity="directional_relation:test",
            source="P1_SOURCE",
            source_step_direction="step_up",
            target="P1_TARGET",
            target_response_direction="increase",
            selected_delay_horizon_seconds=5,
            approved_source_threshold_reference=references["source_step_threshold"],
            approved_source_stability_reference=references["source_stability_tolerance"],
            approved_target_scale_reference=references["target_noise_scale"],
            fit_evidence_reference=_hash("fit"),
            confirmation_evidence_reference=_hash("confirmation"),
        )
        numeric = ApprovedNumericEvidenceBundleV1(
            relation_binding_hash=relation.binding_hash,
            source_threshold_reference=references["source_step_threshold"],
            source_stability_reference=references["source_stability_tolerance"],
            target_scale_reference=references["target_noise_scale"],
            fit_evidence_reference=relation.fit_evidence_reference,
            confirmation_evidence_reference=relation.confirmation_evidence_reference,
            preregistered_window_constant_references=tuple(references[role] for role in WINDOW_NUMERIC_ROLES),
        )
        roles = (*CALIBRATED_NUMERIC_ROLES, "selected_delay_horizon_seconds", *WINDOW_NUMERIC_ROLES)
        raw_bindings = [
            {
                "numeric_role": role,
                "numeric_value": 5 if role == "selected_delay_horizon_seconds" else float(index + 1),
                "numeric_reference": references[role],
            }
            for index, role in enumerate(roles)
        ]
        private_content = {
            "relation_binding_hash": relation.binding_hash,
            "relation_identity": relation.relation_identity,
            "source": relation.source,
            "source_step_direction": relation.source_step_direction,
            "target": relation.target,
            "target_response_direction": relation.target_response_direction,
            "selected_horizon_seconds": 5,
            "d1_fit_evidence_hash": relation.fit_evidence_reference,
            "d2_confirmation_evidence_hash": relation.confirmation_evidence_reference,
            "numeric_bindings": raw_bindings,
        }
        private = dict(private_content, artifact_hash=stable_hash_v1(private_content))
        projected = project_real_evidence_v1(
            private_record=private,
            public_primitive=relation.to_dict(),
            public_bundle=numeric.to_dict(),
            public_manifest={"private_evidence_record_hash": private["artifact_hash"]},
        )
        view = projected.render_view()
        self.assertEqual(len(view.numeric_bindings), 10)
        self.assertNotIn("selected_delay_horizon_seconds", view.numeric_references)
        self.assertEqual(view.selected_delay_horizon_seconds, 5)
        self.assertNotIn("origin_arms", view.to_dict())
        proposals = ConstructionProposalLedgerV1()
        outcomes = ConstructionOutcomeLedgerV1()
        outcome = run_real_t0_v1(
            evidence=projected, proposal_ledger=proposals, outcome_ledger=outcomes
        )
        self.assertEqual(outcome.outcome, "accepted_proposal")
        self.assertEqual(outcome.generation_calls_consumed, 0)
        self.assertEqual(len(proposals.records), 1)

    def test_private_root_guards_reject_repository_containment(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repository = root / "repo"
            repository.mkdir()
            e1 = root / "e1"
            e1.mkdir()
            with self.assertRaisesRegex(Exception, "outside Git"):
                validate_private_roots_v1(
                    repository_root=repository,
                    e1_private_value=str(e1),
                    e3_private_value=str(repository / "private"),
                )

    def test_live_runner_is_only_credential_reader(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        live_module = (repository / "src/paperworks/v6/task039e3_scientific_execution_v1.py").read_text(encoding="utf-8")
        transport = (repository / "src/paperworks/v6/task039e3_live_transport_v1.py").read_text(encoding="utf-8")
        runner = (repository / "scripts/run_task039e3_scientific_execution.py").read_text(encoding="utf-8")
        self.assertNotIn("OPENAI_API_KEY", live_module)
        self.assertNotIn("OPENAI_API_KEY", transport)
        self.assertEqual(runner.count('os.environ.get("OPENAI_API_KEY")'), 1)
        self.assertNotIn("HAI_DATA_ROOT", runner + live_module + transport)


if __name__ == "__main__":
    unittest.main()
