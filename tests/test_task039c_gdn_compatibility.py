from __future__ import annotations

import inspect
import json
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from paperworks.gdn.gdn_remediation_environment_v1 import verify_self_hash_v1
from paperworks.gdn.pyg_softmax_compatibility_v1 import (
    EXACT_ENVIRONMENT_RECEIPT_HASH,
    FLOAT32_ATOL,
    FLOAT32_RTOL,
    FLOAT64_ATOL,
    FLOAT64_RTOL,
    FROZEN_HYPERPARAMETER_HASH,
    GDNR_RESULT_COMMIT,
    INSTALLED_PYG_SIGNATURE,
    assert_allowed_gdnc_paths_v1,
    assert_gdnc_scientific_patch_scope_v1,
    independent_grouped_softmax_reference_v1,
    verify_synthetic_semantic_equivalence_v1,
)
from paperworks.gdn.upstream_candidate_backend_v1 import (
    ALLOWED_VALUE_FILES,
    FROZEN_SEEDS,
    TASK039C0_PAIR_UNIVERSE_HASH,
    UpstreamGDNDataBoundaryError,
    UpstreamGDNTrainingConfigV1,
    _load_runtime_types_v1,
    authorize_gdn_data_request_v1,
    upstream_sparse_softmax_compat_v1,
    verify_pinned_upstream_checkout_v1,
)
from paperworks.v6.candidate_discovery_protocol_v1 import (
    CandidateDiscoveryProtocolBundleV1,
)
from scripts.run_task039c_gdn_compat import ALLOWED_COMMIT_A_PATHS


ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "external/gdn"
ENVIRONMENT = ROOT / "docs/task_reports/TASK-039C_GDNR_ENVIRONMENT_RECEIPT.json"
C0 = ROOT / "docs/task_reports/TASK-039C0_PROTOCOL_BUNDLE.json"


