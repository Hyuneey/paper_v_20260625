from __future__ import annotations

import json
import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path

from paperworks.candidates.gdn_candidate_discovery_v1 import (
    GDNCandidateDiscoveryError,
    GDNCandidateResultV1,
    GDNSeedGraphRecordV1,
    aggregate_and_rank_gdn_candidates_v1,
)
from paperworks.gdn.gdn_remediation_environment_v1 import (
    FIDELITY_RECEIPT_HASH,
    PHASE_A_COMMIT,
    derive_frozen_p1_feature_order_from_headers_v1,
    enrich_passing_gdn_result_v1,
)
from paperworks.gdn.upstream_candidate_backend_v1 import (
    FROZEN_SEEDS,
    UpstreamGDNDataBoundaryError,
    UpstreamGDNTrainingConfigV1,
    authorize_gdn_data_request_v1,
)
from paperworks.v6.candidate_discovery_protocol_v1 import (
    derive_candidate_budget_views_v1,
)
from paperworks.v6.common import stable_hash_v1


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_task039c_gdn_remediation.py"
HASH = "a" * 64


def universe() -> tuple[tuple[str, str], ...]:
    return tuple(
        (f"S{source:02d}", f"T{target:02d}")
        for source in range(12)
        for target in range(12)
    )


def seed_record(seed: int, selected=()) -> GDNSeedGraphRecordV1:
    pairs = universe()
    return GDNSeedGraphRecordV1(
        seed=seed,
        successful=True,
        selected_edges=tuple(selected),
        candidate_similarities={pair: 0.25 for pair in pairs},
        hyperparameter_hash=HASH,
        epoch_count=2,
        best_validation_loss=0.1,
    )


def passing_result() -> dict:
    selected = (("S00", "T00"),)
    records = tuple(seed_record(seed, selected) for seed in FROZEN_SEEDS)
    ranking = aggregate_and_rank_gdn_candidates_v1(
        universe_pairs=universe(), seed_records=records
    )
    base = GDNCandidateResultV1(
        status="passed_task039c_gdn_candidate_discovery",
        phase_a_commit=PHASE_A_COMMIT,
        fidelity_receipt_hash=FIDELITY_RECEIPT_HASH,
        dependency_environment_fingerprint="b" * 64,
        backend_classification="upstream_aligned_validated",
        source_count=12,
        target_count=12,
        real_hai_feature_access=True,
        seeds_attempted=FROZEN_SEEDS,
        seeds_completed=FROZEN_SEEDS,
        br2_pair_supervision_used=False,
        train3_accessed=False,
        train4_accessed=False,
        test_accessed=False,
        attention_used_for_primary_ranking=False,
        posthoc_xai_used=False,
        created_at="2026-08-10T00:00:00+00:00",
        ranking=ranking,
        seed_records=records,
    )
    return enrich_passing_gdn_result_v1(
        base_result=base.to_dict(),
        environment_receipt_hash="c" * 64,
        remediation_execution_commit="d" * 40,
        private_seed_ledger_hashes=(
            {"seed": 11, "ledger_hash": "1" * 64},
            {"seed": 23, "ledger_hash": "2" * 64},
            {"seed": 37, "ledger_hash": "3" * 64},
        ),
        data_access_audit_ref="TASK-039C_GDNR_DATA_ACCESS_AUDIT.json",
    )


