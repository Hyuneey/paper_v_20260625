"""Deterministic synthetic delayed-response contract vertical slice."""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Mapping

from paperworks.contracts.accepted_rule import canonical_rule_verification_subject_sha256
from paperworks.contracts.explanation_v1 import (
    canonical_explanation_record_sha256,
    explanation_record_to_dict,
    parse_explanation_record,
    render_delayed_response_explanation,
)
from paperworks.contracts.parameter_v1 import (
    CalibrationParameterV1,
    calibration_parameter_to_dict,
    load_calibration_parameter,
)
from paperworks.contracts.phase1_adapters import (
    ContractAdapterResult,
    DelayedResponseArtifactCollectionV1,
    adapt_phase1_calibration_parameter,
    adapt_phase1_candidate_graph,
    adapt_phase1_evidence_package,
)
from paperworks.contracts.rule_v1 import (
    canonical_rule_document_sha256,
    load_delayed_response_rule,
)
from paperworks.contracts.runtime_authority import (
    authorize_delayed_response_runtime,
    canonical_runtime_authorization_sha256,
    canonical_verifier_policy_sha256,
    verify_runtime_authorization_bundle,
)
from paperworks.contracts.runtime_v1 import (
    canonical_runtime_trace_sha256,
    canonical_runtime_window_sha256,
    execute_delayed_response_rule,
    load_runtime_window,
    parse_runtime_trace,
    runtime_trace_to_dict,
)
from paperworks.contracts.verifier_v1 import (
    DelayedResponseVerifierPolicyV1,
    canonical_verifier_result_sha256,
    verify_delayed_response_rule,
)


PIPELINE_VERSION = "task032f-vertical-slice-1.0.0"
DEFAULT_CONFIG = Path("configs/contracts/task032f_synthetic_vertical_slice.json")
EXPECTED_TRACE_OPERATORS = (
    "regime_check",
    "trigger_check",
    "lag_check",
    "window_check",
    "relation_check",
    "tolerance_check",
    "persistence_check",
    "abstention_check",
    "output",
)
_PARAMETER_SOURCE_KEYS = (
    "calibration_delay",
    "calibration_tolerance",
    "calibration_duration",
    "calibration_support",
)


class SyntheticVerticalSliceError(ValueError):
    """Sanitized fail-closed integration error."""

    def __init__(self, stage: str, issue_code: str, message: str) -> None:
        super().__init__(f"{issue_code} at {stage}: {message}")
        self.stage = stage
        self.issue_code = issue_code
        self.message = message

    def to_failure_record(self) -> dict[str, str]:
        return {"stage": self.stage, "issue_code": self.issue_code, "message": self.message}


@dataclass(frozen=True)
class SyntheticScenarioResultV1:
    scenario_id: str
    input_window_hash: str
    execution_id: str
    trace_hash: str
    explanation_id: str
    explanation_hash: str
    status: str
    trigger_satisfied: bool
    expected_effect_satisfied: bool | None
    violation_detected: bool
    abstention_reason: str | None
    nine_steps_verified: bool
    trace_binding_verified: bool
    explanation_binding_verified: bool
    contract_expectation_matched: bool


@dataclass(frozen=True)
class SyntheticAdapterLedgerV1:
    source_fixture_hashes: tuple[tuple[str, str], ...]
    statuses: tuple[tuple[str, str], ...]
    source_hashes: tuple[tuple[str, str], ...]
    target_hashes: tuple[tuple[str, str], ...]
    approved_parameter_hashes: tuple[tuple[str, str], ...]
    parameter_lineage_matches: tuple[tuple[str, bool], ...]
    severity_parameter_hash: str


@dataclass(frozen=True)
class SyntheticVerificationLedgerV1:
    candidate_rule_id: str
    candidate_transport_hash: str
    verification_subject_hash: str
    accepted_rule_hash: str
    verifier_result_id: str
    verifier_result_hash: str
    stage_statuses: tuple[tuple[int, str, str], ...]
    all_twenty_stages_passed: bool
    runtime_authorized: bool


