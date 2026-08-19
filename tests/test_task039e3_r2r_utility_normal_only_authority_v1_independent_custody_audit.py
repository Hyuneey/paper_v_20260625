from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

from paperworks.v6.common import stable_hash_v1
import paperworks.v6.task039e3_r2r_utility_normal_only_authority_v1 as subject


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs" / "task_reports"
AUDITED_BUILDER_COMMIT = "d58757b63d21519bc39398ddcf96be1682e8b01a"
TIMESTAMP = "2026-08-19T12:00:00+09:00"


def load(name: str) -> dict[str, object]:
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


def rehash(document: dict[str, object]) -> None:
    document["artifact_hash"] = stable_hash_v1(
        {key: value for key, value in document.items() if key != "artifact_hash"}
    )


def small_identity(path: Path, role: str, rows: int) -> subject.NormalInputIdentityV1:
    header = path.read_bytes().splitlines(keepends=True)[0]
    return subject.NormalInputIdentityV1(
        logical_role=role,
        relative_path=f"hai-23.05/{path.name}",
        sha256=sha256(path.read_bytes()).hexdigest(),
        byte_size=path.stat().st_size,
        row_count=rows,
        header_sha256=sha256(header).hexdigest(),
    )


class IndependentCustodyAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.authority = subject.build_common42_authority_v1(
            load("TASK-039E3_R2R_UTILITY_PROTOCOL_EXECUTABLE_EQUIVALENCE.json"),
            load("TASK-039E1_CONSTRUCTION_EVIDENCE_MANIFEST.json"),
        )
        windows: dict[str, int | float] = {
            "source_pre_window_seconds": 5,
            "source_post_window_seconds": 5,
            "minimum_source_stability_fraction": 0.8,
            "source_refractory_seconds": 10,
            "cross_source_isolation_radius_seconds": 2,
            "target_baseline_window_seconds": 5,
            "target_response_window_seconds": 3,
        }
        values: dict[tuple[str, str], int | float] = {}
        for relation in cls.authority.relations:
            for role in subject.UTILITY_NUMERIC_ROLES:
                if role == "source_step_threshold":
                    value: int | float = 2.0
                elif role == "source_stability_tolerance":
                    value = 0.2
                elif role == "target_noise_scale":
                    value = 0.1
                else:
                    value = windows[role]
                values[(relation.relation_binding_hash, role)] = value
        cls.registry = subject.build_private_registry_document_v1(cls.authority, values)

    def test_both_identity_preflights_precede_either_parser_and_postchecks_follow(self) -> None:
        calls: list[str] = []

        def verify(_path: Path, expected: subject.NormalInputIdentityV1) -> None:
            calls.append(f"verify:{expected.logical_role}")

        def read(path: Path, _features: frozenset[str], _rows: int) -> dict[str, tuple[float, ...]]:
            calls.append(f"parse:{path.name}")
            return {"P1_FCV01D": (1.0,)}

        with mock.patch.object(subject, "verify_normal_input_file_v1", side_effect=verify), mock.patch.object(
            subject, "_read_verified_feature_columns", side_effect=read
        ):
            subject.load_verified_normal_features_v1(
                train1_path=Path("hai-train1.csv"),
                train2_path=Path("hai-train2.csv"),
                required_features=frozenset({"P1_FCV01D"}),
            )
        self.assertEqual(
            calls,
            [
                "verify:normal_train1",
                "verify:normal_train2",
                "parse:hai-train1.csv",
                "parse:hai-train2.csv",
                "verify:normal_train1",
                "verify:normal_train2",
            ],
        )

    def test_wrong_train1_size_hash_and_train2_hash_allow_zero_value_reads(self) -> None:
        def exercise(fail_at: int) -> None:
            verify_calls = 0

            def verify(_path: Path, _expected: subject.NormalInputIdentityV1) -> None:
                nonlocal verify_calls
                verify_calls += 1
                if verify_calls == fail_at:
                    raise subject.NormalOnlyAuthorityV1Error("independent identity mismatch")

            with mock.patch.object(subject, "verify_normal_input_file_v1", side_effect=verify), mock.patch.object(
                subject, "_read_verified_feature_columns"
            ) as reader:
                with self.assertRaises(subject.NormalOnlyAuthorityV1Error):
                    subject.load_verified_normal_features_v1(
                        train1_path=Path("hai-train1.csv"),
                        train2_path=Path("hai-train2.csv"),
                        required_features=frozenset({"P1_FCV01D"}),
                    )
                reader.assert_not_called()

        for failure_name, call in (("train1_size_or_hash", 1), ("train2_hash", 2)):
            with self.subTest(failure=failure_name):
                exercise(call)

    def test_synthetic_exact_files_parse_and_post_read_mutation_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            train1 = root / "hai-train1.csv"
            train2 = root / "hai-train2.csv"
            train1.write_text("P1_FCV01D\n1.0\n2.0\n", encoding="utf-8", newline="")
            train2.write_text("P1_FCV01D\n3.0\n4.0\n", encoding="utf-8", newline="")
            identity1 = small_identity(train1, "normal_train1", 2)
            identity2 = small_identity(train2, "normal_train2", 2)
            with mock.patch.object(subject, "NORMAL_TRAIN1_IDENTITY", identity1), mock.patch.object(
                subject, "NORMAL_TRAIN2_IDENTITY", identity2
            ):
                observed1, observed2 = subject.load_verified_normal_features_v1(
                    train1_path=train1,
                    train2_path=train2,
                    required_features=frozenset({"P1_FCV01D"}),
                )
                self.assertEqual(observed1["P1_FCV01D"], (1.0, 2.0))
                self.assertEqual(observed2["P1_FCV01D"], (3.0, 4.0))

                original_reader = subject._read_verified_feature_columns
                read_count = 0

                def mutate_after_read(path: Path, features: frozenset[str], rows: int):
                    nonlocal read_count
                    result = original_reader(path, features, rows)
                    read_count += 1
                    if read_count == 1:
                        data = path.read_bytes()
                        path.write_bytes(data.replace(b"1.0", b"9.0", 1))
                    return result

                with mock.patch.object(subject, "_read_verified_feature_columns", side_effect=mutate_after_read):
                    with self.assertRaises(subject.NormalOnlyAuthorityV1Error):
                        subject.load_verified_normal_features_v1(
                            train1_path=train1,
                            train2_path=train2,
                            required_features=frozenset({"P1_FCV01D"}),
                        )

    def test_csv_header_row_and_token_closure_is_strict(self) -> None:
        fixtures = {
            "missing_feature": "OTHER\n1\n",
            "duplicate_header": "P1_FCV01D,P1_FCV01D\n1,1\n",
            "missing_token": "P1_FCV01D\n\n",
            "nonnumeric": "P1_FCV01D\nabc\n",
            "nonfinite": "P1_FCV01D\nNaN\n",
            "wrong_rows": "P1_FCV01D\n1\n",
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, content in fixtures.items():
                path = root / f"{name}.csv"
                path.write_text(content, encoding="utf-8", newline="")
                with self.subTest(name=name), self.assertRaises(subject.NormalOnlyAuthorityV1Error):
                    subject._read_verified_feature_columns(path, frozenset({"P1_FCV01D"}), 2)

    def test_explicit_private_locator_and_path_separation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            private = root / "private.json"
            locator = root / "locator.json"
            receipt = root / "receipt.json"
            kwargs = dict(
                registry=self.registry,
                authority=self.authority,
                private_destination=private,
                local_locator_manifest=locator,
                public_receipt_path=receipt,
                repository_root=ROOT,
                builder_commit=AUDITED_BUILDER_COMMIT,
                builder_git_blob="b" * 40,
                builder_source_sha256="c" * 64,
                execution_timestamp=TIMESTAMP,
            )
            for env in ({}, {subject.PRIVATE_LOCATOR_ENV: str(root / "other.json")}):
                with self.subTest(env=bool(env)), mock.patch.dict(os.environ, env, clear=True), self.assertRaises(subject.NormalOnlyAuthorityV1Error):
                    subject.finalize_materialization_atomically_v1(**kwargs)
            with mock.patch.dict(os.environ, {subject.PRIVATE_LOCATOR_ENV: str(private)}):
                for field, value in (
                    ("private_destination", ROOT / "inside-private.json"),
                    ("local_locator_manifest", ROOT / "inside-locator.json"),
                    ("local_locator_manifest", private),
                    ("public_receipt_path", private),
                ):
                    changed = dict(kwargs)
                    changed[field] = value
                    with self.subTest(field=field, value=str(value)), self.assertRaises(subject.NormalOnlyAuthorityV1Error):
                        subject.finalize_materialization_atomically_v1(**changed)

    def test_locator_must_be_validated_before_any_normal_value_parse(self) -> None:
        """The explicit destination is a pre-read authority gate, not a finalization detail."""

        authority = self.authority
        with tempfile.TemporaryDirectory() as directory, mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(
            subject, "validate_route_c_bindings_v1"
        ), mock.patch.object(subject, "validate_normal_input_authorities_v1"), mock.patch.object(
            subject, "build_common42_authority_v1", return_value=authority
        ), mock.patch.object(
            subject, "verify_builder_checkout_v1", return_value=("b" * 40, "c" * 64)
        ), mock.patch.object(
            subject,
            "load_verified_normal_features_v1",
            side_effect=AssertionError("scientific values parsed before locator validation"),
        ) as loader:
            root = Path(directory)
            with self.assertRaises(subject.NormalOnlyAuthorityV1Error):
                subject.materialize_normal_only_authority_v1(
                    feasibility_audit={},
                    dependency_matrix={},
                    common42_check={},
                    dataset_manifest={},
                    d1_data_access_audit={},
                    executable_equivalence={},
                    evidence_manifest={},
                    train1_path=root / "hai-train1.csv",
                    train2_path=root / "hai-train2.csv",
                    private_destination=root / "private.json",
                    local_locator_manifest=root / "locator.json",
                    public_receipt_path=root / "receipt.json",
                    repository_root=ROOT,
                    expected_builder_commit=AUDITED_BUILDER_COMMIT,
                    execution_timestamp=TIMESTAMP,
                )
            loader.assert_not_called()

    def _finalize_in(self, root: Path) -> tuple[Path, Path, Path]:
        private = root / "private.json"
        locator = root / "locator.json"
        receipt = root / "receipt.json"
        with mock.patch.dict(os.environ, {subject.PRIVATE_LOCATOR_ENV: str(private)}):
            subject.finalize_materialization_atomically_v1(
                registry=self.registry,
                authority=self.authority,
                private_destination=private,
                local_locator_manifest=locator,
                public_receipt_path=receipt,
                repository_root=ROOT,
                builder_commit=AUDITED_BUILDER_COMMIT,
                builder_git_blob="b" * 40,
                builder_source_sha256="c" * 64,
                execution_timestamp=TIMESTAMP,
            )
        return private, locator, receipt

    def test_atomic_write_order_and_failure_injection_never_writes_receipt_early(self) -> None:
        original_write = subject._atomic_json_write
        for fail_call in (1, 2, 3):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                private = root / "private.json"
                locator = root / "locator.json"
                receipt = root / "receipt.json"
                calls = 0

                def injected(path: Path, document, *, private: bool) -> None:
                    nonlocal calls
                    calls += 1
                    if calls == fail_call:
                        raise subject.NormalOnlyAuthorityV1Error("injected atomic stage failure")
                    original_write(path, document, private=private)

                with mock.patch.dict(os.environ, {subject.PRIVATE_LOCATOR_ENV: str(private)}), mock.patch.object(
                    subject, "_atomic_json_write", side_effect=injected
                ), self.assertRaises(subject.NormalOnlyAuthorityV1Error):
                    subject.finalize_materialization_atomically_v1(
                        registry=self.registry,
                        authority=self.authority,
                        private_destination=private,
                        local_locator_manifest=locator,
                        public_receipt_path=receipt,
                        repository_root=ROOT,
                        builder_commit=AUDITED_BUILDER_COMMIT,
                        builder_git_blob="b" * 40,
                        builder_source_sha256="c" * 64,
                        execution_timestamp=TIMESTAMP,
                    )
                self.assertFalse(receipt.exists())
                self.assertFalse(any(".partial-" in path.name for path in root.iterdir()))

    def test_public_receipt_schema_must_reject_disguised_numeric_leakage(self) -> None:
        receipt = subject.public_receipt_document_v1(
            authority=self.authority,
            private_registry_hash=str(self.registry["artifact_hash"]),
            builder_commit=AUDITED_BUILDER_COMMIT,
            builder_git_blob="b" * 40,
            builder_source_sha256="c" * 64,
            execution_timestamp=TIMESTAMP,
        )
        receipt["synthetic_threshold_preimage"] = 123.456
        rehash(receipt)
        with self.assertRaises(subject.NormalOnlyAuthorityV1Error):
            subject.validate_public_receipt_v1(receipt, self.authority)

    def test_final_validator_requires_locator_file_outside_git(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            external = Path(directory)
            private, locator, receipt = self._finalize_in(external)
            with tempfile.TemporaryDirectory(dir=ROOT) as inside_directory:
                inside_locator = Path(inside_directory) / "locator.json"
                shutil.copyfile(locator, inside_locator)
                with mock.patch.dict(os.environ, {subject.PRIVATE_LOCATOR_ENV: str(private)}), self.assertRaises(subject.NormalOnlyAuthorityV1Error):
                    subject.validate_finalized_authority_v1(
                        authority=self.authority,
                        private_destination=private,
                        local_locator_manifest=inside_locator,
                        public_receipt_path=receipt,
                        repository_root=ROOT,
                    )

    def test_final_validator_requires_locator_receipt_builder_cross_binding(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            private, locator, receipt = self._finalize_in(root)
            locator_document = json.loads(locator.read_text(encoding="utf-8"))
            locator_document["builder_commit"] = "e" * 40
            rehash(locator_document)
            locator.write_text(json.dumps(locator_document), encoding="utf-8")
            with mock.patch.dict(os.environ, {subject.PRIVATE_LOCATOR_ENV: str(private)}), self.assertRaises(subject.NormalOnlyAuthorityV1Error):
                subject.validate_finalized_authority_v1(
                    authority=self.authority,
                    private_destination=private,
                    local_locator_manifest=locator,
                    public_receipt_path=receipt,
                    repository_root=ROOT,
                )

    def test_builder_checkout_is_internally_pinned_to_audited_commit(self) -> None:
        """A caller must not self-authorize an arbitrary current HEAD."""

        arbitrary_head = "e" * 40
        completed = (
            subprocess.CompletedProcess([], 0, arbitrary_head + "\n", ""),
            subprocess.CompletedProcess([], 0, "b" * 40 + "\n", ""),
            subprocess.CompletedProcess([], 0, "", ""),
        )
        with mock.patch.object(subject.subprocess, "run", side_effect=completed), self.assertRaises(subject.NormalOnlyAuthorityV1Error):
            subject.verify_builder_checkout_v1(ROOT, expected_builder_commit=arbitrary_head)

    def test_exact_audited_builder_blob_and_source_bytes_are_frozen(self) -> None:
        relative = "src/paperworks/v6/task039e3_r2r_utility_normal_only_authority_v1.py"
        blob = subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", f"{AUDITED_BUILDER_COMMIT}:{relative}"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        frozen = subprocess.run(
            ["git", "-C", str(ROOT), "show", f"{AUDITED_BUILDER_COMMIT}:{relative}"],
            check=True,
            capture_output=True,
        ).stdout
        self.assertEqual(blob, "b071678a151161f9585301472f5eb23d7ce2c246")
        self.assertEqual(sha256(frozen).hexdigest(), "f18eceabd1f0f5aee7755bff964b985014411b6a0b98425e424863a59256b30e")


if __name__ == "__main__":
    unittest.main()
