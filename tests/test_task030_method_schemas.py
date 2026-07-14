from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
import re
import unittest
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = REPO_ROOT / "schemas"
VALID_ROOT = REPO_ROOT / "fixtures/task030/valid"
INVALID_ROOT = REPO_ROOT / "fixtures/task030/invalid"

SCHEMA_BY_FIXTURE = {
    "graph.json": "graph_schema.json",
    "evidence_package.json": "evidence_package_schema.json",
    "rule_dsl.json": "rule_dsl_schema.json",
    "verifier_acceptance.json": "verifier_result_schema.json",
    "verifier_rejection.json": "verifier_result_schema.json",
    "runtime_trace.json": "runtime_trace_schema.json",
    "explanation_record.json": "explanation_record_schema.json",
}
PROHIBITED_FIELDS = {
    "python",
    "code",
    "source_code",
    "eval",
    "exec",
    "import",
    "callable",
    "lambda",
    "shell",
    "command",
    "dynamic_expression",
}


class ContractValidationError(ValueError):
    def __init__(self, code: str, path: str, message: str):
        super().__init__(f"{code} at {path}: {message}")
        self.code = code
        self.path = path


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_local_ref(root: dict[str, Any], reference: str) -> dict[str, Any]:
    if not reference.startswith("#/"):
        raise ContractValidationError("SCHEMA_REF", "$", "only local refs are allowed")
    current: Any = root
    for part in reference[2:].split("/"):
        current = current[part.replace("~1", "/").replace("~0", "~")]
    return current


def is_type(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    raise ContractValidationError("SCHEMA_TYPE", "$", f"unsupported schema type {expected}")


def validate_schema_instance(
    value: Any,
    schema: dict[str, Any],
    root: dict[str, Any] | None = None,
    path: str = "$",
) -> None:
    root = root or schema
    if "$ref" in schema:
        validate_schema_instance(value, resolve_local_ref(root, schema["$ref"]), root, path)
        return
    if "anyOf" in schema:
        errors = []
        for option in schema["anyOf"]:
            try:
                validate_schema_instance(value, option, root, path)
                return
            except ContractValidationError as exc:
                errors.append(exc)
        raise ContractValidationError("SCHEMA_ANY_OF", path, str(errors[-1]))

    if "const" in schema and value != schema["const"]:
        raise ContractValidationError("SCHEMA_CONST", path, "constant mismatch")
    if "enum" in schema and value not in schema["enum"]:
        raise ContractValidationError("SCHEMA_ENUM", path, "value is outside enum")

    expected_types = schema.get("type")
    if expected_types is not None:
        if isinstance(expected_types, str):
            expected_types = [expected_types]
        if not any(is_type(value, item) for item in expected_types):
            raise ContractValidationError("SCHEMA_TYPE", path, "type mismatch")

    if isinstance(value, dict):
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        missing = [name for name in required if name not in value]
        if missing:
            raise ContractValidationError("SCHEMA_REQUIRED", path, f"missing {missing}")
        if schema.get("additionalProperties") is False:
            unknown = sorted(set(value) - set(properties))
            if unknown:
                raise ContractValidationError("SCHEMA_ADDITIONAL_PROPERTY", path, f"unknown {unknown}")
        for name, child in value.items():
            if name in properties:
                validate_schema_instance(child, properties[name], root, f"{path}.{name}")

    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            raise ContractValidationError("SCHEMA_MIN_ITEMS", path, "too few items")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            raise ContractValidationError("SCHEMA_MAX_ITEMS", path, "too many items")
        if schema.get("uniqueItems"):
            canonical = [json.dumps(item, sort_keys=True) for item in value]
            if len(canonical) != len(set(canonical)):
                raise ContractValidationError("SCHEMA_UNIQUE", path, "duplicate items")
        for index, item in enumerate(value):
            validate_schema_instance(item, schema.get("items", {}), root, f"{path}[{index}]")

    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            raise ContractValidationError("SCHEMA_MIN_LENGTH", path, "string too short")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            raise ContractValidationError("SCHEMA_MAX_LENGTH", path, "string too long")
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            raise ContractValidationError("SCHEMA_PATTERN", path, "pattern mismatch")
        if schema.get("format") == "date-time":
            try:
                dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError as exc:
                raise ContractValidationError("SCHEMA_FORMAT", path, "invalid date-time") from exc
        if schema.get("format") == "date":
            try:
                dt.date.fromisoformat(value)
            except ValueError as exc:
                raise ContractValidationError("SCHEMA_FORMAT", path, "invalid date") from exc

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            raise ContractValidationError("SCHEMA_MINIMUM", path, "below minimum")
        if "maximum" in schema and value > schema["maximum"]:
            raise ContractValidationError("SCHEMA_MAXIMUM", path, "above maximum")
        if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]:
            raise ContractValidationError("SCHEMA_EXCLUSIVE_MINIMUM", path, "not above minimum")


