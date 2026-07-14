from __future__ import annotations

import copy
import dataclasses
import json
import unittest
from pathlib import Path

from paperworks.contracts import (
    DelayedResponseArtifactCollectionV1,
    DelayedResponseVerifierPolicyV1,
    RuntimeAuthorizationBundleV1,
    RuntimeAuthorizationError,
    authorize_delayed_response_runtime,
    canonical_runtime_authorization_sha256,
    load_calibration_parameter,
    load_candidate_graph,
    load_delayed_response_rule,
    load_evidence_package,
    parse_verifier_result,
    verifier_result_to_dict,
    with_computed_artifact_hash,
)


ROOT = Path(__file__).resolve().parents[1]


def authorization_inputs():
    rule = load_delayed_response_rule(ROOT / "fixtures/task032e/accepted_rule.json")
    result = parse_verifier_result(json.loads((ROOT / "fixtures/task032e/verifier_result.json").read_text(encoding="utf-8")))
    graph = load_candidate_graph(ROOT / "fixtures/task032c/graph_delayed_response.json")
    evidence = load_evidence_package(ROOT / "fixtures/task032c/evidence_delayed_response.json")
    parameters = tuple(load_calibration_parameter(path) for path in sorted((ROOT / "fixtures/task032d").glob("parameter_*.json")))
    policy = DelayedResponseVerifierPolicyV1.from_dict(json.loads((ROOT / "fixtures/task032d/verifier_policy.json").read_text(encoding="utf-8")))
    return rule, result, DelayedResponseArtifactCollectionV1(graph, evidence, parameters), policy


def authorized_bundle() -> RuntimeAuthorizationBundleV1:
    rule, result, artifacts, policy = authorization_inputs()
    return authorize_delayed_response_runtime(
        rule, result, artifacts, verifier_policy=policy,
        created_at="2026-07-14T18:45:00Z",
    )


class Task032ERuntimeAuthorityTests(unittest.TestCase):
    def test_valid_binding_creates_only_authorized_bundle(self) -> None:
        rule, result, artifacts, policy = authorization_inputs()
        self.assertFalse(rule.runtime_authorized)
        self.assertFalse(result.runtime_authorized)
        self.assertFalse(artifacts.runtime_authorized)
        manual = RuntimeAuthorizationBundleV1(rule, result, artifacts, policy, authorized_bundle().receipt)
        self.assertFalse(manual.runtime_authorized)
        bundle = authorized_bundle()
        self.assertTrue(bundle.runtime_authorized)
        self.assertEqual(canonical_runtime_authorization_sha256(bundle.receipt), bundle.receipt.authorization_hash)
        self.assertEqual(bundle.receipt.accepted_rule_hash, rule.verified_rule_hash)

    def test_missing_and_rule_hash_mismatch_fail(self) -> None:
        rule, result, artifacts, policy = authorization_inputs()
        with self.assertRaises(RuntimeAuthorizationError) as missing:
            authorize_delayed_response_runtime(None, result, artifacts, verifier_policy=policy, created_at="2026-07-14T18:45:00Z")
        self.assertEqual(missing.exception.issue_code, "RUNTIME_RULE_MISSING")
        with self.assertRaises(RuntimeAuthorizationError) as mismatch:
            authorize_delayed_response_runtime(dataclasses.replace(rule, verified_rule_hash="f" * 64), result, artifacts, verifier_policy=policy, created_at="2026-07-14T18:45:00Z")
        self.assertEqual(mismatch.exception.issue_code, "RUNTIME_RULE_HASH_MISMATCH")

    def test_verifier_hash_id_and_policy_mismatch_fail(self) -> None:
        rule, result, artifacts, policy = authorization_inputs()
        with self.assertRaises(RuntimeAuthorizationError):
            authorize_delayed_response_runtime(rule, dataclasses.replace(result, artifact_hash="0" * 64), artifacts, verifier_policy=policy, created_at="2026-07-14T18:45:00Z")
        changed = verifier_result_to_dict(result)
        changed["verifier_result_id"] = "VERIFY-AAAAAAAAAAAAAAAAAAAA"
        changed_result = parse_verifier_result(with_computed_artifact_hash(changed))
        with self.assertRaises(RuntimeAuthorizationError) as bad_id:
            authorize_delayed_response_runtime(rule, changed_result, artifacts, verifier_policy=policy, created_at="2026-07-14T18:45:00Z")
        self.assertEqual(bad_id.exception.issue_code, "VERIFIER_RESULT_ID_MISMATCH")
        bad_policy = dataclasses.replace(policy, verifier_version="other-verifier")
        with self.assertRaises(RuntimeAuthorizationError) as policy_error:
            authorize_delayed_response_runtime(rule, result, artifacts, verifier_policy=bad_policy, created_at="2026-07-14T18:45:00Z")
        self.assertEqual(policy_error.exception.issue_code, "VERIFIER_POLICY_MISMATCH")

    def test_external_hash_mismatches_fail(self) -> None:
        rule, result, artifacts, policy = authorization_inputs()
        for changed in (
            DelayedResponseArtifactCollectionV1(dataclasses.replace(artifacts.graph, artifact_hash="0" * 64), artifacts.evidence, artifacts.parameters),
            DelayedResponseArtifactCollectionV1(artifacts.graph, dataclasses.replace(artifacts.evidence, artifact_hash="0" * 64), artifacts.parameters),
            DelayedResponseArtifactCollectionV1(artifacts.graph, artifacts.evidence, (dataclasses.replace(artifacts.parameters[0], artifact_hash="0" * 64),) + artifacts.parameters[1:]),
        ):
            with self.assertRaises(RuntimeAuthorizationError):
                authorize_delayed_response_runtime(rule, result, changed, verifier_policy=policy, created_at="2026-07-14T18:45:00Z")

    def test_verified_reference_set_mismatch_fails(self) -> None:
        rule, result, artifacts, policy = authorization_inputs()
        for field_name in ("verified_graph_edges", "verified_evidence", "verified_normal_references", "verified_parameters"):
            changed = verifier_result_to_dict(result)
            changed[field_name] = []
            changed_result = parse_verifier_result(with_computed_artifact_hash(changed))
            with self.assertRaises(RuntimeAuthorizationError):
                authorize_delayed_response_runtime(rule, changed_result, artifacts, verifier_policy=policy, created_at="2026-07-14T18:45:00Z")

    def test_authorization_preserves_inputs(self) -> None:
        rule, result, artifacts, policy = authorization_inputs()
        before = copy.deepcopy((rule, result, artifacts, policy))
        authorize_delayed_response_runtime(rule, result, artifacts, verifier_policy=policy, created_at="2026-07-14T18:45:00Z")
        self.assertEqual((rule, result, artifacts, policy), before)

    def test_tampered_authorized_bundle_fails_execution_revalidation(self) -> None:
        bundle = authorized_bundle()
        changed_receipt = dataclasses.replace(bundle.receipt, graph_hash="f" * 64)
        changed = dataclasses.replace(bundle, receipt=changed_receipt)
        self.assertTrue(changed.runtime_authorized)
        from paperworks.contracts import execute_delayed_response_rule, load_runtime_window, RuntimeV1Error
        runtime_window = load_runtime_window(ROOT / "fixtures/task032e/window_response_present.json")
        with self.assertRaises(RuntimeV1Error):
            execute_delayed_response_rule(changed, runtime_window)


if __name__ == "__main__":
    unittest.main()
