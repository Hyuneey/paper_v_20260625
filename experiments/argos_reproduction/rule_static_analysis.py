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
    threshold_names = (
        "threshold",
        "boundary",
        "limit",
        "cutoff",
        "scale",
        "deviation",
        "mad",
        "baseline",
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for item in [node.left, *node.comparators]:
                values.extend(_numeric_constants(item))
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(
                isinstance(target, ast.Name)
                and any(word in target.id.lower() for word in threshold_names)
                for target in targets
            ):
                values.extend(_numeric_constants(node.value))
    return values


def redacted_expression(node: ast.AST | None) -> dict[str, Any] | None:
    """Return structured AST semantics without reproducing source text."""

    if node is None:
        return None
    if isinstance(node, ast.Name):
        return {"node": "Name", "id": node.id}
    if isinstance(node, ast.Constant):
        value: Any = node.value
        if isinstance(value, str):
            value = "<string>"
        return {"node": "Constant", "value": value, "value_type": type(node.value).__name__}
    if isinstance(node, ast.Attribute):
        return {
            "node": "Attribute",
            "value": redacted_expression(node.value),
            "attr": node.attr,
        }
    if isinstance(node, ast.Subscript):
        return {
            "node": "Subscript",
            "value": redacted_expression(node.value),
            "slice": redacted_expression(node.slice),
        }
    if isinstance(node, ast.Slice):
        return {
            "node": "Slice",
            "lower": redacted_expression(node.lower),
            "upper": redacted_expression(node.upper),
            "step": redacted_expression(node.step),
        }
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        return {
            "node": type(node).__name__,
            "elements": [redacted_expression(item) for item in node.elts],
        }
    if isinstance(node, ast.Dict):
        return {
            "node": "Dict",
            "keys": [redacted_expression(item) for item in node.keys],
            "values": [redacted_expression(item) for item in node.values],
        }
    if isinstance(node, ast.Call):
        return {
            "node": "Call",
            "function": _call_name(node.func) or type(node.func).__name__,
            "args": [redacted_expression(item) for item in node.args],
            "keywords": [
                {"name": item.arg or "<expanded>", "value": redacted_expression(item.value)}
                for item in node.keywords
            ],
        }
    if isinstance(node, ast.BinOp):
        return {
            "node": "BinOp",
            "operator": type(node.op).__name__,
            "left": redacted_expression(node.left),
            "right": redacted_expression(node.right),
        }
    if isinstance(node, ast.UnaryOp):
        return {
            "node": "UnaryOp",
            "operator": type(node.op).__name__,
            "operand": redacted_expression(node.operand),
        }
    if isinstance(node, ast.BoolOp):
        return {
            "node": "BoolOp",
            "operator": type(node.op).__name__,
            "values": [redacted_expression(item) for item in node.values],
        }
    if isinstance(node, ast.Compare):
        return {
            "node": "Compare",
            "left": redacted_expression(node.left),
            "operators": [type(item).__name__ for item in node.ops],
            "comparators": [redacted_expression(item) for item in node.comparators],
        }
    if isinstance(node, ast.IfExp):
        return {
            "node": "IfExp",
            "test": redacted_expression(node.test),
            "body": redacted_expression(node.body),
            "orelse": redacted_expression(node.orelse),
        }
    if isinstance(node, ast.Starred):
        return {"node": "Starred", "value": redacted_expression(node.value)}
    return {"node": type(node).__name__}


def _target_descriptor(node: ast.AST) -> dict[str, Any]:
    return redacted_expression(node) or {"node": type(node).__name__}


def _parent_map(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    return {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}


def _nearest_context(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> ast.AST | None:
    current = parents.get(node)
    context_types = (
        ast.Assign,
        ast.AnnAssign,
        ast.AugAssign,
        ast.Compare,
        ast.Call,
        ast.Subscript,
        ast.For,
        ast.While,
        ast.If,
    )
    while current is not None:
        if isinstance(current, context_types):
            return current
        current = parents.get(current)
    return None


def _numeric_constants_with_context(tree: ast.AST) -> list[dict[str, Any]]:
    parents = _parent_map(tree)
    records: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.Constant)
            and isinstance(node.value, (int, float))
            and not isinstance(node.value, bool)
        ):
            continue
        context = _nearest_context(node, parents)
        record: dict[str, Any] = {
            "value": node.value,
            "value_type": type(node.value).__name__,
            "context_node": type(context).__name__ if context else "Module",
        }
        if isinstance(context, ast.Assign):
            record["assignment_targets"] = [_target_descriptor(item) for item in context.targets]
        elif isinstance(context, ast.AnnAssign):
            record["assignment_targets"] = [_target_descriptor(context.target)]
        elif isinstance(context, ast.Call):
            record["call"] = _call_name(context.func)
        elif isinstance(context, ast.Compare):
            record["comparison_operators"] = [type(item).__name__ for item in context.ops]
        records.append(record)
    return records


def _assignment_records(tree: ast.AST) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            records.append(
                {
                    "assignment_type": "Assign",
                    "targets": [_target_descriptor(item) for item in node.targets],
                    "expression": redacted_expression(node.value),
                }
            )
        elif isinstance(node, ast.AnnAssign):
            records.append(
                {
                    "assignment_type": "AnnAssign",
                    "targets": [_target_descriptor(node.target)],
                    "expression": redacted_expression(node.value),
                }
            )
        elif isinstance(node, ast.AugAssign):
            records.append(
                {
                    "assignment_type": "AugAssign",
                    "targets": [_target_descriptor(node.target)],
                    "operator": type(node.op).__name__,
                    "expression": redacted_expression(node.value),
                }
            )
    return records


def _comparison_records(tree: ast.AST) -> list[dict[str, Any]]:
    return [
        {
            "operators": [type(item).__name__ for item in node.ops],
            "expression": redacted_expression(node),
        }
        for node in ast.walk(tree)
        if isinstance(node, ast.Compare)
    ]


def _name_targets(node: ast.Assign | ast.AnnAssign) -> list[str]:
    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
    return [item.id for item in targets if isinstance(item, ast.Name)]


def _derived_threshold_records(tree: ast.AST) -> list[dict[str, Any]]:
    keywords = (
        "threshold",
        "boundary",
        "limit",
        "cutoff",
        "scale",
        "deviation",
        "mad",
        "baseline",
    )
    records: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            names = _name_targets(node)
            if names and any(any(word in name.lower() for word in keywords) for name in names):
                records.append(
                    {
                        "kind": "named_threshold_dependency",
                        "targets": names,
                        "expression": redacted_expression(node.value),
                    }
                )
        elif isinstance(node, ast.Compare):
            for comparator in node.comparators:
                if isinstance(comparator, (ast.Call, ast.BinOp, ast.Name, ast.Attribute, ast.Subscript)):
                    records.append(
                        {
                            "kind": "comparison_boundary",
                            "operators": [type(item).__name__ for item in node.ops],
                            "expression": redacted_expression(comparator),
                        }
                    )
    return records


def _subscript_records(tree: ast.AST) -> list[dict[str, Any]]:
    return [
        {
            "base": redacted_expression(node.value),
            "slice": redacted_expression(node.slice),
        }
        for node in ast.walk(tree)
        if isinstance(node, ast.Subscript)
    ]


def _source_names(node: ast.AST) -> list[str]:
    return sorted({item.id for item in ast.walk(node) if isinstance(item, ast.Name)})


def _loop_bound_records(tree: ast.AST) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.For):
            records.append(
                {
                    "loop_type": "For",
                    "target": _target_descriptor(node.target),
                    "iterator": redacted_expression(node.iter),
                    "source_names": _source_names(node.iter),
                }
            )
        elif isinstance(node, ast.While):
            records.append(
                {
                    "loop_type": "While",
                    "condition": redacted_expression(node.test),
                    "source_names": _source_names(node.test),
                }
            )
    return records