def find_prohibited_field(value: Any, path: str = "$") -> str | None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in PROHIBITED_FIELDS:
                return f"{path}.{key}"
            found = find_prohibited_field(child, f"{path}.{key}")
            if found:
                return found
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found = find_prohibited_field(child, f"{path}[{index}]")
            if found:
                return found
    return None


def apply_patches(document: dict[str, Any], patches: list[dict[str, Any]]) -> dict[str, Any]:
    result = copy.deepcopy(document)
    for patch in patches:
        parts = [part for part in patch["path"].split("/") if part]
        parent: Any = result
        for part in parts[:-1]:
            parent = parent[int(part)] if isinstance(parent, list) else parent[part]
        leaf = parts[-1]
        if patch["operation"] in {"add", "replace"}:
            if isinstance(parent, list):
                parent[int(leaf)] = patch["value"]
            else:
                parent[leaf] = patch["value"]
        elif patch["operation"] == "remove":
            if isinstance(parent, list):
                del parent[int(leaf)]
            else:
                del parent[leaf]
        else:
            raise AssertionError(f"unsupported fixture patch operation: {patch['operation']}")
    return result


def collect_parameter_refs(value: Any) -> set[str]:
    refs: set[str] = set()
    if isinstance(value, dict):
        for child in value.values():
            refs.update(collect_parameter_refs(child))
    elif isinstance(value, list):
        for child in value:
            refs.update(collect_parameter_refs(child))
    elif isinstance(value, str) and value.startswith("PARAM-"):
        refs.add(value)
    return refs


def load_valid_bundle() -> dict[str, Any]:
    parameters = [read_json(path) for path in sorted(VALID_ROOT.glob("parameter_*.json"))]
    return {
        "graph": read_json(VALID_ROOT / "graph.json"),
        "evidence": read_json(VALID_ROOT / "evidence_package.json"),
        "parameters": parameters,
        "rule": read_json(VALID_ROOT / "rule_dsl.json"),
        "verifier": read_json(VALID_ROOT / "verifier_acceptance.json"),
        "runtime": read_json(VALID_ROOT / "runtime_trace.json"),
        "explanation": read_json(VALID_ROOT / "explanation_record.json"),
    }


