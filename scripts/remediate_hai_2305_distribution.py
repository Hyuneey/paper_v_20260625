#!/usr/bin/env python3
"""Freeze and verify the official Kaggle HAI 23.05 distribution.

The CLI has three deliberately separate phases:

``metadata`` freezes sanitized metadata without downloading payloads;
``download`` requires that receipt to be committed, then downloads exactly the
ten allowlisted files; and ``materialize-lfs`` installs only verified bytes into
the local official Git checkout before the unchanged TASK-039A audit runs.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from paperworks.data.hai_distribution_v1 import (  # noqa: E402
    HAIDistributionByteEquivalenceResultV1,
    HAIDistributionError,
    HAIDistributionFileEquivalenceV1,
    HAIOfficialDistributionMetadataV1,
    build_official_distribution_metadata,
    canonical_self_hash,
)
from paperworks.data.hai_provenance_v1 import (  # noqa: E402
    parse_lfs_pointer_text,
    streaming_sha256,
    write_public_json,
)


CONFIG_PATH = REPOSITORY_ROOT / "configs/data/hai_2305_official_distribution_remediation.json"
TASK039A_CONFIG_PATH = REPOSITORY_ROOT / "configs/data/hai_2305_official_provenance.json"
REPORT_ROOT = REPOSITORY_ROOT / "docs/task_reports"
METADATA_REPORT = REPORT_ROOT / "TASK-039AR_KAGGLE_METADATA_FREEZE.json"
EQUIVALENCE_REPORT = REPORT_ROOT / "TASK-039AR_BYTE_EQUIVALENCE_REPORT.json"
MARKDOWN_REPORT = REPORT_ROOT / "TASK-039AR_REPORT.md"


class SelectiveDownloadUnavailable(HAIDistributionError):
    """Raised when the official route cannot return one allowlisted file."""


def _load_self_hashed_json(path: Path, field_name: str) -> dict[str, Any]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get(field_name) != canonical_self_hash(document, field_name):
        raise HAIDistributionError("configuration self-hash mismatch")
    return document


def _run_git(repository: Path, *arguments: str, text: bool = True) -> str | bytes:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=False,
        capture_output=True,
        text=text,
    )
    if completed.returncode != 0:
        raise HAIDistributionError("required Git operation failed")
    return completed.stdout.strip() if text else completed.stdout


def _assert_external_root(root: Path) -> Path:
    resolved = root.resolve()
    try:
        resolved.relative_to(REPOSITORY_ROOT.resolve())
    except ValueError:
        return resolved
    raise HAIDistributionError("distribution payload root must remain outside the repository")


def _committed_json_matches_worktree(committed: bytes, working: bytes) -> bool:
    try:
        committed_document = json.loads(committed.decode("utf-8"))
        working_document = json.loads(working.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HAIDistributionError("frozen receipt must be UTF-8 JSON") from exc
    return committed_document == working_document


def _assert_tracked_at_head(path: Path) -> None:
    resolved = path.resolve()
    try:
        relative = resolved.relative_to(REPOSITORY_ROOT.resolve()).as_posix()
    except ValueError as exc:
        raise HAIDistributionError("frozen receipt must be inside the repository") from exc
    if _run_git(REPOSITORY_ROOT, "status", "--porcelain") != "":
        raise HAIDistributionError("payload acquisition requires a clean paper worktree")
    _run_git(REPOSITORY_ROOT, "ls-files", "--error-unmatch", "--", relative)
    committed = _run_git(
        REPOSITORY_ROOT, "show", f"HEAD:{relative}", text=False
    )
    if not _committed_json_matches_worktree(committed, resolved.read_bytes()):
        raise HAIDistributionError("receipt content does not match the committed HEAD")


class _ApprovedRedirectHandler(urllib.request.HTTPRedirectHandler):
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
            raise SelectiveDownloadUnavailable("download redirect left approved hosts")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _opener(allowed_hosts: Sequence[str]) -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(_ApprovedRedirectHandler(allowed_hosts))


def _get_json(url: str, *, allowed_hosts: Sequence[str]) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "paperworks-task039ar/1.0"},
        method="GET",
    )
    try:
        with _opener(allowed_hosts).open(request, timeout=60) as response:
            payload = response.read()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise HAIDistributionError("official Kaggle metadata request failed") from exc
    try:
        result = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HAIDistributionError("official Kaggle metadata is not UTF-8 JSON") from exc
    if not isinstance(result, dict):
        raise HAIDistributionError("official Kaggle metadata must be an object")
    return result


def _download_one_archive(
    *,
    url: str,
    destination: Path,
    allowed_hosts: Sequence[str],
) -> None:
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/zip", "User-Agent": "paperworks-task039ar/1.0"},
        method="GET",
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".part")
    try:
        with _opener(allowed_hosts).open(request, timeout=300) as response:
            with temporary.open("wb") as output:
                shutil.copyfileobj(response, output, length=1024 * 1024)
        temporary.replace(destination)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        temporary.unlink(missing_ok=True)
        raise SelectiveDownloadUnavailable("selective Kaggle file download failed") from exc


def _extract_exact_member(
    *, archive: Path, expected_relative_path: str, destination_root: Path
) -> Path:
    expected = PurePosixPath(expected_relative_path)
    destination = destination_root / Path(*expected.parts)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".part")
    if not zipfile.is_zipfile(archive):
        with archive.open("rb") as source, temporary.open("wb") as output:
            shutil.copyfileobj(source, output, length=1024 * 1024)
        temporary.replace(destination)
        return destination
    try:
        with zipfile.ZipFile(archive, "r") as bundle:
            files = [item for item in bundle.infolist() if not item.is_dir()]
            if len(files) != 1:
                raise SelectiveDownloadUnavailable(
                    "selective download archive contains more than one file"
                )
            member = files[0]
            normalized = PurePosixPath(member.filename)
            if normalized.is_absolute() or ".." in normalized.parts:
                raise SelectiveDownloadUnavailable("selective archive path is unsafe")
            if normalized not in {expected, PurePosixPath(expected.name)}:
                raise SelectiveDownloadUnavailable(
                    "selective archive member does not match the requested file"
                )
            with bundle.open(member, "r") as source, temporary.open("wb") as output:
                shutil.copyfileobj(source, output, length=1024 * 1024)
            temporary.replace(destination)
            return destination
    except zipfile.BadZipFile as exc:
        raise SelectiveDownloadUnavailable("selective ZIP response is malformed") from exc


def _write_equivalence_result(
    *,
    status: str,
    metadata: HAIOfficialDistributionMetadataV1,
    execution_code_commit: str,
    records: Sequence[HAIDistributionFileEquivalenceV1],
    created_at: str,
) -> HAIDistributionByteEquivalenceResultV1:
    result = HAIDistributionByteEquivalenceResultV1(
        task_id="TASK-039AR",
        status=status,
        metadata_receipt_hash=metadata.artifact_hash,
        execution_code_commit=execution_code_commit,
        records=tuple(sorted(records, key=lambda item: item.relative_path)),
        expected_file_count=10,
        selectively_downloaded_file_count=len(records),
        complete_dataset_download_used=False,
        haiend_or_earlier_payload_downloaded=False,
        credentials_included=False,
        signed_urls_included=False,
        all_files_byte_equivalent=(
            len(records) == 10 and all(item.byte_equivalent for item in records)
        ),
        created_at=created_at,
    )
    write_public_json(EQUIVALENCE_REPORT, result.to_dict())
    MARKDOWN_REPORT.write_text(
        "\n".join(
            (
                "# TASK-039AR Report",
                "",
                f"Status: `{status}`",
                "",
                f"Metadata receipt: `{metadata.artifact_hash}`",
                "",
                "TASK-039AR used the official Kaggle distribution owned by `icsdataset`",
                "only as a selective payload route. Git identity and Git-LFS pointers at",
                "the pinned official snapshot remained the integrity authority. No full",
                "multi-version download, HAIEnd payload, credentials, signed URL, raw row,",
                "attack detail, or scientific analysis entered the public artifacts.",
                "",
            )
        ),
        encoding="utf-8",
    )
    return result


def command_metadata(args: argparse.Namespace) -> int:
    config = _load_self_hashed_json(args.config, "config_hash")
    task039a = _load_self_hashed_json(args.task039a_config, "config_hash")
    if args.output.resolve() != METADATA_REPORT.resolve():
        raise HAIDistributionError("metadata output must use the frozen report path")
    owner = str(config["kaggle_owner"])
    slug = str(config["kaggle_slug"])
    version = int(config["dataset_version_identifier"])
    metadata_endpoint = str(config["metadata_endpoint"])
    inventory_endpoint = str(config["file_inventory_endpoint"]).format(
        owner=owner, slug=slug, version=version
    )
    allowed_hosts = tuple(str(item) for item in config["allowed_initial_hosts"])
    metadata = build_official_distribution_metadata(
        dataset_view=_get_json(metadata_endpoint, allowed_hosts=allowed_hosts),
        file_list=_get_json(inventory_endpoint, allowed_hosts=allowed_hosts),
        owner=owner,
        slug=slug,
        dataset_version_identifier=version,
        expected_files=tuple(task039a["expected_lfs_files"]),
        official_git_repository=str(task039a["official_repository"]),
        official_git_snapshot_commit=str(task039a["snapshot_commit"]),
        introduction_commit=str(task039a["introduction_commit"]),
        task039a_expected_config_hash=str(task039a["config_hash"]),
        metadata_endpoint=metadata_endpoint,
        file_inventory_endpoint=inventory_endpoint,
        selective_download_endpoint_template=str(
            config["selective_download_endpoint_template"]
        ),
        created_at=args.created_at,
        execution_code_commit=args.execution_code_commit,
    )
    write_public_json(args.output, metadata.to_dict())
    return 0


def command_download(args: argparse.Namespace) -> int:
    _assert_tracked_at_head(args.metadata_receipt)
    config = _load_self_hashed_json(args.config, "config_hash")
    task039a = _load_self_hashed_json(args.task039a_config, "config_hash")
    metadata = HAIOfficialDistributionMetadataV1.from_dict(
        json.loads(args.metadata_receipt.read_text(encoding="utf-8"))
    )
    if metadata.task039a_expected_config_hash != task039a["config_hash"]:
        raise HAIDistributionError("metadata receipt is not bound to TASK-039A")
    if metadata.execution_code_commit != args.execution_code_commit:
        raise HAIDistributionError("execution commit differs from metadata freeze")
    acquisition_root = _assert_external_root(args.acquisition_root)
    acquisition_root.mkdir(parents=True, exist_ok=True)
    allowed_hosts = tuple(str(item) for item in config["allowed_download_hosts"])
    inventory = {item.name: item for item in metadata.complete_file_inventory}
    records: list[HAIDistributionFileEquivalenceV1] = []
    status = "passed_official_distribution_byte_equivalence"
    for expected in sorted(task039a["expected_lfs_files"], key=lambda item: item["relative_path"]):
        relative = str(expected["relative_path"])
        advertised = inventory[relative].advertised_size_bytes
        pointer_text = str(
            _run_git(
                args.official_root,
                "show",
                f"{task039a['snapshot_commit']}:{relative}",
            )
        )
        pointer_oid, pointer_size = parse_lfs_pointer_text(pointer_text)
        encoded_name = urllib.parse.quote(relative, safe="")
        url = metadata.selective_download_endpoint_template.format(
            owner=metadata.owner,
            slug=metadata.slug,
            version=metadata.dataset_version_identifier,
            file_name=encoded_name,
        )
        archive = acquisition_root / "archives" / (
            sha256(relative.encode("utf-8")).hexdigest() + ".zip"
        )
        try:
            _download_one_archive(url=url, destination=archive, allowed_hosts=allowed_hosts)
            extracted = _extract_exact_member(
                archive=archive,
                expected_relative_path=relative,
                destination_root=acquisition_root / "payload",
            )
        finally:
            archive.unlink(missing_ok=True)
        extracted_hash = streaming_sha256(extracted)
        extracted_size = extracted.stat().st_size
        record = HAIDistributionFileEquivalenceV1(
            relative_path=relative,
            kaggle_advertised_size_bytes=advertised,
            official_lfs_oid_sha256=pointer_oid,
            official_lfs_pointer_size_bytes=pointer_size,
            task039a_expected_sha256=str(expected["oid_sha256"]),
            task039a_expected_size_bytes=int(expected["byte_size"]),
            extracted_sha256=extracted_hash,
            extracted_size_bytes=extracted_size,
            byte_equivalent=(
                extracted_hash == pointer_oid == expected["oid_sha256"]
                and extracted_size == pointer_size == int(expected["byte_size"])
                and advertised == int(expected["byte_size"])
            ),
        )
        records.append(record)
        if not record.byte_equivalent:
            status = "failed_official_distribution_byte_equivalence"
            break
    result = _write_equivalence_result(
        status=status,
        metadata=metadata,
        execution_code_commit=args.execution_code_commit,
        records=records,
        created_at=args.created_at,
    )
    return 0 if result.status == "passed_official_distribution_byte_equivalence" else 2


def command_materialize_lfs(args: argparse.Namespace) -> int:
    _assert_tracked_at_head(args.equivalence_receipt)
    task039a = _load_self_hashed_json(args.task039a_config, "config_hash")
    result = HAIDistributionByteEquivalenceResultV1.from_dict(
        json.loads(args.equivalence_receipt.read_text(encoding="utf-8"))
    )
    if result.status != "passed_official_distribution_byte_equivalence":
        raise HAIDistributionError("only a passing receipt may materialize LFS objects")
    acquisition_root = _assert_external_root(args.acquisition_root)
    official_root = _assert_external_root(args.official_root)
    if _run_git(official_root, "rev-parse", "HEAD") != task039a["snapshot_commit"]:
        raise HAIDistributionError("official checkout HEAD differs from the freeze")
    if _run_git(official_root, "status", "--porcelain") != "":
        raise HAIDistributionError("official checkout must be clean before materialization")
    git_dir_raw = str(_run_git(official_root, "rev-parse", "--git-dir"))
    git_dir = (official_root / git_dir_raw).resolve()
    if git_dir != (official_root / ".git").resolve():
        raise HAIDistributionError("official checkout must use its own .git directory")
    expected_by_path = {
        str(item["relative_path"]): item for item in task039a["expected_lfs_files"]
    }
    for record in result.records:
        expected = expected_by_path[record.relative_path]
        source = acquisition_root / "payload" / Path(
            *PurePosixPath(record.relative_path).parts
        )
        if (
            streaming_sha256(source) != expected["oid_sha256"]
            or source.stat().st_size != int(expected["byte_size"])
        ):
            raise HAIDistributionError("verified payload changed before LFS materialization")
        oid = str(expected["oid_sha256"])
        object_path = git_dir / "lfs" / "objects" / oid[:2] / oid[2:4] / oid
        object_path.parent.mkdir(parents=True, exist_ok=True)
        if object_path.exists():
            if streaming_sha256(object_path) != oid:
                raise HAIDistributionError("existing local LFS object hash mismatch")
        else:
            with tempfile.NamedTemporaryFile(
                dir=object_path.parent, delete=False
            ) as temporary:
                temporary_path = Path(temporary.name)
                with source.open("rb") as input_stream:
                    shutil.copyfileobj(input_stream, temporary, length=1024 * 1024)
            if streaming_sha256(temporary_path) != oid:
                temporary_path.unlink(missing_ok=True)
                raise HAIDistributionError("copied local LFS object hash mismatch")
            temporary_path.replace(object_path)
        _run_git(official_root, "lfs", "checkout", "--", record.relative_path)
    if _run_git(official_root, "status", "--porcelain") != "":
        raise HAIDistributionError("materialized official checkout is not Git-clean")
    _run_git(
        official_root,
        "-c",
        "lfs.fetchexclude=*,!hai-23.05/**",
        "lfs",
        "fsck",
        "--objects",
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--config", type=Path, default=CONFIG_PATH)
    common.add_argument("--task039a-config", type=Path, default=TASK039A_CONFIG_PATH)
    common.add_argument("--execution-code-commit", required=True)
    common.add_argument(
        "--created-at",
        default=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )

    metadata = subparsers.add_parser("metadata", parents=[common])
    metadata.add_argument("--output", type=Path, default=METADATA_REPORT)

    download = subparsers.add_parser("download", parents=[common])
    download.add_argument("--metadata-receipt", type=Path, default=METADATA_REPORT)
    download.add_argument("--acquisition-root", type=Path, required=True)
    download.add_argument("--official-root", type=Path, required=True)

    materialize = subparsers.add_parser("materialize-lfs", parents=[common])
    materialize.add_argument("--equivalence-receipt", type=Path, default=EQUIVALENCE_REPORT)
    materialize.add_argument("--acquisition-root", type=Path, required=True)
    materialize.add_argument("--official-root", type=Path, required=True)
    return parser


def main() -> int:
    arguments = build_parser().parse_args()
    try:
        if arguments.command == "metadata":
            return command_metadata(arguments)
        if arguments.command == "download":
            return command_download(arguments)
        if arguments.command == "materialize-lfs":
            return command_materialize_lfs(arguments)
        raise HAIDistributionError("unknown remediation command")
    except SelectiveDownloadUnavailable:
        if arguments.command == "download":
            metadata = HAIOfficialDistributionMetadataV1.from_dict(
                json.loads(arguments.metadata_receipt.read_text(encoding="utf-8"))
            )
            _write_equivalence_result(
                status="blocked_selective_official_download_unavailable",
                metadata=metadata,
                execution_code_commit=arguments.execution_code_commit,
                records=(),
                created_at=arguments.created_at,
            )
        print("TASK-039AR blocked: selective official download unavailable", file=sys.stderr)
        return 3
    except (HAIDistributionError, OSError, json.JSONDecodeError) as exc:
        print(f"TASK-039AR failed: {type(exc).__name__}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
