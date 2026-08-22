"""Path-redacted private custody boundary for one D2 recovery execution.

This module contains infrastructure only. It never imports the D2 execution
module and never reads predictions, labels, test data, or scientific values.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import secrets
from typing import Any, Mapping, NoReturn
import weakref


RECOVERY_CUSTODY_VERSION = "TASK039E3_R2R_D2_EXECUTION_RECOVERY_CUSTODY_V1"
RECOVERY_BINDING_KEY = "TASK039E3_D2_RECOVERY_PRIVATE_EVIDENCE_ROOT_V1"
RECOVERY_BINDING_FILE = ".env.d2_recovery_custody.local"
PRIVATE_ROOT_PERMISSION_POLICY = "OWNER_ONLY_WHERE_SUPPORTED_AND_SENTINEL_PROVEN"
SENTINEL_POLICY = "ATOMIC_CREATE_FSYNC_RENAME_REOPEN_DELETE_NO_RESIDUE_V1"
ALLOWED_PRIVATE_FILENAMES = frozenset({
    "task039e3_inner_d2_fusion_evidence_v1.json",
    "task039e3_inner_d2_metric_evidence_v1.json",
})
SANITIZED_FAILURE_CODES = frozenset({
    "D2_RECOVERY_PRIVATE_CUSTODY_ROOT_INVALID",
    "D2_RECOVERY_PRIVATE_CUSTODY_WRITE_DENIED",
    "D2_RECOVERY_PRIVATE_CUSTODY_TARGET_EXISTS",
    "D2_RECOVERY_PRIVATE_CUSTODY_SYMLINK_REJECTED",
    "D2_RECOVERY_PRIVATE_CUSTODY_ATOMIC_RENAME_FAILED",
    "D2_RECOVERY_PRIVATE_CUSTODY_RESIDUE_DETECTED",
    "D2_RECOVERY_PRIVATE_CUSTODY_UNEXPECTED",
})


def stable_hash_v1(value: Mapping[str, Any]) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=True, allow_nan=False).encode("utf-8")
    return sha256(raw).hexdigest()


RECOVERY_CUSTODY_MODULE_IDENTITY = stable_hash_v1({
    "version": RECOVERY_CUSTODY_VERSION,
    "binding_key": RECOVERY_BINDING_KEY,
    "permission_policy": PRIVATE_ROOT_PERMISSION_POLICY,
    "sentinel_policy": SENTINEL_POLICY,
    "allowed_private_filenames": sorted(ALLOWED_PRIVATE_FILENAMES),
    "failure_codes": sorted(SANITIZED_FAILURE_CODES),
    "scientific_functions": 0,
})
RECOVERY_CUSTODY_REMEDIATION_HASH = stable_hash_v1({
    "artifact_type": "D2RecoveryCustodyRemediationV1",
    "module_identity": RECOVERY_CUSTODY_MODULE_IDENTITY,
    "historical_root_cause": "PRIVATE_PARENT_PERMISSION_DENIED",
    "recovery_class": "PATH_REDACTION_AND_CUSTODY_RECOVERY",
})
PATH_REDACTION_AUDIT_IDENTITY = stable_hash_v1({
    "artifact_type": "D2RecoveryPathRedactionContractV1",
    "failure_codes": sorted(SANITIZED_FAILURE_CODES),
    "raw_exception_args_exposed": False,
    "raw_exception_string_exposed": False,
    "exception_chaining_exposed": False,
})


class D2RecoveryCustodyV1Error(RuntimeError):
    """A path-free recovery-custody failure."""

    def __init__(self, code: str) -> None:
        safe = code if code in SANITIZED_FAILURE_CODES else "D2_RECOVERY_PRIVATE_CUSTODY_UNEXPECTED"
        self.code = safe
        super().__init__(safe)

    def __repr__(self) -> str:
        return f"D2RecoveryCustodyV1Error({self.code!r})"


def _fail(code: str) -> NoReturn:
    raise D2RecoveryCustodyV1Error(code) from None


def _repository_root_v1() -> Path:
    return Path(__file__).resolve().parents[3]


@dataclass(frozen=True, repr=False)
class D2RecoveryPrivateRootV1:
    custody_version: str
    module_identity: str
    outside_git: bool
    symlink: bool
    permission_policy: str
    _path: Path = field(repr=False, compare=False)

    def __repr__(self) -> str:
        return "<D2RecoveryPrivateRootV1 validated=True path=REDACTED>"

    def __reduce__(self) -> object:
        _fail("D2_RECOVERY_PRIVATE_CUSTODY_ROOT_INVALID")


_ISSUED_ROOTS: dict[int, tuple[weakref.ReferenceType[D2RecoveryPrivateRootV1], str]] = {}


def _issue_root_v1(path: Path, repository: Path) -> D2RecoveryPrivateRootV1:
    try:
        root = path.resolve(strict=True)
        repo = repository.resolve(strict=True)
        if path.is_symlink() or root.is_symlink():
            _fail("D2_RECOVERY_PRIVATE_CUSTODY_SYMLINK_REJECTED")
        if not root.is_dir() or root == repo or repo in root.parents:
            _fail("D2_RECOVERY_PRIVATE_CUSTODY_ROOT_INVALID")
        value = D2RecoveryPrivateRootV1(
            RECOVERY_CUSTODY_VERSION, RECOVERY_CUSTODY_MODULE_IDENTITY,
            True, False, PRIVATE_ROOT_PERMISSION_POLICY, root,
        )
        oid = id(value)
        _ISSUED_ROOTS[oid] = (weakref.ref(value, lambda _: _ISSUED_ROOTS.pop(oid, None)), str(root))
        return value
    except D2RecoveryCustodyV1Error:
        raise
    except BaseException:
        _fail("D2_RECOVERY_PRIVATE_CUSTODY_ROOT_INVALID")


def _validate_root_v1(value: D2RecoveryPrivateRootV1) -> Path:
    issued = _ISSUED_ROOTS.get(id(value))
    if (type(value) is not D2RecoveryPrivateRootV1 or issued is None
            or issued[0]() is not value or value.module_identity != RECOVERY_CUSTODY_MODULE_IDENTITY):
        _fail("D2_RECOVERY_PRIVATE_CUSTODY_ROOT_INVALID")
    try:
        path = value._path.resolve(strict=True)
        if str(path) != issued[1] or value._path.is_symlink() or not path.is_dir():
            _fail("D2_RECOVERY_PRIVATE_CUSTODY_ROOT_INVALID")
        return path
    except D2RecoveryCustodyV1Error:
        raise
    except BaseException:
        _fail("D2_RECOVERY_PRIVATE_CUSTODY_ROOT_INVALID")


def _load_binding_path_v1() -> Path:
    binding = _repository_root_v1() / RECOVERY_BINDING_FILE
    try:
        if binding.is_symlink() or not binding.is_file():
            _fail("D2_RECOVERY_PRIVATE_CUSTODY_ROOT_INVALID")
        matches: list[str] = []
        for line in binding.read_text(encoding="utf-8").splitlines():
            match = re.fullmatch(r"([A-Z0-9_]+)='(.*)'", line)
            if match and match.group(1) == RECOVERY_BINDING_KEY:
                matches.append(match.group(2).replace("'\"'\"'", "'"))
        if len(matches) != 1:
            _fail("D2_RECOVERY_PRIVATE_CUSTODY_ROOT_INVALID")
        return Path(matches[0])
    except D2RecoveryCustodyV1Error:
        raise
    except BaseException:
        _fail("D2_RECOVERY_PRIVATE_CUSTODY_ROOT_INVALID")


def initialize_local_recovery_binding_v1() -> str:
    """Create the task-local private plane without returning or printing a path."""

    try:
        base_text = os.environ.get("LOCALAPPDATA")
        if not base_text:
            _fail("D2_RECOVERY_PRIVATE_CUSTODY_ROOT_INVALID")
        root = Path(base_text) / "paper_v_20260625_private_custody" / "task039e3_d2_recovery_v1"
        root.mkdir(mode=0o700, parents=True, exist_ok=True)
        if root.is_symlink() or not root.is_dir():
            _fail("D2_RECOVERY_PRIVATE_CUSTODY_ROOT_INVALID")
        try:
            os.chmod(root, 0o700)
        except OSError:
            pass
        binding = _repository_root_v1() / RECOVERY_BINDING_FILE
        if binding.is_symlink():
            _fail("D2_RECOVERY_PRIVATE_CUSTODY_SYMLINK_REJECTED")
        escaped = str(root).replace("'", "'\"'\"'")
        content = f"{RECOVERY_BINDING_KEY}='{escaped}'\n"
        temporary = binding.with_suffix(binding.suffix + ".tmp")
        if temporary.exists() or temporary.is_symlink():
            _fail("D2_RECOVERY_PRIVATE_CUSTODY_TARGET_EXISTS")
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.chmod(temporary, 0o600)
        except OSError:
            pass
        os.replace(temporary, binding)
        _issue_root_v1(root, _repository_root_v1())
        return "D2_RECOVERY_LOCAL_BINDING_READY"
    except D2RecoveryCustodyV1Error:
        raise
    except PermissionError:
        _fail("D2_RECOVERY_PRIVATE_CUSTODY_WRITE_DENIED")
    except BaseException:
        _fail("D2_RECOVERY_PRIVATE_CUSTODY_UNEXPECTED")


def load_recovery_private_root_v1() -> D2RecoveryPrivateRootV1:
    return _issue_root_v1(_load_binding_path_v1(), _repository_root_v1())


def _atomic_write_bytes_v1(root: D2RecoveryPrivateRootV1, filename: str,
                           content: bytes, *, allow_sentinel: bool = False) -> bytes:
    directory = _validate_root_v1(root)
    if (type(filename) is not str or Path(filename).name != filename
            or (not allow_sentinel and filename not in ALLOWED_PRIVATE_FILENAMES)):
        _fail("D2_RECOVERY_PRIVATE_CUSTODY_ROOT_INVALID")
    target = directory / filename
    temporary = directory / f".{filename}.tmp"
    try:
        if target.exists() or target.is_symlink() or temporary.exists() or temporary.is_symlink():
            _fail("D2_RECOVERY_PRIVATE_CUSTODY_TARGET_EXISTS")
        with temporary.open("xb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.chmod(temporary, 0o600)
        except OSError:
            pass
        try:
            os.replace(temporary, target)
        except BaseException:
            try:
                temporary.unlink(missing_ok=True)
            except BaseException:
                pass
            _fail("D2_RECOVERY_PRIVATE_CUSTODY_ATOMIC_RENAME_FAILED")
        replay = target.read_bytes()
        if replay != content:
            _fail("D2_RECOVERY_PRIVATE_CUSTODY_UNEXPECTED")
        return replay
    except D2RecoveryCustodyV1Error:
        raise
    except PermissionError:
        _fail("D2_RECOVERY_PRIVATE_CUSTODY_WRITE_DENIED")
    except FileExistsError:
        _fail("D2_RECOVERY_PRIVATE_CUSTODY_TARGET_EXISTS")
    except BaseException:
        _fail("D2_RECOVERY_PRIVATE_CUSTODY_UNEXPECTED")


def write_recovery_private_json_atomic_v1(root: D2RecoveryPrivateRootV1,
                                          filename: str,
                                          document: Mapping[str, Any]) -> str:
    """Persist an already-computed private document; no science occurs here."""

    try:
        content = (json.dumps(document, sort_keys=True, separators=(",", ":"),
                              ensure_ascii=True, allow_nan=False) + "\n").encode("utf-8")
        _atomic_write_bytes_v1(root, filename, content)
        observed = document.get("artifact_hash")
        if type(observed) is not str:
            _fail("D2_RECOVERY_PRIVATE_CUSTODY_UNEXPECTED")
        return observed
    except D2RecoveryCustodyV1Error:
        raise
    except BaseException:
        _fail("D2_RECOVERY_PRIVATE_CUSTODY_UNEXPECTED")


@dataclass(frozen=True, repr=False)
class D2RecoveryCustodyPreflightReceiptV1:
    artifact_type: str
    schema_version: str
    custody_version: str
    module_identity: str
    remediation_hash: str
    path_redaction_audit_identity: str
    private_root_configured: bool
    private_root_writable: bool
    private_root_outside_git: bool
    private_root_symlink: bool
    permission_policy: str
    atomic_create: bool
    atomic_rename: bool
    private_reopen: bool
    sentinel_cleanup: bool
    residue_count: int
    scientific_d0_prediction_parses: int
    scientific_d1_prediction_parses: int
    fusion_computations: int
    label_parses: int
    metric_computations: int
    d2_scientific_executions: int
    test2_accesses: int
    preflight_attempts: int
    preflight_retries: int
    private_paths_exposed: int
    artifact_hash: str
    _root: D2RecoveryPrivateRootV1 = field(repr=False, compare=False)

    def __repr__(self) -> str:
        return "<D2RecoveryCustodyPreflightReceiptV1 validated=True path=REDACTED>"

    def _payload(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items()
                if not k.startswith("_") and k != "artifact_hash"}

    def to_public_dict(self) -> dict[str, Any]:
        return {**self._payload(), "artifact_hash": self.artifact_hash}


_ISSUED_PREFLIGHTS: dict[int, tuple[weakref.ReferenceType[D2RecoveryCustodyPreflightReceiptV1], str]] = {}
_REAL_PREFLIGHT_ATTEMPTED = False


def _issue_preflight_v1(value: D2RecoveryCustodyPreflightReceiptV1) -> D2RecoveryCustodyPreflightReceiptV1:
    oid = id(value)
    _ISSUED_PREFLIGHTS[oid] = (weakref.ref(value, lambda _: _ISSUED_PREFLIGHTS.pop(oid, None)), value.artifact_hash)
    return value


def perform_d2_recovery_custody_preflight_v1() -> D2RecoveryCustodyPreflightReceiptV1:
    global _REAL_PREFLIGHT_ATTEMPTED
    if _REAL_PREFLIGHT_ATTEMPTED:
        _fail("D2_RECOVERY_PRIVATE_CUSTODY_UNEXPECTED")
    _REAL_PREFLIGHT_ATTEMPTED = True
    root = load_recovery_private_root_v1()
    token = secrets.token_hex(16)
    filename = f".task039e3-d2-recovery-sentinel-{token}"
    directory = _validate_root_v1(root)
    target = directory / filename
    content = secrets.token_bytes(64)
    try:
        replay = _atomic_write_bytes_v1(root, filename, content, allow_sentinel=True)
        if replay != content:
            _fail("D2_RECOVERY_PRIVATE_CUSTODY_UNEXPECTED")
        target.unlink()
        if target.exists() or target.is_symlink():
            _fail("D2_RECOVERY_PRIVATE_CUSTODY_RESIDUE_DETECTED")
        provisional = D2RecoveryCustodyPreflightReceiptV1(
            "D2RecoveryCustodyPreflightReceiptV1", "1.0.0", RECOVERY_CUSTODY_VERSION,
            RECOVERY_CUSTODY_MODULE_IDENTITY, RECOVERY_CUSTODY_REMEDIATION_HASH,
            PATH_REDACTION_AUDIT_IDENTITY, True, True, True, False,
            PRIVATE_ROOT_PERMISSION_POLICY, True, True, True, True, 0,
            0, 0, 0, 0, 0, 0, 0, 1, 0, 0, "", root,
        )
        return _issue_preflight_v1(replace(
            provisional, artifact_hash=stable_hash_v1(provisional._payload())
        ))
    except D2RecoveryCustodyV1Error:
        try:
            target.unlink(missing_ok=True)
        except BaseException:
            pass
        raise
    except BaseException:
        try:
            target.unlink(missing_ok=True)
        except BaseException:
            pass
        _fail("D2_RECOVERY_PRIVATE_CUSTODY_UNEXPECTED")


def validate_d2_recovery_custody_preflight_v1(
    value: D2RecoveryCustodyPreflightReceiptV1,
) -> str:
    issued = _ISSUED_PREFLIGHTS.get(id(value))
    if (type(value) is not D2RecoveryCustodyPreflightReceiptV1 or issued is None
            or issued[0]() is not value or issued[1] != value.artifact_hash):
        _fail("D2_RECOVERY_PRIVATE_CUSTODY_UNEXPECTED")
    _validate_root_v1(value._root)
    expected_true = (
        value.private_root_configured, value.private_root_writable,
        value.private_root_outside_git, value.atomic_create, value.atomic_rename,
        value.private_reopen, value.sentinel_cleanup,
    )
    if not all(item is True for item in expected_true) or value.private_root_symlink is not False:
        _fail("D2_RECOVERY_PRIVATE_CUSTODY_UNEXPECTED")
    if value.residue_count != 0 or stable_hash_v1(value._payload()) != value.artifact_hash:
        _fail("D2_RECOVERY_PRIVATE_CUSTODY_UNEXPECTED")
    return value.artifact_hash


def _issue_synthetic_recovery_root_v1(path: Path, repository: Path) -> D2RecoveryPrivateRootV1:
    """Private synthetic fixture hook; never used by real authorization."""
    return _issue_root_v1(path, repository)


def _build_synthetic_preflight_v1(
    root: D2RecoveryPrivateRootV1,
) -> D2RecoveryCustodyPreflightReceiptV1:
    """Issue a no-I/O process-local receipt for synthetic contract tests."""
    _validate_root_v1(root)
    provisional = D2RecoveryCustodyPreflightReceiptV1(
        "D2RecoveryCustodyPreflightReceiptV1", "1.0.0", RECOVERY_CUSTODY_VERSION,
        RECOVERY_CUSTODY_MODULE_IDENTITY, RECOVERY_CUSTODY_REMEDIATION_HASH,
        PATH_REDACTION_AUDIT_IDENTITY, True, True, True, False,
        PRIVATE_ROOT_PERMISSION_POLICY, True, True, True, True, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "", root,
    )
    return _issue_preflight_v1(replace(
        provisional, artifact_hash=stable_hash_v1(provisional._payload())
    ))


__all__ = [
    "ALLOWED_PRIVATE_FILENAMES", "D2RecoveryCustodyPreflightReceiptV1",
    "D2RecoveryCustodyV1Error", "D2RecoveryPrivateRootV1",
    "PATH_REDACTION_AUDIT_IDENTITY", "PRIVATE_ROOT_PERMISSION_POLICY",
    "RECOVERY_CUSTODY_MODULE_IDENTITY", "RECOVERY_CUSTODY_REMEDIATION_HASH",
    "RECOVERY_CUSTODY_VERSION", "initialize_local_recovery_binding_v1",
    "load_recovery_private_root_v1", "perform_d2_recovery_custody_preflight_v1",
    "validate_d2_recovery_custody_preflight_v1",
    "write_recovery_private_json_atomic_v1",
]
