from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path
import subprocess
import unittest

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.relation_profiling_protocol_v1 import FROZEN_SOURCES, SOURCE_IDENTITY_HASH
from paperworks.v6.task039e3_r2r_utility_protocol_v2 import (
    HISTORICAL_SOURCE_IDENTITY_HASH,
    UTILITY_SOURCE_UNIVERSE_V2,
    UtilityProtocolV2Error,
    is_event_isolated_v2,
    logical_to_physical_v2,
    physical_to_logical_v2,
)


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs/task_reports"


def _json(name: str) -> dict[str, object]:
    value = json.loads((REPORTS / name).read_text(encoding="utf-8"))
    observed = value["artifact_hash"]
    payload = {key: item for key, item in value.items() if key != "artifact_hash"}
    if stable_hash_v1(payload) != observed:
        raise AssertionError(f"{name} self-hash differs")
    return value


def _blob(path: str) -> str:
    return subprocess.check_output(["git", "hash-object", path], cwd=ROOT, text=True).strip()


def _raw_sha(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def _events(offset: int | None = None) -> dict[str, tuple[int, ...]]:
    value = {source: () for source in UTILITY_SOURCE_UNIVERSE_V2}
    value[UTILITY_SOURCE_UNIVERSE_V2[0]] = (10,)
    if offset is not None:
        value[UTILITY_SOURCE_UNIVERSE_V2[1]] = (10 + offset,)
    return value


class IndependentPublicAuthorityReauditTests(unittest.TestCase):
    def test_coordinate_formula_endpoints_and_roundtrips(self) -> None:
        expected = {
            ("hai-test1.csv", 0): 0,
            ("hai-test1.csv", 53_999): 53_999,
            ("hai-test2.csv", 54_120): 0,
            ("hai-test2.csv", 284_519): 230_399,
        }
        for (file_name, logical), physical in expected.items():
            self.assertEqual(logical_to_physical_v2(file_name, logical), physical)
            self.assertEqual(physical_to_logical_v2(file_name, physical), logical)

    def test_virtual_purge_and_invalid_coordinates_fail_closed(self) -> None:
        coordinate = _json("TASK-039E3_R2R_UTILITY_PROTOCOL_REMEDIATION_COORDINATE_BINDING.json")
        self.assertEqual(coordinate["purge"]["logical_range"], [54_000, 54_120])
        self.assertTrue(coordinate["purge"]["virtual_non_observation"])
        for key in (
            "maps_to_physical_row", "maps_to_feature_row", "maps_to_label_row",
            "included_in_attack_events", "included_in_normal_exposure",
            "included_in_metric_denominator", "eligible_for_interpreter",
        ):
            self.assertFalse(coordinate["purge"][key])
        for index in (54_000, 54_001, 54_119):
            with self.assertRaises(UtilityProtocolV2Error):
                logical_to_physical_v2("hai-test2.csv", index)
        for invalid in (-1, 284_520, True, 54_120.0, "54120"):
            with self.assertRaises(UtilityProtocolV2Error):
                logical_to_physical_v2("hai-test2.csv", invalid)  # type: ignore[arg-type]
        for invalid in (230_400, True, 0.0, "0"):
            with self.assertRaises(UtilityProtocolV2Error):
                physical_to_logical_v2("hai-test2.csv", invalid)  # type: ignore[arg-type]
        with self.assertRaises(UtilityProtocolV2Error):
            logical_to_physical_v2("unknown.csv", 0)

    def test_exact_historical_12_source_authority_and_isolation(self) -> None:
        self.assertEqual(tuple(FROZEN_SOURCES), UTILITY_SOURCE_UNIVERSE_V2)
        self.assertEqual(len(UTILITY_SOURCE_UNIVERSE_V2), 12)
        self.assertEqual(SOURCE_IDENTITY_HASH, HISTORICAL_SOURCE_IDENTITY_HASH)
        self.assertNotIn("required_sources", inspect.signature(is_event_isolated_v2).parameters)
        for offset in (-2, -1, 0, 1, 2):
            self.assertFalse(is_event_isolated_v2(UTILITY_SOURCE_UNIVERSE_V2[0], 10, _events(offset)))
        for offset in (-3, 3):
            self.assertTrue(is_event_isolated_v2(UTILITY_SOURCE_UNIVERSE_V2[0], 10, _events(offset)))
        for changed in ("missing", "extra"):
            value = _events()
            if changed == "missing":
                value.pop(UTILITY_SOURCE_UNIVERSE_V2[-1])
            else:
                value["UNBOUND"] = ()
            with self.assertRaises(UtilityProtocolV2Error):
                is_event_isolated_v2(UTILITY_SOURCE_UNIVERSE_V2[0], 10, value)

    def test_canonical_v2_and_source_freeze_exact(self) -> None:
        canonical = _json("TASK-039E3_R2R_UTILITY_PROTOCOL_CANONICAL_AUTHORITY_V2.json")
        freeze = _json("TASK-039E3_R2R_UTILITY_PROTOCOL_REMEDIATION_SOURCE_FREEZE.json")
        self.assertEqual(canonical["artifact_hash"], "9e23c16e7c85f825e19dd30da96a17b88e3daf06763eb98c3bdba86bea189d44")
        self.assertEqual(canonical["canonical_protocol"], "BASE_V1_PLUS_REMEDIATION_V2")
        self.assertEqual(freeze["artifact_hash"], "6ed4f60018993c378e2388565d00a33f189f74d86fc5017468f9a30e6b4a1726")
        self.assertEqual(len(freeze["records"]), 4)
        for record in freeze["records"]:
            self.assertEqual(_blob(record["path"]), record["git_blob"])
            self.assertEqual(_raw_sha(record["path"]), record["raw_byte_sha256"])

    def test_original_v1_is_byte_immutable(self) -> None:
        path = "src/paperworks/v6/task039e3_r2r_utility_protocol_v1.py"
        self.assertEqual(_blob(path), "2e6960c6838519310b71df417b4fb4824f4a4f92")
        self.assertEqual(_raw_sha(path), "56305eced40020b00e29783fa9d795f3a352b230e584ffed0ae5465f1f1a5165")


if __name__ == "__main__":
    unittest.main()
