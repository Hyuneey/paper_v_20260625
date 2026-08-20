"""Independent R2 side-effect, leakage, and regression-custody audit.

The oracle in this file is the frozen zero-real-access task boundary and the
Git objects named by the task.  It intentionally does not import prior test
helpers or use remediation reports as evidence.
"""

from __future__ import annotations

import ast
import builtins
import copy
from contextlib import ExitStack, contextmanager
from dataclasses import asdict, fields
import hashlib
import json
import os
from pathlib import Path
import pickle
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import urllib.request


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
R2_IMPLEMENTATION_COMMIT = "7c62206bc967e4ab0e101da474aee589e919551f"
R2_FREEZE_COMMIT = "9da3c2c8f3d3bc6b4a617efe0f1aca7fd56b8b19"
R2_IMPLEMENTATION_PARENT = "eef6d7c6b6ef0155b8bc393b4bbc3d82996baed6"

PRODUCTION_FILES = {
    "src/paperworks/v6/task039e3_r2r_utility_evaluator_types_v1.py":
        "b869222947e1f7fa983f6595225e71161942bfeb26fd77168a6c1ae5e10f9864",
    "src/paperworks/v6/task039e3_r2r_utility_evaluator_authority_v1.py":
        "2b6d6594e8df91c97a74ac0d184714b97608b45fe22374a1573f07a59d773b3a",
    "src/paperworks/v6/task039e3_r2r_utility_evaluator_input_v1.py":
        "07213dc4b18f0b4752552850332bef5a01fb86647908a6c8c2addda92880abc3",
    "src/paperworks/v6/task039e3_r2r_utility_evaluator_census_v1.py":
        "0b52d44472182f9bcadd85667773ed17d82ecb7ecaca678ae80437d9e67801f1",
    "src/paperworks/v6/task039e3_r2r_utility_evaluator_rule_engine_v1.py":
        "e9ca811b609ddc253f0298f38a6fdfe003400697a3c2a651a4ff934d81ea1849",
    "src/paperworks/v6/task039e3_r2r_utility_evaluator_metrics_v1.py":
        "b5b70a1016259de0044429583ed159306857088b094c944125bf5717794f4364",
    "src/paperworks/v6/task039e3_r2r_utility_evaluator_v1.py":
        "6b13c78b42bb581cdc6fe01e92495a8c2105c71d4f0eedc3c8c469aafccad13e",
}

EVALUATOR_MODULES = tuple(
    "paperworks.v6." + Path(path).stem for path in PRODUCTION_FILES
)

R2_REPORT_FILES = {
    "docs/task_reports/TASK-039E3_R2R_UTILITY_EVALUATOR_V1_R2_BUNDLE.json",
    "docs/task_reports/TASK-039E3_R2R_UTILITY_EVALUATOR_V1_R2_IMPLEMENTATION_AUTHORITY.json",
    "docs/task_reports/TASK-039E3_R2R_UTILITY_EVALUATOR_V1_R2_PROVENANCE_REMEDIATION.json",
    "docs/task_reports/TASK-039E3_R2R_UTILITY_EVALUATOR_V1_R2_READINESS.json",
    "docs/task_reports/TASK-039E3_R2R_UTILITY_EVALUATOR_V1_R2_RECEIPT.json",
    "docs/task_reports/TASK-039E3_R2R_UTILITY_EVALUATOR_V1_R2_REGRESSION_REPORT.json",
    "docs/task_reports/TASK-039E3_R2R_UTILITY_EVALUATOR_V1_R2_REPORT.md",
    "docs/task_reports/TASK-039E3_R2R_UTILITY_EVALUATOR_V1_R2_RULE_PREDICTION_PROVENANCE.json",
    "docs/task_reports/TASK-039E3_R2R_UTILITY_EVALUATOR_V1_R2_TEST_UPDATE_AUDIT.json",
}

R2_EXISTING_TEST_UPDATES = {
    "tests/test_task039e3_r2r_utility_evaluator_v1_metrics.py",
    "tests/test_task039e3_r2r_utility_evaluator_v1_remediation_r1_authority.py",
}

