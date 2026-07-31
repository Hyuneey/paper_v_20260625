from __future__ import annotations

import ast
import hashlib
import json
import unittest
from pathlib import Path

from paperworks.gdn.fidelity_v1 import GDNFidelityFreezeV1
from tests.task039p1d_support import (
    MASKED_SOURCE_SHA256,
    TORCH_BEHAVIOR_AST_SHA256,
    UPSTREAM_FILES,
    make_fidelity_freeze,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/v6/task039p1d_gdn_fidelity_freeze.json"
FIDELITY_REPORT = ROOT / "docs/task_reports/TASK-039P1D_FIDELITY_REPORT.json"
TORCH_BEHAVIOR_SYMBOLS = {
    "TorchGDNTrainingConfig",
    "MeanGraphLayer",
    "TorchGDNEmbeddingModel",
    "fit_torch_gdn_embedding_checkpoint",
    "_normal_windows_to_tensor",
    "_message_passing_edges",
    "_batched_edge_index",
}


class Task039P1DUpstreamMappingTests(unittest.TestCase):
    def test_config_freezes_exact_pinned_file_records(self) -> None:
        payload = json.loads(CONFIG.read_text(encoding="utf-8"))
        parsed = GDNFidelityFreezeV1.from_dict(payload)
        self.assertEqual(parsed.upstream_file_records, UPSTREAM_FILES)
        self.assertEqual(parsed.to_dict(), make_fidelity_freeze().to_dict())
        self.assertEqual(len(parsed.upstream_file_records), 7)

    def test_current_behavior_hashes_match_frozen_baseline(self) -> None:
        masked_text = (
            ROOT / "src/paperworks/gdn/masked.py"
        ).read_text(encoding="utf-8")
        self.assertEqual(
            hashlib.sha256(masked_text.encode("utf-8")).hexdigest(),
            MASKED_SOURCE_SHA256,
        )

        source = (
            ROOT / "src/paperworks/gdn/torch_backend.py"
        ).read_text(encoding="utf-8")
        tree = ast.parse(source)
        selected = [
            node
            for node in tree.body
            if isinstance(node, (ast.ClassDef, ast.FunctionDef))
            and node.name in TORCH_BEHAVIOR_SYMBOLS
        ]
        canonical = ast.dump(
            ast.Module(body=selected, type_ignores=[]),
            annotate_fields=True,
            include_attributes=False,
        ).encode("utf-8")
        self.assertEqual(
            hashlib.sha256(canonical).hexdigest(),
            TORCH_BEHAVIOR_AST_SHA256,
        )

    def test_fidelity_report_covers_every_required_comparison_dimension(
        self,
    ) -> None:
        report = json.loads(FIDELITY_REPORT.read_text(encoding="utf-8"))
        expected = {
            "input_shape",
            "training_target",
            "node_embeddings",
            "learned_graph",
            "candidate_mask",
            "graph_layer",
            "embedding_conditioned_attention",
            "self_loop_handling",
            "output_gating",
            "batch_normalization_dropout",
            "objective",
            "checkpoint_selection",
            "split_window_policy",
        }
        self.assertEqual(set(report["comparison"]), expected)
        self.assertTrue(report["upstream"]["git_blob_and_sha256_verified"])


if __name__ == "__main__":
    unittest.main()
