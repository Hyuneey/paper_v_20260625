from __future__ import annotations

import copy
import dataclasses
import json
import unittest
from pathlib import Path

from paperworks.contracts import (
    AcceptedRuleError,
    DelayedResponseArtifactCollectionV1,
    DelayedResponseVerifierPolicyV1,
    canonical_rule_document_sha256,
    canonical_rule_verification_subject_bytes,
    canonical_rule_verification_subject_sha256,
    canonical_verifier_result_sha256,
    delayed_response_rule_to_dict,
    load_calibration_parameter,
    load_candidate_graph,
    load_delayed_response_rule,
    load_evidence_package,
    materialize_accepted_rule,
    parse_verifier_result,
    verifier_result_to_dict,
    verify_contract_artifact_hash,
    verify_delayed_response_rule,
)


ROOT = Path(__file__).resolve().parents[1]


def aligned_bundle():
    rule = load_delayed_response_rule(ROOT / "fixtures/task032d/rule_candidate.json")
    graph = load_candidate_graph(ROOT / "fixtures/task032c/graph_delayed_response.json")
    evidence = load_evidence_package(ROOT / "fixtures/task032c/evidence_delayed_response.json")
    parameters = tuple(
        load_calibration_parameter(path)
        for path in sorted((ROOT / "fixtures/task032d").glob("parameter_*.json"))
    )
    policy = DelayedResponseVerifierPolicyV1.from_dict(
        json.loads((ROOT / "fixtures/task032d/verifier_policy.json").read_text(encoding="utf-8"))
    )
    return rule, DelayedResponseArtifactCollectionV1(graph, evidence, parameters), policy


class Task032DAuthorityHashTests(unittest.TestCase):
    def test_subject_hash_excludes_only_authority_fields(self) -> None:
        rule, _, _ = aligned_bundle()
        document = delayed_response_rule_to_dict(rule)
        changed_authority = copy.deepcopy(document)
        changed_authority["status"] = "accepted"
        changed_authority["verified_rule_hash"] = "f" * 64
        self.assertEqual(
            canonical_rule_verification_subject_bytes(document),
            canonical_rule_verification_subject_bytes(changed_authority),
        )
        changed_science = copy.deepcopy(document)
        changed_science["lag"]["maximum"] = 4
        self.assertNotEqual(
            canonical_rule_verification_subject_sha256(document),
            canonical_rule_verification_subject_sha256(changed_science),
        )

    def test_materialization_is_new_immutable_and_runtime_unauthorized(self) -> None:
        rule, _, _ = aligned_bundle()
        before = delayed_response_rule_to_dict(rule)
        accepted = materialize_accepted_rule(rule)
        self.assertEqual(delayed_response_rule_to_dict(rule), before)
        self.assertEqual(accepted.status, "accepted")
        self.assertEqual(accepted.verified_rule_hash, canonical_rule_verification_subject_sha256(rule))
        self.assertEqual(
            canonical_rule_verification_subject_sha256(accepted),
            canonical_rule_verification_subject_sha256(rule),
        )
        self.assertNotEqual(canonical_rule_document_sha256(accepted), canonical_rule_document_sha256(rule))
        self.assertFalse(accepted.runtime_authorized)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            accepted.status = "candidate"  # type: ignore[misc]

    def test_materialization_rejects_preclaimed_authority(self) -> None:
        rule, _, _ = aligned_bundle()
        with self.assertRaises(AcceptedRuleError) as caught:
            materialize_accepted_rule(dataclasses.replace(rule, status="accepted"))
        self.assertEqual(caught.exception.issue_code, "RULE_AUTHORITY_PRECLAIMED")

    def test_accepted_outcome_binds_three_rule_hashes_and_result_self_hash(self) -> None:
        rule, artifacts, policy = aligned_bundle()
        outcome = verify_delayed_response_rule(rule, artifacts, policy=policy)
        self.assertEqual(outcome.verifier_result.status, "accepted")
        self.assertEqual(len(outcome.stage_records), 20)
        self.assertTrue(all(record.status == "passed" for record in outcome.stage_records))
        self.assertEqual(outcome.accepted_rule.verified_rule_hash, outcome.verification_subject_hash)
        self.assertEqual(outcome.verifier_result.rule_hash, outcome.verification_subject_hash)
        self.assertEqual(outcome.verifier_result_hash, outcome.verifier_result.artifact_hash)
        self.assertEqual(canonical_verifier_result_sha256(outcome.verifier_result), outcome.verifier_result_hash)
        self.assertEqual(verify_contract_artifact_hash(verifier_result_to_dict(outcome.verifier_result)), outcome.verifier_result_hash)
        self.assertFalse(outcome.runtime_authorized)
        self.assertFalse(outcome.verifier_result.runtime_authorized)

    def test_verifier_result_round_trip_and_determinism(self) -> None:
        rule, artifacts, policy = aligned_bundle()
        first = verify_delayed_response_rule(rule, artifacts, policy=policy)
        second = verify_delayed_response_rule(rule, artifacts, policy=policy)
        self.assertEqual(first, second)
        restored = parse_verifier_result(verifier_result_to_dict(first.verifier_result))
        self.assertEqual(restored, first.verifier_result)

    def test_stage_one_failure_records_all_later_stages_as_skipped(self) -> None:
        rule, artifacts, policy = aligned_bundle()
        bad_graph = dataclasses.replace(artifacts.graph, artifact_hash="0" * 64)
        bad_artifacts = DelayedResponseArtifactCollectionV1(bad_graph, artifacts.evidence, artifacts.parameters)
        outcome = verify_delayed_response_rule(rule, bad_artifacts, policy=policy)
        self.assertEqual(outcome.stage_records[0].status, "failed")
        self.assertTrue(all(record.status == "skipped_due_to_prior_failure" for record in outcome.stage_records[1:]))
        self.assertIsNone(outcome.accepted_rule)
        self.assertFalse(outcome.runtime_authorized)


if __name__ == "__main__":
    unittest.main()
