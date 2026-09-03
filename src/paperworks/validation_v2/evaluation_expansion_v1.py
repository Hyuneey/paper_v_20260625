"""Public-only contracts for the Validation V2 evaluation expansion.

This module contains arithmetic and structural validation only.  It never
opens HAI data, labels, predictions, credentials, or provider transports.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import comb, sqrt
from typing import Iterable, Mapping, Sequence


class EvaluationExpansionError(ValueError):
    """Raised when a prospective evaluation contract is incomplete."""


PANEL_IDS = (
    "HAI23_TEST1_DEVELOPMENT_V1",
    "HAI23_TEST2_PRIMARY_HELDOUT_V1",
    "HAI22_EXTERNAL_REPLICATION_V1",
    "HAI21_EXTERNAL_REPLICATION_V1",
)

ALLOWED_PANEL_ROLES = {
    "DEVELOPMENT_ONLY",
    "PRIMARY_HELDOUT",
    "EXTERNAL_VERSION_REPLICATION_1",
    "EXTERNAL_VERSION_REPLICATION_2",
}

ETAPR_UPSTREAM = "https://github.com/saurf4ng/eTaPR"
ETAPR_COMMIT = "af9e7aed35cfd160cbe0d04c8ec4c102502cb677"


@dataclass(frozen=True)
class Hai21ChronologicalPartitionV1:
    """Value-blind arithmetic for the prospective HAI 21.03 train3 split."""

    row_count: int
    purge_rows: int
    block_a_start: int
    block_a_stop: int
    block_b_start: int
    block_b_stop: int


def partition_hai21_train3_v1(row_count: int, purge_rows: int) -> Hai21ChronologicalPartitionV1:
    """Split by row count, place an explicit purge between A and B, fail closed."""

    if not isinstance(row_count, int) or isinstance(row_count, bool) or row_count <= 0:
        raise EvaluationExpansionError("row_count must be a positive integer")
    if not isinstance(purge_rows, int) or isinstance(purge_rows, bool) or purge_rows < 0:
        raise EvaluationExpansionError("purge_rows must be a non-negative integer")
    midpoint = row_count // 2
    left_purge = purge_rows // 2
    right_purge = purge_rows - left_purge
    a_stop = midpoint - left_purge
    b_start = midpoint + right_purge
    if a_stop <= 0 or b_start >= row_count or a_stop > b_start:
        raise EvaluationExpansionError("purge leaves an invalid chronological partition")
    return Hai21ChronologicalPartitionV1(
        row_count=row_count,
        purge_rows=purge_rows,
        block_a_start=0,
        block_a_stop=a_stop,
        block_b_start=b_start,
        block_b_stop=row_count,
    )


def wilson_interval_95_v1(successes: int, total: int) -> tuple[float, float] | None:
    """Return the two-sided Wilson 95% interval; undefined denominators stay None."""

    for name, value in (("successes", successes), ("total", total)):
        if not isinstance(value, int) or isinstance(value, bool):
            raise EvaluationExpansionError(f"{name} must be an integer")
    if total < 0 or successes < 0 or successes > total:
        raise EvaluationExpansionError("invalid binomial counts")
    if total == 0:
        return None
    z = 1.959963984540054
    estimate = successes / total
    denominator = 1.0 + (z * z) / total
    centre = estimate + (z * z) / (2.0 * total)
    margin = z * sqrt((estimate * (1.0 - estimate) + (z * z) / (4.0 * total)) / total)
    return ((centre - margin) / denominator, (centre + margin) / denominator)


def mcnemar_exact_two_sided_v1(b_only: int, c_only: int) -> float | None:
    """Exact paired two-sided McNemar p-value from discordant scenario counts."""

    for name, value in (("b_only", b_only), ("c_only", c_only)):
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise EvaluationExpansionError(f"{name} must be a non-negative integer")
    discordant = b_only + c_only
    if discordant == 0:
        return None
    tail = sum(comb(discordant, index) for index in range(min(b_only, c_only) + 1))
    return min(1.0, 2.0 * tail / (2**discordant))


def validate_aligned_scenario_sets_v1(
    left_ids: Sequence[str], right_ids: Sequence[str]
) -> tuple[str, ...]:
    """Require exact, duplicate-free, ordered identity alignment before pairing."""

    left = tuple(left_ids)
    right = tuple(right_ids)
    if not left or left != right:
        raise EvaluationExpansionError("paired scenario identities are not exactly aligned")
    if len(set(left)) != len(left) or any(not value for value in left):
        raise EvaluationExpansionError("scenario identities must be unique and non-empty")
    return left


def validate_panel_registry_v1(rows: Iterable[Mapping[str, str]]) -> None:
    """Validate public panel identities and preparation-only access boundaries."""

    materialized = list(rows)
    if tuple(row.get("panel_id", "") for row in materialized) != PANEL_IDS:
        raise EvaluationExpansionError("panel registry identity/order mismatch")
    for row in materialized:
        if row.get("role") not in ALLOWED_PANEL_ROLES:
            raise EvaluationExpansionError("unknown panel role")
        if row["panel_id"] == PANEL_IDS[0]:
            if row.get("result_status") != "COMPLETE_DEVELOPMENT_ONLY":
                raise EvaluationExpansionError("development panel status mismatch")
        else:
            if row.get("attack_access_status") != "NOT_ACCESSED":
                raise EvaluationExpansionError("future attack panel was accessed")
            if row.get("label_access_status") != "NOT_ACCESSED":
                raise EvaluationExpansionError("future label panel was accessed")
            if row.get("result_status") != "PREREGISTRATION_PREPARATION_ONLY":
                raise EvaluationExpansionError("future panel status mismatch")


def validate_version_separated_summary_v1(
    version_rows: Sequence[Mapping[str, object]], *, primary_pooled_recall: bool
) -> None:
    """Reject the prohibited IID-style pooled primary result."""

    if primary_pooled_recall:
        raise EvaluationExpansionError("primary pooled Recall is prohibited")
    versions = [str(row.get("dataset_version", "")) for row in version_rows]
    if len(versions) < 2 or len(set(versions)) != len(versions) or any(not item for item in versions):
        raise EvaluationExpansionError("version summaries must be separate and uniquely identified")


def validate_etapr_freeze_v1(config: Mapping[str, object]) -> None:
    """Validate a future eTaPR freeze without implementing or executing eTaPR."""

    if config.get("upstream") != ETAPR_UPSTREAM or config.get("commit") != ETAPR_COMMIT:
        raise EvaluationExpansionError("official eTaPR source identity mismatch")
    if config.get("implementation_mode") != "OFFICIAL_OR_CONFORMANCE_VERIFIED_WRAPPER":
        raise EvaluationExpansionError("look-alike eTaPR implementations are prohibited")
    if config.get("attack_data_accessed") is not False:
        raise EvaluationExpansionError("eTaPR preparation accessed attack data")
    if config.get("point_adjustment") is not False:
        raise EvaluationExpansionError("point adjustment is prohibited")
    for field in ("theta_p", "theta_r", "delta"):
        value = config.get(field)
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= float(value) <= 1:
            raise EvaluationExpansionError(f"invalid eTaPR parameter: {field}")


def binary_stream_to_closed_ranges_v1(values: Sequence[bool], *, file_id: str) -> tuple[tuple[int, int, str], ...]:
    """Convert one file-local Boolean stream to inclusive eTaPR ranges.

    The function performs representation conversion only.  It does not score,
    adjust, dilate, or combine ranges across files.
    """

    if not file_id or any(not isinstance(value, bool) for value in values):
        raise EvaluationExpansionError("file_id and strict Boolean values are required")
    ranges: list[tuple[int, int, str]] = []
    start: int | None = None
    for index, value in enumerate(values):
        if value and start is None:
            start = index
        elif not value and start is not None:
            ranges.append((start, index - 1, f"{file_id}:{len(ranges) + 1}"))
            start = None
    if start is not None:
        ranges.append((start, len(values) - 1, f"{file_id}:{len(ranges) + 1}"))
    return tuple(ranges)
