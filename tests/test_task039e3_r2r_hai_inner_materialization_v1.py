from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from hashlib import sha256
import importlib.util
from io import StringIO
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "local" / "materialize_hai_inner_payload_v1.py"
SPEC = importlib.util.spec_from_file_location(
    "materialize_hai_inner_payload_v1", MODULE_PATH
)
assert SPEC is not None and SPEC.loader is not None
subject = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = subject
SPEC.loader.exec_module(subject)


FEATURE_BYTES = b"synthetic feature payload\n"
LABEL_BYTES = b"synthetic label payload\n"
SYNTHETIC_FEATURE = subject.PayloadSpec(
    subject.FEATURE_RELATIVE_PATH,
    sha256(FEATURE_BYTES).hexdigest(),
    len(FEATURE_BYTES),
)
SYNTHETIC_LABEL = subject.PayloadSpec(
    subject.LABEL_RELATIVE_PATH,
    sha256(LABEL_BYTES).hexdigest(),
    len(LABEL_BYTES),
)


def _write_payload(root: Path, spec: subject.PayloadSpec, content: bytes) -> None:
    path = root / Path(*subject.PurePosixPath(spec.relative_path).parts)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def _result(cache_root: Path) -> subject.HAIInnerMaterializationResult:
    return subject.HAIInnerMaterializationResult(
        cache_root=cache_root,
        official_source_match=True,
        pinned_commit_match=True,
        acquisition_route=subject.ROUTE_GIT_LFS,
        git_lfs_available=True,
        existing_cache_reused=False,
        test1_feature_materialized=True,
        test1_label_materialized=True,
        test1_feature_hash_match=True,
        test1_label_hash_match=True,
        test1_feature_size_match=True,
        test1_label_size_match=True,
        official_git_fetches=1,
        official_lfs_test1_fetches=1,
        official_lfs_label_test1_fetches=1,
        official_distribution_test1_fetches=0,
        official_distribution_label_test1_fetches=0,
        test2_lfs_payload_fetches=0,
        test2_file_opens=0,
        test2_hashes=0,
        scientific_feature_parses=0,
        scientific_label_parses=0,
        attack_event_derivations=0,
        rule_executions=0,
        metric_computations=0,
        private_paths_emitted=0,
    )


