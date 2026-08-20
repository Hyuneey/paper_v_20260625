"""Independent integrity audit for the frozen D0 PCA-SPE model/threshold.

This audit never imports or calls the authoritative D0 training module. Public
Git/artifact checks and private numeric reconstruction are separated. Private
paths and numeric arrays are never included in returned or printed results.
"""

from __future__ import annotations

import argparse
import csv
from hashlib import sha256
import io
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import subprocess
from typing import Any, Mapping, NoReturn, Sequence


TASK_ID = "TASK-039E3-R2R-UTILITY-INNER-D0-DETECTOR-MODEL-THRESHOLD-INTEGRITY-AUDIT-V1"
BASE_COMMIT = "7ca7c035f1ec5b1fa6950fcfbdb9167d7d958517"
TRAINING_COMMIT_A = "34edab1dc148fdd82a050c3446e87d6eda4f95fe"
INDEPENDENT_COMMIT_B = "1041b6ed1efc335b8f5c5fe50dbfc22a87ec6d44"
FREEZE_COMMIT_C = "44ce989d7f50e2722eed70963e030ba1ba44fadf"

DETECTOR_ID = "D0_PCA_SPE_V1"
DESIGN_HASH = "357d19d02dee73273d52c7b147b5ddcfa11ead43a7198f2bf089ec78c2d8e174"
FEATURE_SET_HASH = "6dea06e82c0d99f35a0d11c5e97503e8bb3a0fc8c1d9963b997986021fd23515"
FEATURE_ORDER_HASH = "a612bdb9850ad0dd865dc62b23199bf2b696452c492e4aabe09fe554fa246d57"
PREPROCESSING_HASH = "baae5495094b211731e4fcdf7bab2870e3c81e7c973bfe052fc87b457ccb6270"
MODEL_HASH = "f32943cc2172100c77514d9ce8f6731978b51934e753234b2d34b5154127b54b"
THRESHOLD_HASH = "7ac0628cad5983b9864d31a9984bd414867b80f175248dbdf5cd69d7589f3695"

MODEL_RECEIPT_HASH = "913f4a4bcf1771146f9493cded893b10eb97d2d177fe224f855c289d81ef1362"
THRESHOLD_RECEIPT_HASH = "2ee6fc8aba25d23449c14b08deae2eca0c5b739f6a251e43ead41923c978d326"
TRAIN4_SANITY_HASH = "fb58290c1a59d164d9ace673968910db0f8ab65331ef3dfacd837c39685921ee"
ACCOUNTING_HASH = "ca7f038c1c91b24feee38101c9d8b19cfe97a3dc417c32cee879f47942eed5f4"
READINESS_HASH = "fcba1018b1e42ff7fdda9467a02a4f902ec6803486a3847675752508537cda29"
BUNDLE_HASH = "fa041f5e0006fc56665d22c82eb0fdea51917e573ffc4946c8a3f83bf4ada1e6"
RECEIPT_HASH = "b4142789cbe99513c1763df15e0207588b75453829d2abe1aba4eaa60da75357"
DESIGN_REPORT_HASH = "3ffcec30d2bc605bf0b4ca15f80fcc3ed40aa283b6ae913e767c0ad9db18ece7"
FEATURE_SCOPE_HASH = "4e9ba5a52733ae00f8cf755cda9918667c7065e0bc5b6eed2712aab97c3d6dd0"
DESIGN_CONFIG_HASH = "b931c872688117365f2d4418bd7e521a8cd281455eb92927d32d11276f621713"

PYTHON_VERSION = "3.12.13"
NUMPY_VERSION = "2.3.5"
FEATURE_COUNT = 37
FIT_ROWS = 572_400
SCALE_FLOOR = 1e-12
VARIANCE_TARGET = 0.95
ALPHA = 0.001
EXPECTED_K = 10
EXPECTED_RESIDUAL_DIMENSIONS = 27
EXPECTED_Q_INDEX = 125_873
EXPECTED_TRAIN4_POINT_ALARMS = 15_401
EXPECTED_TRAIN4_EPISODES = 479
EXPECTED_TRAIN4_FAR = 8.709090909090909
NEGATIVE_EIGENVALUE_EPSILON_MULTIPLIER = 64

P1_FEATURE_ORDER = (
    "P1_FCV01D", "P1_FCV01Z", "P1_FCV02D", "P1_FCV02Z", "P1_FCV03D",
    "P1_FCV03Z", "P1_FT01", "P1_FT01Z", "P1_FT02", "P1_FT02Z",
    "P1_FT03", "P1_FT03Z", "P1_LCV01D", "P1_LCV01Z", "P1_LIT01",
    "P1_PCV01D", "P1_PCV01Z", "P1_PCV02D", "P1_PCV02Z", "P1_PIT01",
    "P1_PIT01_HH", "P1_PIT02", "P1_PP01AD", "P1_PP01AR", "P1_PP01BD",
    "P1_PP01BR", "P1_PP02D", "P1_PP02R", "P1_PP04", "P1_PP04D",
    "P1_PP04SP", "P1_SOL01D", "P1_SOL03D", "P1_STSP", "P1_TIT01",
    "P1_TIT02", "P1_TIT03",
)

