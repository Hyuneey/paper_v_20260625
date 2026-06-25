"""Mock-only provider-neutral schema-constrained LLM planner."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Protocol, Sequence

from paperworks.data.contracts import SCHEMA_VERSION, stable_hash
from paperworks.dsl import (
    CalibrationValueRef,
    ChangedToPredicate,
    IncreaseWithinPredicate,
    PlannerProvenance,
    ResponseMissingPredicate,
    RuleAst,
    RuleDslError,
    RuleSchemaRegistry,
    SchemaIssue,
    parse_rule_json,
)
from paperworks.dsl.rules import DSL_SCHEMA_VERSION, RULE_FAMILY
from paperworks.profiling import RelationEvidencePack


PROMPT_TEMPLATE_ID = "mock_rule_planner_v1"
ALLOWED_PREDICATES = ("changed_to", "increase_within", "response_missing")
FORBIDDEN_PROMPT_KEYS = ("raw", "row", "rows", "window", "windows", "series", "sequence", "test_label", "test_interval")
FORBIDDEN_PROMPT_TEXT = ("normal.csv", "attack.csv", "merged.csv", "timestamp,", "normal/attack")
TIMESTAMP_LIKE_RAW_RE = re.compile(
    r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}[ tT]\d{1,2}:\d{2}(?::\d{2})?(?:\.\d+)?\s*,"
)


class LLMPlanningError(ValueError):
    """Raised when mock-only planning inputs violate safety policy."""


class LLMProvider(Protocol):
    def generate_rule(self, request: "RulePlanningRequest") -> "RulePlanningResponse":
        """Return provider output for a schema-constrained rule request."""


@dataclass(frozen=True)
class ProviderConfig:
    provider_name: str = "mock"
    provider_type: str = "mock"
    model_or_deployment: str = "mock-llm-provider"
    api_version: str = "none"
    temperature: float = 0.0
    seed: int | None = 0
    seed_supported: bool = True
    allow_network: bool = False
    require_api_key: bool = False
    config_version: str = "1.0"

    def __post_init__(self) -> None:
        if self.provider_name != "mock" or self.provider_type != "mock":
            raise LLMPlanningError("TASK-012 only approves mock provider configuration")
        if self.allow_network:
            raise LLMPlanningError("network calls are prohibited for TASK-012")
        if self.require_api_key:
            raise LLMPlanningError("API keys are prohibited for TASK-012")
        if self.temperature != 0:
            raise LLMPlanningError("TASK-012 mock provider temperature must be 0")

    @property
    def config_hash(self) -> str:
        return stable_hash(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PlannerConfig:
    planner_name: str = "mock_rule_planner"
    planner_version: str = "1.0"
    store_full_prompt: bool = False
    store_full_raw_response: bool = False
    store_hashes: bool = True
    store_redacted_summaries: bool = True
    config_version: str = "1.0"

    def __post_init__(self) -> None:
        if self.store_full_prompt:
            raise LLMPlanningError("full prompt retention is prohibited by default")
        if self.store_full_raw_response:
            raise LLMPlanningError("full raw response retention is prohibited by default")
        if not self.store_hashes or not self.store_redacted_summaries:
            raise LLMPlanningError("TASK-012/TASK-013 require hashes and redacted summaries")

    @property
    def config_hash(self) -> str:
        return stable_hash(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PromptTemplate:
    template_id: str
    template_text: str
    schema_version: str = SCHEMA_VERSION

    @property
    def template_hash(self) -> str:
        return stable_hash({"template_id": self.template_id, "template_text": self.template_text})


@dataclass(frozen=True)
class RulePlanningRequest:
    provider_config: ProviderConfig
    planner_config_hash: str
    prompt_template_id: str
    prompt_template_hash: str
    prompt_text: str
    redacted_prompt_summary: Mapping[str, Any]
    evidence_hash: str
    dsl_schema_version: str
    allowed_rule_families: tuple[str, ...]
    allowed_predicates: tuple[str, ...]
    calibration_artifact_ids: tuple[str, ...]
    candidate_artifact_ids: tuple[str, ...]
    verifier_feedback_ids: tuple[str, ...] = ()

    @property
    def request_hash(self) -> str:
        return stable_hash(
            {
                "provider_config": self.provider_config.to_dict(),
                "planner_config_hash": self.planner_config_hash,
                "prompt_template_hash": self.prompt_template_hash,
                "prompt_text": self.prompt_text,
                "evidence_hash": self.evidence_hash,
                "allowed_rule_families": list(self.allowed_rule_families),
                "allowed_predicates": list(self.allowed_predicates),
                "calibration_artifact_ids": list(self.calibration_artifact_ids),
                "candidate_artifact_ids": list(self.candidate_artifact_ids),
                "verifier_feedback_ids": list(self.verifier_feedback_ids),
            }
        )

    def to_redacted_dict(self) -> dict[str, Any]:
        return {
            "provider_config": self.provider_config.to_dict(),
            "provider_config_hash": self.provider_config.config_hash,
            "planner_config_hash": self.planner_config_hash,
            "prompt_template_id": self.prompt_template_id,
            "prompt_template_hash": self.prompt_template_hash,
            "redacted_prompt_summary": dict(self.redacted_prompt_summary),
            "evidence_hash": self.evidence_hash,
            "request_hash": self.request_hash,
            "dsl_schema_version": self.dsl_schema_version,
            "allowed_rule_families": list(self.allowed_rule_families),
            "allowed_predicates": list(self.allowed_predicates),
            "calibration_artifact_ids": list(self.calibration_artifact_ids),
            "candidate_artifact_ids": list(self.candidate_artifact_ids),
            "verifier_feedback_ids": list(self.verifier_feedback_ids),
        }


@dataclass(frozen=True)
class RulePlanningResponse:
    provider_name: str
    model_or_deployment: str
    api_version: str
    raw_response_text: str
    response_metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def raw_response_hash(self) -> str:
        return stable_hash({"raw_response_text": self.raw_response_text})

    def to_redacted_dict(self) -> dict[str, Any]:
        return {
            "provider_name": self.provider_name,
            "model_or_deployment": self.model_or_deployment,
            "api_version": self.api_version,
            "raw_response_hash": self.raw_response_hash,
            "redacted_response_summary": _redacted_response_summary(self.raw_response_text),
            "response_metadata": dict(self.response_metadata),
        }


@dataclass(frozen=True)
class LLMPlannerResult:
    status: str
    rule: RuleAst | None
    issues: tuple[SchemaIssue, ...]
    provider_name: str
    provider_type: str
    model_or_deployment: str
    api_version: str
    temperature: float
    seed: int | None
    seed_supported: bool
    prompt_template_id: str
    prompt_template_hash: str
    evidence_hash: str
    request_hash: str
    raw_response_hash: str
    redaction_status: str
    parse_status: str
    dsl_schema_version: str
    allowed_rule_families: tuple[str, ...]
    allowed_predicates: tuple[str, ...]
    calibration_artifact_ids: tuple[str, ...]
    candidate_artifact_ids: tuple[str, ...]
    verifier_feedback_ids: tuple[str, ...]
    provider_config_hash: str
    planner_config_hash: str
    config_hash: str
    code_commit: str | None
    created_at: str
    network_allowed: bool = False
    redacted_prompt_summary: Mapping[str, Any] = field(default_factory=dict)
    redacted_response_summary: Mapping[str, Any] = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "llm_planner_result"

    def __post_init__(self) -> None:
        if self.status not in {"planned", "rejected", "provider_error"}:
            raise LLMPlanningError("unsupported planner result status")
        if self.network_allowed:
            raise LLMPlanningError("TASK-012 planner artifacts must record network_allowed=false")
        if self.status == "planned" and self.rule is None:
            raise LLMPlanningError("planned result requires a rule")

    @property
    def result_id(self) -> str:
        return stable_hash(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "status": self.status,
            "rule": self.rule.to_dict() if self.rule is not None else None,
            "issues": [issue.to_dict() for issue in self.issues],
            "provider_name": self.provider_name,
            "provider_type": self.provider_type,
            "model_or_deployment": self.model_or_deployment,
            "api_version": self.api_version,
            "temperature": self.temperature,
            "seed": self.seed,
            "seed_supported": self.seed_supported,
            "prompt_template_id": self.prompt_template_id,
            "prompt_template_hash": self.prompt_template_hash,
            "evidence_hash": self.evidence_hash,
            "request_hash": self.request_hash,
            "raw_response_hash": self.raw_response_hash,
            "redaction_status": self.redaction_status,
            "parse_status": self.parse_status,
            "dsl_schema_version": self.dsl_schema_version,
            "allowed_rule_families": list(self.allowed_rule_families),
            "allowed_predicates": list(self.allowed_predicates),
            "calibration_artifact_ids": list(self.calibration_artifact_ids),
            "candidate_artifact_ids": list(self.candidate_artifact_ids),
            "verifier_feedback_ids": list(self.verifier_feedback_ids),
            "provider_config_hash": self.provider_config_hash,
            "planner_config_hash": self.planner_config_hash,
            "config_hash": self.config_hash,
            "code_commit": self.code_commit,
            "created_at": self.created_at,
            "network_allowed": self.network_allowed,
            "redacted_prompt_summary": dict(self.redacted_prompt_summary),
            "redacted_response_summary": dict(self.redacted_response_summary),
        }


class MockLLMProvider:
    """Offline mock provider used by TASK-012 tests and CI."""

    def __init__(
        self,
        *,
        response_text: str | None = None,
        response_texts: Sequence[str] = (),
        raise_error: bool = False,
    ) -> None:
        self._response_text = response_text
        self._response_texts = tuple(response_texts)
        self._raise_error = raise_error
        self.calls = 0

    def generate_rule(self, request: RulePlanningRequest) -> RulePlanningResponse:
        call_index = self.calls
        self.calls += 1
        if self._raise_error:
            raise LLMPlanningError("mock provider error")
        if self._response_texts:
            response_text = self._response_texts[min(call_index, len(self._response_texts) - 1)]
        else:
            response_text = self._response_text or _default_mock_response(request)
        return RulePlanningResponse(
            provider_name=request.provider_config.provider_name,
            model_or_deployment=request.provider_config.model_or_deployment,
            api_version=request.provider_config.api_version,
            raw_response_text=response_text,
            response_metadata={"mock": True, "network_used": False},
        )


def default_prompt_template() -> PromptTemplate:
    return PromptTemplate(
        template_id=PROMPT_TEMPLATE_ID,
        template_text=(
            "You are a schema-constrained planner. Use only supplied variables, "
            "calibration references, predicates, and rule families. Return JSON only."
        ),
    )


def build_rule_planning_request(
    *,
    evidence: RelationEvidencePack,
    registry: RuleSchemaRegistry,
    provider_config: ProviderConfig | None = None,
    planner_config: PlannerConfig | None = None,
    prompt_template: PromptTemplate | None = None,
    verifier_feedback_ids: Sequence[str] = (),
    prompt_extras: Mapping[str, Any] | None = None,
) -> RulePlanningRequest:
    config = provider_config or ProviderConfig()
    planning_config = planner_config or PlannerConfig()
    template = prompt_template or default_prompt_template()
    source_meta = registry.metadata_for(evidence.source)
    target_meta = registry.metadata_for(evidence.target)
    allowed_families = registry.allowed_families(source_meta, target_meta)
    payload = {
        "source": evidence.source,
        "target": evidence.target,
        "source_metadata": source_meta.to_dict(),
        "target_metadata": target_meta.to_dict(),
        "relation_type": evidence.relation_type,
        "recommended_rule_family": evidence.recommended_rule_family,
        "allowed_rule_families": list(allowed_families),
        "allowed_predicates": list(ALLOWED_PREDICATES),
        "calibration_record_ids": dict(evidence.calibration_record_ids),
        "calibrated_parameters": dict(evidence.calibrated_parameters),
        "support_counts": dict(evidence.support_counts),
        "candidate_artifact_ids": list(evidence.upstream_artifact_ids),
        "verifier_feedback_ids": list(verifier_feedback_ids),
    }
    if prompt_extras:
        payload["prompt_extras"] = dict(prompt_extras)
    audit_prompt_payload(payload)
    prompt_text = _render_prompt(template, payload)
    audit_prompt_payload({"prompt_text": prompt_text})
    return RulePlanningRequest(
        provider_config=config,
        planner_config_hash=_planner_config_hash(
            planner_config=planning_config,
            prompt_template=template,
            allowed_predicates=ALLOWED_PREDICATES,
        ),
        prompt_template_id=template.template_id,
        prompt_template_hash=template.template_hash,
        prompt_text=prompt_text,
        redacted_prompt_summary=_redacted_prompt_summary(evidence, allowed_families, verifier_feedback_ids),
        evidence_hash=evidence.evidence_pack_id,
        dsl_schema_version=DSL_SCHEMA_VERSION,
        allowed_rule_families=tuple(allowed_families),
        allowed_predicates=ALLOWED_PREDICATES,
        calibration_artifact_ids=tuple(sorted(evidence.calibration_record_ids.values())),
        candidate_artifact_ids=tuple(evidence.upstream_artifact_ids),
        verifier_feedback_ids=tuple(verifier_feedback_ids),
    )


def plan_rule_with_provider(
    *,
    evidence: RelationEvidencePack,
    registry: RuleSchemaRegistry,
    provider: LLMProvider,
    provider_config: ProviderConfig | None = None,
    planner_config: PlannerConfig | None = None,
    prompt_template: PromptTemplate | None = None,
    verifier_feedback_ids: Sequence[str] = (),
    prompt_extras: Mapping[str, Any] | None = None,
    code_commit: str | None = None,
    created_at: str = "unspecified",
) -> LLMPlannerResult:
    request = build_rule_planning_request(
        evidence=evidence,
        registry=registry,
        provider_config=provider_config,
        planner_config=planner_config,
        prompt_template=prompt_template,
        verifier_feedback_ids=verifier_feedback_ids,
        prompt_extras=prompt_extras,
    )
    try:
        response = provider.generate_rule(request)
    except Exception as exc:
        return _result(
            status="provider_error",
            rule=None,
            issues=(SchemaIssue("PROVIDER_ERROR", str(exc), "provider"),),
            request=request,
            response=None,
            parse_status="provider_error",
            code_commit=code_commit,
            created_at=created_at,
        )

    try:
        rule = parse_rule_json(response.raw_response_text)
    except Exception as exc:
        return _result(
            status="rejected",
            rule=None,
            issues=(SchemaIssue("DSL_SCHEMA_INVALID", str(exc), "provider_response"),),
            request=request,
            response=response,
            parse_status="parse_failed",
            code_commit=code_commit,
            created_at=created_at,
        )

    issues = tuple(registry.validate(rule))
    if issues:
        return _result(
            status="rejected",
            rule=None,
            issues=issues,
            request=request,
            response=response,
            parse_status="parsed",
            code_commit=code_commit,
            created_at=created_at,
        )

    return _result(
        status="planned",
        rule=rule,
        issues=(),
        request=request,
        response=response,
        parse_status="parsed",
        code_commit=code_commit,
        created_at=created_at,
    )


def audit_prompt_payload(payload: Any) -> None:
    violations: list[str] = []
    _scan_payload(payload, "payload", violations)
    if violations:
        raise LLMPlanningError("prompt payload failed redaction audit: " + ", ".join(violations))


def _result(
    *,
    status: str,
    rule: RuleAst | None,
    issues: tuple[SchemaIssue, ...],
    request: RulePlanningRequest,
    response: RulePlanningResponse | None,
    parse_status: str,
    code_commit: str | None,
    created_at: str,
) -> LLMPlannerResult:
    redacted_response = response.to_redacted_dict() if response is not None else {
        "raw_response_hash": stable_hash({"raw_response_text": ""}),
        "redacted_response_summary": {},
    }
    return LLMPlannerResult(
        status=status,
        rule=rule,
        issues=issues,
        provider_name=request.provider_config.provider_name,
        provider_type=request.provider_config.provider_type,
        model_or_deployment=request.provider_config.model_or_deployment,
        api_version=request.provider_config.api_version,
        temperature=request.provider_config.temperature,
        seed=request.provider_config.seed,
        seed_supported=request.provider_config.seed_supported,
        prompt_template_id=request.prompt_template_id,
        prompt_template_hash=request.prompt_template_hash,
        evidence_hash=request.evidence_hash,
        request_hash=request.request_hash,
        raw_response_hash=str(redacted_response["raw_response_hash"]),
        redaction_status="passed",
        parse_status=parse_status,
        dsl_schema_version=request.dsl_schema_version,
        allowed_rule_families=request.allowed_rule_families,
        allowed_predicates=request.allowed_predicates,
        calibration_artifact_ids=request.calibration_artifact_ids,
        candidate_artifact_ids=request.candidate_artifact_ids,
        verifier_feedback_ids=request.verifier_feedback_ids,
        provider_config_hash=request.provider_config.config_hash,
        planner_config_hash=request.planner_config_hash,
        config_hash=stable_hash(
            {
                "provider_config_hash": request.provider_config.config_hash,
                "planner_config_hash": request.planner_config_hash,
            }
        ),
        code_commit=code_commit,
        created_at=created_at,
        network_allowed=request.provider_config.allow_network,
        redacted_prompt_summary=request.redacted_prompt_summary,
        redacted_response_summary=dict(redacted_response["redacted_response_summary"]),
    )


def _render_prompt(template: PromptTemplate, payload: Mapping[str, Any]) -> str:
    return template.template_text + "\n" + json.dumps(payload, sort_keys=True, ensure_ascii=True)


def _planner_config_hash(
    *,
    planner_config: PlannerConfig,
    prompt_template: PromptTemplate,
    allowed_predicates: Sequence[str],
) -> str:
    return stable_hash(
        {
            "planner_config": planner_config.to_dict(),
            "prompt_template_id": prompt_template.template_id,
            "prompt_template_hash": prompt_template.template_hash,
            "allowed_predicates": list(allowed_predicates),
            "dsl_schema_version": DSL_SCHEMA_VERSION,
        }
    )


def _default_mock_response(request: RulePlanningRequest) -> str:
    summary = request.redacted_prompt_summary
    source = str(summary["source"])
    target = str(summary["target"])
    calibration_ids = dict(summary["calibration_record_ids"])
    calibrated_parameters = dict(summary["calibrated_parameters"])
    max_delay_ref = CalibrationValueRef(
        parameter_name="max_response_delay_seconds",
        calibration_record_id=str(calibration_ids["max_response_delay_seconds"]),
        field_name="value",
        resolved_value=float(calibrated_parameters["max_response_delay_seconds"]),
        unit="seconds",
    )
    magnitude_ref = CalibrationValueRef(
        parameter_name="min_response_magnitude",
        calibration_record_id=str(calibration_ids["min_response_magnitude"]),
        field_name="value",
        resolved_value=float(calibrated_parameters["min_response_magnitude"]),
        unit="target_units",
    )
    expected = IncreaseWithinPredicate(variable=target, min_magnitude=magnitude_ref, max_delay_seconds=max_delay_ref)
    provisional = RuleAst(
        rule_id="rule.mock.pending",
        schema_version=DSL_SCHEMA_VERSION,
        source=source,
        target=target,
        relation_type=str(summary["relation_type"]),
        trigger_predicate=ChangedToPredicate(variable=source, from_state=0.0, to_state=1.0),
        response_predicate=ResponseMissingPredicate(expected_response=expected),
        calibration_references={
            "max_response_delay_seconds": max_delay_ref,
            "min_response_magnitude": magnitude_ref,
        },
        candidate_pair_artifact_id=str(summary["candidate_artifact_ids"][0]),
        metadata_artifact_id=str(summary["candidate_artifact_ids"][1]) if len(summary["candidate_artifact_ids"]) > 1 else stable_hash({"metadata": request.evidence_hash}),
        planner_provenance=PlannerProvenance(
            planner_type="llm_json_dsl",
            planner_version="mock-1.0",
            source_artifact_ids=tuple(str(item) for item in summary["candidate_artifact_ids"]),
        ),
        description_template="mock provider JSON DSL rule",
        rule_family=RULE_FAMILY,
    )
    rule_id = f"rule.mock.{provisional.deterministic_id[:16]}"
    return json.dumps({**provisional.to_dict(), "rule_id": rule_id}, sort_keys=True, separators=(",", ":"))


def _redacted_prompt_summary(
    evidence: RelationEvidencePack,
    allowed_families: Sequence[str],
    verifier_feedback_ids: Sequence[str],
) -> dict[str, Any]:
    return {
        "source": evidence.source,
        "target": evidence.target,
        "relation_type": evidence.relation_type,
        "recommended_rule_family": evidence.recommended_rule_family,
        "allowed_rule_families": list(allowed_families),
        "allowed_predicates": list(ALLOWED_PREDICATES),
        "calibration_record_ids": dict(evidence.calibration_record_ids),
        "calibrated_parameters": dict(evidence.calibrated_parameters),
        "support_counts": dict(evidence.support_counts),
        "candidate_artifact_ids": list(evidence.upstream_artifact_ids),
        "verifier_feedback_ids": list(verifier_feedback_ids),
    }


def _redacted_response_summary(raw_response_text: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw_response_text)
    except Exception:
        return {"json": False, "length": len(raw_response_text)}
    if not isinstance(payload, Mapping):
        return {"json": True, "object": False}
    return {
        "json": True,
        "object": True,
        "schema_version": payload.get("schema_version"),
        "rule_family": payload.get("rule_family"),
        "source": payload.get("source"),
        "target": payload.get("target"),
    }


def _scan_payload(value: Any, path: str, violations: list[str]) -> None:
    lowered_path = path.lower()
    if any(token in lowered_path for token in FORBIDDEN_PROMPT_KEYS):
        violations.append(path)
    if isinstance(value, str):
        lowered = value.lower()
        if any(token in lowered for token in FORBIDDEN_PROMPT_TEXT):
            violations.append(path)
        if TIMESTAMP_LIKE_RAW_RE.search(value):
            violations.append(path)
        if re.search(r"\[\s*-?\d+(?:\.\d+)?\s*,\s*-?\d+(?:\.\d+)?\s*,\s*-?\d+(?:\.\d+)?", value):
            violations.append(path)
    elif isinstance(value, Mapping):
        for key, item in value.items():
            _scan_payload(item, f"{path}.{key}", violations)
    elif isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        if len(value) >= 3 and all(isinstance(item, (int, float)) for item in value):
            violations.append(path)
        for index, item in enumerate(value):
            _scan_payload(item, f"{path}[{index}]", violations)
