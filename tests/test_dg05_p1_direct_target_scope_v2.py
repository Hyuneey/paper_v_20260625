from __future__ import annotations

from copy import deepcopy
import unittest

from paperworks.validation_v2.dg05_p1_direct_target_scope_v2 import (
    MANUAL_HASH,
    DECISION_HASH,
    P1DirectTargetScopeV2Error,
    build_scope_authority,
    build_target_process_authority,
    classify_scenario_targets,
    self_hashed,
    validate_target_process_authority,
)


DECISION = DECISION_HASH


class P1DirectTargetScopeV2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.target = "OFFICIAL_INTERNAL_TARGET"
        self.authority = build_target_process_authority(
            raw_targets=["P1_CANONICAL", self.target],
            canonical_hai23_identities=["P1_CANONICAL"],
            target_controllers={"P1_CANONICAL": ["OFFICIAL_CONTROLLER"], self.target: ["OFFICIAL_CONTROLLER"]},
            decision_hash=DECISION,
            source_commit="2a814cebc9a66b06c9e5cd545e2d72e65d383737",
        )
        self.scope = build_scope_authority(decision_hash=DECISION, target_process_authority_hash=self.authority["self_hash"])

    def test_internal_target_is_not_forced_to_feature_alias(self) -> None:
        record = next(item for item in self.authority["records"] if item["canonical_hai_feature_identity"] is None)
        self.assertEqual(record["target_namespace"], "OTHER_OFFICIAL_HAI_TARGET_IDENTITY")
        self.assertIsNone(record["canonical_hai_feature_identity"])
        self.assertFalse(record["heuristic_alias"])

    def test_any_verified_p1_preserves_unknown_handling(self) -> None:
        self.assertEqual(classify_scenario_targets(["UNKNOWN", self.target], self.authority, self.scope), "P1_ELIGIBLE")
        self.assertEqual(classify_scenario_targets(["UNKNOWN"], self.authority, self.scope), "UNRESOLVED")

    def test_noncanonical_alias_and_source_mutations_fail(self) -> None:
        alias = deepcopy(self.authority)
        target_record = next(item for item in alias["records"] if item["canonical_hai_feature_identity"] is None)
        target_record["canonical_hai_feature_identity"] = "P1_CANONICAL"
        target_record["record_hash"] = "0" * 64
        alias = self_hashed(alias)
        with self.assertRaises(P1DirectTargetScopeV2Error):
            validate_target_process_authority(alias)

        source = deepcopy(self.authority)
        source["records"][0]["source_sha256"] = "b" * 64
        source["records"][0]["record_hash"] = "0" * 64
        source = self_hashed(source)
        with self.assertRaises(P1DirectTargetScopeV2Error):
            validate_target_process_authority(source)
        self.assertEqual(MANUAL_HASH, "0668345c4e80331b918fe17c81f8f363b13bd22886831d286e761bc62b71a556")


if __name__ == "__main__":
    unittest.main()