NORMAL_FILES = (
    ("hai-23.05/hai-train1.csv", "53007b0ba604fbf338e7ac2e08cd81d874b5d1388f3aecb213ddcba5bf2bec4a", 162_418_984, 280_800),
    ("hai-23.05/hai-train2.csv", "0e520e82bf78a661ab19ce4967f3c766bd809820f457a9c90c365102d4534c56", 169_121_615, 291_600),
    ("hai-23.05/hai-train3.csv", "bfcec2dc05adea103e7491546b0e28268faaa26d3cc717d10f4595c94b81e85d", 72_774_793, 126_000),
    ("hai-23.05/hai-train4.csv", "56658c83657d42a65db982b864362e0d0ffeb96d1f7b357d5e76e3a5c522d940", 114_494_940, 198_000),
)

PUBLIC_REPORTS = {
    "implementation_audit": ("TASK-039E3_R2R_UTILITY_INNER_D0_TRAINING_V1_IMPLEMENTATION_AUDIT.json", "545a9082e84dd350dfc2df941f70021932879e73020462cdb76075b6c20d58a5"),
    "model_receipt": ("TASK-039E3_R2R_UTILITY_INNER_D0_TRAINING_V1_MODEL_RECEIPT.json", MODEL_RECEIPT_HASH),
    "threshold_receipt": ("TASK-039E3_R2R_UTILITY_INNER_D0_TRAINING_V1_THRESHOLD_RECEIPT.json", THRESHOLD_RECEIPT_HASH),
    "train4_sanity": ("TASK-039E3_R2R_UTILITY_INNER_D0_TRAINING_V1_TRAIN4_SANITY.json", TRAIN4_SANITY_HASH),
    "accounting": ("TASK-039E3_R2R_UTILITY_INNER_D0_TRAINING_V1_ACCOUNTING.json", ACCOUNTING_HASH),
    "readiness": ("TASK-039E3_R2R_UTILITY_INNER_D0_TRAINING_V1_READINESS.json", READINESS_HASH),
    "bundle": ("TASK-039E3_R2R_UTILITY_INNER_D0_TRAINING_V1_BUNDLE.json", BUNDLE_HASH),
    "receipt": ("TASK-039E3_R2R_UTILITY_INNER_D0_TRAINING_V1_RECEIPT.json", RECEIPT_HASH),
}

COMMIT_A_FILES = frozenset({
    "TASKS/TASK-039E3-R2R-UTILITY-INNER-D0-DETECTOR-NORMAL-TRAINING-AND-CALIBRATION-V1.md",
    "scripts/local/materialize_hai_d0_normal_payload_v1.py",
    "src/paperworks/v6/task039e3_r2r_d0_detector_training_v1.py",
    "tests/test_task039e3_r2r_d0_detector_training_v1.py",
})
COMMIT_B_FILES = frozenset({"tests/test_task039e3_r2r_d0_detector_training_v1_independent.py"})
COMMIT_C_FILES = frozenset({f"docs/task_reports/{name}" for name, _ in PUBLIC_REPORTS.values()} | {"docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_TRAINING_V1_REPORT.md"})
COMMIT_D_FILES = frozenset({
    "docs/project_state/CURRENT_STATE.md", "docs/project_state/CURRENT_STATE.json",
    "docs/project_state/AUTHORITY_INDEX.md", "docs/project_state/TASK_LEDGER.md",
    "docs/project_state/HANDOFF.md",
})

_FAILURE_CODES = frozenset({
    "D0_INTEGRITY_AUDIT_BLOCKED_PUBLIC_CUSTODY",
    "D0_INTEGRITY_AUDIT_BLOCKED_PRIVATE_CUSTODY",
    "D0_INTEGRITY_AUDIT_BLOCKED_NORMAL_INPUT",
    "D0_INTEGRITY_AUDIT_BLOCKED_PREPROCESSING",
    "D0_INTEGRITY_AUDIT_BLOCKED_PCA",
    "D0_INTEGRITY_AUDIT_BLOCKED_THRESHOLD",
    "D0_INTEGRITY_AUDIT_BLOCKED_TRAIN4",
    "D0_INTEGRITY_AUDIT_BLOCKED_LEAKAGE",
    "D0_INTEGRITY_AUDIT_BLOCKED_UNEXPECTED",
})


class D0IntegrityAuditError(RuntimeError):
    def __init__(self, code: str) -> None:
        self.code = code if code in _FAILURE_CODES else "D0_INTEGRITY_AUDIT_BLOCKED_UNEXPECTED"
        super().__init__(self.code)


def _fail(code: str) -> NoReturn:
    raise D0IntegrityAuditError(code)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def canonical_hash_v1(document: Mapping[str, Any], field: str = "artifact_hash") -> str:
    payload = dict(document)
    payload.pop(field, None)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    return sha256(encoded).hexdigest()


def _git(arguments: Sequence[str]) -> bytes:
    try:
        completed = subprocess.run(
            ("git", *arguments), cwd=_repo_root(), stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, check=False,
        )
        if completed.returncode != 0:
            _fail("D0_INTEGRITY_AUDIT_BLOCKED_PUBLIC_CUSTODY")
        return completed.stdout
    except D0IntegrityAuditError:
        raise
    except BaseException:
        _fail("D0_INTEGRITY_AUDIT_BLOCKED_PUBLIC_CUSTODY")


