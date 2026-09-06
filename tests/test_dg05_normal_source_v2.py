from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from paperworks.validation_v2.dg05_normal_source_v2 import (
    DG05NormalSourceError,
    build_normal_source_bundle_v2,
    build_normal_source_registry_v2,
    persist_normal_source_bundle_v2,
    replay_normal_source_registry_v2,
)
from paperworks.validation_v2.dg05_production_chain_v1 import digest_v1


H = "a" * 64
G = "b" * 40
BINDING = "c" * 64


def _timestamps() -> list[str]:
    return [f"2026-09-06T00:00:0{i}" for i in range(6)]


def _rule_trace() -> dict:
    return {
        "opportunities": 2,
        "pass": 1,
        "fail": 1,
        "abstain": 0,
        "system_errors": 0,
        "evaluation_invocations": 2,
        "evaluated_system_errors": 0,
        "rule_alarm_rows": [2],
        "fail_sources_by_row": {"2": ["S0"]},
        "per_rule_runtime": [
            {
                "rule_id": "R0", "source_id": "S0", "opportunities": 2,
                "pass": 1, "fail": 1, "abstain": 0, "system_errors": 0,
                "evaluation_invocations": 2, "evaluated_system_errors": 0,
                "fail_rows": [2],
            },
            {
                "rule_id": "R1", "source_id": "S1", "opportunities": 0,
                "pass": 0, "fail": 0, "abstain": 0, "system_errors": 0,
                "evaluation_invocations": 0, "evaluated_system_errors": 0,
                "fail_rows": [],
            },
        ],
    }


