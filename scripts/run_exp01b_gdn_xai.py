#!/usr/bin/env python3
"""Freeze the EXP-01B CUDA environment, then run the normal-only experiment.

Importing this module performs no device discovery, file access, or scientific
I/O.  ``freeze-environment`` runs only the preregistered synthetic CUDA smoke.
``run`` replays the committed environment receipt before it resolves the
private HAI capability and opens exactly train1 through train4 once each.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
from importlib import metadata
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import subprocess
import sys
from typing import Any, Callable, Mapping

from paperworks.validation_v2.exp01_scientific_v1 import (
    META_RESULT_HASH,
    PAIR_UNIVERSE,
    STAT_RESULT_HASH,
)
from paperworks.validation_v2.exp01b_backend_v1 import (
    Exp01BDeviceTrainingConfigV1,
    configure_and_smoke_exp01b_backend_v1,
)
from paperworks.validation_v2.exp01b_contract_v1 import (
    ComputeBackend,
    Exp01BEnvironmentFreezeV1,
    REQUIRED_CUBLAS_WORKSPACE_CONFIG,
    REQUIRED_DETERMINISTIC_FLAGS,
    REQUIRED_PYTHONHASHSEED,
    build_environment_freeze_v1,
    preregistration_document_v1,
)
from paperworks.validation_v2.exp01b_runner_v1 import (
    Exp01BScientificInputsV1,
    FormalV4RuleConversionInputV1,
    run_exp01b_v1,
    write_sanitized_exp01b_outputs_v1,
)
from paperworks.validation_v2.hai_feature_adapter_v1 import (
    HAIFeatureAccessLedgerV1,
    load_authorized_hai_feature_frame_for_operations_v1,
    resolve_hai_feature_root_capability_v1,
)
from paperworks.validation_v2.protocol_v1 import (
    ProtocolExecutionGuardV1,
    ProtocolOperationV1,
    build_validation_protocol_v1,
)
from paperworks.v6.common import stable_hash_v1


PUBLIC_ROOT = Path("research_control_center/validation_v2/exp01b_gdn_xai")
ENVIRONMENT_RECEIPT = PUBLIC_ROOT / "environment/EXP01B_GPU_ENVIRONMENT_RECEIPT.json"
PREREGISTRATION = PUBLIC_ROOT / "preregistration/EXP01B_PREREGISTRATION.json"
NORMAL_RECEIPT = PUBLIC_ROOT / "receipts/EXP01B_NORMAL_INPUT_RECEIPTS.json"
PUBLIC_RESULTS = PUBLIC_ROOT / "results"
PRIVATE_CHECKPOINTS = Path("artifacts/validation_v2/exp01b_gdn_xai/private")
META_PATH = Path("docs/task_reports/TASK-039C_META_RESULT.json")
STAT_PATH = Path("docs/task_reports/TASK-039C_STAT_RESULT.json")
V2A_CANDIDATE_AUTHORITY = Path(
    "research_control_center/validation_v2/core_v2a/authorities/"
    "VALIDATION_V2_META_STAT_CANDIDATE_UNION_AUTHORITY_V1.json"
)
V2A_PORTFOLIO_AUTHORITY = Path(
    "research_control_center/validation_v2/core_v2a/authorities/"
    "V2A_FORMAL_V4_PORTFOLIO_AUTHORITY.json"
)
_DRIVE_PATH = re.compile(r"(?i)(?:^|[^A-Za-z0-9_])[A-Z]:[\\/]")


class Exp01BCliError(RuntimeError):
    """Path-safe, fail-closed EXP-01B entrypoint error."""


def _canonical(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        dict(value), sort_keys=True, separators=(",", ":"),
        ensure_ascii=True, allow_nan=False,
    ).encode("utf-8")


def _load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise Exp01BCliError("EXP01B_PUBLIC_AUTHORITY_UNAVAILABLE") from exc
    if type(value) is not dict:
        raise Exp01BCliError("EXP01B_PUBLIC_AUTHORITY_INVALID")
    return value


def _write_new(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = _canonical(value) + b"\n"
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb", closefd=False) as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        os.close(descriptor)
    if path.read_bytes() != payload:
        raise Exp01BCliError("EXP01B_ATOMIC_REOPEN_MISMATCH")


def _head(root: Path) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True,
    ).strip()


def _script_hash() -> str:
    return sha256(Path(__file__).read_bytes()).hexdigest()


def _validate_preregistration(root: Path) -> dict[str, Any]:
    expected = preregistration_document_v1()
    observed = _load_object(root / PREREGISTRATION)
    if observed != expected:
        raise Exp01BCliError("EXP01B_PREREGISTRATION_REPLAY_MISMATCH")
    return observed


def _validate_launch_environment(environment: Mapping[str, str]) -> None:
    if environment.get("CUBLAS_WORKSPACE_CONFIG") != REQUIRED_CUBLAS_WORKSPACE_CONFIG:
        raise Exp01BCliError("EXP01B_CUBLAS_LAUNCH_ENV_MISSING")
    if environment.get("PYTHONHASHSEED") != REQUIRED_PYTHONHASHSEED:
        raise Exp01BCliError("EXP01B_PYTHONHASHSEED_LAUNCH_ENV_MISSING")


def _driver_version() -> str:
    try:
        output = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
            text=True, stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise Exp01BCliError("EXP01B_NVIDIA_DRIVER_RECEIPT_UNAVAILABLE") from exc
    values = tuple(line.strip() for line in output.splitlines() if line.strip())
    if not values:
        raise Exp01BCliError("EXP01B_NVIDIA_DRIVER_RECEIPT_UNAVAILABLE")
    return values[0]


def _environment_payload(
    *, root: Path, torch_module: Any, driver_version: str,
    smoke: Callable[..., Mapping[str, object]] = configure_and_smoke_exp01b_backend_v1,
) -> dict[str, Any]:
    _validate_launch_environment(os.environ)
    _validate_preregistration(root)
    if not bool(torch_module.cuda.is_available()) or int(torch_module.cuda.device_count()) < 1:
        raise Exp01BCliError("EXP01B_CUDA_REQUIRED")
    gpu_model = str(torch_module.cuda.get_device_name(0))
    if "5060" not in gpu_model:
        raise Exp01BCliError("EXP01B_APPROVED_GPU_IDENTITY_MISMATCH")
    config = Exp01BDeviceTrainingConfigV1(device="cuda")
    smoke_result = dict(smoke(torch_module=torch_module, config=config))
    if not bool(smoke_result.get("synthetic_smoke_passed")):
        raise Exp01BCliError("EXP01B_SYNTHETIC_CUDA_SMOKE_FAILED")
    environment = build_environment_freeze_v1(
        backend=ComputeBackend.CUDA,
        python_version=sys.version.split()[0],
        torch_version=str(torch_module.__version__),
        cuda_build=str(torch_module.version.cuda),
        driver_version=driver_version,
        gpu_model=gpu_model,
        deterministic_flags=dict(REQUIRED_DETERMINISTIC_FLAGS),
        synthetic_smoke_passed=True,
        model_device=str(smoke_result.get("model_device")),
        tensor_device=str(smoke_result.get("tensor_device")),
    )
    pyg_version = metadata.version("torch-geometric")
    if pyg_version != "2.8.0":
        raise Exp01BCliError("EXP01B_TORCH_GEOMETRIC_VERSION_MISMATCH")
    body = {
        "schema": "paperworks.validation_v2.exp01b_gpu_environment_receipt_v1",
        "schema_version": "1.0.0",
        "experiment_id": "EXP-01B-GDN-XAI-V1",
        "source_commit": _head(root),
        "runner_script_sha256": _script_hash(),
        "preregistration_hash": preregistration_document_v1()["preregistration_hash"],
        "environment": {**environment.body_document(), "environment_hash": environment.environment_hash},
        "torch_geometric_version": pyg_version,
        "synthetic_only": True,
        "scientific_data_accesses": 0,
        "test1_accesses": 0,
        "label_accesses": 0,
        "test2_accesses": 0,
        "heldout_accesses": 0,
        "private_paths_embedded": False,
    }
    return {**body, "receipt_hash": stable_hash_v1(body)}


def freeze_environment(root: Path) -> None:
    import torch

    receipt = _environment_payload(
        root=root, torch_module=torch, driver_version=_driver_version(),
    )
    _write_new(root / ENVIRONMENT_RECEIPT, receipt)


def _environment_from_receipt(
    document: Mapping[str, Any], *, preregistration_hash: str,
    runner_script_sha256: str, source_is_ancestor: bool,
) -> Exp01BEnvironmentFreezeV1:
    body = {key: value for key, value in document.items() if key != "receipt_hash"}
    if document.get("receipt_hash") != stable_hash_v1(body):
        raise Exp01BCliError("EXP01B_ENVIRONMENT_RECEIPT_SELF_HASH_MISMATCH")
    if (
        document.get("preregistration_hash") != preregistration_hash
        or document.get("runner_script_sha256") != runner_script_sha256
        or document.get("torch_geometric_version") != "2.8.0"
        or not source_is_ancestor
        or document.get("synthetic_only") is not True
        or any(document.get(key) != 0 for key in (
            "scientific_data_accesses", "test1_accesses", "label_accesses",
            "test2_accesses", "heldout_accesses",
        ))
        or document.get("private_paths_embedded") is not False
    ):
        raise Exp01BCliError("EXP01B_ENVIRONMENT_RECEIPT_BINDING_MISMATCH")
    item = document.get("environment")
    if type(item) is not dict or item.get("backend") != "cuda":
        raise Exp01BCliError("EXP01B_NON_CUDA_ENVIRONMENT_REJECTED")
    environment = build_environment_freeze_v1(
        backend=ComputeBackend.CUDA,
        python_version=str(item.get("python_version")),
        torch_version=str(item.get("torch_version")),
        cuda_build=str(item.get("cuda_build")),
        driver_version=str(item.get("driver_version")),
        gpu_model=str(item.get("gpu_model")),
        deterministic_flags=dict(item.get("deterministic_flags", {})),
        synthetic_smoke_passed=bool(item.get("synthetic_smoke_passed")),
        model_device=str(item.get("model_device")),
        tensor_device=str(item.get("tensor_device")),
        cublas_workspace_config=str(item.get("cublas_workspace_config")),
        pythonhashseed=str(item.get("pythonhashseed")),
        process_launch_verified=bool(item.get("process_launch_verified")),
        functional_variant_chunk_size=int(item.get("functional_variant_chunk_size", 0)),
    )
    if item.get("environment_hash") != environment.environment_hash:
        raise Exp01BCliError("EXP01B_ENVIRONMENT_IDENTITY_MISMATCH")
    return environment


def _assert_live_environment_matches_receipt(
    *, document: Mapping[str, Any], environment: Exp01BEnvironmentFreezeV1,
    torch_module: Any,
) -> None:
    """Fail before scientific I/O if the live backend differs from its receipt."""

    _validate_launch_environment(os.environ)
    item = document.get("environment")
    if type(item) is not dict:
        raise Exp01BCliError("EXP01B_ENVIRONMENT_RECEIPT_INVALID")
    if (
        not bool(torch_module.cuda.is_available())
        or int(torch_module.cuda.device_count()) < 1
        or str(torch_module.__version__) != environment.torch_version
        or str(torch_module.version.cuda) != environment.cuda_build
        or str(torch_module.cuda.get_device_name(0)) != environment.gpu_model
        or _driver_version() != environment.driver_version
        or metadata.version("torch-geometric") != document.get("torch_geometric_version")
    ):
        raise Exp01BCliError("EXP01B_LIVE_ENVIRONMENT_MISMATCH")
    smoke = configure_and_smoke_exp01b_backend_v1(
        torch_module=torch_module,
        config=Exp01BDeviceTrainingConfigV1(device="cuda"),
    )
    if (
        smoke.get("synthetic_smoke_passed") is not True
        or smoke.get("scientific_training_config_hash")
        != Exp01BDeviceTrainingConfigV1(device="cuda").hyperparameter_hash
        or smoke.get("model_device") != "cuda"
        or smoke.get("tensor_device") != "cuda"
    ):
        raise Exp01BCliError("EXP01B_LIVE_SYNTHETIC_SMOKE_MISMATCH")


def _source_is_ancestor(root: Path, source_commit: object) -> bool:
    if type(source_commit) is not str or len(source_commit) != 40:
        return False
    return subprocess.run(
        ["git", "merge-base", "--is-ancestor", source_commit, "HEAD"],
        cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ).returncode == 0


def _replay_environment(
    root: Path, preregistration_hash: str,
) -> tuple[dict[str, Any], Exp01BEnvironmentFreezeV1]:
    document = _load_object(root / ENVIRONMENT_RECEIPT)
    environment = _environment_from_receipt(
        document,
        preregistration_hash=preregistration_hash,
        runner_script_sha256=_script_hash(),
        source_is_ancestor=_source_is_ancestor(root, document.get("source_commit")),
    )
    return document, environment


def _pair(row: Mapping[str, Any], *, meta: bool) -> tuple[str, str]:
    source_key, target_key = ("source_identity", "target_identity") if meta else ("source", "target")
    pair = (str(row.get(source_key)), str(row.get(target_key)))
    if pair not in PAIR_UNIVERSE:
        raise Exp01BCliError("EXP01B_RANKING_PAIR_OUTSIDE_UNIVERSE")
    return pair


def _authority_hash_replays(document: Mapping[str, Any], field: str) -> bool:
    expected = document.get(field)
    body = {key: value for key, value in document.items() if key != field}
    return type(expected) is str and expected == sha256(_canonical(body)).hexdigest()


def _load_rankings_and_conversion(
    root: Path,
) -> tuple[tuple[tuple[str, str], ...], tuple[tuple[str, str], ...], FormalV4RuleConversionInputV1]:
    meta = _load_object(root / META_PATH)
    stat = _load_object(root / STAT_PATH)
    candidate = _load_object(root / V2A_CANDIDATE_AUTHORITY)
    portfolio = _load_object(root / V2A_PORTFOLIO_AUTHORITY)
    if meta.get("artifact_hash") != META_RESULT_HASH or stat.get("artifact_hash") != STAT_RESULT_HASH:
        raise Exp01BCliError("EXP01B_META_STAT_AUTHORITY_MISMATCH")
    meta_rows, stat_rows = meta.get("top20_identities"), stat.get("top20")
    if type(meta_rows) is not list or type(stat_rows) is not list or len(meta_rows) != 20 or len(stat_rows) != 20:
        raise Exp01BCliError("EXP01B_META_STAT_TOP20_MISSING")
    meta_ranking = tuple(_pair(row, meta=True) for row in meta_rows)
    stat_ranking = tuple(_pair(row, meta=False) for row in stat_rows)
    union = tuple(sorted(set(meta_ranking) | set(stat_ranking)))
    candidate_rows = candidate.get("candidates")
    candidate_pairs = tuple(sorted(
        (str(row.get("source")), str(row.get("target"))) for row in candidate_rows
    )) if type(candidate_rows) is list else ()
    if (
        candidate.get("artifact_type") != "validation_v2a_meta_stat_candidate_union_authority_v1"
        or not _authority_hash_replays(candidate, "authority_hash")
        or candidate.get("meta_artifact_hash") != META_RESULT_HASH
        or candidate.get("stat_artifact_hash") != STAT_RESULT_HASH
        or candidate_pairs != union
        or len(union) != 29
        or candidate.get("labels_accessed") is not False
        or candidate.get("test1_accessed") is not False
        or candidate.get("test2_accessed") is not False
    ):
        raise Exp01BCliError("EXP01B_V2A_CANDIDATE_AUTHORITY_REPLAY_FAILED")
    descriptors = portfolio.get("descriptors")
    if (
        portfolio.get("artifact_type") != "validation_v2_formal_v4_portfolio_authority_v1"
        or not _authority_hash_replays(portfolio, "authority_hash")
        or portfolio.get("authority_family") != "FORMAL_V4"
        or portfolio.get("canonical_to_v4_bridge_used") is not False
        or type(descriptors) is not list
    ):
        raise Exp01BCliError("EXP01B_V2A_FORMAL_V4_AUTHORITY_REPLAY_FAILED")
    executable = tuple(sorted(set(
        (str(item.get("source")), str(item.get("target"))) for item in descriptors
    )))
    conversion = FormalV4RuleConversionInputV1(
        authority_hash=str(portfolio["authority_hash"]), executable_pairs=executable,
    )
    return meta_ranking, stat_ranking, conversion


def _load_normal_inputs(
    root: Path, *, source_commit: str,
    capability_resolver: Callable[[Path], Any] = resolve_hai_feature_root_capability_v1,
    frame_loader: Callable[..., Any] = load_authorized_hai_feature_frame_for_operations_v1,
) -> tuple[Exp01BScientificInputsV1, dict[str, Any]]:
    protocol = build_validation_protocol_v1(source_commit=source_commit)
    guard = ProtocolExecutionGuardV1(protocol)
    ledger = HAIFeatureAccessLedgerV1(experiment_id="EXP-01B-GDN-XAI-V1")
    capability = capability_resolver(root)
    operations = {
        "train1": (ProtocolOperationV1.CANDIDATE_LEARNING, ProtocolOperationV1.RELATION_FIT),
        "train2": (ProtocolOperationV1.CANDIDATE_LEARNING, ProtocolOperationV1.RELATION_FIT),
        "train3": (ProtocolOperationV1.RELATION_CONFIRMATION,),
        "train4": (ProtocolOperationV1.NORMAL_SANITY,),
    }
    frames: dict[str, Any] = {}
    receipts: dict[str, dict[str, Any]] = {}
    for split in ("train1", "train2", "train3", "train4"):
        frame = frame_loader(
            capability=capability, split_id=split, operations=operations[split],
            protocol_guard=guard, ledger=ledger,
        )
        frames[split] = frame
        receipt = frame.receipt.to_dict()
        if (
            receipt.get("split_id") != split
            or receipt.get("file_open_count") != 1
            or receipt.get("labels_accessed") is not False
            or receipt.get("test2_accesses") != 0
            or receipt.get("heldout_accesses") != 0
        ):
            raise Exp01BCliError("EXP01B_NORMAL_READ_RECEIPT_REJECTED")
        receipts[split] = receipt
    inputs = Exp01BScientificInputsV1(
        train1=frames["train1"].numeric_matrix(),
        train2=frames["train2"].numeric_matrix(),
        train3=frames["train3"].numeric_matrix(),
        train4=frames["train4"].numeric_matrix(),
        receipt_hashes={split: str(receipts[split]["receipt_hash"]) for split in receipts},
    )
    body = {
        "schema": "paperworks.validation_v2.exp01b_normal_input_receipts_v1",
        "schema_version": "1.0.0",
        "experiment_id": "EXP-01B-GDN-XAI-V1",
        "splits": receipts,
        "access_ledger": ledger.public_document(),
        "split_open_counts": {split: 1 for split in receipts},
        "test1_accesses": 0,
        "label_accesses": 0,
        "test2_accesses": 0,
        "heldout_accesses": 0,
        "private_paths_embedded": False,
    }
    return inputs, {**body, "receipt_hash": stable_hash_v1(body)}


def _contains_private_path(value: object) -> bool:
    if isinstance(value, Mapping):
        return any(_contains_private_path(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_private_path(item) for item in value)
    if not isinstance(value, str):
        return False
    return (
        bool(_DRIVE_PATH.search(value))
        or PureWindowsPath(value).is_absolute()
        or PurePosixPath(value).is_absolute()
        or value.startswith("~")
    )


def _assert_public_document_safe(document: Mapping[str, Any]) -> None:
    if _contains_private_path(document):
        raise Exp01BCliError("EXP01B_PRIVATE_PATH_IN_PUBLIC_OUTPUT")


def run(root: Path) -> None:
    preregistration = _validate_preregistration(root)
    environment_document, environment = _replay_environment(
        root, str(preregistration["preregistration_hash"]),
    )
    import torch

    _assert_live_environment_matches_receipt(
        document=environment_document, environment=environment, torch_module=torch,
    )
    meta_ranking, stat_ranking, conversion = _load_rankings_and_conversion(root)
    source_commit = _head(root)
    scientific_inputs, input_receipt = _load_normal_inputs(root, source_commit=source_commit)
    _assert_public_document_safe(input_receipt)
    _write_new(root / NORMAL_RECEIPT, input_receipt)
    result = run_exp01b_v1(
        scientific_inputs=scientific_inputs,
        environment=environment,
        private_checkpoint_root=(root / PRIVATE_CHECKPOINTS).resolve(),
        meta_ranking=meta_ranking,
        stat_ranking=stat_ranking,
        rule_conversion=conversion,
        torch_module=torch,
    )
    _assert_public_document_safe(result.public_document)
    write_sanitized_exp01b_outputs_v1(
        result=result, output_root=(root / PUBLIC_RESULTS).resolve(),
    )
    for path in (root / PUBLIC_ROOT).rglob("*"):
        if path.is_file() and path.suffix.lower() in {".json", ".csv"}:
            text = path.read_text(encoding="utf-8")
            if _DRIVE_PATH.search(text) or "artifacts/validation_v2/exp01b_gdn_xai/private" in text:
                raise Exp01BCliError("EXP01B_PRIVATE_PATH_IN_PUBLIC_OUTPUT")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("freeze-environment", "run"))
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    root = args.repository_root.resolve(strict=True)
    if args.phase == "freeze-environment":
        freeze_environment(root)
    else:
        run(root)


if __name__ == "__main__":
    main()
