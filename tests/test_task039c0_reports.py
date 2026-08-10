from __future__ import annotations

import json
import re
import unittest
from copy import deepcopy
from pathlib import Path

from jsonschema import Draft202012Validator

from paperworks.v6.candidate_discovery_protocol_v1 import (
    CandidateDiscoveryProtocolBundleV1,
)
from paperworks.v6.common import stable_hash_v1
from paperworks.v6.schema_registry_v1 import load_v6_schema_registry_v1


ROOT = Path(__file__).resolve().parents[1]
C0_TYPES = (
    "candidate_universe_policy_v1",
    "candidate_budget_policy_v1",
    "metadata_candidate_policy_v1",
    "statistical_candidate_policy_v1",
    "gdn_candidate_policy_v1",
    "candidate_arm_result_contract_v1",
    "candidate_integration_policy_v1",
    "task039c0_data_access_policy_v1",
    "task039c0_parallel_branch_plan_v1",
    "candidate_discovery_protocol_bundle_v1",
)
PUBLIC_OUTPUTS = (
    "TASKS/TASK-039C0_CANDIDATE_DISCOVERY_PROTOCOL.md",
    "docs/v6/CANDIDATE_DISCOVERY_COMMON_UNIVERSE.md",
    "docs/v6/CANDIDATE_DISCOVERY_METADATA_POLICY.md",
    "docs/v6/CANDIDATE_DISCOVERY_STATISTICAL_POLICY.md",
    "docs/v6/CANDIDATE_DISCOVERY_GDN_POLICY.md",
    "docs/v6/CANDIDATE_DISCOVERY_INTEGRATION_POLICY.md",
    "docs/v6/CANDIDATE_DISCOVERY_ANTI_LEAKAGE.md",
    "docs/task_reports/TASK-039C0_PROTOCOL_BUNDLE.json",
    "docs/task_reports/TASK-039C0_PARALLEL_BRANCH_PLAN.json",
    "docs/task_reports/TASK-039C0_DATA_ACCESS_POLICY.json",
    "docs/task_reports/TASK-039C0_REPORT.md",
)


def _load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def _assert_closed(test: unittest.TestCase, schema: object) -> None:
    if isinstance(schema, dict):
        if schema.get("type") == "object":
            test.assertIs(schema.get("additionalProperties"), False)
        for value in schema.values():
            _assert_closed(test, value)
    elif isinstance(schema, list):
        for value in schema:
            _assert_closed(test, value)


