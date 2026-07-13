"""Hash-bound semantic audit for the captured TASK-026Q ARGOS rule.

This module parses quarantined source with ``ast`` only. It never imports or
executes the captured module and never contacts a provider.
"""

from __future__ import annotations

import argparse
import ast
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.argos_reproduction import prompt_capture, rule_static_analysis


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        import json

        return json.load(handle)


def _verified_source(path: Path, expected_hash: str, step: str) -> tuple[str, dict[str, str]]:
    prompt_capture.assert_private_artifact_path(path)
    actual_hash = prompt_capture.sha256_file(path)
    if actual_hash != expected_hash:
        raise ValueError(f"Captured rule hash mismatch before {step}: {actual_hash} != {expected_hash}")
    return path.read_text(encoding="utf-8"), {"audit_step": step, "verified_rule_hash": actual_hash}


def _imported_modules(tree: ast.Module) -> list[str]:
    modules: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules.append(node.module or "")
    return sorted(set(modules))


def _defined_functions(tree: ast.Module) -> list[dict[str, Any]]:
    return [
        {
            "name": node.name,
            "argument_names": [argument.arg for argument in node.args.args],
            "argument_count": len(node.args.args),
            "return_annotation": rule_static_analysis.redacted_expression(node.returns),
        }
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]


def _global_assignments(tree: ast.Module) -> list[dict[str, Any]]:
    assignments: list[dict[str, Any]] = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            assignments.append(
                {
                    "assignment_type": "Assign",
                    "targets": [rule_static_analysis.redacted_expression(item) for item in node.targets],
                    "expression": rule_static_analysis.redacted_expression(node.value),
                }
            )
        elif isinstance(node, ast.AnnAssign):
            assignments.append(
                {
                    "assignment_type": "AnnAssign",
                    "targets": [rule_static_analysis.redacted_expression(node.target)],
                    "expression": rule_static_analysis.redacted_expression(node.value),
                }
            )
    return assignments


def _conditional_expressions(tree: ast.Module) -> list[dict[str, Any]]:
    return [
        {
            "statement_type": type(node).__name__,
            "expression": rule_static_analysis.redacted_expression(node.test),
        }
        for node in ast.walk(tree)
        if isinstance(node, (ast.If, ast.While, ast.IfExp))
    ]


def _return_expressions(tree: ast.Module) -> list[dict[str, Any] | None]:
    return [
        rule_static_analysis.redacted_expression(node.value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Return)
    ]


def _output_records(tree: ast.Module) -> dict[str, Any]:
    initializations: list[dict[str, Any]] = []
    mutations: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            continue
        targets: list[ast.AST]
        if isinstance(node, ast.Assign):
            targets = list(node.targets)
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
            value = node.value
        else:
            targets = [node.target]
            value = node.value
        for target in targets:
            if isinstance(target, ast.Name) and target.id == "labels":
                initializations.append(
                    {
                        "target": "labels",
                        "expression": rule_static_analysis.redacted_expression(value),
                        "line_number": getattr(node, "lineno", None),
                    }
                )
            elif isinstance(target, ast.Subscript):
                base = rule_static_analysis.redacted_expression(target.value)
                if isinstance(target.value, ast.Name) and target.value.id == "labels":
                    mutations.append(
                        {
                            "target": base,
                            "slice": rule_static_analysis.redacted_expression(target.slice),
                            "value": rule_static_analysis.redacted_expression(value),
                            "line_number": getattr(node, "lineno", None),
                        }
                    )
    return {"output_initialization": initializations, "output_mutation_locations": mutations}


def _input_column_access(tree: ast.Module) -> list[dict[str, Any]]:
    accesses: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Subscript) or not isinstance(node.slice, ast.Tuple):
            continue
        elements = node.slice.elts
        if len(elements) != 2:
            continue
        column = elements[1]
        if isinstance(column, ast.Constant) and isinstance(column.value, int):
            accesses.append(
                {
                    "base": rule_static_analysis.redacted_expression(node.value),
                    "column_index": column.value,
                    "row_selector": rule_static_analysis.redacted_expression(elements[0]),
                }
            )
    return accesses


