"""Fail-closed scientific-preparation contracts for Validation V2 EXP-02.

This module is deliberately a custody and authority layer around
``numeric_policy_v1``.  It reads no data, performs no scientific selection,
creates no runtime authority, and authorizes no development-label access.
Private numeric summaries remain outside public receipts: only their counts
and cryptographic identities cross this boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from hashlib import sha256
import json
import re
from typing import Any, Callable, Mapping, Sequence

from .formal_v4_authority_v1 import V4_NUMERIC_ROLES
from .numeric_policy_v1 import (
    EXP02_CONFIRMATION_SPLIT,
    EXP02_FIT_SPLITS,
    EXP02_SELECTION_SPLIT,
    ConfirmedCohortAuthorityV1,
    NormalPolicySelectionAuthorityV1,
    NumericPolicyCandidateV1,
    NumericPolicyError,
    NumericPolicySelectionResultV1,
    NumericPolicySelectionSummaryV1,
    candidate_set_hash_v1,
    validate_confirmed_cohort_authority_v1,
    validate_normal_policy_selection_authority_v1,
    validate_numeric_policy_selection_result_v1,
    validate_numeric_policy_selection_summary_v1,
    select_numeric_policy_on_train4_v1,
)
from .protocol_v1 import ValidationProtocolV1, validate_validation_protocol_v1


EXP02_SCIENTIFIC_CONTRACT_VERSION = "VALIDATION_V2_EXP02_SCIENTIFIC_V1"
EXP02_CANDIDATE_COUNT = 37
EXP02_SELECTION_NAMESPACE = "validation-v2/exp02/train4-selection-only/formal-v4-v1"
EXP02_PUBLIC_AUTHORITY_STATE = "SELECTED_FORMAL_V4_NUMERIC_AUTHORITY_NOT_RUNTIME_AUTHORIZED"

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_PUBLIC_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")


class Exp02ScientificError(ValueError):
    """A stable fail-closed issue from the EXP-02 preparation boundary."""

    def __init__(self, issue_code: str, message: str) -> None:
        super().__init__(f"{issue_code}: {message}")
        self.issue_code = issue_code
        self.message = message


def _fail(code: str, message: str) -> None:
    raise Exp02ScientificError(code, message)


def _canonical_bytes(document: Mapping[str, Any]) -> bytes:
    return json.dumps(
        dict(document), sort_keys=True, separators=(",", ":"),
        ensure_ascii=True, allow_nan=False,
    ).encode("utf-8")


def _hash(document: Mapping[str, Any]) -> str:
    return sha256(_canonical_bytes(document)).hexdigest()


def _expected_hash(document: Mapping[str, Any], field: str) -> str:
    return _hash({key: value for key, value in document.items() if key != field})


def _sha(value: object, name: str) -> str:
    if type(value) is not str or _SHA256.fullmatch(value) is None:
        _fail("EXP02_SCI_HASH_INVALID", f"{name} must be lowercase SHA-256")
    return value


def _commit(value: object) -> str:
    if type(value) is not str or _COMMIT.fullmatch(value) is None:
        _fail("EXP02_SCI_COMMIT_INVALID", "source_commit must be an exact Git commit")
    return value


def _positive_int(value: object, name: str) -> int:
    if type(value) is not int or value <= 0:
        _fail("EXP02_SCI_COUNT_INVALID", f"{name} must be an exact positive integer")
    return value


def _public_id(value: object, name: str) -> str:
    if type(value) is not str or _PUBLIC_ID.fullmatch(value) is None:
        _fail("EXP02_SCI_PUBLIC_ID_INVALID", f"{name} must be a path-free public identifier")
    return value


def _require_external(observed: str, expected: str, code: str, name: str) -> None:
    _sha(expected, f"expected_{name}")
    if observed != expected:
        _fail(code, f"{name} differs from the externally frozen identity")


class Exp02OperationV1(str, Enum):
    CONFIRM_COHORT = "CONFIRM_COHORT"
    DERIVE_PRIVATE_SUMMARIES = "DERIVE_PRIVATE_SUMMARIES"
    SELECT_ON_NORMAL_TRAIN4 = "SELECT_ON_NORMAL_TRAIN4"


def assert_exp02_split_allowed_v1(*, split_id: str, operation: Exp02OperationV1) -> None:
    """Enforce the frozen normal-only split roles before any adapter can run."""

    if type(operation) is not Exp02OperationV1 or type(split_id) is not str:
        _fail("EXP02_SCI_SPLIT_REQUEST_INVALID", "split and operation types must be exact")
    allowed = {
        Exp02OperationV1.CONFIRM_COHORT: (EXP02_CONFIRMATION_SPLIT,),
        Exp02OperationV1.DERIVE_PRIVATE_SUMMARIES: EXP02_FIT_SPLITS,
        Exp02OperationV1.SELECT_ON_NORMAL_TRAIN4: (EXP02_SELECTION_SPLIT,),
    }
    if split_id not in allowed[operation]:
        _fail("EXP02_SCI_SPLIT_PROHIBITED", f"{split_id} is not authorized for {operation.value}")


@dataclass(frozen=True)
class V2ConfirmedCohortBindingV1:
    cohort_hash: str
    confirmation_artifact_hash: str
    relation_count: int
    relation_ids_hash: str
    source_commit: str
    confirmation_split: str
    self_hash: str

    def body_dict(self) -> dict[str, Any]:
        return {
            "artifact_type": "validation_v2_exp02_confirmed_cohort_binding_v1",
            "cohort_hash": self.cohort_hash,
            "confirmation_artifact_hash": self.confirmation_artifact_hash,
            "confirmation_split": self.confirmation_split,
            "relation_count": self.relation_count,
            "relation_ids_hash": self.relation_ids_hash,
            "schema_version": "1.0.0",
            "source_commit": self.source_commit,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.body_dict(), "self_hash": self.self_hash}


def build_v2_confirmed_cohort_binding_v1(
    cohort: ConfirmedCohortAuthorityV1,
) -> V2ConfirmedCohortBindingV1:
    validate_confirmed_cohort_authority_v1(cohort)
    relation_ids_hash = _hash({"relation_ids": [item.relation_id for item in cohort.relations]})
    provisional = V2ConfirmedCohortBindingV1(
        cohort_hash=cohort.cohort_hash,
        confirmation_artifact_hash=cohort.confirmation_artifact_hash,
        relation_count=len(cohort.relations),
        relation_ids_hash=relation_ids_hash,
        source_commit=cohort.source_commit,
        confirmation_split=cohort.confirmation_split,
        self_hash="",
    )
    return replace(provisional, self_hash=_hash(provisional.body_dict()))


def validate_v2_confirmed_cohort_binding_v1(
    receipt: V2ConfirmedCohortBindingV1,
    *,
    cohort: ConfirmedCohortAuthorityV1,
    expected_receipt_hash: str,
) -> str:
    if type(receipt) is not V2ConfirmedCohortBindingV1:
        _fail("EXP02_SCI_COHORT_RECEIPT_TYPE", "cohort receipt type differs")
    expected = build_v2_confirmed_cohort_binding_v1(cohort)
    if receipt != expected:
        _fail("EXP02_SCI_COHORT_REPLAY_MISMATCH", "cohort binding differs from replay")
    _require_external(receipt.self_hash, expected_receipt_hash, "EXP02_SCI_COHORT_STALE", "cohort receipt")
    return receipt.self_hash


@dataclass(frozen=True)
class PrivateSummaryHashReceiptV1:
    split_id: str
    cohort_hash: str
    relation_count: int
    summary_count: int
    private_summary_bundle_hash: str
    source_commit: str
    contains_numeric_values: bool
    contains_private_paths: bool
    self_hash: str

    def body_dict(self) -> dict[str, Any]:
        return {
            "artifact_type": "validation_v2_exp02_private_summary_hash_receipt_v1",
            **{key: value for key, value in self.__dict__.items() if key != "self_hash"},
            "schema_version": "1.0.0",
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.body_dict(), "self_hash": self.self_hash}


def build_private_summary_hash_receipt_v1(
    *, split_id: str, cohort: V2ConfirmedCohortBindingV1,
    private_summary_bundle_hash: str,
) -> PrivateSummaryHashReceiptV1:
    assert_exp02_split_allowed_v1(
        split_id=split_id, operation=Exp02OperationV1.DERIVE_PRIVATE_SUMMARIES
    )
    _sha(private_summary_bundle_hash, "private_summary_bundle_hash")
    _positive_int(cohort.relation_count, "cohort.relation_count")
    provisional = PrivateSummaryHashReceiptV1(
        split_id=split_id, cohort_hash=cohort.cohort_hash,
        relation_count=cohort.relation_count, summary_count=cohort.relation_count,
        private_summary_bundle_hash=private_summary_bundle_hash,
        source_commit=cohort.source_commit, contains_numeric_values=False,
        contains_private_paths=False, self_hash="",
    )
    return replace(provisional, self_hash=_hash(provisional.body_dict()))


def validate_private_summary_hash_receipts_v1(
    receipts: Sequence[PrivateSummaryHashReceiptV1],
    *, cohort: V2ConfirmedCohortBindingV1,
    expected_receipt_hashes: Mapping[str, str],
) -> str:
    if type(receipts) not in (tuple, list) or len(receipts) != 2:
        _fail("EXP02_SCI_SUMMARY_SPLIT_COVERAGE", "exact train1/train2 receipts are required")
    by_split: dict[str, PrivateSummaryHashReceiptV1] = {}
    for receipt in receipts:
        if type(receipt) is not PrivateSummaryHashReceiptV1 or receipt.split_id in by_split:
            _fail("EXP02_SCI_SUMMARY_RECEIPT_INVALID", "summary receipt type or split duplicates")
        expected = build_private_summary_hash_receipt_v1(
            split_id=receipt.split_id, cohort=cohort,
            private_summary_bundle_hash=receipt.private_summary_bundle_hash,
        )
        if receipt != expected or receipt.contains_numeric_values or receipt.contains_private_paths:
            _fail("EXP02_SCI_SUMMARY_REPLAY_MISMATCH", "private-summary receipt differs from replay")
        frozen = expected_receipt_hashes.get(receipt.split_id)
        if frozen is None:
            _fail("EXP02_SCI_SUMMARY_EXPECTED_HASH_MISSING", "external split identity is absent")
        _require_external(receipt.self_hash, frozen, "EXP02_SCI_SUMMARY_STALE", receipt.split_id)
        by_split[receipt.split_id] = receipt
    if tuple(sorted(by_split)) != EXP02_FIT_SPLITS or set(expected_receipt_hashes) != set(EXP02_FIT_SPLITS):
        _fail("EXP02_SCI_SUMMARY_SPLIT_COVERAGE", "exact train1/train2 identities are required")
    return _hash({"summary_receipts": [by_split[name].self_hash for name in EXP02_FIT_SPLITS]})


@dataclass(frozen=True)
class CandidateSetFreezeReceiptV1:
    cohort_binding_hash: str
    fit_summary_receipts_hash: str
    candidate_set_hash: str
    candidate_ids_hash: str
    candidate_count: int
    formal_v4_roles_hash: str
    authority_namespace: str
    selection_only: bool
    runtime_authority: bool
    labels_allowed: bool
    self_hash: str

    def body_dict(self) -> dict[str, Any]:
        return {
            "artifact_type": "validation_v2_exp02_candidate_set_freeze_receipt_v1",
            **{key: value for key, value in self.__dict__.items() if key != "self_hash"},
            "schema_version": "1.0.0",
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.body_dict(), "self_hash": self.self_hash}


def build_candidate_set_freeze_receipt_v1(
    *, candidates: Sequence[NumericPolicyCandidateV1],
    cohort: V2ConfirmedCohortBindingV1, fit_summary_receipts_hash: str,
) -> CandidateSetFreezeReceiptV1:
    _sha(fit_summary_receipts_hash, "fit_summary_receipts_hash")
    observed_set_hash = candidate_set_hash_v1(candidates)
    if len(candidates) != EXP02_CANDIDATE_COUNT:
        _fail("EXP02_SCI_CANDIDATE_COUNT", "the frozen candidate set must contain exactly 37 candidates")
    if any(item.cohort_hash != cohort.cohort_hash for item in candidates):
        _fail("EXP02_SCI_CANDIDATE_COHORT_MISMATCH", "candidate set binds another cohort")
    ids = sorted(item.candidate_id for item in candidates)
    provisional = CandidateSetFreezeReceiptV1(
        cohort_binding_hash=cohort.self_hash,
        fit_summary_receipts_hash=fit_summary_receipts_hash,
        candidate_set_hash=observed_set_hash,
        candidate_ids_hash=_hash({"candidate_ids": ids}),
        candidate_count=EXP02_CANDIDATE_COUNT,
        formal_v4_roles_hash=_hash({"roles": list(V4_NUMERIC_ROLES)}),
        authority_namespace=EXP02_SELECTION_NAMESPACE,
        selection_only=True, runtime_authority=False, labels_allowed=False,
        self_hash="",
    )
    return replace(provisional, self_hash=_hash(provisional.body_dict()))


def validate_candidate_set_freeze_receipt_v1(
    receipt: CandidateSetFreezeReceiptV1, *, candidates: Sequence[NumericPolicyCandidateV1],
    cohort: V2ConfirmedCohortBindingV1, fit_summary_receipts_hash: str,
    expected_receipt_hash: str,
) -> str:
    if type(receipt) is not CandidateSetFreezeReceiptV1:
        _fail("EXP02_SCI_CANDIDATE_RECEIPT_TYPE", "candidate receipt type differs")
    expected = build_candidate_set_freeze_receipt_v1(
        candidates=candidates, cohort=cohort,
        fit_summary_receipts_hash=fit_summary_receipts_hash,
    )
    if receipt != expected or not receipt.selection_only or receipt.runtime_authority or receipt.labels_allowed:
        _fail("EXP02_SCI_CANDIDATE_REPLAY_MISMATCH", "candidate freeze differs from replay")
    _require_external(receipt.self_hash, expected_receipt_hash, "EXP02_SCI_CANDIDATE_STALE", "candidate receipt")
    return receipt.self_hash


class CandidateEvaluationStateV1(str, Enum):
    EVALUATED = "EVALUATED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class CandidateEvaluationReceiptV1:
    candidate_hash: str
    summary_hash: str
    state: CandidateEvaluationStateV1
    issue_codes: tuple[str, ...]
    self_hash: str

    def body_dict(self) -> dict[str, Any]:
        return {
            "candidate_hash": self.candidate_hash,
            "issue_codes": list(self.issue_codes),
            "state": self.state.value,
            "summary_hash": self.summary_hash,
        }


def build_candidate_evaluation_receipt_v1(
    *, candidate: NumericPolicyCandidateV1, summary: NumericPolicySelectionSummaryV1,
    selection_authority: NormalPolicySelectionAuthorityV1,
    protocol: ValidationProtocolV1, issue_codes: Sequence[str] = (),
) -> CandidateEvaluationReceiptV1:
    validate_numeric_policy_selection_summary_v1(
        summary, candidate=candidate, selection_authority=selection_authority,
        protocol=protocol,
    )
    if type(issue_codes) not in (tuple, list) or any(
        type(code) is not str or not code or code != code.upper() for code in issue_codes
    ):
        _fail("EXP02_SCI_EVALUATION_ISSUE_INVALID", "issue codes must be explicit uppercase strings")
    normalized = tuple(sorted(set(issue_codes)))
    derived_failures: list[str] = []
    if summary.system_error_count:
        derived_failures.append("SYSTEM_ERROR_NONZERO")
    if summary.unsupported_relation_count:
        derived_failures.append("UNSUPPORTED_RELATION_NONZERO")
    if derived_failures and not set(derived_failures).issubset(normalized):
        _fail("EXP02_SCI_EVALUATION_FAILURE_HIDDEN", "explicit summary failures require issue codes")
    state = CandidateEvaluationStateV1.FAILED if normalized else CandidateEvaluationStateV1.EVALUATED
    provisional = CandidateEvaluationReceiptV1(
        candidate_hash=candidate.candidate_hash, summary_hash=summary.summary_hash,
        state=state, issue_codes=normalized, self_hash="",
    )
    return replace(provisional, self_hash=_hash(provisional.body_dict()))


@dataclass(frozen=True)
class Train4EvaluationBundleV1:
    selection_authority_hash: str
    candidate_set_receipt_hash: str
    candidate_set_hash: str
    evaluation_receipts: tuple[CandidateEvaluationReceiptV1, ...]
    candidate_count: int
    evaluated_count: int
    failed_count: int
    contains_numeric_values: bool
    contains_private_paths: bool
    self_hash: str

    def body_dict(self) -> dict[str, Any]:
        return {
            "artifact_type": "validation_v2_exp02_train4_evaluation_bundle_v1",
            "candidate_count": self.candidate_count,
            "candidate_set_hash": self.candidate_set_hash,
            "candidate_set_receipt_hash": self.candidate_set_receipt_hash,
            "contains_numeric_values": self.contains_numeric_values,
            "contains_private_paths": self.contains_private_paths,
            "evaluated_count": self.evaluated_count,
            "evaluation_receipts": [item.body_dict() | {"self_hash": item.self_hash} for item in self.evaluation_receipts],
            "failed_count": self.failed_count,
            "schema_version": "1.0.0",
            "selection_authority_hash": self.selection_authority_hash,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.body_dict(), "self_hash": self.self_hash}


def build_train4_evaluation_bundle_v1(
    *, candidates: Sequence[NumericPolicyCandidateV1],
    candidate_set_receipt: CandidateSetFreezeReceiptV1,
    evaluations: Sequence[CandidateEvaluationReceiptV1],
    selection_authority: NormalPolicySelectionAuthorityV1,
    summaries: Sequence[NumericPolicySelectionSummaryV1],
    protocol: ValidationProtocolV1,
) -> Train4EvaluationBundleV1:
    validate_normal_policy_selection_authority_v1(selection_authority, protocol=protocol)
    if candidate_set_hash_v1(candidates) != candidate_set_receipt.candidate_set_hash:
        _fail("EXP02_SCI_EVALUATION_CANDIDATE_SET_MISMATCH", "evaluation candidate set differs")
    if selection_authority.candidate_set_hash != candidate_set_receipt.candidate_set_hash:
        _fail("EXP02_SCI_EVALUATION_AUTHORITY_MISMATCH", "train4 authority binds another candidate set")
    if type(evaluations) not in (tuple, list) or len(evaluations) != EXP02_CANDIDATE_COUNT:
        _fail("EXP02_SCI_EVALUATION_COVERAGE", "every one of the 37 candidates requires a receipt")
    expected_hashes = {item.candidate_hash for item in candidates}
    candidate_by_hash = {item.candidate_hash: item for item in candidates}
    if type(summaries) not in (tuple, list) or len(summaries) != EXP02_CANDIDATE_COUNT:
        _fail("EXP02_SCI_EVALUATION_SUMMARY_COVERAGE", "exactly one summary per candidate is required")
    summary_by_candidate = {item.candidate_hash: item for item in summaries}
    if len(summary_by_candidate) != EXP02_CANDIDATE_COUNT or set(summary_by_candidate) != expected_hashes:
        _fail("EXP02_SCI_EVALUATION_SUMMARY_COVERAGE", "summary coverage is partial, foreign, or duplicated")
    observed_hashes = [item.candidate_hash for item in evaluations]
    if len(set(observed_hashes)) != len(observed_hashes) or set(observed_hashes) != expected_hashes:
        _fail("EXP02_SCI_EVALUATION_COVERAGE", "candidate evaluation coverage is partial or duplicated")
    for row in evaluations:
        if row.self_hash != _hash(row.body_dict()):
            _fail("EXP02_SCI_EVALUATION_ROW_MUTATED", "candidate evaluation receipt hash differs")
        if (row.state is CandidateEvaluationStateV1.FAILED) != bool(row.issue_codes):
            _fail("EXP02_SCI_EVALUATION_FAILURE_AMBIGUOUS", "failure state and explicit issues differ")
        expected_row = build_candidate_evaluation_receipt_v1(
            candidate=candidate_by_hash[row.candidate_hash],
            summary=summary_by_candidate[row.candidate_hash],
            selection_authority=selection_authority, protocol=protocol,
            issue_codes=row.issue_codes,
        )
        if row != expected_row:
            _fail("EXP02_SCI_EVALUATION_ROW_REPLAY_MISMATCH", "candidate evaluation row differs from summary replay")
    ordered = tuple(sorted(evaluations, key=lambda item: item.candidate_hash))
    provisional = Train4EvaluationBundleV1(
        selection_authority_hash=selection_authority.authority_hash,
        candidate_set_receipt_hash=candidate_set_receipt.self_hash,
        candidate_set_hash=candidate_set_receipt.candidate_set_hash,
        evaluation_receipts=ordered, candidate_count=EXP02_CANDIDATE_COUNT,
        evaluated_count=sum(item.state is CandidateEvaluationStateV1.EVALUATED for item in ordered),
        failed_count=sum(item.state is CandidateEvaluationStateV1.FAILED for item in ordered),
        contains_numeric_values=False, contains_private_paths=False, self_hash="",
    )
    return replace(provisional, self_hash=_hash(provisional.body_dict()))


def validate_train4_evaluation_bundle_v1(
    bundle: Train4EvaluationBundleV1, *, candidates: Sequence[NumericPolicyCandidateV1],
    candidate_set_receipt: CandidateSetFreezeReceiptV1,
    selection_authority: NormalPolicySelectionAuthorityV1,
    summaries: Sequence[NumericPolicySelectionSummaryV1],
    protocol: ValidationProtocolV1,
    expected_bundle_hash: str,
) -> str:
    if type(bundle) is not Train4EvaluationBundleV1:
        _fail("EXP02_SCI_EVALUATION_BUNDLE_TYPE", "train4 bundle type differs")
    expected = build_train4_evaluation_bundle_v1(
        candidates=candidates, candidate_set_receipt=candidate_set_receipt,
        evaluations=bundle.evaluation_receipts, selection_authority=selection_authority,
        summaries=summaries, protocol=protocol,
    )
    if bundle != expected or bundle.contains_numeric_values or bundle.contains_private_paths:
        _fail("EXP02_SCI_EVALUATION_REPLAY_MISMATCH", "train4 bundle differs from replay")
    _require_external(bundle.self_hash, expected_bundle_hash, "EXP02_SCI_EVALUATION_STALE", "train4 bundle")
    return bundle.self_hash


@dataclass(frozen=True)
class SelectionDecisionReceiptV1:
    selection_result_hash: str
    selected_candidate_hash: str
    selected_candidate_id: str
    evaluation_bundle_hash: str
    candidate_set_receipt_hash: str
    cohort_binding_hash: str
    selection_authority_hash: str
    authority_namespace: str
    runtime_authority: bool
    labels_allowed: bool
    self_hash: str

    def body_dict(self) -> dict[str, Any]:
        return {
            "artifact_type": "validation_v2_exp02_selection_decision_receipt_v1",
            **{key: value for key, value in self.__dict__.items() if key != "self_hash"},
            "schema_version": "1.0.0",
        }


def build_selection_decision_receipt_v1(
    *, result: NumericPolicySelectionResultV1,
    candidates: Sequence[NumericPolicyCandidateV1],
    selection_authority: NormalPolicySelectionAuthorityV1,
    protocol: ValidationProtocolV1,
    evaluation_bundle: Train4EvaluationBundleV1,
    candidate_set_receipt: CandidateSetFreezeReceiptV1,
    cohort: V2ConfirmedCohortBindingV1,
    summaries: Sequence[NumericPolicySelectionSummaryV1],
) -> SelectionDecisionReceiptV1:
    validate_numeric_policy_selection_result_v1(
        result, candidates=candidates, selection_authority=selection_authority,
        protocol=protocol,
    )
    if candidate_set_receipt.self_hash != _hash(candidate_set_receipt.body_dict()):
        _fail("EXP02_SCI_CANDIDATE_RECEIPT_MUTATED", "candidate-set receipt hash differs")
    if candidate_set_receipt.cohort_binding_hash != cohort.self_hash:
        _fail("EXP02_SCI_DECISION_COHORT_MISMATCH", "candidate set binds another confirmed cohort")
    if evaluation_bundle.self_hash != _hash(evaluation_bundle.body_dict()):
        _fail("EXP02_SCI_EVALUATION_BUNDLE_MUTATED", "train4 bundle hash differs")
    if evaluation_bundle.candidate_set_receipt_hash != candidate_set_receipt.self_hash:
        _fail("EXP02_SCI_DECISION_EVALUATION_MISMATCH", "decision evaluation bundle is foreign")
    try:
        expected_result = select_numeric_policy_on_train4_v1(
            candidates=candidates, summaries=summaries,
            selection_authority=selection_authority, protocol=protocol,
        )
    except NumericPolicyError as exc:
        _fail("EXP02_SCI_SELECTION_REPLAY_FAILED", str(exc))
    if result != expected_result:
        _fail("EXP02_SCI_SELECTION_RESULT_REPLAY_MISMATCH", "selected candidate differs from deterministic replay")
    by_candidate = {item.candidate_hash: item for item in evaluation_bundle.evaluation_receipts}
    successful = frozenset(
        item.candidate_hash
        for item in evaluation_bundle.evaluation_receipts
        if item.state is CandidateEvaluationStateV1.EVALUATED
    )
    failed = frozenset(
        item.candidate_hash
        for item in evaluation_bundle.evaluation_receipts
        if item.state is CandidateEvaluationStateV1.FAILED
    )
    if (
        frozenset(result.eligible_candidate_hashes) != successful
        or frozenset(candidate_hash for candidate_hash, _ in result.rejected) != failed
    ):
        _fail(
            "EXP02_SCI_SELECTION_EVALUATION_PARTITION_MISMATCH",
            "selection eligibility must exactly replay successful and failed train4 evaluations",
        )
    selected_evaluation = by_candidate.get(result.selected_candidate_hash)
    if selected_evaluation is None or selected_evaluation.state is not CandidateEvaluationStateV1.EVALUATED:
        _fail("EXP02_SCI_SELECTED_CANDIDATE_FAILED", "selected candidate lacks a successful evaluation")
    provisional = SelectionDecisionReceiptV1(
        selection_result_hash=result.result_hash,
        selected_candidate_hash=result.selected_candidate_hash,
        selected_candidate_id=result.selected_candidate_id,
        evaluation_bundle_hash=evaluation_bundle.self_hash,
        candidate_set_receipt_hash=candidate_set_receipt.self_hash,
        cohort_binding_hash=candidate_set_receipt.cohort_binding_hash,
        selection_authority_hash=selection_authority.authority_hash,
        authority_namespace=EXP02_SELECTION_NAMESPACE,
        runtime_authority=False, labels_allowed=False, self_hash="",
    )
    return replace(provisional, self_hash=_hash(provisional.body_dict()))


def validate_selection_decision_receipt_v1(
    receipt: SelectionDecisionReceiptV1, *, result: NumericPolicySelectionResultV1,
    candidates: Sequence[NumericPolicyCandidateV1],
    selection_authority: NormalPolicySelectionAuthorityV1,
    protocol: ValidationProtocolV1, evaluation_bundle: Train4EvaluationBundleV1,
    candidate_set_receipt: CandidateSetFreezeReceiptV1,
    cohort: V2ConfirmedCohortBindingV1,
    summaries: Sequence[NumericPolicySelectionSummaryV1],
    expected_receipt_hash: str,
) -> str:
    if type(receipt) is not SelectionDecisionReceiptV1:
        _fail("EXP02_SCI_DECISION_TYPE", "selection decision receipt type differs")
    expected = build_selection_decision_receipt_v1(
        result=result, candidates=candidates, selection_authority=selection_authority,
        protocol=protocol, evaluation_bundle=evaluation_bundle,
        candidate_set_receipt=candidate_set_receipt, cohort=cohort,
        summaries=summaries,
    )
    if receipt != expected or receipt.runtime_authority or receipt.labels_allowed:
        _fail("EXP02_SCI_DECISION_REPLAY_MISMATCH", "selection decision differs from replay")
    _require_external(receipt.self_hash, expected_receipt_hash, "EXP02_SCI_DECISION_STALE", "selection decision")
    return receipt.self_hash


@dataclass(frozen=True)
class FormalV4NumericAuthorityPublicReceiptV1:
    authority_artifact_id: str
    authority_artifact_hash: str
    decision_receipt_hash: str
    selected_candidate_hash: str
    cohort_hash: str
    relation_count: int
    numeric_role_count: int
    binding_count: int
    numeric_roles_hash: str
    authority_namespace: str
    state: str
    contains_numeric_values: bool
    contains_private_paths: bool
    runtime_authorized: bool
    self_hash: str

    def body_dict(self) -> dict[str, Any]:
        return {
            "artifact_type": "validation_v2_exp02_formal_v4_numeric_authority_public_receipt_v1",
            **{key: value for key, value in self.__dict__.items() if key != "self_hash"},
            "schema_version": "1.0.0",
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.body_dict(), "self_hash": self.self_hash}


def build_formal_v4_numeric_authority_public_receipt_v1(
    *, authority_artifact_id: str, authority_artifact_hash: str,
    decision: SelectionDecisionReceiptV1, cohort: V2ConfirmedCohortBindingV1,
) -> FormalV4NumericAuthorityPublicReceiptV1:
    _public_id(authority_artifact_id, "authority_artifact_id")
    _sha(authority_artifact_hash, "authority_artifact_hash")
    _positive_int(cohort.relation_count, "cohort.relation_count")
    if decision.self_hash != _hash(decision.body_dict()):
        _fail("EXP02_SCI_DECISION_MUTATED", "selection decision hash differs")
    if decision.runtime_authority or decision.labels_allowed:
        _fail("EXP02_SCI_AUTHORITY_ESCALATION", "selection decision cannot authorize runtime or labels")
    if decision.cohort_binding_hash != cohort.self_hash:
        _fail("EXP02_SCI_AUTHORITY_COHORT_MISMATCH", "selection decision binds another confirmed cohort")
    role_count = len(V4_NUMERIC_ROLES)
    provisional = FormalV4NumericAuthorityPublicReceiptV1(
        authority_artifact_id=authority_artifact_id,
        authority_artifact_hash=authority_artifact_hash,
        decision_receipt_hash=decision.self_hash,
        selected_candidate_hash=decision.selected_candidate_hash,
        cohort_hash=cohort.cohort_hash, relation_count=cohort.relation_count,
        numeric_role_count=role_count, binding_count=cohort.relation_count * role_count,
        numeric_roles_hash=_hash({"roles": list(V4_NUMERIC_ROLES)}),
        authority_namespace=EXP02_SELECTION_NAMESPACE,
        state=EXP02_PUBLIC_AUTHORITY_STATE,
        contains_numeric_values=False, contains_private_paths=False,
        runtime_authorized=False, self_hash="",
    )
    return replace(provisional, self_hash=_hash(provisional.body_dict()))


def validate_formal_v4_numeric_authority_public_receipt_v1(
    receipt: FormalV4NumericAuthorityPublicReceiptV1, *,
    decision: SelectionDecisionReceiptV1, cohort: V2ConfirmedCohortBindingV1,
    expected_receipt_hash: str,
) -> str:
    if type(receipt) is not FormalV4NumericAuthorityPublicReceiptV1:
        _fail("EXP02_SCI_PUBLIC_AUTHORITY_TYPE", "public authority receipt type differs")
    expected = build_formal_v4_numeric_authority_public_receipt_v1(
        authority_artifact_id=receipt.authority_artifact_id,
        authority_artifact_hash=receipt.authority_artifact_hash,
        decision=decision, cohort=cohort,
    )
    if receipt != expected or receipt.contains_numeric_values or receipt.contains_private_paths or receipt.runtime_authorized:
        _fail("EXP02_SCI_PUBLIC_AUTHORITY_REPLAY_MISMATCH", "public authority receipt differs")
    _require_external(receipt.self_hash, expected_receipt_hash, "EXP02_SCI_PUBLIC_AUTHORITY_STALE", "public authority receipt")
    return receipt.self_hash


@dataclass(frozen=True)
class AtomicFreezeEvidenceV1:
    artifact_id: str
    byte_count: int
    payload_bytes_sha256: str
    reopened_bytes_sha256: str
    atomic_replace_completed: bool
    fsync_completed: bool
    close_completed: bool
    reopen_completed: bool
    evidence_hash: str

    def body_dict(self) -> dict[str, Any]:
        return {key: value for key, value in self.__dict__.items() if key != "evidence_hash"}


def build_atomic_freeze_evidence_v1(
    *, artifact_id: str, payload: bytes,
    reopened_bytes_sha256: str,
    atomic_replace_completed: bool, fsync_completed: bool,
    close_completed: bool, reopen_completed: bool,
) -> AtomicFreezeEvidenceV1:
    _public_id(artifact_id, "artifact_id")
    if type(payload) is not bytes or not payload:
        _fail("EXP02_SCI_FREEZE_PAYLOAD_INVALID", "freeze payload must be non-empty exact bytes")
    _sha(reopened_bytes_sha256, "reopened_bytes_sha256")
    flags = (atomic_replace_completed, fsync_completed, close_completed, reopen_completed)
    if any(type(flag) is not bool for flag in flags) or not all(flags):
        _fail("EXP02_SCI_FREEZE_SEQUENCE_INCOMPLETE", "atomic write, fsync, close, and reopen must all complete")
    payload_hash = sha256(payload).hexdigest()
    if reopened_bytes_sha256 != payload_hash:
        _fail("EXP02_SCI_FREEZE_REOPEN_MISMATCH", "reopened bytes differ from written payload")
    provisional = AtomicFreezeEvidenceV1(
        artifact_id=artifact_id, byte_count=len(payload),
        payload_bytes_sha256=payload_hash,
        reopened_bytes_sha256=reopened_bytes_sha256,
        atomic_replace_completed=True, fsync_completed=True,
        close_completed=True, reopen_completed=True, evidence_hash="",
    )
    return replace(provisional, evidence_hash=_hash(provisional.body_dict()))


@dataclass(frozen=True)
class SelectedPolicyFreezeReceiptV1:
    artifact_id: str
    decision_receipt_hash: str
    numeric_authority_receipt_hash: str
    payload_bytes_sha256: str
    byte_count: int
    atomic_evidence_hash: str
    frozen: bool
    runtime_authorized: bool
    label_access_authorized: bool
    self_hash: str

    def body_dict(self) -> dict[str, Any]:
        return {
            "artifact_type": "validation_v2_exp02_selected_policy_freeze_receipt_v1",
            **{key: value for key, value in self.__dict__.items() if key != "self_hash"},
            "schema_version": "1.0.0",
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.body_dict(), "self_hash": self.self_hash}


AtomicPersistCallbackV1 = Callable[[bytes], AtomicFreezeEvidenceV1]


def freeze_selected_policy_v1(
    *, artifact_id: str, decision: SelectionDecisionReceiptV1,
    numeric_authority: FormalV4NumericAuthorityPublicReceiptV1,
    persist_and_reopen: AtomicPersistCallbackV1,
) -> SelectedPolicyFreezeReceiptV1:
    """Cross an injected atomic I/O boundary and bind its reopened-byte proof."""

    _public_id(artifact_id, "artifact_id")
    if decision.self_hash != _hash(decision.body_dict()):
        _fail("EXP02_SCI_DECISION_MUTATED", "selection decision hash differs")
    if numeric_authority.self_hash != _hash(numeric_authority.body_dict()):
        _fail("EXP02_SCI_PUBLIC_AUTHORITY_MUTATED", "numeric authority receipt hash differs")
    if numeric_authority.decision_receipt_hash != decision.self_hash:
        _fail("EXP02_SCI_FREEZE_AUTHORITY_MISMATCH", "numeric authority binds another decision")
    payload = _canonical_bytes({
        "artifact_type": "validation_v2_exp02_selected_policy_payload_v1",
        "authority_namespace": EXP02_SELECTION_NAMESPACE,
        "decision_receipt_hash": decision.self_hash,
        "numeric_authority_receipt_hash": numeric_authority.self_hash,
        "schema_version": "1.0.0",
    })
    if not callable(persist_and_reopen):
        _fail("EXP02_SCI_FREEZE_CALLBACK_INVALID", "atomic persistence callback is required")
    evidence = persist_and_reopen(payload)
    if type(evidence) is not AtomicFreezeEvidenceV1:
        _fail("EXP02_SCI_FREEZE_EVIDENCE_TYPE", "persistence callback returned another type")
    if evidence.evidence_hash != _hash(evidence.body_dict()):
        _fail("EXP02_SCI_FREEZE_EVIDENCE_MUTATED", "atomic evidence hash differs")
    payload_hash = sha256(payload).hexdigest()
    if (
        evidence.artifact_id != artifact_id
        or evidence.payload_bytes_sha256 != payload_hash
        or evidence.reopened_bytes_sha256 != payload_hash
        or evidence.byte_count != len(payload)
        or evidence.atomic_replace_completed is not True
        or evidence.fsync_completed is not True
        or evidence.close_completed is not True
        or evidence.reopen_completed is not True
    ):
        _fail("EXP02_SCI_FREEZE_EVIDENCE_FOREIGN", "atomic evidence binds another artifact or payload")
    provisional = SelectedPolicyFreezeReceiptV1(
        artifact_id=artifact_id, decision_receipt_hash=decision.self_hash,
        numeric_authority_receipt_hash=numeric_authority.self_hash,
        payload_bytes_sha256=evidence.payload_bytes_sha256,
        byte_count=evidence.byte_count, atomic_evidence_hash=evidence.evidence_hash,
        frozen=True, runtime_authorized=False, label_access_authorized=False,
        self_hash="",
    )
    return replace(provisional, self_hash=_hash(provisional.body_dict()))


def validate_selected_policy_freeze_receipt_v1(
    receipt: SelectedPolicyFreezeReceiptV1, *, decision: SelectionDecisionReceiptV1,
    numeric_authority: FormalV4NumericAuthorityPublicReceiptV1,
    expected_receipt_hash: str,
) -> str:
    if type(receipt) is not SelectedPolicyFreezeReceiptV1:
        _fail("EXP02_SCI_FREEZE_RECEIPT_TYPE", "selected-policy freeze receipt type differs")
    if receipt.self_hash != _hash(receipt.body_dict()):
        _fail("EXP02_SCI_FREEZE_RECEIPT_MUTATED", "selected-policy freeze receipt hash differs")
    if (
        receipt.decision_receipt_hash != decision.self_hash
        or receipt.numeric_authority_receipt_hash != numeric_authority.self_hash
        or not receipt.frozen or receipt.runtime_authorized or receipt.label_access_authorized
    ):
        _fail("EXP02_SCI_FREEZE_RECEIPT_BINDING", "freeze receipt binding or authority state differs")
    _require_external(receipt.self_hash, expected_receipt_hash, "EXP02_SCI_FREEZE_RECEIPT_STALE", "freeze receipt")
    return receipt.self_hash


class Exp02ScientificStageV1(str, Enum):
    READY = "READY"
    COHORT_BOUND = "COHORT_BOUND"
    FIT_SUMMARIES_BOUND = "FIT_SUMMARIES_BOUND"
    CANDIDATES_FROZEN = "CANDIDATES_FROZEN"
    TRAIN4_EVALUATED = "TRAIN4_EVALUATED"
    POLICY_SELECTED = "POLICY_SELECTED"
    V4_AUTHORITY_MATERIALIZED = "V4_AUTHORITY_MATERIALIZED"
    POLICY_DURABLY_FROZEN = "POLICY_DURABLY_FROZEN"


_STAGES = tuple(Exp02ScientificStageV1)


@dataclass(frozen=True)
class Exp02ScientificStateReceiptV1:
    stage: Exp02ScientificStageV1
    source_commit: str
    protocol_hash: str
    bound_artifact_hashes: tuple[str, ...]
    previous_state_hash: str | None
    self_hash: str

    def body_dict(self) -> dict[str, Any]:
        return {
            "artifact_type": "validation_v2_exp02_scientific_state_receipt_v1",
            "bound_artifact_hashes": list(self.bound_artifact_hashes),
            "previous_state_hash": self.previous_state_hash,
            "protocol_hash": self.protocol_hash,
            "schema_version": "1.0.0",
            "source_commit": self.source_commit,
            "stage": self.stage.value,
        }


def start_exp02_scientific_state_v1(protocol: ValidationProtocolV1) -> Exp02ScientificStateReceiptV1:
    validate_validation_protocol_v1(protocol)
    provisional = Exp02ScientificStateReceiptV1(
        stage=Exp02ScientificStageV1.READY, source_commit=protocol.source_commit,
        protocol_hash=protocol.protocol_hash, bound_artifact_hashes=(),
        previous_state_hash=None, self_hash="",
    )
    return replace(provisional, self_hash=_hash(provisional.body_dict()))


def advance_exp02_scientific_state_v1(
    current: Exp02ScientificStateReceiptV1, *,
    next_stage: Exp02ScientificStageV1, artifact_hash: str,
    protocol: ValidationProtocolV1,
) -> Exp02ScientificStateReceiptV1:
    validate_validation_protocol_v1(protocol)
    if type(current) is not Exp02ScientificStateReceiptV1 or current.self_hash != _hash(current.body_dict()):
        _fail("EXP02_SCI_STATE_MUTATED", "current state receipt differs from its hash")
    if current.protocol_hash != protocol.protocol_hash or current.source_commit != protocol.source_commit:
        _fail("EXP02_SCI_STATE_AUTHORITY_MISMATCH", "state receipt binds another protocol or source commit")
    _sha(artifact_hash, "artifact_hash")
    if type(next_stage) is not Exp02ScientificStageV1:
        _fail("EXP02_SCI_STATE_TYPE", "next stage type differs")
    current_index = _STAGES.index(current.stage)
    if current_index + 1 >= len(_STAGES) or _STAGES[current_index + 1] is not next_stage:
        _fail("EXP02_SCI_STATE_ORDER", "scientific preparation stages must advance exactly once in order")
    provisional = Exp02ScientificStateReceiptV1(
        stage=next_stage, source_commit=current.source_commit,
        protocol_hash=current.protocol_hash,
        bound_artifact_hashes=current.bound_artifact_hashes + (artifact_hash,),
        previous_state_hash=current.self_hash, self_hash="",
    )
    return replace(provisional, self_hash=_hash(provisional.body_dict()))


__all__ = [
    "EXP02_CANDIDATE_COUNT", "EXP02_PUBLIC_AUTHORITY_STATE",
    "EXP02_SCIENTIFIC_CONTRACT_VERSION", "EXP02_SELECTION_NAMESPACE",
    "AtomicFreezeEvidenceV1", "CandidateEvaluationReceiptV1",
    "CandidateEvaluationStateV1", "CandidateSetFreezeReceiptV1",
    "Exp02OperationV1", "Exp02ScientificError", "Exp02ScientificStageV1",
    "Exp02ScientificStateReceiptV1", "FormalV4NumericAuthorityPublicReceiptV1",
    "PrivateSummaryHashReceiptV1", "SelectedPolicyFreezeReceiptV1",
    "SelectionDecisionReceiptV1", "Train4EvaluationBundleV1",
    "V2ConfirmedCohortBindingV1", "advance_exp02_scientific_state_v1",
    "assert_exp02_split_allowed_v1", "build_atomic_freeze_evidence_v1",
    "build_candidate_evaluation_receipt_v1", "build_candidate_set_freeze_receipt_v1",
    "build_formal_v4_numeric_authority_public_receipt_v1",
    "build_private_summary_hash_receipt_v1", "build_selection_decision_receipt_v1",
    "build_train4_evaluation_bundle_v1", "build_v2_confirmed_cohort_binding_v1",
    "freeze_selected_policy_v1", "start_exp02_scientific_state_v1",
    "validate_candidate_set_freeze_receipt_v1",
    "validate_formal_v4_numeric_authority_public_receipt_v1",
    "validate_private_summary_hash_receipts_v1", "validate_selected_policy_freeze_receipt_v1",
    "validate_selection_decision_receipt_v1",
    "validate_train4_evaluation_bundle_v1", "validate_v2_confirmed_cohort_binding_v1",
]
