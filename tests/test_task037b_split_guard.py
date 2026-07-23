import json
from pathlib import Path

import pytest

from experiments.argos_reproduction.kpi_detector_split_guard import (
    KpiDetectorSplitGuardError,
    assert_split_allowed,
    load_frozen_splits,
)


ROOT = Path(__file__).resolve().parents[1]


def config():
    return json.loads((ROOT / "configs/argos_reproduction/task037b_dual_lstm_detector_validation.json").read_text())


def test_frozen_ten_kpi_splits_match_task035b_manifest():
    splits = load_frozen_splits(config())
    assert len(splits) == 10
    assert len({item.kpi_id for item in splits}) == 10
    assert all(len(item.split_manifest_hash) == 64 for item in splits)


@pytest.mark.parametrize("name", ["test", "sealed_test", "e2x_test"])
def test_test_split_access_fails_closed(name):
    with pytest.raises(KpiDetectorSplitGuardError, match="SEALED_TEST_ACCESS_PROHIBITED"):
        assert_split_allowed(name)
