"""Freeze or independently replay the prospective DG05 Executable V10 package."""
from __future__ import annotations

from pathlib import Path

import freeze_dg05_v5_release as release_freezer


release_freezer.VERSION_TAG = "V10"
release_freezer.EXECUTABLE_VERSION = "DG05_EXECUTABLE_V10"
release_freezer.OUT = (
    release_freezer.ROOT
    / "research_control_center/validation_v2/dg05_v10_release"
)
release_freezer.SUPERSEDED_CANDIDATE_HASH = (
    "e2ca02f97171b75f27a1617077e438b7793845ec649a58ec333ed56232687c04"
)
release_freezer.FREEZER_PATH = Path(__file__)


if __name__ == "__main__":
    release_freezer.main()
