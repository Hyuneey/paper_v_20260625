from experiments.argos_reproduction.detector_error_segments import (
    build_error_segments,
    private_segment_manifest,
    segment_counts,
    segments_by_category,
)


def test_generation_error_segments_are_half_open_and_complete():
    grouped = segments_by_category(build_error_segments([0, 1, 1, 0], [0, 0, 1, 1]))
    assert grouped["TN"] == ((0, 1),)
    assert grouped["FN"] == ((1, 2),)
    assert grouped["TP"] == ((2, 3),)
    assert grouped["FP"] == ((3, 4),)
    counts = segment_counts(grouped)
    assert all(counts[key] == {"segment_count": 1, "point_count": 1} for key in counts)
    manifest = private_segment_manifest(
        grouped, kpi_id="synthetic", variant="LSTMADalpha",
        prediction_hash="a" * 64, threshold_hash="b" * 64,
    )
    assert manifest["interval_semantics"] == "half_open"
