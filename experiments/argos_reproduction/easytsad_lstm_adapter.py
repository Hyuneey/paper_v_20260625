"""Container-only adapter for the frozen EasyTSAD LSTMAD variants."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
from pathlib import Path
import random
import sys
import types
from typing import Any, Mapping


class EasyTsadAdapterError(RuntimeError):
    pass


def stable_json_bytes(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalize_values(values: object, minimum: float, maximum: float) -> Any:
    import numpy as np

    array = np.asarray(values, dtype=np.float64)
    scale = maximum - minimum
    transformed = (array - minimum) / (scale if scale != 0.0 else 1.0)
    return np.clip(transformed, -2.0, 3.0)


def align_scores(raw_scores: object, input_count: int, missing_prefix_count: int) -> Any:
    import numpy as np

    scores = np.asarray(raw_scores, dtype=np.float64)
    if scores.ndim != 1 or input_count < 0 or missing_prefix_count < 0:
        raise EasyTsadAdapterError("TASK037B_SCORE_ALIGNMENT_INVALID")
    if len(scores) != max(input_count - missing_prefix_count, 0):
        raise EasyTsadAdapterError("TASK037B_SCORE_LENGTH_INVALID")
    aligned = np.pad(scores, (input_count - len(scores), 0), constant_values=0.0)
    if aligned.shape != (input_count,) or not np.all(np.isfinite(aligned)):
        raise EasyTsadAdapterError("TASK037B_ALIGNED_SCORE_INVALID")
    return aligned


def _load_values(path: Path) -> Any:
    import numpy as np

    values = np.load(path, allow_pickle=False)
    values = np.asarray(values, dtype=np.float64).reshape(-1)
    if values.ndim != 1 or len(values) == 0 or not np.all(np.isfinite(values)):
        raise EasyTsadAdapterError("TASK037B_INPUT_VALUES_INVALID")
    return values


def _load_config(path: Path, variant: str) -> tuple[dict[str, Any], dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        config = json.load(handle)
    if variant not in ("LSTMADalpha", "LSTMADbeta"):
        raise EasyTsadAdapterError("TASK037B_VARIANT_UNSUPPORTED")
    registered = tuple(item["detector_id"] for item in config["detector_arms"])
    if registered != ("LSTMADalpha", "LSTMADbeta"):
        raise EasyTsadAdapterError("TASK037B_VARIANT_REGISTRY_INVALID")
    return config, dict(config["detector_configurations"][variant])


def _method_class(variant: str) -> Any:
    sys.path.insert(0, "/opt/easytsad")
    controller_stub = types.ModuleType("EasyTSAD.Controller")
    controller_stub.PathManager = object
    sys.modules.setdefault("EasyTSAD.Controller", controller_stub)
    if variant == "LSTMADalpha":
        from EasyTSAD.Methods.LSTMADalpha.LSTMADalpha import LSTMADalpha

        return LSTMADalpha
    if variant == "LSTMADbeta":
        from EasyTSAD.Methods.LSTMADbeta.LSTMADbeta import LSTMADbeta

        return LSTMADbeta
    raise EasyTsadAdapterError("TASK037B_VARIANT_UNSUPPORTED")


def _tsdata(train: Any, valid: Any, test: Any) -> Any:
    import numpy as np
    from EasyTSAD.DataFactory import TSData

    return TSData(
        train=train,
        valid=valid,
        test=test,
        train_label=np.zeros(len(train), dtype=np.int8),
        valid_label=np.zeros(len(valid), dtype=np.int8),
        test_label=np.zeros(len(test), dtype=np.int8),
        info={"task": "TASK-037B", "labels_are_synthetic_placeholders": True},
    )


def _seed(seed: int) -> None:
    import numpy as np
    import torch

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)


def _params(model: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "window_size": int(model["input_window"]),
        "pred_len": int(model["prediction_horizon"]),
        "input_size": 1,
        "hidden_dim": int(model["hidden_size"]),
        "num_layer": int(model["layer_count"]),
        "batch_size": int(model["batch_size"]),
        "epochs": int(model["epochs"]),
        "lr": float(model["learning_rate"]),
    }


def train(
    *, variant: str, values_path: Path, config_path: Path, output_dir: Path, seed: int
) -> dict[str, Any]:
    import numpy as np

    _, model = _load_config(config_path, variant)
    if seed != int(model["seed"]):
        raise EasyTsadAdapterError("TASK037B_SEED_MISMATCH")
    values = _load_values(values_path)
    validation_count = int(len(values) * float(model["internal_validation_proportion"]))
    if validation_count <= int(model["input_window"]) + int(model["prediction_horizon"]):
        raise EasyTsadAdapterError("TASK037B_INTERNAL_VALIDATION_TOO_SHORT")
    train_values = values[:-validation_count]
    valid_values = values[-validation_count:]
    minimum = float(np.min(train_values))
    maximum = float(np.max(train_values))
    train_norm = normalize_values(train_values, minimum, maximum)
    valid_norm = normalize_values(valid_values, minimum, maximum)
    _seed(seed)
    method = _method_class(variant)(_params(model))
    checkpoint_dir = output_dir / "checkpoint"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    method.early_stopping.save_path = str(checkpoint_dir)
    log = io.StringIO()
    with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        method.train_valid_phase(_tsdata(train_norm, valid_norm, valid_norm))
    checkpoint = checkpoint_dir / "best_network.pth"
    if not checkpoint.is_file():
        raise EasyTsadAdapterError("TASK037B_CHECKPOINT_NOT_CREATED")
    normalization = {
        "schema_version": "1.0",
        "method": "generation_train_subpartition_min_max",
        "feature_range": [0.0, 1.0],
        "clip_range": [-2.0, 3.0],
        "minimum": minimum,
        "maximum": maximum,
        "fit_count": int(len(train_values)),
        "generation_count": int(len(values)),
        "internal_validation_count": validation_count,
    }
    normalization_path = output_dir / "normalization.json"
    normalization_path.write_bytes(stable_json_bytes(normalization) + b"\n")
    (output_dir / "training.log").write_text(log.getvalue(), encoding="utf-8")
    return {
        "status": "trained",
        "variant": variant,
        "seed": seed,
        "input_count": int(len(values)),
        "training_count": int(len(train_values)),
        "internal_validation_count": validation_count,
        "checkpoint_sha256": sha256_file(checkpoint),
        "normalization_sha256": sha256_file(normalization_path),
        "training_log_sha256": sha256_file(output_dir / "training.log"),
        "labels_received": False,
    }


def score(
    *,
    variant: str,
    values_path: Path,
    config_path: Path,
    checkpoint_path: Path,
    normalization_path: Path,
    output_dir: Path,
    seed: int,
) -> dict[str, Any]:
    import numpy as np
    import torch

    _, model = _load_config(config_path, variant)
    if seed != int(model["seed"]):
        raise EasyTsadAdapterError("TASK037B_SEED_MISMATCH")
    values = _load_values(values_path)
    with normalization_path.open("r", encoding="utf-8") as handle:
        normalization = json.load(handle)
    normalized = normalize_values(values, float(normalization["minimum"]), float(normalization["maximum"]))
    _seed(seed)
    method = _method_class(variant)(_params(model))
    state = torch.load(checkpoint_path, map_location="cpu")
    method.model.load_state_dict(state)
    method.model.to(method.device)
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        method.test_phase(_tsdata(normalized[:1], normalized[:1], normalized))
    raw = np.asarray(method.anomaly_score(), dtype=np.float64)
    missing_prefix = int(model["input_window"]) + int(model["prediction_horizon"])
    aligned = align_scores(raw, len(values), missing_prefix)
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = output_dir / "raw_score.npy"
    aligned_path = output_dir / "aligned_score.npy"
    np.save(raw_path, raw, allow_pickle=False)
    np.save(aligned_path, aligned, allow_pickle=False)
    return {
        "status": "scored",
        "variant": variant,
        "seed": seed,
        "input_count": int(len(values)),
        "raw_score_count": int(len(raw)),
        "aligned_score_count": int(len(aligned)),
        "missing_prefix_count": missing_prefix,
        "alignment_policy": str(model["missing_prefix_policy"]),
        "scores_finite": bool(np.all(np.isfinite(aligned))),
        "raw_score_sha256": sha256_file(raw_path),
        "aligned_score_sha256": sha256_file(aligned_path),
        "score_min": float(np.min(aligned)),
        "score_max": float(np.max(aligned)),
        "score_mean": float(np.mean(aligned)),
        "score_std": float(np.std(aligned)),
        "labels_received": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("train", "score"))
    parser.add_argument("--variant", required=True)
    parser.add_argument("--values", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--normalization", type=Path)
    args = parser.parse_args()
    if args.mode == "train":
        result = train(
            variant=args.variant,
            values_path=args.values,
            config_path=args.config,
            output_dir=args.output,
            seed=args.seed,
        )
    else:
        if args.checkpoint is None or args.normalization is None:
            raise EasyTsadAdapterError("TASK037B_SCORE_ARTIFACTS_REQUIRED")
        result = score(
            variant=args.variant,
            values_path=args.values,
            config_path=args.config,
            checkpoint_path=args.checkpoint,
            normalization_path=args.normalization,
            output_dir=args.output,
            seed=args.seed,
        )
    print(stable_json_bytes(result).decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