@dataclass(frozen=True)
class SyntheticRuntimeLedgerV1:
    authorization_id: str
    authorization_hash: str
    verifier_policy_hash: str
    bound_rule_hash: str
    bound_verifier_result_hash: str
    bound_graph_hash: str
    bound_evidence_hash: str
    bound_parameter_hashes: tuple[tuple[str, str], ...]
    scenarios: tuple[SyntheticScenarioResultV1, ...]


@dataclass(frozen=True)
class SyntheticVerticalSliceReportV1:
    schema_version: str
    task_id: str
    pipeline_version: str
    created_at: str
    execution_scope: str
    status: str
    claim_boundary: str
    config_hash: str
    integration_code_version: str
    adapters: SyntheticAdapterLedgerV1
    verification: SyntheticVerificationLedgerV1
    runtime: SyntheticRuntimeLedgerV1
    report_hash: str


def synthetic_vertical_slice_report_to_dict(report: SyntheticVerticalSliceReportV1) -> dict[str, Any]:
    return {
        "schema_version": report.schema_version,
        "task_id": report.task_id,
        "pipeline_version": report.pipeline_version,
        "created_at": report.created_at,
        "execution_scope": report.execution_scope,
        "status": report.status,
        "claim_boundary": report.claim_boundary,
        "config_hash": report.config_hash,
        "integration_code_version": report.integration_code_version,
        "adapters": {
            "source_fixture_hashes": dict(report.adapters.source_fixture_hashes),
            "statuses": dict(report.adapters.statuses),
            "source_hashes": dict(report.adapters.source_hashes),
            "target_hashes": dict(report.adapters.target_hashes),
            "approved_parameter_hashes": dict(report.adapters.approved_parameter_hashes),
            "parameter_lineage_matches": dict(report.adapters.parameter_lineage_matches),
            "severity_parameter_hash": report.adapters.severity_parameter_hash,
        },
        "verification": {
            "candidate_rule_id": report.verification.candidate_rule_id,
            "candidate_transport_hash": report.verification.candidate_transport_hash,
            "verification_subject_hash": report.verification.verification_subject_hash,
            "accepted_rule_hash": report.verification.accepted_rule_hash,
            "verifier_result_id": report.verification.verifier_result_id,
            "verifier_result_hash": report.verification.verifier_result_hash,
            "stage_statuses": [
                {"stage": stage, "name": name, "status": status}
                for stage, name, status in report.verification.stage_statuses
            ],
            "all_twenty_stages_passed": report.verification.all_twenty_stages_passed,
            "runtime_authorized": report.verification.runtime_authorized,
        },
        "runtime": {
            "authorization_id": report.runtime.authorization_id,
            "authorization_hash": report.runtime.authorization_hash,
            "verifier_policy_hash": report.runtime.verifier_policy_hash,
            "bound_rule_hash": report.runtime.bound_rule_hash,
            "bound_verifier_result_hash": report.runtime.bound_verifier_result_hash,
            "bound_graph_hash": report.runtime.bound_graph_hash,
            "bound_evidence_hash": report.runtime.bound_evidence_hash,
            "bound_parameter_hashes": dict(report.runtime.bound_parameter_hashes),
            "scenarios": [_scenario_to_dict(item) for item in report.runtime.scenarios],
        },
        "report_hash": report.report_hash,
    }


