"""Fail-closed input boundary for Utility Evaluator V1.

The production loader is deliberately an authorization gate in this freeze:
no real utility execution authorization exists, so it raises before inspecting
or resolving a caller path.  The only executable input plane is the explicit
``SYNTHETIC_CONTRACT_ONLY`` in-memory frame below.
"""

from __future__ import annotations

from paperworks.v6.task039e3_r2r_utility_evaluator_authority_v1 import (
    EvaluatorAuthorityBundleV1,
    validate_evaluator_authority_bundle_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_types_v1 import (
    SYNTHETIC_AUTHORITY_IDENTITY,
    SYNTHETIC_CONTRACT_ONLY,
    SyntheticFeatureFrameV1,
    SyntheticFeatureRowV1,
    UtilityEvaluatorV1Error,
    dataclass_payload_v1,
    stable_hash_v1,
    strict_float_v1,
    strict_int_v1,
    strict_str_v1,
    strict_tuple_v1,
)
from paperworks.v6.task039e3_r2r_utility_protocol_v3 import (
    FILE_ROW_COUNTS,
    FILE_SPLITS,
    HAI_DATASET_MANIFEST_HASH,
)
from paperworks.v6.task039e3_r2r_utility_protocol_v4 import (
    CANONICAL_V4_AUTHORITY_HASH,
    UtilityProtocolV4CanonicalAuthority,
    validate_utility_protocol_v4_authority,
)


def _validated_v4_authority(
    authority_bundle: EvaluatorAuthorityBundleV1,
) -> UtilityProtocolV4CanonicalAuthority:
    try:
        validate_evaluator_authority_bundle_v1(authority_bundle)
        authority = authority_bundle.v4_authority
        observed = validate_utility_protocol_v4_authority(authority)
    except Exception as error:
        raise UtilityEvaluatorV1Error("INPUT_AUTHORITY_BUNDLE_INVALID") from error
    if observed != CANONICAL_V4_AUTHORITY_HASH:
        raise UtilityEvaluatorV1Error("INPUT_V4_AUTHORITY_NOT_CURRENT")
    return authority


def load_authorized_hai_feature_frame_v1(
    authority_bundle: EvaluatorAuthorityBundleV1,
    *,
    execution_authorization: object,
    dataset_manifest_identity: object,
    split_identity: object,
    source_file_identity: object,
    expected_file_identity: object,
) -> SyntheticFeatureFrameV1:
    """Fail before path resolution or file I/O until a later task authorizes it.

    There is intentionally no path parameter.  A future implementation must
    add a typed execution authority rather than accepting an arbitrary path.
    """

    _validated_v4_authority(authority_bundle)
    del (
        execution_authorization,
        dataset_manifest_identity,
        split_identity,
        source_file_identity,
        expected_file_identity,
    )
    raise UtilityEvaluatorV1Error("REAL_HAI_EXECUTION_AUTHORIZATION_UNAVAILABLE")


def _row_payload_v1(
    *,
    dataset_manifest_identity: str,
    split_identity: str,
    source_file_identity: str,
    physical_row_index: int,
    timestamp_second: int,
    feature_values: tuple[tuple[str, float], ...],
) -> dict[str, object]:
    validated_feature_values = tuple(
        _validate_feature_pair_v1(pair) for pair in feature_values
    )
    return {
        "artifact_type": "task039e3_r2r_utility_evaluator_v1_synthetic_feature_row",
        "dataset_manifest_identity": dataset_manifest_identity,
        "execution_mode": SYNTHETIC_CONTRACT_ONLY,
        "feature_values": [
            {"feature": feature, "value": value}
            for feature, value in validated_feature_values
        ],
        "physical_row_index": physical_row_index,
        "source_file_identity": source_file_identity,
        "split_identity": split_identity,
        "synthetic_authority_identity": SYNTHETIC_AUTHORITY_IDENTITY,
        "timestamp_second": timestamp_second,
    }


def _validate_feature_pair_v1(pair: object) -> tuple[str, float]:
    """Reject widened feature pairs before destructuring or hash replay."""

    if type(pair) is not tuple or len(pair) != 2:
        raise UtilityEvaluatorV1Error("SYNTHETIC_FEATURE_PAIR_CONTAINER_INVALID")
    feature = strict_str_v1(pair[0], "feature")
    value = strict_float_v1(pair[1], f"feature[{feature}]")
    return feature, value


def _frame_payload_v1(frame: SyntheticFeatureFrameV1) -> dict[str, object]:
    return {
        "artifact_type": "task039e3_r2r_utility_evaluator_v1_synthetic_feature_frame",
        "dataset_manifest_identity": frame.dataset_manifest_identity,
        "execution_mode": frame.execution_mode,
        "feature_schema_authority_hash": frame.feature_schema_authority_hash,
        "ordered_features": list(frame.ordered_features),
        "rows": [dataclass_payload_v1(row) for row in frame.rows],
        "source_file_identity": frame.source_file_identity,
        "split_identity": frame.split_identity,
        "synthetic_authority_identity": frame.synthetic_authority_identity,
    }


def build_synthetic_feature_frame_v1(
    authority_bundle: EvaluatorAuthorityBundleV1,
    *,
    source_file_identity: str,
    start_physical_row_index: int,
    rows: tuple[tuple[float, ...], ...],
) -> SyntheticFeatureFrameV1:
    """Build one exact 22-feature, finite, in-memory synthetic frame.

    Dataset, split, schema, ordering, row identity, and timestamp coordinate are
    factory-derived; none is supplied as caller authority.
    """

    authority = _validated_v4_authority(authority_bundle)
    file_identity = strict_str_v1(source_file_identity, "source_file_identity")
    if file_identity not in FILE_ROW_COUNTS:
        raise UtilityEvaluatorV1Error("SYNTHETIC_SOURCE_FILE_IDENTITY_UNKNOWN")
    start = strict_int_v1(start_physical_row_index, "start_physical_row_index", minimum=0)
    canonical_rows = strict_tuple_v1(rows, "rows")
    if not canonical_rows:
        raise UtilityEvaluatorV1Error("SYNTHETIC_FRAME_EMPTY")
    ordered_features = authority.feature_schema.union_features
    if type(ordered_features) is not tuple or len(ordered_features) != 22:
        raise UtilityEvaluatorV1Error("SYNTHETIC_FEATURE_SCHEMA_NOT_12_10_22")
    if start + len(canonical_rows) > FILE_ROW_COUNTS[file_identity]:
        raise UtilityEvaluatorV1Error("SYNTHETIC_FRAME_OUTSIDE_FILE_COORDINATES")
    built_rows = []
    for offset, values in enumerate(canonical_rows):
        canonical_values = strict_tuple_v1(values, "row values")
        if len(canonical_values) != len(ordered_features):
            raise UtilityEvaluatorV1Error("SYNTHETIC_FEATURE_CARDINALITY_MISMATCH")
        feature_values = tuple(
            (
                feature,
                strict_float_v1(value, f"feature[{feature}]"),
            )
            for feature, value in zip(ordered_features, canonical_values, strict=True)
        )
        physical_index = start + offset
        timestamp_second = physical_index
        payload = _row_payload_v1(
            dataset_manifest_identity=HAI_DATASET_MANIFEST_HASH,
            split_identity=FILE_SPLITS[file_identity],
            source_file_identity=file_identity,
            physical_row_index=physical_index,
            timestamp_second=timestamp_second,
            feature_values=feature_values,
        )
        built_rows.append(
            SyntheticFeatureRowV1(
                physical_index,
                timestamp_second,
                feature_values,
                stable_hash_v1(payload),
            )
        )
    provisional = SyntheticFeatureFrameV1(
        SYNTHETIC_CONTRACT_ONLY,
        SYNTHETIC_AUTHORITY_IDENTITY,
        HAI_DATASET_MANIFEST_HASH,
        FILE_SPLITS[file_identity],
        file_identity,
        authority.feature_schema.authority_hash,
        ordered_features,
        tuple(built_rows),
        "",
    )
    return SyntheticFeatureFrameV1(
        provisional.execution_mode,
        provisional.synthetic_authority_identity,
        provisional.dataset_manifest_identity,
        provisional.split_identity,
        provisional.source_file_identity,
        provisional.feature_schema_authority_hash,
        provisional.ordered_features,
        provisional.rows,
        stable_hash_v1(_frame_payload_v1(provisional)),
    )


def validate_synthetic_feature_frame_v1(
    frame: SyntheticFeatureFrameV1,
    authority_bundle: EvaluatorAuthorityBundleV1,
) -> str:
    authority = _validated_v4_authority(authority_bundle)
    if type(frame) is not SyntheticFeatureFrameV1:
        raise UtilityEvaluatorV1Error("SYNTHETIC_FRAME_TYPE_INVALID")
    if (
        frame.execution_mode != SYNTHETIC_CONTRACT_ONLY
        or frame.synthetic_authority_identity != SYNTHETIC_AUTHORITY_IDENTITY
        or frame.dataset_manifest_identity != HAI_DATASET_MANIFEST_HASH
        or frame.source_file_identity not in FILE_ROW_COUNTS
        or frame.split_identity != FILE_SPLITS.get(frame.source_file_identity)
        or frame.feature_schema_authority_hash != authority.feature_schema.authority_hash
        or frame.ordered_features != authority.feature_schema.union_features
        or len(frame.ordered_features) != 22
        or type(frame.rows) is not tuple
        or not frame.rows
    ):
        raise UtilityEvaluatorV1Error("SYNTHETIC_FRAME_AUTHORITY_INVALID")
    expected_indices = tuple(
        range(frame.rows[0].physical_row_index, frame.rows[0].physical_row_index + len(frame.rows))
    )
    if tuple(row.physical_row_index for row in frame.rows) != expected_indices:
        raise UtilityEvaluatorV1Error("SYNTHETIC_FRAME_ROW_COORDINATES_INVALID")
    if expected_indices[-1] >= FILE_ROW_COUNTS[frame.source_file_identity]:
        raise UtilityEvaluatorV1Error("SYNTHETIC_FRAME_OUTSIDE_FILE_COORDINATES")
    for row in frame.rows:
        if type(row) is not SyntheticFeatureRowV1:
            raise UtilityEvaluatorV1Error("SYNTHETIC_ROW_TYPE_INVALID")
        strict_int_v1(row.physical_row_index, "physical_row_index", minimum=0)
        if row.timestamp_second != row.physical_row_index or type(row.timestamp_second) is not int:
            raise UtilityEvaluatorV1Error("SYNTHETIC_TIMESTAMP_COORDINATE_INVALID")
        if type(row.feature_values) is not tuple:
            raise UtilityEvaluatorV1Error("SYNTHETIC_FEATURE_CONTAINER_INVALID")
        validated_feature_values = tuple(
            _validate_feature_pair_v1(pair) for pair in row.feature_values
        )
        if tuple(feature for feature, _ in validated_feature_values) != frame.ordered_features:
            raise UtilityEvaluatorV1Error("SYNTHETIC_FEATURE_ORDER_INVALID")
        expected_row_hash = stable_hash_v1(
            _row_payload_v1(
                dataset_manifest_identity=frame.dataset_manifest_identity,
                split_identity=frame.split_identity,
                source_file_identity=frame.source_file_identity,
                physical_row_index=row.physical_row_index,
                timestamp_second=row.timestamp_second,
                feature_values=validated_feature_values,
            )
        )
        if row.row_identity != expected_row_hash:
            raise UtilityEvaluatorV1Error("SYNTHETIC_ROW_IDENTITY_INVALID")
    if frame.frame_hash != stable_hash_v1(_frame_payload_v1(frame)):
        raise UtilityEvaluatorV1Error("SYNTHETIC_FRAME_HASH_INVALID")
    return frame.frame_hash


def feature_series_v1(
    frame: SyntheticFeatureFrameV1,
    authority_bundle: EvaluatorAuthorityBundleV1,
    feature: str,
) -> tuple[float, ...]:
    validate_synthetic_feature_frame_v1(frame, authority_bundle)
    name = strict_str_v1(feature, "feature")
    if name not in frame.ordered_features:
        raise UtilityEvaluatorV1Error("FEATURE_OUTSIDE_CANONICAL_SCHEMA")
    index = frame.ordered_features.index(name)
    return tuple(row.feature_values[index][1] for row in frame.rows)


def feature_value_v1(
    frame: SyntheticFeatureFrameV1,
    authority_bundle: EvaluatorAuthorityBundleV1,
    *,
    physical_row_index: int,
    feature: str,
) -> float:
    validate_synthetic_feature_frame_v1(frame, authority_bundle)
    index = strict_int_v1(physical_row_index, "physical_row_index", minimum=0)
    matches = [row for row in frame.rows if row.physical_row_index == index]
    if len(matches) != 1:
        raise UtilityEvaluatorV1Error("ROW_OUTSIDE_SYNTHETIC_FRAME")
    name = strict_str_v1(feature, "feature")
    if name not in frame.ordered_features:
        raise UtilityEvaluatorV1Error("FEATURE_OUTSIDE_CANONICAL_SCHEMA")
    return matches[0].feature_values[frame.ordered_features.index(name)][1]


__all__ = [
    "EvaluatorAuthorityBundleV1",
    "load_authorized_hai_feature_frame_v1",
    "build_synthetic_feature_frame_v1",
    "validate_synthetic_feature_frame_v1",
    "feature_series_v1",
    "feature_value_v1",
]
