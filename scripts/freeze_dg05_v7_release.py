"""Freeze or independently replay the prospective DG05 Executable V7 package."""
from __future__ import annotations

from pathlib import Path

import freeze_dg05_v5_release as release_freezer


release_freezer.VERSION_TAG = "V7"
release_freezer.EXECUTABLE_VERSION = "DG05_EXECUTABLE_V7"
release_freezer.OUT = (
    release_freezer.ROOT
    / "research_control_center/validation_v2/dg05_v7_release"
)
release_freezer.SUPERSEDED_CANDIDATE_HASH = (
    "8d480bcdcc586244ef60c83940aec5decb2662a011becd25bd89948e558ff2cd"
)
release_freezer.FREEZER_PATH = Path(__file__)


if __name__ == "__main__":
    release_freezer.main()
