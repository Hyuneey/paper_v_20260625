from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from hashlib import sha256
import importlib.util
from io import StringIO
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "local" / "bootstrap_custody_bindings_v1.py"
SPEC = importlib.util.spec_from_file_location("bootstrap_custody_bindings_v1", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
subject = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = subject
SPEC.loader.exec_module(subject)


FEATURE_BYTES = b"synthetic feature fixture\n"
LABEL_BYTES = b"synthetic label fixture\n"
FEATURE_SHA = sha256(FEATURE_BYTES).hexdigest()
LABEL_SHA = sha256(LABEL_BYTES).hexdigest()


class TestLocalCustodyBindingBootstrapV1(unittest.TestCase):
    def _make_root(
        self,
        base: Path,
        *,
        feature: bytes | None = FEATURE_BYTES,
        label: bytes | None = LABEL_BYTES,
    ) -> Path:
        root = base / "synthetic-custody"
        edition = root / "hai-23.05"
        edition.mkdir(parents=True)
        if feature is not None:
            (edition / "hai-test1.csv").write_bytes(feature)
        if label is not None:
            (edition / "label-test1.csv").write_bytes(label)
        return root

    def _run(
        self,
        repo: Path,
        root: Path,
        *,
        extra_env: dict[str, str] | None = None,
    ) -> subject.LocalBindingBootstrapResult:
        environ = {subject.HAI_DATA_ROOT_KEY: str(root)}
        if extra_env:
            environ.update(extra_env)
        return subject.run_bootstrap(
            repo,
            environ=environ,
            interactive_allowed=False,
            expected_feature_sha256=FEATURE_SHA,
            expected_label_sha256=LABEL_SHA,
            check_ignored=lambda _: True,
        )

    def test_env_file_path_is_gitignored(self) -> None:
        import subprocess

        completed = subprocess.run(
            ["git", "check-ignore", "-q", subject.ENV_FILE_NAME],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        self.assertEqual(completed.returncode, 0)

    def test_unexpected_keys_rejected(self) -> None:
        with self.assertRaises(subject.LocalCustodyBindingBootstrapError) as raised:
            subject._parse_env_text("HAI_DATA_ROOT='safe'\nAPI_TOKEN='secret'\n")
        self.assertEqual(raised.exception.code, subject.ENV_FILE_INVALID)

    def test_hai_root_missing_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            missing = Path(temp) / "absent"
            with self.assertRaises(subject.LocalCustodyBindingBootstrapError) as raised:
                subject.validate_hai_data_root(
                    str(missing),
                    expected_feature_sha256=FEATURE_SHA,
                    expected_label_sha256=LABEL_SHA,
                )
        self.assertEqual(raised.exception.code, subject.INVALID_ROOT)

    def test_hai_root_symlink_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            root = self._make_root(base)
            original = Path.is_symlink

            def is_symlink(path: Path) -> bool:
                if path == root:
                    return True
                return original(path)

            with mock.patch.object(Path, "is_symlink", is_symlink):
                with self.assertRaises(
                    subject.LocalCustodyBindingBootstrapError
                ) as raised:
                    subject.validate_hai_data_root(
                        str(root),
                        expected_feature_sha256=FEATURE_SHA,
                        expected_label_sha256=LABEL_SHA,
                    )
        self.assertEqual(raised.exception.code, subject.INVALID_ROOT)

    def test_missing_test1_feature_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = self._make_root(Path(temp), feature=None)
            with self.assertRaises(subject.LocalCustodyBindingBootstrapError) as raised:
                subject.validate_hai_data_root(
                    str(root),
                    expected_feature_sha256=FEATURE_SHA,
                    expected_label_sha256=LABEL_SHA,
                )
        self.assertEqual(raised.exception.code, subject.INVALID_ROOT)

    def test_missing_test1_label_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = self._make_root(Path(temp), label=None)
            with self.assertRaises(subject.LocalCustodyBindingBootstrapError) as raised:
                subject.validate_hai_data_root(
                    str(root),
                    expected_feature_sha256=FEATURE_SHA,
                    expected_label_sha256=LABEL_SHA,
                )
        self.assertEqual(raised.exception.code, subject.INVALID_ROOT)

    def test_wrong_feature_hash_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = self._make_root(Path(temp), feature=b"wrong")
            with self.assertRaises(subject.LocalCustodyBindingBootstrapError) as raised:
                subject.validate_hai_data_root(
                    str(root),
                    expected_feature_sha256=FEATURE_SHA,
                    expected_label_sha256=LABEL_SHA,
                )
        self.assertEqual(raised.exception.code, subject.TEST1_HASH_MISMATCH)

    def test_wrong_label_hash_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = self._make_root(Path(temp), label=b"wrong")
            with self.assertRaises(subject.LocalCustodyBindingBootstrapError) as raised:
                subject.validate_hai_data_root(
                    str(root),
                    expected_feature_sha256=FEATURE_SHA,
                    expected_label_sha256=LABEL_SHA,
                )
        self.assertEqual(raised.exception.code, subject.TEST1_HASH_MISMATCH)

    def test_test2_never_opened(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = self._make_root(Path(temp))
            opened: list[str] = []

            def hashing(path: Path) -> str:
                opened.append(path.name)
                return sha256(path.read_bytes()).hexdigest()

            subject.validate_hai_data_root(
                str(root),
                expected_feature_sha256=FEATURE_SHA,
                expected_label_sha256=LABEL_SHA,
                hash_file=hashing,
            )
        self.assertEqual(opened, ["hai-test1.csv", "label-test1.csv"])

    def test_values_never_printed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            root = self._make_root(repo)
            private_text = str(root)
            output = StringIO()
            errors = StringIO()
            with redirect_stdout(output), redirect_stderr(errors):
                result = self._run(repo, root)
                subject._emit_success(result, output)
            combined = output.getvalue() + errors.getvalue()
        self.assertNotIn(private_text, combined)
        self.assertIn("private_paths_emitted = 0", combined)

    def test_exception_path_redacted(self) -> None:
        output = StringIO()
        failure = RuntimeError("private-location-should-never-appear")
        with mock.patch.object(subject, "run_bootstrap", side_effect=failure):
            with mock.patch.object(subject.sys.stdin, "isatty", return_value=False):
                with redirect_stdout(output), redirect_stderr(StringIO()):
                    code = subject.main()
        self.assertEqual(code, 2)
        self.assertEqual(output.getvalue(), subject.UNEXPECTED_FAILURE + "\n")
        self.assertNotIn("private-location", output.getvalue())

    def test_chmod_permission_policy(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "local-binding"
            target.write_text("synthetic", encoding="utf-8")
            self.assertTrue(subject._apply_permission_policy(target))
            if os.name == "posix":
                self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o600)

    def test_env_file_reload(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            root = self._make_root(repo)
            self._run(repo, root)
            reloaded = subject._read_env_file(repo / subject.ENV_FILE_NAME)
        self.assertEqual(set(reloaded), {subject.HAI_DATA_ROOT_KEY})

    def test_existing_optional_private_bindings_preserved_internally(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            root = self._make_root(repo)
            optional = {
                subject.MAIN_REGISTRY_KEY: "synthetic-main",
                subject.MAIN_LOCATOR_KEY: "synthetic-main-locator",
                subject.SUPPLEMENT_REGISTRY_KEY: "synthetic-supplement",
                subject.SUPPLEMENT_LOCATOR_KEY: "synthetic-supplement-locator",
            }
            result = self._run(repo, root, extra_env=optional)
            reloaded = subject._read_env_file(repo / subject.ENV_FILE_NAME)
        self.assertEqual({key: reloaded[key] for key in optional}, optional)
        self.assertTrue(result.optional_main_registry_binding_present)
        self.assertTrue(result.optional_main_locator_binding_present)
        self.assertTrue(result.optional_supplement_registry_binding_present)
        self.assertTrue(result.optional_supplement_locator_binding_present)

    def test_unrelated_secrets_not_copied(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            root = self._make_root(repo)
            self._run(repo, root, extra_env={"API_TOKEN": "must-not-copy"})
            text = (repo / subject.ENV_FILE_NAME).read_text(encoding="utf-8")
        self.assertNotIn("API_TOKEN", text)
        self.assertNotIn("must-not-copy", text)

    def test_missing_interactive_input_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(subject.LocalCustodyBindingBootstrapError) as raised:
                subject.run_bootstrap(
                    Path(temp),
                    environ={},
                    interactive_allowed=False,
                    check_ignored=lambda _: True,
                )
        self.assertEqual(raised.exception.code, subject.INPUT_REQUIRED)

    def test_hidden_prompt_used_once(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            root = self._make_root(repo)
            prompts: list[str] = []

            def hidden(prompt: str) -> str:
                prompts.append(prompt)
                return str(root)

            subject.run_bootstrap(
                repo,
                environ={},
                interactive_allowed=True,
                hidden_prompt=hidden,
                expected_feature_sha256=FEATURE_SHA,
                expected_label_sha256=LABEL_SHA,
                check_ignored=lambda _: True,
            )
        self.assertEqual(prompts, [subject.INPUT_PROMPT])


if __name__ == "__main__":
    unittest.main()
