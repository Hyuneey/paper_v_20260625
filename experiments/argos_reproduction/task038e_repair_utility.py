"""Repair outer-utility classification helpers."""


def utility_classification(combined_f1: float, detector_f1: float) -> str:
    if combined_f1 > detector_f1:
        return "outer_useful"
    if combined_f1 < detector_f1:
        return "outer_regressive"
    return "outer_equal"
