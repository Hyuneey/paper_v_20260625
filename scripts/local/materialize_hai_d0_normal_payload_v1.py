"""Selective, path-silent materialization of D0 normal-only HAI payloads.

The three public stage functions have fixed allowlists: train1+train2, then
train3, then train4 only after model and threshold hashes have been supplied.
They never accept a caller payload list and never fetch any test or label file.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sys
from types import ModuleType
from typing import Any, Mapping, NoReturn, Sequence


OFFICIAL_REPOSITORY = "https://github.com/icsdataset/hai"
PINNED_COMMIT = "2a814cebc9a66b06c9e5cd545e2d72e65d383737"

FIT_SPECS = (
    ("hai-23.05/hai-train1.csv", "53007b0ba604fbf338e7ac2e08cd81d874b5d1388f3aecb213ddcba5bf2bec4a", 162_418_984),
    ("hai-23.05/hai-train2.csv", "0e520e82bf78a661ab19ce4967f3c766bd809820f457a9c90c365102d4534c56", 169_121_615),
)
CALIBRATION_SPECS = (
    ("hai-23.05/hai-train3.csv", "bfcec2dc05adea103e7491546b0e28268faaa26d3cc717d10f4595c94b81e85d", 72_774_793),
)
SANITY_SPECS = (
    ("hai-23.05/hai-train4.csv", "56658c83657d42a65db982b864362e0d0ffeb96d1f7b357d5e76e3a5c522d940", 114_494_940),
)
ALL_NORMAL_RELATIVE_PATHS = frozenset(item[0] for item in (*FIT_SPECS, *CALIBRATION_SPECS, *SANITY_SPECS))

BLOCKED = "D0_NORMAL_MATERIALIZATION_BLOCKED"
BLOCKED_STAGE = "D0_NORMAL_MATERIALIZATION_BLOCKED_STAGE_ORDER"
BLOCKED_CUSTODY = "D0_NORMAL_MATERIALIZATION_BLOCKED_CUSTODY"
BLOCKED_PATH = "D0_NORMAL_MATERIALIZATION_BLOCKED_PATH_GUARD"
_FAILURE_CODES = frozenset({BLOCKED, BLOCKED_STAGE, BLOCKED_CUSTODY, BLOCKED_PATH})


class D0NormalMaterializationError(RuntimeError):
    def __init__(self, code: str) -> None:
        self.code = code if code in _FAILURE_CODES else BLOCKED
        super().__init__(self.code)


def _fail(code: str) -> NoReturn:
    raise D0NormalMaterializationError(code)


@dataclass(frozen=True)
class D0NormalMaterializationResultV1:
    cache_root: Path
    stage: str
    official_source_match: bool
    pinned_commit_match: bool
    normal_file_hash_matches: tuple[bool, ...]
    normal_file_size_matches: tuple[bool, ...]
    test1_fetches: int = 0
    label_fetches: int = 0
    test2_fetches: int = 0
    scientific_parses: int = 0
    private_paths_exposed: int = 0

    def sanitized_payload(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "official_source_match": self.official_source_match,
            "pinned_commit_match": self.pinned_commit_match,
            "normal_file_hash_matches": list(self.normal_file_hash_matches),
            "normal_file_size_matches": list(self.normal_file_size_matches),
            "test1_fetches": self.test1_fetches,
            "label_fetches": self.label_fetches,
            "test2_fetches": self.test2_fetches,
            "scientific_parses": self.scientific_parses,
            "private_paths_exposed": self.private_paths_exposed,
        }


def _load_generic_helper(repository_root: Path) -> ModuleType:
    try:
        path = repository_root / "scripts/local/materialize_hai_inner_payload_v1.py"
        spec = importlib.util.spec_from_file_location("_task039e3_generic_acquisition_primitives", path)
        if spec is None or spec.loader is None:
            _fail(BLOCKED)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module
    except D0NormalMaterializationError:
        raise
    except BaseException:
        _fail(BLOCKED)


def _cache_root(repository_root: Path) -> Path:
    try:
        raw_base = os.environ.get("LOCALAPPDATA") if os.name == "nt" else os.environ.get("XDG_CACHE_HOME")
        base = Path(raw_base) if raw_base else Path.home() / ".cache"
        cache = base / "paper_v_20260625" / "official_hai_2305" / f"snapshot_{PINNED_COMMIT[:12]}_d0_normal_v1"
        resolved_repo = repository_root.resolve()
        resolved_cache = cache.resolve()
        if resolved_cache == resolved_repo or resolved_repo in resolved_cache.parents:
            _fail(BLOCKED_PATH)
        return cache
    except D0NormalMaterializationError:
        raise
    except BaseException:
        _fail(BLOCKED_PATH)


def _specs(module: ModuleType, raw_specs: Sequence[tuple[str, str, int]]) -> tuple[Any, ...]:
    result = tuple(module.PayloadSpec(relative, digest, size) for relative, digest, size in raw_specs)
    if any(item.relative_path not in ALL_NORMAL_RELATIVE_PATHS for item in result):
        _fail(BLOCKED_CUSTODY)
    return result


def _set_fixed_stage(module: ModuleType, specs: tuple[Any, ...]) -> None:
    module.PAYLOAD_SPECS = specs
    module.AUTHORIZED_PAYLOADS = tuple(item.relative_path for item in specs)


def _authority_sidecar_payload() -> dict[str, Any]:
    payload = {
        "artifact_type": "task039e3_r2r_d0_normal_materialization_authority_v1",
        "official_repository": OFFICIAL_REPOSITORY,
        "pinned_commit": PINNED_COMMIT,
        "task039ar_metadata_hash": "a7389cc123a544302b896c4c1ffc931a3c61c22318c0fa53c575cd1567d5fbfe",
        "task039ar_equivalence_hash": "7917f8736c119e774a945096f41f8abc18bce30267dd9e754c5a20157a5bf7a8",
        "allowed_relative_paths": sorted(ALL_NORMAL_RELATIVE_PATHS),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return {**payload, "artifact_hash": sha256(encoded).hexdigest()}


def _write_authority_sidecar(cache_root: Path) -> None:
    path = cache_root / ".d0_normal_authority.json"
    if path.exists():
        return
    temporary = path.with_suffix(".part")
    try:
        document = _authority_sidecar_payload()
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(document, stream, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        _fail(BLOCKED_CUSTODY)


def _validate_authority_sidecar(cache_root: Path) -> None:
    try:
        document = json.loads((cache_root / ".d0_normal_authority.json").read_text(encoding="utf-8"))
        expected = _authority_sidecar_payload()
        if document != expected:
            _fail(BLOCKED_CUSTODY)
    except D0NormalMaterializationError:
        raise
    except BaseException:
        _fail(BLOCKED_CUSTODY)


def _validate_source_identity(module: ModuleType, cache_root: Path) -> None:
    git_dir = cache_root / ".official.git"
    if git_dir.is_dir() and not git_dir.is_symlink():
        try:
            module._validate_repository_identity(git_dir, runner=module._run_silent)
            return
        except BaseException:
            _fail(BLOCKED_CUSTODY)
    _validate_authority_sidecar(cache_root)


def _validate_specs(module: ModuleType, cache_root: Path, specs: Sequence[Any]) -> None:
    for spec in specs:
        try:
            module.validate_payload(cache_root, spec)
        except BaseException:
            _fail(BLOCKED_CUSTODY)


def _load_stage_state(cache_root: Path) -> Mapping[str, Any]:
    path = cache_root / ".d0_normal_stage.json"
    if not path.exists():
        return {}
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(document, dict):
            _fail(BLOCKED_STAGE)
        observed = document.get("artifact_hash")
        payload = dict(document)
        payload.pop("artifact_hash", None)
        if observed != sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest():
            _fail(BLOCKED_STAGE)
        return document
    except D0NormalMaterializationError:
        raise
    except BaseException:
        _fail(BLOCKED_STAGE)


def _write_stage_state(cache_root: Path, stage: str, *, model_hash: str | None = None, threshold_hash: str | None = None) -> None:
    path = cache_root / ".d0_normal_stage.json"
    temporary = path.with_suffix(".part")
    payload: dict[str, Any] = {
        "artifact_type": "task039e3_r2r_d0_normal_materialization_stage_v1",
        "stage": stage,
        "model_hash": model_hash,
        "threshold_hash": threshold_hash,
    }
    payload["artifact_hash"] = sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()
    try:
        if temporary.exists():
            _fail(BLOCKED_STAGE)
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except D0NormalMaterializationError:
        raise
    except BaseException:
        _fail(BLOCKED_STAGE)


def _materialize_specs(repository_root: Path, cache_root: Path, raw_specs: Sequence[tuple[str, str, int]]) -> None:
    module = _load_generic_helper(repository_root)
    specs = _specs(module, raw_specs)
    _set_fixed_stage(module, specs)
    try:
        cache_root.parent.mkdir(parents=True, exist_ok=True)
        if cache_root.exists():
            if cache_root.is_symlink() or not cache_root.is_dir():
                _fail(BLOCKED_CUSTODY)
            _validate_source_identity(module, cache_root)
        else:
            cache_root.mkdir(parents=True, exist_ok=False)
            _write_authority_sidecar(cache_root)
        missing: list[Any] = []
        for spec in specs:
            target = cache_root / PurePosixPath(spec.relative_path)
            if target.exists():
                module.validate_payload(cache_root, spec)
            else:
                missing.append(spec)
        if missing:
            _set_fixed_stage(module, tuple(missing))
            git_dir = cache_root / ".official.git"
            if not git_dir.exists():
                try:
                    prepared, _ = module._prepare_pinned_bare_repository(cache_root, runner=module._run_silent)
                    if prepared != git_dir:
                        _fail(BLOCKED_CUSTODY)
                except BaseException:
                    if git_dir.exists() and not git_dir.is_symlink():
                        shutil.rmtree(git_dir, ignore_errors=True)
            acquired = False
            if git_dir.is_dir() and not git_dir.is_symlink() and module._git_lfs_available(repository_root, module._run_silent):
                try:
                    module._fetch_with_lfs(git_dir, cache_root, runner=module._run_silent)
                    acquired = True
                except BaseException:
                    acquired = False
            if not acquired:
                module._fetch_with_official_distribution(repository_root, cache_root)
            _write_authority_sidecar(cache_root)
        _validate_source_identity(module, cache_root)
        _validate_specs(module, cache_root, specs)
    except D0NormalMaterializationError:
        raise
    except BaseException:
        _fail(BLOCKED)


def _result(cache_root: Path, stage: str, count: int) -> D0NormalMaterializationResultV1:
    return D0NormalMaterializationResultV1(
        cache_root=cache_root,
        stage=stage,
        official_source_match=True,
        pinned_commit_match=True,
        normal_file_hash_matches=tuple(True for _ in range(count)),
        normal_file_size_matches=tuple(True for _ in range(count)),
    )


def materialize_fit_payloads_v1(repository_root: Path) -> D0NormalMaterializationResultV1:
    cache_root = _cache_root(repository_root)
    state = _load_stage_state(cache_root) if cache_root.exists() else {}
    if state and state.get("stage") not in {"FIT_READY"}:
        _fail(BLOCKED_STAGE)
    _materialize_specs(repository_root, cache_root, FIT_SPECS)
    _write_stage_state(cache_root, "FIT_READY")
    return _result(cache_root, "FIT_READY", 2)


def materialize_calibration_payload_v1(repository_root: Path, cache_root: Path) -> D0NormalMaterializationResultV1:
    if cache_root.resolve() != _cache_root(repository_root).resolve():
        _fail(BLOCKED_PATH)
    state = _load_stage_state(cache_root)
    if state.get("stage") != "FIT_READY":
        _fail(BLOCKED_STAGE)
    _materialize_specs(repository_root, cache_root, CALIBRATION_SPECS)
    _write_stage_state(cache_root, "CALIBRATION_READY")
    return _result(cache_root, "CALIBRATION_READY", 1)


def materialize_train4_sanity_payload_v1(
    repository_root: Path,
    cache_root: Path,
    *,
    model_hash: str,
    threshold_hash: str,
) -> D0NormalMaterializationResultV1:
    if cache_root.resolve() != _cache_root(repository_root).resolve():
        _fail(BLOCKED_PATH)
    if not all(len(value) == 64 and all(char in "0123456789abcdef" for char in value) for value in (model_hash, threshold_hash)):
        _fail(BLOCKED_STAGE)
    state = _load_stage_state(cache_root)
    if state.get("stage") != "CALIBRATION_READY":
        _fail(BLOCKED_STAGE)
    _materialize_specs(repository_root, cache_root, SANITY_SPECS)
    _write_stage_state(cache_root, "SANITY_READY", model_hash=model_hash, threshold_hash=threshold_hash)
    return _result(cache_root, "SANITY_READY", 1)


__all__ = [
    "D0NormalMaterializationError",
    "D0NormalMaterializationResultV1",
    "materialize_fit_payloads_v1",
    "materialize_calibration_payload_v1",
    "materialize_train4_sanity_payload_v1",
]