class NormalSourceV2Tests(unittest.TestCase):
    def _bundle(self, *, method: str = "M1_T0_RULE_ONLY", alarms: list[bool] | None = None) -> dict:
        is_rule = method != "M0_PCA_SPE"
        return build_normal_source_bundle_v2(
            component_id=f"P|{method}|F",
            panel_id="P",
            dataset_version="X",
            method_id=method,
            file_id="F",
            component_role="GUARD",
            authority_class="GUARD_CONDITIONED_NORMAL",
            method_authority_hash=H,
            physical_file_authority_hash=H,
            projection_authority_hash=H,
            timestamps=_timestamps(),
            alarms=alarms if alarms is not None else [False, False, True, False, False, False],
            configured_rule_sources={"R0": "S0", "R1": "S1"} if is_rule else None,
            runtime_trace=_rule_trace() if is_rule else None,
            source_commit=G,
        )

    def _registry(self, receipt: dict, bundle: dict) -> dict:
        return build_normal_source_registry_v2(
            component_receipts=[receipt],
            component_metadata=[{
                "component_id": bundle["component_id"],
                "panel_id": bundle["panel_id"],
                "dataset_version": bundle["dataset_version"],
                "method_id": bundle["method_id"],
                "file_id": bundle["file_id"],
                "component_role": bundle["component_role"],
                "authority_class": bundle["authority_class"],
                "method_authority_hash": bundle["method_authority_hash"],
                "physical_file_authority_hash": bundle["physical_file_authority_hash"],
                "projection_authority_hash": bundle["projection_authority_hash"],
                "timeline_authority_hash": bundle["timeline_authority"]["self_hash"],
            }],
            dec031_binding_hash=BINDING,
            required_components=[{
                "component_id": bundle["component_id"],
                "panel_id": bundle["panel_id"],
                "dataset_version": bundle["dataset_version"],
                "method_id": bundle["method_id"],
                "file_id": bundle["file_id"],
                "component_role": bundle["component_role"],
                "authority_class": bundle["authority_class"],
            }],
            source_commit=G,
        )

    def _registry_many(self, rows: list[tuple[dict, dict]]) -> dict:
        metadata = []
        required = []
        for _, bundle in rows:
            item = {
                "component_id": bundle["component_id"], "panel_id": bundle["panel_id"],
                "dataset_version": bundle["dataset_version"], "method_id": bundle["method_id"],
                "file_id": bundle["file_id"], "component_role": bundle["component_role"],
                "authority_class": bundle["authority_class"],
            }
            required.append(dict(item))
            metadata.append({**item,
                "method_authority_hash": bundle["method_authority_hash"],
                "physical_file_authority_hash": bundle["physical_file_authority_hash"],
                "projection_authority_hash": bundle["projection_authority_hash"],
                "timeline_authority_hash": bundle["timeline_authority"]["self_hash"],
            })
        return build_normal_source_registry_v2(
            component_receipts=[receipt for receipt, _ in rows], component_metadata=metadata,
            dec031_binding_hash=BINDING, required_components=required, source_commit=G)

    def test_persist_and_independently_replay_source_bytes(self) -> None:
        with TemporaryDirectory() as raw:
            path = Path(raw) / "source.json"
            bundle = self._bundle()
            receipt = persist_normal_source_bundle_v2(path, bundle)
            registry = self._registry(receipt, bundle)
            result = replay_normal_source_registry_v2(
                registry=registry,
                component_paths={bundle["component_id"]: path},
                expected_dec031_binding_hash=BINDING,
            )
            method = result["methods"][0]
            self.assertEqual(method["false_seconds"], 1)
            self.assertEqual(method["false_episodes"], 1)
            self.assertFalse(result["caller_supplied_burden_values"])
            census = method["components"][0]["runtime_census"]
            self.assertEqual(census["configured_rule_count"], 2)
            self.assertEqual(census["formed_rule_count"], 1)

    def test_missing_runtime_is_not_zero(self) -> None:
        with self.assertRaisesRegex(DG05NormalSourceError, "EVIDENCE_MISSING"):
            build_normal_source_bundle_v2(
                component_id="C", panel_id="P", dataset_version="X",
                method_id="M1_T0_RULE_ONLY", file_id="F", component_role="GUARD",
                authority_class="GUARD_CONDITIONED_NORMAL", method_authority_hash=H,
                physical_file_authority_hash=H, projection_authority_hash=H,
                timestamps=_timestamps(), alarms=[False] * 6,
                configured_rule_sources=None, runtime_trace=None, source_commit=G,
            )

    def test_caller_decimal_and_source_mutation_rejected(self) -> None:
        with TemporaryDirectory() as raw:
            path = Path(raw) / "source.json"
            bundle = self._bundle()
            receipt = persist_normal_source_bundle_v2(path, bundle)
            registry = self._registry(receipt, bundle)
            registry["false_seconds_per_hour"] = 0.0
            with self.assertRaisesRegex(DG05NormalSourceError, "REGISTRY_REQUIRED"):
                replay_normal_source_registry_v2(
                    registry=registry,
                    component_paths={bundle["component_id"]: path},
                    expected_dec031_binding_hash=BINDING,
                )
            registry.pop("false_seconds_per_hour")
            # Restore registry self-hash is intentionally omitted: a coherent
            # caller-side summary edit must not become source evidence.
            value = json.loads(path.read_text(encoding="ascii"))
            value["alarms"][0] = True
            value["self_hash"] = value["self_hash"]  # byte hash still changes
            path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n", encoding="ascii")
            with self.assertRaisesRegex(DG05NormalSourceError, "BYTE_HASH"):
                replay_normal_source_registry_v2(
                    registry=self._registry(receipt, bundle),
                    component_paths={bundle["component_id"]: path},
                    expected_dec031_binding_hash=BINDING,
                )

    def test_method_authority_and_train_component_swap_rejected(self) -> None:
        with TemporaryDirectory() as raw:
            path = Path(raw) / "source.json"
            bundle = self._bundle(method="M0_PCA_SPE", alarms=[False] * 6)
            receipt = persist_normal_source_bundle_v2(path, bundle)
            registry = self._registry(receipt, bundle)
            registry["components"][0]["method_authority_hash"] = "d" * 64
            registry["self_hash"] = digest_v1({k: v for k, v in registry.items() if k != "self_hash"})
            with self.assertRaisesRegex(DG05NormalSourceError, "method_authority_hash"):
                replay_normal_source_registry_v2(
                    registry=registry,
                    component_paths={bundle["component_id"]: path},
                    expected_dec031_binding_hash=BINDING,
                )

    def test_exposure_mutation_and_cross_method_component_swaps_rejected(self) -> None:
        with TemporaryDirectory() as raw:
            root = Path(raw)
            t0 = self._bundle(method="M1_T0_RULE_ONLY")
            t2 = self._bundle(method="M2_T2_RULE_ONLY")
            t0["component_id"] = "P|M1_T0_RULE_ONLY|F"
            t0["self_hash"] = digest_v1({k: v for k, v in t0.items() if k != "self_hash"})
            t2["component_id"] = "P|M2_T2_RULE_ONLY|F"
            t2["self_hash"] = digest_v1({k: v for k, v in t2.items() if k != "self_hash"})
            t0_path, t2_path = root / "t0.json", root / "t2.json"
            t0_receipt = persist_normal_source_bundle_v2(t0_path, t0)
            t2_receipt = persist_normal_source_bundle_v2(t2_path, t2)
            registry = self._registry_many([(t0_receipt, t0), (t2_receipt, t2)])
            with self.assertRaisesRegex(DG05NormalSourceError, "BYTE_HASH"):
                replay_normal_source_registry_v2(
                    registry=registry,
                    component_paths={t0["component_id"]: t2_path, t2["component_id"]: t0_path},
                    expected_dec031_binding_hash=BINDING)

            changed = json.loads(t0_path.read_text(encoding="ascii"))
            changed["exposure_seconds"] += 1
            changed["self_hash"] = digest_v1({k: v for k, v in changed.items() if k != "self_hash"})
            t0_path.write_text(json.dumps(changed, sort_keys=True, separators=(",", ":")) + "\n", encoding="ascii")
            with self.assertRaisesRegex(DG05NormalSourceError, "BYTE_HASH"):
                replay_normal_source_registry_v2(
                    registry=registry,
                    component_paths={t0["component_id"]: t0_path, t2["component_id"]: t2_path},
                    expected_dec031_binding_hash=BINDING)

    def test_hai22_train_role_swap_is_rejected(self) -> None:
        with TemporaryDirectory() as raw:
            root = Path(raw)
            rows = []
            paths = {}
            for role in ("POST_FREEZE_TRAIN5_ROBUSTNESS", "POST_FREEZE_TRAIN6_STABILITY"):
                bundle = build_normal_source_bundle_v2(
                    component_id=f"P|M0|{role}", panel_id="P", dataset_version="22.04",
                    method_id="M0_PCA_SPE", file_id=role, component_role=role,
                    authority_class="POST_FREEZE_NORMAL_AUDIT", method_authority_hash=H,
                    physical_file_authority_hash=H, projection_authority_hash=H,
                    timestamps=_timestamps(), alarms=[False] * 6,
                    configured_rule_sources=None, runtime_trace=None, source_commit=G)
                path = root / f"{role}.json"
                receipt = persist_normal_source_bundle_v2(path, bundle)
                rows.append((receipt, bundle)); paths[bundle["component_id"]] = path
            registry = self._registry_many(rows)
            ids = [bundle["component_id"] for _, bundle in rows]
            with self.assertRaisesRegex(DG05NormalSourceError, "BYTE_HASH"):
                replay_normal_source_registry_v2(
                    registry=registry, component_paths={ids[0]: paths[ids[1]], ids[1]: paths[ids[0]]},
                    expected_dec031_binding_hash=BINDING)

    def test_exact_component_roster_rejects_omission_and_duplicate(self) -> None:
        with TemporaryDirectory() as raw:
            path = Path(raw) / "source.json"
            bundle = self._bundle(method="M0_PCA_SPE", alarms=[False] * 6)
            receipt = persist_normal_source_bundle_v2(path, bundle)
            with self.assertRaisesRegex(DG05NormalSourceError, "COMPONENT_ROSTER"):
                build_normal_source_registry_v2(
                    component_receipts=[receipt],
                    component_metadata=[{
                        "component_id": bundle["component_id"], "panel_id": "P",
                        "dataset_version": "X", "method_id": "M0_PCA_SPE", "file_id": "F",
                        "component_role": "GUARD", "authority_class": "GUARD_CONDITIONED_NORMAL",
                        "method_authority_hash": H, "physical_file_authority_hash": H,
                        "projection_authority_hash": H,
                        "timeline_authority_hash": bundle["timeline_authority"]["self_hash"],
                    }],
                    required_components=[], dec031_binding_hash=BINDING, source_commit=G,
                )

    def test_fusion_is_reconstructed_from_base_and_distinct_sources(self) -> None:
        trace = _rule_trace()
        trace["per_rule_runtime"][1].update({
            "opportunities": 1, "fail": 1, "evaluation_invocations": 1,
            "fail_rows": [2],
        })
        trace.update({
            "opportunities": 3, "fail": 2, "evaluation_invocations": 3,
            "rule_alarm_rows": [2], "rule_component_alarm_rows": [2],
            "fail_sources_by_row": {"2": ["S0", "S1"]},
            "fusion_base_alarm_rows": [4], "fusion_output_alarm_rows": [2, 4],
        })
        bundle = build_normal_source_bundle_v2(
            component_id="FUSION", panel_id="P", dataset_version="X",
            method_id="M3_PCA_PLUS_T0", file_id="F", component_role="GUARD",
            authority_class="GUARD_CONDITIONED_NORMAL", method_authority_hash=H,
            physical_file_authority_hash=H, projection_authority_hash=H,
            timestamps=_timestamps(), alarms=[False, False, True, False, True, False],
            configured_rule_sources={"R0": "S0", "R1": "S1"},
            runtime_trace=trace, source_commit=G,
        )
        with TemporaryDirectory() as raw:
            root = Path(raw)
            fusion_path = root / "fusion.json"
            fusion_receipt = persist_normal_source_bundle_v2(fusion_path, bundle)
            rule = self._bundle(method="M1_T0_RULE_ONLY")
            rule_path = root / "rule.json"
            rule_receipt = persist_normal_source_bundle_v2(rule_path, rule)
            registry = self._registry_many([(fusion_receipt, bundle), (rule_receipt, rule)])
            with self.assertRaisesRegex(DG05NormalSourceError, "BYTE_HASH"):
                replay_normal_source_registry_v2(
                    registry=registry,
                    component_paths={bundle["component_id"]: rule_path, rule["component_id"]: fusion_path},
                    expected_dec031_binding_hash=BINDING)
        forged = _rule_trace()
        forged.update({
            "rule_alarm_rows": [2], "rule_component_alarm_rows": [2],
            "fail_sources_by_row": {"2": ["S0", "S1"]},
            "fusion_base_alarm_rows": [4], "fusion_output_alarm_rows": [2, 4],
        })
        bad = build_normal_source_bundle_v2(
            component_id="BAD", panel_id="P", dataset_version="X",
            method_id="M3_PCA_PLUS_T0", file_id="F", component_role="GUARD",
            authority_class="GUARD_CONDITIONED_NORMAL", method_authority_hash=H,
            physical_file_authority_hash=H, projection_authority_hash=H,
            timestamps=_timestamps(), alarms=[False, False, True, False, True, False],
            configured_rule_sources={"R0": "S0", "R1": "S1"},
            runtime_trace=forged, source_commit=G,
        )
        with TemporaryDirectory() as raw:
            with self.assertRaisesRegex(DG05NormalSourceError, "SOURCE_RECONSTRUCTION"):
                persist_normal_source_bundle_v2(Path(raw) / "bad.json", bad)


if __name__ == "__main__":
    unittest.main()
