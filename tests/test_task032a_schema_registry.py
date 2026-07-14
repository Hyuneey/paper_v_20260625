from __future__ import annotations

import copy
import hashlib
import json
import shutil
import tempfile
import unittest
from importlib.metadata import version
from pathlib import Path

from jsonschema import Draft202012Validator

from paperworks.contracts import SchemaRegistryError, load_schema_registry, validate_artifact, validate_artifact_file


REPO_ROOT = Path(__file__).resolve().parents[1]
VALID_ROOT = REPO_ROOT / "fixtures/task030/valid"
INVALID_ROOT = REPO_ROOT / "fixtures/task030/invalid"
MANIFEST_PATH = REPO_ROOT / "configs/contracts/task032a_schema_registry.json"

ARTIFACT_TYPE_BY_FIXTURE = {
    "evidence_package.json": "evidence_package",
    "explanation_record.json": "explanation_record",
    "graph.json": "graph",
    "parameter_duration.json": "parameter_registry",
    "parameter_lag.json": "parameter_registry",
    "parameter_severity.json": "parameter_registry",
    "parameter_tolerance.json": "parameter_registry",
    "rule_dsl.json": "rule_dsl",
    "runtime_trace.json": "runtime_trace",
    "verifier_acceptance.json": "verifier_result",
    "verifier_rejection.json": "verifier_result",
}