def _is_safe_module_constant(node: ast.AST) -> bool:
    if isinstance(node, ast.Assign):
        return all(isinstance(target, ast.Name) for target in node.targets) and isinstance(node.value, ast.Constant)
    if isinstance(node, ast.AnnAssign):
        return isinstance(node.target, ast.Name) and isinstance(node.value, ast.Constant)
    return False


def _top_level_executable_records(tree: ast.Module) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if _is_safe_module_constant(node):
            continue
        records.append({"statement_type": type(node).__name__})
    return records


def _global_state_mutation_records(tree: ast.Module) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)) and not _is_safe_module_constant(node):
            records.append({"mutation_type": type(node).__name__, "scope": "module"})
    for node in ast.walk(tree):
        if isinstance(node, (ast.Global, ast.Nonlocal)):
            records.append(
                {
                    "mutation_type": type(node).__name__,
                    "scope": "function",
                    "names": sorted(node.names),
                }
            )
    return records


def _import_aliases(tree: ast.AST) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for item in node.names:
                aliases[item.asname or item.name] = item.name
        elif isinstance(node, ast.ImportFrom):
            for item in node.names:
                aliases[item.asname or item.name] = f"{node.module}.{item.name}" if node.module else item.name
    return aliases


def normalize_dotted_name(name: str, aliases: dict[str, str]) -> str:
    first, separator, remainder = name.partition(".")
    normalized = aliases.get(first, first)
    return f"{normalized}.{remainder}" if separator else normalized


