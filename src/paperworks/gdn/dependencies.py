"""Lightweight optional-dependency inspection for GDN smoke backends."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import metadata, util
from typing import Any

from paperworks.v6.common import V6_FOUNDATION_SCHEMA_VERSION, stable_hash_v1


GDN_DEPENDENCY_STATUS_ARTIFACT_TYPE = "gdn_dependency_status"
GDN_OPTIONAL_DEPENDENCY_ISSUE_CODE = "GDN_OPTIONAL_DEPENDENCY_UNAVAILABLE"
_INSPECTION_METHOD = "importlib.util.find_spec+importlib.metadata.version"


@dataclass(frozen=True)
class GDNDependencyStatusV1:
    """Metadata-only availability result that does not import a heavy backend."""

    torch_available: bool
    torch_geometric_available: bool
    torch_version: str | None
    torch_geometric_version: str | None
    backend_importable: bool
    missing_packages: tuple[str, ...]
    inspection_method: str = _INSPECTION_METHOD
    schema_version: str = V6_FOUNDATION_SCHEMA_VERSION
    artifact_type: str = GDN_DEPENDENCY_STATUS_ARTIFACT_TYPE

    def __post_init__(self) -> None:
        if self.schema_version != V6_FOUNDATION_SCHEMA_VERSION:
            raise ValueError("unsupported GDN dependency-status schema version")
        if self.artifact_type != GDN_DEPENDENCY_STATUS_ARTIFACT_TYPE:
            raise ValueError("invalid GDN dependency-status artifact type")
        expected_missing = tuple(
            name
            for name, available in (
                ("torch", self.torch_available),
                ("torch-geometric", self.torch_geometric_available),
            )
            if not available
        )
        if self.missing_packages != expected_missing:
            raise ValueError("missing_packages does not match dependency availability")
        if self.backend_importable != (
            self.torch_available and self.torch_geometric_available
        ):
            raise ValueError("backend_importable does not match dependency availability")
        if not self.torch_available and self.torch_version is not None:
            raise ValueError("unavailable torch cannot have a version")
        if (
            not self.torch_geometric_available
            and self.torch_geometric_version is not None
        ):
            raise ValueError("unavailable torch-geometric cannot have a version")
        if self.inspection_method != _INSPECTION_METHOD:
            raise ValueError("unsupported dependency inspection method")

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._payload())

    def _payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "torch_available": self.torch_available,
            "torch_geometric_available": self.torch_geometric_available,
            "torch_version": self.torch_version,
            "torch_geometric_version": self.torch_geometric_version,
            "backend_importable": self.backend_importable,
            "missing_packages": list(self.missing_packages),
            "inspection_method": self.inspection_method,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "artifact_hash": self.artifact_hash}


class GDNOptionalDependencyError(ImportError):
    """Stable fail-closed error for unavailable Torch/PyG public symbols."""

    issue_code = GDN_OPTIONAL_DEPENDENCY_ISSUE_CODE

    def __init__(
        self,
        status: GDNDependencyStatusV1,
        *,
        detail: str | None = None,
    ) -> None:
        self.dependency_status = status
        suffix = f" ({detail})" if detail else ""
        missing = ", ".join(status.missing_packages) or "backend import"
        super().__init__(
            f"{self.issue_code}: optional GDN dependencies unavailable: "
            f"{missing}{suffix}"
        )


def _installed_version(distribution_name: str) -> str | None:
    try:
        return metadata.version(distribution_name)
    except metadata.PackageNotFoundError:
        return None


def inspect_gdn_dependencies() -> GDNDependencyStatusV1:
    """Inspect dependency metadata without importing Torch or PyG."""

    torch_available = util.find_spec("torch") is not None
    torch_geometric_available = util.find_spec("torch_geometric") is not None
    missing = tuple(
        name
        for name, available in (
            ("torch", torch_available),
            ("torch-geometric", torch_geometric_available),
        )
        if not available
    )
    return GDNDependencyStatusV1(
        torch_available=torch_available,
        torch_geometric_available=torch_geometric_available,
        torch_version=_installed_version("torch") if torch_available else None,
        torch_geometric_version=(
            _installed_version("torch-geometric")
            if torch_geometric_available
            else None
        ),
        backend_importable=torch_available and torch_geometric_available,
        missing_packages=missing,
    )


def require_gdn_optional_dependencies() -> GDNDependencyStatusV1:
    """Return dependency status or raise the stable project-owned error."""

    status = inspect_gdn_dependencies()
    if not status.backend_importable:
        raise GDNOptionalDependencyError(status)
    return status


def wrap_gdn_backend_import_error(
    error: BaseException,
    *,
    status: GDNDependencyStatusV1,
) -> GDNOptionalDependencyError:
    """Normalize a present-but-unimportable backend to the stable boundary."""

    return GDNOptionalDependencyError(
        status,
        detail=f"{type(error).__name__}: backend import failed",
    )


__all__ = [
    "GDNDependencyStatusV1",
    "GDNOptionalDependencyError",
    "GDN_OPTIONAL_DEPENDENCY_ISSUE_CODE",
    "inspect_gdn_dependencies",
    "require_gdn_optional_dependencies",
    "wrap_gdn_backend_import_error",
]