class TestHAIInnerMaterializationV1(unittest.TestCase):
    def test_correct_source_required(self) -> None:
        subject.require_official_source(subject.OFFICIAL_REPOSITORY)
        with self.assertRaises(subject.HAIInnerMaterializationError) as raised:
            subject.require_official_source("https://example.invalid/hai")
        self.assertEqual(raised.exception.code, subject.BLOCKED_SOURCE)

    def test_moving_ref_rejected(self) -> None:
        with self.assertRaises(subject.HAIInnerMaterializationError) as raised:
            subject.require_pinned_revision("main")
        self.assertEqual(raised.exception.code, subject.BLOCKED_PINNED_COMMIT)

    def test_wrong_commit_rejected(self) -> None:
        with self.assertRaises(subject.HAIInnerMaterializationError) as raised:
            subject.require_pinned_revision("0" * 40)
        self.assertEqual(raised.exception.code, subject.BLOCKED_PINNED_COMMIT)

    def test_test1_only_include_policy(self) -> None:
        commands = (
            subject.lfs_fetch_arguments(subject.FEATURE_SPEC),
            subject.lfs_fetch_arguments(subject.LABEL_SPEC),
        )
        includes = {item[3].removeprefix("--include=") for item in commands}
        self.assertEqual(includes, set(subject.AUTHORIZED_PAYLOADS))
        self.assertFalse(any("test2" in part for command in commands for part in command))

    def test_test2_payload_excluded(self) -> None:
        with self.assertRaises(subject.HAIInnerMaterializationError) as raised:
            subject.require_authorized_payload("hai-23.05/hai-test2.csv")
        self.assertEqual(raised.exception.code, subject.BLOCKED_PATH_GUARD)

    def test_wrong_feature_hash_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _write_payload(root, SYNTHETIC_FEATURE, b"wrong feature\n")
            with self.assertRaises(subject.HAIInnerMaterializationError) as raised:
                subject.validate_payload(root, SYNTHETIC_FEATURE)
        self.assertEqual(raised.exception.code, subject.BLOCKED_CUSTODY)

    def test_wrong_label_hash_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _write_payload(root, SYNTHETIC_LABEL, b"wrong label\n")
            with self.assertRaises(subject.HAIInnerMaterializationError) as raised:
                subject.validate_payload(root, SYNTHETIC_LABEL)
        self.assertEqual(raised.exception.code, subject.BLOCKED_CUSTODY)

    def test_wrong_feature_size_rejected(self) -> None:
        wrong = subject.PayloadSpec(
            SYNTHETIC_FEATURE.relative_path,
            SYNTHETIC_FEATURE.sha256,
            SYNTHETIC_FEATURE.size_bytes + 1,
        )
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _write_payload(root, SYNTHETIC_FEATURE, FEATURE_BYTES)
            with self.assertRaises(subject.HAIInnerMaterializationError) as raised:
                subject.validate_payload(root, wrong)
        self.assertEqual(raised.exception.code, subject.BLOCKED_CUSTODY)

    def test_wrong_label_size_rejected(self) -> None:
        wrong = subject.PayloadSpec(
            SYNTHETIC_LABEL.relative_path,
            SYNTHETIC_LABEL.sha256,
            SYNTHETIC_LABEL.size_bytes + 1,
        )
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _write_payload(root, SYNTHETIC_LABEL, LABEL_BYTES)
            with self.assertRaises(subject.HAIInnerMaterializationError) as raised:
                subject.validate_payload(root, wrong)
        self.assertEqual(raised.exception.code, subject.BLOCKED_CUSTODY)

    def test_private_path_not_output(self) -> None:
        private_marker = "private-cache-marker"
        output = StringIO()
        subject._emit_success(_result(Path(private_marker)), output)
        self.assertNotIn(private_marker, output.getvalue())
        self.assertIn("private_paths_emitted = 0", output.getvalue())

    def test_sanitized_state_excludes_cache_root(self) -> None:
        private_marker = "private-cache-marker"
        payload = _result(Path(private_marker)).sanitized_payload()
        self.assertNotIn("cache_root", payload)
        self.assertNotIn(private_marker, str(payload))

    def test_frozen_fallback_authority_replays(self) -> None:
        metadata, hosts = subject._load_fallback_authority(ROOT)
        self.assertEqual(metadata["artifact_hash"], subject.TASK039AR_METADATA_HASH)
        self.assertEqual(set(hosts), {"www.kaggle.com", "storage.googleapis.com"})

    def test_exception_path_redaction(self) -> None:
        output = StringIO()
        with mock.patch.object(
            subject,
            "run",
            side_effect=RuntimeError("private-cache-marker"),
        ):
            with redirect_stdout(output), redirect_stderr(StringIO()):
                status = subject.main()
        self.assertEqual(status, 2)
        self.assertEqual(output.getvalue(), subject.BLOCKED_UNEXPECTED + "\n")
        self.assertNotIn("private-cache-marker", output.getvalue())

    def test_cache_outside_repository_requirement(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repository = Path(temp) / "repository"
            repository.mkdir()
            inside = repository / "private-cache"
            outside = Path(temp) / "private-cache"
            with self.assertRaises(subject.HAIInnerMaterializationError) as raised:
                subject.require_cache_outside_repository(inside, repository)
            self.assertEqual(raised.exception.code, subject.BLOCKED_PATH_GUARD)
            subject.require_cache_outside_repository(outside, repository)

    def test_existing_valid_cache_reuse(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            cache = Path(temp) / "cache"
            (cache / ".official.git").mkdir(parents=True)
            _write_payload(cache, SYNTHETIC_FEATURE, FEATURE_BYTES)
            _write_payload(cache, SYNTHETIC_LABEL, LABEL_BYTES)

            def runner(arguments, cwd, environment):
                if tuple(arguments) == ("git", "remote", "get-url", "origin"):
                    return subject.CommandResult(0, subject.OFFICIAL_REPOSITORY.encode())
                if tuple(arguments) == ("git", "rev-parse", "HEAD"):
                    return subject.CommandResult(0, subject.PINNED_COMMIT.encode())
                return subject.CommandResult(1)

            subject._validate_existing_cache(
                cache,
                runner=runner,
                specs=(SYNTHETIC_FEATURE, SYNTHETIC_LABEL),
            )

    def test_noncanonical_cache_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            cache = Path(temp) / "cache"
            (cache / ".official.git").mkdir(parents=True)
            _write_payload(cache, SYNTHETIC_FEATURE, FEATURE_BYTES)
            _write_payload(cache, SYNTHETIC_LABEL, LABEL_BYTES)

            def runner(arguments, cwd, environment):
                if tuple(arguments) == ("git", "remote", "get-url", "origin"):
                    return subject.CommandResult(0, b"https://example.invalid/hai")
                return subject.CommandResult(0, subject.PINNED_COMMIT.encode())

            with self.assertRaises(subject.HAIInnerMaterializationError) as raised:
                subject._validate_existing_cache(
                    cache,
                    runner=runner,
                    specs=(SYNTHETIC_FEATURE, SYNTHETIC_LABEL),
                )
        self.assertEqual(raised.exception.code, subject.BLOCKED_CACHE)

    def test_env_file_write_without_path_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repository = Path(temp) / "repository"
            cache = Path(temp) / "cache"
            repository.mkdir()
            cache.mkdir()
            helper = subject._load_binding_helper()
            helper.validate_hai_data_root = lambda value: None
            private_marker = str(cache)
            output = StringIO()
            with redirect_stdout(output), redirect_stderr(StringIO()):
                observed = subject.persist_hai_binding(
                    repository,
                    _result(cache),
                    environ={
                        helper.MAIN_REGISTRY_KEY: "synthetic-main-binding",
                        "UNRELATED_SECRET": "must-not-copy",
                    },
                    ignored_check=lambda _: True,
                    tracked_check=lambda _: False,
                    binding_helper=helper,
                )
            content = (repository / helper.ENV_FILE_NAME).read_text(encoding="utf-8")
        self.assertTrue(observed.local_binding_configured)
        self.assertEqual(output.getvalue(), "")
        self.assertNotIn(private_marker, output.getvalue())
        self.assertIn(helper.HAI_DATA_ROOT_KEY, content)
        self.assertIn(helper.MAIN_REGISTRY_KEY, content)
        self.assertNotIn("UNRELATED_SECRET", content)
        self.assertNotIn("must-not-copy", content)


if __name__ == "__main__":
    unittest.main()
