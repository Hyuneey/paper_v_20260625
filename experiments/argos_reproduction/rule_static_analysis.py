"""Static analysis for captured ARGOS Python rules.

The analysis in this module is structural only. It never imports or executes
captured rule code.
"""

from __future__ import annotations

import ast
import re
from collections import Counter
from typing import Any

from experiments.argos_reproduction import mock_harness


CODE_FENCE_RE = re.compile(r"```(?:python|py)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def count_code_fences(response_text: str) -> int:
    return len(CODE_FENCE_RE.findall(response_text))


def extract_first_code_fence(response_text: str) -> str:
    return mock_harness.extract_python_rule(response_text)


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _call_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def _comparison_operator_name(op: ast.cmpop) -> str:
    return type(op).__name__


def _numeric_constants(tree: ast.AST) -> list[float | int]:
    constants: list[float | int] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            constants.append(node.value)
    return constants


def _threshold_like_constants(tree: ast.AST) -> list[float | int]:
    values: list[float | int] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for item in [node.left, *node.comparators]:
                if isinstance(item, ast.Constant) and isinstance(item.value, (int, float)) and not isinstance(item.value, bool):
                    values.append(item.value)
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and any(word in target.id.lower() for word in ("threshold", "limit", "cutoff")):
                    if isinstance(node.value, ast.Constant) and isinstance(node.value.value, (int, float)):
                        values.append(node.value.value)
    return values


def _comment_flags(code: str) -> dict[str, bool]:
    lower_lines = [line.lower() for line in code.splitlines()]
    return {
        "normal_rule_comments_exist": any("normal rule" in line for line in lower_lines),
        "abnormal_rule_comments_exist": any("abnormal rule" in line for line in lower_lines),
    }


def _hardcoding_flags(tree: ast.AST, code: str) -> dict[str, bool]:
    suspicious_index_constants: list[int] = []
    suspicious_label_constants: list[int] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript):
            slice_node = node.slice
            if isinstance(slice_node, ast.Tuple):
                for element in slice_node.elts:
                    if isinstance(element, ast.Constant) and isinstance(element.value, int) and element.value not in {0, 1}:
                        suspicious_index_constants.append(element.value)
            elif isinstance(slice_node, ast.Constant) and isinstance(slice_node.value, int) and slice_node.value not in {0, 1}:
                suspicious_index_constants.append(slice_node.value)
        if isinstance(node, ast.Compare):
            text = ast.unparse(node).lower()
            if "label" in text:
                for value in _numeric_constants(node):
                    if value in {0, 1}:
                        suspicious_label_constants.append(int(value))
    lower_code = code.lower()
    return {
        "indices_or_labels_hardcoded_suspected": bool(suspicious_index_constants or suspicious_label_constants),
        "index_keyword_present": "index" in lower_code,
        "label_keyword_present": "label" in lower_code,
        "suspicious_index_constants": sorted(set(suspicious_index_constants)),
        "suspicious_label_constants": sorted(set(suspicious_label_constants)),
    }


def _cyclomatic_complexity_estimate(tree: ast.AST) -> int:
    complexity = 1
    branch_nodes = (
        ast.If,
        ast.For,
        ast.While,
        ast.Try,
        ast.ExceptHandler,
        ast.IfExp,
        ast.BoolOp,
        ast.comprehension,
        ast.Match,
    )
    for node in ast.walk(tree):
        if isinstance(node, branch_nodes):
            complexity += 1
    return complexity


