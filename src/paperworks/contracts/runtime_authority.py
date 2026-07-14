"""Fail-closed runtime authorization for accepted delayed-response rules."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping

from paperworks.contracts.accepted_rule import canonical_rule_verification_subject_sha256
from paperworks.contracts.artifact_hashing import ContractArtifactHashError, verify_contract_artifact_hash
from paperworks.contracts.evidence_v1 import evidence_package_to_dict, parse_evidence_package
from paperworks.contracts.graph_v1 import candidate_graph_to_dict, parse_candidate_graph
from paperworks.contracts.parameter_v1 import calibration_parameter_to_dict, parse_calibration_parameter
from paperworks.contracts.phase1_adapters import DelayedResponseArtifactCollectionV1
from paperworks.contracts.rule_v1 import DelayedResponseRuleV1, delayed_response_rule_to_dict, parse_delayed_response_rule
from paperworks.contracts.verifier_v1 import (
    DelayedResponseVerifierPolicyV1,
    VerifierResultV1,
    VerifierV1Error,
    verifier_result_to_dict,
    verify_verifier_result_binding,
)


AUTHORIZATION_VERSION = "1.0.0"
_AUTHORIZATION_CAPABILITY = object()


class RuntimeAuthorizationError(ValueError):
    def __init__(self, issue_code: str, message: str) -> None:
        super().__init__(f"{issue_code}: {message}")
        self.issue_code = issue_code
        self.message = message


@dataclass(frozen=True)
class RuntimeAuthorizationReceiptV1:
    authorization_id: str
    authorization_version: str
    authorization_hash: str
    accepted_rule_id: str
    accepted_rule_hash: str
    verifier_result_id: str
    verifier_result_hash: str
    verifier_version: str
    graph_id: str
    graph_hash: str
    evidence_id: str
    evidence_hash: str
    parameter_hashes: tuple[tuple[str, str], ...]
    verifier_policy_hash: str
    runtime_scope: str
    created_at: str


@dataclass(frozen=True)
class RuntimeAuthorizationBundleV1:
    accepted_rule: DelayedResponseRuleV1
    verifier_result: VerifierResultV1
    artifacts: DelayedResponseArtifactCollectionV1
    verifier_policy: DelayedResponseVerifierPolicyV1
    receipt: RuntimeAuthorizationReceiptV1
    _capability: object | None = field(default=None, repr=False, compare=False)

    @property
    def runtime_authorized(self) -> bool:
        return self._capability is _AUTHORIZATION_CAPABILITY


def authorization_receipt_to_dict(receipt: RuntimeAuthorizationReceiptV1) -> dict[str, Any]:
    return {
        "authorization_id": receipt.authorization_id,
        "authorization_version": receipt.authorization_version,
        "authorization_hash": receipt.authorization_hash,
        "accepted_rule_id": receipt.accepted_rule_id,
        "accepted_rule_hash": receipt.accepted_rule_hash,
        "verifier_result_id": receipt.verifier_result_id,
        "verifier_result_hash": receipt.verifier_result_hash,
        "verifier_version": receipt.verifier_version,
        "graph_id": receipt.graph_id,
        "graph_hash": receipt.graph_hash,
        "evidence_id": receipt.evidence_id,
        "evidence_hash": receipt.evidence_hash,
        "parameter_hashes": {key: value for key, value in receipt.parameter_hashes},
        "verifier_policy_hash": receipt.verifier_policy_hash,
        "runtime_scope": receipt.runtime_scope,
        "created_at": receipt.created_at,
    }


def canonical_runtime_authorization_bytes(document: Mapping[str, Any] | RuntimeAuthorizationReceiptV1) -> bytes:
    payload = authorization_receipt_to_dict(document) if isinstance(document, RuntimeAuthorizationReceiptV1) else copy.deepcopy(dict(document))
    payload.pop("authorization_hash", None)
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")


def canonical_runtime_authorization_sha256(document: Mapping[str, Any] | RuntimeAuthorizationReceiptV1) -> str:
    return hashlib.sha256(canonical_runtime_authorization_bytes(document)).hexdigest()


def canonical_verifier_policy_sha256(policy: DelayedResponseVerifierPolicyV1) -> str:
    payload = json.dumps(policy.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def authorize_delayed_response_runtime(
    accepted_rule: DelayedResponseRuleV1 | None,
    verifier_result: VerifierResultV1,
    artifacts: DelayedResponseArtifactCollectionV1,
    *,
    verifier_policy: DelayedResponseVerifierPolicyV1,
    created_at: str,
    runtime_scope: str = "synthetic_only",
) -> RuntimeAuthorizationBundleV1:
    if accepted_rule is None:
        _fail("RUNTIME_RULE_MISSING", "accepted rule is required")
    if accepted_rule.status != "accepted" or accepted_rule.verified_rule_hash is None:
        _fail("RUNTIME_RULE_NOT_ACCEPTED", "rule lacks accepted authority fields")
    if verifier_result.status != "accepted":
        _fail("RUNTIME_VERIFIER_NOT_ACCEPTED", "verifier result is not accepted")
    if runtime_scope != "synthetic_only":
        _fail("RUNTIME_SCOPE_PROHIBITED", "TASK-032E permits synthetic_only scope")
    if not created_at:
        _fail("RUNTIME_AUTHORIZATION_TIME_MISSING", "created_at must be supplied")
    try:
        parsed_time = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        if parsed_time.utcoffset() is None:
            raise ValueError("timezone is required")
    except ValueError:
        _fail("RUNTIME_AUTHORIZATION_TIME_INVALID", "created_at must be RFC3339-compatible")

    _reparse_inputs(accepted_rule, artifacts)
    subject_hash = canonical_rule_verification_subject_sha256(accepted_rule)
    if accepted_rule.verified_rule_hash != subject_hash or verifier_result.rule_hash != subject_hash:
        _fail("RUNTIME_RULE_HASH_MISMATCH", "accepted rule and verifier result hashes disagree")
    try:
        verify_verifier_result_binding(
            accepted_rule,
            verifier_result,
            artifacts,
            policy=verifier_policy,
        )
    except VerifierV1Error as exc:
        _fail(exc.issue_code, exc.message)

    rule = accepted_rule
    evidence = artifacts.evidence
    parameter_ids = tuple(sorted(item.parameter_id for item in artifacts.parameters))
    if parameter_ids != tuple(sorted(rule.parameter_refs)):
        _fail("RUNTIME_PARAMETER_SET_MISMATCH", "parameter artifacts do not exactly match rule references")
    if tuple(sorted(verifier_result.verified_parameters)) != parameter_ids:
        _fail("RUNTIME_VERIFIED_PARAMETER_MISMATCH", "verified parameter set differs")
    if tuple(sorted(verifier_result.verified_graph_edges)) != tuple(sorted(rule.graph_edge_refs)):
        _fail("RUNTIME_VERIFIED_EDGE_MISMATCH", "verified edge set differs")
    if tuple(sorted(verifier_result.verified_evidence)) != tuple(sorted(rule.evidence_refs)):
        _fail("RUNTIME_VERIFIED_EVIDENCE_MISMATCH", "verified evidence set differs")
    if tuple(sorted(verifier_result.verified_normal_references)) != tuple(sorted(rule.normal_reference_refs)):
        _fail("RUNTIME_VERIFIED_NORMAL_MISMATCH", "verified normal-reference set differs")
    if rule.graph_edge_refs[0] not in artifacts.edge_by_id or rule.evidence_refs != (evidence.evidence_id,):
        _fail("RUNTIME_EXTERNAL_REFERENCE_MISMATCH", "external references are absent")
    if not (
        artifacts.graph.dataset_version == evidence.dataset_version == rule.dataset_version
        and evidence.operating_regime == rule.operating_regime.regime_id
        and evidence.source_variables == rule.source_variables
        and evidence.target_variables == rule.target_variables
    ):
        _fail("RUNTIME_CONTEXT_BINDING_MISMATCH", "dataset, regime, or variables differ")
    for parameter in artifacts.parameters:
        if not (
            parameter.dataset_version == rule.dataset_version
            and parameter.operating_regime == rule.operating_regime.regime_id
            and parameter.source_variables == rule.source_variables
            and parameter.target_variables == rule.target_variables
        ):
            _fail("RUNTIME_PARAMETER_BINDING_MISMATCH", "parameter context differs")

    parameter_hashes = tuple(sorted((item.parameter_id, item.artifact_hash) for item in artifacts.parameters))
    base = {
        "authorization_id": "AUTH-PENDING",
        "authorization_version": AUTHORIZATION_VERSION,
        "authorization_hash": "0" * 64,
        "accepted_rule_id": rule.rule_id,
        "accepted_rule_hash": subject_hash,
        "verifier_result_id": verifier_result.verifier_result_id,
        "verifier_result_hash": verifier_result.artifact_hash,
        "verifier_version": verifier_result.verifier_version,
        "graph_id": artifacts.graph.graph_id,
        "graph_hash": artifacts.graph.artifact_hash,
        "evidence_id": evidence.evidence_id,
        "evidence_hash": evidence.artifact_hash,
        "parameter_hashes": dict(parameter_hashes),
        "verifier_policy_hash": canonical_verifier_policy_sha256(verifier_policy),
        "runtime_scope": runtime_scope,
        "created_at": created_at,
    }
    base["authorization_id"] = _authorization_id_from_document(base)
    base["authorization_hash"] = canonical_runtime_authorization_sha256(base)
    receipt = _typed_receipt(base)
    if canonical_runtime_authorization_sha256(receipt) != receipt.authorization_hash:
        _fail("RUNTIME_AUTHORIZATION_HASH_MISMATCH", "authorization receipt failed self-hash")
    bundle = RuntimeAuthorizationBundleV1(
        rule, verifier_result, artifacts, verifier_policy, receipt, _AUTHORIZATION_CAPABILITY
    )
    verify_runtime_authorization_bundle(bundle)
    return bundle


def verify_runtime_authorization_bundle(bundle: RuntimeAuthorizationBundleV1) -> str:
    """Revalidate every receipt and verifier binding before execution."""

    if not isinstance(bundle, RuntimeAuthorizationBundleV1) or not bundle.runtime_authorized:
        _fail("RUNTIME_NOT_AUTHORIZED", "authorized runtime bundle is required")
    receipt = bundle.receipt
    if canonical_runtime_authorization_sha256(receipt) != receipt.authorization_hash:
        _fail("RUNTIME_AUTHORIZATION_HASH_MISMATCH", "authorization receipt failed self-hash")
    if _authorization_id_from_document(authorization_receipt_to_dict(receipt)) != receipt.authorization_id:
        _fail("RUNTIME_AUTHORIZATION_ID_MISMATCH", "authorization identifier does not recompute")
    rule, result, artifacts, policy = (
        bundle.accepted_rule, bundle.verifier_result, bundle.artifacts, bundle.verifier_policy,
    )
    expected_parameters = tuple(sorted((item.parameter_id, item.artifact_hash) for item in artifacts.parameters))
    checks = (
        (receipt.authorization_version == AUTHORIZATION_VERSION, "RUNTIME_AUTHORIZATION_VERSION_MISMATCH"),
        (receipt.runtime_scope == "synthetic_only", "RUNTIME_SCOPE_PROHIBITED"),
        (receipt.accepted_rule_id == rule.rule_id and receipt.accepted_rule_hash == rule.verified_rule_hash, "RUNTIME_AUTHORIZATION_RULE_MISMATCH"),
        (receipt.verifier_result_id == result.verifier_result_id and receipt.verifier_result_hash == result.artifact_hash, "RUNTIME_AUTHORIZATION_VERIFIER_MISMATCH"),
        (receipt.verifier_version == result.verifier_version, "RUNTIME_AUTHORIZATION_VERIFIER_VERSION_MISMATCH"),
        (receipt.graph_id == artifacts.graph.graph_id and receipt.graph_hash == artifacts.graph.artifact_hash, "RUNTIME_AUTHORIZATION_GRAPH_MISMATCH"),
        (receipt.evidence_id == artifacts.evidence.evidence_id and receipt.evidence_hash == artifacts.evidence.artifact_hash, "RUNTIME_AUTHORIZATION_EVIDENCE_MISMATCH"),
        (receipt.parameter_hashes == expected_parameters, "RUNTIME_AUTHORIZATION_PARAMETER_MISMATCH"),
        (receipt.verifier_policy_hash == canonical_verifier_policy_sha256(policy), "RUNTIME_AUTHORIZATION_POLICY_MISMATCH"),
    )
    for passed, code in checks:
        if not passed:
            _fail(code, "runtime authorization binding differs")
    _reparse_inputs(rule, artifacts)
    try:
        verify_verifier_result_binding(rule, result, artifacts, policy=policy)
    except VerifierV1Error as exc:
        _fail(exc.issue_code, exc.message)
    return receipt.authorization_id


def _reparse_inputs(rule: DelayedResponseRuleV1, artifacts: DelayedResponseArtifactCollectionV1) -> None:
    try:
        parse_delayed_response_rule(delayed_response_rule_to_dict(rule))
        parse_candidate_graph(candidate_graph_to_dict(artifacts.graph))
        parse_evidence_package(evidence_package_to_dict(artifacts.evidence))
        for parameter in artifacts.parameters:
            parse_calibration_parameter(calibration_parameter_to_dict(parameter))
    except ValueError as exc:
        _fail("RUNTIME_BOUND_ARTIFACT_INVALID", "a bound artifact failed structural or hash validation")


def _typed_receipt(item: Mapping[str, Any]) -> RuntimeAuthorizationReceiptV1:
    hashes = item["parameter_hashes"]
    if not isinstance(hashes, Mapping):
        _fail("RUNTIME_AUTHORIZATION_RECEIPT_INVALID", "parameter hashes must be a mapping")
    if re.fullmatch(r"AUTH-[A-F0-9]{20}", str(item["authorization_id"])) is None:
        _fail("RUNTIME_AUTHORIZATION_RECEIPT_INVALID", "authorization ID is invalid")
    return RuntimeAuthorizationReceiptV1(
        authorization_id=str(item["authorization_id"]),
        authorization_version=str(item["authorization_version"]),
        authorization_hash=str(item["authorization_hash"]),
        accepted_rule_id=str(item["accepted_rule_id"]),
        accepted_rule_hash=str(item["accepted_rule_hash"]),
        verifier_result_id=str(item["verifier_result_id"]),
        verifier_result_hash=str(item["verifier_result_hash"]),
        verifier_version=str(item["verifier_version"]),
        graph_id=str(item["graph_id"]),
        graph_hash=str(item["graph_hash"]),
        evidence_id=str(item["evidence_id"]),
        evidence_hash=str(item["evidence_hash"]),
        parameter_hashes=tuple(sorted((str(key), str(value)) for key, value in hashes.items())),
        verifier_policy_hash=str(item["verifier_policy_hash"]),
        runtime_scope=str(item["runtime_scope"]),
        created_at=str(item["created_at"]),
    )


def _authorization_id_from_document(document: Mapping[str, Any]) -> str:
    payload = copy.deepcopy(dict(document))
    payload.pop("authorization_id", None)
    payload.pop("authorization_hash", None)
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")).hexdigest()
    return f"AUTH-{digest[:20].upper()}"


def _fail(code: str, message: str) -> None:
    raise RuntimeAuthorizationError(code, message)
