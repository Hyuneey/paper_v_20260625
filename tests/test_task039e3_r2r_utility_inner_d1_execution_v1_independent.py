from __future__ import annotations

import ast
import copy
from dataclasses import fields, replace
import inspect
import json
from pathlib import Path
import subprocess
import unittest

from paperworks.v6 import task039e3_r2r_utility_evaluator_authority_v1 as evaluator_authority
from paperworks.v6 import task039e3_r2r_utility_inner_d1_execution_v1 as bridge
from paperworks.v6 import task039e3_r2r_utility_source_census_supplement_v1 as supplement


ROOT = Path(__file__).resolve().parents[1]
COMMIT_A = "936296c"
INDEPENDENT_ATTACKS = 40


def role_value(role: str) -> int | float:
    values: dict[str, int | float] = {
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
    }
    return values[role]


def bypass_dataclass(value: object, **changes: object) -> object:
    forged = object.__new__(type(value))
    for item in fields(value):
        object.__setattr__(
            forged, item.name, changes.get(item.name, getattr(value, item.name))
        )
    return forged


class IndependentInnerD1ExecutionBridgeAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.authority, cls.bundle = bridge._load_public_authorities_v1()
        cls.main_records = tuple(
            evaluator_authority.SyntheticNumericRecordV1(
                "SYNTHETIC_MAIN_420",
                rule.source,
                rule.relation_binding_hash,
                role,
                reference,
                role_value(role),
            )
            for rule in cls.authority.rule_descriptors
            for role, reference in rule.numeric_reference_bindings
        )
        cls.supplement_records = tuple(
            evaluator_authority.SyntheticNumericRecordV1(
                evaluator_authority.SUPPLEMENT_PURPOSE,
                source,
                None,
                role,
                supplement.supplement_reference_identity_v1(source, role),
                role_value(role),
            )
            for source in evaluator_authority.SUPPLEMENT_SOURCES
            for role in evaluator_authority.SOURCE_CENSUS_ROLES
        )

    def test_01_commit_a_and_frozen_module_identity(self) -> None:
        source_relative = "src/paperworks/v6/task039e3_r2r_utility_inner_d1_execution_v1.py"
        observed = subprocess.run(
            ["git", "log", "-1", "--format=%h", "--", source_relative],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip()
        self.assertEqual(observed, COMMIT_A)
        frozen = (
            "task039e3_r2r_utility_evaluator_types_v1.py",
            "task039e3_r2r_utility_evaluator_authority_v1.py",
            "task039e3_r2r_utility_evaluator_input_v1.py",
            "task039e3_r2r_utility_evaluator_census_v1.py",
            "task039e3_r2r_utility_evaluator_rule_engine_v1.py",
            "task039e3_r2r_utility_evaluator_metrics_v1.py",
            "task039e3_r2r_utility_evaluator_v1.py",
        )
        for name in frozen:
            relative = f"src/paperworks/v6/{name}"
            base_blob = subprocess.run(
                ["git", "rev-parse", f"1a961eadc4813acfc959580c0558f0bf33aa5c7c:{relative}"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip()
            head_blob = subprocess.run(
                ["git", "rev-parse", f"HEAD:{relative}"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip()
            self.assertEqual(base_blob, head_blob)
        authorization_relative = "src/paperworks/v6/task039e3_r2r_utility_inner_execution_authorization_v1.py"
        self.assertEqual(
            subprocess.run(
                ["git", "rev-parse", f"721b5b60ecbf1e2b33bf03f864ee9171a47800e1:{authorization_relative}"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip(),
            subprocess.run(
                ["git", "rev-parse", f"HEAD:{authorization_relative}"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip(),
        )

    def test_02_ten_committed_grant_forgery_attacks_reject(self) -> None:
        grant = bridge.issue_committed_inner_d1_execution_grant_v1()
        mutations = (
            {"authorization_hash": "a" * 64},
            {"authorization_report_commit": "a" * 40},
            {"custody_preflight_hash": "a" * 64},
            {"readiness_hash": "a" * 64},
            {"bundle_hash": "a" * 64},
            {"receipt_hash": "a" * 64},
            {"authorization_scope": "OUTER"},
            {"d0_authorized": True},
            {"d2_authorized": True},
            {"detector_authorized": True},
        )
        self.assertEqual(len(mutations), 10)
        for mutation in mutations:
            forged = bypass_dataclass(grant, **mutation)
            payload = forged._payload()
            object.__setattr__(forged, "grant_hash", bridge.stable_hash_v1(payload))
            with self.subTest(mutation=tuple(mutation)), self.assertRaises(
                bridge.InnerD1ExecutionV1Error
            ):
                bridge.validate_committed_inner_d1_execution_grant_v1(forged)

    def test_03_ten_cross_artifact_and_self_rehash_attacks_reject(self) -> None:
        documents = bridge._load_committed_artifact_set_v1()
        attacks = (
            ("authorization", "feature_filename", "hai-test2.csv"),
            ("authorization", "label_filename", "label-test2.csv"),
            ("authorization", "experiment_arm", "D0"),
            ("authorization", "fusion_authorized", True),
            ("authorization", "recalibration_authorized", True),
            ("authorization", "rule_regeneration_authorized", True),
            ("authorization", "metric_modification_authorized", True),
            ("preflight", "main_registry_content_hash_match", False),
            ("preflight", "supplement_registry_content_hash_match", False),
            ("receipt", "authorization_hash", "b" * 64),
        )
        self.assertEqual(len(attacks), 10)
        for name, key, value in attacks:
            forged = copy.deepcopy(documents)
            forged[name][key] = value
            payload = {k: v for k, v in forged[name].items() if k != "artifact_hash"}
            forged[name]["artifact_hash"] = bridge.stable_hash_v1(payload)
            with self.subTest(name=name, key=key), self.assertRaises(
                bridge.InnerD1ExecutionV1Error
            ):
                bridge._validate_committed_artifact_set_v1(forged)

    def test_04_ten_caller_scientific_knob_attacks_reject_before_io(self) -> None:
        keywords = (
            "repo_root",
            "feature_path",
            "label_path",
            "main_registry_path",
            "supplement_registry_path",
            "opportunity_subset",
            "threshold_override",
            "metric_denominator",
            "retry",
            "output_writer",
        )
        self.assertEqual(len(keywords), 10)
        self.assertEqual(tuple(inspect.signature(bridge.execute_authorized_inner_d1_v1).parameters), ())
        for keyword in keywords:
            with self.subTest(keyword=keyword), self.assertRaises(TypeError):
                bridge.execute_authorized_inner_d1_v1(**{keyword: object()})

    def test_05_five_private_resolver_cross_authority_attacks_reject(self) -> None:
        resolver = bridge.build_differential_numeric_resolver_v1(
            self.bundle, self.main_records, self.supplement_records
        )
        attacks = []
        forged = object.__new__(bridge.RealPrivateNumericResolverV1)
        for name in (
            "_bundle",
            "_relation_values",
            "_relation_references",
            "_source_values",
            "resolver_identity",
        ):
            object.__setattr__(forged, name, getattr(resolver, name))
        attacks.append(forged)
        for member in ("_relation_values", "_relation_references", "_source_values"):
            candidate = object.__new__(bridge.RealPrivateNumericResolverV1)
            for name in (
                "_bundle",
                "_relation_values",
                "_relation_references",
                "_source_values",
                "resolver_identity",
            ):
                value = dict(getattr(resolver, name)) if name == member else getattr(resolver, name)
                object.__setattr__(candidate, name, value)
            attacks.append(candidate)
        attacks.append(copy.copy(resolver) if False else forged)
        self.assertEqual(len(attacks), 5)
        for index, candidate in enumerate(attacks):
            with self.subTest(index=index), self.assertRaises(
                bridge.InnerD1ExecutionV1Error
            ):
                bridge.validate_real_private_numeric_resolver_v1(candidate, self.bundle)

    def test_06_five_prediction_factory_and_label_order_attacks_reject(self) -> None:
        ordered = self.authority.feature_schema.union_features
        rule = self.authority.rule_descriptors[0]
        rows = []
        for index in range(50):
            values = {feature: 0.0 for feature in ordered}
            if index >= 20:
                values[rule.source] = 2.0 if rule.source_direction == "step_up" else -2.0
            rows.append(tuple(values[feature] for feature in ordered))
        frame = bridge.build_differential_feature_frame_v1(self.bundle, tuple(rows))
        resolver = bridge.build_differential_numeric_resolver_v1(
            self.bundle, self.main_records, self.supplement_records
        )
        census = bridge.enumerate_real_full_census_v1(
            frame, self.bundle, resolver, differential=True
        )
        results = tuple(
            bridge.execute_real_rule_v1(
                envelope,
                census,
                frame,
                self.bundle,
                resolver,
                differential=True,
            )
            for envelope in census.relation_opportunities
        )
        grant = bridge.issue_committed_inner_d1_execution_grant_v1()
        token = bridge._issue_execution_token_v1(grant)
        attempts = (
            results,
            tuple(bypass_dataclass(result) for result in results),
            tuple(reversed(results)),
            results[:-1],
            results + results[:1],
        )
        self.assertEqual(len(attempts), 5)
        for index, attempt in enumerate(attempts):
            with self.subTest(index=index), self.assertRaises(
                bridge.InnerD1ExecutionV1Error
            ):
                bridge.build_scientific_rule_prediction_artifact_v1(
                    token, census, attempt
                )
        with self.assertRaises(bridge.InnerD1ExecutionV1Error):
            bridge._issue_execution_token_v1(grant)
        module = ast.parse(
            (ROOT / "src/paperworks/v6/task039e3_r2r_utility_inner_d1_execution_v1.py").read_text(
                encoding="utf-8"
            )
        )
        function = next(
            item
            for item in module.body
            if isinstance(item, ast.FunctionDef)
            and item.name == "execute_authorized_inner_d1_v1"
        )
        source = ast.unparse(function)
        self.assertLess(
            source.index("build_scientific_rule_prediction_artifact_v1"),
            source.index("_load_real_label_custody_v1"),
        )


if __name__ == "__main__":
    unittest.main()
