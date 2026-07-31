from __future__ import annotations

import unittest

from paperworks.gdn.fidelity_v1 import (
    GDNBackendFidelityRecordV1,
    GDNFidelityClassV1,
    GDNFidelityError,
    GDNFidelityFreezeV1,
)
from tests.task039p1d_support import make_fidelity_freeze, make_fidelity_records


class Task039P1DFidelityRecordTests(unittest.TestCase):
    def test_three_frozen_records_have_required_claim_ceilings(self) -> None:
        records = make_fidelity_records()
        self.assertEqual(len(records), 3)
        by_id = {record.backend_id: record for record in records}
        self.assertEqual(
            by_id["deterministic_embedding_smoke"].fidelity_class,
            GDNFidelityClassV1.SYNTHETIC_SMOKE_ONLY,
        )
        self.assertEqual(
            by_id["torch_pyg_cpu_smoke"].fidelity_class,
            GDNFidelityClassV1.SYNTHETIC_SMOKE_ONLY,
        )
        self.assertEqual(
            by_id["masked_candidate_extraction"].fidelity_class,
            GDNFidelityClassV1.PROJECT_OWNED_EXTRACTION_COMPONENT,
        )
        for record in records:
            self.assertFalse(record.scientific_gdn_claim_allowed)
            self.assertFalse(record.production_candidate_ranking_allowed)
            self.assertFalse(record.data_accessed)
            self.assertFalse(record.model_trained)
            self.assertEqual(
                record,
                GDNBackendFidelityRecordV1.from_dict(record.to_dict()),
            )

    def test_unvalidated_record_cannot_grant_scientific_or_production_use(
        self,
    ) -> None:
        base = make_fidelity_records()[1].to_dict()
        base.pop("artifact_hash")
        base["scientific_gdn_claim_allowed"] = True
        with self.assertRaises(GDNFidelityError):
            GDNBackendFidelityRecordV1.from_dict(base)

    def test_freeze_is_deterministic_and_contains_no_validated_backend(self) -> None:
        first = make_fidelity_freeze()
        second = make_fidelity_freeze()
        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertEqual(first, GDNFidelityFreezeV1.from_dict(first.to_dict()))
        self.assertEqual(
            first.required_rq1_fidelity_class,
            "upstream_aligned_validated",
        )
        self.assertNotIn(
            GDNFidelityClassV1.UPSTREAM_ALIGNED_VALIDATED,
            {record.fidelity_class for record in first.backend_records},
        )


if __name__ == "__main__":
    unittest.main()
