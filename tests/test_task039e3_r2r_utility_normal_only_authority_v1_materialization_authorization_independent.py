from __future__ import annotations

import ast
from dataclasses import replace
from hashlib import sha256
import inspect
import json
from pathlib import Path
import subprocess
import unittest
from unittest import mock

from paperworks.v6.common import stable_hash_v1
from paperworks.v6 import task039e3_r2r_utility_normal_only_authority_v1 as observed


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = "src/paperworks/v6/task039e3_r2r_utility_normal_only_authority_v1.py"
INTERFACE_COMMIT = "216783ac6b3c77376b4e56b92ddc655907ce3668"
INTERFACE_BLOB = "5e6d52fdfadada7373c50c382a347930f3384e24"
INTERFACE_RAW = "1b15098e9f8c75a76ad98f7a0ef998af86470b195d035ffab08e9f185fe1a3d9"


def git(*arguments: str, binary: bool = False) -> str | bytes:
    result = subprocess.run(
        ["git", "-C", str(ROOT), *arguments],
        check=True,
        capture_output=True,
        text=not binary,
    )
    return result.stdout if binary else result.stdout.strip()


def rehash(document: dict[str, object]) -> None:
    document["artifact_hash"] = stable_hash_v1(
        {key: value for key, value in document.items() if key != "artifact_hash"}
    )


def independent_authorization_document() -> dict[str, object]:
    document: dict[str, object] = {
        "artifact_type": "task039e3_r2r_utility_normal_only_authority_v1_materialization_authorization",
        "schema_version": "1.0.0",
        "authority_version": "TASK039E3_UTILITY_NORMAL_ONLY_AUTHORITY_V1",
        "control_revision": "R1",
        "scientific_v1_commit": "d58757b63d21519bc39398ddcf96be1682e8b01a",
        "scientific_v1_source_blob": "b071678a151161f9585301472f5eb23d7ce2c246",
        "scientific_v1_source_raw_sha256": "f18eceabd1f0f5aee7755bff964b985014411b6a0b98425e424863a59256b30e",
        "common42_authority_definition_hash": "6e7a286a37a5048a7887e8bea69f9ec0a9c3ff76c538cbb475e886fba276e4de",
        "calibration_policy_hash": "4f2622050637e3e83205dec59400fa6bf9ed2bd1a41f6b8ceb1900dc9f69b881",
        "executable_equivalence_hash": "3efdce159bc5ac39825d4e4654428237e47205307f83aae7a133db6c5789f60f",
        "normal_input_identity_set_hash": "cc502d87daf19a1511f868c1c767045a4457d505d195b0214f244d1910fe0cda",
        "protocol_audit_closure_hash": "e0d9975a4027cc08140b3b8fd1027580a6668c17eee967553ce604f303e63c36",
        "protocol_audit_receipt_hash": "5be947afa0456ab839e5955aeca238e3fe96ab451a4b8be8c2e7dafaa49c6647",
        "authorized_control_commit": INTERFACE_COMMIT,
        "authorized_control_source_blob": INTERFACE_BLOB,
        "authorized_control_source_raw_sha256": INTERFACE_RAW,
        "focused_independent_reaudit_receipt_hash": "d" * 64,
        "scope": "NORMAL_TRAIN1_TRAIN2_NUMERIC_AUTHORITY_MATERIALIZATION_ONLY",
        "normal_train1_sha256": "53007b0ba604fbf338e7ac2e08cd81d874b5d1388f3aecb213ddcba5bf2bec4a",
        "normal_train2_sha256": "0e520e82bf78a661ab19ce4967f3c766bd809820f457a9c90c365102d4534c56",
        "train3_access": False,
        "test_access": False,
        "label_access": False,
        "provider_access": False,
        "utility_execution": False,
        "materialization_authorized": True,
        "private_locator_environment": "TASK039E3_UTILITY_NORMAL_ONLY_AUTHORITY_V1",
    }
    rehash(document)
    return document


def independent_audit_document(
    authorization: observed.MaterializationExecutionAuthorizationR1,
) -> dict[str, object]:
    document: dict[str, object] = {
        "artifact_type": "task039e3_r2r_utility_normal_only_authority_v1_materialization_authorization_interface_audit",
        "schema_version": "1.0.0",
        "status": "passed_task039e3_r2r_utility_normal_only_authority_v1_materialization_authorization_interface_audit",
        "interface_commit": authorization.authorized_control_commit,
        "interface_source_git_blob": authorization.authorized_control_source_blob,
        "interface_source_raw_sha256": authorization.authorized_control_source_raw_sha256,
        "independent_audit_commit": "e" * 40,
        "independent_tests_passed": 8,
        "independent_tests_failed": 0,
        "scientific_change": False,
        "authorization_control_change": True,
        "protocol_audit_closure_hash": authorization.protocol_audit_closure_hash,
        "protocol_audit_receipt_hash": authorization.protocol_audit_receipt_hash,
        "remaining_blockers": 0,
        "access_counters": {
            "hai_normal_value_accesses": 0,
            "hai_test_value_accesses": 0,
            "hai_label_accesses": 0,
            "train3_value_accesses": 0,
            "utility_computations": 0,
            "provider_calls": 0,
            "api_key_access": False,
            "scientific_llm_calls": 0,
        },
    }
    rehash(document)
    return document


