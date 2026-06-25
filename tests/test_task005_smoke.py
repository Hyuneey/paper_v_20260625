from __future__ import annotations

import json
import unittest
from pathlib import Path

from paperworks.candidates import (
    CandidateSmokeError,
    run_task005_smoke,
    validate_task005_smoke_report,
)
from paperworks.metadata import load_metadata_json


CONFIG_PATH = Path("configs/candidates/task005_metadata_same_stage_only_smoke.json")
METADATA_PATH = Path("configs/metadata/swat_variables.json")


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def load_feature_order() -> tuple[str, ...]:
    payload = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    return tuple(item["name"] for item in payload["variables"])


class Task005SmokeTests(unittest.TestCase):
    def test_smoke_report_fixture_passes_gate(self) -> None:
        config = load_config()
        report = run_task005_smoke(
            config=config,
            metadata=load_metadata_json(METADATA_PATH),
            feature_order=load_feature_order(),
            created_at="2026-06-25T00:00:00Z",
        )
        validate_task005_smoke_report(config=config, report=report)
        self.assertTrue(report.passed)
        self.assertEqual(report.candidate_policy_name, "metadata_same_stage_only_smoke")
        self.assertGreater(report.candidate_pair_count, 0)
        self.assertGreater(report.emitted_edge_count, 0)
        self.assertIn("This is a smoke feasibility result.", report.required_report_statements)

    def test_provenance_completeness_fixture(self) -> None:
        report = run_task005_smoke(
            config=load_config(),
            metadata=load_metadata_json(METADATA_PATH),
            feature_order=load_feature_order(),
            created_at="2026-06-25T00:00:00Z",
        )
        required = {
            "candidate_origins",
            "source",
            "target",
            "rank",
            "score",
            "seed",
            "K",
            "config_hash",
            "data_manifest_reference",
        }
        for candidate in report.emitted_candidates:
            self.assertTrue(required.issubset(candidate))
            self.assertEqual(len(candidate["config_hash"]), 64)
            self.assertEqual(len(candidate["data_manifest_reference"]), 64)
            self.assertEqual(candidate["candidate_origins"], ["domain"])

    def test_deterministic_report_generation(self) -> None:
        config = load_config()
        first = run_task005_smoke(
            config=config,
            metadata=load_metadata_json(METADATA_PATH),
            feature_order=load_feature_order(),
            created_at="2026-06-25T00:00:00Z",
        )
        second = run_task005_smoke(
            config=config,
            metadata=load_metadata_json(METADATA_PATH),
            feature_order=load_feature_order(),
            created_at="2026-06-25T00:00:00Z",
        )
        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertEqual(first.report_id, second.report_id)

    def test_missing_run_detection(self) -> None:
        config = load_config()
        report = run_task005_smoke(
            config=config,
            metadata=load_metadata_json(METADATA_PATH),
            feature_order=load_feature_order(),
            created_at="2026-06-25T00:00:00Z",
        )
        config["pass_fail_gate"]["required_checks"].append("missing_configured_run")
        with self.assertRaises(CandidateSmokeError):
            validate_task005_smoke_report(config=config, report=report)

    def test_no_test_role_guard_via_config_validation(self) -> None:
        config = load_config()
        config["candidate_origins"]["normal_statistical_top_m"] = True
        with self.assertRaises(CandidateSmokeError):
            run_task005_smoke(
                config=config,
                metadata=load_metadata_json(METADATA_PATH),
                feature_order=load_feature_order(),
            )


if __name__ == "__main__":
    unittest.main()
