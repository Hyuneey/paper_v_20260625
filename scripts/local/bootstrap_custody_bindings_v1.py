"""Path-silent bootstrap for local-only custody bindings.

This helper persists only the approved machine-specific custody variables in
the Git-ignored ``.env.custody.local`` file.  It never discovers custody
assets, parses scientific data, or displays a binding value.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
import getpass
from hashlib import sha256
import os
from pathlib import Path
import shlex
import stat
import subprocess
import sys
import tempfile
from typing import NoReturn, TextIO


ENV_FILE_NAME = ".env.custody.local"
HAI_DATA_ROOT_KEY = "HAI_DATA_ROOT"
MAIN_REGISTRY_KEY = "TASK039E3_UTILITY_NORMAL_ONLY_AUTHORITY_V1"
MAIN_LOCATOR_KEY = "TASK039E3_UTILITY_NORMAL_ONLY_AUTHORITY_V1_LOCATOR"
SUPPLEMENT_REGISTRY_KEY = "TASK039E3_UTILITY_SOURCE_CENSUS_SUPPLEMENT_V1"
SUPPLEMENT_LOCATOR_KEY = (
    "TASK039E3_UTILITY_SOURCE_CENSUS_SUPPLEMENT_V1_LOCATOR"
)
ALLOWED_KEYS = (
    HAI_DATA_ROOT_KEY,
    MAIN_REGISTRY_KEY,
    MAIN_LOCATOR_KEY,
    SUPPLEMENT_REGISTRY_KEY,
    SUPPLEMENT_LOCATOR_KEY,
)

EXPECTED_TEST1_FEATURE_SHA256 = (
    "78c7f1d4de1f2ab9ccc2f8c719f80f831033543adb0c81d0d78f84f40838d4be"
)
EXPECTED_TEST1_LABEL_SHA256 = (
    "eaf69edb9c5834bc393afd7bf658b5e408d34fd7bfc3261f80516765fb818fbc"
)

INPUT_PROMPT = "Enter local HAI data root (input hidden): "
INPUT_REQUIRED = "LOCAL_BINDING_INPUT_REQUIRED"
INVALID_ROOT = "LOCAL_BINDING_BLOCKED_INVALID_HAI_ROOT"
TEST1_HASH_MISMATCH = "LOCAL_BINDING_BLOCKED_TEST1_HASH_MISMATCH"
GITIGNORE_REQUIRED = "LOCAL_BINDING_BLOCKED_GITIGNORE_REQUIRED"
ENV_FILE_INVALID = "LOCAL_BINDING_BLOCKED_ENV_FILE"
PERMISSION_FAILURE = "LOCAL_BINDING_BLOCKED_PERMISSIONS"
UNEXPECTED_FAILURE = "LOCAL_BINDING_BLOCKED_UNEXPECTED"

_FAILURE_CODES = frozenset(
    {
        INPUT_REQUIRED,
        INVALID_ROOT,
        TEST1_HASH_MISMATCH,
        GITIGNORE_REQUIRED,
        ENV_FILE_INVALID,
        PERMISSION_FAILURE,
        UNEXPECTED_FAILURE,
    }
)


class LocalCustodyBindingBootstrapError(RuntimeError):
    """A path-redacted, fixed-code bootstrap failure."""

    def __init__(self, code: str) -> None:
        if code not in _FAILURE_CODES:
            code = UNEXPECTED_FAILURE
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class Test1CustodyCheck:
    root: Path
    feature_hash_match: bool
    label_hash_match: bool


@dataclass(frozen=True)
class LocalBindingBootstrapResult:
    hai_data_root_configured: bool
    test1_feature_hash_match: bool
    test1_label_hash_match: bool
    test2_reads: int
    private_paths_emitted: int
    private_numeric_values_exposed: int
    local_binding_permissions: bool
    optional_main_registry_binding_present: bool
    optional_main_locator_binding_present: bool
    optional_supplement_registry_binding_present: bool
    optional_supplement_locator_binding_present: bool


def _raise(code: str) -> NoReturn:
    raise LocalCustodyBindingBootstrapError(code)


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_hai_data_root(
    raw_value: str,
    *,
    expected_feature_sha256: str = EXPECTED_TEST1_FEATURE_SHA256,
    expected_label_sha256: str = EXPECTED_TEST1_LABEL_SHA256,
    hash_file: Callable[[Path], str] = _sha256_file,
) -> Test1CustodyCheck:
    """Validate only the authorized test1 assets and return no path output."""

    if not isinstance(raw_value, str) or not raw_value.strip():
        _raise(INVALID_ROOT)
    try:
        supplied = Path(raw_value).expanduser()
        if supplied.is_symlink() or not supplied.exists() or not supplied.is_dir():
            _raise(INVALID_ROOT)
        root = supplied.resolve(strict=True)
        edition = root / "hai-23.05"
        if edition.is_symlink() or not edition.is_dir():
            _raise(INVALID_ROOT)
        feature = edition / "hai-test1.csv"
        label = edition / "label-test1.csv"
        if feature.is_symlink() or not feature.is_file():
            _raise(INVALID_ROOT)
        if label.is_symlink() or not label.is_file():
            _raise(INVALID_ROOT)
        feature_match = hash_file(feature) == expected_feature_sha256
        label_match = hash_file(label) == expected_label_sha256
    except LocalCustodyBindingBootstrapError:
        raise
    except BaseException:
        _raise(INVALID_ROOT)
    if not feature_match or not label_match:
        _raise(TEST1_HASH_MISMATCH)
    return Test1CustodyCheck(
        root=root,
        feature_hash_match=True,
        label_hash_match=True,
    )


def _shell_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def _serialize_env(values: Mapping[str, str]) -> str:
    if set(values) - set(ALLOWED_KEYS) or HAI_DATA_ROOT_KEY not in values:
        _raise(ENV_FILE_INVALID)
    lines: list[str] = []
    for key in ALLOWED_KEYS:
        if key not in values:
            continue
        value = values[key]
        if not isinstance(value, str) or not value:
            _raise(ENV_FILE_INVALID)
        lines.append(f"{key}={_shell_quote(value)}")
    return "\n".join(lines) + "\n"


def _parse_env_text(text: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for raw_line in text.splitlines():
        if not raw_line.strip():
            continue
        try:
            tokens = shlex.split(raw_line, comments=False, posix=True)
        except BaseException:
            _raise(ENV_FILE_INVALID)
        if len(tokens) != 1 or "=" not in tokens[0]:
            _raise(ENV_FILE_INVALID)
        key, value = tokens[0].split("=", 1)
        if key not in ALLOWED_KEYS or key in parsed or not value:
            _raise(ENV_FILE_INVALID)
        parsed[key] = value
    if HAI_DATA_ROOT_KEY not in parsed:
        _raise(ENV_FILE_INVALID)
    return parsed


def _read_env_file(path: Path) -> dict[str, str]:
    try:
        return _parse_env_text(path.read_text(encoding="utf-8"))
    except LocalCustodyBindingBootstrapError:
        raise
    except BaseException:
        _raise(ENV_FILE_INVALID)


def _apply_permission_policy(path: Path) -> bool:
    """Apply the narrowest practical stdlib-only local permission policy."""

    try:
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
        if os.name == "posix":
            return stat.S_IMODE(path.stat().st_mode) == 0o600
        return path.is_file()
    except BaseException:
        return False


def _write_env_file(path: Path, values: Mapping[str, str]) -> None:
    payload = _serialize_env(values)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            prefix=f"{ENV_FILE_NAME}.",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as stream:
            temporary_name = stream.name
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        temporary = Path(temporary_name)
        if not _apply_permission_policy(temporary):
            _raise(PERMISSION_FAILURE)
        os.replace(temporary, path)
        temporary_name = None
        if not _apply_permission_policy(path):
            _raise(PERMISSION_FAILURE)
    except LocalCustodyBindingBootstrapError:
        raise
    except BaseException:
        _raise(ENV_FILE_INVALID)
    finally:
        if temporary_name is not None:
            try:
                Path(temporary_name).unlink(missing_ok=True)
            except BaseException:
                pass


def _gitignored(repo_root: Path) -> bool:
    try:
        completed = subprocess.run(
            ["git", "check-ignore", "-q", ENV_FILE_NAME],
            cwd=repo_root,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return completed.returncode == 0
    except BaseException:
        return False


def _binding_values(
    environ: Mapping[str, str],
    root: Path,
) -> dict[str, str]:
    values = {HAI_DATA_ROOT_KEY: str(root)}
    for key in ALLOWED_KEYS[1:]:
        value = environ.get(key)
        if isinstance(value, str) and value:
            values[key] = value
    return values


def run_bootstrap(
    repo_root: Path,
    *,
    environ: Mapping[str, str],
    interactive_allowed: bool,
    hidden_prompt: Callable[[str], str] = getpass.getpass,
    expected_feature_sha256: str = EXPECTED_TEST1_FEATURE_SHA256,
    expected_label_sha256: str = EXPECTED_TEST1_LABEL_SHA256,
    check_ignored: Callable[[Path], bool] = _gitignored,
) -> LocalBindingBootstrapResult:
    """Run the local bootstrap without emitting any dynamic value."""

    env_path = repo_root / ENV_FILE_NAME
    if not check_ignored(repo_root):
        _raise(GITIGNORE_REQUIRED)

    raw_root = environ.get(HAI_DATA_ROOT_KEY)
    if not raw_root:
        if not interactive_allowed:
            _raise(INPUT_REQUIRED)
        try:
            raw_root = hidden_prompt(INPUT_PROMPT)
        except BaseException:
            _raise(INPUT_REQUIRED)

    first_check = validate_hai_data_root(
        raw_root,
        expected_feature_sha256=expected_feature_sha256,
        expected_label_sha256=expected_label_sha256,
    )
    values = _binding_values(environ, first_check.root)
    _write_env_file(env_path, values)

    reloaded = _read_env_file(env_path)
    if reloaded != values or set(reloaded) - set(ALLOWED_KEYS):
        _raise(ENV_FILE_INVALID)
    second_check = validate_hai_data_root(
        reloaded[HAI_DATA_ROOT_KEY],
        expected_feature_sha256=expected_feature_sha256,
        expected_label_sha256=expected_label_sha256,
    )
    permissions_ok = _apply_permission_policy(env_path)
    if not permissions_ok:
        _raise(PERMISSION_FAILURE)

    return LocalBindingBootstrapResult(
        hai_data_root_configured=True,
        test1_feature_hash_match=second_check.feature_hash_match,
        test1_label_hash_match=second_check.label_hash_match,
        test2_reads=0,
        private_paths_emitted=0,
        private_numeric_values_exposed=0,
        local_binding_permissions=True,
        optional_main_registry_binding_present=MAIN_REGISTRY_KEY in reloaded,
        optional_main_locator_binding_present=MAIN_LOCATOR_KEY in reloaded,
        optional_supplement_registry_binding_present=(
            SUPPLEMENT_REGISTRY_KEY in reloaded
        ),
        optional_supplement_locator_binding_present=(
            SUPPLEMENT_LOCATOR_KEY in reloaded
        ),
    )


def _emit_success(result: LocalBindingBootstrapResult, output: TextIO) -> None:
    lines = (
        "local_binding_bootstrap = PASS",
        "hai_data_root_configured = true",
        "test1_feature_hash_match = true",
        "test1_label_hash_match = true",
        f"test2_reads = {result.test2_reads}",
        f"private_paths_emitted = {result.private_paths_emitted}",
        (
            "private_numeric_values_exposed = "
            f"{result.private_numeric_values_exposed}"
        ),
        "local_binding_permissions = PASS",
        (
            "optional_main_registry_binding_present = "
            f"{str(result.optional_main_registry_binding_present).lower()}"
        ),
        (
            "optional_main_locator_binding_present = "
            f"{str(result.optional_main_locator_binding_present).lower()}"
        ),
        (
            "optional_supplement_registry_binding_present = "
            f"{str(result.optional_supplement_registry_binding_present).lower()}"
        ),
        (
            "optional_supplement_locator_binding_present = "
            f"{str(result.optional_supplement_locator_binding_present).lower()}"
        ),
    )
    output.write("\n".join(lines) + "\n")


def main() -> int:
    sys.tracebacklimit = 0
    try:
        repo_root = Path(__file__).resolve().parents[2]
        result = run_bootstrap(
            repo_root,
            environ=os.environ,
            interactive_allowed=bool(sys.stdin and sys.stdin.isatty()),
        )
    except LocalCustodyBindingBootstrapError as failure:
        sys.stdout.write(failure.code + "\n")
        return 2
    except BaseException:
        sys.stdout.write(UNEXPECTED_FAILURE + "\n")
        return 2
    _emit_success(result, sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
