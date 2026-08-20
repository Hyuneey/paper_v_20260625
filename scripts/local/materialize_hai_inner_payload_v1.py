"""Path-silent materialization of the frozen HAI 23.05 INNER payload.

The helper reconstructs only the authorized test1 feature and label files from
the pinned official source.  Private cache and binding paths are never emitted.
No CSV or label content is parsed.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tempfile
from types import ModuleType
from typing import Any, NoReturn, TextIO
import urllib.error
import urllib.parse
import urllib.request
import zipfile


OFFICIAL_REPOSITORY = "https://github.com/icsdataset/hai"
PINNED_COMMIT = "2a814cebc9a66b06c9e5cd545e2d72e65d383737"
FEATURE_RELATIVE_PATH = "hai-23.05/hai-test1.csv"
LABEL_RELATIVE_PATH = "hai-23.05/label-test1.csv"
AUTHORIZED_PAYLOADS = (FEATURE_RELATIVE_PATH, LABEL_RELATIVE_PATH)

FEATURE_SHA256 = (
    "78c7f1d4de1f2ab9ccc2f8c719f80f831033543adb0c81d0d78f84f40838d4be"
)
FEATURE_SIZE = 31_255_559
LABEL_SHA256 = (
    "eaf69edb9c5834bc393afd7bf658b5e408d34fd7bfc3261f80516765fb818fbc"
)
LABEL_SIZE = 1_242_017

TASK039AR_METADATA_HASH = (
    "a7389cc123a544302b896c4c1ffc931a3c61c22318c0fa53c575cd1567d5fbfe"
)
TASK039AR_EQUIVALENCE_HASH = (
    "7917f8736c119e774a945096f41f8abc18bce30267dd9e754c5a20157a5bf7a8"
)
TASK039AR_CONFIG_HASH = (
    "b568a7491f648e216011a6c293cbed644a535ad4c3e3e4cad2c1b834b6a7a958"
)
KAGGLE_OWNER = "icsdataset"
KAGGLE_SLUG = "hai-security-dataset"
KAGGLE_VERSION = 10

ROUTE_GIT_LFS = "OFFICIAL_GIT_LFS_SELECTIVE"
ROUTE_DISTRIBUTION = "OFFICIAL_KAGGLE_SELECTIVE_FALLBACK"
ROUTE_CACHE_REUSE = "PINNED_OFFICIAL_CACHE_REUSE"
RESULT_SIDECAR_NAME = ".env.custody.local.materialization-v1.json"

BLOCKED_NETWORK = "CODE_MATERIALIZATION_BLOCKED_OFFICIAL_NETWORK"
BLOCKED_GIT_LFS = "CODE_MATERIALIZATION_BLOCKED_GIT_LFS_UNAVAILABLE"
BLOCKED_PINNED_COMMIT = "CODE_MATERIALIZATION_BLOCKED_PINNED_COMMIT"
BLOCKED_SOURCE = "CODE_MATERIALIZATION_BLOCKED_SOURCE_MISMATCH"
BLOCKED_CUSTODY = "CODE_MATERIALIZATION_BLOCKED_TEST1_CUSTODY_MISMATCH"
BLOCKED_CACHE = "CODE_MATERIALIZATION_BLOCKED_NONCANONICAL_CACHE"
BLOCKED_BINDING = "CODE_MATERIALIZATION_BLOCKED_LOCAL_BINDING"
BLOCKED_PATH_GUARD = "CODE_MATERIALIZATION_BLOCKED_PATH_GUARD"
BLOCKED_UNEXPECTED = "CODE_MATERIALIZATION_BLOCKED_UNEXPECTED"

_FAILURE_CODES = frozenset(
    {
        BLOCKED_NETWORK,
        BLOCKED_GIT_LFS,
        BLOCKED_PINNED_COMMIT,
        BLOCKED_SOURCE,
        BLOCKED_CUSTODY,
        BLOCKED_CACHE,
        BLOCKED_BINDING,
        BLOCKED_PATH_GUARD,
        BLOCKED_UNEXPECTED,
    }
)


class HAIInnerMaterializationError(RuntimeError):
    """A fixed-code failure that cannot contain a private path."""

    def __init__(self, code: str) -> None:
        if code not in _FAILURE_CODES:
            code = BLOCKED_UNEXPECTED
        self.code = code
        super().__init__(code)


def _raise(code: str) -> NoReturn:
    raise HAIInnerMaterializationError(code)


@dataclass(frozen=True)
class PayloadSpec:
    relative_path: str
    sha256: str
    size_bytes: int


FEATURE_SPEC = PayloadSpec(FEATURE_RELATIVE_PATH, FEATURE_SHA256, FEATURE_SIZE)
LABEL_SPEC = PayloadSpec(LABEL_RELATIVE_PATH, LABEL_SHA256, LABEL_SIZE)
PAYLOAD_SPECS = (FEATURE_SPEC, LABEL_SPEC)


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: bytes = b""


CommandRunner = Callable[
    [Sequence[str], Path, Mapping[str, str] | None], CommandResult
]


@dataclass(frozen=True)
class HAIInnerMaterializationResult:
    cache_root: Path
    official_source_match: bool
    pinned_commit_match: bool
    acquisition_route: str
    git_lfs_available: bool
    existing_cache_reused: bool
    test1_feature_materialized: bool
    test1_label_materialized: bool
    test1_feature_hash_match: bool
    test1_label_hash_match: bool
    test1_feature_size_match: bool
    test1_label_size_match: bool
    official_git_fetches: int
    official_lfs_test1_fetches: int
    official_lfs_label_test1_fetches: int
    official_distribution_test1_fetches: int
    official_distribution_label_test1_fetches: int
    test2_lfs_payload_fetches: int
    test2_file_opens: int
    test2_hashes: int
    scientific_feature_parses: int
    scientific_label_parses: int
    attack_event_derivations: int
    rule_executions: int
    metric_computations: int
    private_paths_emitted: int
    local_binding_configured: bool = False
    local_binding_ignored: bool = False
    local_binding_tracked: bool = False
    main_registry_binding_present: bool = False
    main_locator_binding_present: bool = False
    supplement_registry_binding_present: bool = False
    supplement_locator_binding_present: bool = False

    def sanitized_payload(self) -> dict[str, Any]:
        return {
            "artifact_type": "task039e3_r2r_hai_inner_materialization_local_state",
            "schema_version": "1.0.0",
            "official_source_match": self.official_source_match,
            "pinned_commit_match": self.pinned_commit_match,
            "acquisition_route": self.acquisition_route,
            "git_lfs_available": self.git_lfs_available,
            "existing_cache_reused": self.existing_cache_reused,
            "test1_feature_materialized": self.test1_feature_materialized,
            "test1_label_materialized": self.test1_label_materialized,
            "test1_feature_hash_match": self.test1_feature_hash_match,
            "test1_label_hash_match": self.test1_label_hash_match,
            "test1_feature_size_match": self.test1_feature_size_match,
            "test1_label_size_match": self.test1_label_size_match,
            "official_git_fetches": self.official_git_fetches,
            "official_lfs_test1_fetches": self.official_lfs_test1_fetches,
            "official_lfs_label_test1_fetches": (
                self.official_lfs_label_test1_fetches
            ),
            "official_distribution_test1_fetches": (
                self.official_distribution_test1_fetches
            ),
            "official_distribution_label_test1_fetches": (
                self.official_distribution_label_test1_fetches
            ),
            "test2_lfs_payload_fetches": self.test2_lfs_payload_fetches,
            "test2_file_opens": self.test2_file_opens,
            "test2_hashes": self.test2_hashes,
            "scientific_feature_parses": self.scientific_feature_parses,
            "scientific_label_parses": self.scientific_label_parses,
            "attack_event_derivations": self.attack_event_derivations,
            "rule_executions": self.rule_executions,
            "metric_computations": self.metric_computations,
            "private_paths_emitted": self.private_paths_emitted,
            "local_binding_configured": self.local_binding_configured,
            "local_binding_ignored": self.local_binding_ignored,
            "local_binding_tracked": self.local_binding_tracked,
            "main_registry_binding_present": self.main_registry_binding_present,
            "main_locator_binding_present": self.main_locator_binding_present,
            "supplement_registry_binding_present": (
                self.supplement_registry_binding_present
            ),
            "supplement_locator_binding_present": (
                self.supplement_locator_binding_present
            ),
        }


def _run_silent(
    arguments: Sequence[str],
    cwd: Path,
    environment: Mapping[str, str] | None = None,
) -> CommandResult:
    try:
        merged = os.environ.copy()
        if environment:
            merged.update(environment)
        completed = subprocess.run(
            list(arguments),
            cwd=cwd,
            env=merged,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        return CommandResult(completed.returncode, completed.stdout)
    except BaseException:
        return CommandResult(127, b"")


def _require_success(result: CommandResult, code: str) -> bytes:
    if result.returncode != 0:
        _raise(code)
    return result.stdout


def _canonical_url(value: str) -> str:
    normalized = value.strip().rstrip("/")
    if normalized.endswith(".git"):
        normalized = normalized[:-4]
    return normalized


def require_official_source(value: str) -> None:
    if _canonical_url(value) != OFFICIAL_REPOSITORY:
        _raise(BLOCKED_SOURCE)


def require_pinned_revision(value: str) -> None:
    if value != PINNED_COMMIT:
        _raise(BLOCKED_PINNED_COMMIT)


def require_authorized_payload(relative_path: str) -> None:
    if relative_path not in AUTHORIZED_PAYLOADS:
        _raise(BLOCKED_PATH_GUARD)


def lfs_fetch_arguments(spec: PayloadSpec) -> tuple[str, ...]:
    require_authorized_payload(spec.relative_path)
    return (
        "git",
        "lfs",
        "fetch",
        f"--include={spec.relative_path}",
        "--exclude=",
        "origin",
        PINNED_COMMIT,
    )


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _payload_path(root: Path, spec: PayloadSpec) -> Path:
    require_authorized_payload(spec.relative_path)
    return root / Path(*PurePosixPath(spec.relative_path).parts)


def validate_payload(
    root: Path,
    spec: PayloadSpec,
    *,
    hash_file: Callable[[Path], str] = _sha256_file,
) -> None:
    path = _payload_path(root, spec)
    try:
        if path.is_symlink() or not path.is_file():
            _raise(BLOCKED_CUSTODY)
        if path.stat().st_size != spec.size_bytes:
            _raise(BLOCKED_CUSTODY)
        if hash_file(path) != spec.sha256:
            _raise(BLOCKED_CUSTODY)
    except HAIInnerMaterializationError:
        raise
    except BaseException:
        _raise(BLOCKED_CUSTODY)


def require_cache_outside_repository(cache_root: Path, repository_root: Path) -> None:
    try:
        cache = cache_root.resolve()
        repository = repository_root.resolve(strict=True)
        if cache == repository or repository in cache.parents:
            _raise(BLOCKED_PATH_GUARD)
    except HAIInnerMaterializationError:
        raise
    except BaseException:
        _raise(BLOCKED_PATH_GUARD)


def _private_cache_root(repository_root: Path) -> Path:
    try:
        if os.name == "nt":
            raw_base = os.environ.get("LOCALAPPDATA")
        else:
            raw_base = os.environ.get("XDG_CACHE_HOME")
        base = Path(raw_base) if raw_base else Path.home() / ".cache"
        result = (
            base
            / "paper_v_20260625"
            / "official_hai_2305"
            / f"snapshot_{PINNED_COMMIT[:12]}_inner_v1"
        )
        require_cache_outside_repository(result, repository_root)
        return result
    except HAIInnerMaterializationError:
        raise
    except BaseException:
        _raise(BLOCKED_PATH_GUARD)


def _decode_output(result: CommandResult, code: str) -> str:
    content = _require_success(result, code)
    try:
        return content.decode("utf-8").strip()
    except BaseException:
        _raise(code)


def _git_lfs_available(
    repository_root: Path,
    runner: CommandRunner,
) -> bool:
    return runner(("git", "lfs", "version"), repository_root, None).returncode == 0


def _validate_repository_identity(
    git_dir: Path,
    *,
    runner: CommandRunner,
) -> None:
    origin = _decode_output(
        runner(("git", "remote", "get-url", "origin"), git_dir, None),
        BLOCKED_SOURCE,
    )
    require_official_source(origin)
    head = _decode_output(
        runner(("git", "rev-parse", "HEAD"), git_dir, None),
        BLOCKED_PINNED_COMMIT,
    )
    require_pinned_revision(head)


def _validate_existing_cache(
    cache_root: Path,
    *,
    runner: CommandRunner,
    specs: Sequence[PayloadSpec] = PAYLOAD_SPECS,
) -> None:
    try:
        if cache_root.is_symlink() or not cache_root.is_dir():
            _raise(BLOCKED_CACHE)
        git_dir = cache_root / ".official.git"
        if git_dir.is_symlink() or not git_dir.is_dir():
            _raise(BLOCKED_CACHE)
        _validate_repository_identity(git_dir, runner=runner)
        for spec in specs:
            validate_payload(cache_root, spec)
    except HAIInnerMaterializationError as failure:
        if failure.code in {BLOCKED_SOURCE, BLOCKED_PINNED_COMMIT, BLOCKED_CUSTODY}:
            _raise(BLOCKED_CACHE)
        raise
    except BaseException:
        _raise(BLOCKED_CACHE)


def _parse_lfs_pointer(content: str, spec: PayloadSpec) -> None:
    lines = content.strip().splitlines()
    expected = (
        "version https://git-lfs.github.com/spec/v1",
        f"oid sha256:{spec.sha256}",
        f"size {spec.size_bytes}",
    )
    if tuple(lines) != expected:
        _raise(BLOCKED_CUSTODY)


def _prepare_pinned_bare_repository(
    staging_root: Path,
    *,
    runner: CommandRunner,
) -> tuple[Path, int]:
    git_dir = staging_root / ".official.git"
    environment = {
        "GIT_LFS_SKIP_SMUDGE": "1",
        "GIT_TERMINAL_PROMPT": "0",
    }
    clone = runner(
        (
            "git",
            "clone",
            "--bare",
            "--filter=blob:none",
            "--no-tags",
            OFFICIAL_REPOSITORY,
            str(git_dir),
        ),
        staging_root,
        environment,
    )
    _require_success(clone, BLOCKED_NETWORK)
    fetches = 1
    origin = _decode_output(
        runner(("git", "remote", "get-url", "origin"), git_dir, environment),
        BLOCKED_SOURCE,
    )
    require_official_source(origin)
    present = runner(
        ("git", "cat-file", "-e", f"{PINNED_COMMIT}^{{commit}}"),
        git_dir,
        environment,
    )
    if present.returncode != 0:
        _require_success(
            runner(
                ("git", "fetch", "--no-tags", "origin", PINNED_COMMIT),
                git_dir,
                environment,
            ),
            BLOCKED_NETWORK,
        )
        fetches += 1
    _require_success(
        runner(
            ("git", "cat-file", "-e", f"{PINNED_COMMIT}^{{commit}}"),
            git_dir,
            environment,
        ),
        BLOCKED_PINNED_COMMIT,
    )
    _require_success(
        runner(
            ("git", "update-ref", "--no-deref", "HEAD", PINNED_COMMIT),
            git_dir,
            environment,
        ),
        BLOCKED_PINNED_COMMIT,
    )
    _validate_repository_identity(git_dir, runner=runner)
    for spec in PAYLOAD_SPECS:
        pointer = _decode_output(
            runner(
                ("git", "show", f"{PINNED_COMMIT}:{spec.relative_path}"),
                git_dir,
                environment,
            ),
            BLOCKED_PINNED_COMMIT,
        )
        _parse_lfs_pointer(pointer, spec)
    return git_dir, fetches


def _copy_lfs_object(git_dir: Path, staging_root: Path, spec: PayloadSpec) -> None:
    source = (
        git_dir
        / "lfs"
        / "objects"
        / spec.sha256[:2]
        / spec.sha256[2:4]
        / spec.sha256
    )
    destination = _payload_path(staging_root, spec)
    try:
        if source.is_symlink() or not source.is_file():
            _raise(BLOCKED_CUSTODY)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + ".part")
        with source.open("rb") as input_stream, temporary.open("wb") as output_stream:
            shutil.copyfileobj(input_stream, output_stream, length=1024 * 1024)
        os.replace(temporary, destination)
        validate_payload(staging_root, spec)
    except HAIInnerMaterializationError:
        raise
    except BaseException:
        _raise(BLOCKED_CUSTODY)


def _fetch_with_lfs(
    git_dir: Path,
    staging_root: Path,
    *,
    runner: CommandRunner,
) -> None:
    environment = {
        "GIT_LFS_SKIP_SMUDGE": "1",
        "GIT_TERMINAL_PROMPT": "0",
    }
    for spec in PAYLOAD_SPECS:
        _require_success(
            runner(lfs_fetch_arguments(spec), git_dir, environment),
            BLOCKED_GIT_LFS,
        )
        _copy_lfs_object(git_dir, staging_root, spec)


def _canonical_hash(
    document: Mapping[str, Any],
    field_name: str = "artifact_hash",
) -> str:
    payload = dict(document)
    payload.pop(field_name, None)
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _load_fallback_authority(repository_root: Path) -> tuple[dict[str, Any], tuple[str, ...]]:
    try:
        metadata = json.loads(
            (
                repository_root
                / "docs/task_reports/TASK-039AR_KAGGLE_METADATA_FREEZE.json"
            ).read_text(encoding="utf-8")
        )
        equivalence = json.loads(
            (
                repository_root
                / "docs/task_reports/TASK-039AR_BYTE_EQUIVALENCE_REPORT.json"
            ).read_text(encoding="utf-8")
        )
        config = json.loads(
            (
                repository_root
                / "configs/data/hai_2305_official_distribution_remediation.json"
            ).read_text(encoding="utf-8")
        )
    except BaseException:
        _raise(BLOCKED_GIT_LFS)
    if (
        metadata.get("artifact_hash") != TASK039AR_METADATA_HASH
        or _canonical_hash(metadata) != TASK039AR_METADATA_HASH
        or equivalence.get("artifact_hash") != TASK039AR_EQUIVALENCE_HASH
        or _canonical_hash(equivalence) != TASK039AR_EQUIVALENCE_HASH
        or config.get("config_hash") != TASK039AR_CONFIG_HASH
        or _canonical_hash(config, "config_hash") != TASK039AR_CONFIG_HASH
    ):
        _raise(BLOCKED_GIT_LFS)
    if (
        metadata.get("owner") != KAGGLE_OWNER
        or metadata.get("slug") != KAGGLE_SLUG
        or metadata.get("dataset_version_identifier") != KAGGLE_VERSION
        or metadata.get("official_git_repository") != OFFICIAL_REPOSITORY
        or metadata.get("official_git_snapshot_commit") != PINNED_COMMIT
        or equivalence.get("status")
        != "passed_official_distribution_byte_equivalence"
        or equivalence.get("all_files_byte_equivalent") is not True
    ):
        _raise(BLOCKED_GIT_LFS)
    records = {
        item.get("relative_path"): item
        for item in equivalence.get("records", [])
        if isinstance(item, dict)
    }
    for spec in PAYLOAD_SPECS:
        record = records.get(spec.relative_path)
        if (
            not isinstance(record, dict)
            or record.get("byte_equivalent") is not True
            or record.get("official_lfs_oid_sha256") != spec.sha256
            or record.get("task039a_expected_sha256") != spec.sha256
            or record.get("official_lfs_pointer_size_bytes") != spec.size_bytes
            or record.get("task039a_expected_size_bytes") != spec.size_bytes
        ):
            _raise(BLOCKED_GIT_LFS)
    hosts = tuple(str(item) for item in config.get("allowed_download_hosts", ()))
    if set(hosts) != {"www.kaggle.com", "storage.googleapis.com"}:
        _raise(BLOCKED_GIT_LFS)
    return metadata, hosts


class _RestrictedRedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self, allowed_hosts: Sequence[str]) -> None:
        super().__init__()
        self._allowed_hosts = frozenset(allowed_hosts)

    def redirect_request(  # type: ignore[override]
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> urllib.request.Request | None:
        parsed = urllib.parse.urlparse(newurl)
        if parsed.scheme != "https" or parsed.hostname not in self._allowed_hosts:
            _raise(BLOCKED_NETWORK)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _download_selective_payload(
    *,
    url: str,
    staging_root: Path,
    spec: PayloadSpec,
    allowed_hosts: Sequence[str],
) -> None:
    require_authorized_payload(spec.relative_path)
    archive: Path | None = None
    try:
        opener = urllib.request.build_opener(_RestrictedRedirectHandler(allowed_hosts))
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/zip",
                "User-Agent": "paperworks-task039e3-materialization/1.0",
            },
            method="GET",
        )
        destination = _payload_path(staging_root, spec)
        destination.parent.mkdir(parents=True, exist_ok=True)
        archive = destination.with_suffix(destination.suffix + ".download")
        with opener.open(request, timeout=300) as response, archive.open("wb") as out:
            shutil.copyfileobj(response, out, length=1024 * 1024)
        temporary = destination.with_suffix(destination.suffix + ".part")
        if zipfile.is_zipfile(archive):
            with zipfile.ZipFile(archive, "r") as bundle:
                members = [item for item in bundle.infolist() if not item.is_dir()]
                if len(members) != 1:
                    _raise(BLOCKED_NETWORK)
                member = members[0]
                observed = PurePosixPath(member.filename)
                expected = PurePosixPath(spec.relative_path)
                if observed.is_absolute() or ".." in observed.parts:
                    _raise(BLOCKED_NETWORK)
                if observed not in {expected, PurePosixPath(expected.name)}:
                    _raise(BLOCKED_NETWORK)
                with bundle.open(member, "r") as source, temporary.open("wb") as out:
                    shutil.copyfileobj(source, out, length=1024 * 1024)
        else:
            os.replace(archive, temporary)
            archive = None
        os.replace(temporary, destination)
        validate_payload(staging_root, spec)
    except HAIInnerMaterializationError:
        raise
    except (urllib.error.URLError, TimeoutError, OSError, zipfile.BadZipFile):
        _raise(BLOCKED_NETWORK)
    finally:
        if archive is not None:
            try:
                archive.unlink(missing_ok=True)
            except BaseException:
                pass


def _fetch_with_official_distribution(
    repository_root: Path,
    staging_root: Path,
) -> None:
    metadata, hosts = _load_fallback_authority(repository_root)
    template = str(metadata.get("selective_download_endpoint_template", ""))
    expected_template = (
        "https://www.kaggle.com/api/v1/datasets/download/"
        "{owner}/{slug}/{file_name}?datasetVersionNumber={version}"
    )
    if template != expected_template:
        _raise(BLOCKED_GIT_LFS)
    for spec in PAYLOAD_SPECS:
        encoded = urllib.parse.quote(spec.relative_path, safe="")
        url = template.format(
            owner=KAGGLE_OWNER,
            slug=KAGGLE_SLUG,
            file_name=encoded,
            version=KAGGLE_VERSION,
        )
        _download_selective_payload(
            url=url,
            staging_root=staging_root,
            spec=spec,
            allowed_hosts=hosts,
        )


def _safe_cleanup_staging(staging: Path, expected_parent: Path) -> None:
    try:
        if (
            staging.parent.resolve() == expected_parent.resolve()
            and staging.name.endswith(".staging-v1")
            and staging.exists()
            and not staging.is_symlink()
        ):
            shutil.rmtree(staging)
    except BaseException:
        pass


def _new_result(
    *,
    cache_root: Path,
    route: str,
    lfs_available: bool,
    reused: bool,
    git_fetches: int,
) -> HAIInnerMaterializationResult:
    return HAIInnerMaterializationResult(
        cache_root=cache_root,
        official_source_match=True,
        pinned_commit_match=True,
        acquisition_route=route,
        git_lfs_available=lfs_available,
        existing_cache_reused=reused,
        test1_feature_materialized=True,
        test1_label_materialized=True,
        test1_feature_hash_match=True,
        test1_label_hash_match=True,
        test1_feature_size_match=True,
        test1_label_size_match=True,
        official_git_fetches=git_fetches,
        official_lfs_test1_fetches=(0 if reused or route != ROUTE_GIT_LFS else 1),
        official_lfs_label_test1_fetches=(
            0 if reused or route != ROUTE_GIT_LFS else 1
        ),
        official_distribution_test1_fetches=(
            0 if reused or route != ROUTE_DISTRIBUTION else 1
        ),
        official_distribution_label_test1_fetches=(
            0 if reused or route != ROUTE_DISTRIBUTION else 1
        ),
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


def materialize_payload(
    repository_root: Path,
    *,
    cache_root: Path | None = None,
    runner: CommandRunner = _run_silent,
) -> HAIInnerMaterializationResult:
    require_pinned_revision(PINNED_COMMIT)
    chosen = cache_root if cache_root is not None else _private_cache_root(repository_root)
    require_cache_outside_repository(chosen, repository_root)
    lfs_available = _git_lfs_available(repository_root, runner)
    if chosen.exists():
        _validate_existing_cache(chosen, runner=runner)
        return _new_result(
            cache_root=chosen,
            route=ROUTE_CACHE_REUSE,
            lfs_available=lfs_available,
            reused=True,
            git_fetches=0,
        )

    parent = chosen.parent
    staging = parent / f"{chosen.name}.staging-v1"
    try:
        parent.mkdir(parents=True, exist_ok=True)
        if staging.exists() or staging.is_symlink():
            _raise(BLOCKED_CACHE)
        staging.mkdir()
        git_dir, git_fetches = _prepare_pinned_bare_repository(
            staging, runner=runner
        )
        route = ROUTE_GIT_LFS
        if lfs_available:
            try:
                _fetch_with_lfs(git_dir, staging, runner=runner)
            except HAIInnerMaterializationError as failure:
                if failure.code != BLOCKED_GIT_LFS:
                    raise
                route = ROUTE_DISTRIBUTION
                _fetch_with_official_distribution(repository_root, staging)
        else:
            route = ROUTE_DISTRIBUTION
            _fetch_with_official_distribution(repository_root, staging)
        for spec in PAYLOAD_SPECS:
            validate_payload(staging, spec)
        os.replace(staging, chosen)
        _validate_existing_cache(chosen, runner=runner)
        return _new_result(
            cache_root=chosen,
            route=route,
            lfs_available=lfs_available,
            reused=False,
            git_fetches=git_fetches,
        )
    except HAIInnerMaterializationError:
        _safe_cleanup_staging(staging, parent)
        raise
    except BaseException:
        _safe_cleanup_staging(staging, parent)
        _raise(BLOCKED_UNEXPECTED)


def _load_binding_helper() -> ModuleType:
    path = Path(__file__).with_name("bootstrap_custody_bindings_v1.py")
    spec = importlib.util.spec_from_file_location(
        "_task039e3_local_binding_helper", path
    )
    if spec is None or spec.loader is None:
        _raise(BLOCKED_BINDING)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        _raise(BLOCKED_BINDING)
    return module


def _default_ignored_check(repository_root: Path) -> bool:
    return (
        _run_silent(
            ("git", "check-ignore", "-q", ".env.custody.local"),
            repository_root,
            None,
        ).returncode
        == 0
    )


def _default_tracked_check(repository_root: Path) -> bool:
    return (
        _run_silent(
            ("git", "ls-files", "--error-unmatch", ".env.custody.local"),
            repository_root,
            None,
        ).returncode
        == 0
    )


def persist_hai_binding(
    repository_root: Path,
    result: HAIInnerMaterializationResult,
    *,
    environ: Mapping[str, str],
    ignored_check: Callable[[Path], bool] = _default_ignored_check,
    tracked_check: Callable[[Path], bool] = _default_tracked_check,
    binding_helper: ModuleType | None = None,
) -> HAIInnerMaterializationResult:
    helper = binding_helper if binding_helper is not None else _load_binding_helper()
    env_path = repository_root / helper.ENV_FILE_NAME
    if not ignored_check(repository_root) or tracked_check(repository_root):
        _raise(BLOCKED_BINDING)
    if env_path.is_symlink():
        _raise(BLOCKED_BINDING)
    values: dict[str, str] = {}
    if env_path.exists():
        try:
            values.update(helper._read_env_file(env_path))
        except BaseException:
            _raise(BLOCKED_BINDING)
    values[helper.HAI_DATA_ROOT_KEY] = str(result.cache_root)
    for key in helper.ALLOWED_KEYS[1:]:
        value = environ.get(key)
        if isinstance(value, str) and value:
            values[key] = value
    try:
        helper._write_env_file(env_path, values)
        reloaded = helper._read_env_file(env_path)
        if reloaded != values or not helper._apply_permission_policy(env_path):
            _raise(BLOCKED_BINDING)
        helper.validate_hai_data_root(reloaded[helper.HAI_DATA_ROOT_KEY])
    except HAIInnerMaterializationError:
        raise
    except BaseException:
        _raise(BLOCKED_BINDING)
    return replace(
        result,
        local_binding_configured=True,
        local_binding_ignored=True,
        local_binding_tracked=False,
        main_registry_binding_present=helper.MAIN_REGISTRY_KEY in reloaded,
        main_locator_binding_present=helper.MAIN_LOCATOR_KEY in reloaded,
        supplement_registry_binding_present=(
            helper.SUPPLEMENT_REGISTRY_KEY in reloaded
        ),
        supplement_locator_binding_present=(
            helper.SUPPLEMENT_LOCATOR_KEY in reloaded
        ),
    )


def _write_local_state(
    repository_root: Path,
    result: HAIInnerMaterializationResult,
) -> None:
    payload = result.sanitized_payload()
    document = dict(payload)
    document["artifact_hash"] = _canonical_hash(payload)
    target = repository_root / RESULT_SIDECAR_NAME
    temporary: Path | None = None
    try:
        encoded = json.dumps(
            document,
            sort_keys=True,
            indent=2,
            ensure_ascii=True,
            allow_nan=False,
        ) + "\n"
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=repository_root,
            prefix=RESULT_SIDECAR_NAME + ".",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, target)
        temporary = None
        os.chmod(target, 0o600)
    except BaseException:
        _raise(BLOCKED_BINDING)
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except BaseException:
                pass


def _emit_success(result: HAIInnerMaterializationResult, output: TextIO) -> None:
    lines = (
        "hai_inner_materialization = PASS",
        "official_source_match = true",
        "pinned_commit_match = true",
        f"git_lfs_available = {str(result.git_lfs_available).lower()}",
        "test1_feature_materialized = true",
        "test1_label_materialized = true",
        "test1_feature_hash_match = true",
        "test1_label_hash_match = true",
        "test1_feature_size_match = true",
        "test1_label_size_match = true",
        f"test2_lfs_payload_fetches = {result.test2_lfs_payload_fetches}",
        f"private_paths_emitted = {result.private_paths_emitted}",
    )
    output.write("\n".join(lines) + "\n")


def run(repository_root: Path) -> HAIInnerMaterializationResult:
    result = materialize_payload(repository_root)
    result = persist_hai_binding(
        repository_root,
        result,
        environ=os.environ,
    )
    _write_local_state(repository_root, result)
    return result


def main() -> int:
    sys.tracebacklimit = 0
    try:
        repository_root = Path(__file__).resolve().parents[2]
        result = run(repository_root)
    except HAIInnerMaterializationError as failure:
        sys.stdout.write(failure.code + "\n")
        return 2
    except BaseException:
        sys.stdout.write(BLOCKED_UNEXPECTED + "\n")
        return 2
    _emit_success(result, sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