class Task039C0ReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bundle_payload = _load(
            "docs/task_reports/TASK-039C0_PROTOCOL_BUNDLE.json"
        )
        cls.bundle = CandidateDiscoveryProtocolBundleV1.from_dict(
            cls.bundle_payload
        )

    def test_config_self_hash_and_lineage(self) -> None:
        config = _load("configs/v6/task039c0_candidate_discovery_protocol.json")
        expected = config.pop("config_hash")
        self.assertEqual(stable_hash_v1(config), expected)
        self.assertEqual(
            config["frozen_lineage"]["selected_process_id"], "P1"
        )

    def test_protocol_hashes_and_counts(self) -> None:
        universe = self.bundle.universe_policy
        self.assertEqual(
            self.bundle.artifact_hash,
            "41aab751d6bbbaadc72a95ef3289ea6440c26659fb38f640bf17fb0688836dff",
        )
        self.assertEqual(universe.eligible_pair_count, 144)
        self.assertEqual(
            universe.source_identity_list_hash,
            "0af3f80f18a3eab59b9783af64d306c8d774eeb69b3a72c24c10048abd4ed234",
        )
        self.assertEqual(
            universe.target_identity_list_hash,
            "063037980aae4f0eaf45fbebb59f2aa0a924fbad583f3818107a793dfe7248e7",
        )
        self.assertEqual(
            universe.eligible_pair_universe_hash,
            "fc072d3e18ce4623972c2cb64f6266727092ecae03fdb0f0dd929d705e1d8557",
        )

    def test_public_artifact_self_hashes(self) -> None:
        for relative in (
            "docs/task_reports/TASK-039C0_PROTOCOL_BUNDLE.json",
            "docs/task_reports/TASK-039C0_PARALLEL_BRANCH_PLAN.json",
            "docs/task_reports/TASK-039C0_DATA_ACCESS_POLICY.json",
        ):
            payload = _load(relative)
            observed = payload.pop("artifact_hash")
            self.assertEqual(stable_hash_v1(payload), observed, relative)

    def test_schemas_registered_meta_valid_and_closed(self) -> None:
        registry = load_v6_schema_registry_v1(repository_root=ROOT)
        self.assertEqual(len(registry.artifact_types), 80)
        for artifact_type in C0_TYPES:
            schema = registry.schema_for(artifact_type)
            Draft202012Validator.check_schema(schema)
            _assert_closed(self, schema)

    def test_generated_instances_validate(self) -> None:
        registry = load_v6_schema_registry_v1(repository_root=ROOT)
        objects = {
            "candidate_universe_policy_v1": self.bundle.universe_policy.to_dict(),
            "candidate_budget_policy_v1": self.bundle.budget_policy.to_dict(),
            "metadata_candidate_policy_v1": self.bundle.metadata_policy.to_dict(),
            "statistical_candidate_policy_v1": self.bundle.statistical_policy.to_dict(),
            "gdn_candidate_policy_v1": self.bundle.gdn_policy.to_dict(),
            "candidate_arm_result_contract_v1": self.bundle.arm_result_contract.to_dict(),
            "candidate_integration_policy_v1": self.bundle.integration_policy.to_dict(),
            "task039c0_data_access_policy_v1": self.bundle.data_access_policy.to_dict(),
            "task039c0_parallel_branch_plan_v1": self.bundle.parallel_branch_plan.to_dict(),
            "candidate_discovery_protocol_bundle_v1": self.bundle.to_dict(),
        }
        for artifact_type, payload in objects.items():
            Draft202012Validator(
                registry.schema_for(artifact_type)
            ).validate(payload)

    def test_required_public_outputs_exist(self) -> None:
        for relative in PUBLIC_OUTPUTS:
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_parallel_branch_plan_is_exact(self) -> None:
        self.assertEqual(
            self.bundle.parallel_branch_plan.parallel_branches,
            (
                "task-039c-meta",
                "task-039c-stat",
                "task-039c-gdn",
                "task-039c-review",
                "task-039c-integration",
            ),
        )
        self.assertTrue(self.bundle.parallel_branch_plan.all_initial_refs_must_equal)
        self.assertFalse(self.bundle.parallel_branch_plan.main_merge_authorized)

    def test_public_outputs_contain_no_absolute_local_path(self) -> None:
        pattern = re.compile(r"[A-Za-z]:[\\/](?:Users|Documents|Desktop)[\\/]", re.I)
        for relative in PUBLIC_OUTPUTS:
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIsNone(pattern.search(text), relative)

    def test_no_result_artifact_claims_execution(self) -> None:
        self.assertFalse(self.bundle.real_hai_feature_access)
        self.assertFalse(self.bundle.candidate_discovery_executed)
        self.assertFalse(self.bundle.final_candidate_universe_created)
        self.assertNotIn("candidate_ranking_results", self.bundle_payload)

    def test_bundle_unknown_field_is_schema_rejected(self) -> None:
        payload = deepcopy(self.bundle_payload)
        payload["unexpected"] = True
        registry = load_v6_schema_registry_v1(repository_root=ROOT)
        with self.assertRaises(Exception):
            Draft202012Validator(
                registry.schema_for("candidate_discovery_protocol_bundle_v1")
            ).validate(payload)


if __name__ == "__main__":
    unittest.main()