def _git_text(arguments: Sequence[str]) -> str:
    try:
        return _git(arguments).decode("utf-8").strip()
    except D0IntegrityAuditError:
        raise
    except BaseException:
        _fail("D0_INTEGRITY_AUDIT_BLOCKED_PUBLIC_CUSTODY")


def _commit_files(commit: str) -> frozenset[str]:
    output = _git_text(("diff-tree", "--no-commit-id", "--name-only", "-r", commit))
    return frozenset(line for line in output.splitlines() if line)


def _load_public_reports() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    base = _repo_root() / "docs/task_reports"
    try:
        for key, (name, expected_hash) in PUBLIC_REPORTS.items():
            path = base / name
            if path.is_symlink() or not path.is_file():
                _fail("D0_INTEGRITY_AUDIT_BLOCKED_PUBLIC_CUSTODY")
            document = json.loads(path.read_text(encoding="utf-8"))
            if type(document) is not dict or document.get("artifact_hash") != expected_hash or canonical_hash_v1(document) != expected_hash:
                _fail("D0_INTEGRITY_AUDIT_BLOCKED_PUBLIC_CUSTODY")
            result[key] = document
        return result
    except D0IntegrityAuditError:
        raise
    except BaseException:
        _fail("D0_INTEGRITY_AUDIT_BLOCKED_PUBLIC_CUSTODY")


def _validate_public_cross_hashes(documents: Mapping[str, Mapping[str, Any]]) -> None:
    i, m, t, s, a, r, b, c = (documents[key] for key in (
        "implementation_audit", "model_receipt", "threshold_receipt", "train4_sanity",
        "accounting", "readiness", "bundle", "receipt",
    ))
    conditions = (
        m.get("implementation_audit_hash") == i.get("artifact_hash"),
        t.get("model_receipt_hash") == m.get("artifact_hash"),
        s.get("threshold_receipt_hash") == t.get("artifact_hash"),
        r.get("accounting_hash") == a.get("artifact_hash"),
        r.get("model_receipt_hash") == m.get("artifact_hash"),
        r.get("threshold_receipt_hash") == t.get("artifact_hash"),
        r.get("train4_sanity_hash") == s.get("artifact_hash"),
        b.get("readiness_hash") == r.get("artifact_hash"),
        b.get("accounting_hash") == a.get("artifact_hash"),
        c.get("bundle_hash") == b.get("artifact_hash"),
        c.get("readiness_hash") == r.get("artifact_hash"),
        c.get("model_content_hash") == MODEL_HASH,
        c.get("threshold_content_hash") == THRESHOLD_HASH,
    )
    if not all(conditions):
        _fail("D0_INTEGRITY_AUDIT_BLOCKED_PUBLIC_CUSTODY")


def validate_frozen_public_semantics_v1(documents: Mapping[str, Mapping[str, Any]]) -> None:
    model = documents["model_receipt"]
    threshold = documents["threshold_receipt"]
    sanity = documents["train4_sanity"]
    accounting = documents["accounting"]
    if (
        model.get("d0_design_hash") != DESIGN_HASH
        or model.get("feature_count") != FEATURE_COUNT
        or model.get("feature_set_hash") != FEATURE_SET_HASH
        or model.get("feature_order_hash") != FEATURE_ORDER_HASH
        or model.get("preprocessing_content_hash") != PREPROCESSING_HASH
        or model.get("model_content_hash") != MODEL_HASH
        or model.get("selected_k") != EXPECTED_K
        or model.get("residual_dimensions") != EXPECTED_RESIDUAL_DIMENSIONS
        or model.get("exact_tied_cutoff_encountered") is not False
        or threshold.get("d0_design_hash") != DESIGN_HASH
        or threshold.get("model_content_hash") != MODEL_HASH
        or threshold.get("threshold_content_hash") != THRESHOLD_HASH
        or threshold.get("alpha") != ALPHA
        or threshold.get("q_index") != EXPECTED_Q_INDEX
        or threshold.get("comparison_operator") != "score > threshold"
        or sanity.get("point_alarm_count") != EXPECTED_TRAIN4_POINT_ALARMS
        or sanity.get("alarm_episode_count") != EXPECTED_TRAIN4_EPISODES
        or sanity.get("normal_far_episodes_per_hour") != EXPECTED_TRAIN4_FAR
        or sanity.get("result_driven_change") is not False
        or accounting.get("model_fit_attempts") != 1
        or accounting.get("model_fit_retries") != 0
        or accounting.get("threshold_calibration_attempts") != 1
        or accounting.get("threshold_calibration_retries") != 0
        or accounting.get("train1_scientific_parses") != 1
        or accounting.get("train2_scientific_parses") != 1
        or accounting.get("train3_scientific_parses") != 1
        or accounting.get("train4_scientific_parses") != 1
        or accounting.get("test1_accesses") != 0
        or accounting.get("label_accesses") != 0
        or accounting.get("test2_accesses") != 0
        or accounting.get("d0_inner_executions") != 0
        or accounting.get("d2_executions") != 0
        or accounting.get("outer_executions") != 0
        or accounting.get("d1_performance_reads") != 0
        or accounting.get("result_driven_changes") is not False
    ):
        _fail("D0_INTEGRITY_AUDIT_BLOCKED_PUBLIC_CUSTODY")