class IndependentMaterializationAuthorizationAudit(unittest.TestCase):
    def test_01_source_has_no_own_commit_blob_or_raw_hash(self) -> None:
        source = (ROOT / SOURCE_PATH).read_text(encoding="utf-8")
        self.assertNotIn(INTERFACE_COMMIT, source)
        self.assertNotIn(INTERFACE_BLOB, source)
        self.assertNotIn(INTERFACE_RAW, source)
        self.assertEqual(git("rev-parse", f"HEAD:{SOURCE_PATH}"), INTERFACE_BLOB)
        self.assertEqual(sha256((ROOT / SOURCE_PATH).read_bytes()).hexdigest(), INTERFACE_RAW)
        self.assertEqual(git("status", "--porcelain", "--", SOURCE_PATH), "")

    def test_02_authorization_mutation_oracle_rejects_26_cases(self) -> None:
        canonical = independent_authorization_document()
        immutable_mutations = {
            "artifact_type": "other",
            "schema_version": "2.0.0",
            "authority_version": "other",
            "control_revision": "R2",
            "scientific_v1_commit": "f" * 40,
            "scientific_v1_source_blob": "f" * 40,
            "scientific_v1_source_raw_sha256": "f" * 64,
            "common42_authority_definition_hash": "f" * 64,
            "calibration_policy_hash": "f" * 64,
            "executable_equivalence_hash": "f" * 64,
            "normal_input_identity_set_hash": "f" * 64,
            "protocol_audit_closure_hash": "f" * 64,
            "protocol_audit_receipt_hash": "f" * 64,
            "scope": "broader",
            "normal_train1_sha256": "f" * 64,
            "normal_train2_sha256": "f" * 64,
            "train3_access": True,
            "test_access": True,
            "label_access": True,
            "provider_access": True,
            "utility_execution": True,
            "materialization_authorized": False,
            "private_locator_environment": "other",
            "artifact_hash": "f" * 64,
        }
        rejected = 0
        for field, value in immutable_mutations.items():
            candidate = json.loads(json.dumps(canonical))
            candidate[field] = value
            if field != "artifact_hash":
                rehash(candidate)
            with self.subTest(field=field), self.assertRaises(observed.NormalOnlyAuthorityV1Error):
                observed.materialization_execution_authorization_from_document_r1(candidate)
            rejected += 1
        for kind in ("unknown", "missing"):
            candidate = json.loads(json.dumps(canonical))
            if kind == "unknown":
                candidate["unknown"] = 1
            else:
                del candidate["scope"]
            rehash(candidate)
            with self.subTest(kind=kind), self.assertRaises(observed.NormalOnlyAuthorityV1Error):
                observed.materialization_execution_authorization_from_document_r1(candidate)
            rejected += 1
        self.assertEqual(rejected, 26)

    def test_03_self_consistent_control_replacement_is_not_committed_authority(self) -> None:
        document = independent_authorization_document()
        for field, value in (
            ("authorized_control_commit", "a" * 40),
            ("authorized_control_source_blob", "b" * 40),
            ("authorized_control_source_raw_sha256", "c" * 64),
            ("focused_independent_reaudit_receipt_hash", "e" * 64),
        ):
            candidate = json.loads(json.dumps(document))
            candidate[field] = value
            rehash(candidate)
            authorization = observed.materialization_execution_authorization_from_document_r1(
                candidate
            )
            with self.subTest(field=field), self.assertRaises(
                observed.NormalOnlyAuthorityV1Error
            ):
                observed.verify_authorized_builder_checkout_r1(ROOT, authorization)

    def test_04_interface_audit_mutation_oracle_rejects_22_cases(self) -> None:
        first = observed.materialization_execution_authorization_from_document_r1(
            independent_authorization_document()
        )
        audit = independent_audit_document(first)
        authorization = replace(
            first,
            focused_independent_reaudit_receipt_hash=str(audit["artifact_hash"]),
            authorization_hash="0" * 64,
        )
        authorization = replace(
            authorization, authorization_hash=stable_hash_v1(authorization.payload())
        )
        self.assertEqual(
            observed.validate_materialization_authorization_interface_audit_r1(
                audit, authorization
            ),
            audit["artifact_hash"],
        )
        mutations: list[tuple[str, object]] = [
            ("artifact_type", "other"),
            ("schema_version", "2.0.0"),
            ("status", "blocked"),
            ("interface_commit", "f" * 40),
            ("interface_source_git_blob", "f" * 40),
            ("interface_source_raw_sha256", "f" * 64),
            ("independent_audit_commit", "f" * 39),
            ("independent_tests_passed", 0),
            ("independent_tests_failed", 1),
            ("scientific_change", True),
            ("authorization_control_change", False),
            ("protocol_audit_closure_hash", "f" * 64),
            ("protocol_audit_receipt_hash", "f" * 64),
            ("remaining_blockers", 1),
        ]
        for key in sorted(audit["access_counters"]):
            mutations.append((f"access_counters.{key}", True if key != "api_key_access" else 1))
        rejected = 0
        for field, value in mutations:
            candidate = json.loads(json.dumps(audit))
            if field.startswith("access_counters."):
                candidate["access_counters"][field.split(".", 1)[1]] = value
            else:
                candidate[field] = value
            rehash(candidate)
            with self.subTest(field=field), self.assertRaises(observed.NormalOnlyAuthorityV1Error):
                observed.validate_materialization_authorization_interface_audit_r1(
                    candidate, authorization
                )
            rejected += 1
        self.assertEqual(rejected, 22)

    def test_05_source_and_both_calibration_dependencies_are_exact(self) -> None:
        expected = (
            (SOURCE_PATH, INTERFACE_BLOB, INTERFACE_RAW),
            (
                observed.RELATION_PROFILING_SOURCE,
                "7d7da2c07cbd5207edc223b4a854885f30b584b3",
                "ba7a7ea29eb0d68077a51442691d201915470d16dca751dff3c214a7ead3c529",
            ),
            (
                observed.E1_MATERIALIZATION_SOURCE,
                "af4401cbcf2240df8523a36c0ff69a197fdfae4b",
                "2a6e627fcc95b532fead6619c3aa7d0a6f5781537206cddb2638c736c0856a24",
            ),
        )
        for path, blob, raw in expected:
            with self.subTest(path=path):
                self.assertEqual(git("rev-parse", f"HEAD:{path}"), blob)
                self.assertEqual(sha256(git("show", f"HEAD:{path}", binary=True)).hexdigest(), raw)
                self.assertEqual(git("status", "--porcelain", "--", path), "")

    def test_06_authorization_precedes_caller_metadata_and_normal_reads(self) -> None:
        argv: list[str] = []
        for name in (
            "feasibility-audit", "dependency-matrix", "common42-check", "dataset-manifest",
            "d1-data-access-audit", "executable-equivalence", "evidence-manifest",
            "train1", "train2", "private-destination", "local-locator-manifest",
            "public-receipt", "repository-root",
        ):
            argv.extend((f"--{name}", "independent"))
        argv.extend(("--execution-timestamp", "2026-08-19T00:00:00+09:00"))
        with mock.patch.object(
            observed,
            "load_committed_materialization_execution_authorization_r1",
            side_effect=observed.NormalOnlyAuthorityV1Error("independent stop"),
        ), mock.patch.object(observed, "_load_json_document") as metadata, mock.patch.object(
            observed, "load_verified_normal_features_v1"
        ) as values:
            with self.assertRaises(observed.NormalOnlyAuthorityV1Error):
                observed.main(argv)
            metadata.assert_not_called()
            values.assert_not_called()

    def test_07_caller_has_no_authorization_or_feature_choice_on_canonical_path(self) -> None:
        parameters = inspect.signature(observed.materialize_normal_only_authority_r1).parameters
        for prohibited in (
            "authorization", "authorization_path", "authorization_hash",
            "expected_builder_commit", "required_features",
        ):
            self.assertNotIn(prohibited, parameters)
        source = inspect.getsource(observed.materialize_normal_only_authority_r1)
        self.assertIn("load_committed_materialization_execution_authorization_r1", source)
        self.assertIn("_load_authorized_normal_features_r1", source)

    def test_08_scientific_functions_match_pre_interface_parent(self) -> None:
        parent_source = git(
            "show",
            "5c37e1604455de523e3eb5894fed9de92d42a9bf:" + SOURCE_PATH,
        )
        current_source = (ROOT / SOURCE_PATH).read_text(encoding="utf-8")
        names = {
            "build_common42_authority_v1",
            "new_reference_identity_v1",
            "derive_source_parameters_normal_only_v1",
            "derive_target_scale_normal_only_v1",
            "calibrate_all_role_values_v1",
        }

        def functions(text: str) -> dict[str, str]:
            lines = text.splitlines(keepends=True)
            result: dict[str, str] = {}
            for node in ast.parse(text).body:
                if isinstance(node, ast.FunctionDef) and node.name in names:
                    result[node.name] = "".join(lines[node.lineno - 1 : node.end_lineno])
            return result

        self.assertEqual(functions(parent_source), functions(current_source))
        self.assertEqual(observed.COMMON_RELATION_COUNT, 42)
        self.assertEqual(observed.UTILITY_NUMERIC_REFERENCE_COUNT, 420)
        self.assertFalse(observed.T2_UTILITY_SCOPE_AUTHORIZED)


if __name__ == "__main__":
    unittest.main()
