"""Prospective EXP-03 reference-only construction contract; no I/O.

This adapter checks bounded construction against immutable Formal V4 fields.
It neither selects rules nor authorizes a dataset/runtime. Numeric values never
enter the provider view. Historical preparation contracts remain unchanged.
"""
from __future__ import annotations

from dataclasses import fields, replace
from decimal import Decimal
import json
from typing import Any

from . import exp03_construction_v1 as existing
from .formal_v4_authority_v1 import (
    FormalV4RuleDescriptorV1, NumericReferenceBindingV1,
    canonical_document_hash_v1, V4_NUMERIC_ROLES,
)

MODEL = "gpt-5.4-mini-2026-03-17"
ENDPOINT = "https://api.openai.com/v1/responses"
PORTFOLIO_HASH = "ec0b3e2a32d457287cb8b101bec39059e99335be3fd85a3d1fb98668224c52aa"
COHORT_HASH = "7bfb75e6559bd80af30c824439a73261212feb59d6d77ec334e48900bf1531f2"
INPUT_CAP, OUTPUT_CAP, CALL_CAP = 4096, 2048, 819
TOTAL_INPUT, TOTAL_OUTPUT, TOTAL_TOKENS = 3354624, 1677312, 5031936
USD_CAP = Decimal("10.07")
INPUT_RATE, OUTPUT_RATE = Decimal("0.75"), Decimal("4.50")
NO_RULE_REASONS = tuple(sorted(existing.INTENTIONAL_NO_RULE_REASON_CODES))
FIELDS = ("relation_id", "source", "target", "source_direction", "target_direction", "selected_horizon_seconds", "numeric_reference_ids")
PROMPT = (
    "Construct one bounded Formal V4 relational rule from the supplied frozen normal-only relation projection. "
    "Return only the strict JSON envelope. Use decision RULE with the exact relation identity, source, target, "
    "directions, horizon and all approved numeric reference IDs in their supplied order; reason must be null. "
    "Ordered numeric roles: " + ",".join(V4_NUMERIC_ROLES) + ". "
    "Never invent variables, numbers, references, code or causal claims. Numeric values remain local. "
    "The summary hash binds confirmed identity metadata, not statistics. If no safe construction is possible, use NO_RULE, "
    "a closed reason, and null in all rule fields. Do not infer missing numeric values. "
    "A feedback object, when present, contains only this proposal's deterministic verifier issue codes "
    "and a same-corpus reference slice; it grants no new evidence."
)


def h(value: dict[str, Any]) -> str:
    return canonical_document_hash_v1(value)


def schema() -> dict[str, Any]:
    properties: dict[str, Any] = {
        "decision": {"type": "string", "enum": ["RULE", "NO_RULE"]},
        "reason": {"type": ["string", "null"], "enum": [None, *NO_RULE_REASONS]},
    }
    for name in FIELDS:
        if name == "selected_horizon_seconds":
            properties[name] = {"type": ["integer", "null"]}
        elif name == "numeric_reference_ids":
            properties[name] = {"type": ["array", "null"], "items": {"type": "string"}}
        else:
            properties[name] = {"type": ["string", "null"]}
    return {"type": "object", "additionalProperties": False, "required": list(properties), "properties": properties}


def model_policy() -> dict[str, Any]:
    return {
        "model": MODEL, "endpoint": ENDPOINT, "reasoning": {"effort": "none"},
        "temperature": 0.7, "top_p": 1.0, "seed": None,
        "max_output_tokens": OUTPUT_CAP, "store": False,
        "service_tier": "default", "tools": [], "stream": False,
        "automatic_retries": 0, "timeout_seconds": 60,
        "concurrency": 1, "maximum_calls": CALL_CAP,
        "maximum_input_tokens": TOTAL_INPUT, "maximum_output_tokens": TOTAL_OUTPUT,
        "maximum_total_tokens": TOTAL_TOKENS, "maximum_usd": str(USD_CAP),
        "input_usd_per_million": str(INPUT_RATE), "output_usd_per_million": str(OUTPUT_RATE),
        "input_bound": "UTF8_BYTES_OF_COMPLETE_REQUEST_PLUS_512_SERVER_FRAMING_RESERVE",
        "uncertain_transport": "RETAIN_FULL_RESERVATION_AND_STOP_NO_RESEND",
    }