def _public_leakage_pass() -> bool:
    base = _repo_root() / "docs/task_reports"
    text = "\n".join((base / name).read_text(encoding="utf-8") for name, _ in PUBLIC_REPORTS.values())
    text += "\n" + (base / "TASK-039E3_R2R_UTILITY_INNER_D0_TRAINING_V1_REPORT.md").read_text(encoding="utf-8")
    if re.search(r"(?:[A-Za-z]:\\Users\\|/home/|/Users/)", text):
        return False
    forbidden = (
        "means_float_hex", "scales_float_hex", "retained_loadings_float_hex",
        "eigenvalues_float_hex", "threshold_float_hex", "raw_scores",
        "label_vector", "cache_path",
    )
    return not any(token in text for token in forbidden)


def run_public_audit_v1() -> dict[str, Any]:
    if _git_text(("merge-base", "--is-ancestor", BASE_COMMIT, "HEAD")):
        _fail("D0_INTEGRITY_AUDIT_BLOCKED_PUBLIC_CUSTODY")
    chain = ((TRAINING_COMMIT_A, INDEPENDENT_COMMIT_B), (INDEPENDENT_COMMIT_B, FREEZE_COMMIT_C), (FREEZE_COMMIT_C, BASE_COMMIT))
    for parent, child in chain:
        if _git_text(("rev-parse", f"{child}^")) != parent:
            _fail("D0_INTEGRITY_AUDIT_BLOCKED_PUBLIC_CUSTODY")
    if _commit_files(TRAINING_COMMIT_A) != COMMIT_A_FILES or _commit_files(INDEPENDENT_COMMIT_B) != COMMIT_B_FILES or _commit_files(FREEZE_COMMIT_C) != COMMIT_C_FILES or _commit_files(BASE_COMMIT) != COMMIT_D_FILES:
        _fail("D0_INTEGRITY_AUDIT_BLOCKED_PUBLIC_CUSTODY")
    for path in COMMIT_C_FILES:
        current = (_repo_root() / PurePosixPath(path)).read_bytes()
        if current != _git(("show", f"{FREEZE_COMMIT_C}:{path}")):
            _fail("D0_INTEGRITY_AUDIT_BLOCKED_PUBLIC_CUSTODY")
    production_path = "src/paperworks/v6/task039e3_r2r_d0_detector_training_v1.py"
    current_source = (_repo_root() / production_path).read_bytes()
    commit_source = _git(("show", f"{TRAINING_COMMIT_A}:{production_path}"))
    if current_source != commit_source:
        _fail("D0_INTEGRITY_AUDIT_BLOCKED_PUBLIC_CUSTODY")
    source_sha = sha256(current_source).hexdigest()
    source_blob = _git_text(("rev-parse", f"{TRAINING_COMMIT_A}:{production_path}"))
    source_text = current_source.decode("utf-8")
    forbidden_source_tokens = (
        "hai-test1.csv", "label-test1.csv", "hai-test2.csv", "label-test2.csv",
        "D1_METRICS_V1.json", "D1_RULE_PREDICTION_ARTIFACT_V1.json",
        "sklearn", "torch", "scipy", "randomized_svd",
    )
    if any(token in source_text for token in forbidden_source_tokens) or "np.linalg.eigh" not in source_text:
        _fail("D0_INTEGRITY_AUDIT_BLOCKED_PUBLIC_CUSTODY")

    design_report_path = _repo_root() / "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_DETECTOR_DESIGN_V1_DESIGN.json"
    feature_scope_path = _repo_root() / "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_DETECTOR_DESIGN_V1_FEATURE_SCOPE.json"
    config_path = _repo_root() / "configs/v6/task039e3_r2r_d0_pca_spe_detector_v1.json"
    design_report = json.loads(design_report_path.read_text(encoding="utf-8"))
    feature_scope = json.loads(feature_scope_path.read_text(encoding="utf-8"))
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if (
        canonical_hash_v1(design_report) != DESIGN_REPORT_HASH
        or design_report.get("artifact_hash") != DESIGN_REPORT_HASH
        or canonical_hash_v1(feature_scope) != FEATURE_SCOPE_HASH
        or feature_scope.get("artifact_hash") != FEATURE_SCOPE_HASH
        or canonical_hash_v1(config, "config_hash") != DESIGN_CONFIG_HASH
        or config.get("config_hash") != DESIGN_CONFIG_HASH
        or design_report.get("d0_detector_design_hash") != DESIGN_HASH
        or feature_scope.get("feature_count") != FEATURE_COUNT
        or feature_scope.get("ordered_features") != list(P1_FEATURE_ORDER)
        or feature_scope.get("feature_set_hash") != FEATURE_SET_HASH
        or feature_scope.get("feature_order_hash") != FEATURE_ORDER_HASH
    ):
        _fail("D0_INTEGRITY_AUDIT_BLOCKED_PUBLIC_CUSTODY")

    report_path = _repo_root() / "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_TRAINING_V1_REPORT.md"
    report_text = report_path.read_text(encoding="utf-8")
    report_match = re.search(r"Report artifact hash: `([0-9a-f]{64})`", report_text)
    if report_match is None:
        _fail("D0_INTEGRITY_AUDIT_BLOCKED_PUBLIC_CUSTODY")
    report_preimage = report_text[:report_match.start(1)] + "PENDING" + report_text[report_match.end(1):]
    if sha256(report_preimage.encode("utf-8")).hexdigest() != report_match.group(1):
        _fail("D0_INTEGRITY_AUDIT_BLOCKED_PUBLIC_CUSTODY")
    documents = _load_public_reports()
    _validate_public_cross_hashes(documents)
    validate_frozen_public_semantics_v1(documents)
    if not _public_leakage_pass():
        _fail("D0_INTEGRITY_AUDIT_BLOCKED_LEAKAGE")
    return {
        "frozen_result_commit_verified": True,
        "post_freeze_mutation_count": 0,
        "production_changes_after_commit_a": 0,
        "d0_design_hash_match": True,
        "implementation_source_sha256": source_sha,
        "implementation_git_blob": source_blob,
        "training_implementation_hash_match": True,
        "design_replay_match": True,
        "markdown_self_hash_match": True,
        "public_receipts_self_hash_match": True,
        "public_receipts_cross_hash_match": True,
        "public_leakage_pass": True,
        "original_model_fit_attempts": 1,
        "original_model_fit_retries": 0,
        "original_threshold_calibration_attempts": 1,
        "original_threshold_calibration_retries": 0,
        "result_driven_changes": False,
        "test1_accesses": 0,
        "label_accesses": 0,
        "test2_accesses": 0,
        "d1_performance_reads": 0,
    }


