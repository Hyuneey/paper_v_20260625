"""Bounded I/O helpers for the TASK-039B normal-only HAI audit."""

from __future__ import annotations

import ast
import csv
import json
import re
from array import array
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

from paperworks.data.contracts_v2 import DatasetManifestV2
from paperworks.data.hai_provenance_v1 import streaming_sha256
from paperworks.feasibility.hai_process_v1 import (
    APPROVED_TRAIN_FILES,
    HAIFeasibilityError,
    PROCESS_NAMES,
    TASK039BDataAccessLedger,
    canonical_json,
)


@dataclass(frozen=True)
class VerifiedTrainingFileV1:
    relative_path: str
    sha256: str
    byte_size: int
    row_count: int
    header: tuple[str, ...]
    header_hash: str


@dataclass(frozen=True)
class ManualExtractionResultV1:
    extractor: str
    extractor_version: str
    page_count: int
    title: str
    page_texts: tuple[str, ...]


@dataclass(frozen=True)
class ManualVariableEntryV1:
    variable_name: str
    page_references: tuple[int, ...]
    description: str
    unit: str
    excerpt_hash: str | None


def load_verified_task039a_manifest(path: Path) -> DatasetManifestV2:
    document = json.loads(path.read_text(encoding="utf-8"))
    manifest = DatasetManifestV2.from_dict(document)
    if manifest.dataset_name != "HAI" or manifest.dataset_version_or_edition != "23.05":
        raise HAIFeasibilityError("TASK-039A manifest is not HAI 23.05")
    if manifest.manifest_id != "5b0c395169fea468f7afd52aceafc4e6dadf062a1bc557c5bbe5dd6b8a761aa2":
        raise HAIFeasibilityError("TASK-039A manifest identity mismatch")
    return manifest


def _count_rows_without_value_parsing(path: Path) -> int:
    lines = 0
    with path.open("rb") as handle:
        for _ in handle:
            lines += 1
    return max(lines - 1, 0)


def _read_header(path: Path) -> tuple[str, ...]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        try:
            return tuple(next(csv.reader(handle)))
        except StopIteration as exc:
            raise HAIFeasibilityError("training CSV is empty") from exc


def verify_training_files(
    *,
    data_root: Path,
    manifest: DatasetManifestV2,
    ledger: TASK039BDataAccessLedger,
) -> tuple[VerifiedTrainingFileV1, ...]:
    """Verify all four authorized files before any feature value is parsed."""

    manifest_files = {item.relative_local_path: item for item in manifest.files}
    records: list[VerifiedTrainingFileV1] = []
    expected_header: tuple[str, ...] | None = None
    for relative in APPROVED_TRAIN_FILES:
        ledger.authorize(
            relative,
            purpose="pre_value_integrity_header_and_row_count",
            feature_values_accessed=False,
        )
        record = manifest_files.get(relative)
        if record is None or record.row_count is None:
            raise HAIFeasibilityError("authorized train file is missing from manifest")
        local = (data_root.parent / PurePosixPath(relative)).resolve()
        if local.parent != data_root.resolve() or not local.is_file():
            raise HAIFeasibilityError("authorized training file is missing")
        digest = streaming_sha256(local)
        size = local.stat().st_size
        header = _read_header(local)
        row_count = _count_rows_without_value_parsing(local)
        if digest != record.sha256 or size != record.byte_size or row_count != record.row_count:
            raise HAIFeasibilityError("training file integrity or row count mismatch")
        if expected_header is None:
            expected_header = header
        elif header != expected_header:
            raise HAIFeasibilityError("training CSV ordered headers differ")
        feature_names = [
            value
            for value in header
            if value.strip().lower()
            not in {"timestamp", "time", "datetime", "date_time", "label", "attack", "anomaly", "is_attack"}
        ]
        feature_hash = sha256(
            json.dumps(feature_names, separators=(",", ":"), ensure_ascii=True).encode()
        ).hexdigest()
        records.append(
            VerifiedTrainingFileV1(
                relative_path=relative,
                sha256=digest,
                byte_size=size,
                row_count=row_count,
                header=header,
                header_hash=feature_hash,
            )
        )
    if records[0].header_hash != manifest.feature_names_hash:
        raise HAIFeasibilityError("training header does not match TASK-039A manifest")
    if manifest.nominal_sampling_interval_seconds != 1.0:
        raise HAIFeasibilityError("TASK-039A nominal sampling interval is not one second")
    return tuple(records)


def process_feature_names(header: Sequence[str], process_id: str) -> tuple[str, ...]:
    if process_id not in PROCESS_NAMES:
        raise HAIFeasibilityError("only P1 and P3 process scopes are authorized")
    names = tuple(item for item in header if item.startswith(f"{process_id}_"))
    if not names:
        raise HAIFeasibilityError("verified header contains no process-scoped features")
    if any(item.startswith(("P2_", "P4_")) for item in names):
        raise HAIFeasibilityError("process scope includes P2 or P4")
    return names


