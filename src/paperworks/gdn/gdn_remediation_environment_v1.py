"""Exact-environment contracts for the bounded TASK-039C-GDNR attempt.

This module owns environment and serialization checks only.  It deliberately
does not reimplement the frozen GDN model, training loop, projection, or
ranking formulas.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from email.parser import Parser
from importlib import metadata, util
from pathlib import Path
from typing import Any, Mapping, Sequence

from paperworks.gdn.upstream_candidate_backend_v1 import (
    APPROVED_PORT_DEPENDENCIES,
    DependencyEnvironmentV1,
    build_dependency_status_v1,
)
from paperworks.v6.common import parse_iso_datetime, require_sha256, stable_hash_v1


TASK_ID = "TASK-039C-GDNR"
REMEDIATION_BRANCH = "task-039c-gdn-remediation"
BLOCKED_GDN_COMMIT = "c0efdb6218385ec326be1a929371242314e63cb6"
PHASE_A_COMMIT = "229cb29cfec567e6491515de34c495a863c6e5fa"
REVIEW_COMMIT = "058b5e2023b66ccbf6704c5baf1f6c677f17b07a"
FIDELITY_RECEIPT_HASH = (
    "93821469e465a942ff94c779c6798355383e35003b13db24c19b9760ca3266c4"
)
SOURCE_IDENTITY_HASH = (
    "0af3f80f18a3eab59b9783af64d306c8d774eeb69b3a72c24c10048abd4ed234"
)
TARGET_IDENTITY_HASH = (
    "063037980aae4f0eaf45fbebb59f2aa0a924fbad583f3818107a793dfe7248e7"
)
CANDIDATE_LEARNING_VIEW_ID = (
    "eaa77f331bf79cc6887ccddcfff8818880c1a93c16ebc6fdd2d06a1c8db37eca"
)
CANDIDATE_FEATURE_ORDER_HASH = (
    "a612bdb9850ad0dd865dc62b23199bf2b696452c492e4aabe09fe554fa246d57"
)

REQUIRED_PYTHON_VERSION = "3.12.13"
REQUIRED_PLATFORM_ID = "windows-amd64"
REQUIRED_TOP_LEVEL_PACKAGES = {
    "jsonschema": "4.26.0",
    "torch": "2.12.1",
    "torch-geometric": "2.8.0",
}
REQUIRED_TOP_LEVEL_WHEELS = {
    "torch": (
        "torch-2.12.1-cp312-cp312-win_amd64.whl",
        "e86550597877fb272ddc52db2f85b82cb601ea7bd932576a0340152cae2200b3",
    ),
    "torch-geometric": (
        "torch_geometric-2.8.0-py3-none-any.whl",
        "1f62e415a2e9ee69d34617d1b0b230e9d9040f51809b96e801e742770fd4dada",
    ),
}
UNAPPROVED_PYG_EXTENSIONS = (
    "pyg-lib",
    "torch-cluster",
    "torch-scatter",
    "torch-sparse",
    "torch-spline-conv",
)
ROOT_ENVIRONMENT_VARIABLES = (
    "TASK039C_GDN_ENV_ROOT",
    "TASK039C_GDN_WHEELHOUSE",
    "TASK039C_GDN_PRIVATE_ROOT",
    "HAI_DATA_ROOT",
)
DETERMINISTIC_ENVIRONMENT = {
    "MKL_NUM_THREADS": "1",
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "PYTHONHASHSEED": "0",
}
ALLOWED_VALUE_FILES = (
    "hai-23.05/hai-train1.csv",
    "hai-23.05/hai-train2.csv",
)

_ABSOLUTE_WINDOWS_PATH = re.compile(r"(?<![A-Za-z])[A-Za-z]:[\\/]")
_CANONICAL_NAME = re.compile(r"[-_.]+")


class GDNRRemediationError(ValueError):
    """Base error for the bounded remediation attempt."""

    status = "failed_gdn_result_contract"


class ExactGDNEnvironmentUnavailable(GDNRRemediationError):
    status = "blocked_exact_gdn_environment_unavailable"


class MissingUnapprovedExtensionError(GDNRRemediationError):
    status = "blocked_exact_gdn_environment_missing_unapproved_extension"


class GDNRSourceChangeError(GDNRRemediationError):
    status = "failed_gdn_remediation_requires_scientific_change"


class GDNRDataBoundaryError(GDNRRemediationError):
    status = "failed_gdn_data_boundary"


class GDNRTrainingError(GDNRRemediationError):
    status = "failed_gdn_training"


class GDNRResultContractError(GDNRRemediationError):
    status = "failed_gdn_result_contract"


def canonical_package_name_v1(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ExactGDNEnvironmentUnavailable("wheel package name is missing")
    return _CANONICAL_NAME.sub("-", value).lower()


def _is_within(path: Path, parent: Path) -> bool:
    return path == parent or parent in path.parents


@dataclass(frozen=True)
class ExternalRemediationRootsV1:
    environment_root: Path
    wheelhouse_root: Path
    private_root: Path
    hai_data_root: Path

    @classmethod
    def from_environment(
        cls,
        *,
        repository_root: Path,
        environ: Mapping[str, str] | None = None,
        require_existing: bool = False,
    ) -> "ExternalRemediationRootsV1":
        source = os.environ if environ is None else environ
        missing = [name for name in ROOT_ENVIRONMENT_VARIABLES if not source.get(name)]
        if missing:
            raise ExactGDNEnvironmentUnavailable(
                "required external-root environment variables are missing"
            )
        raw = [Path(str(source[name])) for name in ROOT_ENVIRONMENT_VARIABLES]
        if any(not path.is_absolute() for path in raw):
            raise ExactGDNEnvironmentUnavailable("external roots must be absolute")
        resolved = tuple(path.resolve(strict=require_existing) for path in raw)
        if len(set(resolved)) != len(resolved):
            raise ExactGDNEnvironmentUnavailable("external roots must be distinct")
        repository = repository_root.resolve(strict=True)
        if any(_is_within(path, repository) for path in resolved):
            raise ExactGDNEnvironmentUnavailable(
                "environment, wheelhouse, private, and HAI roots must remain outside Git"
            )
        if require_existing and any(not path.is_dir() for path in resolved):
            raise ExactGDNEnvironmentUnavailable("every external root must exist as a directory")
        return cls(*resolved)

    def to_private_dict(self) -> dict[str, str]:
        return {
            "environment_root": str(self.environment_root),
            "wheelhouse_root": str(self.wheelhouse_root),
            "private_root": str(self.private_root),
            "hai_data_root": str(self.hai_data_root),
        }


def assert_public_payload_sanitized_v1(value: Any) -> None:
    """Reject absolute paths and path-like URI disclosures recursively."""

    if isinstance(value, Mapping):
        for item in value.values():
            assert_public_payload_sanitized_v1(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            assert_public_payload_sanitized_v1(item)
    elif isinstance(value, str):
        lowered = value.lower()
        if (
            _ABSOLUTE_WINDOWS_PATH.search(value)
            or value.startswith(("\\\\", "//"))
            or "file://" in lowered
            or "checkpoint_path" in lowered
            or "raw_feature_values" in lowered
        ):
            raise GDNRResultContractError("public artifact contains a private path or value token")


def verify_self_hash_v1(
    document: Mapping[str, Any], *, field_name: str = "artifact_hash"
) -> str:
    observed = str(document.get(field_name, ""))
    require_sha256(observed, field_name)
    content = {key: value for key, value in document.items() if key != field_name}
    if stable_hash_v1(content) != observed:
        raise GDNRResultContractError(f"{field_name} does not match content")
    return observed


@dataclass(frozen=True)
class WheelRecordV1:
    file_name: str
    package_name: str
    version: str
    byte_size: int
    sha256: str

    def __post_init__(self) -> None:
        if (
            Path(self.file_name).name != self.file_name
            or not self.file_name.lower().endswith(".whl")
        ):
            raise ExactGDNEnvironmentUnavailable("source distributions are prohibited")
        if self.package_name != canonical_package_name_v1(self.package_name):
            raise ExactGDNEnvironmentUnavailable("wheel package name is not canonical")
        if not self.version or self.byte_size <= 0:
            raise ExactGDNEnvironmentUnavailable("wheel metadata is incomplete")
        require_sha256(self.sha256, "wheel sha256")

    @classmethod
    def from_path(cls, path: Path) -> "WheelRecordV1":
        if path.suffix.lower() != ".whl" or not path.is_file():
            raise ExactGDNEnvironmentUnavailable("wheelhouse contains a non-wheel artifact")
        try:
            with zipfile.ZipFile(path) as archive:
                candidates = sorted(
                    name
                    for name in archive.namelist()
                    if name.endswith(".dist-info/METADATA")
                    and name.count("/") == 1
                )
                if len(candidates) != 1:
                    raise ExactGDNEnvironmentUnavailable(
                        "wheel must contain exactly one top-level distribution metadata file"
                    )
                message = Parser().parsestr(
                    archive.read(candidates[0]).decode("utf-8", errors="strict")
                )
        except (OSError, UnicodeDecodeError, zipfile.BadZipFile) as exc:
            raise ExactGDNEnvironmentUnavailable("wheel bytes cannot be inspected") from exc
        name = canonical_package_name_v1(str(message.get("Name", "")))
        version = str(message.get("Version", ""))
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return cls(path.name, name, version, path.stat().st_size, digest.hexdigest())

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_name": self.file_name,
            "package_name": self.package_name,
            "version": self.version,
            "byte_size": self.byte_size,
            "sha256": self.sha256,
        }


def inspect_wheelhouse_v1(wheelhouse_root: Path) -> tuple[WheelRecordV1, ...]:
    root = wheelhouse_root.resolve(strict=True)
    entries = tuple(sorted(root.iterdir(), key=lambda path: path.name.casefold()))
    if not entries:
        raise ExactGDNEnvironmentUnavailable("wheelhouse is empty")
    records = tuple(WheelRecordV1.from_path(path) for path in entries)
    names = [record.package_name for record in records]
    if len(names) != len(set(names)):
        raise ExactGDNEnvironmentUnavailable("wheelhouse contains duplicate distributions")
    by_name = {record.package_name: record for record in records}
    for name, version in REQUIRED_TOP_LEVEL_PACKAGES.items():
        record = by_name.get(name)
        if record is None or record.version != version:
            raise ExactGDNEnvironmentUnavailable(
                f"wheelhouse lacks exact approved top-level package {name}"
            )
    for name, (file_name, digest) in REQUIRED_TOP_LEVEL_WHEELS.items():
        record = by_name[name]
        if record.file_name != file_name or record.sha256 != digest:
            raise ExactGDNEnvironmentUnavailable(
                f"frozen wheel identity mismatch for {name}"
            )
    if any(name in by_name for name in UNAPPROVED_PYG_EXTENSIONS):
        raise MissingUnapprovedExtensionError(
            "unapproved optional PyG extension appeared in the wheelhouse"
        )
    return records


def build_sanitized_wheelhouse_receipt_v1(
    records: Sequence[WheelRecordV1], *, created_at: str
) -> dict[str, Any]:
    parse_iso_datetime(created_at, "created_at")
    ordered = tuple(sorted(records, key=lambda item: item.file_name.casefold()))
    manifest = [item.to_dict() for item in ordered]
    manifest_hash = stable_hash_v1(
        {"artifact_type": "task039c_gdn_wheel_manifest_v1", "wheels": manifest}
    )
    content: dict[str, Any] = {
        "schema_version": "1.0.0",
        "artifact_type": "task039c_gdn_sanitized_wheelhouse_receipt_v1",
        "task_id": TASK_ID,
        "status": "passed_exact_binary_wheelhouse_verification",
        "wheel_count": len(ordered),
        "wheels": manifest,
        "sanitized_wheel_manifest_hash": manifest_hash,
        "top_level_exact_match": True,
        "source_distributions_present": False,
        "unapproved_pyg_extensions_present": False,
        "wheelhouse_root_disclosed": False,
        "created_at": created_at,
    }
    assert_public_payload_sanitized_v1(content)
    return {**content, "artifact_hash": stable_hash_v1(content)}


def build_private_wheelhouse_receipt_v1(
    *, public_receipt: Mapping[str, Any], wheelhouse_root: Path
) -> dict[str, Any]:
    verify_self_hash_v1(public_receipt)
    content = {
        "schema_version": "1.0.0",
        "artifact_type": "task039c_gdn_private_wheelhouse_receipt_v1",
        "task_id": TASK_ID,
        "wheelhouse_root": str(wheelhouse_root.resolve(strict=True)),
        "public_receipt": dict(public_receipt),
    }
    return {**content, "artifact_hash": stable_hash_v1(content)}


def _installed_distributions_v1() -> dict[str, str]:
    result: dict[str, str] = {}
    for distribution in metadata.distributions():
        name = canonical_package_name_v1(str(distribution.metadata.get("Name", "")))
        version = str(distribution.version)
        if name in result and result[name] != version:
            raise ExactGDNEnvironmentUnavailable("installed distribution is ambiguous")
        result[name] = version
    return dict(sorted(result.items()))


def _run_python_module_v1(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", *arguments],
        check=False,
        capture_output=True,
        text=True,
    )


def _verify_runtime_imports_v1() -> tuple[str, bool]:
    try:
        import torch
        import torch_geometric  # noqa: F401
        from torch_geometric.nn.conv import MessagePassing  # noqa: F401
        from torch_geometric.nn.inits import glorot, zeros  # noqa: F401
        from torch_geometric.utils import (  # noqa: F401
            add_self_loops,
            remove_self_loops,
            softmax,
        )
    except (ImportError, OSError, RuntimeError) as exc:
        lowered = str(exc).lower()
        if any(token in lowered for token in UNAPPROVED_PYG_EXTENSIONS):
            raise MissingUnapprovedExtensionError(
                "frozen backend import requested an unapproved PyG extension"
            ) from exc
        raise ExactGDNEnvironmentUnavailable("exact Torch/PyG imports failed") from exc
    runtime_version = str(torch.__version__)
    if runtime_version.split("+", 1)[0] != REQUIRED_TOP_LEVEL_PACKAGES["torch"]:
        raise ExactGDNEnvironmentUnavailable("torch runtime version differs from metadata")
    try:
        value = float((torch.tensor([1.0], device="cpu") + 1.0).item())
    except (RuntimeError, TypeError, ValueError) as exc:
        raise ExactGDNEnvironmentUnavailable("CPU tensor execution is unavailable") from exc
    if value != 2.0:
        raise ExactGDNEnvironmentUnavailable("CPU tensor verification produced an invalid value")
    return runtime_version, True


@dataclass(frozen=True)
class TASK039CGDNEnvironmentReceiptV1:
    python_version: str
    platform_id: str
    top_level_packages: Mapping[str, str]
    wheel_manifest: tuple[WheelRecordV1, ...]
    sanitized_wheel_manifest_hash: str
    wheelhouse_receipt_hash: str
    installed_package_freeze_hash: str
    installed_package_count: int
    pip_version: str
    pip_check_status: str
    dependency_environment_fingerprint: str
    fidelity_receipt_hash: str
    torch_runtime_version: str
    cpu_execution_available: bool
    created_at: str
    status: str = "passed_exact_gdn_environment_remediation"
    schema_version: str = "1.0.0"
    artifact_type: str = "task039c_gdn_environment_receipt_v1"
    task_id: str = TASK_ID

    def __post_init__(self) -> None:
        if (
            self.python_version != REQUIRED_PYTHON_VERSION
            or self.platform_id != REQUIRED_PLATFORM_ID
            or dict(self.top_level_packages) != REQUIRED_TOP_LEVEL_PACKAGES
        ):
            raise ExactGDNEnvironmentUnavailable("environment identity is not exact")
        require_sha256(self.sanitized_wheel_manifest_hash, "wheel manifest hash")
        require_sha256(self.wheelhouse_receipt_hash, "wheelhouse receipt hash")
        require_sha256(self.installed_package_freeze_hash, "installed freeze hash")
        require_sha256(
            self.dependency_environment_fingerprint,
            "dependency environment fingerprint",
        )
        if self.fidelity_receipt_hash != FIDELITY_RECEIPT_HASH:
            raise GDNRSourceChangeError("fidelity receipt binding changed")
        if not self.wheel_manifest or self.installed_package_count <= 0:
            raise ExactGDNEnvironmentUnavailable("environment inventory is empty")
        if self.pip_check_status != "passed" or not self.cpu_execution_available:
            raise ExactGDNEnvironmentUnavailable("environment verification did not pass")
        if self.torch_runtime_version.split("+", 1)[0] != "2.12.1":
            raise ExactGDNEnvironmentUnavailable("torch runtime is not compatible")
        parse_iso_datetime(self.created_at, "created_at")

    def _payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "task_id": self.task_id,
            "status": self.status,
            "python_version": self.python_version,
            "platform_id": self.platform_id,
            "top_level_packages": dict(self.top_level_packages),
            "wheel_count": len(self.wheel_manifest),
            "wheel_manifest": [item.to_dict() for item in self.wheel_manifest],
            "sanitized_wheel_manifest_hash": self.sanitized_wheel_manifest_hash,
            "wheelhouse_receipt_hash": self.wheelhouse_receipt_hash,
            "installed_package_freeze_hash": self.installed_package_freeze_hash,
            "installed_package_count": self.installed_package_count,
            "pip_version": self.pip_version,
            "pip_check_status": self.pip_check_status,
            "dependency_environment_fingerprint": self.dependency_environment_fingerprint,
            "fidelity_receipt_hash": self.fidelity_receipt_hash,
            "torch_runtime_version": self.torch_runtime_version,
            "cpu_execution_available": self.cpu_execution_available,
            "gpu_or_cuda_required": False,
            "unapproved_pyg_extensions_installed": False,
            "wheelhouse_installed_distribution_match": True,
            "deterministic_environment": dict(DETERMINISTIC_ENVIRONMENT),
            "environment_exact_match": True,
            "environment_root_disclosed": False,
            "created_at": self.created_at,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self._payload()
        assert_public_payload_sanitized_v1(payload)
        return {**payload, "artifact_hash": self.artifact_hash}


def verify_exact_current_environment_v1(
    *,
    public_wheelhouse_receipt: Mapping[str, Any],
    fidelity_receipt_hash: str,
    created_at: str,
) -> tuple[TASK039CGDNEnvironmentReceiptV1, dict[str, str], tuple[str, ...]]:
    """Verify the current interpreter after offline installation."""

    verify_self_hash_v1(public_wheelhouse_receipt)
    records = tuple(
        WheelRecordV1(
            file_name=str(item["file_name"]),
            package_name=str(item["package_name"]),
            version=str(item["version"]),
            byte_size=int(item["byte_size"]),
            sha256=str(item["sha256"]),
        )
        for item in public_wheelhouse_receipt.get("wheels", ())
    )
    if tuple(item.to_dict() for item in records) != tuple(
        item.to_dict() for item in inspect_wheelhouse_v1(Path(os.environ["TASK039C_GDN_WHEELHOUSE"]))
    ):
        raise ExactGDNEnvironmentUnavailable("wheelhouse changed after verification")
    python_version = platform.python_version()
    platform_id = f"{platform.system().lower()}-{platform.machine().lower()}"
    if python_version != REQUIRED_PYTHON_VERSION or platform_id != REQUIRED_PLATFORM_ID:
        raise ExactGDNEnvironmentUnavailable("Python or platform identity differs")
    top_level = {
        name: metadata.version(name) if util.find_spec(name.replace("-", "_")) else ""
        for name in REQUIRED_TOP_LEVEL_PACKAGES
    }
    if top_level != REQUIRED_TOP_LEVEL_PACKAGES:
        raise ExactGDNEnvironmentUnavailable("top-level installed versions are not exact")
    for name in UNAPPROVED_PYG_EXTENSIONS:
        try:
            metadata.version(name)
        except metadata.PackageNotFoundError:
            continue
        raise MissingUnapprovedExtensionError(
            "unapproved optional PyG extension is installed"
        )
    for name, value in DETERMINISTIC_ENVIRONMENT.items():
        if os.environ.get(name) != value:
            raise ExactGDNEnvironmentUnavailable(
                "deterministic execution environment variables are not exact"
            )
    torch_runtime_version, cpu_available = _verify_runtime_imports_v1()
    pip_check = _run_python_module_v1("pip", "check")
    if pip_check.returncode != 0:
        raise ExactGDNEnvironmentUnavailable("pip check failed in exact environment")
    freeze = _run_python_module_v1("pip", "freeze", "--all")
    if freeze.returncode != 0:
        raise ExactGDNEnvironmentUnavailable("installed package freeze failed")
    freeze_lines = tuple(sorted(line.strip() for line in freeze.stdout.splitlines() if line.strip()))
    if any(" @ " in line or "file:" in line.lower() or _ABSOLUTE_WINDOWS_PATH.search(line) for line in freeze_lines):
        raise ExactGDNEnvironmentUnavailable("installed freeze contains a path dependency")
    installed = _installed_distributions_v1()
    wheel_versions = {item.package_name: item.version for item in records}
    unexpected = set(installed) - set(wheel_versions) - {"pip"}
    missing = set(wheel_versions) - set(installed)
    mismatched = {
        name
        for name in set(wheel_versions) & set(installed)
        if wheel_versions[name] != installed[name]
    }
    if unexpected or missing or mismatched:
        raise ExactGDNEnvironmentUnavailable(
            "wheelhouse and installed-distribution receipts do not match"
        )
    dependency = build_dependency_status_v1(
        (
            DependencyEnvironmentV1(
                environment_id="task039c_gdnr_exact_cp312",
                python_version=python_version,
                platform_id=platform_id,
                torch_version=top_level["torch"],
                torch_geometric_version=top_level["torch-geometric"],
            ),
        )
    )
    if not dependency.exact_backend_available:
        raise ExactGDNEnvironmentUnavailable("existing exact dependency gate did not pass")
    installed_hash = stable_hash_v1(
        {
            "artifact_type": "task039c_gdn_installed_package_freeze_v1",
            "freeze": list(freeze_lines),
        }
    )
    receipt = TASK039CGDNEnvironmentReceiptV1(
        python_version=python_version,
        platform_id=platform_id,
        top_level_packages=top_level,
        wheel_manifest=records,
        sanitized_wheel_manifest_hash=str(
            public_wheelhouse_receipt["sanitized_wheel_manifest_hash"]
        ),
        wheelhouse_receipt_hash=str(public_wheelhouse_receipt["artifact_hash"]),
        installed_package_freeze_hash=installed_hash,
        installed_package_count=len(installed),
        pip_version=metadata.version("pip"),
        pip_check_status="passed",
        dependency_environment_fingerprint=dependency.environment_fingerprint,
        fidelity_receipt_hash=fidelity_receipt_hash,
        torch_runtime_version=torch_runtime_version,
        cpu_execution_available=cpu_available,
        created_at=created_at,
    )
    return receipt, installed, freeze_lines


def build_private_environment_receipt_v1(
    *,
    public_receipt: Mapping[str, Any],
    roots: ExternalRemediationRootsV1,
    installed_packages: Mapping[str, str],
    freeze_lines: Sequence[str],
) -> dict[str, Any]:
    verify_self_hash_v1(public_receipt)
    content = {
        "schema_version": "1.0.0",
        "artifact_type": "task039c_gdn_private_environment_receipt_v1",
        "task_id": TASK_ID,
        "external_roots": roots.to_private_dict(),
        "public_receipt": dict(public_receipt),
        "installed_packages": dict(installed_packages),
        "pip_freeze": list(freeze_lines),
    }
    return {**content, "artifact_hash": stable_hash_v1(content)}


def load_verified_private_environment_receipt_v1(
    path: Path, *, roots: ExternalRemediationRootsV1
) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ExactGDNEnvironmentUnavailable("private environment receipt is unavailable") from exc
    verify_self_hash_v1(document)
    if document.get("external_roots") != roots.to_private_dict():
        raise ExactGDNEnvironmentUnavailable("private environment roots changed")
    public = document.get("public_receipt")
    if not isinstance(public, Mapping):
        raise ExactGDNEnvironmentUnavailable("public environment binding is missing")
    verify_self_hash_v1(public)
    assert_public_payload_sanitized_v1(public)
    return document


def derive_frozen_p1_feature_order_from_headers_v1(
    *, data_root: Path, expected_feature_order_hash: str = CANDIDATE_FEATURE_ORDER_HASH
) -> tuple[str, ...]:
    """Read metadata headers only and bind the full P1 view before values load."""

    require_sha256(expected_feature_order_hash, "expected feature order hash")
    root = data_root.resolve(strict=True)
    orders: list[tuple[str, ...]] = []
    for relative in ALLOWED_VALUE_FILES:
        path = (root / relative).resolve(strict=True)
        if not path.is_relative_to(root):
            raise GDNRDataBoundaryError("authorized HAI path escaped its root")
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                header = tuple(next(csv.reader(handle)))
        except (OSError, StopIteration, UnicodeDecodeError) as exc:
            raise GDNRDataBoundaryError("authorized HAI header is unavailable") from exc
        if len(header) != len(set(header)):
            raise GDNRDataBoundaryError("authorized HAI header is ambiguous")
        order = tuple(name for name in header if name.startswith("P1_"))
        if not order or any(
            token in name.lower() for name in order for token in ("label", "attack", "anomaly")
        ):
            raise GDNRDataBoundaryError("frozen P1 feature view is invalid")
        orders.append(order)
    if len(set(orders)) != 1:
        raise GDNRDataBoundaryError("train1/train2 P1 header order differs")
    feature_order = orders[0]
    observed = stable_hash_v1({"features": list(feature_order)})
    if observed != expected_feature_order_hash:
        raise GDNRDataBoundaryError("frozen candidate-learning feature order mismatch")
    return feature_order


def enrich_passing_gdn_result_v1(
    *,
    base_result: Mapping[str, Any],
    environment_receipt_hash: str,
    remediation_execution_commit: str,
    private_seed_ledger_hashes: Sequence[Mapping[str, Any]],
    data_access_audit_ref: str,
) -> dict[str, Any]:
    """Add remediation lineage/access bindings to an already-built GDN result."""

    if base_result.get("status") != "passed_task039c_gdn_candidate_discovery":
        raise GDNRResultContractError("only a passing base GDN result may be enriched")
    verify_self_hash_v1(base_result)
    require_sha256(environment_receipt_hash, "environment receipt hash")
    if not re.fullmatch(r"[a-f0-9]{40}", remediation_execution_commit):
        raise GDNRResultContractError("remediation execution commit must be a full SHA")
    if len(private_seed_ledger_hashes) != 3:
        raise GDNRResultContractError("exactly three private seed ledger hashes are required")
    expected_seeds = [11, 23, 37]
    observed_seeds = [int(item.get("seed", -1)) for item in private_seed_ledger_hashes]
    if observed_seeds != expected_seeds:
        raise GDNRResultContractError("private seed ledger order changed")
    for item in private_seed_ledger_hashes:
        require_sha256(str(item.get("ledger_hash", "")), "private seed ledger hash")
    if Path(data_access_audit_ref).name != data_access_audit_ref:
        raise GDNRResultContractError("data access audit reference must be a file name")
    payload = {key: value for key, value in base_result.items() if key != "artifact_hash"}
    payload.update(
        {
            "source_identity_hash": SOURCE_IDENTITY_HASH,
            "target_identity_hash": TARGET_IDENTITY_HASH,
            "candidate_learning_view_id": CANDIDATE_LEARNING_VIEW_ID,
            "environment_receipt_hash": environment_receipt_hash,
            "remediation_execution_commit": remediation_execution_commit,
            "private_seed_ledger_hashes": [dict(item) for item in private_seed_ledger_hashes],
            "data_access_audit_ref": data_access_audit_ref,
            "train1_accessed": True,
            "train2_accessed": True,
            "labels_accessed": False,
            "attacks_accessed": False,
            "meta_output_used": False,
            "stat_output_used": False,
        }
    )
    assert_public_payload_sanitized_v1(payload)
    return {**payload, "artifact_hash": stable_hash_v1(payload)}


__all__ = [
    "ALLOWED_VALUE_FILES",
    "BLOCKED_GDN_COMMIT",
    "CANDIDATE_FEATURE_ORDER_HASH",
    "CANDIDATE_LEARNING_VIEW_ID",
    "DETERMINISTIC_ENVIRONMENT",
    "ExactGDNEnvironmentUnavailable",
    "ExternalRemediationRootsV1",
    "FIDELITY_RECEIPT_HASH",
    "GDNRDataBoundaryError",
    "GDNRRemediationError",
    "GDNRResultContractError",
    "GDNRSourceChangeError",
    "GDNRTrainingError",
    "MissingUnapprovedExtensionError",
    "PHASE_A_COMMIT",
    "REMEDIATION_BRANCH",
    "REQUIRED_PLATFORM_ID",
    "REQUIRED_PYTHON_VERSION",
    "REQUIRED_TOP_LEVEL_PACKAGES",
    "REQUIRED_TOP_LEVEL_WHEELS",
    "REVIEW_COMMIT",
    "SOURCE_IDENTITY_HASH",
    "TARGET_IDENTITY_HASH",
    "TASK039CGDNEnvironmentReceiptV1",
    "TASK_ID",
    "UNAPPROVED_PYG_EXTENSIONS",
    "WheelRecordV1",
    "assert_public_payload_sanitized_v1",
    "build_private_environment_receipt_v1",
    "build_private_wheelhouse_receipt_v1",
    "build_sanitized_wheelhouse_receipt_v1",
    "canonical_package_name_v1",
    "derive_frozen_p1_feature_order_from_headers_v1",
    "enrich_passing_gdn_result_v1",
    "inspect_wheelhouse_v1",
    "load_verified_private_environment_receipt_v1",
    "verify_exact_current_environment_v1",
    "verify_self_hash_v1",
]