def canonical_vertical_slice_report_bytes(
    report: SyntheticVerticalSliceReportV1 | Mapping[str, Any],
) -> bytes:
    document = (
        synthetic_vertical_slice_report_to_dict(report)
        if isinstance(report, SyntheticVerticalSliceReportV1)
        else copy.deepcopy(dict(report))
    )
    document.pop("report_hash", None)
    return json.dumps(
        document, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("utf-8")


def canonical_vertical_slice_report_sha256(
    report: SyntheticVerticalSliceReportV1 | Mapping[str, Any],
) -> str:
    return hashlib.sha256(canonical_vertical_slice_report_bytes(report)).hexdigest()


def run_task032f_vertical_slice(
    config: str | Path | Mapping[str, Any] = DEFAULT_CONFIG,
    *,
    repository_root: str | Path | None = None,
    document_overrides: Mapping[str, Mapping[str, Any]] | None = None,
) -> SyntheticVerticalSliceReportV1:
    """Run the complete synthetic path; failures return no partial report."""

    root = Path(repository_root).resolve() if repository_root is not None else _repository_root()
    config_document = _load_config(config, root)
    _validate_config(config_document)
    overrides = document_overrides or {}
    config_hash = _canonical_mapping_sha256(config_document)
    source_documents: dict[str, Mapping[str, Any]] = {}
    source_fixture_hashes: dict[str, str] = {}
    for key, relative_path in sorted(config_document["source_artifacts"].items()):
        source_documents[key], source_fixture_hashes[key] = _load_document(
            root, relative_path, override=overrides.get(key)
        )

    contexts = config_document["adapter_contexts"]
    graph_result = adapt_phase1_candidate_graph(
        source_documents["candidate_universe"],
        context=copy.deepcopy(contexts["graph"]),
        gdn_edges=source_documents["gdn_edges"],
    )
    _require_created("graph_adapter", graph_result)
    evidence_result = adapt_phase1_evidence_package(
        source_documents["relation_profile"],
        source_documents["relation_evidence_pack"],
        context=copy.deepcopy(contexts["evidence"]),
    )
    _require_created("evidence_adapter", evidence_result)

    parameter_results: dict[str, ContractAdapterResult] = {}
    parameter_context = contexts["parameters"]
    for source_key in _PARAMETER_SOURCE_KEYS:
        mapping = _parameter_mapping(parameter_context, source_key)
        result = adapt_phase1_calibration_parameter(
            source_documents[source_key], mapping=mapping
        )
        _require_created(f"parameter_adapter.{source_key}", result)
        parameter_results[source_key] = result

    canonical = config_document["canonical_artifacts"]
    approved_parameters: list[CalibrationParameterV1] = []
    lineage_matches: dict[str, bool] = {}
    for parameter_id, relative_path in sorted(canonical["approved_parameters"].items()):
        approved = _load_parameter(
            root,
            relative_path,
            override=overrides.get(f"approved:{parameter_id}"),
        )
        adapter_result = next(
            (
                item
                for item in parameter_results.values()
                if item.target_artifact is not None
                and item.target_artifact.parameter_id == parameter_id
            ),
            None,
        )
        if adapter_result is None or not _parameter_lineage_matches(
            adapter_result.target_artifact, approved
        ):
            _fail(
                "parameter_authority_bridge",
                "PARAMETER_ADAPTER_APPROVAL_LINEAGE_MISMATCH",
                "calibrated adapter output does not match its explicit approved artifact",
            )
        lineage_matches[parameter_id] = True
        approved_parameters.append(approved)

    severity = _load_parameter(
        root,
        canonical["severity_parameter"],
        override=overrides.get("severity_parameter"),
    )
    if severity.parameter_role != "severity_boundary" or severity.approval_status != "approved":
        _fail(
            "severity_parameter",
            "SEVERITY_PARAMETER_INVALID",
            "explicit severity parameter must be approved and have severity_boundary role",
        )
    approved_parameters.append(severity)
    approved_parameters.sort(key=lambda item: item.parameter_id)

    graph = graph_result.target_artifact
    evidence = evidence_result.target_artifact
    if graph is None or evidence is None:
        _fail("artifact_collection", "ADAPTER_TARGET_MISSING", "created adapter target is absent")
    artifacts = DelayedResponseArtifactCollectionV1(
        graph, evidence, tuple(approved_parameters)
    )

    rule_path = config_document["candidate_rule"]
    if "candidate_rule" in overrides:
        from paperworks.contracts.rule_v1 import parse_delayed_response_rule

        candidate = parse_delayed_response_rule(copy.deepcopy(overrides["candidate_rule"]))
    else:
        candidate = load_delayed_response_rule(_safe_path(root, rule_path))
    if candidate.status != "candidate" or candidate.verified_rule_hash is not None:
        _fail(
            "candidate_rule",
            "CANDIDATE_AUTHORITY_PRECLAIMED",
            "candidate must not preclaim accepted authority",
        )
    _precheck_rule_references(candidate, artifacts)

    policy_document, _ = _load_document(
        root,
        config_document["verifier_policy"],
        override=overrides.get("verifier_policy"),
    )
    policy = DelayedResponseVerifierPolicyV1.from_dict(policy_document)
    try:
        verification = verify_delayed_response_rule(candidate, artifacts, policy=policy)
    except ValueError as exc:
        _fail("verifier", getattr(exc, "issue_code", "VERIFIER_FAILED"), "verifier failed closed")
    if (
        verification.verifier_result.status != "accepted"
        or verification.accepted_rule is None
        or len(verification.stage_records) != 20
        or any(item.status != "passed" for item in verification.stage_records)
    ):
        _fail(
            "verifier",
            "VERTICAL_SLICE_VERIFIER_NOT_ACCEPTED",
            "all twenty verifier stages must pass",
        )
    accepted_rule = verification.accepted_rule
    subject_hash = canonical_rule_verification_subject_sha256(accepted_rule)
    if not (
        accepted_rule.verified_rule_hash
        == verification.verifier_result.rule_hash
        == verification.verification_subject_hash
        == subject_hash
    ):
        _fail("verifier", "VERTICAL_SLICE_AUTHORITY_HASH_MISMATCH", "accepted hashes differ")
    if not (
        canonical_verifier_result_sha256(verification.verifier_result)
        == verification.verifier_result_hash
        == verification.verifier_result.artifact_hash
    ):
        _fail("verifier", "VERTICAL_SLICE_VERIFIER_HASH_MISMATCH", "verifier-result hash differs")

    runtime_config = config_document["runtime_authorization"]
    try:
        authorization = authorize_delayed_response_runtime(
            accepted_rule,
            verification.verifier_result,
            artifacts,
            verifier_policy=policy,
            created_at=runtime_config["created_at"],
            runtime_scope=runtime_config["runtime_scope"],
        )
        verify_runtime_authorization_bundle(authorization)
    except ValueError as exc:
        _fail(
            "runtime_authorization",
            getattr(exc, "issue_code", "RUNTIME_AUTHORIZATION_FAILED"),
            "runtime authorization failed closed",
        )

    scenario_results: list[SyntheticScenarioResultV1] = []
    for scenario in config_document["scenarios"]:
        scenario_id = scenario["scenario_id"]
        window_override = overrides.get(f"scenario:{scenario_id}")
        if window_override is None:
            window = load_runtime_window(_safe_path(root, scenario["window_file"]))
        else:
            from paperworks.contracts.runtime_v1 import parse_runtime_window

            window = parse_runtime_window(copy.deepcopy(window_override))
        try:
            execution = execute_delayed_response_rule(authorization, window)
            trace = parse_runtime_trace(runtime_trace_to_dict(execution.trace))
        except ValueError as exc:
            _fail(
                f"runtime.{scenario_id}",
                getattr(exc, "issue_code", "RUNTIME_SCENARIO_FAILED"),
                "runtime scenario failed closed",
            )
        nine_steps = (
            len(trace.satisfaction_trace) == 9
            and tuple(item.operator for item in trace.satisfaction_trace)
            == EXPECTED_TRACE_OPERATORS
        )
        trace_binding = (
            trace.rule_hash == accepted_rule.verified_rule_hash
            and trace.verifier_result_ref
            == verification.verifier_result.verifier_result_id
            and trace.input_window_id == window.input_window_id
            and canonical_runtime_trace_sha256(trace) == trace.artifact_hash
        )
        if not nine_steps or not trace_binding:
            _fail(
                f"runtime.{scenario_id}",
                "RUNTIME_TRACE_BINDING_FAILED",
                "runtime trace failed step or authority binding",
            )
        try:
            explanation = render_delayed_response_explanation(
                authorization, execution, window
            )
            parsed_explanation = parse_explanation_record(
                explanation_record_to_dict(explanation)
            )
        except ValueError as exc:
            _fail(
                f"explanation.{scenario_id}",
                getattr(exc, "issue_code", "EXPLANATION_FAILED"),
                "explanation binding failed closed",
            )
        explanation_binding = (
            parsed_explanation.execution_id == trace.execution_id
            and parsed_explanation.rule_hash == accepted_rule.verified_rule_hash
            and parsed_explanation.verifier_result_ref
            == verification.verifier_result.verifier_result_id
            and canonical_explanation_record_sha256(parsed_explanation)
            == parsed_explanation.artifact_hash
            and not parsed_explanation.detector_result.available
            and not parsed_explanation.fusion_result.available
        )
        expectation = _scenario_expectation_matches(scenario, execution)
        if not explanation_binding:
            _fail(
                f"explanation.{scenario_id}",
                "EXPLANATION_BINDING_FAILED",
                "explanation does not bind the authorized trace",
            )
        if not expectation:
            _fail(
                f"expectation.{scenario_id}",
                "CONTRACT_EXPECTATION_MISMATCH",
                "synthetic scenario differs from its predeclared contract state",
            )
        scenario_results.append(
            SyntheticScenarioResultV1(
                scenario_id=scenario_id,
                input_window_hash=canonical_runtime_window_sha256(window),
                execution_id=trace.execution_id,
                trace_hash=trace.artifact_hash,
                explanation_id=parsed_explanation.explanation_id,
                explanation_hash=parsed_explanation.artifact_hash,
                status=trace.status,
                trigger_satisfied=trace.trigger_satisfied,
                expected_effect_satisfied=trace.expected_effect_satisfied,
                violation_detected=trace.violation_detected,
                abstention_reason=execution.abstention_reason,
                nine_steps_verified=nine_steps,
                trace_binding_verified=trace_binding,
                explanation_binding_verified=explanation_binding,
                contract_expectation_matched=expectation,
            )
        )

    adapter_results = {
        "graph": graph_result,
        "evidence": evidence_result,
        **parameter_results,
    }
    adapter_ledger = SyntheticAdapterLedgerV1(
        source_fixture_hashes=tuple(sorted(source_fixture_hashes.items())),
        statuses=tuple(sorted((name, item.status) for name, item in adapter_results.items())),
        source_hashes=tuple(sorted((name, item.source_sha256) for name, item in adapter_results.items())),
        target_hashes=tuple(
            sorted((name, item.target_artifact_sha256 or "") for name, item in adapter_results.items())
        ),
        approved_parameter_hashes=tuple(
            sorted((item.parameter_id, item.artifact_hash) for item in approved_parameters)
        ),
        parameter_lineage_matches=tuple(sorted(lineage_matches.items())),
        severity_parameter_hash=severity.artifact_hash,
    )
    verification_ledger = SyntheticVerificationLedgerV1(
        candidate_rule_id=candidate.rule_id,
        candidate_transport_hash=canonical_rule_document_sha256(candidate),
        verification_subject_hash=verification.verification_subject_hash,
        accepted_rule_hash=accepted_rule.verified_rule_hash,
        verifier_result_id=verification.verifier_result.verifier_result_id,
        verifier_result_hash=verification.verifier_result_hash,
        stage_statuses=tuple(
            (item.stage, item.name, item.status) for item in verification.stage_records
        ),
        all_twenty_stages_passed=True,
        runtime_authorized=verification.runtime_authorized,
    )
    runtime_ledger = SyntheticRuntimeLedgerV1(
        authorization_id=authorization.receipt.authorization_id,
        authorization_hash=canonical_runtime_authorization_sha256(authorization.receipt),
        verifier_policy_hash=canonical_verifier_policy_sha256(policy),
        bound_rule_hash=authorization.receipt.accepted_rule_hash,
        bound_verifier_result_hash=authorization.receipt.verifier_result_hash,
        bound_graph_hash=authorization.receipt.graph_hash,
        bound_evidence_hash=authorization.receipt.evidence_hash,
        bound_parameter_hashes=authorization.receipt.parameter_hashes,
        scenarios=tuple(scenario_results),
    )
    provisional = SyntheticVerticalSliceReportV1(
        schema_version="1.0.0",
        task_id=config_document["task_id"],
        pipeline_version=config_document["pipeline_version"],
        created_at=config_document["created_at"],
        execution_scope="synthetic_only",
        status="completed_synthetic_contract_gate",
        claim_boundary=(
            "The complete delayed-response contract pipeline is connected and "
            "deterministically replayable on predeclared synthetic fixtures."
        ),
        config_hash=config_hash,
        integration_code_version=PIPELINE_VERSION,
        adapters=adapter_ledger,
        verification=verification_ledger,
        runtime=runtime_ledger,
        report_hash="0" * 64,
    )
    return replace(
        provisional, report_hash=canonical_vertical_slice_report_sha256(provisional)
    )


def verify_task032f_deterministic_replay(
    config: str | Path | Mapping[str, Any] = DEFAULT_CONFIG,
    *,
    repository_root: str | Path | None = None,
) -> dict[str, Any]:
    """Execute two fresh complete runs and compare every canonical ledger field."""

    root = Path(repository_root).resolve() if repository_root is not None else _repository_root()
    config_document = _load_config(config, root)
    before = _configured_fixture_hashes(config_document, root)
    first = run_task032f_vertical_slice(config_document, repository_root=root)
    second = run_task032f_vertical_slice(copy.deepcopy(config_document), repository_root=root)
    after = _configured_fixture_hashes(config_document, root)
    first_document = synthetic_vertical_slice_report_to_dict(first)
    second_document = synthetic_vertical_slice_report_to_dict(second)
    replay_verified = first_document == second_document and before == after
    if not replay_verified:
        _fail(
            "deterministic_replay",
            "VERTICAL_SLICE_REPLAY_MISMATCH",
            "fresh complete runs or fixture hashes differ",
        )
    return {
        "schema_version": "1.0.0",
        "task_id": "TASK-032F",
        "status": "deterministic_replay_verified",
        "fresh_runs": 2,
        "fixture_hashes_unchanged": True,
        "reports_byte_equivalent": True,
        "first_report_hash": first.report_hash,
        "second_report_hash": second.report_hash,
        "adapter_target_hashes_equal": first.adapters.target_hashes == second.adapters.target_hashes,
        "candidate_transport_hash_equal": first.verification.candidate_transport_hash == second.verification.candidate_transport_hash,
        "verification_subject_hash_equal": first.verification.verification_subject_hash == second.verification.verification_subject_hash,
        "accepted_rule_hash_equal": first.verification.accepted_rule_hash == second.verification.accepted_rule_hash,
        "verifier_result_binding_equal": (
            first.verification.verifier_result_id,
            first.verification.verifier_result_hash,
        )
        == (
            second.verification.verifier_result_id,
            second.verification.verifier_result_hash,
        ),
        "authorization_binding_equal": (
            first.runtime.authorization_id,
            first.runtime.authorization_hash,
        )
        == (
            second.runtime.authorization_id,
            second.runtime.authorization_hash,
        ),
        "scenario_bindings_equal": tuple(
            (item.execution_id, item.trace_hash, item.explanation_id, item.explanation_hash)
            for item in first.runtime.scenarios
        )
        == tuple(
            (item.execution_id, item.trace_hash, item.explanation_id, item.explanation_hash)
            for item in second.runtime.scenarios
        ),
    }


def _scenario_to_dict(item: SyntheticScenarioResultV1) -> dict[str, Any]:
    return {
        "scenario_id": item.scenario_id,
        "input_window_hash": item.input_window_hash,
        "execution_id": item.execution_id,
        "trace_hash": item.trace_hash,
        "explanation_id": item.explanation_id,
        "explanation_hash": item.explanation_hash,
        "status": item.status,
        "trigger_satisfied": item.trigger_satisfied,
        "expected_effect_satisfied": item.expected_effect_satisfied,
        "violation_detected": item.violation_detected,
        "abstention_reason": item.abstention_reason,
        "nine_steps_verified": item.nine_steps_verified,
        "trace_binding_verified": item.trace_binding_verified,
        "explanation_binding_verified": item.explanation_binding_verified,
        "contract_expectation_matched": item.contract_expectation_matched,
    }


def _load_config(config: str | Path | Mapping[str, Any], root: Path) -> dict[str, Any]:
    if isinstance(config, Mapping):
        return copy.deepcopy(dict(config))
    candidate = Path(config)
    if candidate.is_absolute():
        path = candidate.resolve()
        try:
            path.relative_to(root)
        except ValueError:
            _fail("path_policy", "VERTICAL_SLICE_PATH_ESCAPE", "configuration is outside the repository root")
    else:
        path = _safe_path(root, candidate)
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        _fail("configuration", "VERTICAL_SLICE_CONFIG_INVALID", "configuration is not readable JSON")
    if not isinstance(document, dict):
        _fail("configuration", "VERTICAL_SLICE_CONFIG_INVALID", "configuration must be an object")
    return document


def _validate_config(config: Mapping[str, Any]) -> None:
    required = {
        "schema_version",
        "task_id",
        "pipeline_version",
        "created_at",
        "source_artifacts",
        "adapter_contexts",
        "canonical_artifacts",
        "candidate_rule",
        "verifier_policy",
        "runtime_authorization",
        "scenarios",
        "report_output",
    }
    if set(config) != required:
        _fail("configuration", "VERTICAL_SLICE_CONFIG_FIELDS", "configuration fields differ")
    if config["task_id"] != "TASK-032F" or config["pipeline_version"] != PIPELINE_VERSION:
        _fail("configuration", "VERTICAL_SLICE_CONFIG_VERSION", "task or pipeline version differs")
    source_keys = set(config["source_artifacts"])
    if source_keys != {
        "candidate_universe",
        "gdn_edges",
        "relation_profile",
        "relation_evidence_pack",
        *_PARAMETER_SOURCE_KEYS,
    }:
        _fail("configuration", "VERTICAL_SLICE_SOURCE_SET", "source artifact set differs")
    scenario_ids = [item.get("scenario_id") for item in config["scenarios"]]
    required_scenarios = {
        "response_present",
        "response_missing",
        "no_trigger",
        "multiple_triggers",
        "regime_mismatch",
        "missing_input",
        "first_sample_trigger",
        "insufficient_coverage",
    }
    if set(scenario_ids) != required_scenarios or len(scenario_ids) != len(set(scenario_ids)):
        _fail("configuration", "VERTICAL_SLICE_SCENARIO_SET", "scenario set differs")
    if config["runtime_authorization"].get("runtime_scope") != "synthetic_only":
        _fail("configuration", "VERTICAL_SLICE_SCOPE", "runtime scope must be synthetic_only")


def _load_document(
    root: Path,
    relative_path: str | Path,
    *,
    override: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], str]:
    if override is not None:
        document = copy.deepcopy(dict(override))
        return document, _canonical_mapping_sha256(document)
    path = _safe_path(root, relative_path)
    try:
        raw = path.read_bytes()
        document = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        _fail("fixture_load", "VERTICAL_SLICE_FIXTURE_INVALID", "fixture is not readable JSON")
    if not isinstance(document, dict):
        _fail("fixture_load", "VERTICAL_SLICE_FIXTURE_INVALID", "fixture must be an object")
    return document, hashlib.sha256(raw).hexdigest()