def load_process_values(
    *,
    data_root: Path,
    verified_files: Sequence[VerifiedTrainingFileV1],
    process_id: str,
    ledger: TASK039BDataAccessLedger,
) -> dict[str, dict[str, array]]:
    """Numerically parse only one authorized process from train1 through train3."""

    names = process_feature_names(verified_files[0].header, process_id)
    index_by_name = {name: verified_files[0].header.index(name) for name in names}
    result: dict[str, dict[str, array]] = {}
    for record in verified_files[:3]:
        ledger.authorize(
            record.relative_path,
            purpose="normal_candidate_fit_or_calibration_process_values",
            feature_values_accessed=True,
            process_scope=(process_id,),
        )
        local = data_root.parent / PurePosixPath(record.relative_path)
        columns = {name: array("d") for name in names}
        with local.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle)
            header = tuple(next(reader))
            if header != record.header:
                raise HAIFeasibilityError("training header changed after preflight")
            parsed_rows = 0
            for row in reader:
                if len(row) != len(header):
                    raise HAIFeasibilityError("malformed training row")
                for name, index in index_by_name.items():
                    text = row[index].strip()
                    try:
                        value = float(text) if text else float("nan")
                    except ValueError as exc:
                        raise HAIFeasibilityError("non-numeric process value") from exc
                    columns[name].append(value)
                parsed_rows += 1
        if parsed_rows != record.row_count:
            raise HAIFeasibilityError("process value row count mismatch")
        result[record.relative_path] = columns
    return result


def extract_manual_pages(pdf_path: Path) -> ManualExtractionResultV1:
    """Extract bounded page text locally with pypdf; never persist full text."""

    try:
        import pypdf  # type: ignore
    except ImportError as exc:
        raise HAIFeasibilityError("blocked_hai_metadata_evidence_insufficient") from exc
    reader = pypdf.PdfReader(str(pdf_path))
    page_texts = tuple((page.extract_text() or "") for page in reader.pages)
    title = str((reader.metadata or {}).get("/Title", "unverified"))
    version = getattr(pypdf, "__version__", "unverified")
    return ManualExtractionResultV1(
        extractor="pypdf",
        extractor_version=str(version),
        page_count=len(reader.pages),
        title=title,
        page_texts=page_texts,
    )


def extract_manual_variable_entries(
    *, page_texts: Sequence[str], variable_names: Sequence[str]
) -> dict[str, ManualVariableEntryV1]:
    """Find exact tag references and retain only bounded one-line descriptions."""

    output: dict[str, ManualVariableEntryV1] = {}
    for variable in variable_names:
        hits: list[tuple[int, str]] = []
        pattern = re.compile(rf"(?<![A-Za-z0-9_]){re.escape(variable)}(?![A-Za-z0-9_])")
        for page_number, text in enumerate(page_texts, start=1):
            lines = [" ".join(line.split()) for line in text.splitlines()]
            for index, line in enumerate(lines):
                if pattern.search(line):
                    context = " ".join(
                        item for item in lines[max(0, index - 1) : index + 2] if item
                    )
                    hits.append((page_number, context[:480]))
        pages = tuple(sorted({page for page, _ in hits}))
        contexts = tuple(dict.fromkeys(context for _, context in hits if context))
        description = contexts[0][:320] if contexts else ""
        unit_match = re.search(
            r"(?:unit\s*[:=]?\s*|\[)([A-Za-z0-9%/()._-]{1,24})\]?",
            description,
            flags=re.IGNORECASE,
        )
        unit = unit_match.group(1) if unit_match else "unverified"
        excerpt_hash = (
            sha256(canonical_json({"contexts": list(contexts)}).encode()).hexdigest()
            if contexts
            else None
        )
        output[variable] = ManualVariableEntryV1(
            variable_name=variable,
            page_references=pages,
            description=description,
            unit=unit,
            excerpt_hash=excerpt_hash,
        )
    return output


def official_graph_references_by_variable(
    *,
    official_root: Path,
    public_reference_inventory: Mapping[str, Any],
    variable_names: Sequence[str],
) -> dict[str, tuple[str, ...]]:
    """Map exact variable strings to already inventoried official graph files."""

    output: dict[str, list[str]] = {name: [] for name in variable_names}
    for record in public_reference_inventory.get("graphs", []):
        relative = str(record.get("relative_path", ""))
        if not relative.startswith("graph/"):
            continue
        path = (official_root / PurePosixPath(relative)).resolve()
        if official_root.resolve() not in path.parents or not path.is_file():
            raise HAIFeasibilityError("official graph reference is unavailable")
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        parsed: object
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            try:
                parsed = ast.literal_eval(text)
            except (SyntaxError, ValueError):
                parsed = text
        normalized = json.dumps(parsed, ensure_ascii=True) if not isinstance(parsed, str) else parsed
        for name in variable_names:
            if name in normalized:
                output[name].append(relative)
    return {name: tuple(sorted(set(paths))) for name, paths in output.items()}


def private_ledger_hash_and_write(path: Path, document: Mapping[str, Any]) -> str:
    """Write a detailed private screening ledger outside the repository."""

    payload = json.loads(canonical_json(document))
    digest = sha256(canonical_json(payload).encode()).hexdigest()
    payload["artifact_hash"] = digest
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return digest
