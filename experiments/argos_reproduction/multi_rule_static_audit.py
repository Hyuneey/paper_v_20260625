"""Static, non-executing audit for TASK-035A generated rule text."""

from __future__ import annotations

import ast
import hashlib
import re
import argparse
import json
from pathlib import Path
import sys
from typing import Any

REPO_ROOT_BOOTSTRAP = Path(__file__).resolve().parents[2]
if str(REPO_ROOT_BOOTSTRAP) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT_BOOTSTRAP))

from experiments.argos_reproduction.expanded_kpi_cohort import REPO_ROOT, read_json, sha256_json, write_json


PROHIBITED_NAMES = {"eval", "exec", "compile", "open", "getattr", "setattr", "delattr", "__import__", "input", "breakpoint"}
PROHIBITED_ROOTS = {"os", "sys", "subprocess", "socket", "pathlib", "requests", "urllib", "http", "shutil", "multiprocessing", "threading", "ctypes", "importlib", "runpy"}
PROHIBITED_NUMPY = {"load", "save", "savez", "fromfile", "tofile", "memmap", "loadtxt", "genfromtxt"}


def extract_python_fence(text: str) -> tuple[str | None, int]:
    matches = re.findall(r"```python\s*\n(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    return (matches[0].strip() + "\n" if len(matches) == 1 else None, len(matches))


def _call_name(node: ast.Call) -> str:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        parts: list[str] = [node.func.attr]
        value = node.func.value
        while isinstance(value, ast.Attribute):
            parts.append(value.attr); value = value.value
        if isinstance(value, ast.Name): parts.append(value.id)
        return ".".join(reversed(parts))
    return "<dynamic>"


def audit_response(response_text: str) -> tuple[dict[str, Any], str | None]:
    code, fence_count = extract_python_fence(response_text)
    result: dict[str, Any] = {
        "response_captured": bool(response_text), "response_sha256": hashlib.sha256(response_text.encode()).hexdigest(),
        "code_fence_count": fence_count, "rule_extracted": code is not None, "rule_sha256": None,
        "syntax_valid": False, "inference_definition_count": 0, "signature_valid": False,
        "allowed_imports_valid": False, "prohibited_calls_absent": False,
        "hardcoded_index_or_label_suspicion": False, "source_line_count": 0,
        "estimated_complexity": 0, "static_status": "static_invalid",
    }
    if code is None:
        return result, None
    result["rule_sha256"] = hashlib.sha256(code.encode()).hexdigest()
    result["source_line_count"] = len(code.splitlines())
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return result, code
    result["syntax_valid"] = True
    functions = [node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "inference"]
    result["inference_definition_count"] = len(functions)
    if len(functions) == 1:
        fn = functions[0]
        result["signature_valid"] = (
            not isinstance(fn, ast.AsyncFunctionDef) and len(fn.args.args) == 1 and fn.args.args[0].arg == "sample"
            and not fn.args.vararg and not fn.args.kwarg and not fn.args.kwonlyargs
        )
    imports_valid = True
    dangerous = False
    complexity = 1
    hardcoded = False
    top_level_valid = True
    for statement in tree.body:
        if not isinstance(statement, (ast.Import, ast.FunctionDef, ast.Assign, ast.AnnAssign)):
            top_level_valid = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports_valid &= all(alias.name == "numpy" for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports_valid = False
        elif isinstance(node, (ast.If, ast.For, ast.While, ast.Try, ast.BoolOp, ast.comprehension)):
            complexity += 1
        elif isinstance(node, ast.Attribute) and (node.attr.startswith("__") or (isinstance(node.value, ast.Name) and node.value.id in PROHIBITED_ROOTS)):
            dangerous = True
        elif isinstance(node, ast.Call):
            name = _call_name(node)
            root = name.split(".")[0]
            if name == "<dynamic>" or root in PROHIBITED_ROOTS or name in PROHIBITED_NAMES or name.split(".")[-1] in PROHIBITED_NAMES:
                dangerous = True
            if root in {"np", "numpy"} and name.split(".")[-1] in PROHIBITED_NUMPY:
                dangerous = True
        elif isinstance(node, ast.Return) and isinstance(node.value, (ast.List, ast.Tuple)) and len(node.value.elts) >= 2:
            hardcoded = all(isinstance(item, ast.Constant) and item.value in (0, 1) for item in node.value.elts)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and any(token in node.value.lower() for token in ("http://", "https://", "openai_api_key")):
            dangerous = True
    result["allowed_imports_valid"] = bool(imports_valid)
    result["prohibited_calls_absent"] = not dangerous
    result["hardcoded_index_or_label_suspicion"] = hardcoded
    result["estimated_complexity"] = complexity
    passed = all((result["syntax_valid"], result["inference_definition_count"] == 1, result["signature_valid"], imports_valid, top_level_valid, not dangerous, not hardcoded))
    result["static_status"] = "static_valid" if passed else "static_invalid"
    return result, code


def audit_all(config_path: Path) -> dict[str, Any]:
    config = read_json(config_path)
    provider = read_json(REPO_ROOT / config["reports"]["provider"])
    private_root = REPO_ROOT / config["private_root"]
    records: list[dict[str, Any]] = []
    for slot in provider["slots"]:
        base = {key: slot[key] for key in ("slot_id", "kpi_id", "anchor_id", "replicate_id")}
        if slot["capture_status"] != "provider_response_captured":
            records.append({**base, "static_status": "not_audited_no_response", "terminal_status": slot["capture_status"]})
            continue
        response_path = private_root / "responses" / slot["slot_id"] / "raw_response.md"
        response = response_path.read_text(encoding="utf-8")
        audit, code = audit_response(response)
        if code is not None:
            rule_path = private_root / "quarantine" / f"{audit['rule_sha256']}.py"
            rule_path.parent.mkdir(parents=True, exist_ok=True)
            if rule_path.exists() and rule_path.read_text(encoding="utf-8") != code:
                raise RuntimeError("TASK035A_RULE_HASH_COLLISION")
            rule_path.write_text(code, encoding="utf-8")
        private_audit = private_root / "static_audits" / f"{slot['slot_id']}.json"
        write_json(private_audit, audit)
        terminal = "response_without_rule" if not audit["rule_extracted"] else ("static_invalid" if audit["static_status"] != "static_valid" else "provider_response_captured")
        records.append({**base, **audit, "terminal_status": terminal})
    valid = [item for item in records if item.get("static_status") == "static_valid"]
    rule_groups: dict[str, list[str]] = {}
    for item in valid:
        rule_groups.setdefault(item["rule_sha256"], []).append(item["slot_id"])
    per_kpi: dict[str, dict[str, Any]] = {}
    for item in records:
        summary = per_kpi.setdefault(item["kpi_id"], {"responses": 0, "static_valid": 0, "rule_hashes": set()})
        summary["responses"] += bool(item.get("response_captured"))
        summary["static_valid"] += item.get("static_status") == "static_valid"
        if item.get("rule_sha256"): summary["rule_hashes"].add(item["rule_sha256"])
    per_anchor: list[dict[str, Any]] = []
    anchor_groups: dict[str, list[dict[str, Any]]] = {}
    for item in records: anchor_groups.setdefault(item["anchor_id"], []).append(item)
    for anchor_id, items in sorted(anchor_groups.items()):
        responses = [item.get("response_sha256") for item in items]
        rules = [item.get("rule_sha256") for item in items]
        per_anchor.append({"anchor_id": anchor_id, "kpi_id": items[0]["kpi_id"], "replicate_response_same": len(responses) == 2 and None not in responses and len(set(responses)) == 1, "replicate_rule_same": len(rules) == 2 and None not in rules and len(set(rules)) == 1, "comparison_status": "available" if None not in responses else "unavailable_due_to_failure"})
    report = {
        "schema_version": "1.0", "task_id": "TASK-035A", "artifact_type": "static_audit_report",
        "rules_extracted": sum(bool(item.get("rule_extracted")) for item in records),
        "static_valid": len(valid), "distinct_response_hashes": len({item.get("response_sha256") for item in records if item.get("response_sha256")}),
        "distinct_rule_hashes": len(rule_groups), "duplicate_rule_groups": [slots for slots in rule_groups.values() if len(slots) > 1],
        "per_kpi": {kpi: {"responses": item["responses"], "static_valid": item["static_valid"], "distinct_rule_hashes": len(item["rule_hashes"])} for kpi, item in sorted(per_kpi.items())},
        "per_anchor": per_anchor, "slots": records, "raw_rule_source_tracked": False,
    }
    report["report_hash"] = sha256_json(report)
    write_json(REPO_ROOT / config["reports"]["static"], report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/argos_reproduction/task035a_expanded_rule_cohort.json")
    args = parser.parse_args()
    report = audit_all((REPO_ROOT / args.config).resolve())
    print(json.dumps({"rules_extracted": report["rules_extracted"], "static_valid": report["static_valid"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
