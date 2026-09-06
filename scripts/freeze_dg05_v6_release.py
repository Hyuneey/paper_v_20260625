"""Freeze or independently replay the prospective DG05 Executable V6 package."""
from __future__ import annotations

from pathlib import Path

import freeze_dg05_v5_release as release_freezer


release_freezer.VERSION_TAG = "V6"
release_freezer.EXECUTABLE_VERSION = "DG05_EXECUTABLE_V6"
release_freezer.OUT = (
    release_freezer.ROOT
    / "research_control_center/validation_v2/dg05_v6_release"
)
release_freezer.SUPERSEDED_CANDIDATE_HASH = (
    "b8a186d54a251b8691401d9db4ca87b9c45b87e17befb07c2766d1c3e41097bf"
)
release_freezer.FREEZER_PATH = Path(__file__)


if __name__ == "__main__":
    release_freezer.main()
