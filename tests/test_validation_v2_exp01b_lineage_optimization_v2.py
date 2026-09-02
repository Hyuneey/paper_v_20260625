from __future__ import annotations

import ast
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

from paperworks.validation_v2.exp01_scientific_v1 import PAIR_UNIVERSE
from paperworks.validation_v2.exp01b_backend_v1 import Exp01BLineageEvidenceV1
from paperworks.v6.common import stable_hash_v1


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "finalize_exp01b_public_lineage.py"
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location("exp01b_lineage_finalizer_test", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class Exp01BLineageOptimizationTests(unittest.TestCase):
    def _identity(self) -> dict[str, object]:
        body = {
            "experiment_id": "EXP-01B-GDN-XAI-V1",
            "run_id": "exp01b-test-seed-11",
            "view": "TRAIN1_ONLY",
            "seed": 11,
            "checkpoint_sha256": "a" * 64,
            "implementation_hash": "b" * 64,
        }
        return {**body, "identity_hash": stable_hash_v1(body)}

    def _evidence(self) -> Exp01BLineageEvidenceV1:
        graph = (("P1_PCV01D", "P1_FT01"),)
        return Exp01BLineageEvidenceV1(
            embedding_scores={pair: float(index) for index, pair in enumerate(PAIR_UNIVERSE)},
            attention_scores={graph[0]: 0.25},
            attention_invariance_passed=True,
            graph_edges=graph,
            graph_hash=stable_hash_v1({"graph_edges": graph}),
        )

    def test_private_cache_is_atomic_replayable_and_identity_bound(self) -> None:
        identity = self._identity()
        evidence = self._evidence()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cache.json"
            cache_hash = MODULE._persist_private_cache(
                path, identity=identity, evidence=evidence,
            )
            self.assertEqual(len(cache_hash), 64)
            replay = MODULE._load_private_cache(path, expected_identity=identity)
            self.assertIsNotNone(replay)
            self.assertEqual(replay.graph_hash, evidence.graph_hash)
            wrong = {**identity, "source_commit": "c" * 40}
            with self.assertRaises(MODULE.Exp01BLineageClosureError):
                MODULE._load_private_cache(path, expected_identity=wrong)

            document = json.loads(path.read_text(encoding="utf-8"))
            document["attention_invariance_passed"] = False
            path.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaises(MODULE.Exp01BLineageClosureError):
                MODULE._load_private_cache(path, expected_identity=identity)

    def test_lineage_input_attempts_preserve_interruption_and_real_counts(self) -> None:
        closure = {
            "schema": "input",
            "schema_version": "1.0.0",
            "experiment_id": "EXP-01B-GDN-XAI-V1",
            "split_open_counts": {split: 1 for split in ("train1", "train2", "train3", "train4")},
            "test1_accesses": 0,
            "label_accesses": 0,
            "test2_accesses": 0,
            "heldout_accesses": 0,
            "private_paths_embedded": False,
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first, history1 = MODULE._write_lineage_input_attempt(
                root, closure_input_receipt=closure,
                original_input_receipt_hash="d" * 64,
            )
            second, history2 = MODULE._write_lineage_input_attempt(
                root, closure_input_receipt=closure,
                original_input_receipt_hash="d" * 64,
            )
            self.assertEqual(first["cumulative_known_split_open_counts"]["train4"], 2)
            self.assertEqual(second["cumulative_known_split_open_counts"]["train4"], 3)
            self.assertEqual(second["previous_attempt_receipt_hash"], first["receipt_hash"])
            self.assertEqual(len(history1), 1)
            self.assertEqual(len(history2), 2)

    def test_finalizer_has_no_training_call_and_private_cache_is_git_ignored(self) -> None:
        tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
        called = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertNotIn("train_exp01b_seed_v1", called)
        self.assertNotIn("train_exp01_seed_v2", called)
        self.assertTrue(str(MODULE.PRIVATE_LINEAGE_CACHE).replace("\\", "/").startswith("artifacts/"))
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("artifacts/", ignore)


if __name__ == "__main__":
    unittest.main()
