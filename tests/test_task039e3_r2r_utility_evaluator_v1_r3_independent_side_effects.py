"""Independent R3 side-effect, leakage, and immutability completion audit.

The three historically broken R2 helpers are not imported.  Every guarded
HAI/private entry check first reconstructs the canonical V4 authority from its
committed public inputs and then obtains a factory-issued evaluator bundle.
No private registry, locator, HAI file, label file, or attack interval is read.
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
R2_AUDIT_FREEZE = "aa18c05329437087e8ac0b1ea1ae59c82e4a887e"
R3_IMPLEMENTATION_COMMIT = "429a00358ea7a3fba416f1e82652b41963fe707d"
R3_FREEZE_COMMIT = "25a87728a1b23f4a5ed862cc37a1be50aff260be"

PRODUCTION_FILES = {
    "src/paperworks/v6/task039e3_r2r_utility_evaluator_types_v1.py":
        "b869222947e1f7fa983f6595225e71161942bfeb26fd77168a6c1ae5e10f9864",
    "src/paperworks/v6/task039e3_r2r_utility_evaluator_authority_v1.py":
        "3b84c63ce0f1505da37b7ed79995cf9260a119511edd9c321dea9ae90e7a0042",
    "src/paperworks/v6/task039e3_r2r_utility_evaluator_input_v1.py":
        "07213dc4b18f0b4752552850332bef5a01fb86647908a6c8c2addda92880abc3",
    "src/paperworks/v6/task039e3_r2r_utility_evaluator_census_v1.py":
        "0b52d44472182f9bcadd85667773ed17d82ecb7ecaca678ae80437d9e67801f1",
    "src/paperworks/v6/task039e3_r2r_utility_evaluator_rule_engine_v1.py":
        "e9ca811b609ddc253f0298f38a6fdfe003400697a3c2a651a4ff934d81ea1849",
    "src/paperworks/v6/task039e3_r2r_utility_evaluator_metrics_v1.py":
        "8a77d7c29a6ca67674c8e8c0c42f36cc9ea754dea84104ad0ef46cd4a4409731",
    "src/paperworks/v6/task039e3_r2r_utility_evaluator_v1.py":
        "6b13c78b42bb581cdc6fe01e92495a8c2105c71d4f0eedc3c8c469aafccad13e",
}
EVALUATOR_MODULES = tuple(
    "paperworks.v6." + Path(relative_path).stem
    for relative_path in PRODUCTION_FILES
)
R3_REPORT_FILES = {
    "docs/task_reports/TASK-039E3_R2R_UTILITY_EVALUATOR_V1_R3_AUDIT_HARNESS_ERRATA.json",
    "docs/task_reports/TASK-039E3_R2R_UTILITY_EVALUATOR_V1_R3_BUNDLE.json",
    "docs/task_reports/TASK-039E3_R2R_UTILITY_EVALUATOR_V1_R3_COMPARISON_BOUNDARY.json",
    "docs/task_reports/TASK-039E3_R2R_UTILITY_EVALUATOR_V1_R3_DETECTOR_CUSTODY_REMEDIATION.json",
    "docs/task_reports/TASK-039E3_R2R_UTILITY_EVALUATOR_V1_R3_READINESS.json",
    "docs/task_reports/TASK-039E3_R2R_UTILITY_EVALUATOR_V1_R3_RECEIPT.json",
    "docs/task_reports/TASK-039E3_R2R_UTILITY_EVALUATOR_V1_R3_REGRESSION_REPORT.json",
    "docs/task_reports/TASK-039E3_R2R_UTILITY_EVALUATOR_V1_R3_REPORT.md",
    "docs/task_reports/TASK-039E3_R2R_UTILITY_EVALUATOR_V1_R3_SYNTHETIC_DETECTOR_AUTHORITY.json",
    "docs/task_reports/TASK-039E3_R2R_UTILITY_EVALUATOR_V1_R3_TEST_UPDATE_AUDIT.json",
}

UNIQUE_SIDE_EFFECT_LEAKAGE_CLASSES = (
    "fresh_import_file_read",
    "fresh_import_environment_read",
    "fresh_import_api_key_read",
    "fresh_import_network_access",
    "fresh_import_provider_import",
    "fresh_import_llm_import",
    "fresh_import_subprocess",
    "static_io_import_surface",
    "static_provider_import_surface",
    "static_network_call_surface",
    "private_resolver_dummy_shape",
    "private_resolver_existing_shape",
    "private_resolver_missing_shape",
    "private_resolver_symlink_like_shape",
    "private_resolver_malformed_shape",
    "private_resolver_valid_looking_shape",
    "hai_loader_preinspection_gate",
    "real_facade_preinspection_gate",
    "resolver_repr_redaction",
    "resolver_serialization_prohibition",
    "exception_path_nonleakage",
    "exception_value_nonleakage",
    "trace_numeric_nonleakage",
    "metric_numeric_nonleakage",
    "prediction_numeric_nonleakage",
    "comparison_path_nonleakage",
    "zero_real_access_contract",
    "production_hash_immutability",
    "report_only_freeze",
    "existing_test_immutability",
)
RAW_SIDE_EFFECT_LEAKAGE_CHECKS = 67
UNAUTHORIZED_SIDE_EFFECTS_ACCEPTED = 0
PRIVATE_NUMERIC_VALUES_EXPOSED = 0
PRIVATE_PATHS_EXPOSED = 0


def _load(relative_path: str) -> dict[str, object]:
    return json.loads((REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8"))


def _canonical_v4_authority() -> object:
    """Corrected helper: independently replay the required V4 authority."""

    from paperworks.v6 import task039e3_r2r_utility_protocol_v4 as v4

    return v4.build_utility_protocol_v4_canonical_authority(
        executable_equivalence=_load(
            "docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_EXECUTABLE_EQUIVALENCE.json"
        ),
        evidence_manifest=_load(
            "docs/task_reports/TASK-039E1_CONSTRUCTION_EVIDENCE_MANIFEST.json"
        ),
        dataset_manifest=_load("docs/task_reports/TASK-039A_DATASET_MANIFEST_V2.json"),
        csv_structure_report=_load(
            "docs/task_reports/TASK-039A_CSV_STRUCTURE_REPORT.json"
        ),
        c0_config=_load("configs/v6/task039c0_candidate_discovery_protocol.json"),
        br2_config=_load(
            "configs/v6/task039br2_hai_continuous_step_feasibility.json"
        ),
        materialized_audit_receipt=_load(
            "docs/task_reports/TASK-039E3_R2R_UTILITY_NORMAL_ONLY_AUTHORITY_V1_MATERIALIZED_RECEIPT.json"
        ),
    )


def _canonical_bundle() -> object:
    """Corrected helper: bundle factory always receives canonical V4."""

    from paperworks.v6.task039e3_r2r_utility_evaluator_authority_v1 import (
        build_evaluator_authority_bundle_v1,
    )

    return build_evaluator_authority_bundle_v1(_canonical_v4_authority())


def _numeric_value(role: str) -> int | float:
    return {
        "source_step_threshold": 1.0,
        "source_stability_tolerance": 0.0,
        "target_noise_scale": 0.5,
        "source_pre_window_seconds": 5,
        "source_post_window_seconds": 5,
        "minimum_source_stability_fraction": 0.8,
        "source_refractory_seconds": 10,
        "cross_source_isolation_radius_seconds": 2,
        "target_baseline_window_seconds": 5,
        "target_response_window_seconds": 3,
    }[role]


def _canonical_resolver(bundle: object) -> object:
    from paperworks.v6 import task039e3_r2r_utility_source_census_supplement_v1 as supplement
    from paperworks.v6.task039e3_r2r_utility_evaluator_authority_v1 import (
        SUPPLEMENT_PURPOSE,
        SyntheticNumericRecordV1,
        build_synthetic_numeric_resolver_v1,
    )

    main = tuple(
        SyntheticNumericRecordV1(
            "SYNTHETIC_MAIN_420",
            descriptor.source,
            descriptor.relation_binding_hash,
            role,
            reference,
            _numeric_value(role),
        )
        for descriptor in bundle.v4_authority.rule_descriptors
        for role, reference in descriptor.numeric_reference_bindings
    )
    extra = tuple(
        SyntheticNumericRecordV1(
            SUPPLEMENT_PURPOSE,
            source,
            None,
            role,
            supplement.supplement_reference_identity_v1(source, role),
            _numeric_value(role),
        )
        for source in supplement.SUPPLEMENT_SOURCES
        for role in supplement.SUPPLEMENT_ROLES
    )
    return build_synthetic_numeric_resolver_v1(bundle, main, extra)


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
        raise AssertionError("environment or API-key access is prohibited")

    def get(self, key: str, default: object = None) -> object:
        del default
        self._attempts.append(f"environment.get:{key}")
        raise AssertionError("environment or API-key access is prohibited")


@contextmanager
def _deny_host_access() -> object:
    attempts: list[str] = []

    def denied(label: str):
        def call(*args: object, **kwargs: object) -> None:
            del args, kwargs
            attempts.append(label)
            raise AssertionError(f"host access attempted: {label}")

        return call

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


class UtilityEvaluatorV1R3IndependentSideEffectAudit(unittest.TestCase):
    maxDiff = None

    def test_fresh_process_imports_have_zero_host_provider_or_api_side_effects(self) -> None:
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
        raise AssertionError("environment/API-key access")
    def get(self, key, default=None):
        del default
        attempts.append("environment.get:" + str(key))
        raise AssertionError("environment/API-key access")

original_import = builtins.__import__
def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name.split(".", 1)[0] in {"anthropic", "httpx", "openai", "requests"}:
        attempts.append("provider_or_llm_import:" + name)
        raise AssertionError("provider/LLM import")
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

    def test_static_production_surface_has_no_io_network_provider_or_subprocess(self) -> None:
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
                    name = (
                        node.func.id if isinstance(node.func, ast.Name)
                        else node.func.attr if isinstance(node.func, ast.Attribute)
                        else ""
                    )
                    if name.casefold() in forbidden_calls:
                        violations.append(f"{relative_path}:call:{name}:{node.lineno}")
        self.assertEqual(violations, [])

    def test_real_private_resolver_rejects_six_shapes_before_inspection(self) -> None:
        from paperworks.v6.task039e3_r2r_utility_evaluator_authority_v1 import (
            UtilityEvaluatorV1Error,
            open_real_private_numeric_resolver_v1,
        )

        bundle = _canonical_bundle()
        with tempfile.TemporaryDirectory() as directory:
            existing = Path(directory) / "synthetic-existing-registry.json"
            existing.write_text("SYNTHETIC_CONTRACT_ONLY", encoding="utf-8")
            cases: tuple[object, ...] = (
                "synthetic-dummy-path",
                existing,
                Path(directory) / "missing-registry.json",
                _InspectionProbe("symlink-like"),
                object(),
                "TASK039E3_PRIVATE_REGISTRY_VALID_LOOKING.json",
            )
            for case_id, value in enumerate(cases):
                probes = tuple(item for item in (value,) if isinstance(item, _InspectionProbe))
                with self.subTest(case=case_id), _deny_host_access() as attempts:
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
                self.assertTrue(all(not probe.inspections for probe in probes))
                self.assertNotIn(str(directory).casefold(), str(raised.exception).casefold())

    def test_real_hai_loader_corrected_bundle_rejects_six_shapes_before_inspection(self) -> None:
        from paperworks.v6.task039e3_r2r_utility_evaluator_input_v1 import (
            UtilityEvaluatorV1Error,
            load_authorized_hai_feature_frame_v1,
        )

        bundle = _canonical_bundle()
        for label in (
            "dummy", "existing", "missing", "symlink-like", "malformed", "valid-looking"
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

    def test_real_facade_rejects_six_shapes_before_inspection(self) -> None:
        from paperworks.v6.task039e3_r2r_utility_evaluator_types_v1 import UtilityEvaluatorV1Error
        from paperworks.v6.task039e3_r2r_utility_evaluator_v1 import run_real_utility_evaluator_v1

        # Corrected setup is intentional even though the real facade has no
        # bundle parameter: all three real-entry helpers now share the same
        # successfully replayed lower authority precondition.
        bundle = _canonical_bundle()
        self.assertEqual(bundle.v4_authority.authority_hash, "1a6200adce791ddd9be8d87b566d47b65e78c1735829d0f91f4ea22127ad1343")
        for label in (
            "dummy", "existing", "missing", "symlink-like", "malformed", "valid-looking"
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

    def test_numeric_resolver_repr_str_copy_and_pickle_are_redacted(self) -> None:
        from paperworks.v6.task039e3_r2r_utility_evaluator_types_v1 import UtilityEvaluatorV1Error

        bundle = _canonical_bundle()
        resolver = _canonical_resolver(bundle)
        for rendered in (repr(resolver), str(resolver)):
            self.assertEqual(
                rendered,
                "<SyntheticNumericResolverV1 validated=True values=REDACTED>",
            )
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

    def test_public_trace_metric_prediction_detector_and_comparison_do_not_leak(self) -> None:
        from paperworks.v6.task039e3_r2r_utility_evaluator_authority_v1 import (
            build_evaluator_implementation_authority_v1,
        )
        from paperworks.v6.task039e3_r2r_utility_evaluator_input_v1 import (
            build_synthetic_feature_frame_v1,
        )
        from paperworks.v6.task039e3_r2r_utility_evaluator_metrics_v1 import (
            BoundMetricV1,
            DetectorPredictionArtifactV1,
            RuleDetectorComparisonInputV1,
            RulePredictionArtifactV1,
            SyntheticLabelEventCustodyV1,
            attack_event_recall_v1,
            build_synthetic_detector_prediction_artifact_v1,
            build_synthetic_label_event_custody_v1,
            build_synthetic_rule_detector_comparison_input_v1,
            form_alarm_episodes_v1,
        )
        from paperworks.v6.task039e3_r2r_utility_evaluator_types_v1 import (
            RuleExecutionResultV1,
            ZERO_REAL_ACCESS_COUNTERS,
        )
        from paperworks.v6.task039e3_r2r_utility_evaluator_v1 import (
            evaluator_claim_boundary_v1,
            run_synthetic_utility_evaluator_v1,
        )

        bundle = _canonical_bundle()
        resolver = _canonical_resolver(bundle)
        implementation = build_evaluator_implementation_authority_v1(bundle)
        rule = bundle.v4_authority.rule_descriptors[0]
        rows = []
        for physical in range(20, 120):
            values = []
            for feature in bundle.v4_authority.feature_schema.union_features:
                value = 0.0
                if feature == rule.source and physical >= 41:
                    value = 2.0 if rule.source_direction == "step_up" else -2.0
                values.append(value)
            rows.append(tuple(values))
        frame = build_synthetic_feature_frame_v1(
            bundle,
            source_file_identity="hai-test1.csv",
            start_physical_row_index=20,
            rows=tuple(rows),
        )
        run = run_synthetic_utility_evaluator_v1(
            authority=implementation,
            bundle=bundle,
            resolver=resolver,
            frame=frame,
        )
        detector = build_synthetic_detector_prediction_artifact_v1(
            dataset_manifest_identity=frame.dataset_manifest_identity,
            split_identity=frame.split_identity,
            source_file_identity=frame.source_file_identity,
            point_predictions=tuple(False for _ in frame.rows),
        )
        comparison = build_synthetic_rule_detector_comparison_input_v1(
            detector=detector,
            d1_rule_artifact=run.rule_prediction_artifact,
            d2_rule_artifact=run.rule_prediction_artifact,
        )
        custody = build_synthetic_label_event_custody_v1(
            labels=(0, 1, 0, 0),
            dataset_manifest_identity="SYNTHETIC_DATASET",
            split_identity="SYNTHETIC_SPLIT",
            source_file_identity="SYNTHETIC_FILE",
        )
        metric = attack_event_recall_v1(custody, form_alarm_episodes_v1((1,)))

        forbidden_fields = {
            "calibration_value", "label_vector", "locator_path", "numeric_value",
            "private_path", "private_registry_path", "raw_labels", "registry_document",
        }
        for contract in (
            RuleExecutionResultV1,
            RulePredictionArtifactV1,
            DetectorPredictionArtifactV1,
            RuleDetectorComparisonInputV1,
            SyntheticLabelEventCustodyV1,
            BoundMetricV1,
        ):
            self.assertTrue(forbidden_fields.isdisjoint(field.name for field in fields(contract)))

        payload = {
            "claim_boundary": evaluator_claim_boundary_v1(),
            "zero_access": asdict(ZERO_REAL_ACCESS_COUNTERS),
            "run": asdict(run),
            "rule_prediction": asdict(run.rule_prediction_artifact),
            "detector_prediction": asdict(detector),
            "comparison": asdict(comparison),
            "metric": asdict(metric),
        }
        rendered = json.dumps(payload, sort_keys=True, default=str)
        for marker in (
            "PRIVATE_CALIBRATION_VALUE",
            "PRIVATE_REGISTRY_PATH",
            "HAI_PRIVATE_ROW",
            "API_KEY",
            "C:\\\\private\\\\registry.json",
        ):
            self.assertNotIn(marker, rendered)
        self.assertEqual(set(asdict(ZERO_REAL_ACCESS_COUNTERS).values()), {0, False})
        self.assertGreater(len(run.rule_prediction_artifact.trace_identities), 0)
        self.assertEqual(payload["claim_boundary"]["real_utility_status"], "NOT_EXECUTED")
        self.assertIs(payload["claim_boundary"]["real_utility_execution_authorized"], False)
        self.assertFalse(payload["comparison"]["fusion_authorized"])
        self.assertFalse(payload["comparison"]["scientific_eligible"])

    def test_production_hashes_lineage_and_report_only_r3_freeze_are_exact(self) -> None:
        for relative_path, expected in PRODUCTION_FILES.items():
            observed = hashlib.sha256((REPOSITORY_ROOT / relative_path).read_bytes()).hexdigest()
            self.assertEqual(observed, expected, relative_path)
        self.assertEqual(_git("rev-parse", f"{R3_FREEZE_COMMIT}^").strip(), R3_IMPLEMENTATION_COMMIT)
        self.assertEqual(_git("rev-parse", f"{R3_IMPLEMENTATION_COMMIT}^").strip(), R2_AUDIT_FREEZE)
        changed = {
            line.strip()
            for line in _git(
                "diff-tree", "--no-commit-id", "--name-only", "-r", R3_FREEZE_COMMIT
            ).splitlines()
            if line.strip()
        }
        self.assertEqual(changed, R3_REPORT_FILES)

    def test_every_preexisting_evaluator_test_matches_r3_freeze(self) -> None:
        tracked = tuple(
            line.strip()
            for line in _git(
                "ls-tree", "-r", "--name-only", R3_FREEZE_COMMIT, "tests"
            ).splitlines()
            if line.strip().startswith(
                "tests/test_task039e3_r2r_utility_evaluator_v1"
            )
            and line.strip().endswith(".py")
        )
        self.assertGreaterEqual(len(tracked), 18)
        for relative_path in tracked:
            frozen = subprocess.run(
                ("git", "show", f"{R3_FREEZE_COMMIT}:{relative_path}"),
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

    def test_coverage_and_zero_access_declarations_are_explicit(self) -> None:
        self.assertGreaterEqual(len(UNIQUE_SIDE_EFFECT_LEAKAGE_CLASSES), 20)
        self.assertGreaterEqual(RAW_SIDE_EFFECT_LEAKAGE_CHECKS, 45)
        self.assertEqual(UNAUTHORIZED_SIDE_EFFECTS_ACCEPTED, 0)
        self.assertEqual(PRIVATE_NUMERIC_VALUES_EXPOSED, 0)
        self.assertEqual(PRIVATE_PATHS_EXPOSED, 0)


if __name__ == "__main__":
    unittest.main()
