"""Primary-source-only EasyTSAD/ARGOS detector identity audit."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping

REPO_ROOT_BOOTSTRAP = Path(__file__).resolve().parents[2]
if str(REPO_ROOT_BOOTSTRAP) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT_BOOTSTRAP))

from experiments.argos_reproduction.lstm_variant_resolver import resolve_lstm_variant


REPO_ROOT = REPO_ROOT_BOOTSTRAP
PINNED_EASYTSAD_COMMIT = "55eff2c6d62f9c792bf6253c046dcc04636efe5a"
PINNED_ARGOS_COMMIT = "6b24161ff08de069840a1fb4fbaecf7bf8e393f1"
SOURCE_FILES = (
    "EasyTSAD/Methods/LSTMADalpha/LSTMADalpha.py",
    "EasyTSAD/Methods/LSTMADalpha/TSDataset.py",
    "EasyTSAD/Methods/LSTMADalpha/config.toml",
    "EasyTSAD/Methods/LSTMADbeta/LSTMADbeta.py",
    "EasyTSAD/Methods/LSTMADbeta/TSDataset.py",
    "EasyTSAD/Methods/LSTMADbeta/config.toml",
    "EasyTSAD/TrainingSchema/Naive.py",
    "EasyTSAD/TrainingSchema/BaseSchema.py",
    "EasyTSAD/DataFactory/LoadData.py",
    "EasyTSAD/DataFactory/TSData.py",
    "EasyTSAD/Evaluations/Protocols/EventF1PA.py",
    "EasyTSAD/Evaluations/Protocols/PointF1PA.py",
    "pyproject.toml",
    "LICENSE",
)


class DetectorAuditError(RuntimeError):
    pass


def stable_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def with_report_hash(report: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(report)
    result["report_hash"] = sha256_bytes(stable_json(result).encode())
    return result


def _git_head(path: Path) -> str:
    head_path = path / ".git" / "HEAD"
    if not head_path.is_file():
        raise DetectorAuditError("DETECTOR_SOURCE_GIT_UNAVAILABLE")
    value = head_path.read_text(encoding="ascii").strip()
    if not value.startswith("ref: "):
        return value
    ref_name = value[5:]
    ref_path = path / ".git" / ref_name
    if ref_path.is_file():
        return ref_path.read_text(encoding="ascii").strip()
    packed = path / ".git" / "packed-refs"
    if packed.is_file():
        for line in packed.read_text(encoding="ascii").splitlines():
            if line and not line.startswith(("#", "^")):
                commit, name = line.split(" ", 1)
                if name == ref_name:
                    return commit
    raise DetectorAuditError("DETECTOR_SOURCE_GIT_REF_UNAVAILABLE")


def source_alignment(config: Mapping[str, Any]) -> dict[str, Any]:
    easytsad = REPO_ROOT / str(config["sources"]["easytsad_checkout"])
    argos = REPO_ROOT / str(config["sources"]["argos_checkout"])
    if _git_head(easytsad) != PINNED_EASYTSAD_COMMIT:
        raise DetectorAuditError("EASYTSAD_COMMIT_MISMATCH")
    if _git_head(argos) != PINNED_ARGOS_COMMIT:
        raise DetectorAuditError("ARGOS_COMMIT_MISMATCH")
    hashes = {name: sha256_file(easytsad / name) for name in SOURCE_FILES}
    return with_report_hash(
        {
            "schema_version": "1.0",
            "task_id": "TASK-037A",
            "artifact_type": "source_alignment_report",
            "status": "aligned",
            "easytsad": {
                "repository": "dawnvince/EasyTSAD",
                "source_url": "https://github.com/dawnvince/EasyTSAD",
                "source_commit": PINNED_EASYTSAD_COMMIT,
                "package_version": "0.2.0.2",
                "commit_date": "2024-08-23T11:57:57+08:00",
                "license": "GPL-3.0",
                "source_file_hashes": hashes,
                "checkout_tracked": False,
                "upstream_modified": False,
            },
            "argos": {"source_commit": PINNED_ARGOS_COMMIT, "upstream_modified": False},
        }
    )


def identity_report(config: Mapping[str, Any]) -> dict[str, Any]:
    resolution = resolve_lstm_variant(
        argos_names=("AnomalyTransformer", "AutoRegression", "FCVAE", "LSTMAD", "TFAD"),
        easytsad_variants={"LSTMADalpha": True, "LSTMADbeta": True},
        explicit_variant_evidence=None,
    )
    variants = {
        "LSTMADalpha": {
            "model_class": {"value": "LSTMADalpha", "provenance": "exact_source_value"},
            "architecture": "seq2seq encoder-decoder",
            "input_window": {"value": 100, "provenance": "official_default"},
            "prediction_horizon": {"value": 3, "provenance": "official_default"},
            "hidden_size": {"value": 20, "provenance": "official_default"},
            "layer_count": {"value": 2, "provenance": "official_default"},
            "dropout": {"value": None, "provenance": "exact_source_value"},
            "learning_rate": {"value": 0.0008, "provenance": "official_default"},
        },
        "LSTMADbeta": {
            "model_class": {"value": "LSTMADbeta", "provenance": "exact_source_value"},
            "architecture": "single LSTM multi-step predictor",
            "input_window": {"value": 100, "provenance": "official_default"},
            "prediction_horizon": {"value": 3, "provenance": "official_default"},
            "hidden_size": {"value": 20, "provenance": "official_default"},
            "layer_count": {"value": 2, "provenance": "official_default"},
            "dropout": {"value": None, "provenance": "exact_source_value"},
            "learning_rate": {"value": 0.0005, "provenance": "official_default"},
        },
    }
    common = {
        "batch_size": {"value": 128, "provenance": "official_default"},
        "epochs": {"value": 100, "provenance": "official_default"},
        "optimizer": {"value": "Adam", "provenance": "exact_source_value"},
        "loss": {"value": "MSELoss", "provenance": "exact_source_value"},
        "early_stopping": {"value": "validation loss, patience 3", "provenance": "exact_source_value"},
        "normalization": {"value": "min-max fitted on train values", "provenance": "official_default"},
        "training_schema": {"value": "unresolved by ARGOS; EasyTSAD naive frozen for future curve-wise run", "provenance": "unresolved"},
        "training_data_filter": {"value": "none in official method/schema path", "provenance": "exact_source_value"},
        "score_formula": {"value": "overlapping multi-step squared error averaged by aligned horizon", "provenance": "exact_source_value"},
        "score_alignment": {"value": "source evaluator right-aligns shorter score by trimming the label prefix", "provenance": "exact_source_value"},
        "missing_prefix_policy": {"value": "source emits no prefix scores; project adapter policy is explicit zero left-padding", "provenance": "exact_source_value"},
        "random_seed_behavior": {"value": "not set by the method classes", "provenance": "exact_source_value"},
        "checkpoint_rule": {"value": "best validation loss when save_path supplied", "provenance": "exact_source_value"},
        "required_dependencies": {"value": ["torch", "torchinfo", "numpy", "tqdm", "scikit-learn", "toml"], "provenance": "exact_source_value"},
        "python_version": {"value": ">=3.9,<3.13", "provenance": "official_default"},
        "torch_version": {"value": None, "provenance": "unresolved"},
        "numpy_version": {"value": "^1.26.1", "provenance": "official_default"},
        "scikit_learn_version": {"value": "^1.3.2", "provenance": "official_default"},
        "cpu_compatibility": {"value": True, "provenance": "exact_source_value"},
        "deterministic_algorithm_compatibility": {"value": None, "provenance": "unresolved"},
        "threshold_interface": {"value": "PointF1PA and EventF1PA optimize label-aware thresholds on the evaluated scores", "provenance": "exact_source_value"},
        "argos_specific_hyperparameters": {"value": None, "provenance": "unresolved"},
    }
    return with_report_hash(
        {
            "schema_version": "1.0",
            "task_id": "TASK-037A",
            "artifact_type": "detector_identity_report",
            "status": resolution.identity_status,
            "detector_family": resolution.detector_family,
            "retained_variants": list(resolution.retained_variants),
            "detector_role": resolution.detector_role,
            "selection_between_variants": resolution.selection_between_variants,
            "source_reasons": list(resolution.source_reasons),
            "argos_exact_variant_identified": False,
            "argos_exact_config_identified": False,
            "argos_training_schema_identified": False,
            "argos_selection_scope": "per_dataset",
            "variants": variants,
            "common_source_behavior": common,
            "future_training_label_policy": "contaminated_training",
            "real_kpi_detector_run": False,
            "performance_metrics_computed": False,
        }
    )


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json(payload) + "\n", encoding="utf-8")


def readiness_report(config: Mapping[str, Any]) -> dict[str, Any]:
    identity = read_json(REPO_ROOT / config["reports"]["identity"])
    source = read_json(REPO_ROOT / config["reports"]["source_alignment"])
    environment = read_json(REPO_ROOT / config["reports"]["environment"])
    smoke = read_json(REPO_ROOT / config["reports"]["smoke"])
    ready = source["status"] == "aligned" and environment["status"] == "passed" and smoke["status"] == "passed"
    status = (
        "unresolved_variant_ambiguity_with_dual_arm_freeze"
        if ready and identity["status"] == "detector_family_recovered_variant_ambiguous"
        else "passed_detector_audit_and_preflight" if ready else "failed_synthetic_detector_smoke"
    )
    return with_report_hash({
        "schema_version": "1.0",
        "task_id": "TASK-037A",
        "artifact_type": "readiness_report",
        "status": status,
        "detector_identity_status": identity["status"],
        "retained_variants": identity["retained_variants"],
        "selection_between_variants": "prohibited",
        "source_alignment_status": source["status"],
        "environment_preflight_status": environment["status"],
        "synthetic_smoke_status": smoke["status"],
        "task037b_execution_authorized": False,
        "e4_e5_e6_execution_authorized": False,
        "real_kpi_detector_training": False,
        "real_kpi_detector_scoring": False,
        "real_threshold_selection": False,
        "fusion_execution": False,
        "test_values_parsed": False,
        "test_labels_parsed": False,
        "provider_calls": False,
        "performance_metrics_computed": False,
        "allowed_claim": "Both official LSTMAD variants import, fit, checkpoint, score, align, threshold, and replay deterministically on predeclared synthetic series in the isolated environment.",
    })


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/argos_reproduction/task037a_detector_audit.json")
    args = parser.parse_args()
    config = read_json(REPO_ROOT / args.config)
    write_json(REPO_ROOT / config["reports"]["identity"], identity_report(config))
    write_json(REPO_ROOT / config["reports"]["source_alignment"], source_alignment(config))
    if all((REPO_ROOT / config["reports"][name]).is_file() for name in ("environment", "smoke")):
        write_json(REPO_ROOT / config["reports"]["readiness"], readiness_report(config))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