UNIQUE_SEMANTIC_ATTACK_CLASSES = (
    "fresh_import_file_and_path_io",
    "fresh_import_environment_and_credential_access",
    "fresh_import_network_access",
    "fresh_import_subprocess_access",
    "fresh_import_provider_or_llm_dependency",
    "static_production_io_surface",
    "unauthorized_private_resolver_preinspection_gate",
    "unauthorized_hai_loader_preinspection_gate",
    "unauthorized_real_facade_preinspection_gate",
    "path_shape_independent_rejection",
    "private_resolver_repr_redaction",
    "private_resolver_serialization_prohibition",
    "exception_path_and_value_nonleakage",
    "public_artifact_schema_nonleakage",
    "production_raw_hash_custody",
    "r2_report_only_freeze_custody",
    "r2_test_update_scope_and_assertion_custody",
    "previous_evaluator_test_immutability",
)


def _git(*arguments: str) -> str:
    result = subprocess.run(
        ("git", *arguments),
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout


class _InspectionProbe(os.PathLike[str]):
    """A caller object that fails the audit if production inspects it."""

    def __init__(self, label: str) -> None:
        self.label = label
        self.inspections: list[str] = []

    def _reject(self, operation: str) -> str:
        self.inspections.append(operation)
        raise AssertionError(f"production inspected caller object via {operation}")

    def __fspath__(self) -> str:
        return self._reject("__fspath__")

    def __str__(self) -> str:
        return self._reject("__str__")

    def __repr__(self) -> str:
        return self._reject("__repr__")


class _GuardedEnvironment(dict[str, str]):
    def __init__(self, attempts: list[str]) -> None:
        super().__init__()
        self._attempts = attempts

    def __getitem__(self, key: str) -> str:
        self._attempts.append(f"environment.__getitem__:{key}")
        raise AssertionError("environment access is prohibited")

    def get(self, key: str, default: object = None) -> object:
        del default
        self._attempts.append(f"environment.get:{key}")
        raise AssertionError("environment access is prohibited")


@contextmanager
def _deny_host_access() -> list[str]:
    """Fail immediately if a real entry point touches host resources."""

    attempts: list[str] = []

    def denied(label: str):
        def _call(*args: object, **kwargs: object) -> None:
            del args, kwargs
            attempts.append(label)
            raise AssertionError(f"host access attempted: {label}")

        return _call

    patches = (
        mock.patch.object(builtins, "open", denied("builtins.open")),
        mock.patch.object(Path, "open", denied("Path.open")),
        mock.patch.object(Path, "read_text", denied("Path.read_text")),
        mock.patch.object(Path, "read_bytes", denied("Path.read_bytes")),
        mock.patch.object(Path, "resolve", denied("Path.resolve")),
        mock.patch.object(Path, "stat", denied("Path.stat")),
        mock.patch.object(Path, "exists", denied("Path.exists")),
        mock.patch.object(os, "open", denied("os.open")),
        mock.patch.object(os, "stat", denied("os.stat")),
        mock.patch.object(os, "lstat", denied("os.lstat")),
        mock.patch.object(os, "readlink", denied("os.readlink")),
        mock.patch.object(os, "getenv", denied("os.getenv")),
        mock.patch.object(os, "environ", _GuardedEnvironment(attempts)),
        mock.patch.object(socket, "create_connection", denied("socket.create_connection")),
        mock.patch.object(socket, "socket", denied("socket.socket")),
        mock.patch.object(urllib.request, "urlopen", denied("urllib.request.urlopen")),
    )
    with ExitStack() as stack:
        for patch in patches:
            stack.enter_context(patch)
        yield attempts


def _valid_synthetic_resolver() -> object:
    """Build closed synthetic authority without importing a prior test helper."""

    from paperworks.v6 import task039e3_r2r_utility_source_census_supplement_v1 as supplement
    from paperworks.v6.task039e3_r2r_utility_evaluator_authority_v1 import (
        SUPPLEMENT_PURPOSE,
        SUPPLEMENT_SOURCES,
        SOURCE_CENSUS_ROLES,
        SyntheticNumericRecordV1,
        build_evaluator_authority_bundle_v1,
        build_synthetic_numeric_resolver_v1,
    )

    bundle = build_evaluator_authority_bundle_v1()
    exact_values: dict[str, int | float] = {
        "source_step_threshold": 1.0,
        "source_stability_tolerance": 0.0,
        "target_noise_scale": 1.0,
        "minimum_source_stability_fraction": 0.8,
        "source_pre_window_seconds": 5,
        "source_post_window_seconds": 5,
        "source_refractory_seconds": 10,
        "cross_source_isolation_radius_seconds": 2,
        "target_baseline_window_seconds": 5,
        "target_response_window_seconds": 3,
    }
    main_records = tuple(
        SyntheticNumericRecordV1(
            "SYNTHETIC_MAIN_420",
            descriptor.source,
            descriptor.relation_binding_hash,
            role,
            reference,
            exact_values[role],
        )
        for descriptor in bundle.v4_authority.rule_descriptors
        for role, reference in descriptor.numeric_reference_bindings
    )
    supplement_records = tuple(
        SyntheticNumericRecordV1(
            SUPPLEMENT_PURPOSE,
            source,
            None,
            role,
            supplement.supplement_reference_identity_v1(source, role),
            exact_values[role],
        )
        for source in SUPPLEMENT_SOURCES
        for role in SOURCE_CENSUS_ROLES
    )
    return build_synthetic_numeric_resolver_v1(
        bundle,
        main_records,
        supplement_records,
    )


class UtilityEvaluatorV1R2IndependentSideEffectAudit(unittest.TestCase):
    maxDiff = None

    def test_fresh_process_imports_have_zero_host_or_provider_side_effects(self) -> None:
        script = r'''
import builtins
import http.client
import importlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import urllib.request

attempts = []

def denied(label):
    def call(*args, **kwargs):
        del args, kwargs
        attempts.append(label)
        raise AssertionError("prohibited import side effect: " + label)
    return call

class GuardEnvironment(dict):
    def __getitem__(self, key):
        attempts.append("environment.__getitem__:" + str(key))
        raise AssertionError("environment access")
    def get(self, key, default=None):
        del default
        attempts.append("environment.get:" + str(key))
        raise AssertionError("environment access")

original_import = builtins.__import__
def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name.split(".", 1)[0] in {"openai", "anthropic", "requests", "httpx"}:
        attempts.append("provider_import:" + name)
        raise AssertionError("provider import")
    return original_import(name, globals, locals, fromlist, level)

sys.path.insert(0, sys.argv[1])
builtins.open = denied("builtins.open")
builtins.__import__ = guarded_import
Path.open = denied("Path.open")
Path.read_text = denied("Path.read_text")
Path.read_bytes = denied("Path.read_bytes")
Path.resolve = denied("Path.resolve")
Path.stat = denied("Path.stat")
Path.exists = denied("Path.exists")
os.getenv = denied("os.getenv")
os.environ = GuardEnvironment()
socket.create_connection = denied("socket.create_connection")
socket.socket = denied("socket.socket")
urllib.request.urlopen = denied("urllib.request.urlopen")
http.client.HTTPConnection.connect = denied("HTTPConnection.connect")
http.client.HTTPSConnection.connect = denied("HTTPSConnection.connect")
subprocess.Popen = denied("subprocess.Popen")
subprocess.run = denied("subprocess.run")
subprocess.call = denied("subprocess.call")
subprocess.check_call = denied("subprocess.check_call")
subprocess.check_output = denied("subprocess.check_output")

for module_name in sys.argv[2:]:
    importlib.import_module(module_name)
print(json.dumps(attempts, sort_keys=True))
'''
        result = subprocess.run(
            (sys.executable, "-I", "-c", script, str(SOURCE_ROOT), *EVALUATOR_MODULES),
            cwd=REPOSITORY_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), [])

    def test_static_production_surface_contains_no_io_provider_or_network_code(self) -> None:
        forbidden_import_roots = {
            "anthropic", "httpx", "openai", "requests", "socket", "subprocess", "urllib"
        }
        forbidden_calls = {
            "open", "getenv", "popen", "run", "urlopen", "read_text", "read_bytes"
        }
        violations: list[str] = []
        for relative_path in PRODUCTION_FILES:
            tree = ast.parse((REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.split(".", 1)[0] in forbidden_import_roots:
                            violations.append(f"{relative_path}:import:{alias.name}")
                elif isinstance(node, ast.ImportFrom) and node.module is not None:
                    if node.module.split(".", 1)[0] in forbidden_import_roots:
                        violations.append(f"{relative_path}:from:{node.module}")
                elif isinstance(node, ast.Call):
                    name = ""
                    if isinstance(node.func, ast.Name):
                        name = node.func.id
                    elif isinstance(node.func, ast.Attribute):
                        name = node.func.attr
                    if name.casefold() in forbidden_calls:
                        violations.append(f"{relative_path}:call:{name}:{node.lineno}")
        self.assertEqual(violations, [])

    def test_real_private_resolver_rejects_all_path_shapes_before_inspection(self) -> None:
        from paperworks.v6.task039e3_r2r_utility_evaluator_authority_v1 import (
            UtilityEvaluatorV1Error,
            build_evaluator_authority_bundle_v1,
            open_real_private_numeric_resolver_v1,
        )

        bundle = build_evaluator_authority_bundle_v1()
        with tempfile.TemporaryDirectory() as directory:
            existing = Path(directory) / "synthetic-existing-registry.json"
            existing.write_text("SYNTHETIC_CONTRACT_ONLY", encoding="utf-8")
            cases: tuple[object, ...] = (
                "synthetic-valid-looking-private-registry.json",
                existing,
                Path(directory) / "missing-registry.json",
                _InspectionProbe("dummy-pathlike"),
                _InspectionProbe("symlink-like-path"),
                object(),
            )
            for value in cases:
                probes = tuple(item for item in (value,) if isinstance(item, _InspectionProbe))
                with self.subTest(path_shape=type(value).__name__), _deny_host_access() as attempts:
                    with self.assertRaisesRegex(
                        UtilityEvaluatorV1Error,
                        "^REAL_UTILITY_EXECUTION_NOT_AUTHORIZED$",
                    ) as raised:
                        open_real_private_numeric_resolver_v1(
                            authority_bundle=bundle,
                            future_execution_authorization=_InspectionProbe("authorization"),
                            main_locator_path=value,
                            supplement_locator_path=value,
                        )
                self.assertEqual(attempts, [])
                self.assertEqual([probe.inspections for probe in probes], [[] for _ in probes])
                self.assertNotIn("registry", str(raised.exception).casefold())
                self.assertNotIn(str(directory).casefold(), str(raised.exception).casefold())

    def test_real_hai_loader_rejects_all_objects_before_input_inspection(self) -> None:
        from paperworks.v6.task039e3_r2r_utility_evaluator_authority_v1 import (
            UtilityEvaluatorV1Error,
            build_evaluator_authority_bundle_v1,
        )
        from paperworks.v6.task039e3_r2r_utility_evaluator_input_v1 import (
            load_authorized_hai_feature_frame_v1,
        )

        bundle = build_evaluator_authority_bundle_v1()
        for label in (
            "dummy", "existing-temp", "missing", "symlink-like", "malformed", "valid-looking"
        ):
            values = tuple(_InspectionProbe(f"{label}:{position}") for position in range(5))
            with self.subTest(label=label), _deny_host_access() as attempts:
                with self.assertRaisesRegex(
                    UtilityEvaluatorV1Error,
                    "^REAL_HAI_EXECUTION_AUTHORIZATION_UNAVAILABLE$",
                ) as raised:
                    load_authorized_hai_feature_frame_v1(
                        bundle,
                        execution_authorization=values[0],
                        dataset_manifest_identity=values[1],
                        split_identity=values[2],
                        source_file_identity=values[3],
                        expected_file_identity=values[4],
                    )
            self.assertEqual(attempts, [])
            self.assertTrue(all(not probe.inspections for probe in values))
            self.assertNotIn(label, str(raised.exception))

    def test_real_facade_rejects_all_objects_before_inspection(self) -> None:
        from paperworks.v6.task039e3_r2r_utility_evaluator_types_v1 import UtilityEvaluatorV1Error
        from paperworks.v6.task039e3_r2r_utility_evaluator_v1 import run_real_utility_evaluator_v1

        for label in (
            "dummy", "existing-temp", "missing", "symlink-like", "malformed", "valid-looking"
        ):
            values = tuple(_InspectionProbe(f"{label}:{position}") for position in range(5))
            with self.subTest(label=label), _deny_host_access() as attempts:
                with self.assertRaisesRegex(
                    UtilityEvaluatorV1Error,
                    "^REAL_UTILITY_EXECUTION_NOT_AUTHORIZED$",
                ) as raised:
                    run_real_utility_evaluator_v1(
                        execution_authorization=values[0],
                        main_locator=values[1],
                        supplement_locator=values[2],
                        hai_input=values[3],
                        labels=values[4],
                    )
            self.assertEqual(attempts, [])
            self.assertTrue(all(not probe.inspections for probe in values))
            self.assertNotIn(label, str(raised.exception))

    def test_numeric_resolver_public_repr_and_serialization_are_fail_closed(self) -> None:
        from paperworks.v6.task039e3_r2r_utility_evaluator_types_v1 import UtilityEvaluatorV1Error

        resolver = _valid_synthetic_resolver()
        for rendered in (repr(resolver), str(resolver)):
            self.assertEqual(rendered, "<SyntheticNumericResolverV1 validated=True values=REDACTED>")
            self.assertNotIn("_relation_values", rendered)
            self.assertNotIn("_source_values", rendered)
        for operation in (
            lambda: pickle.dumps(resolver),
            lambda: copy.copy(resolver),
            lambda: copy.deepcopy(resolver),
            resolver.export_private_document,
        ):
            with self.subTest(operation=operation), self.assertRaisesRegex(
                UtilityEvaluatorV1Error,
                "^SYNTHETIC_PRIVATE_SERIALIZATION_PROHIBITED$",
            ):
                operation()

    def test_public_contracts_hold_identities_not_private_values_or_paths(self) -> None:
        from paperworks.v6.task039e3_r2r_utility_evaluator_metrics_v1 import (
            BoundMetricV1,
            RulePredictionArtifactV1,
            SyntheticLabelEventCustodyV1,
            attack_event_recall_v1,
            build_synthetic_label_event_custody_v1,
            form_alarm_episodes_v1,
        )
        from paperworks.v6.task039e3_r2r_utility_evaluator_types_v1 import (
            RuleExecutionResultV1,
            ZERO_REAL_ACCESS_COUNTERS,
        )
        from paperworks.v6.task039e3_r2r_utility_evaluator_v1 import evaluator_claim_boundary_v1

        forbidden_fields = {
            "calibration_value", "label_vector", "locator_path", "numeric_value",
            "private_path", "private_registry_path", "raw_labels", "registry_document",
        }
        for contract in (
            RuleExecutionResultV1,
            RulePredictionArtifactV1,
            SyntheticLabelEventCustodyV1,
            BoundMetricV1,
        ):
            self.assertTrue(forbidden_fields.isdisjoint(field.name for field in fields(contract)))

        custody = build_synthetic_label_event_custody_v1(
            labels=(0, 1, 0, 0),
            dataset_manifest_identity="SYNTHETIC_DATASET",
            split_identity="SYNTHETIC_SPLIT",
            source_file_identity="SYNTHETIC_FILE",
        )
        metric = attack_event_recall_v1(custody, form_alarm_episodes_v1((1,)))
        public_payload = {
            "claim_boundary": evaluator_claim_boundary_v1(),
            "zero_access": asdict(ZERO_REAL_ACCESS_COUNTERS),
            "custody": asdict(custody),
            "metric": asdict(metric),
        }
        rendered = json.dumps(public_payload, sort_keys=True, default=str)
        for private_marker in (
            "PRIVATE_CALIBRATION_VALUE", "PRIVATE_REGISTRY_PATH", "HAI_PRIVATE_ROW"
        ):
            self.assertNotIn(private_marker, rendered)
        self.assertEqual(set(asdict(ZERO_REAL_ACCESS_COUNTERS).values()), {0, False})
        self.assertEqual(public_payload["claim_boundary"]["real_utility_status"], "NOT_EXECUTED")
        self.assertIs(public_payload["claim_boundary"]["real_utility_execution_authorized"], False)

    def test_r2_production_hashes_lineage_and_report_only_freeze_are_exact(self) -> None:
        for relative_path, expected in PRODUCTION_FILES.items():
            observed = hashlib.sha256((REPOSITORY_ROOT / relative_path).read_bytes()).hexdigest()
            self.assertEqual(observed, expected, relative_path)
        self.assertEqual(_git("rev-parse", f"{R2_FREEZE_COMMIT}^").strip(), R2_IMPLEMENTATION_COMMIT)
        self.assertEqual(_git("rev-parse", f"{R2_IMPLEMENTATION_COMMIT}^").strip(), R2_IMPLEMENTATION_PARENT)
        changed = {
            line.strip()
            for line in _git(
                "diff-tree", "--no-commit-id", "--name-only", "-r", R2_FREEZE_COMMIT
            ).splitlines()
            if line.strip()
        }
        self.assertEqual(changed, R2_REPORT_FILES)

    def test_r2_existing_test_updates_are_only_provenance_fixture_changes(self) -> None:
        changed = {
            line.strip()
            for line in _git(
                "diff", "--name-only", R2_IMPLEMENTATION_PARENT, R2_IMPLEMENTATION_COMMIT,
                "--", "tests"
            ).splitlines()
            if line.strip()
        }
        added_r2_test = "tests/test_task039e3_r2r_utility_evaluator_v1_remediation_r2_provenance.py"
        self.assertEqual(changed, R2_EXISTING_TEST_UPDATES | {added_r2_test})

        metrics_diff = _git(
            "diff", "--unified=0", R2_IMPLEMENTATION_PARENT, R2_IMPLEMENTATION_COMMIT,
            "--", "tests/test_task039e3_r2r_utility_evaluator_v1_metrics.py"
        )
        changed_metrics_lines = tuple(
            line for line in metrics_diff.splitlines()
            if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))
        )
        self.assertTrue(changed_metrics_lines)
        self.assertFalse(any("assert" in line.casefold() for line in changed_metrics_lines))
        self.assertFalse(any(token in metrics_diff.casefold() for token in (
            "expected_recall", "expected_far", "source_event_count", "opportunity_count"
        )))
        self.assertIn("evaluator_implementation_authority", metrics_diff)

        authority_diff = _git(
            "diff", "--unified=0", R2_IMPLEMENTATION_PARENT, R2_IMPLEMENTATION_COMMIT,
            "--", "tests/test_task039e3_r2r_utility_evaluator_v1_remediation_r1_authority.py"
        )
        changed_authority_lines = tuple(
            line for line in authority_diff.splitlines()
            if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))
        )
        self.assertTrue(changed_authority_lines)
        scientific_terms = (
            "attack_event", "census", "far", "metric", "opportunity", "rule_state"
        )
        self.assertFalse(any(
            term in "\n".join(changed_authority_lines).casefold() for term in scientific_terms
        ))
        self.assertIn('UTILITY_EVALUATOR_CONTROL_REVISION, "R2"', authority_diff)

    def test_all_preexisting_evaluator_tests_match_the_r2_freeze(self) -> None:
        tracked = tuple(
            line.strip()
            for line in _git(
                "ls-tree", "-r", "--name-only", R2_FREEZE_COMMIT, "tests"
            ).splitlines()
            if line.strip().startswith("tests/test_task039e3_r2r_utility_evaluator_v1")
            and line.strip().endswith(".py")
        )
        self.assertGreaterEqual(len(tracked), 14)
        for relative_path in tracked:
            frozen = subprocess.run(
                ("git", "show", f"{R2_FREEZE_COMMIT}:{relative_path}"),
                cwd=REPOSITORY_ROOT,
                check=True,
                capture_output=True,
            ).stdout
            current = (REPOSITORY_ROOT / relative_path).read_bytes()
            self.assertEqual(
                hashlib.sha256(current).hexdigest(),
                hashlib.sha256(frozen).hexdigest(),
                relative_path,
            )


if __name__ == "__main__":
    unittest.main()