def analyze_code_semantics(tree: ast.Module) -> dict[str, Any]:
    aliases = _import_aliases(tree)
    calls = sorted(
        {
            normalize_dotted_name(_call_name(node.func), aliases)
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and _call_name(node.func)
        }
    )
    attributes = sorted(
        {
            normalize_dotted_name(_call_name(node), aliases)
            for node in ast.walk(tree)
            if isinstance(node, ast.Attribute) and _call_name(node)
        }
    )
    dunder = sorted(
        {
            normalize_dotted_name(_call_name(node), aliases)
            for node in ast.walk(tree)
            if isinstance(node, ast.Attribute) and node.attr.startswith("__") and node.attr.endswith("__")
        }
    )
    dynamic_names = {"getattr", "setattr", "delattr", "vars", "globals", "locals", "__getattribute__"}
    dynamic = sorted(
        {
            normalize_dotted_name(_call_name(node.func), aliases)
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and _call_name(node.func).split(".")[-1] in dynamic_names
        }
    )
    return {
        "numeric_constants_with_context": _numeric_constants_with_context(tree),
        "assignments_with_redacted_expression": _assignment_records(tree),
        "comparisons_with_redacted_expression": _comparison_records(tree),
        "derived_threshold_expressions": _derived_threshold_records(tree),
        "subscript_patterns": _subscript_records(tree),
        "loop_bound_sources": _loop_bound_records(tree),
        "top_level_executable_statements": _top_level_executable_records(tree),
        "global_state_mutations": _global_state_mutation_records(tree),
        "dunder_attribute_access": dunder,
        "dynamic_attribute_access": dynamic,
        "normalized_call_set": calls,
        "normalized_attribute_set": attributes,
    }


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
            "numeric_constants_with_context": [],
            "assignments_with_redacted_expression": [],
            "comparisons_with_redacted_expression": [],
            "derived_threshold_expressions": [],
            "subscript_patterns": [],
            "loop_bound_sources": [],
            "top_level_executable_statements": [],
            "global_state_mutations": [],
            "dunder_attribute_access": [],
            "dynamic_attribute_access": [],
            "normalized_call_set": [],
            "normalized_attribute_set": [],
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
    semantic_analysis = analyze_code_semantics(tree)

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
        **semantic_analysis,
        "execution_performed": False,
        "structural_diagnostics_only": True,
    }
