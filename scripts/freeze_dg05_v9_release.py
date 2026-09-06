"""Freeze or independently replay the prospective DG05 Executable V9 package."""
from __future__ import annotations

from pathlib import Path

import freeze_dg05_v5_release as release_freezer


release_freezer.VERSION_TAG = "V9"
release_freezer.EXECUTABLE_VERSION = "DG05_EXECUTABLE_V9"
release_freezer.OUT = (
    release_freezer.ROOT
    / "research_control_center/validation_v2/dg05_v9_release"
)
release_freezer.SUPERSEDED_CANDIDATE_HASH = (
    "b05f3f3a0ae79f061d467557365ff154f1a2bc79d03f772e0784125a705b8c90"
)
release_freezer.FREEZER_PATH = Path(__file__)


if __name__ == "__main__":
    release_freezer.main()