def _load_parameter(
    root: Path, relative_path: str | Path, *, override: Mapping[str, Any] | None
) -> CalibrationParameterV1:
    if override is not None:
        from paperworks.contracts.parameter_v1 import parse_calibration_parameter

        try:
            return parse_calibration_parameter(copy.deepcopy(override))
        except ValueError as exc:
            _fail(
                "parameter_load",
                getattr(exc, "issue_code", "PARAMETER_LOAD_INVALID"),
                "parameter artifact failed closed",
            )
    try:
        return load_calibration_parameter(_safe_path(root, relative_path))
    except ValueError as exc:
        _fail(
            "parameter_load",
            getattr(exc, "issue_code", "PARAMETER_LOAD_INVALID"),
            "parameter artifact failed closed",
        )


def _parameter_mapping(context: Mapping[str, Any], source_key: str) -> dict[str, Any]:
    mapping = copy.deepcopy(dict(context["common"]))
    mapping.update(copy.deepcopy(dict(context[source_key])))
    mapping.update(copy.deepcopy(dict(context["details"][source_key])))
    return mapping


def _parameter_lineage_matches(
    calibrated: CalibrationParameterV1, approved: CalibrationParameterV1
) -> bool:
    calibrated_document = calibration_parameter_to_dict(calibrated)
    approved_document = calibration_parameter_to_dict(approved)
    for document in (calibrated_document, approved_document):
        for key in ("artifact_hash", "approval_status", "approved_by", "approval_date"):
            document.pop(key, None)
    return calibrated_document == approved_document


