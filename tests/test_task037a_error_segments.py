import pytest

from experiments.argos_reproduction.detector_error_segments import (
    DetectorSegmentError,
    argos_inclusive_intervals,
    build_error_segments,
    segment_manifest_hash,
    segments_by_category,
)


def test_error_segments_are_maximal_sorted_and_half_open():
    segments = build_error_segments(
        [0, 0, 1, 1, 1, 0, 0, 1],
        [0, 1, 0, 0, 1, 1, 0, 1],
    )
    grouped = segments_by_category(segments)
    assert grouped["TN"] == ((0, 1), (6, 7))
    assert grouped["FP"] == ((1, 2), (5, 6))
    assert grouped["FN"] == ((2, 4),)
    assert grouped["TP"] == ((4, 5), (7, 8))
    assert argos_inclusive_intervals(grouped)["FN"] == [[2, 3]]
    assert segment_manifest_hash(grouped, prediction_hash="a" * 64, threshold_hash="b" * 64) == segment_manifest_hash(grouped, prediction_hash="a" * 64, threshold_hash="b" * 64)


def test_segment_contract_rejects_nonbinary_or_mismatched_inputs():
    with pytest.raises(DetectorSegmentError):
        build_error_segments([0, 2], [0, 1])
    with pytest.raises(DetectorSegmentError):
        build_error_segments([0], [0, 1])