def validate_approval(value: dict[str, Any]) -> None:
    required = {
        "decision": "APPROVED_WITH_FIXED_SNAPSHOT", "provider": "OpenAI API", "model_snapshot": MODEL,
        "maximum_generation_calls": CALL_CAP, "maximum_input_tokens": TOTAL_INPUT,
        "maximum_output_tokens": TOTAL_OUTPUT, "maximum_total_tokens": TOTAL_TOKENS,
        "maximum_standard_api_usd": str(USD_CAP), "scientific_concurrency": 1,
        "moving_alias_allowed": False, "fallback_allowed": False, "t2_early_stop_on_accept": True,
        "fourth_call_allowed": False, "raw_rows_allowed": False, "private_numeric_payload_allowed": False,
        "labels_allowed": False, "test1_allowed": False, "test2_allowed": False, "heldout_allowed": False,
        "cross_arm_outcomes_allowed": False, "existing_scientific_results_mutable": False,
        "generation_requires_precommitted_full_contract_and_one_call_gate": True,
        "next_gate_after_completion": "DG-04",
        "provider_projection": "EXISTING_CLOSED_NORMAL_ONLY_REDACTED_PROJECTION",
    }
    if type(value) is not dict or any(type(value.get(k)) is not type(v) or value[k] != v for k, v in required.items()):
        raise ValueError("EXP03_USER_APPROVAL_SEMANTICS_MISMATCH")


def validate_projection_content(payload: dict[str, Any]) -> None:
    allowed = {"relation_id", "source_id", "target_id", "source_direction", "target_direction",
               "selected_horizon_seconds", "numeric_reference_ids", "normal_evidence_summary_hash"}
    if type(payload) is not dict or set(payload) != allowed:
        raise ValueError("CLOSED_PROJECTION_FIELDS")
    for key in ("relation_id", "source_id", "target_id"):
        existing._identifier(payload[key], key)
    if payload["source_id"] == payload["target_id"] or payload["source_direction"] not in {"step_up", "step_down"} or payload["target_direction"] not in {"increase", "decrease"}:
        raise ValueError("PROJECTION_RELATION")
    if type(payload["selected_horizon_seconds"]) is not int or payload["selected_horizon_seconds"] not in {1, 5, 10, 30, 60}:
        raise ValueError("PROJECTION_HORIZON")
    refs = payload["numeric_reference_ids"]
    if type(refs) is not list or len(refs) != 10 or len(set(refs)) != 10:
        raise ValueError("PROJECTION_REFERENCE_COUNT")
    for ref in refs:
        existing._identifier(ref, "numeric_reference_id")
    existing._hash(payload["normal_evidence_summary_hash"], "normal_evidence_summary_hash")


def descriptor_from_json(row: dict[str, Any]) -> FormalV4RuleDescriptorV1:
    kwargs = {field.name: row[field.name] for field in fields(FormalV4RuleDescriptorV1)}
    kwargs["numeric_reference_bindings"] = tuple(NumericReferenceBindingV1(**r) for r in kwargs["numeric_reference_bindings"])
    value = FormalV4RuleDescriptorV1(**kwargs)
    if value.to_dict() != row:
        raise ValueError("EXP03_DESCRIPTOR_REPLAY_MISMATCH")
    return value


def projection_payload(descriptor: FormalV4RuleDescriptorV1, confirmation_hash: str) -> dict[str, Any]:
    summary = {
        "schema": "exp03_public_normal_confirmation_summary_v1",
        "cohort_hash": COHORT_HASH, "confirmation_authority_hash": confirmation_hash,
        "relation_id": descriptor.relation_id, "relation_binding_hash": descriptor.relation_binding_hash,
        "source": descriptor.source, "target": descriptor.target,
        "source_direction": descriptor.source_direction, "target_direction": descriptor.target_direction,
        "selected_horizon_seconds": descriptor.selected_horizon_seconds,
        "kind": "FROZEN_CONFIRMED_IDENTITY_ONLY_NO_INVENTED_SUPPORT_STATISTICS",
    }
    return {
        "relation_id": descriptor.relation_id, "source_id": descriptor.source, "target_id": descriptor.target,
        "source_direction": descriptor.source_direction, "target_direction": descriptor.target_direction,
        "selected_horizon_seconds": descriptor.selected_horizon_seconds,
        "numeric_reference_ids": [b.reference_id for b in descriptor.numeric_reference_bindings],
        "normal_evidence_summary_hash": h(summary),
    }