def validate_bundle_semantics(bundle: dict[str, Any]) -> None:
    graph = bundle["graph"]
    nodes = {node["node_id"]: node for node in graph["nodes"]}
    variables = {node["variable_name"] for node in graph["nodes"]}
    edges = {edge["edge_id"]: edge for edge in graph["edges"]}
    for edge in edges.values():
        if edge["source_node"] not in nodes or edge["target_node"] not in nodes:
            raise ContractValidationError("UNKNOWN_EDGE_NODE", "graph.edges", "edge node is not registered")
        if edge["source_node"] == edge["target_node"]:
            raise ContractValidationError("SELF_EDGE", "graph.edges", "candidate self-edge is prohibited")

    evidence = bundle["evidence"]
    evidence_ids = {evidence["evidence_id"]}
    normal_refs = {evidence["matched_normal_reference"]["reference_id"]}
    if not set(evidence["source_variables"] + evidence["target_variables"]).issubset(variables):
        raise ContractValidationError("UNKNOWN_VARIABLE", "evidence", "evidence variable is not registered")

    parameters = {item["parameter_id"]: item for item in bundle["parameters"]}
    for parameter in parameters.values():
        if parameter["approval_status"] != "approved":
            raise ContractValidationError("PARAMETER_NOT_APPROVED", "parameter", "parameter is not approved")
        if parameter["calibration_split"] != "calibration":
            raise ContractValidationError("TEST_SPLIT_PARAMETER", "parameter", "calibration split is invalid")
        if not set(parameter["normal_reference_refs"]).issubset(normal_refs):
            raise ContractValidationError("UNKNOWN_NORMAL_REFERENCE", "parameter", "normal reference missing")

    rule = bundle["rule"]
    if not set(rule["source_variables"] + rule["target_variables"]).issubset(variables):
        raise ContractValidationError("UNKNOWN_VARIABLE", "rule", "rule variable is not registered")
    if not set(rule["graph_edge_refs"]).issubset(edges):
        raise ContractValidationError("UNKNOWN_EDGE", "rule", "rule edge is not registered")
    if not set(rule["evidence_refs"]).issubset(evidence_ids):
        raise ContractValidationError("UNKNOWN_EVIDENCE", "rule", "evidence is not registered")
    if not set(rule["normal_reference_refs"]).issubset(normal_refs):
        raise ContractValidationError("UNKNOWN_NORMAL_REFERENCE", "rule", "normal reference is not registered")
    missing_parameters = collect_parameter_refs(rule) - set(parameters)
    if missing_parameters:
        raise ContractValidationError("MISSING_PARAMETER", "rule", f"missing {sorted(missing_parameters)}")

    verifier = bundle["verifier"]
    if verifier["status"] != "accepted" or verifier["rule_id"] != rule["rule_id"]:
        raise ContractValidationError("VERIFIER_NOT_ACCEPTED", "verifier", "rule lacks accepted verifier result")
    if set(verifier["verified_parameters"]) != collect_parameter_refs(rule):
        raise ContractValidationError("VERIFIER_PARAMETER_MISMATCH", "verifier", "parameter set differs")

    runtime = bundle["runtime"]
    if runtime["rule_id"] != rule["rule_id"] or runtime["rule_hash"] != rule["verified_rule_hash"]:
        raise ContractValidationError("RUNTIME_RULE_MISMATCH", "runtime", "runtime rule reference differs")
    if runtime["verifier_result_ref"] != verifier["verifier_result_id"]:
        raise ContractValidationError("RUNTIME_VERIFIER_MISMATCH", "runtime", "runtime verifier differs")

    explanation = bundle["explanation"]
    if explanation["rule_id"] != rule["rule_id"]:
        raise ContractValidationError("EXPLANATION_RULE_NOT_FOUND", "explanation", "rule is not registered")
    if explanation["execution_id"] != runtime["execution_id"]:
        raise ContractValidationError("EXPLANATION_RUNTIME_NOT_FOUND", "explanation", "runtime is not registered")
    if explanation["causal_claim_made"] or explanation["root_cause_claim_made"]:
        raise ContractValidationError("UNSUPPORTED_CLAIM", "explanation", "causal claim is prohibited")


