"""Bounded mock-only verifier-feedback rule refinement loop."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Sequence

from paperworks.data.contracts import SCHEMA_VERSION, stable_hash
from paperworks.dsl import RuleAst, RuleSchemaRegistry
from paperworks.profiling import RelationEvidencePack
from paperworks.verification import (
    FeedbackIssue,
    VerificationConfig,
    VerificationDataset,
    VerificationReport,
    verify_rule,
)

from paperworks.planning.llm import (
    LLMPlannerResult,
    LLMPlanningError,
    LLMProvider,
    PlannerConfig,
    PromptTemplate,
    ProviderConfig,
    plan_rule_with_provider,
)


RECOVERABLE_FEEDBACK_CODES = frozenset(
    {
        "NORMAL_FP_TOO_HIGH",
        "VALIDATION_COVERAGE_TOO_LOW",
        "STRUCTURAL_DUPLICATE",
        "FIRING_OVERLAP_DUPLICATE",
    }
)


@dataclass(frozen=True)
class RefinementPolicy:
    max_iterations: int
    provider_failure_limit: int = 1
    stop_on_repeated_rule: bool = True
    stop_on_no_improvement: bool = True
    config_version: str = "1.0"

    def __post_init__(self) -> None:
        if self.max_iterations <= 0:
            raise LLMPlanningError("max_iterations must be positive")
        if self.provider_failure_limit <= 0:
            raise LLMPlanningError("provider_failure_limit must be positive")

    @property
    def config_hash(self) -> str:
        return stable_hash(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RefinementIteration:
    iteration_index: int
    previous_rule_hash: str
    verifier_feedback_ids: tuple[str, ...]
    feedback_codes: tuple[str, ...]
    revised_rule_hash: str | None
    parse_status: str
    schema_validation_status: str
    verification_status: str
    stop_reason: str | None
    planner_result: LLMPlannerResult
    verification_report: VerificationReport | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "iteration_index": self.iteration_index,
            "previous_rule_hash": self.previous_rule_hash,
            "verifier_feedback_ids": list(self.verifier_feedback_ids),
            "feedback_codes": list(self.feedback_codes),
            "revised_rule_hash": self.revised_rule_hash,
            "parse_status": self.parse_status,
            "schema_validation_status": self.schema_validation_status,
            "verification_status": self.verification_status,
            "stop_reason": self.stop_reason,
            "planner_result": self.planner_result.to_dict(),
            "verification_report": self.verification_report.to_dict() if self.verification_report else None,
        }


@dataclass(frozen=True)
class RefinementSessionResult:
    status: str
    stop_reason: str
    max_iterations: int
    iterations: tuple[RefinementIteration, ...]
    initial_planner_result: LLMPlannerResult
    initial_verification_report: VerificationReport | None
    final_rule: RuleAst | None
    final_verification_report: VerificationReport | None
    policy_hash: str
    provider_config_hash: str
    planner_config_hash: str
    verifier_config_hash: str
    code_commit: str | None
    created_at: str
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "refinement_session"
    network_allowed: bool = False
    redaction_status: str = "passed"

    def __post_init__(self) -> None:
        if self.status not in {"verified", "rejected", "provider_error"}:
            raise LLMPlanningError("unsupported refinement status")
        if self.network_allowed:
            raise LLMPlanningError("TASK-013 refinement artifacts must record network_allowed=false")

    @property
    def session_id(self) -> str:
        return stable_hash(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "status": self.status,
            "stop_reason": self.stop_reason,
            "max_iterations": self.max_iterations,
            "iterations": [iteration.to_dict() for iteration in self.iterations],
            "initial_planner_result": self.initial_planner_result.to_dict(),
            "initial_verification_report": (
                self.initial_verification_report.to_dict() if self.initial_verification_report else None
            ),
            "final_rule": self.final_rule.to_dict() if self.final_rule else None,
            "final_verification_report": (
                self.final_verification_report.to_dict() if self.final_verification_report else None
            ),
            "policy_hash": self.policy_hash,
            "provider_config_hash": self.provider_config_hash,
            "planner_config_hash": self.planner_config_hash,
            "verifier_config_hash": self.verifier_config_hash,
            "code_commit": self.code_commit,
            "created_at": self.created_at,
            "network_allowed": self.network_allowed,
            "redaction_status": self.redaction_status,
        }


def refine_rule_with_feedback(
    *,
    initial_planner_result: LLMPlannerResult,
    evidence: RelationEvidencePack,
    registry: RuleSchemaRegistry,
    provider: LLMProvider,
    normal_dataset: VerificationDataset,
    validation_dataset: VerificationDataset,
    verifier_config: VerificationConfig,
    policy: RefinementPolicy,
    provider_config: ProviderConfig | None = None,
    planner_config: PlannerConfig | None = None,
    prompt_template: PromptTemplate | None = None,
    existing_rules: Sequence[RuleAst] = (),
    code_commit: str | None = None,
    created_at: str = "unspecified",
) -> RefinementSessionResult:
    """Refine a candidate rule with structured verifier feedback only."""

    provider_cfg = provider_config or ProviderConfig()
    planner_cfg = planner_config or PlannerConfig()
    provider_config_hash = provider_cfg.config_hash

    if initial_planner_result.status != "planned" or initial_planner_result.rule is None:
        return _session(
            status="rejected",
            stop_reason="initial_planner_not_planned",
            policy=policy,
            provider_config_hash=provider_config_hash,
            planner_config_hash=initial_planner_result.planner_config_hash,
            verifier_config_hash=verifier_config.config_hash,
            initial_planner_result=initial_planner_result,
            initial_verification_report=None,
            final_rule=None,
            final_verification_report=None,
            iterations=(),
            code_commit=code_commit,
            created_at=created_at,
        )

    current_rule = initial_planner_result.rule
    current_report = verify_rule(
        current_rule,
        registry=registry,
        normal_dataset=normal_dataset,
        validation_dataset=validation_dataset,
        existing_rules=existing_rules,
        config=verifier_config,
    )
    if current_report.status == "passed":
        return _session(
            status="verified",
            stop_reason="verifier_passed",
            policy=policy,
            provider_config_hash=provider_config_hash,
            planner_config_hash=initial_planner_result.planner_config_hash,
            verifier_config_hash=verifier_config.config_hash,
            initial_planner_result=initial_planner_result,
            initial_verification_report=current_report,
            final_rule=current_rule,
            final_verification_report=current_report,
            iterations=(),
            code_commit=code_commit,
            created_at=created_at,
        )

    if _has_non_recoverable_feedback(current_report.issues):
        return _session(
            status="rejected",
            stop_reason="non_recoverable_feedback",
            policy=policy,
            provider_config_hash=provider_config_hash,
            planner_config_hash=initial_planner_result.planner_config_hash,
            verifier_config_hash=verifier_config.config_hash,
            initial_planner_result=initial_planner_result,
            initial_verification_report=current_report,
            final_rule=current_rule,
            final_verification_report=current_report,
            iterations=(),
            code_commit=code_commit,
            created_at=created_at,
        )

    seen_rule_hashes = {current_rule.deterministic_id}
    iterations: list[RefinementIteration] = []
    provider_failures = 0
    previous_issue_score = _issue_score(current_report)
    planner_config_hash = initial_planner_result.planner_config_hash

    for iteration_index in range(policy.max_iterations):
        previous_rule_hash = current_rule.deterministic_id
        feedback_ids = (current_report.report_id,)
        feedback_codes = tuple(issue.code for issue in current_report.issues)
        planner_result = plan_rule_with_provider(
            evidence=evidence,
            registry=registry,
            provider=provider,
            provider_config=provider_cfg,
            planner_config=planner_cfg,
            prompt_template=prompt_template,
            verifier_feedback_ids=feedback_ids,
            prompt_extras={"verifier_feedback": _feedback_prompt_summary(current_report)},
            code_commit=code_commit,
            created_at=created_at,
        )
        planner_config_hash = planner_result.planner_config_hash

        if planner_result.status == "provider_error":
            provider_failures += 1
            stop_reason = "provider_failure_limit" if provider_failures >= policy.provider_failure_limit else None
            iterations.append(
                _iteration(
                    iteration_index=iteration_index,
                    previous_rule_hash=previous_rule_hash,
                    feedback_ids=feedback_ids,
                    feedback_codes=feedback_codes,
                    planner_result=planner_result,
                    verification_report=None,
                    stop_reason=stop_reason,
                )
            )
            if stop_reason is not None:
                return _session(
                    status="provider_error",
                    stop_reason=stop_reason,
                    policy=policy,
                    provider_config_hash=provider_config_hash,
                    planner_config_hash=planner_config_hash,
                    verifier_config_hash=verifier_config.config_hash,
                    initial_planner_result=initial_planner_result,
                    initial_verification_report=current_report,
                    final_rule=current_rule,
                    final_verification_report=current_report,
                    iterations=tuple(iterations),
                    code_commit=code_commit,
                    created_at=created_at,
                )
            continue

        if planner_result.status != "planned" or planner_result.rule is None:
            iterations.append(
                _iteration(
                    iteration_index=iteration_index,
                    previous_rule_hash=previous_rule_hash,
                    feedback_ids=feedback_ids,
                    feedback_codes=feedback_codes,
                    planner_result=planner_result,
                    verification_report=None,
                    stop_reason="schema_validation_failed",
                )
            )
            return _session(
                status="rejected",
                stop_reason="schema_validation_failed",
                policy=policy,
                provider_config_hash=provider_config_hash,
                planner_config_hash=planner_config_hash,
                verifier_config_hash=verifier_config.config_hash,
                initial_planner_result=initial_planner_result,
                initial_verification_report=current_report,
                final_rule=current_rule,
                final_verification_report=current_report,
                iterations=tuple(iterations),
                code_commit=code_commit,
                created_at=created_at,
            )

        revised_rule = planner_result.rule
        revised_rule_hash = revised_rule.deterministic_id
        if policy.stop_on_repeated_rule and revised_rule_hash in seen_rule_hashes:
            iterations.append(
                _iteration(
                    iteration_index=iteration_index,
                    previous_rule_hash=previous_rule_hash,
                    feedback_ids=feedback_ids,
                    feedback_codes=feedback_codes,
                    planner_result=planner_result,
                    verification_report=None,
                    stop_reason="repeated_rule",
                )
            )
            return _session(
                status="rejected",
                stop_reason="repeated_rule",
                policy=policy,
                provider_config_hash=provider_config_hash,
                planner_config_hash=planner_config_hash,
                verifier_config_hash=verifier_config.config_hash,
                initial_planner_result=initial_planner_result,
                initial_verification_report=current_report,
                final_rule=current_rule,
                final_verification_report=current_report,
                iterations=tuple(iterations),
                code_commit=code_commit,
                created_at=created_at,
            )

        revised_report = verify_rule(
            revised_rule,
            registry=registry,
            normal_dataset=normal_dataset,
            validation_dataset=validation_dataset,
            existing_rules=existing_rules,
            config=verifier_config,
        )
        if revised_report.status == "passed":
            iterations.append(
                _iteration(
                    iteration_index=iteration_index,
                    previous_rule_hash=previous_rule_hash,
                    feedback_ids=feedback_ids,
                    feedback_codes=feedback_codes,
                    planner_result=planner_result,
                    verification_report=revised_report,
                    stop_reason="verifier_passed",
                )
            )
            return _session(
                status="verified",
                stop_reason="verifier_passed",
                policy=policy,
                provider_config_hash=provider_config_hash,
                planner_config_hash=planner_config_hash,
                verifier_config_hash=verifier_config.config_hash,
                initial_planner_result=initial_planner_result,
                initial_verification_report=current_report,
                final_rule=revised_rule,
                final_verification_report=revised_report,
                iterations=tuple(iterations),
                code_commit=code_commit,
                created_at=created_at,
            )

        stop_reason = _failed_iteration_stop_reason(
            current_report=current_report,
            revised_report=revised_report,
            previous_issue_score=previous_issue_score,
            policy=policy,
            iteration_index=iteration_index,
        )
        iterations.append(
            _iteration(
                iteration_index=iteration_index,
                previous_rule_hash=previous_rule_hash,
                feedback_ids=feedback_ids,
                feedback_codes=feedback_codes,
                planner_result=planner_result,
                verification_report=revised_report,
                stop_reason=stop_reason,
            )
        )
        if stop_reason is not None:
            return _session(
                status="rejected",
                stop_reason=stop_reason,
                policy=policy,
                provider_config_hash=provider_config_hash,
                planner_config_hash=planner_config_hash,
                verifier_config_hash=verifier_config.config_hash,
                initial_planner_result=initial_planner_result,
                initial_verification_report=current_report,
                final_rule=revised_rule,
                final_verification_report=revised_report,
                iterations=tuple(iterations),
                code_commit=code_commit,
                created_at=created_at,
            )

        seen_rule_hashes.add(revised_rule_hash)
        current_rule = revised_rule
        current_report = revised_report
        previous_issue_score = _issue_score(current_report)

    return _session(
        status="rejected",
        stop_reason="max_iterations_exhausted",
        policy=policy,
        provider_config_hash=provider_config_hash,
        planner_config_hash=planner_config_hash,
        verifier_config_hash=verifier_config.config_hash,
        initial_planner_result=initial_planner_result,
        initial_verification_report=current_report,
        final_rule=current_rule,
        final_verification_report=current_report,
        iterations=tuple(iterations),
        code_commit=code_commit,
        created_at=created_at,
    )


def _session(
    *,
    status: str,
    stop_reason: str,
    policy: RefinementPolicy,
    provider_config_hash: str,
    planner_config_hash: str,
    verifier_config_hash: str,
    initial_planner_result: LLMPlannerResult,
    initial_verification_report: VerificationReport | None,
    final_rule: RuleAst | None,
    final_verification_report: VerificationReport | None,
    iterations: tuple[RefinementIteration, ...],
    code_commit: str | None,
    created_at: str,
) -> RefinementSessionResult:
    return RefinementSessionResult(
        status=status,
        stop_reason=stop_reason,
        max_iterations=policy.max_iterations,
        iterations=iterations,
        initial_planner_result=initial_planner_result,
        initial_verification_report=initial_verification_report,
        final_rule=final_rule,
        final_verification_report=final_verification_report,
        policy_hash=policy.config_hash,
        provider_config_hash=provider_config_hash,
        planner_config_hash=planner_config_hash,
        verifier_config_hash=verifier_config_hash,
        code_commit=code_commit,
        created_at=created_at,
    )


def _iteration(
    *,
    iteration_index: int,
    previous_rule_hash: str,
    feedback_ids: tuple[str, ...],
    feedback_codes: tuple[str, ...],
    planner_result: LLMPlannerResult,
    verification_report: VerificationReport | None,
    stop_reason: str | None,
) -> RefinementIteration:
    return RefinementIteration(
        iteration_index=iteration_index,
        previous_rule_hash=previous_rule_hash,
        verifier_feedback_ids=feedback_ids,
        feedback_codes=feedback_codes,
        revised_rule_hash=planner_result.rule.deterministic_id if planner_result.rule else None,
        parse_status=planner_result.parse_status,
        schema_validation_status="passed" if planner_result.status == "planned" else "failed",
        verification_status=verification_report.status if verification_report else "not_run",
        stop_reason=stop_reason,
        planner_result=planner_result,
        verification_report=verification_report,
    )


def _feedback_prompt_summary(report: VerificationReport) -> dict[str, Any]:
    return {
        "report_id": report.report_id,
        "rule_id": report.rule_id,
        "status": report.status,
        "feedback_codes": [issue.code for issue in report.issues],
        "issues": [_feedback_issue_summary(issue) for issue in report.issues],
    }


def _feedback_issue_summary(issue: FeedbackIssue) -> dict[str, Any]:
    return {
        "code": issue.code,
        "suggested_action": issue.suggested_action,
        "path": issue.path,
        "observed": issue.observed,
        "limit": issue.limit,
        "duplicate_rule_id": issue.duplicate_rule_id,
    }


def _has_non_recoverable_feedback(issues: Sequence[FeedbackIssue]) -> bool:
    return any(issue.code not in RECOVERABLE_FEEDBACK_CODES for issue in issues)


def _issue_score(report: VerificationReport) -> tuple[int, tuple[str, ...]]:
    return (len(report.issues), tuple(sorted(issue.code for issue in report.issues)))


def _failed_iteration_stop_reason(
    *,
    current_report: VerificationReport,
    revised_report: VerificationReport,
    previous_issue_score: tuple[int, tuple[str, ...]],
    policy: RefinementPolicy,
    iteration_index: int,
) -> str | None:
    if _has_non_recoverable_feedback(revised_report.issues):
        return "non_recoverable_feedback"
    if policy.stop_on_no_improvement and _issue_score(revised_report) >= previous_issue_score:
        return "no_improvement"
    if iteration_index + 1 >= policy.max_iterations:
        return "max_iterations_exhausted"
    if current_report.report_id == revised_report.report_id and policy.stop_on_no_improvement:
        return "no_improvement"
    return None
