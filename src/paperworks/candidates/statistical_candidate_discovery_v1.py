"""P1 statistical candidate discovery for TASK-039C-STAT.

The implementation evaluates the frozen 144-pair C0 universe with within-file
lagged Pearson correlations of first differences.  It owns no relation
calibration, rule-validity, anomaly, detector, runtime, META, GDN, or causal
authority.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

try:
    import numpy as np
except ImportError:  # pragma: no cover - exercised through the project error path
    np = None  # type: ignore[assignment]

from paperworks.data.contracts_v2 import DatasetManifestV2
from paperworks.v6.candidate_discovery_protocol_v1 import (
    CandidateDiscoveryProtocolBundleV1,
    CandidateDiscoveryProtocolError,
    StatisticalHorizonSelectionV1,
    StatisticalRankInputV1,
    assert_candidate_in_universe_v1,
    authorize_br2_pair_artifact_use_v1,
    authorize_candidate_arm_value_access_v1,
    derive_candidate_budget_views_v1,
    eligible_pair_records_v1,
    rank_statistical_candidates_v1,
    select_statistical_horizon_v1,
)
from paperworks.v6.common import stable_hash_v1


TASK_ID = "TASK-039C-STAT"
ARM_ID = "STAT"
PASSED_STATUS = "passed_task039c_statistical_candidate_discovery"
EXPECTED_BASE_COMMIT = "b6522fb83c4cb92d355f98af778f9a6a3c73362f"
EXPECTED_BRANCH = "task-039c-stat"
EXPECTED_C0_PROTOCOL_HASH = (
    "41aab751d6bbbaadc72a95ef3289ea6440c26659fb38f640bf17fb0688836dff"
)
EXPECTED_STAT_POLICY_HASH = (
    "2e3413ee190dbce7106876ff5dd053161a17e18e80d142e75c05e50430c008e3"
)
EXPECTED_SOURCE_IDENTITY_HASH = (
    "0af3f80f18a3eab59b9783af64d306c8d774eeb69b3a72c24c10048abd4ed234"
)
EXPECTED_TARGET_IDENTITY_HASH = (
    "063037980aae4f0eaf45fbebb59f2aa0a924fbad583f3818107a793dfe7248e7"
)
EXPECTED_PAIR_UNIVERSE_HASH = (
    "fc072d3e18ce4623972c2cb64f6266727092ecae03fdb0f0dd929d705e1d8557"
)
EXPECTED_DATASET_MANIFEST_ID = (
    "5b0c395169fea468f7afd52aceafc4e6dadf062a1bc557c5bbe5dd6b8a761aa2"
)
EXPECTED_PROCESS_ID = "P1"
EXPECTED_PAIR_COUNT = 144
EXPECTED_FILES = (
    "hai-23.05/hai-train1.csv",
    "hai-23.05/hai-train2.csv",
)
EXPECTED_HORIZONS = (1, 5, 10, 30, 60)
MIN_PEARSON_OBSERVATIONS = 2
PARITY_ABSOLUTE_TOLERANCE = 1.0e-12
PARITY_RELATIVE_TOLERANCE = 1.0e-12

_ABSOLUTE_WINDOWS_PATH = re.compile(r"(?i)(?:^|[^A-Za-z0-9_])[A-Z]:[\\/]")
_PUBLIC_PROHIBITED_KEYS = frozenset(
    {
        "raw_rows",
        "raw_row",
        "raw_samples",
        "raw_sample",
        "raw_windows",
        "raw_window",
        "feature_values",
        "label_values",
        "event_timestamps",
        "absolute_path",
        "local_path",
        "data_root",
        "private_root",
    }
)


class StatisticalCandidateDiscoveryError(RuntimeError):
    """Stable project-owned failure for TASK-039C-STAT."""


@dataclass(frozen=True)
class ExpectedFileIdentityV1:
    """Verified public identity for one authorized normal training file."""

    relative_path: str
    sha256: str
    byte_size: int
    row_count: int
    feature_names_hash: str


@dataclass(frozen=True)
class AuthorizedFileMatrixV1:
    """Selected numeric columns read once from one identity-checked file."""

    relative_path: str
    columns: tuple[str, ...]
    values: Any
    sha256: str
    byte_size: int
    row_count: int


@dataclass(frozen=True)
class HorizonCorrelationV1:
    """File-specific correlations and stability state for one horizon."""

    horizon_seconds: int
    r_train1: float | None
    r_train2: float | None
    train1_usable: bool
    train2_usable: bool
    sign_stable: bool
    stability_strength: float | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "horizon_seconds": self.horizon_seconds,
            "r_train1": _finite_or_none(self.r_train1),
            "r_train2": _finite_or_none(self.r_train2),
            "train1_usable": self.train1_usable,
            "train2_usable": self.train2_usable,
            "sign_stable": self.sign_stable,
            "stability_strength": _finite_or_none(self.stability_strength),
        }


@dataclass(frozen=True)
class PairStatisticalEvidenceV1:
    """Independent train1/train2 statistical evidence for one frozen pair."""

    source: str
    target: str
    horizons: tuple[HorizonCorrelationV1, ...]
    selection: StatisticalHorizonSelectionV1
    correlation_sign: str | None

    @property
    def supported(self) -> bool:
        return self.selection.status == "cross_file_sign_stable"

    def to_private_dict(self, *, audit_rank: int) -> dict[str, Any]:
        return {
            "audit_rank": audit_rank,
            "source": self.source,
            "target": self.target,
            "method_status": self.selection.status,
            "selected_horizon_seconds": self.selection.selected_horizon,
            "correlation_sign": self.correlation_sign,
            "r_train1": _finite_or_none(self.selection.train1_correlation),
            "r_train2": _finite_or_none(self.selection.train2_correlation),
            "stability_strength": _finite_or_none(self.selection.score),
            "horizons": [item.to_dict() for item in self.horizons],
        }


class STATDataAccessLedgerV1:
    """Fail-closed in-memory ledger for the two authorized file reads."""

    def __init__(self, *, allowed_columns: Sequence[str]) -> None:
        normalized = tuple(str(item) for item in allowed_columns)
        if len(normalized) != 24 or len(set(normalized)) != 24:
            raise StatisticalCandidateDiscoveryError("failed_stat_protocol_compliance")
        self._allowed_columns = normalized
        self._started: dict[str, int] = {}
        self._records: list[dict[str, Any]] = []

    def begin_read(
        self,
        *,
        bundle: CandidateDiscoveryProtocolBundleV1,
        relative_path: str,
        columns: Sequence[str],
    ) -> None:
        authorize_stat_value_request_v1(
            bundle=bundle,
            process_id=EXPECTED_PROCESS_ID,
            relative_path=relative_path,
            columns=columns,
        )
        normalized = tuple(str(item) for item in columns)
        if normalized != self._allowed_columns or self._started.get(relative_path, 0):
            raise StatisticalCandidateDiscoveryError("failed_stat_data_boundary")
        self._started[relative_path] = 1

    def complete_read(self, matrix: AuthorizedFileMatrixV1) -> None:
        if self._started.get(matrix.relative_path) != 1:
            raise StatisticalCandidateDiscoveryError("failed_stat_data_boundary")
        if any(item["relative_path"] == matrix.relative_path for item in self._records):
            raise StatisticalCandidateDiscoveryError("failed_stat_data_boundary")
        self._records.append(
            {
                "relative_path": matrix.relative_path,
                "file_sha256": matrix.sha256,
                "byte_size": matrix.byte_size,
                "row_count": matrix.row_count,
                "selected_column_count": len(matrix.columns),
                "selected_columns_hash": stable_hash_v1(
                    {
                        "artifact_type": "stat_selected_columns_v1",
                        "columns": list(matrix.columns),
                    }
                ),
                "file_open_count": 1,
                "feature_read_pass_count": 1,
                "unrequested_columns_parsed": False,
            }
        )

    @property
    def records(self) -> tuple[dict[str, Any], ...]:
        if tuple(sorted(self._started)) != EXPECTED_FILES or len(self._records) != 2:
            raise StatisticalCandidateDiscoveryError("failed_stat_data_boundary")
        return tuple(sorted((dict(item) for item in self._records), key=lambda item: item["relative_path"]))


class _HashingRawReader(io.RawIOBase):
    """Hash exact bytes while a buffered text reader consumes one file once."""

    def __init__(self, path: Path) -> None:
        super().__init__()
        self._stream = path.open("rb", buffering=0)
        self._digest = hashlib.sha256()
        self.byte_count = 0

    def readable(self) -> bool:
        return True

    def readinto(self, buffer: Any) -> int:
        count = self._stream.readinto(buffer)
        if count:
            block = memoryview(buffer)[:count]
            self._digest.update(block)
            self.byte_count += count
        return count

    @property
    def hexdigest(self) -> str:
        return self._digest.hexdigest()

    def close(self) -> None:
        if not self.closed:
            self._stream.close()
        super().close()


def _require_numpy() -> Any:
    if np is None:
        raise StatisticalCandidateDiscoveryError(
            "failed_stat_numerical_backend_unavailable"
        )
    return np


def _finite_or_none(value: float | None) -> float | None:
    if value is None:
        return None
    number = float(value)
    if not math.isfinite(number):
        return None
    return 0.0 if number == 0.0 else number


def _self_hashed(content: Mapping[str, Any]) -> dict[str, Any]:
    document = dict(content)
    document["artifact_hash"] = stable_hash_v1(document)
    return document


def _load_json(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise StatisticalCandidateDiscoveryError(
            "failed_stat_protocol_compliance"
        ) from exc
    if not isinstance(document, dict):
        raise StatisticalCandidateDiscoveryError("failed_stat_protocol_compliance")
    return document


def _verify_self_hash(document: Mapping[str, Any], field: str = "artifact_hash") -> str:
    supplied = document.get(field)
    if not isinstance(supplied, str) or not re.fullmatch(r"[0-9a-f]{64}", supplied):
        raise StatisticalCandidateDiscoveryError("failed_stat_file_identity")
    content = {key: value for key, value in document.items() if key != field}
    if stable_hash_v1(content) != supplied:
        raise StatisticalCandidateDiscoveryError("failed_stat_file_identity")
    return supplied


def load_frozen_c0_bundle_v1(repository_root: Path) -> CandidateDiscoveryProtocolBundleV1:
    """Load and verify the shared C0 protocol without reading arm results."""

    document = _load_json(
        repository_root / "docs" / "task_reports" / "TASK-039C0_PROTOCOL_BUNDLE.json"
    )
    try:
        bundle = CandidateDiscoveryProtocolBundleV1.from_dict(document)
    except (CandidateDiscoveryProtocolError, KeyError, TypeError, ValueError) as exc:
        raise StatisticalCandidateDiscoveryError(
            "failed_stat_protocol_compliance"
        ) from exc
    universe = bundle.universe_policy
    if (
        bundle.artifact_hash != EXPECTED_C0_PROTOCOL_HASH
        or bundle.statistical_policy.artifact_hash != EXPECTED_STAT_POLICY_HASH
        or universe.source_identity_list_hash != EXPECTED_SOURCE_IDENTITY_HASH
        or universe.target_identity_list_hash != EXPECTED_TARGET_IDENTITY_HASH
        or universe.eligible_pair_universe_hash != EXPECTED_PAIR_UNIVERSE_HASH
        or universe.eligible_pair_count != EXPECTED_PAIR_COUNT
        or universe.selected_process_id != EXPECTED_PROCESS_ID
        or bundle.statistical_policy.horizons_seconds != EXPECTED_HORIZONS
    ):
        raise StatisticalCandidateDiscoveryError("failed_stat_protocol_compliance")
    return bundle


def load_verified_file_identities_v1(
    repository_root: Path,
) -> tuple[ExpectedFileIdentityV1, ...]:
    """Bind train1/train2 to the existing verified manifest and structure audit."""

    manifest_document = _load_json(
        repository_root / "docs" / "task_reports" / "TASK-039A_DATASET_MANIFEST_V2.json"
    )
    csv_document = _load_json(
        repository_root / "docs" / "task_reports" / "TASK-039A_CSV_STRUCTURE_REPORT.json"
    )
    if _verify_self_hash(manifest_document) != EXPECTED_DATASET_MANIFEST_ID:
        raise StatisticalCandidateDiscoveryError("failed_stat_file_identity")
    _verify_self_hash(csv_document, "report_hash")
    try:
        manifest = DatasetManifestV2.from_dict(manifest_document)
    except (KeyError, TypeError, ValueError) as exc:
        raise StatisticalCandidateDiscoveryError("failed_stat_file_identity") from exc
    if (
        manifest.manifest_id != EXPECTED_DATASET_MANIFEST_ID
        or manifest.nominal_sampling_interval_seconds != 1.0
        or not manifest.feature_names_hash
        or csv_document.get("all_headers_aligned") is not True
        or csv_document.get("feature_names_hash") != manifest.feature_names_hash
    ):
        raise StatisticalCandidateDiscoveryError("failed_stat_file_identity")
    manifest_files = {item.relative_local_path: item for item in manifest.files}
    structure_records = {
        str(item.get("relative_path")): item
        for item in csv_document.get("records", ())
        if isinstance(item, Mapping)
    }
    identities: list[ExpectedFileIdentityV1] = []
    for relative in EXPECTED_FILES:
        manifest_file = manifest_files.get(relative)
        structure = structure_records.get(relative)
        if (
            manifest_file is None
            or structure is None
            or manifest_file.logical_file_role != "normal_train_time_series"
            or manifest_file.label_availability != "unavailable"
            or manifest_file.provenance_status != "verified"
            or manifest_file.byte_size is None
            or manifest_file.row_count is None
            or manifest_file.sha256 != structure.get("file_sha256")
            or manifest_file.byte_size != structure.get("byte_size")
            or manifest_file.row_count != structure.get("row_count")
            or structure.get("normal_file_status") != "normal_only_verified"
            or structure.get("nominal_timestamp_delta_seconds") != 1.0
            or structure.get("timestamp_field") != "timestamp"
            or structure.get("ordered_header_matches_canonical") is not True
        ):
            raise StatisticalCandidateDiscoveryError("failed_stat_file_identity")
        identities.append(
            ExpectedFileIdentityV1(
                relative_path=relative,
                sha256=manifest_file.sha256,
                byte_size=manifest_file.byte_size,
                row_count=manifest_file.row_count,
                feature_names_hash=manifest.feature_names_hash,
            )
        )
    return tuple(identities)


def authorize_stat_value_request_v1(
    *,
    bundle: CandidateDiscoveryProtocolBundleV1,
    process_id: str,
    relative_path: str,
    columns: Sequence[str],
) -> None:
    """Authorize only STAT train1/train2 and frozen P1 source/target columns."""

    normalized_path = PurePosixPath(str(relative_path)).as_posix()
    if normalized_path != relative_path or PurePosixPath(relative_path).is_absolute():
        raise StatisticalCandidateDiscoveryError("failed_stat_data_boundary")
    try:
        authorize_candidate_arm_value_access_v1(
            bundle.data_access_policy,
            arm=ARM_ID,
            process_id=process_id,
            relative_file=relative_path,
        )
    except CandidateDiscoveryProtocolError as exc:
        raise StatisticalCandidateDiscoveryError("failed_stat_data_boundary") from exc
    allowed = set(bundle.universe_policy.source_variables) | set(
        bundle.universe_policy.target_variables
    ) | {"timestamp"}
    normalized_columns = tuple(str(item) for item in columns)
    if (
        not normalized_columns
        or len(normalized_columns) != len(set(normalized_columns))
        or any(item not in allowed for item in normalized_columns)
    ):
        raise StatisticalCandidateDiscoveryError("failed_stat_data_boundary")


def reject_br2_pair_supervision_v1(
    *, bundle: CandidateDiscoveryProtocolBundleV1, artifact_kind: str
) -> None:
    """Expose a stable STAT failure for any attempted BR2 ranking supervision."""

    try:
        authorize_br2_pair_artifact_use_v1(
            bundle.data_access_policy,
            artifact_kind=artifact_kind,
            requested_mode="candidate_ranking",
        )
    except CandidateDiscoveryProtocolError as exc:
        raise StatisticalCandidateDiscoveryError("failed_stat_data_boundary") from exc
    raise StatisticalCandidateDiscoveryError("failed_stat_data_boundary")


def assert_stat_candidate_in_universe_v1(
    bundle: CandidateDiscoveryProtocolBundleV1, source: str, target: str
) -> None:
    try:
        assert_candidate_in_universe_v1(bundle.universe_policy, source, target)
    except CandidateDiscoveryProtocolError as exc:
        raise StatisticalCandidateDiscoveryError(
            "failed_stat_protocol_compliance"
        ) from exc


def read_authorized_stat_file_v1(
    *,
    data_root: Path,
    identity: ExpectedFileIdentityV1,
    columns: Sequence[str],
    bundle: CandidateDiscoveryProtocolBundleV1,
    ledger: STATDataAccessLedgerV1,
) -> AuthorizedFileMatrixV1:
    """Open once, hash exact bytes, and parse only selected numeric columns."""

    backend = _require_numpy()
    normalized_columns = tuple(str(item) for item in columns)
    ledger.begin_read(
        bundle=bundle,
        relative_path=identity.relative_path,
        columns=normalized_columns,
    )
    path = data_root / PurePosixPath(identity.relative_path).name
    try:
        if not path.is_file():
            raise StatisticalCandidateDiscoveryError("failed_stat_file_identity")
        hashing_stream = _HashingRawReader(path)
        with io.BufferedReader(hashing_stream, buffer_size=1024 * 1024) as buffered:
            with io.TextIOWrapper(buffered, encoding="utf-8-sig", newline="") as text:
                header_line = text.readline()
                if not header_line:
                    raise StatisticalCandidateDiscoveryError(
                        "failed_stat_file_identity"
                    )
                header = tuple(next(csv.reader([header_line])))
                if len(header) != len(set(header)) or any(
                    name not in header for name in normalized_columns
                ):
                    raise StatisticalCandidateDiscoveryError(
                        "failed_stat_file_identity"
                    )
                indices = tuple(header.index(name) for name in normalized_columns)
                values = backend.loadtxt(
                    text,
                    delimiter=",",
                    dtype=backend.float64,
                    usecols=indices,
                    ndmin=2,
                )
        observed_sha = hashing_stream.hexdigest
        observed_bytes = hashing_stream.byte_count
    except StatisticalCandidateDiscoveryError:
        raise
    except (OSError, UnicodeDecodeError, csv.Error, ValueError) as exc:
        raise StatisticalCandidateDiscoveryError("failed_stat_file_identity") from exc
    if (
        observed_sha != identity.sha256
        or observed_bytes != identity.byte_size
        or values.shape != (identity.row_count, len(normalized_columns))
    ):
        raise StatisticalCandidateDiscoveryError("failed_stat_file_identity")
    matrix = AuthorizedFileMatrixV1(
        relative_path=identity.relative_path,
        columns=normalized_columns,
        values=values,
        sha256=observed_sha,
        byte_size=observed_bytes,
        row_count=int(values.shape[0]),
    )
    ledger.complete_read(matrix)
    return matrix


def file_local_differences_v1(files: Mapping[str, Any]) -> dict[str, Any]:
    """Difference each file independently; never create a boundary difference."""

    backend = _require_numpy()
    result: dict[str, Any] = {}
    for name, values in files.items():
        array = backend.asarray(values, dtype=backend.float64)
        if array.ndim != 2 or array.shape[0] < 2:
            raise StatisticalCandidateDiscoveryError(
                "failed_stat_protocol_compliance"
            )
        result[str(name)] = backend.diff(array, axis=0)
    return result


def pearson_correlation_reference_v1(
    left: Sequence[float], right: Sequence[float]
) -> float | None:
    """Independent finite-pair Pearson reference using ``math.fsum``.

    Pearson's sample and population normalizations cancel in correlation.  Two
    finite paired observations are the mathematical minimum; no additional
    correlation threshold is applied.
    """

    if len(left) != len(right):
        raise StatisticalCandidateDiscoveryError("failed_stat_protocol_compliance")
    pairs = [
        (float(x), float(y))
        for x, y in zip(left, right)
        if math.isfinite(float(x)) and math.isfinite(float(y))
    ]
    if len(pairs) < MIN_PEARSON_OBSERVATIONS:
        return None
    count = len(pairs)
    mean_left = math.fsum(item[0] for item in pairs) / count
    mean_right = math.fsum(item[1] for item in pairs) / count
    centered = tuple((x - mean_left, y - mean_right) for x, y in pairs)
    numerator = math.fsum(x * y for x, y in centered)
    left_ss = math.fsum(x * x for x, _ in centered)
    right_ss = math.fsum(y * y for _, y in centered)
    if left_ss <= 0.0 or right_ss <= 0.0:
        return None
    correlation = numerator / math.sqrt(left_ss * right_ss)
    if not math.isfinite(correlation):
        return None
    return max(-1.0, min(1.0, correlation))


def _pairwise_pearson_matrix_v1(left: Any, right: Any) -> Any:
    backend = _require_numpy()
    x = backend.asarray(left, dtype=backend.float64)
    y = backend.asarray(right, dtype=backend.float64)
    if x.ndim != 2 or y.ndim != 2 or x.shape[0] != y.shape[0]:
        raise StatisticalCandidateDiscoveryError("failed_stat_protocol_compliance")
    result = backend.full((x.shape[1], y.shape[1]), backend.nan, dtype=backend.float64)
    if x.shape[0] < MIN_PEARSON_OBSERVATIONS:
        return result
    if backend.isfinite(x).all() and backend.isfinite(y).all():
        centered_x = x - backend.mean(x, axis=0, dtype=backend.float64)
        centered_y = y - backend.mean(y, axis=0, dtype=backend.float64)
        numerator = centered_x.T @ centered_y
        left_ss = backend.einsum("ij,ij->j", centered_x, centered_x)
        right_ss = backend.einsum("ij,ij->j", centered_y, centered_y)
        denominator = backend.sqrt(backend.outer(left_ss, right_ss))
        with backend.errstate(divide="ignore", invalid="ignore"):
            result = numerator / denominator
        result[(denominator <= 0.0) | ~backend.isfinite(result)] = backend.nan
        finite = backend.isfinite(result)
        result[finite] = backend.clip(result[finite], -1.0, 1.0)
        return result
    for source_index in range(x.shape[1]):
        for target_index in range(y.shape[1]):
            correlation = pearson_correlation_reference_v1(
                x[:, source_index], y[:, target_index]
            )
            if correlation is not None:
                result[source_index, target_index] = correlation
    return result


def vectorized_file_lagged_correlations_v1(
    *, source_values: Any, target_values: Any, horizons: Sequence[int] = EXPECTED_HORIZONS
) -> dict[int, Any]:
    """Calculate all source-target correlations within one file only."""

    backend = _require_numpy()
    frozen_horizons = tuple(int(item) for item in horizons)
    if frozen_horizons != EXPECTED_HORIZONS:
        raise StatisticalCandidateDiscoveryError("failed_stat_protocol_compliance")
    source = backend.asarray(source_values, dtype=backend.float64)
    target = backend.asarray(target_values, dtype=backend.float64)
    if source.ndim != 2 or target.ndim != 2 or source.shape[0] != target.shape[0]:
        raise StatisticalCandidateDiscoveryError("failed_stat_protocol_compliance")
    if source.shape[0] < 2:
        raise StatisticalCandidateDiscoveryError("failed_stat_protocol_compliance")
    dx = backend.diff(source, axis=0)
    dy = backend.diff(target, axis=0)
    matrices: dict[int, Any] = {}
    for horizon in EXPECTED_HORIZONS:
        if dx.shape[0] <= horizon:
            matrices[horizon] = backend.full(
                (source.shape[1], target.shape[1]), backend.nan, dtype=backend.float64
            )
            continue
        matrices[horizon] = _pairwise_pearson_matrix_v1(
            dx[:-horizon], dy[horizon:]
        )
    return matrices


def reference_file_lagged_correlation_v1(
    source: Sequence[float], target: Sequence[float], horizon: int
) -> float | None:
    """Independent scalar implementation of the frozen file-local statistic."""

    if horizon not in EXPECTED_HORIZONS or len(source) != len(target):
        raise StatisticalCandidateDiscoveryError("failed_stat_protocol_compliance")
    dx = [float(source[index]) - float(source[index - 1]) for index in range(1, len(source))]
    dy = [float(target[index]) - float(target[index - 1]) for index in range(1, len(target))]
    if len(dx) <= horizon:
        return None
    return pearson_correlation_reference_v1(dx[:-horizon], dy[horizon:])


def verify_vectorized_parity_v1() -> None:
    """Require deterministic synthetic parity before any optimized real run."""

    backend = _require_numpy()
    generator = backend.random.default_rng(39039)
    source = generator.normal(size=(256, 4)).cumsum(axis=0)
    target = backend.empty((256, 4), dtype=backend.float64)
    target[:, 0] = backend.roll(source[:, 0], 1) + generator.normal(0.0, 0.01, 256)
    target[:, 1] = -backend.roll(source[:, 1], 5) + generator.normal(0.0, 0.01, 256)
    target[:, 2] = 7.0
    target[:, 3] = generator.normal(size=256).cumsum()
    source[10, 3] = backend.nan
    target[20, 3] = backend.inf
    matrices = vectorized_file_lagged_correlations_v1(
        source_values=source, target_values=target
    )
    for horizon in EXPECTED_HORIZONS:
        for source_index in range(source.shape[1]):
            for target_index in range(target.shape[1]):
                expected = reference_file_lagged_correlation_v1(
                    source[:, source_index], target[:, target_index], horizon
                )
                observed = _finite_or_none(matrices[horizon][source_index, target_index])
                if expected is None or observed is None:
                    if expected is not None or observed is not None:
                        raise StatisticalCandidateDiscoveryError(
                            "failed_stat_numerical_parity"
                        )
                    continue
                if not math.isclose(
                    expected,
                    observed,
                    rel_tol=PARITY_RELATIVE_TOLERANCE,
                    abs_tol=PARITY_ABSOLUTE_TOLERANCE,
                ):
                    raise StatisticalCandidateDiscoveryError(
                        "failed_stat_numerical_parity"
                    )


def select_pair_horizon_v1(
    correlations: Mapping[int, tuple[float | None, float | None]],
) -> tuple[tuple[HorizonCorrelationV1, ...], StatisticalHorizonSelectionV1, str | None]:
    """Apply C0 selection while preserving unusable values as null evidence."""

    if tuple(sorted(correlations)) != EXPECTED_HORIZONS:
        raise StatisticalCandidateDiscoveryError("failed_stat_protocol_compliance")
    horizon_records: list[HorizonCorrelationV1] = []
    for horizon in EXPECTED_HORIZONS:
        train1 = _finite_or_none(correlations[horizon][0])
        train2 = _finite_or_none(correlations[horizon][1])
        usable1 = train1 is not None
        usable2 = train2 is not None
        sign_stable = bool(
            usable1
            and usable2
            and train1 != 0.0
            and train2 != 0.0
            and math.copysign(1.0, train1) == math.copysign(1.0, train2)
        )
        strength = min(abs(train1), abs(train2)) if sign_stable else None
        horizon_records.append(
            HorizonCorrelationV1(
                horizon_seconds=horizon,
                r_train1=train1,
                r_train2=train2,
                train1_usable=usable1,
                train2_usable=usable2,
                sign_stable=sign_stable,
                stability_strength=strength,
            )
        )
    stable_records = tuple(item for item in horizon_records if item.sign_stable)
    if stable_records:
        selected = min(
            stable_records,
            key=lambda item: (-float(item.stability_strength), item.horizon_seconds),
        )
        selection = StatisticalHorizonSelectionV1(
            "cross_file_sign_stable",
            selected.horizon_seconds,
            float(selected.stability_strength),
            selected.r_train1,
            selected.r_train2,
        )
    else:
        selection = StatisticalHorizonSelectionV1(
            "direction_unstable", None, 0.0, None, None
        )
    normalized = {
        item.horizon_seconds: (
            item.r_train1 if item.r_train1 is not None else 0.0,
            item.r_train2 if item.r_train2 is not None else 0.0,
        )
        for item in horizon_records
    }
    products = tuple(left * right for left, right in normalized.values())
    if all(math.isfinite(item) for item in products) and all(
        not (
            left != 0.0
            and right != 0.0
            and math.copysign(1.0, left) == math.copysign(1.0, right)
            and product == 0.0
        )
        for (left, right), product in zip(normalized.values(), products)
    ):
        try:
            c0_selection = select_statistical_horizon_v1(normalized)
        except CandidateDiscoveryProtocolError as exc:
            raise StatisticalCandidateDiscoveryError(
                "failed_stat_protocol_compliance"
            ) from exc
        if c0_selection != selection:
            raise StatisticalCandidateDiscoveryError("failed_stat_protocol_compliance")
    sign: str | None = None
    if selection.status == "cross_file_sign_stable":
        if selection.train1_correlation is None or selection.train2_correlation is None:
            raise StatisticalCandidateDiscoveryError("failed_stat_protocol_compliance")
        sign = "positive" if selection.train1_correlation > 0.0 else "negative"
    return tuple(horizon_records), selection, sign


def rank_pair_evidence_v1(
    evaluations: Sequence[PairStatisticalEvidenceV1],
) -> tuple[PairStatisticalEvidenceV1, ...]:
    """Apply the one frozen C0 ranking to supported and audit-only pairs."""

    by_pair = {(item.source, item.target): item for item in evaluations}
    if len(by_pair) != len(evaluations):
        raise StatisticalCandidateDiscoveryError("failed_stat_protocol_compliance")
    rank_inputs = tuple(
        StatisticalRankInputV1(item.source, item.target, item.selection)
        for item in evaluations
    )
    try:
        ranked_inputs = rank_statistical_candidates_v1(rank_inputs)
    except CandidateDiscoveryProtocolError as exc:
        raise StatisticalCandidateDiscoveryError(
            "failed_stat_protocol_compliance"
        ) from exc
    return tuple(by_pair[(item.source, item.target)] for item in ranked_inputs)


def discover_statistical_candidates_v1(
    *,
    bundle: CandidateDiscoveryProtocolBundleV1,
    train1: AuthorizedFileMatrixV1,
    train2: AuthorizedFileMatrixV1,
) -> tuple[PairStatisticalEvidenceV1, ...]:
    """Evaluate and deterministically rank all 144 frozen pairs."""

    backend = _require_numpy()
    sources = bundle.universe_policy.source_variables
    targets = bundle.universe_policy.target_variables
    expected_columns = sources + targets
    if train1.columns != expected_columns or train2.columns != expected_columns:
        raise StatisticalCandidateDiscoveryError("failed_stat_data_boundary")
    matrices_by_file: dict[str, dict[int, Any]] = {}
    for matrix in (train1, train2):
        matrices_by_file[matrix.relative_path] = vectorized_file_lagged_correlations_v1(
            source_values=matrix.values[:, : len(sources)],
            target_values=matrix.values[:, len(sources) :],
        )
    evaluations: list[PairStatisticalEvidenceV1] = []
    for source_index, source in enumerate(sources):
        for target_index, target in enumerate(targets):
            assert_stat_candidate_in_universe_v1(bundle, source, target)
            correlations = {
                horizon: (
                    _finite_or_none(
                        matrices_by_file[EXPECTED_FILES[0]][horizon][source_index, target_index]
                    ),
                    _finite_or_none(
                        matrices_by_file[EXPECTED_FILES[1]][horizon][source_index, target_index]
                    ),
                )
                for horizon in EXPECTED_HORIZONS
            }
            records, selection, sign = select_pair_horizon_v1(correlations)
            evaluations.append(
                PairStatisticalEvidenceV1(
                    source=source,
                    target=target,
                    horizons=records,
                    selection=selection,
                    correlation_sign=sign,
                )
            )
    expected_pairs = eligible_pair_records_v1(sources, targets)
    if (
        len(evaluations) != EXPECTED_PAIR_COUNT
        or tuple((item.source, item.target) for item in evaluations) != expected_pairs
    ):
        raise StatisticalCandidateDiscoveryError("failed_stat_protocol_compliance")
    ranked = rank_pair_evidence_v1(evaluations)
    if len(ranked) != EXPECTED_PAIR_COUNT or len(set(expected_pairs)) != EXPECTED_PAIR_COUNT:
        raise StatisticalCandidateDiscoveryError("failed_stat_protocol_compliance")
    # Keep the backend reference live until both file matrices have been used.
    if backend is None:  # pragma: no cover
        raise StatisticalCandidateDiscoveryError("failed_stat_numerical_backend_unavailable")
    return ranked


def build_private_ledger_v1(
    *,
    ranked_pairs: Sequence[PairStatisticalEvidenceV1],
    execution_code_commit: str,
    created_at: str,
) -> dict[str, Any]:
    content = {
        "schema_version": "1.0.0",
        "artifact_type": "statistical_candidate_private_ledger_v1",
        "task_id": TASK_ID,
        "arm_id": ARM_ID,
        "c0_protocol_hash": EXPECTED_C0_PROTOCOL_HASH,
        "stat_policy_hash": EXPECTED_STAT_POLICY_HASH,
        "pair_universe_hash": EXPECTED_PAIR_UNIVERSE_HASH,
        "evaluated_pair_count": len(ranked_pairs),
        "contains_raw_time_series_samples": False,
        "contains_event_timestamps": False,
        "pairs": [
            item.to_private_dict(audit_rank=index)
            for index, item in enumerate(ranked_pairs, start=1)
        ],
        "creation_metadata": {
            "created_at": created_at,
            "created_by": TASK_ID,
            "code_commit": execution_code_commit,
            "config_hash": EXPECTED_STAT_POLICY_HASH,
        },
    }
    return _self_hashed(content)


def build_data_access_audit_v1(
    *,
    ledger: STATDataAccessLedgerV1,
    private_ledger_hash: str,
    execution_code_commit: str,
    created_at: str,
) -> dict[str, Any]:
    content = {
        "schema_version": "1.0.0",
        "artifact_type": "task039c_stat_data_access_audit_v1",
        "task_id": TASK_ID,
        "arm_id": ARM_ID,
        "status": PASSED_STATUS,
        "c0_protocol_hash": EXPECTED_C0_PROTOCOL_HASH,
        "stat_policy_hash": EXPECTED_STAT_POLICY_HASH,
        "dataset_manifest_id": EXPECTED_DATASET_MANIFEST_ID,
        "allowed_process_id": EXPECTED_PROCESS_ID,
        "allowed_value_files": list(EXPECTED_FILES),
        "access_records": list(ledger.records),
        "private_detailed_ledger_hash": private_ledger_hash,
        "train1_accessed": True,
        "train2_accessed": True,
        "train3_accessed": False,
        "train4_accessed": False,
        "test_accessed": False,
        "labels_accessed": False,
        "attack_summary_accessed": False,
        "private_label_custody_accessed": False,
        "p2_feature_values_accessed": False,
        "p3_feature_values_accessed": False,
        "p4_feature_values_accessed": False,
        "br2_pair_supervision_used": False,
        "cross_arm_score_used": False,
        "timestamp_values_read": False,
        "file_boundaries_explicit": True,
        "cross_file_difference_created": False,
        "cross_file_lag_pair_created": False,
        "raw_time_series_samples_persisted": False,
        "absolute_local_paths_persisted": False,
        "creation_metadata": {
            "created_at": created_at,
            "created_by": TASK_ID,
            "code_commit": execution_code_commit,
            "config_hash": EXPECTED_STAT_POLICY_HASH,
        },
    }
    document = _self_hashed(content)
    assert_public_stat_payload_safe_v1(document)
    return document


def _public_rank_record(
    item: PairStatisticalEvidenceV1,
    *,
    rank: int,
    private_ledger_hash: str,
) -> dict[str, Any]:
    if not item.supported or item.correlation_sign is None:
        raise StatisticalCandidateDiscoveryError("failed_stat_protocol_compliance")
    return {
        "rank": rank,
        "source": item.source,
        "target": item.target,
        "selected_horizon_seconds": item.selection.selected_horizon,
        "correlation_sign": item.correlation_sign,
        "r_train1": _finite_or_none(item.selection.train1_correlation),
        "r_train2": _finite_or_none(item.selection.train2_correlation),
        "stability_strength": _finite_or_none(item.selection.score),
        "method_status": item.selection.status,
        "method_evidence_refs": [private_ledger_hash],
    }


def build_public_result_v1(
    *,
    ranked_pairs: Sequence[PairStatisticalEvidenceV1],
    private_ledger_hash: str,
    data_access_audit_hash: str,
    execution_code_commit: str,
    created_at: str,
) -> dict[str, Any]:
    supported = tuple(item for item in ranked_pairs if item.supported)
    unstable_count = len(ranked_pairs) - len(supported)
    public_ranking = [
        _public_rank_record(item, rank=index, private_ledger_hash=private_ledger_hash)
        for index, item in enumerate(supported, start=1)
    ]
    ranking_hash = stable_hash_v1(
        {
            "artifact_type": "statistical_supported_ranking_v1",
            "pair_universe_hash": EXPECTED_PAIR_UNIVERSE_HASH,
            "records": [
                {key: value for key, value in item.items() if key != "method_evidence_refs"}
                for item in public_ranking
            ],
        }
    )
    try:
        views = derive_candidate_budget_views_v1(
            tuple((item.source, item.target) for item in supported)
        )
    except CandidateDiscoveryProtocolError as exc:
        raise StatisticalCandidateDiscoveryError(
            "failed_stat_protocol_compliance"
        ) from exc
    rank_by_pair = {
        (item["source"], item["target"]): item["rank"] for item in public_ranking
    }

    def view_records(pairs: Sequence[tuple[str, str]]) -> list[dict[str, Any]]:
        return [
            {"rank": rank_by_pair[(source, target)], "source": source, "target": target}
            for source, target in pairs
        ]

    shortfall_by_k = {
        str(k): {"candidate_shortfall": views.candidate_shortfall[k] > 0, "missing_count": views.candidate_shortfall[k]}
        for k in (10, 20, 40)
    }
    candidate_shortfall = any(item["candidate_shortfall"] for item in shortfall_by_k.values())
    content = {
        "schema_version": "1.0.0",
        "artifact_type": "statistical_candidate_result_v1",
        "task_id": TASK_ID,
        "arm_id": ARM_ID,
        "status": PASSED_STATUS,
        "arm_result_status": "candidate_shortfall" if candidate_shortfall else "passed",
        "c0_protocol_hash": EXPECTED_C0_PROTOCOL_HASH,
        "stat_policy_hash": EXPECTED_STAT_POLICY_HASH,
        "source_identity_hash": EXPECTED_SOURCE_IDENTITY_HASH,
        "target_identity_hash": EXPECTED_TARGET_IDENTITY_HASH,
        "pair_universe_hash": EXPECTED_PAIR_UNIVERSE_HASH,
        "dataset_manifest_id": EXPECTED_DATASET_MANIFEST_ID,
        "process_id": EXPECTED_PROCESS_ID,
        "evaluated_pair_count": len(ranked_pairs),
        "supported_stable_count": len(supported),
        "direction_unstable_count": unstable_count,
        "supported_ranking": public_ranking,
        "ranking_hash": ranking_hash,
        "top10": view_records(views.top10),
        "top20": view_records(views.top20),
        "top40": view_records(views.top40),
        "candidate_shortfall": candidate_shortfall,
        "candidate_shortfall_by_k": shortfall_by_k,
        "private_detailed_ledger_hash": private_ledger_hash,
        "data_access_audit_ref": data_access_audit_hash,
        "train1_accessed": True,
        "train2_accessed": True,
        "train3_accessed": False,
        "train4_accessed": False,
        "test_accessed": False,
        "labels_accessed": False,
        "br2_pair_supervision_used": False,
        "cross_arm_score_used": False,
        "raw_time_series_samples_exposed": False,
        "method_name": "lagged_change_correlation_candidate_score",
        "method_interpretation": "statistical_candidate_evidence_not_causality_or_rule_validity",
        "horizons_seconds": list(EXPECTED_HORIZONS),
        "pearson_definition": "float64_centered_product_moment_on_pairwise_finite_aligned_observations",
        "minimum_finite_observations": MIN_PEARSON_OBSERVATIONS,
        "numerical_backend": "numpy_float64_vectorized_with_independent_math_fsum_parity",
        "parity_absolute_tolerance": PARITY_ABSOLUTE_TOLERANCE,
        "parity_relative_tolerance": PARITY_RELATIVE_TOLERANCE,
        "file_boundaries_explicit": True,
        "reranking_for_k_used": False,
        "unstable_padding_used": False,
        "arbitrary_minimum_correlation_threshold": None,
        "creation_metadata": {
            "created_at": created_at,
            "created_by": TASK_ID,
            "code_commit": execution_code_commit,
            "config_hash": EXPECTED_STAT_POLICY_HASH,
        },
    }
    document = _self_hashed(content)
    assert_public_stat_payload_safe_v1(document)
    return document


def assert_public_stat_payload_safe_v1(document: Mapping[str, Any]) -> None:
    """Reject raw values, exact sensitive keys, and absolute local paths."""

    def walk(value: Any, key: str | None = None) -> None:
        if key in _PUBLIC_PROHIBITED_KEYS:
            raise StatisticalCandidateDiscoveryError("failed_stat_data_boundary")
        if isinstance(value, Mapping):
            for child_key, child_value in value.items():
                walk(child_value, str(child_key))
        elif isinstance(value, (list, tuple)):
            for child in value:
                walk(child, key)
        elif isinstance(value, str) and _ABSOLUTE_WINDOWS_PATH.search(value):
            raise StatisticalCandidateDiscoveryError("failed_stat_data_boundary")
        elif isinstance(value, float) and not math.isfinite(value):
            raise StatisticalCandidateDiscoveryError("failed_stat_data_boundary")

    walk(document)


__all__ = [
    "ARM_ID",
    "EXPECTED_BASE_COMMIT",
    "EXPECTED_BRANCH",
    "EXPECTED_C0_PROTOCOL_HASH",
    "EXPECTED_DATASET_MANIFEST_ID",
    "EXPECTED_FILES",
    "EXPECTED_HORIZONS",
    "EXPECTED_PAIR_COUNT",
    "EXPECTED_PAIR_UNIVERSE_HASH",
    "EXPECTED_PROCESS_ID",
    "EXPECTED_SOURCE_IDENTITY_HASH",
    "EXPECTED_STAT_POLICY_HASH",
    "EXPECTED_TARGET_IDENTITY_HASH",
    "PASSED_STATUS",
    "AuthorizedFileMatrixV1",
    "ExpectedFileIdentityV1",
    "HorizonCorrelationV1",
    "PairStatisticalEvidenceV1",
    "STATDataAccessLedgerV1",
    "StatisticalCandidateDiscoveryError",
    "assert_public_stat_payload_safe_v1",
    "assert_stat_candidate_in_universe_v1",
    "authorize_stat_value_request_v1",
    "build_data_access_audit_v1",
    "build_private_ledger_v1",
    "build_public_result_v1",
    "discover_statistical_candidates_v1",
    "file_local_differences_v1",
    "load_frozen_c0_bundle_v1",
    "load_verified_file_identities_v1",
    "pearson_correlation_reference_v1",
    "read_authorized_stat_file_v1",
    "rank_pair_evidence_v1",
    "reference_file_lagged_correlation_v1",
    "reject_br2_pair_supervision_v1",
    "select_pair_horizon_v1",
    "vectorized_file_lagged_correlations_v1",
    "verify_vectorized_parity_v1",
]