def _precheck_rule_references(candidate: Any, artifacts: DelayedResponseArtifactCollectionV1) -> None:
    checks = (
        (set(candidate.graph_edge_refs), set(artifacts.edge_by_id), "graph edge"),
        (set(candidate.evidence_refs), set(artifacts.evidence_by_id), "evidence"),
        (set(candidate.normal_reference_refs), set(artifacts.normal_reference_by_id), "normal reference"),
        (set(candidate.parameter_refs), set(artifacts.parameter_by_id), "parameter"),
    )
    for required, available, label in checks:
        if not required.issubset(available):
            _fail(
                "candidate_reference_precheck",
                "CANDIDATE_REFERENCE_MISSING",
                f"candidate {label} reference is absent",
            )


def _scenario_expectation_matches(
    expected: Mapping[str, Any], execution: Any
) -> bool:
    trace = execution.trace
    return (
        trace.status == expected["expected_status"]
        and trace.trigger_satisfied == expected["expected_trigger_satisfied"]
        and trace.expected_effect_satisfied == expected["expected_effect_satisfied"]
        and trace.violation_detected == expected["expected_violation"]
        and execution.abstention_reason == expected["expected_abstention_reason"]
    )


def _require_created(stage: str, result: ContractAdapterResult) -> None:
    if result.status != "created" or not result.target_artifact_created:
        _fail(stage, f"ADAPTER_{result.status.upper()}", "adapter did not create a complete target")


