from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

from paperworks.validation_v2.dg05_execution_closure_v1 import FROZEN_FULL_SCOPE_PROCESS_MAP_V1


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "research_control_center" / "validation_v2" / "dg05_v11_source_adapter_lfs_closure" / "HAI23_TARGET_NAMESPACE_P1_SCOPE_AMENDMENT_BLOCKER_RECEIPT_V1.json"


def canonical_digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


class HAI23TargetNamespaceP1BlockerV1Tests(unittest.TestCase):
    def test_public_receipt_replays_and_does_not_expose_raw_targets(self) -> None:
        value = json.loads(RECEIPT.read_text(encoding="utf-8"))
        self.assertEqual(value["self_hash"], canonical_digest({key: item for key, item in value.items() if key != "self_hash"}))
        self.assertEqual(value["verdict"], "P1_SCOPE_REQUIRES_PROSPECTIVE_SOURCE_AMENDMENT")
        self.assertFalse(value["private_target_namespace_worksheet"]["raw_values_publicly_exposed"])
        self.assertEqual(value["private_target_namespace_worksheet"]["unresolved_representation_count"], 14)

    def test_frozen_p1_scope_is_a_finite_exact_hai23_identity_set(self) -> None:
        scope = FROZEN_FULL_SCOPE_PROCESS_MAP_V1["23.05"]
        identities = {identity for values in scope.values() for identity in values}
        self.assertEqual(len(identities), 86)
        self.assertEqual(len(scope["P1"]), 44)
        self.assertNotIn("NONCANONICAL_OFFICIAL_DIRECT_TARGET", identities)


if __name__ == "__main__":
    unittest.main()
