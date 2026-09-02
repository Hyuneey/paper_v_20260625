from __future__ import annotations

from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from paperworks.validation_v2.exp01_scientific_v1 import (
    META_RESULT_HASH,
    PAIR_UNIVERSE,
    STAT_RESULT_HASH,
)
from paperworks.validation_v2.exp01b_contract_v1 import (
    ComputeBackend,
    REQUIRED_DETERMINISTIC_FLAGS,
    build_environment_freeze_v1,
    preregistration_document_v1,
)
from paperworks.v6.common import stable_hash_v1


_SCRIPT = Path(__file__).parents[1] / "scripts" / "run_exp01b_gdn_xai.py"
_SPEC = importlib.util.spec_from_file_location("run_exp01b_gdn_xai", _SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
cli = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(cli)


def _write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _authority(document: dict, field: str = "authority_hash") -> dict:
    return {**document, field: sha256(cli._canonical(document)).hexdigest()}


class _Receipt:
    def __init__(self, split: str) -> None:
        self._split = split

    def to_dict(self) -> dict:
        return {
            "split_id": self._split,
            "file_open_count": 1,
            "labels_accessed": False,
            "test2_accesses": 0,
            "heldout_accesses": 0,
            "receipt_hash": sha256(self._split.encode()).hexdigest(),
        }


class _Frame:
    def __init__(self, split: str) -> None:
        self.receipt = _Receipt(split)
        self._split = split

    def numeric_matrix(self):
        return (self._split, "private-matrix")


class Exp01BCliContractTests(unittest.TestCase):
    def test_import_is_nonexecuting_and_launch_environment_fails_closed(self) -> None:
        self.assertTrue(callable(cli.main))
        with self.assertRaisesRegex(cli.Exp01BCliError, "CUBLAS"):
            cli._validate_launch_environment({})
        with self.assertRaisesRegex(cli.Exp01BCliError, "PYTHONHASHSEED"):
            cli._validate_launch_environment({"CUBLAS_WORKSPACE_CONFIG": ":4096:8"})
        cli._validate_launch_environment({
            "CUBLAS_WORKSPACE_CONFIG": ":4096:8", "PYTHONHASHSEED": "0",
        })

    def test_preregistration_and_cuda_environment_receipt_replay_exactly(self) -> None:
        environment = build_environment_freeze_v1(
            backend=ComputeBackend.CUDA, python_version="3.12.13",
            torch_version="2.12.1+cu130", cuda_build="13.0",
            driver_version="610.47", gpu_model="NVIDIA GeForce RTX 5060 Laptop GPU",
            deterministic_flags=dict(REQUIRED_DETERMINISTIC_FLAGS),
            synthetic_smoke_passed=True, model_device="cuda", tensor_device="cuda",
        )
        prereg_hash = preregistration_document_v1()["preregistration_hash"]
        body = {
            "schema": "paperworks.validation_v2.exp01b_gpu_environment_receipt_v1",
            "schema_version": "1.0.0", "experiment_id": "EXP-01B-GDN-XAI-V1",
            "source_commit": "a" * 40, "runner_script_sha256": "b" * 64,
            "preregistration_hash": prereg_hash,
            "environment": {**environment.body_document(), "environment_hash": environment.environment_hash},
            "torch_geometric_version": "2.8.0",
            "synthetic_only": True, "scientific_data_accesses": 0,
            "test1_accesses": 0, "label_accesses": 0, "test2_accesses": 0,
            "heldout_accesses": 0, "private_paths_embedded": False,
        }
        document = {**body, "receipt_hash": stable_hash_v1(body)}
        replay = cli._environment_from_receipt(
            document, preregistration_hash=prereg_hash,
            runner_script_sha256="b" * 64, source_is_ancestor=True,
        )
        self.assertEqual(replay.environment_hash, environment.environment_hash)
        mutated = dict(document)
        mutated["receipt_hash"] = "0" * 64
        with self.assertRaisesRegex(cli.Exp01BCliError, "SELF_HASH"):
            cli._environment_from_receipt(
                mutated, preregistration_hash=prereg_hash,
                runner_script_sha256="b" * 64, source_is_ancestor=True,
            )

    def test_committed_meta_stat_and_formal_v4_authorities_replay(self) -> None:
        meta_pairs = PAIR_UNIVERSE[:20]
        stat_pairs = PAIR_UNIVERSE[:11] + PAIR_UNIVERSE[20:29]
        union = tuple(sorted(set(meta_pairs) | set(stat_pairs)))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write(root / cli.META_PATH, {
                "artifact_hash": META_RESULT_HASH,
                "top20_identities": [
                    {"source_identity": source, "target_identity": target}
                    for source, target in meta_pairs
                ],
            })
            _write(root / cli.STAT_PATH, {
                "artifact_hash": STAT_RESULT_HASH,
                "top20": [{"source": source, "target": target} for source, target in stat_pairs],
            })
            candidate_body = {
                "artifact_type": "validation_v2a_meta_stat_candidate_union_authority_v1",
                "meta_artifact_hash": META_RESULT_HASH, "stat_artifact_hash": STAT_RESULT_HASH,
                "candidates": [{"source": source, "target": target} for source, target in union],
                "labels_accessed": False, "test1_accessed": False, "test2_accessed": False,
            }
            _write(root / cli.V2A_CANDIDATE_AUTHORITY, _authority(candidate_body))
            portfolio_body = {
                "artifact_type": "validation_v2_formal_v4_portfolio_authority_v1",
                "authority_family": "FORMAL_V4", "canonical_to_v4_bridge_used": False,
                "descriptors": [{"source": source, "target": target} for source, target in union[:7]],
            }
            _write(root / cli.V2A_PORTFOLIO_AUTHORITY, _authority(portfolio_body))
            meta, stat, conversion = cli._load_rankings_and_conversion(root)
        self.assertEqual(meta, meta_pairs)
        self.assertEqual(stat, stat_pairs)
        self.assertEqual(conversion.executable_pairs, union[:7])

    def test_normal_loader_opens_exact_train1_through_train4_once(self) -> None:
        calls: list[tuple[str, tuple[str, ...]]] = []

        def resolve(_root):
            return object()

        def load(*, split_id, operations, protocol_guard, ledger, **_kwargs):
            for operation in operations:
                protocol_guard.authorize(split_id=split_id, operation=operation)
            ledger.authorize_once(split_id)
            calls.append((split_id, tuple(item.value for item in operations)))
            return _Frame(split_id)

        inputs, receipt = cli._load_normal_inputs(
            Path.cwd(), source_commit="a" * 40,
            capability_resolver=resolve, frame_loader=load,
        )
        self.assertEqual([item[0] for item in calls], ["train1", "train2", "train3", "train4"])
        self.assertEqual(len(calls), 4)
        self.assertEqual(inputs.receipt_hashes.keys(), {"train1", "train2", "train3", "train4"})
        self.assertEqual(receipt["test1_accesses"], 0)
        self.assertEqual(receipt["test2_accesses"], 0)

    def test_public_outputs_reject_private_paths(self) -> None:
        cli._assert_public_document_safe({"safe": "P1_FCV01D", "path": False})
        with self.assertRaisesRegex(cli.Exp01BCliError, "PRIVATE_PATH"):
            cli._assert_public_document_safe({"unsafe": r"C:\private\hai-train1.csv"})


if __name__ == "__main__":
    unittest.main()