def _np() -> Any:
    try:
        import numpy as np
    except BaseException:
        _fail("D0_INTEGRITY_AUDIT_BLOCKED_UNEXPECTED")
    if str(np.__version__) != NUMPY_VERSION or platform.python_version() != PYTHON_VERSION:
        _fail("D0_INTEGRITY_AUDIT_BLOCKED_PRIVATE_CUSTODY")
    return np


def independent_preprocessing_oracle_v1(train1: Any, train2: Any) -> tuple[Any, Any, Any]:
    np = _np()
    for matrix in (train1, train2):
        if type(matrix) is not np.ndarray or matrix.dtype != np.float64 or matrix.ndim != 2 or matrix.shape[1] != FEATURE_COUNT or not bool(np.isfinite(matrix).all()):
            _fail("D0_INTEGRITY_AUDIT_BLOCKED_PREPROCESSING")
    combined = np.concatenate((train1, train2), axis=0).astype(np.float64, copy=False)
    mean = np.mean(combined, axis=0, dtype=np.float64)
    sigma = np.std(combined, axis=0, ddof=0, dtype=np.float64)
    scale = np.maximum(sigma, np.float64(SCALE_FLOOR))
    standardized = (combined - mean) / scale
    if not bool(np.isfinite(standardized).all()):
        _fail("D0_INTEGRITY_AUDIT_BLOCKED_PREPROCESSING")
    return mean, scale, standardized


def independent_pca_oracle_v1(standardized: Any) -> tuple[Any, Any, int, bool]:
    np = _np()
    if type(standardized) is not np.ndarray or standardized.dtype != np.float64 or standardized.ndim != 2 or standardized.shape[1] != FEATURE_COUNT:
        _fail("D0_INTEGRITY_AUDIT_BLOCKED_PCA")
    covariance = (standardized.T @ standardized) / np.float64(standardized.shape[0])
    covariance = (covariance + covariance.T) / np.float64(2.0)
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    order = np.argsort(-eigenvalues, kind="stable")
    values = eigenvalues[order].astype(np.float64, copy=False)
    vectors = eigenvectors[:, order].astype(np.float64, copy=False)
    total = float(np.sum(values, dtype=np.float64))
    tolerance = NEGATIVE_EIGENVALUE_EPSILON_MULTIPLIER * float(np.finfo(np.float64).eps) * max(1.0, total)
    if not np.isfinite(total) or total <= 0.0 or bool((values < -tolerance).any()):
        _fail("D0_INTEGRITY_AUDIT_BLOCKED_PCA")
    values = np.maximum(values, np.float64(0.0))
    cumulative = np.cumsum(values, dtype=np.float64) / np.float64(np.sum(values, dtype=np.float64))
    k = int(np.searchsorted(cumulative, np.float64(VARIANCE_TARGET), side="left")) + 1
    if k >= FEATURE_COUNT:
        k = FEATURE_COUNT - 1
    tied = bool(values[k - 1] == values[k])
    if tied or k < 1 or k >= FEATURE_COUNT:
        _fail("D0_INTEGRITY_AUDIT_BLOCKED_PCA")
    retained = vectors[:, :k].copy()
    for column in range(k):
        loading = retained[:, column]
        anchor = int(np.argmax(np.abs(loading)))
        if loading[anchor] < 0.0:
            retained[:, column] = -loading
    return values, retained, k, tied


