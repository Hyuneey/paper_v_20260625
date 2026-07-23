"""Synthetic-only EasyTSAD LSTM smoke executed inside the detector container."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import random
import sys
import types
from typing import Any


SMOKE_SEED = 20260723
WINDOW_SIZE = 16
PREDICTION_HORIZON = 3


def stable_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def isolation_probe() -> dict[str, Any]:
    interfaces = sorted(path.name for path in Path("/sys/class/net").iterdir())
    root_write_blocked = False
    try:
        Path("/runtime/task037a-write-probe").write_text("blocked", encoding="utf-8")
    except OSError:
        root_write_blocked = True
    memory_max = Path("/sys/fs/cgroup/memory.max").read_text().strip()
    pids_max = Path("/sys/fs/cgroup/pids.max").read_text().strip()
    cpu_max = Path("/sys/fs/cgroup/cpu.max").read_text().strip()
    return {
        "uid": os.getuid(),
        "interfaces": interfaces,
        "root_write_blocked": root_write_blocked,
        "memory_max": memory_max,
        "pids_max": pids_max,
        "cpu_max": cpu_max,
    }


def _series() -> dict[str, Any]:
    import numpy as np

    x = np.linspace(0.0, 8.0 * np.pi, 128, dtype=np.float64)
    smooth = np.sin(x) + 0.05 * np.cos(3.0 * x)
    periodic = np.cos(x / 2.0)
    spike = smooth.copy(); spike[64] += 4.0
    shift = smooth.copy(); shift[64:] += 1.5
    return {
        "normal_smooth_sequence": smooth,
        "normal_periodic_sequence": periodic,
        "localized_spike": spike,
        "persistent_level_shift": shift,
        "short_sequence": np.linspace(-0.25, 0.25, 24, dtype=np.float64),
        "constant_sequence": np.full(128, 0.5, dtype=np.float64),
    }


def _state_hash(model: Any) -> str:
    digest = hashlib.sha256()
    for name, tensor in sorted(model.state_dict().items()):
        digest.update(name.encode("utf-8"))
        digest.update(tensor.detach().cpu().contiguous().numpy().tobytes())
    return digest.hexdigest()


def _run_variant(variant: str, repeat: int) -> dict[str, Any]:
    import numpy as np
    import torch

    sys.path.insert(0, "/opt/easytsad")
    # The official package imports plotting through Controller even though the
    # detector methods only need TSData's in-memory fields. Keep the smoke
    # dependency-minimal without changing upstream source.
    controller_stub = types.ModuleType("EasyTSAD.Controller")
    controller_stub.PathManager = object
    sys.modules.setdefault("EasyTSAD.Controller", controller_stub)
    from EasyTSAD.DataFactory import TSData
    if variant == "LSTMADalpha":
        from EasyTSAD.Methods.LSTMADalpha.LSTMADalpha import LSTMADalpha as Method
        learning_rate = 0.0008
    elif variant == "LSTMADbeta":
        from EasyTSAD.Methods.LSTMADbeta.LSTMADbeta import LSTMADbeta as Method
        learning_rate = 0.0005
    else:
        raise ValueError("TASK037A_VARIANT_UNSUPPORTED")

    random.seed(SMOKE_SEED)
    np.random.seed(SMOKE_SEED)
    torch.manual_seed(SMOKE_SEED)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    train_x = np.linspace(0.0, 12.0 * np.pi, 192, dtype=np.float64)
    train = np.sin(train_x) + 0.05 * np.cos(3.0 * train_x)
    valid_x = np.linspace(0.0, 6.0 * np.pi, 96, dtype=np.float64)
    valid = np.sin(valid_x) + 0.05 * np.cos(3.0 * valid_x)
    labels_train = np.zeros(train.shape[0], dtype=np.int8)
    labels_valid = np.zeros(valid.shape[0], dtype=np.int8)
    params = {
        "window_size": WINDOW_SIZE,
        "pred_len": PREDICTION_HORIZON,
        "input_size": 1,
        "hidden_dim": 8,
        "num_layer": 1,
        "batch_size": 32,
        "epochs": 2,
        "lr": learning_rate,
    }
    method = Method(params)
    checkpoint_dir = Path(f"/tmp/{variant}-{repeat}")
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    method.early_stopping.save_path = str(checkpoint_dir)
    train_data = TSData(
        train=train,
        valid=valid,
        test=valid,
        train_label=labels_train,
        test_label=labels_valid,
        valid_label=labels_valid,
        info={"synthetic": True},
    )
    with contextlib.redirect_stdout(io.StringIO()):
        method.train_valid_phase(train_data)
    checkpoint = checkpoint_dir / "best_network.pth"
    if not checkpoint.is_file():
        raise RuntimeError("TASK037A_CHECKPOINT_NOT_CREATED")

    scenario_results: list[dict[str, Any]] = []
    threshold_source: Any | None = None
    for scenario_id, values in _series().items():
        labels = np.zeros(values.shape[0], dtype=np.int8)
        data = TSData(
            train=train,
            valid=valid,
            test=values,
            train_label=labels_train,
            test_label=labels,
            valid_label=labels_valid,
            info={"synthetic": True},
        )
        with contextlib.redirect_stdout(io.StringIO()):
            method.test_phase(data)
        raw_score = np.asarray(method.anomaly_score(), dtype=np.float64)
        expected_raw_length = max(values.shape[0] - WINDOW_SIZE - PREDICTION_HORIZON, 0)
        if raw_score.ndim != 1 or raw_score.shape[0] != expected_raw_length:
            raise RuntimeError("TASK037A_SCORE_ALIGNMENT_INVALID")
        aligned = np.pad(raw_score, (values.shape[0] - raw_score.shape[0], 0), constant_values=0.0)
        if aligned.shape != values.shape or not np.all(np.isfinite(aligned)):
            raise RuntimeError("TASK037A_SCORE_CONTRACT_INVALID")
        if threshold_source is None:
            threshold_source = aligned.copy()
        threshold = float(np.quantile(threshold_source, 0.95))
        prediction = (aligned > threshold).astype(np.int8)
        scenario_results.append(
            {
                "scenario_id": scenario_id,
                "input_count": int(values.shape[0]),
                "raw_score_count": int(raw_score.shape[0]),
                "aligned_score_count": int(aligned.shape[0]),
                "scores_finite": True,
                "score_sha256": sha256_bytes(aligned.tobytes()),
                "prediction_sha256": sha256_bytes(prediction.tobytes()),
                "prediction_binary": True,
                "predicted_positive_count": int(prediction.sum()),
            }
        )
    return {
        "variant": variant,
        "repeat": repeat,
        "seed": SMOKE_SEED,
        "checkpoint_created": True,
        "checkpoint_sha256": sha256_bytes(checkpoint.read_bytes()),
        "model_state_sha256": _state_hash(method.model),
        "synthetic_threshold_source": "normal_smooth_score_95th_percentile",
        "score_alignment": "official_score_then_explicit_zero_left_pad_to_input_length",
        "source_modified": False,
        "scenarios": scenario_results,
    }


def run_smoke() -> dict[str, Any]:
    import numpy as np
    import sklearn
    import torch

    variants: list[dict[str, Any]] = []
    for variant in ("LSTMADalpha", "LSTMADbeta"):
        first = _run_variant(variant, 1)
        second = _run_variant(variant, 2)
        first_outputs = [(item["score_sha256"], item["prediction_sha256"]) for item in first["scenarios"]]
        second_outputs = [(item["score_sha256"], item["prediction_sha256"]) for item in second["scenarios"]]
        variants.append(
            {
                "variant": variant,
                "fit_repeats": 2,
                "checkpoint_created": first["checkpoint_created"] and second["checkpoint_created"],
                "model_state_hash_stable": first["model_state_sha256"] == second["model_state_sha256"],
                "score_and_prediction_hashes_stable": first_outputs == second_outputs,
                "reproducibility_status": (
                    "detector_byte_reproducible"
                    if first_outputs == second_outputs and first["model_state_sha256"] == second["model_state_sha256"]
                    else "detector_numerically_reproducible_not_byte_identical"
                ),
                "runs": [first, second],
            }
        )
    passed = all(
        item["checkpoint_created"] and item["score_and_prediction_hashes_stable"] for item in variants
    )
    return {
        "status": "passed" if passed else "failed",
        "execution_scope": "synthetic_only",
        "performance_metrics_computed": False,
        "python_version": sys.version.split()[0],
        "torch_version": torch.__version__,
        "numpy_version": np.__version__,
        "scikit_learn_version": sklearn.__version__,
        "variants": variants,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--isolation-probe", action="store_true")
    parser.add_argument("--container-run", action="store_true")
    args = parser.parse_args()
    payload = {"isolation_probe": isolation_probe()} if args.isolation_probe else run_smoke()
    print(stable_json(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