class Task039CGDNRemediationExecutionTests(unittest.TestCase):
    def test_exact_seed_set_and_frozen_hyperparameters(self) -> None:
        config = UpstreamGDNTrainingConfigV1()
        self.assertEqual(config.seeds, (11, 23, 37))
        self.assertEqual(config.learned_graph_topk, 5)
        self.assertEqual(config.epochs, 30)
        self.assertEqual(config.early_stopping_patience, 15)
        self.assertEqual(config.device, "cpu")

    def test_failed_seed_prevents_ranking(self) -> None:
        failed = GDNSeedGraphRecordV1(
            seed=37,
            successful=False,
            selected_edges=(),
            candidate_similarities={},
            hyperparameter_hash=HASH,
            failure_reason="synthetic failure",
        )
        with self.assertRaisesRegex(GDNCandidateDiscoveryError, "fail closed"):
            aggregate_and_rank_gdn_candidates_v1(
                universe_pairs=universe(),
                seed_records=(seed_record(11), seed_record(23), failed),
            )

    def test_frequency_denominator_is_three(self) -> None:
        pair = ("S00", "T00")
        ranking = aggregate_and_rank_gdn_candidates_v1(
            universe_pairs=universe(),
            seed_records=(seed_record(11, (pair,)), seed_record(23), seed_record(37)),
        )
        self.assertEqual(ranking[0].selected_seed_count, 1)
        self.assertEqual(ranking[0].edge_selection_frequency, 1.0 / 3.0)

    def test_topk_views_are_prefixes_of_one_ranking(self) -> None:
        selected = tuple(universe()[:30])
        ranking = aggregate_and_rank_gdn_candidates_v1(
            universe_pairs=universe(),
            seed_records=tuple(seed_record(seed, selected) for seed in FROZEN_SEEDS),
        )
        identities = tuple((item.source, item.target) for item in ranking)
        views = derive_candidate_budget_views_v1(identities)
        self.assertEqual(views.top10, identities[:10])
        self.assertEqual(views.top20, identities[:20])
        self.assertEqual(views.top40, identities[:30])
        self.assertEqual(dict(views.candidate_shortfall), {10: 0, 20: 0, 40: 10})

    def test_passing_result_hash_is_deterministic(self) -> None:
        first = passing_result()
        second = passing_result()
        self.assertEqual(first, second)
        observed = first.pop("artifact_hash")
        self.assertEqual(stable_hash_v1(first), observed)

    def test_header_bound_view_is_file_local_and_hash_verified(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = root / "hai-23.05"
            data.mkdir()
            features = ("P1_A", "P1_B", "P1_C")
            expected_hash = stable_hash_v1({"features": list(features)})
            for name in ("hai-train1.csv", "hai-train2.csv"):
                (data / name).write_text(
                    "Timestamp," + ",".join(features) + ",attack\n",
                    encoding="utf-8",
                )
            observed = derive_frozen_p1_feature_order_from_headers_v1(
                data_root=root,
                expected_feature_order_hash=expected_hash,
            )
            self.assertEqual(observed, features)

    def test_train3_train4_test_meta_stat_and_br2_are_rejected(self) -> None:
        for prohibited in (
            "hai-23.05/hai-train3.csv",
            "hai-23.05/hai-train4.csv",
            "hai-23.05/hai-test1.csv",
        ):
            with self.subTest(prohibited=prohibited):
                with self.assertRaises(UpstreamGDNDataBoundaryError):
                    authorize_gdn_data_request_v1(
                        process_id="P1",
                        split_role="NORMAL_CANDIDATE_FIT",
                        relative_files=("hai-23.05/hai-train1.csv", prohibited),
                        requested_feature_names=("P1_A",),
                    )
        for prohibited_input in (
            "BR2_pair_ledger",
            "META_output",
            "STAT_output",
        ):
            with self.subTest(prohibited_input=prohibited_input):
                with self.assertRaises(UpstreamGDNDataBoundaryError):
                    authorize_gdn_data_request_v1(
                        process_id="P1",
                        split_role="NORMAL_CANDIDATE_FIT",
                        relative_files=(
                            "hai-23.05/hai-train1.csv",
                            "hai-23.05/hai-train2.csv",
                        ),
                        requested_feature_names=("P1_A",),
                        prohibited_inputs=(prohibited_input,),
                    )

    def test_orchestrator_reuses_production_functions_not_smoke_backend(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        for required in (
            "verify_pinned_upstream_checkout_v1",
            "load_authorized_numeric_segments_v1",
            "train_upstream_aligned_seed_v1",
            "project_seed_record_to_universe_v1",
            "aggregate_and_rank_gdn_candidates_v1",
            "GDNCandidateResultV1",
        ):
            self.assertIn(required, source)
        self.assertNotIn("paperworks.gdn.masked", source)
        self.assertNotIn("paperworks.gdn.torch_backend", source)
        self.assertNotIn("TASK-039C_META_RESULT", source)
        self.assertNotIn("TASK-039C_STAT_RESULT", source)

    def test_fidelity_hash_uses_canonical_git_blob_not_checkout_eol(self) -> None:
        relative = "src/paperworks/gdn/upstream_candidate_backend_v1.py"
        blob = subprocess.run(
            [
                "git",
                "-c",
                f"safe.directory={ROOT.resolve().as_posix()}",
                "-C",
                str(ROOT),
                "show",
                f"c0efdb6218385ec326be1a929371242314e63cb6:{relative}",
            ],
            check=True,
            capture_output=True,
        ).stdout
        receipt = json.loads(
            (ROOT / "docs/task_reports/TASK-039C_GDN_FIDELITY.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(hashlib.sha256(blob).hexdigest(), receipt["implementation_sha256"])

if __name__ == "__main__":
    unittest.main()
