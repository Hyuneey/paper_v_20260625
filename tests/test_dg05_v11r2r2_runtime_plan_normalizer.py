from __future__ import annotations

import unittest

from paperworks.validation_v2.dg05_execution_closure_v1 import digest
from paperworks.validation_v2.dg05_v11r2r2_runtime_plan_normalizer import (
    DG05V11R2R2RuntimePlanOrderError,
    canonical_runtime_plan_identities_v11r2r2,
    normalize_runtime_plan_to_frozen_panel_order_v11r2r2,
    verify_runtime_plan_canonical_order_v11r2r2,
)
from paperworks.validation_v2.multipanel_custody_v1 import (
    FROZEN_ATTACK_FILE_CENSUS_HASH_V2,
    FROZEN_AUTHORITY_SOURCE_COMMIT_V2,
    FrozenPhysicalFileAuthorityV2,
    MultiPanelCustodyError,
    PhysicalFileIdentityV2,
)
from paperworks.validation_v2.dg05_production_chain_v11 import self_hashed


def plan(rows):
    return self_hashed({
        "schema": "dg05_v11r1_protected_resource_plan_v1",
        "classification": "PRIVATE_RUNTIME_MATERIALIZATION_NOT_SCIENTIFIC_AUTHORITY_NOT_USER_APPROVAL_TARGET",
        "physical_custody_hash": "c" * 64,
        "files": rows,
    })


def rows():
    # This mirrors the old lexical materializer order, without any source I/O.
    return [
        {"panel_id": panel, "file_id": file_id, "sha256": digest((panel, file_id)), "size": 1,
         "repository_relative_path": f"synthetic/{panel}/{file_id}", "path": f"synthetic/{panel}/{file_id}",
         "container_type": "IDENTITY", "classification": "PRIVATE_RUNTIME_LOCATOR"}
        for panel, file_id in sorted(canonical_runtime_plan_identities_v11r2r2())
    ]


class RuntimePlanNormalizerTests(unittest.TestCase):
    def test_historical_lexical_order_reproduces_physical_authority_failure(self):
        lexical = rows()
        physical = FrozenPhysicalFileAuthorityV2(
            tuple(PhysicalFileIdentityV2(r["panel_id"], r["file_id"], r["sha256"], "a" * 64, "b" * 64) for r in lexical),
            FROZEN_ATTACK_FILE_CENSUS_HASH_V2, "c" * 64, FROZEN_AUTHORITY_SOURCE_COMMIT_V2,
        )
        with self.assertRaises(MultiPanelCustodyError):
            physical.validate()

    def test_normalization_is_identity_preserving_and_canonical(self):
        normalized, receipt = normalize_runtime_plan_to_frozen_panel_order_v11r2r2(verified_plan=plan(rows()))
        self.assertEqual(tuple((r["panel_id"], r["file_id"]) for r in normalized["files"]), canonical_runtime_plan_identities_v11r2r2())
        self.assertEqual(receipt["unordered_identity_set_hash_before"], receipt["unordered_identity_set_hash_after"])
        self.assertEqual(receipt["status"], "PASS_CANONICAL_FROZEN_PANEL_ORDER")
        self.assertEqual(verify_runtime_plan_canonical_order_v11r2r2(plan=normalized)["status"], receipt["status"])
        twice, _ = normalize_runtime_plan_to_frozen_panel_order_v11r2r2(verified_plan=normalized)
        self.assertEqual(twice, normalized)
        physical = FrozenPhysicalFileAuthorityV2(
            tuple(PhysicalFileIdentityV2(r["panel_id"], r["file_id"], r["sha256"], "a" * 64, "b" * 64) for r in normalized["files"]),
            FROZEN_ATTACK_FILE_CENSUS_HASH_V2, "c" * 64, FROZEN_AUTHORITY_SOURCE_COMMIT_V2,
        )
        physical.validate()

    def test_bad_identity_is_rejected(self):
        mutated = rows(); mutated[-1] = {**mutated[-1], "file_id": "unknown.csv"}
        with self.assertRaises(DG05V11R2R2RuntimePlanOrderError):
            normalize_runtime_plan_to_frozen_panel_order_v11r2r2(verified_plan=plan(mutated))