SCENARIO_CLASSIFICATION = {
    "excessive_complexity.json": ("structural", "invalid"),
    "executable_code_field.json": ("structural", "invalid"),
    "explanation_nonexistent_rule.json": ("semantic", "valid"),
    "invalid_unit.json": ("structural", "invalid"),
    "missing_parameter.json": ("semantic", "valid"),
    "test_split_parameter_provenance.json": ("structural", "invalid"),
    "unapproved_parameter.json": ("semantic", "valid"),
    "unknown_edge.json": ("semantic", "valid"),
    "unknown_variable.json": ("semantic", "valid"),
    "unsupported_relation_type.json": ("structural", "invalid"),
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def apply_patches(document: dict, patches: list[dict]) -> dict:
    result = copy.deepcopy(document)
    for patch in patches:
        parts = [part for part in patch["path"].split("/") if part]
        parent = result
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
    return result


class Task032ASchemaRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = load_schema_registry()

    def test_all_seven_schemas_pass_meta_validation(self) -> None:
        self.assertEqual(version("jsonschema"), "4.26.0")
        self.assertEqual(len(self.registry.artifact_types), 7)
        for registration in read_json(MANIFEST_PATH)["registrations"]:
            schema = read_json(REPO_ROOT / registration["schema_file"])
            Draft202012Validator.check_schema(schema)

    def test_all_eleven_valid_fixtures_pass_structural_validation(self) -> None:
        for name, artifact_type in ARTIFACT_TYPE_BY_FIXTURE.items():
            report = validate_artifact_file(artifact_type, VALID_ROOT / name, registry=self.registry)
            self.assertEqual(report.status, "valid", (name, report.to_dict()))

    def test_task030_invalid_scenarios_respect_structural_semantic_boundary(self) -> None:
        for scenario_name, (classification, expected_status) in SCENARIO_CLASSIFICATION.items():
            scenario = read_json(INVALID_ROOT / scenario_name)
            base = read_json(VALID_ROOT / scenario["base_fixture"])
            instance = apply_patches(base, scenario["patches"])
            artifact_type = ARTIFACT_TYPE_BY_FIXTURE[scenario["base_fixture"]]
            report = validate_artifact(artifact_type, instance, registry=self.registry)
            self.assertEqual(report.status, expected_status, (scenario_name, classification, report.to_dict()))

    def test_date_and_datetime_format_validation_is_active(self) -> None:
        parameter = read_json(VALID_ROOT / "parameter_lag.json")
        parameter["approval_date"] = "2026-02-30"
        date_report = validate_artifact("parameter_registry", parameter, registry=self.registry)
        self.assertEqual(date_report.status, "invalid")
        self.assertIn("format", {issue.validator_keyword for issue in date_report.issues})

        verifier = read_json(VALID_ROOT / "verifier_acceptance.json")
        verifier["created_at"] = "2026-02-30T25:61:00Z"
        datetime_report = validate_artifact("verifier_result", verifier, registry=self.registry)
        self.assertEqual(datetime_report.status, "invalid")
        self.assertIn("format", {issue.validator_keyword for issue in datetime_report.issues})

        verifier["created_at"] = "2026-07-14T00:00:00Z"
        self.assertEqual(validate_artifact("verifier_result", verifier, registry=self.registry).status, "valid")

    def test_unknown_artifact_type_fails_closed(self) -> None:
        report = validate_artifact("unknown", {}, registry=self.registry)
        self.assertEqual(report.status, "registry_error")
        self.assertEqual(report.issues[0].issue_code, "REGISTRY_UNKNOWN_ARTIFACT_TYPE")

    def test_schema_hash_id_version_and_missing_file_fail_closed(self) -> None:
        mutation_cases = ("hash", "id", "version", "missing")
        for mutation in mutation_cases:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                shutil.copytree(REPO_ROOT / "schemas", root / "schemas")
                (root / "configs/contracts").mkdir(parents=True)
                manifest = read_json(MANIFEST_PATH)
                row = manifest["registrations"][0]
                schema_path = root / row["schema_file"]
                if mutation == "hash":
                    row["schema_sha256"] = "0" * 64
                elif mutation == "missing":
                    schema_path.unlink()
                else:
                    schema = read_json(schema_path)
                    if mutation == "id":
                        schema["$id"] = "https://paperworks.local/schemas/changed.json"
                    else:
                        schema["properties"]["schema_version"]["const"] = "9.9.9"
                    schema_path.write_text(json.dumps(schema), encoding="utf-8")
                    row["schema_sha256"] = hashlib.sha256(schema_path.read_bytes()).hexdigest()
                manifest_path = root / "configs/contracts/task032a_schema_registry.json"
                manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                with self.assertRaises(SchemaRegistryError):
                    load_schema_registry(repository_root=root)

    def test_duplicate_schema_registration_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            shutil.copytree(REPO_ROOT / "schemas", root / "schemas")
            (root / "configs/contracts").mkdir(parents=True)
            manifest = read_json(MANIFEST_PATH)
            duplicate = copy.deepcopy(manifest["registrations"][0])
            duplicate["artifact_type"] = "duplicate_artifact_type"
            manifest["registrations"].append(duplicate)
            manifest_path = root / "configs/contracts/task032a_schema_registry.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaises(SchemaRegistryError):
                load_schema_registry(repository_root=root)

    def test_missing_registration_and_contract_commit_mismatch_fail_closed(self) -> None:
        for mutation in ("missing_registration", "contract_commit"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                shutil.copytree(REPO_ROOT / "schemas", root / "schemas")
                (root / "configs/contracts").mkdir(parents=True)
                manifest = read_json(MANIFEST_PATH)
                if mutation == "missing_registration":
                    manifest["registrations"].pop()
                else:
                    manifest["contract_commit"] = "0" * 40
                manifest_path = root / "configs/contracts/task032a_schema_registry.json"
                manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                with self.assertRaises(SchemaRegistryError):
                    load_schema_registry(repository_root=root)

    def test_validation_issue_order_and_hashes_are_deterministic(self) -> None:
        instance = read_json(VALID_ROOT / "rule_dsl.json")
        instance["source_variables"] = [1]
        instance["target_variables"] = [2]
        before = copy.deepcopy(instance)
        first = validate_artifact("rule_dsl", instance, registry=self.registry)
        second = validate_artifact("rule_dsl", instance, registry=self.registry)
        self.assertEqual(first.to_dict(), second.to_dict())
        keys = [
            (issue.instance_path, issue.schema_path, issue.validator_keyword, issue.message)
            for issue in first.issues
        ]
        self.assertEqual(keys, sorted(keys))
        self.assertEqual(instance, before)
        self.assertRegex(first.instance_sha256, r"^[a-f0-9]{64}$")
        self.assertRegex(first.schema_sha256, r"^[a-f0-9]{64}$")

    def test_file_validation_does_not_modify_input(self) -> None:
        path = VALID_ROOT / "graph.json"
        before = path.read_bytes()
        report = validate_artifact_file("graph", path, registry=self.registry)
        self.assertEqual(report.status, "valid")
        self.assertEqual(path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