def template_proposal(projection: dict[str, Any]) -> dict[str, Any]:
    return {"decision": "RULE", "reason": None, "relation_id": projection["relation_id"],
            "source": projection["source_id"], "target": projection["target_id"],
            **{key: projection[key] for key in FIELDS[3:]}}


def strict_parse(text: str) -> dict[str, Any]:
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("DUPLICATE_JSON_KEY")
            result[key] = value
        return result
    value = json.loads(text, object_pairs_hook=pairs, parse_constant=lambda _: (_ for _ in ()).throw(ValueError("NONFINITE_JSON")))
    if type(value) is not dict or set(value) != {"decision", "reason", *FIELDS}:
        raise ValueError("CLOSED_SCHEMA_MISMATCH")
    if value["decision"] == "NO_RULE":
        if value["reason"] not in NO_RULE_REASONS or any(value[key] is not None for key in FIELDS):
            raise ValueError("NO_RULE_SCHEMA_MISMATCH")
    elif value["decision"] == "RULE":
        if value["reason"] is not None:
            raise ValueError("RULE_REASON_MUST_BE_NULL")
        for key in FIELDS:
            expected = int if key == "selected_horizon_seconds" else list if key == "numeric_reference_ids" else str
            if type(value[key]) is not expected:
                raise ValueError("RULE_FIELD_TYPE_MISMATCH")
        if any(type(ref) is not str for ref in value["numeric_reference_ids"]):
            raise ValueError("REFERENCE_TYPE_MISMATCH")
    else:
        raise ValueError("UNKNOWN_DECISION")
    return value


def verify_proposal(value: dict[str, Any], descriptor: FormalV4RuleDescriptorV1) -> dict[str, Any]:
    """Never repair provider fields. Build V4 only from a matching actual proposal.

    This is exact bounded reference construction validity, not causal, utility,
    or canonical VerifierV1 acceptance. Local numeric replay is a separate gate.
    """
    value = strict_parse(json.dumps(value))
    issues = []
    if value["decision"] == "NO_RULE":
        return {"status": "INTENTIONAL_NO_RULE", "issues": [], "proposal_hash": h(value), "projection_hash": None}
    expected = {"relation_id": descriptor.relation_id, "source": descriptor.source, "target": descriptor.target,
                "source_direction": descriptor.source_direction, "target_direction": descriptor.target_direction,
                "selected_horizon_seconds": descriptor.selected_horizon_seconds,
                "numeric_reference_ids": [b.reference_id for b in descriptor.numeric_reference_bindings]}
    for key in FIELDS:
        if value[key] != expected[key]:
            issues.append("NUMERIC_REFERENCE_MISMATCH" if key == "numeric_reference_ids" else "RELATION_FIELD_MISMATCH:" + key)
    projection_hash = None
    if not issues:
        refs = {b.reference_id: b for b in descriptor.numeric_reference_bindings}
        constructed = replace(descriptor, **{k: value[k] for k in FIELDS if k != "numeric_reference_ids"},
                              numeric_reference_bindings=tuple(refs[ref] for ref in value["numeric_reference_ids"]))
        if constructed.to_dict() != descriptor.to_dict():
            raise ValueError("EXP03_FORMAL_V4_PROJECTION_MISMATCH")
        projection_hash = constructed.descriptor_hash
    return {"status": "VERIFIER_REJECTION" if issues else "ACCEPTED_PROPOSAL", "issues": issues,
            "proposal_hash": h(value), "projection_hash": projection_hash,
            "verifier": "EXP03_FORMAL_V4_EXACT_BOUND_CONSTRUCTION_VALIDITY_V1",
            "runtime_authority_granted": False}


