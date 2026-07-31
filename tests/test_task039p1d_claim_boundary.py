from __future__ import annotations

import json
import tomllib
import unittest
from pathlib import Path

from paperworks.gdn.fidelity_v1 import GDNFidelityClassV1
from tests.task039p1d_support import make_fidelity_freeze


ROOT = Path(__file__).resolve().parents[1]


class Task039P1DClaimBoundaryTests(unittest.TestCase):
    def test_torch_dependencies_are_optional_with_unchanged_pins(self) -> None:
        project = tomllib.loads(
            (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )["project"]
        self.assertEqual(
            project["dependencies"],
            ["jsonschema[format-nongpl]==4.26.0"],
        )
        self.assertEqual(
            project["optional-dependencies"]["gdn"],
            ["torch==2.12.1", "torch-geometric==2.8.0"],
        )

    def test_only_validated_future_backend_can_be_called_gdn_in_rq1(self) -> None:
        freeze = make_fidelity_freeze()
        self.assertEqual(
            freeze.required_rq1_fidelity_class,
            GDNFidelityClassV1.UPSTREAM_ALIGNED_VALIDATED.value,
        )
        self.assertTrue(
            all(
                not record.scientific_gdn_claim_allowed
                and not record.production_candidate_ranking_allowed
                for record in freeze.backend_records
            )
        )
        self.assertEqual(
            freeze.production_backend_decision,
            "pending_TASK039A_B_feasibility",
        )

    def test_claim_documents_prohibit_smoke_backend_scientific_use(self) -> None:
        policy = (
            ROOT / "docs/v6/V6_GDN_BACKEND_USE_POLICY.md"
        ).read_text(encoding="utf-8")
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        report = json.loads(
            (
                ROOT / "docs/task_reports/TASK-039P1D_FIDELITY_REPORT.json"
            ).read_text(encoding="utf-8")
        )
        self.assertIn("upstream_aligned_validated", policy)
        self.assertIn("synthetic_smoke_only", policy)
        self.assertIn("must not be used for HAI candidate ranking", policy)
        self.assertIn("TASK-039P1D", agents)
        self.assertFalse(
            report["future_policy"]["existing_smoke_backend_may_be_called_GDN_in_RQ1"]
        )


if __name__ == "__main__":
    unittest.main()
