from __future__ import annotations

import ast
import json
import unittest
from pathlib import Path

from paperworks.contracts import (
    DelayedResponseArtifactCollectionV1,
    DelayedResponseVerifierPolicyV1,
    LegacyDelayedResponseCollectionAdapterV1,
    authorize_delayed_response_runtime,
    load_calibration_parameter,
    load_candidate_graph,
    load_delayed_response_rule,
    load_evidence_package,
    parse_verifier_result,
    verify_delayed_response_rule,
    verify_task032f_deterministic_replay,
)


ROOT = Path(__file__).resolve().parents[1]
ACCEPTED_RULE_HASH = (
    "1b3b5d7f7e059028c2ec83c64c82f7627c9623330ea75f0b37668b64c00d44a2"
)
VERIFIER_RESULT_HASH = (
    "1efeb258886e46a4f311e039d1fb28528ad56d224f4a9498ad459f08a739eaef"
)
AUTHORIZATION_HASH = (
    "ebfbfcd147fa078577f77c8a0fd0cbfbf508c0afaf77d27e71f5c5a918032ef9"
)
TASK032F_REPORT_HASH = (
    "d9474108994708c553fe558ff8dca493ab3d57adfff934de4a42fdccd3d3fa35"
)


def _legacy_collection() -> DelayedResponseArtifactCollectionV1:
    return DelayedResponseArtifactCollectionV1(
        load_candidate_graph(
            ROOT / "fixtures/task032c/graph_delayed_response.json"
        ),
        load_evidence_package(
            ROOT / "fixtures/task032c/evidence_delayed_response.json"
        ),
        tuple(
            load_calibration_parameter(path)
            for path in sorted(
                (ROOT / "fixtures/task032d").glob("parameter_*.json")
            )
        ),
    )


def _policy() -> DelayedResponseVerifierPolicyV1:
    return DelayedResponseVerifierPolicyV1.from_dict(
        json.loads(
            (
                ROOT / "fixtures/task032d/verifier_policy.json"
            ).read_text(encoding="utf-8")
        )
    )


class Task039P1CLegacyCompatibilityTests(unittest.TestCase):
    def test_legacy_verifier_and_authorization_hashes_are_unchanged(self) -> None:
        collection = _legacy_collection()
        candidate = load_delayed_response_rule(
            ROOT / "fixtures/task032d/rule_candidate.json"
        )
        outcome = verify_delayed_response_rule(
            candidate, collection, policy=_policy()
        )
        self.assertEqual(
            outcome.accepted_rule.verified_rule_hash,
            ACCEPTED_RULE_HASH,
        )
        self.assertEqual(outcome.verifier_result.artifact_hash, VERIFIER_RESULT_HASH)

        accepted = load_delayed_response_rule(
            ROOT / "fixtures/task032e/accepted_rule.json"
        )
        result = parse_verifier_result(
            json.loads(
                (
                    ROOT / "fixtures/task032e/verifier_result.json"
                ).read_text(encoding="utf-8")
            )
        )
        bundle = authorize_delayed_response_runtime(
            accepted,
            result,
            collection,
            verifier_policy=_policy(),
            created_at="2026-07-14T18:45:00Z",
        )
        self.assertEqual(bundle.receipt.authorization_hash, AUTHORIZATION_HASH)

    def test_legacy_wrapper_delegates_exact_objects_and_lookups(self) -> None:
        source = _legacy_collection()
        wrapper = LegacyDelayedResponseCollectionAdapterV1(source)
        self.assertIs(wrapper.legacy_collection, source)
        self.assertIs(wrapper.graph, source.graph)
        self.assertIs(wrapper.evidence, source.evidence)
        self.assertEqual(wrapper.parameters, source.parameters)
        self.assertEqual(wrapper.graph_by_id, source.graph_by_id)
        self.assertEqual(wrapper.normal_reference_by_id, source.normal_reference_by_id)
        self.assertFalse(wrapper.rule_binding_verified)
        self.assertFalse(wrapper.runtime_authorized)

    def test_task032f_deterministic_replay_remains_exact(self) -> None:
        result = verify_task032f_deterministic_replay(
            ROOT / "configs/contracts/task032f_synthetic_vertical_slice.json"
        )
        self.assertEqual(result["status"], "deterministic_replay_verified")
        self.assertEqual(result["first_report_hash"], TASK032F_REPORT_HASH)
        self.assertEqual(result["first_report_hash"], result["second_report_hash"])

    def test_verifier_and_runtime_do_not_import_phase1_collection(self) -> None:
        for relative in (
            "src/paperworks/contracts/verifier_v1.py",
            "src/paperworks/contracts/runtime_authority.py",
        ):
            with self.subTest(path=relative):
                tree = ast.parse(
                    (ROOT / relative).read_text(encoding="utf-8"),
                    filename=relative,
                )
                modules = {
                    node.module
                    for node in ast.walk(tree)
                    if isinstance(node, ast.ImportFrom)
                }
                self.assertNotIn(
                    "paperworks.contracts.phase1_adapters",
                    modules,
                )


if __name__ == "__main__":
    unittest.main()