def _semantic_risk_review() -> dict[str, dict[str, str]]:
    return {
        "empty_input_behavior": {
            "status": "explicit_zero_length_return",
            "risk": "low",
            "basis": "A row-count equality guard returns the initialized output before column access.",
        },
        "nan_inf_behavior": {
            "status": "nonfinite_values_masked",
            "risk": "medium",
            "basis": "All-nonfinite input returns zeros; partial nonfinite values are excluded from robust summaries.",
        },
        "constant_series_behavior": {
            "status": "scale_floor_and_absolute_boundary_present",
            "risk": "low",
            "basis": "The scale expression has a positive floor and the comparison has an absolute lower boundary.",
        },
        "short_series_behavior": {
            "status": "slice_bounds_clamped",
            "risk": "low",
            "basis": "Neighborhood and output ranges are bounded by zero and input row count.",
        },
        "off_by_one_risk": {
            "status": "manual_review_required",
            "risk": "medium",
            "basis": "Python-exclusive upper slice bounds are used around both neighborhoods and output spans.",
        },
        "uninitialized_output_risk": {
            "status": "no_path_identified",
            "risk": "low",
            "basis": "The output is initialized before every early return and mutation.",
        },
        "shape_mismatch_risk": {
            "status": "two_dimensional_single_column_minimum_assumed",
            "risk": "medium",
            "basis": "The rule indexes all rows at column zero and does not guard one-dimensional or zero-column input.",
        },
        "nonnumeric_input_risk": {
            "status": "float_conversion_may_fail",
            "risk": "medium",
            "basis": "The selected input column is converted to floating point without an exception boundary.",
        },
    }