def feedback_for(verdict: dict[str, Any], retrieved: bool, projection: dict[str, Any]) -> dict[str, Any]:
    if verdict["status"] != "VERIFIER_REJECTION" or not verdict["issues"]:
        raise ValueError("FEEDBACK_WITHOUT_REJECTION")
    # Foreign relation/variable is terminal. Only bounded in-relation reference
    # mismatches can be corrected. Pure reference issues retrieve at most once.
    if any(i.startswith("RELATION_FIELD_MISMATCH:") for i in verdict["issues"]):
        raise ValueError("NONREPAIRABLE_IDENTITY_REJECTION")
    if verdict["issues"] != ["NUMERIC_REFERENCE_MISMATCH"]:
        raise ValueError("UNKNOWN_OR_UNSUPPORTED_VERIFIER_ISSUE")
    action = "retrieve" if verdict["issues"] == ["NUMERIC_REFERENCE_MISMATCH"] and not retrieved else "revise"
    return {"action": action, "issue_codes": verdict["issues"],
            "same_corpus_numeric_reference_ids": projection["numeric_reference_ids"] if action == "retrieve" else []}


def request_document(projection: dict[str, Any], authorization: existing.ProviderExecutionAuthorizationV1,
                     feedback: dict[str, Any] | None = None) -> dict[str, Any]:
    existing.build_provider_input_projection_v1(projection, authorization)
    validate_projection_content(projection)
    # No arm, repetition, results, prior raw response, private values or paths.
    user: dict[str, Any] = {"relation": projection}
    if feedback is not None:
        if set(feedback) != {"action", "issue_codes", "same_corpus_numeric_reference_ids"}:
            raise ValueError("FEEDBACK_CLOSED_FIELDS")
        if feedback["action"] not in {"revise", "retrieve"}:
            raise ValueError("FEEDBACK_ACTION")
        allowed_issues = {"NUMERIC_REFERENCE_MISMATCH", *("RELATION_FIELD_MISMATCH:" + k for k in FIELDS)}
        if any(i not in allowed_issues for i in feedback["issue_codes"]):
            raise ValueError("FEEDBACK_CODE")
        if feedback["same_corpus_numeric_reference_ids"] not in ([], projection["numeric_reference_ids"]):
            raise ValueError("FOREIGN_RETRIEVAL")
        user["feedback"] = feedback
    return {
        "model": MODEL, "instructions": PROMPT, "input": json.dumps(user, sort_keys=True, separators=(",", ":"), ensure_ascii=True),
        "text": {"format": {"type": "json_schema", "name": "exp03_rule_v1", "strict": True, "schema": schema()}},
        "reasoning": {"effort": "none"}, "temperature": 0.7, "top_p": 1.0,
        "max_output_tokens": OUTPUT_CAP, "store": False, "service_tier": "default", "tools": [], "stream": False,
    }


def input_upper_bound(request: dict[str, Any]) -> int:
    # Tokenizer-independent conservative byte bound including schema, settings
    # and 512 additional server framing tokens. Actual usage must also pass.
    return len(json.dumps(request, separators=(",", ":"), ensure_ascii=True).encode("utf-8")) + 512


def cost(input_tokens: int, output_tokens: int) -> Decimal:
    if any(type(n) is not int or n < 0 for n in (input_tokens, output_tokens)):
        raise ValueError("INVALID_USAGE")
    return (INPUT_RATE * input_tokens + OUTPUT_RATE * output_tokens) / Decimal(1000000)


def budget_guard(calls: int, input_tokens: int, output_tokens: int, usd: Decimal) -> None:
    if any(type(n) is not int or n < 0 for n in (calls, input_tokens, output_tokens)):
        raise ValueError("INVALID_BALANCE")
    if (calls > CALL_CAP or input_tokens > TOTAL_INPUT or output_tokens > TOTAL_OUTPUT
            or input_tokens + output_tokens > TOTAL_TOKENS or not usd.is_finite() or usd > USD_CAP or usd < 0):
        raise ValueError("APPROVED_BUDGET_EXCEEDED")
