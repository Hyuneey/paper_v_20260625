"""Single-path Formal V4 runtime-to-explanation runner for EXP-05.

The runner accepts an observation window, never a precomputed trace.  One
authorized call executes the frozen runtime once, materializes that exact
trace, renders it deterministically, and validates all fidelity checks.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from .explanation_fidelity_v1 import (
    EXP05_FIDELITY_VALIDATOR_VERSION,
    EXP05_RENDERER_CONTRACT_HASH,
    FormalV4ExplanationFidelityResultV1,
    FormalV4ExplanationRecordV1,
    MaterializedFormalV4TraceV1,
    hash_formal_v4_observation_window_v1,
    materialize_formal_v4_trace_v1,
    render_formal_v4_explanation_v1,
    validate_formal_v4_explanation_fidelity_v1,
)
from .formal_v4_authority_v1 import (
    FormalV4AuthorizedRuntimeV1,
    FormalV4ExecutionContextV1,
    canonical_document_hash_v1,
)
from .runtime_policy_v1 import FORMAL_V4_TRACE_CONTRACT_HASH
from .runtime_v1 import (
    FORMAL_V4_RUNTIME_VERSION,
    FormalV4ObservationWindowV1,
    execute_formal_v4_rule_v1,
)


EXP05_ONE_PATH_RUNNER_VERSION = "VALIDATION_V2_EXP05_ONE_PATH_RUNNER_V1"
_RUNNER_CONTRACT = {
    "accepts_precomputed_trace": False,
    "execution_count_per_unit": 1,
    "heldout_authorized": False,
    "labels_accessed": False,
    "llm_calls": 0,
    "network_calls": 0,
    "pipeline": ["runtime", "materialize", "render", "fidelity_validate"],
    "runner_version": EXP05_ONE_PATH_RUNNER_VERSION,
}
EXP05_ONE_PATH_RUNNER_CONTRACT_HASH = canonical_document_hash_v1(_RUNNER_CONTRACT)
_ZERO = "0" * 64
_SCOPES = ("SYNTHETIC_CONFORMANCE", "SCIENTIFIC_V2")


class Exp05RunnerError(ValueError):
    pass


def _fail(code: str) -> None:
    raise Exp05RunnerError(code)


def _hash(value: object, code: str) -> str:
    if type(value) is not str or len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        _fail(code)
    return value


def _commit(value: object) -> str:
    if type(value) is not str or len(value) != 40 or any(ch not in "0123456789abcdef" for ch in value):
        _fail("EXP05_SOURCE_COMMIT_INVALID")
    return value


@dataclass(frozen=True)
class Exp05RunAuthorizationV1:
    execution_scope: str
    preregistration_hash: str
    source_commit: str
    portfolio_authority_hash: str
    runtime_authorization_hash: str
    execution_context_hash: str
    stage2_commit_a_receipt_hash: str | None
    normal_selection_commit_b_receipt_hash: str | None
    test1_features_authorized: bool
    labels_authorized: bool = False
    heldout_authorized: bool = False
    provider_calls_authorized: bool = False
    authorization_hash: str = ""

    def payload(self) -> dict[str, Any]:
        return {
            "execution_context_hash": self.execution_context_hash,
            "execution_scope": self.execution_scope,
            "heldout_authorized": self.heldout_authorized,
            "labels_authorized": self.labels_authorized,
            "normal_selection_commit_b_receipt_hash": self.normal_selection_commit_b_receipt_hash,
            "portfolio_authority_hash": self.portfolio_authority_hash,
            "preregistration_hash": self.preregistration_hash,
            "provider_calls_authorized": self.provider_calls_authorized,
            "runner_contract_hash": EXP05_ONE_PATH_RUNNER_CONTRACT_HASH,
            "schema": "paperworks.validation_v2.exp05_run_authorization_v1",
            "schema_version": "1.0.0",
            "source_commit": self.source_commit,
            "stage2_commit_a_receipt_hash": self.stage2_commit_a_receipt_hash,
            "test1_features_authorized": self.test1_features_authorized,
            "runtime_authorization_hash": self.runtime_authorization_hash,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.payload(), "authorization_hash": self.authorization_hash}


def authorize_exp05_execution_v1(
    *,
    execution_scope: str,
    preregistration_hash: str,
    source_commit: str,
    bundle: FormalV4AuthorizedRuntimeV1,
    stage2_commit_a_receipt_hash: str | None = None,
    normal_selection_commit_b_receipt_hash: str | None = None,
    test1_features_authorized: bool = False,
) -> Exp05RunAuthorizationV1:
    if execution_scope not in _SCOPES or type(bundle) is not FormalV4AuthorizedRuntimeV1:
        _fail("EXP05_RUN_AUTHORIZATION_INPUT_INVALID")
    _hash(preregistration_hash, "EXP05_PREREGISTRATION_HASH_INVALID")
    _commit(source_commit)
    if source_commit != bundle.authority.source_commit:
        _fail("EXP05_SOURCE_COMMIT_MISMATCH")
    if execution_scope == "SYNTHETIC_CONFORMANCE":
        if stage2_commit_a_receipt_hash is not None or normal_selection_commit_b_receipt_hash is not None or test1_features_authorized:
            _fail("EXP05_SYNTHETIC_SCOPE_ESCALATION_REJECTED")
    else:
        _hash(stage2_commit_a_receipt_hash, "EXP05_COMMIT_A_RECEIPT_REQUIRED")
        _hash(normal_selection_commit_b_receipt_hash, "EXP05_COMMIT_B_RECEIPT_REQUIRED")
        if test1_features_authorized is not True:
            _fail("EXP05_TEST1_FEATURE_AUTHORIZATION_REQUIRED")
    provisional = Exp05RunAuthorizationV1(
        execution_scope=execution_scope,
        preregistration_hash=preregistration_hash,
        source_commit=source_commit,
        portfolio_authority_hash=bundle.authority.authority_hash,
        runtime_authorization_hash=bundle.receipt.authorization_hash,
        execution_context_hash=bundle.execution_context.context_hash,
        stage2_commit_a_receipt_hash=stage2_commit_a_receipt_hash,
        normal_selection_commit_b_receipt_hash=normal_selection_commit_b_receipt_hash,
        test1_features_authorized=test1_features_authorized,
    )
    return replace(provisional, authorization_hash=canonical_document_hash_v1(provisional.payload()))


def validate_exp05_run_authorization_v1(
    authorization: Exp05RunAuthorizationV1,
    *,
    bundle: FormalV4AuthorizedRuntimeV1,
    execution_context: FormalV4ExecutionContextV1,
) -> str:
    if type(authorization) is not Exp05RunAuthorizationV1 or type(bundle) is not FormalV4AuthorizedRuntimeV1:
        _fail("EXP05_RUN_AUTHORIZATION_TYPE_INVALID")
    expected = authorize_exp05_execution_v1(
        execution_scope=authorization.execution_scope,
        preregistration_hash=authorization.preregistration_hash,
        source_commit=authorization.source_commit,
        bundle=bundle,
        stage2_commit_a_receipt_hash=authorization.stage2_commit_a_receipt_hash,
        normal_selection_commit_b_receipt_hash=authorization.normal_selection_commit_b_receipt_hash,
        test1_features_authorized=authorization.test1_features_authorized,
    )
    if expected != authorization or authorization.execution_context_hash != execution_context.context_hash:
        _fail("EXP05_RUN_AUTHORIZATION_REPLAY_MISMATCH")
    return authorization.authorization_hash


@dataclass(frozen=True)
class FormalV4RuntimeMaterializationReceiptV1:
    preregistration_hash: str
    exp05_run_authorization_hash: str
    execution_scope: str
    stage2_commit_a_receipt_hash: str | None
    normal_selection_commit_b_receipt_hash: str | None
    test1_features_authorized: bool
    source_commit: str
    runner_contract_hash: str
    runtime_version: str
    trace_contract_hash: str
    runtime_trace_hash: str
    observation_window_hash: str
    materialized_trace_hash: str
    descriptor_hash: str
    descriptor_set_hash: str
    portfolio_authority_hash: str
    authorization_hash: str
    execution_context_hash: str
    renderer_contract_hash: str
    validator_version: str
    same_call_path: bool
    labels_accessed: bool
    heldout_accessed: bool
    provider_calls: int
    llm_calls: int
    receipt_hash: str

    def payload(self) -> dict[str, Any]:
        return {
            "authorization_hash": self.authorization_hash,
            "descriptor_hash": self.descriptor_hash,
            "descriptor_set_hash": self.descriptor_set_hash,
            "execution_context_hash": self.execution_context_hash,
            "execution_scope": self.execution_scope,
            "exp05_run_authorization_hash": self.exp05_run_authorization_hash,
            "heldout_accessed": self.heldout_accessed,
            "labels_accessed": self.labels_accessed,
            "llm_calls": self.llm_calls,
            "materialized_trace_hash": self.materialized_trace_hash,
            "normal_selection_commit_b_receipt_hash": self.normal_selection_commit_b_receipt_hash,
            "observation_window_hash": self.observation_window_hash,
            "portfolio_authority_hash": self.portfolio_authority_hash,
            "preregistration_hash": self.preregistration_hash,
            "provider_calls": self.provider_calls,
            "renderer_contract_hash": self.renderer_contract_hash,
            "runner_contract_hash": self.runner_contract_hash,
            "runtime_trace_hash": self.runtime_trace_hash,
            "runtime_version": self.runtime_version,
            "same_call_path": self.same_call_path,
            "schema": "paperworks.validation_v2.formal_v4_runtime_materialization_receipt_v1",
            "schema_version": "1.0.0",
            "source_commit": self.source_commit,
            "stage2_commit_a_receipt_hash": self.stage2_commit_a_receipt_hash,
            "test1_features_authorized": self.test1_features_authorized,
            "trace_contract_hash": self.trace_contract_hash,
            "validator_version": self.validator_version,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.payload(), "receipt_hash": self.receipt_hash}


@dataclass(frozen=True)
class EvaluatedFormalV4ExplanationUnitV1:
    run_authorization: Exp05RunAuthorizationV1
    runtime_trace_hash: str
    materialized_trace: MaterializedFormalV4TraceV1
    explanation: FormalV4ExplanationRecordV1
    fidelity_result: FormalV4ExplanationFidelityResultV1
    materialization_receipt: FormalV4RuntimeMaterializationReceiptV1
    unit_hash: str

    def payload(self) -> dict[str, Any]:
        return {
            "run_authorization_hash": self.run_authorization.authorization_hash,
            "explanation_hash": self.explanation.artifact_hash,
            "fidelity_result_hash": self.fidelity_result.result_hash,
            "materialization_receipt_hash": self.materialization_receipt.receipt_hash,
            "materialized_trace_hash": self.materialized_trace.self_hash,
            "runtime_trace_hash": self.runtime_trace_hash,
            "schema": "paperworks.validation_v2.exp05_evaluated_unit_v1",
            "schema_version": "1.0.0",
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.payload(), "unit_hash": self.unit_hash}


def validate_formal_v4_runtime_materialization_receipt_v1(
    receipt: FormalV4RuntimeMaterializationReceiptV1,
    *,
    unit: EvaluatedFormalV4ExplanationUnitV1,
) -> str:
    """Replay every safety and authority binding in a materialization receipt."""

    if type(receipt) is not FormalV4RuntimeMaterializationReceiptV1:
        _fail("EXP05_MATERIALIZATION_RECEIPT_TYPE_INVALID")
    trace = unit.materialized_trace
    for value, code in (
        (receipt.preregistration_hash, "EXP05_RECEIPT_PREREGISTRATION_HASH_INVALID"),
        (receipt.exp05_run_authorization_hash, "EXP05_RECEIPT_RUN_AUTHORIZATION_HASH_INVALID"),
        (receipt.runtime_trace_hash, "EXP05_RECEIPT_RUNTIME_TRACE_HASH_INVALID"),
        (receipt.observation_window_hash, "EXP05_RECEIPT_WINDOW_HASH_INVALID"),
        (receipt.materialized_trace_hash, "EXP05_RECEIPT_MATERIALIZED_TRACE_HASH_INVALID"),
        (receipt.descriptor_hash, "EXP05_RECEIPT_DESCRIPTOR_HASH_INVALID"),
        (receipt.descriptor_set_hash, "EXP05_RECEIPT_DESCRIPTOR_SET_HASH_INVALID"),
        (receipt.portfolio_authority_hash, "EXP05_RECEIPT_PORTFOLIO_HASH_INVALID"),
        (receipt.authorization_hash, "EXP05_RECEIPT_AUTHORIZATION_HASH_INVALID"),
        (receipt.execution_context_hash, "EXP05_RECEIPT_CONTEXT_HASH_INVALID"),
        (receipt.receipt_hash, "EXP05_RECEIPT_HASH_INVALID"),
    ):
        _hash(value, code)
    _commit(receipt.source_commit)
    if receipt.execution_scope not in _SCOPES or type(receipt.test1_features_authorized) is not bool:
        _fail("EXP05_RECEIPT_EXECUTION_SCOPE_INVALID")
    if receipt.execution_scope == "SYNTHETIC_CONFORMANCE":
        scope_bindings = (
            receipt.stage2_commit_a_receipt_hash is None,
            receipt.normal_selection_commit_b_receipt_hash is None,
            receipt.test1_features_authorized is False,
            trace.scientific_runner_authorized is False,
        )
    else:
        _hash(receipt.stage2_commit_a_receipt_hash, "EXP05_RECEIPT_COMMIT_A_HASH_INVALID")
        _hash(receipt.normal_selection_commit_b_receipt_hash, "EXP05_RECEIPT_COMMIT_B_HASH_INVALID")
        scope_bindings = (
            receipt.test1_features_authorized is True,
            trace.scientific_runner_authorized is True,
        )
    exact_bindings = (
        receipt.runner_contract_hash == EXP05_ONE_PATH_RUNNER_CONTRACT_HASH,
        receipt.runtime_version == FORMAL_V4_RUNTIME_VERSION == trace.runtime_version,
        receipt.trace_contract_hash == FORMAL_V4_TRACE_CONTRACT_HASH == trace.trace_contract_hash,
        receipt.runtime_trace_hash == unit.runtime_trace_hash == trace.runtime_trace_hash,
        receipt.materialized_trace_hash == trace.self_hash,
        receipt.descriptor_hash == trace.descriptor_hash,
        receipt.descriptor_set_hash == trace.descriptor_set_hash,
        receipt.portfolio_authority_hash == trace.portfolio_authority_hash,
        receipt.authorization_hash == trace.authorization_hash,
        receipt.execution_context_hash == trace.execution_context_hash,
        receipt.source_commit == trace.source_commit,
        receipt.renderer_contract_hash == EXP05_RENDERER_CONTRACT_HASH,
        receipt.validator_version == EXP05_FIDELITY_VALIDATOR_VERSION,
        receipt.same_call_path is True,
        receipt.labels_accessed is False,
        receipt.heldout_accessed is False,
        type(receipt.provider_calls) is int and receipt.provider_calls == 0,
        type(receipt.llm_calls) is int and receipt.llm_calls == 0,
        receipt.receipt_hash == canonical_document_hash_v1(receipt.payload()),
        *scope_bindings,
    )
    if not all(exact_bindings):
        _fail("EXP05_MATERIALIZATION_RECEIPT_BINDING_MISMATCH")
    return receipt.receipt_hash


def validate_evaluated_formal_v4_explanation_unit_v1(
    unit: EvaluatedFormalV4ExplanationUnitV1,
) -> str:
    if type(unit) is not EvaluatedFormalV4ExplanationUnitV1:
        _fail("EXP05_EVALUATED_UNIT_TYPE_INVALID")
    receipt = unit.materialization_receipt
    authorization = unit.run_authorization
    if (
        type(authorization) is not Exp05RunAuthorizationV1
        or authorization.authorization_hash != canonical_document_hash_v1(authorization.payload())
        or authorization.labels_authorized is not False
        or authorization.heldout_authorized is not False
        or authorization.provider_calls_authorized is not False
        or receipt.exp05_run_authorization_hash != authorization.authorization_hash
        or receipt.execution_scope != authorization.execution_scope
        or receipt.preregistration_hash != authorization.preregistration_hash
        or receipt.source_commit != authorization.source_commit
        or receipt.portfolio_authority_hash != authorization.portfolio_authority_hash
        or receipt.authorization_hash != authorization.runtime_authorization_hash
        or receipt.execution_context_hash != authorization.execution_context_hash
        or receipt.stage2_commit_a_receipt_hash != authorization.stage2_commit_a_receipt_hash
        or receipt.normal_selection_commit_b_receipt_hash != authorization.normal_selection_commit_b_receipt_hash
        or receipt.test1_features_authorized is not authorization.test1_features_authorized
    ):
        _fail("EXP05_UNIT_RUN_AUTHORIZATION_BINDING_MISMATCH")
    validate_formal_v4_runtime_materialization_receipt_v1(receipt, unit=unit)
    if (
        receipt.runtime_trace_hash != unit.runtime_trace_hash
        or receipt.materialized_trace_hash != unit.materialized_trace.self_hash
        or unit.explanation.materialized_trace_hash != unit.materialized_trace.self_hash
        or unit.fidelity_result.materialized_trace_hash != unit.materialized_trace.self_hash
        or unit.fidelity_result.explanation_artifact_hash != unit.explanation.artifact_hash
        or unit.unit_hash != canonical_document_hash_v1(unit.payload())
    ):
        _fail("EXP05_EVALUATED_UNIT_REPLAY_MISMATCH")
    replayed = validate_formal_v4_explanation_fidelity_v1(unit.materialized_trace, unit.explanation)
    if replayed != unit.fidelity_result:
        _fail("EXP05_EVALUATED_UNIT_FIDELITY_REPLAY_MISMATCH")
    return unit.unit_hash


def execute_and_materialize_formal_v4_rule_v1(
    bundle: FormalV4AuthorizedRuntimeV1,
    *,
    authorization: Exp05RunAuthorizationV1,
    execution_context: FormalV4ExecutionContextV1,
    repository_root: Path,
    window: FormalV4ObservationWindowV1,
) -> EvaluatedFormalV4ExplanationUnitV1:
    """Execute exactly once and return one indivisible, replayable EXP-05 unit."""

    validate_exp05_run_authorization_v1(
        authorization, bundle=bundle, execution_context=execution_context,
    )
    runtime_trace = execute_formal_v4_rule_v1(
        bundle,
        execution_context=execution_context,
        repository_root=repository_root,
        window=window,
    )
    descriptors = tuple(item for item in bundle.authority.descriptors if item.relation_id == runtime_trace.relation_id)
    if len(descriptors) != 1:
        _fail("EXP05_DESCRIPTOR_SELECTION_REJECTED")
    materialized = materialize_formal_v4_trace_v1(
        runtime_trace=runtime_trace,
        descriptor=descriptors[0],
        authority=bundle.authority,
        receipt=bundle.receipt,
        execution_context=execution_context,
        observation_window=window,
    )
    expected_scientific_scope = authorization.execution_scope == "SCIENTIFIC_V2"
    if materialized.scientific_runner_authorized is not expected_scientific_scope:
        provisional_materialized = replace(
            materialized,
            scientific_runner_authorized=expected_scientific_scope,
            self_hash=_ZERO,
        )
        materialized = replace(
            provisional_materialized,
            self_hash=provisional_materialized.expected_self_hash,
        )
    explanation = render_formal_v4_explanation_v1(materialized)
    fidelity = validate_formal_v4_explanation_fidelity_v1(materialized, explanation)
    receipt_base = FormalV4RuntimeMaterializationReceiptV1(
        preregistration_hash=authorization.preregistration_hash,
        exp05_run_authorization_hash=authorization.authorization_hash,
        execution_scope=authorization.execution_scope,
        stage2_commit_a_receipt_hash=authorization.stage2_commit_a_receipt_hash,
        normal_selection_commit_b_receipt_hash=authorization.normal_selection_commit_b_receipt_hash,
        test1_features_authorized=authorization.test1_features_authorized,
        source_commit=authorization.source_commit,
        runner_contract_hash=EXP05_ONE_PATH_RUNNER_CONTRACT_HASH,
        runtime_version=FORMAL_V4_RUNTIME_VERSION,
        trace_contract_hash=FORMAL_V4_TRACE_CONTRACT_HASH,
        runtime_trace_hash=runtime_trace.trace_hash,
        observation_window_hash=hash_formal_v4_observation_window_v1(window),
        materialized_trace_hash=materialized.self_hash,
        descriptor_hash=descriptors[0].descriptor_hash,
        descriptor_set_hash=bundle.authority.descriptor_set_hash,
        portfolio_authority_hash=bundle.authority.authority_hash,
        authorization_hash=bundle.receipt.authorization_hash,
        execution_context_hash=execution_context.context_hash,
        renderer_contract_hash=EXP05_RENDERER_CONTRACT_HASH,
        validator_version=EXP05_FIDELITY_VALIDATOR_VERSION,
        same_call_path=True,
        labels_accessed=False,
        heldout_accessed=False,
        provider_calls=0,
        llm_calls=0,
        receipt_hash=_ZERO,
    )
    materialization_receipt = replace(
        receipt_base, receipt_hash=canonical_document_hash_v1(receipt_base.payload())
    )
    unit_base = EvaluatedFormalV4ExplanationUnitV1(
        run_authorization=authorization,
        runtime_trace_hash=runtime_trace.trace_hash,
        materialized_trace=materialized,
        explanation=explanation,
        fidelity_result=fidelity,
        materialization_receipt=materialization_receipt,
        unit_hash=_ZERO,
    )
    unit = replace(unit_base, unit_hash=canonical_document_hash_v1(unit_base.payload()))
    validate_evaluated_formal_v4_explanation_unit_v1(unit)
    return unit


__all__ = [
    "EXP05_ONE_PATH_RUNNER_CONTRACT_HASH", "EXP05_ONE_PATH_RUNNER_VERSION",
    "EvaluatedFormalV4ExplanationUnitV1", "Exp05RunAuthorizationV1", "Exp05RunnerError",
    "FormalV4RuntimeMaterializationReceiptV1", "authorize_exp05_execution_v1",
    "execute_and_materialize_formal_v4_rule_v1",
    "validate_formal_v4_runtime_materialization_receipt_v1",
    "validate_evaluated_formal_v4_explanation_unit_v1", "validate_exp05_run_authorization_v1",
]