def independent_spe_oracle_v1(values: Any, mean: Any, scale: Any, retained: Any) -> Any:
    np = _np()
    standardized = (values - mean) / scale
    projection = (standardized @ retained) @ retained.T
    residual = standardized - projection
    scores = np.sum(residual * residual, axis=1, dtype=np.float64)
    if scores.dtype != np.float64 or not bool(np.isfinite(scores).all()) or bool((scores < 0.0).any()):
        _fail("D0_INTEGRITY_AUDIT_BLOCKED_THRESHOLD")
    return scores


def independent_threshold_oracle_v1(scores: Any) -> tuple[float, int]:
    np = _np()
    if type(scores) is not np.ndarray or scores.dtype != np.float64 or scores.ndim != 1 or scores.size < 1:
        _fail("D0_INTEGRITY_AUDIT_BLOCKED_THRESHOLD")
    q_index = (999 * int(scores.size) + 999) // 1000 - 1
    ordered = np.sort(scores, kind="stable")
    return float(ordered[q_index]), q_index


def independent_alarm_episodes_v1(indices: Sequence[int]) -> tuple[tuple[int, int], ...]:
    if any(type(value) is not int or value < 0 for value in indices):
        _fail("D0_INTEGRITY_AUDIT_BLOCKED_TRAIN4")
    ordered = sorted(set(indices))
    if not ordered:
        return ()
    result: list[tuple[int, int]] = []
    start = previous = ordered[0]
    for value in ordered[1:]:
        if value != previous + 1:
            result.append((start, previous + 1))
            start = value
        previous = value
    result.append((start, previous + 1))
    return tuple(result)


class _HashingRawReader(io.RawIOBase):
    def __init__(self, path: Path) -> None:
        self._stream = path.open("rb")
        self._digest = sha256()
        self.byte_count = 0

    def readable(self) -> bool:
        return True

    def readinto(self, buffer: bytearray) -> int:
        count = self._stream.readinto(buffer)
        if count:
            self._digest.update(memoryview(buffer)[:count])
            self.byte_count += count
        return count

    def close(self) -> None:
        self._stream.close()
        super().close()

    @property
    def hexdigest(self) -> str:
        return self._digest.hexdigest()


def _parse_exact_normal_file(path: Path, identity: tuple[str, str, int, int]) -> Any:
    np = _np()
    relative, expected_hash, expected_size, expected_rows = identity
    try:
        if path.is_symlink() or not path.is_file() or path.name != PurePosixPath(relative).name:
            _fail("D0_INTEGRITY_AUDIT_BLOCKED_NORMAL_INPUT")
        hashing = _HashingRawReader(path)
        with io.BufferedReader(hashing, buffer_size=1024 * 1024) as buffered:
            with io.TextIOWrapper(buffered, encoding="utf-8-sig", newline="") as stream:
                header_line = stream.readline()
                header = tuple(next(csv.reader([header_line])))
                if len(header) != len(set(header)) or tuple(name for name in header if name.startswith("P1_")) != P1_FEATURE_ORDER:
                    _fail("D0_INTEGRITY_AUDIT_BLOCKED_NORMAL_INPUT")
                indices = tuple(header.index(name) for name in P1_FEATURE_ORDER)
                matrix = np.loadtxt(stream, delimiter=",", dtype=np.float64, usecols=indices, ndmin=2)
        if hashing.hexdigest != expected_hash or hashing.byte_count != expected_size or matrix.shape != (expected_rows, FEATURE_COUNT) or matrix.dtype != np.float64 or not bool(np.isfinite(matrix).all()):
            _fail("D0_INTEGRITY_AUDIT_BLOCKED_NORMAL_INPUT")
        return matrix
    except D0IntegrityAuditError:
        raise
    except BaseException:
        _fail("D0_INTEGRITY_AUDIT_BLOCKED_NORMAL_INPUT")


_BINDING_PATTERN = re.compile(r"^([A-Z0-9_]+)='((?:[^']|'\"'\"')*)'$")
_APPROVED_BINDING_KEYS = frozenset({
    "HAI_DATA_ROOT",
    "TASK039E3_UTILITY_NORMAL_ONLY_PRIVATE_REGISTRY_V1",
    "TASK039E3_UTILITY_NORMAL_ONLY_PRIVATE_LOCATOR_V1",
    "TASK039E3_UTILITY_SOURCE_CENSUS_SUPPLEMENT_PRIVATE_REGISTRY_V1",
    "TASK039E3_UTILITY_SOURCE_CENSUS_SUPPLEMENT_PRIVATE_LOCATOR_V1",
    "TASK039E3_D0_PCA_SPE_PREPROCESSING_V1",
    "TASK039E3_D0_PCA_SPE_MODEL_V1",
    "TASK039E3_D0_PCA_SPE_THRESHOLD_V1",
})