class Task039CGDNCSoftmaxCompatibilityTests(unittest.TestCase):
    def test_installed_pyg_28_signature_places_ptr_before_num_nodes(self) -> None:
        from importlib.metadata import version
        from torch_geometric.utils import softmax

        self.assertEqual(version("torch-geometric"), "2.8.0")
        signature = inspect.signature(softmax)
        self.assertEqual(str(signature), INSTALLED_PYG_SIGNATURE)
        self.assertEqual(list(signature.parameters), ["src", "index", "ptr", "num_nodes", "dim"])

    def test_upstream_and_failed_port_used_old_positional_semantics(self) -> None:
        upstream = (UPSTREAM / "models/graph_layer.py").read_text(encoding="utf-8")
        self.assertIn("alpha = softmax(alpha, edge_index_i, size_i)", upstream)
        result = subprocess.run(
            [
                "git",
                "-c",
                f"safe.directory={ROOT.resolve().as_posix()}",
                "-C",
                str(ROOT),
                "show",
                f"{GDNR_RESULT_COMMIT}:src/paperworks/gdn/upstream_candidate_backend_v1.py",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("alpha = softmax(alpha, edge_index_i, size_i)", result.stdout)

    def test_adapter_maps_old_third_argument_to_num_nodes_keyword(self) -> None:
        import torch

        src = torch.tensor([1.0, 2.0], dtype=torch.float64)
        index = torch.tensor([0, 0], dtype=torch.long)
        sentinel = torch.tensor([0.25, 0.75], dtype=torch.float64)
        with patch("torch_geometric.utils.softmax", return_value=sentinel) as mocked:
            observed = upstream_sparse_softmax_compat_v1(src, index, 4)
        self.assertIs(observed, sentinel)
        mocked.assert_called_once_with(src, index=index, num_nodes=4)

    def test_independent_grouped_reference_does_not_call_adapter(self) -> None:
        import torch

        src = torch.tensor([-1.0, 2.0, 0.0], dtype=torch.float64)
        index = torch.tensor([0, 1, 0], dtype=torch.long)
        with patch(
            "paperworks.gdn.upstream_candidate_backend_v1.upstream_sparse_softmax_compat_v1",
            side_effect=AssertionError("adapter must not be called"),
        ):
            observed = independent_grouped_softmax_reference_v1(src, index, 3)
        expected_group_zero = torch.softmax(torch.tensor([-1.0, 0.0], dtype=torch.float64), dim=0)
        torch.testing.assert_close(observed[[0, 2]], expected_group_zero)
        self.assertEqual(float(observed[1]), 1.0)

    def test_precommitted_float64_equivalence_matrix_passes(self) -> None:
        records = verify_synthetic_semantic_equivalence_v1()
        self.assertEqual(
            [item["case_id"] for item in records],
            [
                "two_groups_positive_negative_repeated",
                "unused_nodes_and_one_element_group",
                "large_magnitude_stability",
                "multidimensional_graph_layer_shape",
            ],
        )
        self.assertEqual(FLOAT64_ATOL, 1e-12)
        self.assertEqual(FLOAT64_RTOL, 1e-12)
        self.assertTrue(all(item["passed"] for item in records))
        self.assertTrue(all(item["max_absolute_error"] <= FLOAT64_ATOL for item in records))

    def test_graph_layer_coefficients_match_independent_reference(self) -> None:
        import torch
        import torch.nn.functional as functional

        torch.manual_seed(7301)
        config = UpstreamGDNTrainingConfigV1(dropout=0.2)
        _, _, model_type = _load_runtime_types_v1()
        model = model_type(8, config)
        layer = model.gnn_layer.gnn
        layer.eval()
        edge_index_i = torch.tensor([0, 2, 0, 5, 2, 5, 7], dtype=torch.long)
        edge_sources = torch.tensor([1, 3, 4, 6, 0, 2, 5], dtype=torch.long)
        edges = torch.stack((edge_sources, edge_index_i))
        x_i = torch.randn(len(edge_index_i), config.embedding_dim)
        x_j = torch.randn(len(edge_index_i), config.embedding_dim)
        embedding = torch.randn(8, config.embedding_dim)
        original_groups = edge_index_i.clone()

        observed_output = layer.message(
            x_i=x_i,
            x_j=x_j,
            edge_index_i=edge_index_i,
            size_i=8,
            embedding=embedding,
            edges=edges,
        )
        reshaped_i = x_i.view(-1, layer.heads, layer.out_channels)
        reshaped_j = x_j.view(-1, layer.heads, layer.out_channels)
        embedding_i = embedding[edge_index_i].unsqueeze(1).repeat(1, layer.heads, 1)
        embedding_j = embedding[edges[0]].unsqueeze(1).repeat(1, layer.heads, 1)
        key_i = torch.cat((reshaped_i, embedding_i), dim=-1)
        key_j = torch.cat((reshaped_j, embedding_j), dim=-1)
        logits = (key_i * torch.cat((layer.att_i, layer.att_em_i), dim=-1)).sum(-1)
        logits += (key_j * torch.cat((layer.att_j, layer.att_em_j), dim=-1)).sum(-1)
        logits = functional.leaky_relu(
            logits.view(-1, layer.heads, 1), layer.negative_slope
        )
        expected_alpha = independent_grouped_softmax_reference_v1(logits, edge_index_i, 8)
        expected_output = reshaped_j * expected_alpha.view(-1, layer.heads, 1)

        torch.testing.assert_close(
            layer._alpha,
            expected_alpha,
            atol=FLOAT32_ATOL,
            rtol=FLOAT32_RTOL,
        )
        torch.testing.assert_close(
            observed_output,
            expected_output,
            atol=FLOAT32_ATOL,
            rtol=FLOAT32_RTOL,
        )
        self.assertEqual(observed_output.shape, (len(edge_index_i), 1, config.embedding_dim))
        self.assertTrue(torch.equal(edge_index_i, original_groups))
        for target in set(edge_index_i.tolist()):
            selected = layer._alpha[edge_index_i == target]
            torch.testing.assert_close(
                selected.sum(dim=0),
                torch.ones_like(selected.sum(dim=0)),
                atol=FLOAT32_ATOL,
                rtol=FLOAT32_RTOL,
            )

    def test_patch_scope_guard_accepts_only_the_compatibility_binding(self) -> None:
        patched_hash = assert_gdnc_scientific_patch_scope_v1(repository_root=ROOT)
        self.assertRegex(patched_hash, r"^[a-f0-9]{64}$")
        changed = assert_allowed_gdnc_paths_v1(
            repository_root=ROOT,
            allowed_paths=ALLOWED_COMMIT_A_PATHS,
        )
        self.assertIn("src/paperworks/gdn/upstream_candidate_backend_v1.py", changed)

    def test_frozen_hyperparameters_and_seed_set_are_unchanged(self) -> None:
        config = UpstreamGDNTrainingConfigV1()
        self.assertEqual(config.seeds, FROZEN_SEEDS)
        self.assertEqual(config.hyperparameter_hash, FROZEN_HYPERPARAMETER_HASH)
        self.assertEqual(config.learned_graph_topk, 5)
        self.assertEqual(config.epochs, 30)
        self.assertEqual(config.early_stopping_patience, 15)

    def test_upstream_checkout_remains_clean_and_pinned(self) -> None:
        receipt = verify_pinned_upstream_checkout_v1(UPSTREAM)
        self.assertEqual(receipt.commit, "9853899da860682669a134e4af315d036aab4eca")
        self.assertTrue(receipt.detached_head)
        self.assertTrue(receipt.clean_worktree)

    def test_exact_environment_receipt_is_unchanged(self) -> None:
        document = json.loads(ENVIRONMENT.read_text(encoding="utf-8"))
        self.assertEqual(verify_self_hash_v1(document), EXACT_ENVIRONMENT_RECEIPT_HASH)
        self.assertEqual(document["python_version"], "3.12.13")
        self.assertEqual(document["top_level_packages"]["torch"], "2.12.1")
        self.assertEqual(document["top_level_packages"]["torch-geometric"], "2.8.0")

    def test_c0_pair_universe_is_unchanged(self) -> None:
        bundle = CandidateDiscoveryProtocolBundleV1.from_dict(
            json.loads(C0.read_text(encoding="utf-8"))
        )
        self.assertEqual(
            bundle.universe_policy.eligible_pair_universe_hash,
            TASK039C0_PAIR_UNIVERSE_HASH,
        )
        self.assertEqual(bundle.universe_policy.eligible_pair_count, 144)

    def test_prohibited_cross_arm_and_split_requests_fail_before_io(self) -> None:
        features = ("P1_FCV01D", "P1_FT01")
        for prohibited in ("BR2 pair ledger", "META output", "STAT output"):
            with self.subTest(prohibited=prohibited), self.assertRaises(
                UpstreamGDNDataBoundaryError
            ):
                authorize_gdn_data_request_v1(
                    process_id="P1",
                    split_role="NORMAL_CANDIDATE_FIT",
                    relative_files=ALLOWED_VALUE_FILES,
                    requested_feature_names=features,
                    prohibited_inputs=(prohibited,),
                )
        for files in (
            ("hai-23.05/hai-train1.csv", "hai-23.05/hai-train3.csv"),
            ("hai-23.05/hai-train1.csv", "hai-23.05/hai-train4.csv"),
            ("hai-23.05/hai-train1.csv", "hai-23.05/hai-test1.csv"),
        ):
            with self.subTest(files=files), self.assertRaises(UpstreamGDNDataBoundaryError):
                authorize_gdn_data_request_v1(
                    process_id="P1",
                    split_role="NORMAL_CANDIDATE_FIT",
                    relative_files=files,
                    requested_feature_names=features,
                )


if __name__ == "__main__":
    unittest.main()