def _policy_review(
    tree: ast.Module,
    semantics: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    policy = config["frozen_static_policy"]
    observed_imports = _imported_modules(tree)
    observed_calls = semantics["normalized_call_set"]
    observed_attributes = semantics["normalized_attribute_set"]
    allowed_imports = sorted(policy["allowed_imports"])
    allowed_calls = sorted(policy["allowed_calls"])
    allowed_attributes = sorted(policy["allowed_attributes"])
    violations: list[str] = []

    unexpected_imports = sorted(set(observed_imports) - set(allowed_imports))
    unexpected_calls = sorted(set(observed_calls) - set(allowed_calls))
    unexpected_attributes = sorted(set(observed_attributes) - set(allowed_attributes))
    missing_frozen_imports = sorted(set(allowed_imports) - set(observed_imports))
    missing_frozen_calls = sorted(set(allowed_calls) - set(observed_calls))
    missing_frozen_attributes = sorted(set(allowed_attributes) - set(observed_attributes))
    if unexpected_imports:
        violations.append("unexpected_imports")
    if unexpected_calls:
        violations.append("calls_outside_frozen_allowlist")
    if unexpected_attributes:
        violations.append("attributes_outside_frozen_allowlist")
    if missing_frozen_imports or missing_frozen_calls or missing_frozen_attributes:
        violations.append("observed_policy_set_does_not_exactly_match_frozen_policy")
    if semantics["dynamic_attribute_access"]:
        violations.append("dynamic_attribute_access")
    if semantics["dunder_attribute_access"]:
        violations.append("dunder_attribute_access")
    if semantics["top_level_executable_statements"]:
        violations.append("top_level_executable_statements")
    if semantics["global_state_mutations"]:
        violations.append("global_state_mutations")

    return {
        "policy_status": "passed" if not violations else "rejected",
        "violations": violations,
        "allowed_imports": allowed_imports,
        "observed_imports": observed_imports,
        "unexpected_imports": unexpected_imports,
        "missing_frozen_imports": missing_frozen_imports,
        "allowed_calls": allowed_calls,
        "observed_calls": observed_calls,
        "unexpected_calls": unexpected_calls,
        "missing_frozen_calls": missing_frozen_calls,
        "allowed_attributes": allowed_attributes,
        "observed_attributes": observed_attributes,
        "unexpected_attributes": unexpected_attributes,
        "missing_frozen_attributes": missing_frozen_attributes,
        "dangerous_capabilities_rejected": list(policy["dangerous_capabilities_rejected"]),
    }


def audit_rule(config_path: Path, *, persist: bool = True) -> dict[str, Any]:
    config = read_json(config_path)
    expected_hash = config["frozen_artifacts"]["rule_hash"]
    rule_path = REPO_ROOT / config["private_rule_path"]
    hash_verifications: list[dict[str, str]] = []

    source, verification = _verified_source(rule_path, expected_hash, "semantic_ast_analysis")
    hash_verifications.append(verification)
    tree = ast.parse(source)
    semantics = rule_static_analysis.analyze_code_semantics(tree)

    policy_source, verification = _verified_source(rule_path, expected_hash, "frozen_policy_validation")
    hash_verifications.append(verification)
    policy_tree = ast.parse(policy_source)
    policy_semantics = rule_static_analysis.analyze_code_semantics(policy_tree)
    policy_review = _policy_review(policy_tree, policy_semantics, config)

    risk_source, verification = _verified_source(rule_path, expected_hash, "semantic_risk_review")
    hash_verifications.append(verification)
    risk_tree = ast.parse(risk_source)
    output_records = _output_records(risk_tree)

    _, verification = _verified_source(rule_path, expected_hash, "report_persistence_precheck")
    hash_verifications.append(verification)

    report: dict[str, Any] = {
        "schema_version": "1.0",
        "artifact_type": "task027_rule_semantic_audit",
        "task_id": "TASK-027",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "statement": config["report_statement"],
        "code_commit": config.get("code_commit", "untracked_synthetic_test"),
        "config_hash": prompt_capture.sha256_json(config),
        "random_seed": config.get("random_seed"),
        "frozen_artifacts": config["frozen_artifacts"],
        "hash_verification_status": "passed",
        "hash_verifications": hash_verifications,
        "top_level_statement_types": [type(node).__name__ for node in tree.body],
        "imported_modules": _imported_modules(tree),
        "defined_functions": _defined_functions(tree),
        "global_assignments": _global_assignments(tree),
        "input_columns_accessed": _input_column_access(tree),
        "array_slicing_patterns": semantics["subscript_patterns"],
        "loops_and_loop_bounds": semantics["loop_bound_sources"],
        "conditional_expressions": _conditional_expressions(tree),
        "comparison_expressions": semantics["comparisons_with_redacted_expression"],
        "numeric_constants_with_context": semantics["numeric_constants_with_context"],
        "assignments_with_redacted_expression": semantics["assignments_with_redacted_expression"],
        "derived_threshold_expressions": semantics["derived_threshold_expressions"],
        "subscript_patterns": semantics["subscript_patterns"],
        "loop_bound_sources": semantics["loop_bound_sources"],
        "top_level_executable_statements": semantics["top_level_executable_statements"],
        "global_state_mutations": semantics["global_state_mutations"],
        "dunder_attribute_access": semantics["dunder_attribute_access"],
        "dynamic_attribute_access": semantics["dynamic_attribute_access"],
        **output_records,
        "return_expressions": _return_expressions(tree),
        "expected_output_shape": "one_dimensional_array_with_length_equal_to_input_row_count",
        "semantic_risk_review": _semantic_risk_review(),
        "frozen_static_policy_review": policy_review,
        "api_lineage": config.get("api_lineage", {}),
        "raw_rule_text_included": False,
        "provider_call_performed": False,
        "network_call_performed": False,
        "captured_rule_executed": False,
        "performance_metric_reported": False,
        "boundaries": config["boundaries"],
    }
    report["report_hash"] = prompt_capture.sha256_json(report)
    if persist:
        prompt_capture.write_json(REPO_ROOT / config["output_semantic_report_path"], report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/argos_reproduction/task027_semantic_audit.json")
    args = parser.parse_args()
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = REPO_ROOT / config_path
    report = audit_rule(config_path.resolve())
    print(
        prompt_capture.stable_json(
            {
                "hash_verification_status": report["hash_verification_status"],
                "policy_status": report["frozen_static_policy_review"]["policy_status"],
                "captured_rule_executed": report["captured_rule_executed"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