class Task030MethodSchemaTests(unittest.TestCase):
    def test_schema_documents_are_explicit_and_closed(self) -> None:
        schemas = sorted(SCHEMA_ROOT.glob("*_schema.json"))
        self.assertEqual(len(schemas), 7)
        for path in schemas:
            schema = read_json(path)
            self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
            self.assertEqual(schema["properties"]["schema_version"]["const"], "1.0.0")
            self.assertFalse(schema["additionalProperties"], path.name)
            self.assertTrue(schema.get("description"), path.name)

    def test_all_valid_fixtures_pass_schema_validation(self) -> None:
        for fixture_path in sorted(VALID_ROOT.glob("*.json")):
            schema_name = SCHEMA_BY_FIXTURE.get(fixture_path.name)
            if schema_name is None and fixture_path.name.startswith("parameter_"):
                schema_name = "parameter_registry_schema.json"
            self.assertIsNotNone(schema_name, fixture_path.name)
            document = read_json(fixture_path)
            if fixture_path.name == "rule_dsl.json":
                self.assertIsNone(find_prohibited_field(document), fixture_path.name)
            validate_schema_instance(document, read_json(SCHEMA_ROOT / schema_name))

        validate_bundle_semantics(load_valid_bundle())

    def test_invalid_fixtures_fail_for_declared_reason(self) -> None:
        for scenario_path in sorted(INVALID_ROOT.glob("*.json")):
            scenario = read_json(scenario_path)
            document = apply_patches(
                read_json(VALID_ROOT / scenario["base_fixture"]),
                scenario["patches"],
            )
            bundle = load_valid_bundle()
            if scenario["base_fixture"].startswith("parameter_"):
                bundle["parameters"] = [
                    document if item["parameter_id"] == document["parameter_id"] else item
                    for item in bundle["parameters"]
                ]
            elif scenario["base_fixture"] == "rule_dsl.json":
                bundle["rule"] = document
            elif scenario["base_fixture"] == "explanation_record.json":
                bundle["explanation"] = document

            try:
                prohibited = find_prohibited_field(document)
                if prohibited:
                    raise ContractValidationError("EXECUTABLE_FIELD", prohibited, "field is prohibited")
                validate_schema_instance(
                    document,
                    read_json(SCHEMA_ROOT / scenario["target_schema"]),
                )
                validate_bundle_semantics(bundle)
            except ContractValidationError as exc:
                self.assertEqual(exc.code, scenario["expected_error"], scenario_path.name)
            else:
                self.fail(f"invalid fixture passed: {scenario_path.name}")

    def test_task030_has_no_execution_or_data_access_surface(self) -> None:
        source = Path(__file__).read_text(encoding="utf-8")
        prohibited_tokens = [
            "import " + "subprocess",
            "import " + "requests",
            "import " + "urllib",
            "import " + "pandas",
            "import " + "numpy",
            "SWAT_" + "DATA_ROOT",
            "OPENAI_" + "API_KEY",
            "import" + "lib",
            "comp" + "ile(",
            "ex" + "ec(",
            "ev" + "al(",
        ]
        for token in prohibited_tokens:
            self.assertNotIn(token, source)
        self.assertFalse(any("task030" in path.name.lower() for path in (REPO_ROOT / "src/paperworks").rglob("*")))

    def test_frozen_argos_findings_are_recorded_as_audit_not_performance(self) -> None:
        contract = (REPO_ROOT / "docs/method/GRAPH_GUIDED_RULE_CONSTRUCTION_CONTRACT.md").read_text(encoding="utf-8")
        self.assertIn("6b24161ff08de069840a1fb4fbaecf7bf8e393f1", contract)
        self.assertIn("c03427f2ab16e377946d4c1176585156ddae7254", contract)
        self.assertIn("audit findings, not benchmark results", contract)
        self.assertIn("anomaly-anchored evidence curation", contract)

    def test_specification_report_hash_and_boundaries(self) -> None:
        report = read_json(
            REPO_ROOT / "docs/task_reports/TASK-030_SPECIFICATION_REPORT.json"
        )
        expected_hash = report.pop("report_hash")
        canonical = json.dumps(report, sort_keys=True, separators=(",", ":"))
        self.assertEqual(hashlib.sha256(canonical.encode("utf-8")).hexdigest(), expected_hash)
        self.assertEqual(report["task_status"], "complete_specification_only")
        self.assertFalse(report["boundaries"]["dataset_accessed"])
        self.assertFalse(report["boundaries"]["provider_calls"])
        self.assertFalse(report["boundaries"]["generated_python_executed"])
        self.assertFalse(report["boundaries"]["src_paperworks_changed"])


if __name__ == "__main__":
    unittest.main()
