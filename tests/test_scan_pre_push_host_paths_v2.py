from __future__ import annotations

import unittest

from scripts.scan_pre_push_host_paths_v2 import GENERIC_HOME, HISTORICAL_SUFFIX


class PrePushHostPathScannerV2Tests(unittest.TestCase):
    def test_generic_windows_home_is_detected(self) -> None:
        value = b"X:" + b"/" + b"Users/example/private/place"
        self.assertIsNotNone(GENERIC_HOME.search(value))

    def test_generic_posix_home_is_detected(self) -> None:
        value = b"/" + b"home/example/private/place"
        self.assertIsNotNone(GENERIC_HOME.search(value))

    def test_logical_placeholders_are_not_paths(self) -> None:
        for value in (b"<LOCAL_RESEARCH_ROOT>", b"<BUNDLED_PYTHON>", b"<HAI_DATA_ROOT>"):
            self.assertIsNone(GENERIC_HOME.search(value))

    def test_historical_runtime_suffix_is_detected(self) -> None:
        suffix = b"/" + b".cache/codex-runtimes/runtime/python"
        self.assertIsNotNone(HISTORICAL_SUFFIX.match(suffix))

    def test_historical_workspace_suffix_is_detected(self) -> None:
        suffix = b"/" + b"Desktop/paperworks/260625/src"
        self.assertIsNotNone(HISTORICAL_SUFFIX.match(suffix))


if __name__ == "__main__":
    unittest.main()