def _load_bindings() -> dict[str, str]:
    path = _repo_root() / ".env.custody.local"
    try:
        if path.is_symlink() or not path.is_file():
            _fail("D0_INTEGRITY_AUDIT_BLOCKED_PRIVATE_CUSTODY")
        result: dict[str, str] = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line:
                continue
            match = _BINDING_PATTERN.fullmatch(line)
            if match is None or match.group(1) not in _APPROVED_BINDING_KEYS or match.group(1) in result:
                _fail("D0_INTEGRITY_AUDIT_BLOCKED_PRIVATE_CUSTODY")
            result[match.group(1)] = match.group(2).replace("'\"'\"'", "'")
        for key in ("HAI_DATA_ROOT", "TASK039E3_D0_PCA_SPE_PREPROCESSING_V1", "TASK039E3_D0_PCA_SPE_MODEL_V1", "TASK039E3_D0_PCA_SPE_THRESHOLD_V1"):
            if key not in result:
                _fail("D0_INTEGRITY_AUDIT_BLOCKED_PRIVATE_CUSTODY")
        return result
    except D0IntegrityAuditError:
        raise
    except BaseException:
        _fail("D0_INTEGRITY_AUDIT_BLOCKED_PRIVATE_CUSTODY")


def _private_path(value: str) -> Path:
    try:
        path = Path(value)
        repo = _repo_root().resolve()
        resolved = path.resolve(strict=True)
        if not path.is_absolute() or path.is_symlink() or not path.is_file() or resolved == repo or repo in resolved.parents:
            _fail("D0_INTEGRITY_AUDIT_BLOCKED_PRIVATE_CUSTODY")
        return path
    except D0IntegrityAuditError:
        raise
    except BaseException:
        _fail("D0_INTEGRITY_AUDIT_BLOCKED_PRIVATE_CUSTODY")


def _load_private_document(value: str, expected_hash: str) -> dict[str, Any]:
    path = _private_path(value)
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
        if type(document) is not dict or document.get("artifact_hash") != expected_hash or canonical_hash_v1(document) != expected_hash:
            _fail("D0_INTEGRITY_AUDIT_BLOCKED_PRIVATE_CUSTODY")
        return document
    except D0IntegrityAuditError:
        raise
    except BaseException:
        _fail("D0_INTEGRITY_AUDIT_BLOCKED_PRIVATE_CUSTODY")


def _artifact_hash(document: Mapping[str, Any]) -> str:
    return canonical_hash_v1(document)