def analyze_response(response_text: str, allowed_imports: set[str] | None = None) -> dict[str, Any]:
    allowed = allowed_imports or {"numpy"}
    code_fence_count = count_code_fences(response_text)
    code = ""
    code_extraction_status = "not_extracted"
    syntax_parse_status = "not_parsed"
    syntax_error = None
    tree: ast.Module | None = None
    try:
        code = extract_first_code_fence(response_text)
        code_extraction_status = "code_extracted"
        tree = ast.parse(code)
        syntax_parse_status = "parsed"
    except SyntaxError as exc:
        syntax_parse_status = "syntax_error"
        syntax_error = str(exc)
    except Exception as exc:
        syntax_error = str(exc)

    if tree is None:
        return {
            "code_fence_count": code_fence_count,
            "code_extraction_status": code_extraction_status,
            "source_code_line_count": len([line for line in code.splitlines() if line.strip()]),
            "inference_definition_count": 0,
            "syntax_parse_status": syntax_parse_status,
            "syntax_error": syntax_error,
            "required_signature_status": "not_available",
            "signature": {},
            "static_safety_passed": False,
            "imported_modules": [],
            "prohibited_calls": [],
            "function_calls": {},
            "condition_count": 0,
            "numeric_constant_count": 0,
            "comparison_operators_used": [],
            "threshold_like_numeric_constants": [],
            "normal_rule_comments_exist": False,
            "abnormal_rule_comments_exist": False,
            "indices_or_labels_hardcoded_suspected": False,
            "index_keyword_present": False,
            "label_keyword_present": False,
            "suspicious_index_constants": [],
            "suspicious_label_constants": [],
            "estimated_cyclomatic_complexity": 0,
            "execution_performed": False,
            "structural_diagnostics_only": True,
        }

    inference_defs = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "inference"]
    try:
        safety = mock_harness.static_safety_checks(code, allowed)
        required_signature_status = "valid" if safety["signature"]["signature_valid"] else "invalid"
        prohibited_calls = safety["violations"]
    except Exception as exc:
        safety = {"passed": False, "signature": {}, "violations": [str(exc)]}
        required_signature_status = "invalid"
        prohibited_calls = safety["violations"]

    imported_modules: list[str] = []
    comparison_operators: list[str] = []
    condition_count = 0
    calls: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_modules.append((node.module or "").split(".")[0])
        elif isinstance(node, (ast.If, ast.While, ast.BoolOp, ast.Compare)):
            condition_count += 1
        if isinstance(node, ast.Compare):
            comparison_operators.extend(_comparison_operator_name(op) for op in node.ops)
        elif isinstance(node, ast.Call):
            call_name = _call_name(node.func)
            if call_name:
                calls.append(call_name)

    numeric_constants = _numeric_constants(tree)
    threshold_like = _threshold_like_constants(tree)
    comment_flags = _comment_flags(code)
    hardcoding = _hardcoding_flags(tree, code)

    return {
        "code_fence_count": code_fence_count,
        "code_extraction_status": code_extraction_status,
        "source_code_line_count": len([line for line in code.splitlines() if line.strip()]),
        "inference_definition_count": len(inference_defs),
        "syntax_parse_status": syntax_parse_status,
        "syntax_error": syntax_error,
        "required_signature_status": required_signature_status,
        "signature": safety.get("signature", {}),
        "static_safety_passed": bool(safety.get("passed", False)),
        "imported_modules": sorted(set(imported_modules)),
        "prohibited_calls": prohibited_calls,
        "function_calls": dict(sorted(Counter(calls).items())),
        "condition_count": condition_count,
        "numeric_constant_count": len(numeric_constants),
        "comparison_operators_used": sorted(set(comparison_operators)),
        "threshold_like_numeric_constants": sorted(set(threshold_like)),
        "normal_rule_comments_exist": comment_flags["normal_rule_comments_exist"],
        "abnormal_rule_comments_exist": comment_flags["abnormal_rule_comments_exist"],
        "indices_or_labels_hardcoded_suspected": hardcoding["indices_or_labels_hardcoded_suspected"],
        "index_keyword_present": hardcoding["index_keyword_present"],
        "label_keyword_present": hardcoding["label_keyword_present"],
        "suspicious_index_constants": hardcoding["suspicious_index_constants"],
        "suspicious_label_constants": hardcoding["suspicious_label_constants"],
        "estimated_cyclomatic_complexity": _cyclomatic_complexity_estimate(tree),
        "execution_performed": False,
        "structural_diagnostics_only": True,
    }
