"""Freeze or independently replay the prospective DG05 Executable V8 package."""
from __future__ import annotations

from pathlib import Path

import freeze_dg05_v5_release as release_freezer


release_freezer.VERSION_TAG = "V8"
release_freezer.EXECUTABLE_VERSION = "DG05_EXECUTABLE_V8"
release_freezer.OUT = (
    release_freezer.ROOT
    / "research_control_center/validation_v2/dg05_v8_release"
)
release_freezer.SUPERSEDED_CANDIDATE_HASH = (
    "4acbf6d5835b2857515363509493820e9a212430b79a2fc8096c1ca6a342e250"
)
release_freezer.FREEZER_PATH = Path(__file__)


if __name__ == "__main__":
    release_freezer.main()
