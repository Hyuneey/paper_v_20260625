"""Atomic private checkpoint persistence for EXP-01B.

Only sanitized identities leave the private checkpoint namespace.  The module
does not know or serialize dataset paths or values.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import os
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

from paperworks.v6.common import require_sha256, stable_hash_v1


_TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")


class Exp01BCheckpointError(RuntimeError):
    pass


def _file_hash(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def checkpoint_state_hash_v1(state_dict: Mapping[str, Any]) -> str:
    digest = sha256()
    for name in sorted(state_dict):
        tensor = state_dict[name].detach().cpu().contiguous()
        digest.update(name.encode("utf-8"))
        digest.update(str(tensor.dtype).encode("ascii"))
        digest.update(str(tuple(int(item) for item in tensor.shape)).encode("ascii"))
        digest.update(tensor.numpy().tobytes(order="C"))
    return digest.hexdigest()


@dataclass(frozen=True)
class Exp01BCheckpointReceiptV1:
    run_id: str
    view: str
    seed: int
    checkpoint_sha256: str
    state_hash: str
    training_config_hash: str
    environment_hash: str
    graph_hash: str
    byte_size: int
    atomic_write: bool = True
    fsync_completed: bool = True
    close_reopen_replay: bool = True

    def __post_init__(self) -> None:
        if _TOKEN.fullmatch(self.run_id) is None:
            raise Exp01BCheckpointError("checkpoint run ID is unsafe")
        for name in ("checkpoint_sha256", "state_hash", "training_config_hash", "environment_hash", "graph_hash"):
            require_sha256(getattr(self, name), name)
        if self.seed not in {11, 23, 37} or self.byte_size <= 0:
            raise Exp01BCheckpointError("checkpoint schedule or size is invalid")
        if not self.atomic_write or not self.fsync_completed or not self.close_reopen_replay:
            raise Exp01BCheckpointError("durable checkpoint closure is required")

    def public_document(self) -> dict[str, object]:
        body: dict[str, object] = {
            "schema": "paperworks.validation_v2.exp01b_checkpoint_receipt_v1",
            "schema_version": "1.0.0",
            "experiment_id": "EXP-01B-GDN-XAI-V1",
            "run_id": self.run_id,
            "view": self.view,
            "seed": self.seed,
            "checkpoint_sha256": self.checkpoint_sha256,
            "state_hash": self.state_hash,
            "training_config_hash": self.training_config_hash,
            "environment_hash": self.environment_hash,
            "graph_hash": self.graph_hash,
            "byte_size": self.byte_size,
            "atomic_write": self.atomic_write,
            "fsync_completed": self.fsync_completed,
            "close_reopen_replay": self.close_reopen_replay,
            "private_path_disclosed": False,
            "test1_accesses": 0,
            "label_accesses": 0,
            "test2_accesses": 0,
            "heldout_accesses": 0,
        }
        return {**body, "receipt_hash": stable_hash_v1(body)}


def persist_private_checkpoint_v1(
    *, torch_module: Any, private_root: Path, run_id: str, view: str, seed: int,
    state_dict: Mapping[str, Any], training_config_hash: str,
    environment_hash: str, graph_hash: str,
) -> tuple[Path, Exp01BCheckpointReceiptV1]:
    if _TOKEN.fullmatch(run_id) is None or not private_root.is_absolute():
        raise Exp01BCheckpointError("private checkpoint target is invalid")
    private_root.mkdir(parents=True, exist_ok=True)
    final_path = private_root / f"{run_id}.pt"
    temporary = private_root / f".{run_id}.{os.getpid()}.tmp"
    if final_path.exists() or temporary.exists():
        raise Exp01BCheckpointError("checkpoint target already exists")
    payload = {
        "experiment_id": "EXP-01B-GDN-XAI-V1",
        "run_id": run_id,
        "view": view,
        "seed": seed,
        "training_config_hash": training_config_hash,
        "environment_hash": environment_hash,
        "graph_hash": graph_hash,
        "state_dict": dict(state_dict),
    }
    expected_state = checkpoint_state_hash_v1(state_dict)
    try:
        with temporary.open("wb") as stream:
            torch_module.save(payload, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, final_path)
        try:
            directory_fd = os.open(str(private_root), os.O_RDONLY)
        except OSError:
            directory_fd = None
        if directory_fd is not None:
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        with final_path.open("rb") as stream:
            replayed = torch_module.load(stream, map_location="cpu", weights_only=False)
        if (
            replayed.get("run_id") != run_id
            or replayed.get("view") != view
            or replayed.get("seed") != seed
            or replayed.get("training_config_hash") != training_config_hash
            or replayed.get("environment_hash") != environment_hash
            or replayed.get("graph_hash") != graph_hash
            or checkpoint_state_hash_v1(replayed.get("state_dict", {})) != expected_state
        ):
            raise Exp01BCheckpointError("checkpoint close-reopen replay mismatch")
        receipt = Exp01BCheckpointReceiptV1(
            run_id=run_id, view=view, seed=seed,
            checkpoint_sha256=_file_hash(final_path), state_hash=expected_state,
            training_config_hash=training_config_hash,
            environment_hash=environment_hash, graph_hash=graph_hash,
            byte_size=final_path.stat().st_size,
        )
        return final_path, receipt
    except Exception:
        if temporary.exists():
            temporary.unlink()
        if final_path.exists():
            final_path.unlink()
        raise


def checkpoint_set_receipt_v1(receipts: Sequence[Exp01BCheckpointReceiptV1]) -> dict[str, object]:
    rows = tuple(receipts)
    expected = {
        (view, seed)
        for view in ("TRAIN1_TRAIN2_COMBINED", "TRAIN1_ONLY", "TRAIN2_ONLY")
        for seed in (11, 23, 37)
    }
    if {(item.view, item.seed) for item in rows} != expected or len(rows) != 9:
        raise Exp01BCheckpointError("exact nine-checkpoint closure required")
    if len({item.environment_hash for item in rows}) != 1 or len({item.training_config_hash for item in rows}) != 1:
        raise Exp01BCheckpointError("checkpoint set mixed environments or configurations")
    body: dict[str, object] = {
        "schema": "paperworks.validation_v2.exp01b_checkpoint_set_receipt_v1",
        "schema_version": "1.0.0",
        "experiment_id": "EXP-01B-GDN-XAI-V1",
        "checkpoint_count": 9,
        "run_receipt_hashes": [item.public_document()["receipt_hash"] for item in sorted(rows, key=lambda x: (x.view, x.seed))],
        "environment_hash": rows[0].environment_hash,
        "training_config_hash": rows[0].training_config_hash,
        "private_paths_disclosed": False,
        "test1_accesses": 0,
        "label_accesses": 0,
        "test2_accesses": 0,
        "heldout_accesses": 0,
    }
    return {**body, "receipt_hash": stable_hash_v1(body)}


__all__ = [
    "Exp01BCheckpointError", "Exp01BCheckpointReceiptV1", "checkpoint_set_receipt_v1",
    "checkpoint_state_hash_v1", "persist_private_checkpoint_v1",
]