def run_private_oracle_v1() -> dict[str, Any]:
    np = _np()
    bindings = _load_bindings()
    prep_private = _load_private_document(bindings["TASK039E3_D0_PCA_SPE_PREPROCESSING_V1"], PREPROCESSING_HASH)
    model_private = _load_private_document(bindings["TASK039E3_D0_PCA_SPE_MODEL_V1"], MODEL_HASH)
    threshold_private = _load_private_document(bindings["TASK039E3_D0_PCA_SPE_THRESHOLD_V1"], THRESHOLD_HASH)
    try:
        root = Path(bindings["HAI_DATA_ROOT"])
        resolved_root = root.resolve()
        resolved_repo = _repo_root().resolve()
        if not root.is_absolute() or root.is_symlink() or not root.is_dir() or resolved_root == resolved_repo or resolved_repo in resolved_root.parents:
            _fail("D0_INTEGRITY_AUDIT_BLOCKED_PRIVATE_CUSTODY")
    except D0IntegrityAuditError:
        raise
    except BaseException:
        _fail("D0_INTEGRITY_AUDIT_BLOCKED_PRIVATE_CUSTODY")

    train1 = _parse_exact_normal_file(root / PurePosixPath(NORMAL_FILES[0][0]), NORMAL_FILES[0])
    train2 = _parse_exact_normal_file(root / PurePosixPath(NORMAL_FILES[1][0]), NORMAL_FILES[1])
    mean, scale, standardized = independent_preprocessing_oracle_v1(train1, train2)
    del train1, train2
    prep_candidate: dict[str, Any] = {
        "artifact_type": "task039e3_r2r_d0_preprocessing_artifact_v1",
        "schema_version": "1.0.0",
        "detector_id": DETECTOR_ID,
        "design_hash": DESIGN_HASH,
        "feature_order_hash": FEATURE_ORDER_HASH,
        "train1_sha256": NORMAL_FILES[0][1],
        "train2_sha256": NORMAL_FILES[1][1],
        "combined_row_count": FIT_ROWS,
        "python_version": PYTHON_VERSION,
        "numpy_version": NUMPY_VERSION,
        "means_float_hex": [float(item).hex() for item in mean],
        "scales_float_hex": [float(item).hex() for item in scale],
    }
    prep_candidate["artifact_hash"] = _artifact_hash(prep_candidate)
    if prep_candidate != prep_private or prep_candidate["artifact_hash"] != PREPROCESSING_HASH:
        _fail("D0_INTEGRITY_AUDIT_BLOCKED_PREPROCESSING")

    eigenvalues, retained, k, tied = independent_pca_oracle_v1(standardized)
    del standardized
    model_candidate: dict[str, Any] = {
        "artifact_type": "task039e3_r2r_d0_pca_model_artifact_v1",
        "schema_version": "1.0.0",
        "detector_id": DETECTOR_ID,
        "design_hash": DESIGN_HASH,
        "preprocessing_hash": PREPROCESSING_HASH,
        "feature_order_hash": FEATURE_ORDER_HASH,
        "train1_sha256": NORMAL_FILES[0][1],
        "train2_sha256": NORMAL_FILES[1][1],
        "fit_row_count": FIT_ROWS,
        "python_version": PYTHON_VERSION,
        "numpy_version": NUMPY_VERSION,
        "selected_k": k,
        "explained_variance_target": VARIANCE_TARGET,
        "eigenvalues_float_hex": [float(item).hex() for item in eigenvalues],
        "retained_loadings_float_hex": [[float(item).hex() for item in retained[row, :]] for row in range(FEATURE_COUNT)],
        "labels_used": False,
        "test_accessed": False,
    }
    model_candidate["artifact_hash"] = _artifact_hash(model_candidate)
    if model_candidate != model_private or model_candidate["artifact_hash"] != MODEL_HASH or k != EXPECTED_K or FEATURE_COUNT - k != EXPECTED_RESIDUAL_DIMENSIONS or tied:
        _fail("D0_INTEGRITY_AUDIT_BLOCKED_PCA")

    train3 = _parse_exact_normal_file(root / PurePosixPath(NORMAL_FILES[2][0]), NORMAL_FILES[2])
    train3_scores = independent_spe_oracle_v1(train3, mean, scale, retained)
    del train3
    threshold, q_index = independent_threshold_oracle_v1(train3_scores)
    del train3_scores
    threshold_candidate: dict[str, Any] = {
        "artifact_type": "task039e3_r2r_d0_threshold_artifact_v1",
        "schema_version": "1.0.0",
        "detector_id": DETECTOR_ID,
        "design_hash": DESIGN_HASH,
        "model_hash": MODEL_HASH,
        "train3_sha256": NORMAL_FILES[2][1],
        "calibration_row_count": NORMAL_FILES[2][3],
        "alpha": ALPHA,
        "upper_quantile": 0.999,
        "q_index": q_index,
        "order_statistic_policy": "ceil(0.999*n)-1_zero_based_after_ascending_sort_no_interpolation",
        "threshold_float_hex": threshold.hex(),
        "comparison_operator": "score > threshold",
        "labels_used": False,
        "test_used": False,
    }
    threshold_candidate["artifact_hash"] = _artifact_hash(threshold_candidate)
    if threshold_candidate != threshold_private or threshold_candidate["artifact_hash"] != THRESHOLD_HASH or q_index != EXPECTED_Q_INDEX:
        _fail("D0_INTEGRITY_AUDIT_BLOCKED_THRESHOLD")

    train4 = _parse_exact_normal_file(root / PurePosixPath(NORMAL_FILES[3][0]), NORMAL_FILES[3])
    train4_scores = independent_spe_oracle_v1(train4, mean, scale, retained)
    alarms = train4_scores > np.float64(threshold)
    alarm_indices = tuple(int(item) for item in np.flatnonzero(alarms))
    episodes = independent_alarm_episodes_v1(alarm_indices)
    far = len(episodes) / (NORMAL_FILES[3][3] / 3600.0)
    if len(alarm_indices) != EXPECTED_TRAIN4_POINT_ALARMS or len(episodes) != EXPECTED_TRAIN4_EPISODES or far != EXPECTED_TRAIN4_FAR:
        _fail("D0_INTEGRITY_AUDIT_BLOCKED_TRAIN4")

    return {
        "authoritative_private_preprocessing_available": True,
        "authoritative_private_model_available": True,
        "authoritative_private_threshold_available": True,
        "independent_reconstruction_hash_match": True,
        "preprocessing_oracle_hash_match": True,
        "model_oracle_hash_match": True,
        "threshold_oracle_hash_match": True,
        "independent_selected_k": k,
        "independent_residual_dimensions": FEATURE_COUNT - k,
        "independent_tied_cutoff": tied,
        "threshold_q_index_oracle": q_index,
        "threshold_comparator_match": True,
        "train4_point_alarm_oracle": len(alarm_indices),
        "train4_point_alarm_match": True,
        "train4_episode_oracle": len(episodes),
        "train4_episode_match": True,
        "train4_far_oracle": far,
        "train4_far_match": True,
        "train_hash_matches": [True, True, True, True],
        "audit_train1_parses": 1,
        "audit_train2_parses": 1,
        "audit_train3_parses": 1,
        "audit_train4_parses": 1,
        "audit_preprocessing_recomputations": 1,
        "audit_pca_recomputations": 1,
        "audit_threshold_recomputations": 1,
        "audit_train4_sanity_recomputations": 1,
        "audit_authoritative_model_fits": 0,
        "audit_authoritative_threshold_calibrations": 0,
        "test1_accesses": 0,
        "label_accesses": 0,
        "test2_accesses": 0,
        "d1_performance_reads": 0,
        "private_paths_exposed": 0,
        "private_preprocessing_values_exposed": 0,
        "private_pca_values_exposed": 0,
        "private_threshold_values_exposed": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--public", action="store_true")
    parser.add_argument("--private", action="store_true")
    try:
        arguments = parser.parse_args()
        if arguments.public == arguments.private:
            _fail("D0_INTEGRITY_AUDIT_BLOCKED_UNEXPECTED")
        result = run_public_audit_v1() if arguments.public else run_private_oracle_v1()
        print(json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False))
        return 0
    except D0IntegrityAuditError as failure:
        print(failure.code)
        return 2
    except BaseException:
        print("D0_INTEGRITY_AUDIT_BLOCKED_UNEXPECTED")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