def _configured_fixture_hashes(config: Mapping[str, Any], root: Path) -> tuple[tuple[str, str], ...]:
    paths: dict[str, str] = dict(config["source_artifacts"])
    paths["candidate_rule"] = config["candidate_rule"]
    paths["verifier_policy"] = config["verifier_policy"]
    paths["severity_parameter"] = config["canonical_artifacts"]["severity_parameter"]
    for parameter_id, path in config["canonical_artifacts"]["approved_parameters"].items():
        paths[f"approved:{parameter_id}"] = path
    for item in config["scenarios"]:
        paths[f"scenario:{item['scenario_id']}"] = item["window_file"]
    return tuple(
        sorted(
            (name, hashlib.sha256(_safe_path(root, path).read_bytes()).hexdigest())
            for name, path in paths.items()
        )
    )


def _safe_path(root: Path, relative_path: str | Path) -> Path:
    candidate = Path(relative_path)
    if candidate.is_absolute():
        _fail("path_policy", "VERTICAL_SLICE_ABSOLUTE_PATH", "only repository-relative paths are allowed")
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        _fail("path_policy", "VERTICAL_SLICE_PATH_ESCAPE", "path escapes the repository root")
    return resolved


def _canonical_mapping_sha256(document: Mapping[str, Any]) -> str:
    payload = json.dumps(
        copy.deepcopy(dict(document)),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _fail(stage: str, issue_code: str, message: str) -> None:
    raise SyntheticVerticalSliceError(stage, issue_code, message)
