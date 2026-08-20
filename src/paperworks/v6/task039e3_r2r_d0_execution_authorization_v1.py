"""Factory-custodied authorization boundary for future D0 INNER execution.

The sole real-data operation is a one-attempt custody preflight. It validates
three already-frozen private artifacts and hashes the exact test1 feature and
label files as raw bytes. It never parses CSV rows, calculates SPE, creates
predictions, derives events, computes metrics, or opens test2.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import platform
import re
from typing import Any, Mapping, NoReturn
import weakref

from paperworks.v6.common import stable_hash_v1
from paperworks.v6 import task039e3_r2r_d0_detector_design_v1 as design


TASK_ID = "TASK-039E3-R2R-UTILITY-INNER-D0-EXECUTION-AUTHORIZATION-V1"
D0_EXECUTION_AUTHORIZATION_VERSION = "TASK039E3_R2R_D0_INNER_EXECUTION_AUTHORIZATION_V1"
D0_EXECUTION_AUTHORIZATION_SCOPE = "HAI_23_05_P1_TEST1_D0_PCA_SPE_INNER_V1"
PASS_STATUS = "passed_task039e3_r2r_utility_inner_d0_execution_authorization_v1"
SYNTHETIC_CONTRACT_ONLY = "SYNTHETIC_CONTRACT_ONLY"
REAL_CUSTODY_PREFLIGHT = "REAL_CUSTODY_PREFLIGHT"
FUTURE_D0_INNER_EXECUTION = "FUTURE_D0_INNER_EXECUTION"

DETECTOR_ID = "D0_PCA_SPE_V1"
DETECTOR_FAMILY = "PCA_RECONSTRUCTION_SPE"
D0_DESIGN_HASH = "357d19d02dee73273d52c7b147b5ddcfa11ead43a7198f2bf089ec78c2d8e174"
FEATURE_COUNT = 37
FEATURE_SET_HASH = "6dea06e82c0d99f35a0d11c5e97503e8bb3a0fc8c1d9963b997986021fd23515"
FEATURE_ORDER_HASH = "a612bdb9850ad0dd865dc62b23199bf2b696452c492e4aabe09fe554fa246d57"
PREPROCESSING_CONTENT_HASH = "baae5495094b211731e4fcdf7bab2870e3c81e7c973bfe052fc87b457ccb6270"
MODEL_CONTENT_HASH = "f32943cc2172100c77514d9ce8f6731978b51934e753234b2d34b5154127b54b"
THRESHOLD_CONTENT_HASH = "7ac0628cad5983b9864d31a9984bd414867b80f175248dbdf5cd69d7589f3695"
SELECTED_K = 10
RESIDUAL_DIMENSIONS = 27
PCA_VARIANCE_TARGET = 0.95
THRESHOLD_ALPHA = 0.001
THRESHOLD_Q_INDEX = 125_873
THRESHOLD_COMPARATOR = "score > threshold"

PYTHON_VERSION = "3.12.13"
PYTHON_RUNTIME_IDENTITY = "CPython-3.12"
NUMPY_VERSION = "2.3.5"
NUMERIC_BACKEND = "NUMPY_LINEAR_ALGEBRA"

DATASET_MANIFEST_ID = "5b0c395169fea468f7afd52aceafc4e6dadf062a1bc557c5bbe5dd6b8a761aa2"
INNER_SPLIT_ID = "30a7c88d6e0af5c37493237cc83b9520cbcd6f43c2dee7bb50ec3cac2668e7d0"
TEST1_FEATURE_FILENAME = "hai-test1.csv"
TEST1_FEATURE_SHA256 = "78c7f1d4de1f2ab9ccc2f8c719f80f831033543adb0c81d0d78f84f40838d4be"
TEST1_FEATURE_BYTE_SIZE = 31_255_559
TEST1_LABEL_FILENAME = "label-test1.csv"
TEST1_LABEL_SHA256 = "eaf69edb9c5834bc393afd7bf658b5e408d34fd7bfc3261f80516765fb818fbc"
TEST1_LABEL_BYTE_SIZE = 1_242_017
TEST1_PHYSICAL_ROWS = 54_000

TRAIN1_SHA256 = "53007b0ba604fbf338e7ac2e08cd81d874b5d1388f3aecb213ddcba5bf2bec4a"
TRAIN2_SHA256 = "0e520e82bf78a661ab19ce4967f3c766bd809820f457a9c90c365102d4534c56"
TRAIN3_SHA256 = "bfcec2dc05adea103e7491546b0e28268faaa26d3cc717d10f4595c94b81e85d"
COMBINED_FIT_ROWS = 572_400
TRAIN3_ROWS = 126_000

D1_RULE_PREDICTION_HASH = "58c3c49f9657f68d35c830b12eeb493ce4bbf7669c90f04813fb80246c3c2682"
ALARM_EPISODE_POLICY = "MAXIMAL_CONTIGUOUS_UNIQUE_ONE_SECOND_DECISION_INDICES_FILE_LOCAL"
ATTACK_EVENT_RECALL_FORMULA = "ATTACK_EVENTS_OVERLAPPED_BY_AT_LEAST_ONE_ALARM_EPISODE_DIVIDED_BY_ALL_ATTACK_EVENTS"
NORMAL_FAR_FORMULA = "ALARM_EPISODES_WITH_NO_ATTACK_TIMESTAMP_DIVIDED_BY_NORMAL_LABELED_SECONDS_OVER_3600"
FUTURE_PREDICTION_ARTIFACT_FAMILY = "ScientificDetectorPredictionArtifactV1"
FUTURE_EXECUTION_ORDER = (
    "replay_committed_d0_authorization",
    "validate_private_preprocessing_model_threshold",
    "validate_test1_feature_raw_hash",
    "parse_exact_37_test1_p1_features",
    "calculate_one_spe_per_second",
    "apply_frozen_strict_threshold",
    "freeze_detector_prediction_artifact",
    "validate_label_raw_hash_after_prediction_freeze",
    "parse_labels_after_prediction_freeze",
    "derive_attack_events",
    "form_detector_alarm_episodes",
    "compute_frozen_attack_event_recall",
    "compute_frozen_normal_far_episodes_per_hour",
    "freeze_result_and_stop",
)

DESIGN_REPORT_HASH = "3ffcec30d2bc605bf0b4ca15f80fcc3ed40aa283b6ae913e767c0ad9db18ece7"
FEATURE_SCOPE_REPORT_HASH = "4e9ba5a52733ae00f8cf755cda9918667c7065e0bc5b6eed2712aab97c3d6dd0"
INDEPENDENCE_REPORT_HASH = "f430d3233790f4befa3baeb024cce90eef08051358bd13771de4d73126f59692"
DESIGN_INDEPENDENT_AUDIT_HASH = "5375bd7730c92e117d8f08f221084f4b3804a453ddb4073a0c7784bdb78ec3f1"
DESIGN_READINESS_HASH = "533e62761efce660e1d10726268187c2a9ba5e0d2b0763814b64bd75b0473c4e"
DESIGN_BUNDLE_HASH = "8fa5ab4b81a4dad0f7d1d13bd356b3aad21a45e747cd3b047ada697450ce3034"
DESIGN_RECEIPT_HASH = "61299eba73c09faaf9396a6174ad487e4736c6271e274a2c18dd3cb60fd0c8b5"

TRAINING_IMPLEMENTATION_AUDIT_HASH = "545a9082e84dd350dfc2df941f70021932879e73020462cdb76075b6c20d58a5"
TRAINING_IMPLEMENTATION_SOURCE_SHA256 = "af36a3a5b8abccf61cd64c385b14df57adca0128e5c015d1bac74c191846172d"
MODEL_RECEIPT_HASH = "913f4a4bcf1771146f9493cded893b10eb97d2d177fe224f855c289d81ef1362"
THRESHOLD_RECEIPT_HASH = "2ee6fc8aba25d23449c14b08deae2eca0c5b739f6a251e43ead41923c978d326"
TRAINING_ACCOUNTING_HASH = "ca7f038c1c91b24feee38101c9d8b19cfe97a3dc417c32cee879f47942eed5f4"
TRAIN4_SANITY_HASH = "fb58290c1a59d164d9ace673968910db0f8ab65331ef3dfacd837c39685921ee"
TRAINING_READINESS_HASH = "fcba1018b1e42ff7fdda9467a02a4f902ec6803486a3847675752508537cda29"
TRAINING_BUNDLE_HASH = "fa041f5e0006fc56665d22c82eb0fdea51917e573ffc4946c8a3f83bf4ada1e6"
TRAINING_RECEIPT_HASH = "b4142789cbe99513c1763df15e0207588b75453829d2abe1aba4eaa60da75357"

INTEGRITY_PCA_ORACLE_HASH = "e3bd67ebab5e90c431e5eb87ebc4400a203484d4eed1874675d0d3633ae5eea8"
INTEGRITY_THRESHOLD_ORACLE_HASH = "43ee484a9a0f0ebc03699ddf6e201ca8c085081d938f3774e293e26db00b06c2"
INTEGRITY_FREEZE_AUDIT_HASH = "fb05a7801f312ce629f8d684939e4755f2c0773d8b661c95cf554b94d700cac8"
INTEGRITY_PREPROCESSING_ORACLE_HASH = "c9cb4737e224b9a942b66f8267f5c9479dde4c6507b316553fe88db3c8f018c1"
INTEGRITY_TRAIN4_ORACLE_HASH = "57a1b8a8e55f61e1d50526028f5bbae965488c646f97d68fa6d3a2f3e88f05f4"
INTEGRITY_ACCOUNTING_HASH = "c861cc14a0f2c018d77be1f8171806289ea9346d77464ce186a7705a1721f02c"
INTEGRITY_LEAKAGE_AUDIT_HASH = "bc70098b7775101151e8601607ccb6621febe09f70220214ac0285322286dfb8"
INTEGRITY_INDEPENDENT_AUDIT_HASH = "7c0b2fe510e2806985985d68f45db534ce902b16dc26978cc45b631f5790025d"
INTEGRITY_READINESS_HASH = "4849661e894bb3c6d31e3a97451ae3cb596bfb4cf231388514935e64ee460b19"
INTEGRITY_BUNDLE_HASH = "5769e397c078680ab66bff7f698ccbd0c65f929430465543320a06714b7707ce"
INTEGRITY_RECEIPT_HASH = "4a66590a223f17bf363521f1d2e5e2b8f184b85d43500a8f6683b88f9648119c"

_PUBLIC_ARTIFACTS = {
    "design": ("TASK-039E3_R2R_UTILITY_INNER_D0_DETECTOR_DESIGN_V1_DESIGN.json", DESIGN_REPORT_HASH),
    "feature_scope": ("TASK-039E3_R2R_UTILITY_INNER_D0_DETECTOR_DESIGN_V1_FEATURE_SCOPE.json", FEATURE_SCOPE_REPORT_HASH),
    "independence": ("TASK-039E3_R2R_UTILITY_INNER_D0_DETECTOR_DESIGN_V1_INDEPENDENCE.json", INDEPENDENCE_REPORT_HASH),
    "design_independent_audit": ("TASK-039E3_R2R_UTILITY_INNER_D0_DETECTOR_DESIGN_V1_INDEPENDENT_AUDIT.json", DESIGN_INDEPENDENT_AUDIT_HASH),
    "design_readiness": ("TASK-039E3_R2R_UTILITY_INNER_D0_DETECTOR_DESIGN_V1_READINESS.json", DESIGN_READINESS_HASH),
    "design_bundle": ("TASK-039E3_R2R_UTILITY_INNER_D0_DETECTOR_DESIGN_V1_BUNDLE.json", DESIGN_BUNDLE_HASH),
    "design_receipt": ("TASK-039E3_R2R_UTILITY_INNER_D0_DETECTOR_DESIGN_V1_RECEIPT.json", DESIGN_RECEIPT_HASH),
    "training_implementation": ("TASK-039E3_R2R_UTILITY_INNER_D0_TRAINING_V1_IMPLEMENTATION_AUDIT.json", TRAINING_IMPLEMENTATION_AUDIT_HASH),
    "model_receipt": ("TASK-039E3_R2R_UTILITY_INNER_D0_TRAINING_V1_MODEL_RECEIPT.json", MODEL_RECEIPT_HASH),
    "threshold_receipt": ("TASK-039E3_R2R_UTILITY_INNER_D0_TRAINING_V1_THRESHOLD_RECEIPT.json", THRESHOLD_RECEIPT_HASH),
    "training_accounting": ("TASK-039E3_R2R_UTILITY_INNER_D0_TRAINING_V1_ACCOUNTING.json", TRAINING_ACCOUNTING_HASH),
    "train4_sanity": ("TASK-039E3_R2R_UTILITY_INNER_D0_TRAINING_V1_TRAIN4_SANITY.json", TRAIN4_SANITY_HASH),
    "training_readiness": ("TASK-039E3_R2R_UTILITY_INNER_D0_TRAINING_V1_READINESS.json", TRAINING_READINESS_HASH),
    "training_bundle": ("TASK-039E3_R2R_UTILITY_INNER_D0_TRAINING_V1_BUNDLE.json", TRAINING_BUNDLE_HASH),
    "training_receipt": ("TASK-039E3_R2R_UTILITY_INNER_D0_TRAINING_V1_RECEIPT.json", TRAINING_RECEIPT_HASH),
    "integrity_pca": ("TASK-039E3_R2R_UTILITY_INNER_D0_MODEL_THRESHOLD_INTEGRITY_V1_PCA_ORACLE.json", INTEGRITY_PCA_ORACLE_HASH),
    "integrity_threshold": ("TASK-039E3_R2R_UTILITY_INNER_D0_MODEL_THRESHOLD_INTEGRITY_V1_THRESHOLD_ORACLE.json", INTEGRITY_THRESHOLD_ORACLE_HASH),
    "integrity_freeze": ("TASK-039E3_R2R_UTILITY_INNER_D0_MODEL_THRESHOLD_INTEGRITY_V1_FREEZE_AUDIT.json", INTEGRITY_FREEZE_AUDIT_HASH),
    "integrity_preprocessing": ("TASK-039E3_R2R_UTILITY_INNER_D0_MODEL_THRESHOLD_INTEGRITY_V1_PREPROCESSING_ORACLE.json", INTEGRITY_PREPROCESSING_ORACLE_HASH),
    "integrity_train4": ("TASK-039E3_R2R_UTILITY_INNER_D0_MODEL_THRESHOLD_INTEGRITY_V1_TRAIN4_ORACLE.json", INTEGRITY_TRAIN4_ORACLE_HASH),
    "integrity_accounting": ("TASK-039E3_R2R_UTILITY_INNER_D0_MODEL_THRESHOLD_INTEGRITY_V1_ACCOUNTING_AUDIT.json", INTEGRITY_ACCOUNTING_HASH),
    "integrity_leakage": ("TASK-039E3_R2R_UTILITY_INNER_D0_MODEL_THRESHOLD_INTEGRITY_V1_LEAKAGE_AUDIT.json", INTEGRITY_LEAKAGE_AUDIT_HASH),
    "integrity_independent": ("TASK-039E3_R2R_UTILITY_INNER_D0_MODEL_THRESHOLD_INTEGRITY_V1_INDEPENDENT_AUDIT.json", INTEGRITY_INDEPENDENT_AUDIT_HASH),
    "integrity_readiness": ("TASK-039E3_R2R_UTILITY_INNER_D0_MODEL_THRESHOLD_INTEGRITY_V1_READINESS.json", INTEGRITY_READINESS_HASH),
    "integrity_bundle": ("TASK-039E3_R2R_UTILITY_INNER_D0_MODEL_THRESHOLD_INTEGRITY_V1_BUNDLE.json", INTEGRITY_BUNDLE_HASH),
    "integrity_receipt": ("TASK-039E3_R2R_UTILITY_INNER_D0_MODEL_THRESHOLD_INTEGRITY_V1_RECEIPT.json", INTEGRITY_RECEIPT_HASH),
}

HAI_DATA_ROOT_ENV = "HAI_DATA_ROOT"
PREPROCESSING_ENV = "TASK039E3_D0_PCA_SPE_PREPROCESSING_V1"
MODEL_ENV = "TASK039E3_D0_PCA_SPE_MODEL_V1"
THRESHOLD_ENV = "TASK039E3_D0_PCA_SPE_THRESHOLD_V1"
_APPROVED_BINDING_KEYS = frozenset({
    HAI_DATA_ROOT_ENV,
    "TASK039E3_UTILITY_NORMAL_ONLY_PRIVATE_REGISTRY_V1",
    "TASK039E3_UTILITY_NORMAL_ONLY_PRIVATE_LOCATOR_V1",
    "TASK039E3_UTILITY_SOURCE_CENSUS_SUPPLEMENT_PRIVATE_REGISTRY_V1",
    "TASK039E3_UTILITY_SOURCE_CENSUS_SUPPLEMENT_PRIVATE_LOCATOR_V1",
    PREPROCESSING_ENV,
    MODEL_ENV,
    THRESHOLD_ENV,
})
_BINDING_PATTERN = re.compile(r"^([A-Z0-9_]+)='((?:[^']|'\"'\"')*)'$")


class D0ExecutionAuthorizationV1Error(ValueError):
    """An authorization or custody invariant differs."""


def _fail(message: str) -> NoReturn:
    raise D0ExecutionAuthorizationV1Error(message)


def _repository_root_v1() -> Path:
    return Path(__file__).resolve(strict=True).parents[3]


def _closed_json_object_v1(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            _fail("duplicate JSON member rejected")
        value[key] = item
    return value


def _load_public_document_v1(name: str, expected_hash: str) -> dict[str, Any]:
    path = _repository_root_v1() / "docs" / "task_reports" / name
    try:
        if path.is_symlink() or not path.is_file():
            _fail("D0 public authority unavailable")
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_closed_json_object_v1)
        if type(value) is not dict or value.get("artifact_hash") != expected_hash:
            _fail("D0 public authority identity differs")
        payload = dict(value)
        payload.pop("artifact_hash")
        if stable_hash_v1(payload) != expected_hash:
            _fail("D0 public authority self-hash differs")
        return value
    except D0ExecutionAuthorizationV1Error:
        raise
    except BaseException:
        _fail("D0 public authority invalid")


@dataclass(frozen=True)
class D0PublicAuthorityReplayV1:
    authority_set_hash: str
    artifact_hashes: tuple[tuple[str, str], ...]
    public_artifact_count: int
    public_cross_binding_count: int
    d0_design_hash: str
    training_receipt_hash: str
    integrity_receipt_hash: str
    integrity_audited: bool
    d0_execution_ready_for_separate_authorization: bool
    d0_currently_authorized: bool


def replay_required_d0_public_authorities_v1() -> D0PublicAuthorityReplayV1:
    documents = {
        key: _load_public_document_v1(filename, expected)
        for key, (filename, expected) in _PUBLIC_ARTIFACTS.items()
    }
    canonical_design = design.build_d0_detector_design_v1()
    design.validate_d0_detector_design_v1(canonical_design)
    model = documents["model_receipt"]
    threshold = documents["threshold_receipt"]
    train_accounting = documents["training_accounting"]
    train_readiness = documents["training_readiness"]
    train_bundle = documents["training_bundle"]
    train_receipt = documents["training_receipt"]
    pca = documents["integrity_pca"]
    threshold_oracle = documents["integrity_threshold"]
    integrity_accounting = documents["integrity_accounting"]
    integrity_readiness = documents["integrity_readiness"]
    integrity_bundle = documents["integrity_bundle"]
    integrity_receipt = documents["integrity_receipt"]
    feature = documents["feature_scope"]
    independence = documents["independence"]
    design_readiness = documents["design_readiness"]
    design_bundle = documents["design_bundle"]
    design_receipt = documents["design_receipt"]
    design_independent = documents["design_independent_audit"]
    train4 = documents["train4_sanity"]
    integrity_freeze = documents["integrity_freeze"]
    integrity_preprocessing = documents["integrity_preprocessing"]
    integrity_train4 = documents["integrity_train4"]
    integrity_leakage = documents["integrity_leakage"]
    integrity_independent = documents["integrity_independent"]
    training_source = _repository_root_v1() / "src" / "paperworks" / "v6" / "task039e3_r2r_d0_detector_training_v1.py"
    try:
        if training_source.is_symlink() or not training_source.is_file():
            _fail("D0 training implementation unavailable")
        training_source_sha256 = sha256(training_source.read_bytes()).hexdigest()
    except D0ExecutionAuthorizationV1Error:
        raise
    except BaseException:
        _fail("D0 training implementation invalid")
    conditions = (
        canonical_design.design_hash == D0_DESIGN_HASH,
        training_source_sha256 == TRAINING_IMPLEMENTATION_SOURCE_SHA256,
        feature.get("feature_count") == FEATURE_COUNT,
        feature.get("feature_set_hash") == FEATURE_SET_HASH,
        feature.get("feature_order_hash") == FEATURE_ORDER_HASH,
        independence.get("d1_performance_used_for_design") is False,
        independence.get("d1_metric_artifact_read_for_design") is False,
        independence.get("d1_prediction_content_read_for_design") is False,
        independence.get("frozen_d1_rule_prediction_hash") == D1_RULE_PREDICTION_HASH,
        design_readiness.get("d0_detector_design_hash") == D0_DESIGN_HASH,
        design_bundle.get("readiness_hash") == DESIGN_READINESS_HASH,
        design_receipt.get("bundle_hash") == DESIGN_BUNDLE_HASH,
        design_independent.get("accepted_invalid") == 0,
        model.get("d0_design_hash") == D0_DESIGN_HASH,
        model.get("feature_count") == FEATURE_COUNT,
        model.get("preprocessing_content_hash") == PREPROCESSING_CONTENT_HASH,
        model.get("model_content_hash") == MODEL_CONTENT_HASH,
        model.get("selected_k") == SELECTED_K,
        model.get("residual_dimensions") == RESIDUAL_DIMENSIONS,
        model.get("python_version") == PYTHON_VERSION,
        model.get("numpy_version") == NUMPY_VERSION,
        threshold.get("model_receipt_hash") == MODEL_RECEIPT_HASH,
        threshold.get("model_content_hash") == MODEL_CONTENT_HASH,
        threshold.get("threshold_content_hash") == THRESHOLD_CONTENT_HASH,
        threshold.get("alpha") == THRESHOLD_ALPHA,
        threshold.get("q_index") == THRESHOLD_Q_INDEX,
        threshold.get("comparison_operator") == THRESHOLD_COMPARATOR,
        train_accounting.get("model_fit_attempts") == 1,
        train_accounting.get("model_fit_retries") == 0,
        train_accounting.get("threshold_calibration_attempts") == 1,
        train_accounting.get("threshold_calibration_retries") == 0,
        train_accounting.get("test1_accesses") == 0,
        train_accounting.get("label_accesses") == 0,
        train_accounting.get("test2_accesses") == 0,
        train_readiness.get("model_receipt_hash") == MODEL_RECEIPT_HASH,
        train_readiness.get("threshold_receipt_hash") == THRESHOLD_RECEIPT_HASH,
        train_bundle.get("readiness_hash") == TRAINING_READINESS_HASH,
        train_receipt.get("bundle_hash") == TRAINING_BUNDLE_HASH,
        train_receipt.get("readiness_hash") == TRAINING_READINESS_HASH,
        train4.get("model_content_hash") == MODEL_CONTENT_HASH,
        train4.get("threshold_content_hash") == THRESHOLD_CONTENT_HASH,
        train4.get("result_driven_change") is False,
        integrity_freeze.get("post_freeze_mutation_count") == 0,
        integrity_preprocessing.get("preprocessing_content_hash") == PREPROCESSING_CONTENT_HASH,
        integrity_preprocessing.get("preprocessing_oracle_hash_match") is True,
        pca.get("model_content_hash") == MODEL_CONTENT_HASH,
        pca.get("selected_k") == SELECTED_K,
        pca.get("residual_dimensions") == RESIDUAL_DIMENSIONS,
        pca.get("model_oracle_hash_match") is True,
        threshold_oracle.get("threshold_content_hash") == THRESHOLD_CONTENT_HASH,
        threshold_oracle.get("threshold_oracle_hash_match") is True,
        threshold_oracle.get("q_index") == THRESHOLD_Q_INDEX,
        threshold_oracle.get("comparison_operator") == THRESHOLD_COMPARATOR,
        integrity_train4.get("train4_hash_match") is True,
        integrity_train4.get("point_alarm_count_match") is True,
        integrity_train4.get("alarm_episode_count_match") is True,
        integrity_train4.get("normal_far_match") is True,
        integrity_train4.get("threshold_frozen_before_train4") is True,
        integrity_leakage.get("private_paths_exposed") == 0,
        integrity_independent.get("accepted_invalid") == 0,
        integrity_accounting.get("audit_authoritative_model_fits") == 0,
        integrity_accounting.get("audit_authoritative_threshold_calibrations") == 0,
        integrity_accounting.get("test1_accesses") == 0,
        integrity_accounting.get("label_accesses") == 0,
        integrity_accounting.get("test2_accesses") == 0,
        integrity_readiness.get("d0_execution_ready_for_separate_authorization") is True,
        integrity_readiness.get("d0_authorized") is False,
        integrity_bundle.get("readiness_hash") == INTEGRITY_READINESS_HASH,
        integrity_bundle.get("model_content_hash") == MODEL_CONTENT_HASH,
        integrity_bundle.get("threshold_content_hash") == THRESHOLD_CONTENT_HASH,
        integrity_receipt.get("bundle_hash") == INTEGRITY_BUNDLE_HASH,
        integrity_receipt.get("readiness_hash") == INTEGRITY_READINESS_HASH,
        integrity_receipt.get("d0_authorized") is False,
        integrity_receipt.get("d0_executed") is False,
    )
    if not all(conditions):
        _fail("D0 public authority semantic replay differs")
    artifact_hashes = tuple((key, expected) for key, (_, expected) in sorted(_PUBLIC_ARTIFACTS.items()))
    known_hashes = frozenset(expected for _, expected in artifact_hashes)
    cross_binding_count = sum(
        1
        for document in documents.values()
        for key, value in document.items()
        if key != "artifact_hash" and key.endswith("_hash") and value in known_hashes
    )
    if len(artifact_hashes) != 26 or cross_binding_count != 50:
        _fail("D0 public authority DAG closure differs")
    authority_set_hash = stable_hash_v1({
        "artifact_hashes": artifact_hashes,
        "public_artifact_count": len(artifact_hashes),
        "public_cross_binding_count": cross_binding_count,
    })
    return D0PublicAuthorityReplayV1(
        authority_set_hash=authority_set_hash,
        artifact_hashes=artifact_hashes,
        public_artifact_count=len(artifact_hashes),
        public_cross_binding_count=cross_binding_count,
        d0_design_hash=D0_DESIGN_HASH,
        training_receipt_hash=TRAINING_RECEIPT_HASH,
        integrity_receipt_hash=INTEGRITY_RECEIPT_HASH,
        integrity_audited=True,
        d0_execution_ready_for_separate_authorization=True,
        d0_currently_authorized=False,
    )


@dataclass(frozen=True)
class D0InnerExecutionCustodyPreflightReceiptV1:
    authorization_version: str
    authorization_scope: str
    custody_mode: str
    public_authority_set_hash: str
    detector_id: str
    design_hash: str
    feature_count: int
    feature_set_hash: str
    feature_order_hash: str
    preprocessing_expected_hash: str
    preprocessing_observed_match: bool
    model_expected_hash: str
    model_observed_match: bool
    threshold_expected_hash: str
    threshold_observed_match: bool
    training_receipt_hash: str
    training_readiness_hash: str
    integrity_readiness_hash: str
    integrity_bundle_hash: str
    integrity_receipt_hash: str
    dataset_manifest_id: str
    inner_split_id: str
    test1_feature_expected_hash: str
    test1_feature_observed_match: bool
    test1_label_expected_hash: str
    test1_label_observed_match: bool
    python_version: str
    python_runtime_identity: str
    numpy_version: str
    numeric_backend: str
    d0_authorized_scope_intent: str
    test2_touched: bool
    scientific_feature_parsing_performed: bool
    scientific_label_parsing_performed: bool
    detector_execution_count: int
    metric_computation_count: int
    real_preflight_attempts: int
    real_preflight_retries: int
    preprocessing_reads: int
    model_reads: int
    threshold_reads: int
    test1_feature_hash_reads: int
    test1_label_hash_reads: int
    private_paths_exposed: int
    private_model_values_exposed: int
    private_threshold_values_exposed: int
    custody_preflight_hash: str
    _public_replay: D0PublicAuthorityReplayV1 = field(repr=False, compare=False)

    def _payload(self) -> dict[str, object]:
        return {key: value for key, value in self.__dict__.items() if not key.startswith("_") and key != "custody_preflight_hash"}

    def to_public_dict(self) -> dict[str, object]:
        return {**self._payload(), "artifact_hash": self.custody_preflight_hash}


_ISSUED_PREFLIGHTS: dict[int, tuple[weakref.ReferenceType[D0InnerExecutionCustodyPreflightReceiptV1], str, weakref.ReferenceType[D0PublicAuthorityReplayV1], str]] = {}
_REAL_PREFLIGHT_ATTEMPTED = False


def _build_preflight_receipt_v1(replay: D0PublicAuthorityReplayV1, *, real: bool) -> D0InnerExecutionCustodyPreflightReceiptV1:
    count = 1 if real else 0
    mode = REAL_CUSTODY_PREFLIGHT if real else SYNTHETIC_CONTRACT_ONLY
    provisional = D0InnerExecutionCustodyPreflightReceiptV1(
        authorization_version=D0_EXECUTION_AUTHORIZATION_VERSION,
        authorization_scope=D0_EXECUTION_AUTHORIZATION_SCOPE,
        custody_mode=mode,
        public_authority_set_hash=replay.authority_set_hash,
        detector_id=DETECTOR_ID,
        design_hash=D0_DESIGN_HASH,
        feature_count=FEATURE_COUNT,
        feature_set_hash=FEATURE_SET_HASH,
        feature_order_hash=FEATURE_ORDER_HASH,
        preprocessing_expected_hash=PREPROCESSING_CONTENT_HASH,
        preprocessing_observed_match=True,
        model_expected_hash=MODEL_CONTENT_HASH,
        model_observed_match=True,
        threshold_expected_hash=THRESHOLD_CONTENT_HASH,
        threshold_observed_match=True,
        training_receipt_hash=TRAINING_RECEIPT_HASH,
        training_readiness_hash=TRAINING_READINESS_HASH,
        integrity_readiness_hash=INTEGRITY_READINESS_HASH,
        integrity_bundle_hash=INTEGRITY_BUNDLE_HASH,
        integrity_receipt_hash=INTEGRITY_RECEIPT_HASH,
        dataset_manifest_id=DATASET_MANIFEST_ID,
        inner_split_id=INNER_SPLIT_ID,
        test1_feature_expected_hash=TEST1_FEATURE_SHA256,
        test1_feature_observed_match=True,
        test1_label_expected_hash=TEST1_LABEL_SHA256,
        test1_label_observed_match=True,
        python_version=PYTHON_VERSION,
        python_runtime_identity=PYTHON_RUNTIME_IDENTITY,
        numpy_version=NUMPY_VERSION,
        numeric_backend=NUMERIC_BACKEND,
        d0_authorized_scope_intent=FUTURE_D0_INNER_EXECUTION,
        test2_touched=False,
        scientific_feature_parsing_performed=False,
        scientific_label_parsing_performed=False,
        detector_execution_count=0,
        metric_computation_count=0,
        real_preflight_attempts=count,
        real_preflight_retries=0,
        preprocessing_reads=count,
        model_reads=count,
        threshold_reads=count,
        test1_feature_hash_reads=count,
        test1_label_hash_reads=count,
        private_paths_exposed=0,
        private_model_values_exposed=0,
        private_threshold_values_exposed=0,
        custody_preflight_hash="",
        _public_replay=replay,
    )
    return replace(provisional, custody_preflight_hash=stable_hash_v1(provisional._payload()))


def _issue_preflight_v1(receipt: D0InnerExecutionCustodyPreflightReceiptV1) -> D0InnerExecutionCustodyPreflightReceiptV1:
    object_id = id(receipt)
    def cleanup(dead: object) -> None:
        issued = _ISSUED_PREFLIGHTS.get(object_id)
        if issued is not None and (issued[0] is dead or issued[2] is dead):
            _ISSUED_PREFLIGHTS.pop(object_id, None)
    receipt_ref = weakref.ref(receipt, cleanup)
    replay_ref = weakref.ref(receipt._public_replay, cleanup)
    _ISSUED_PREFLIGHTS[object_id] = (receipt_ref, receipt.custody_preflight_hash, replay_ref, receipt.public_authority_set_hash)
    return receipt


def build_synthetic_d0_inner_execution_custody_preflight_receipt_v1() -> D0InnerExecutionCustodyPreflightReceiptV1:
    return _issue_preflight_v1(_build_preflight_receipt_v1(replay_required_d0_public_authorities_v1(), real=False))


def validate_d0_inner_execution_custody_preflight_receipt_v1(receipt: D0InnerExecutionCustodyPreflightReceiptV1, *, require_real: bool = False) -> str:
    if type(receipt) is not D0InnerExecutionCustodyPreflightReceiptV1:
        _fail("D0 preflight receipt type differs")
    issued = _ISSUED_PREFLIGHTS.get(id(receipt))
    if issued is None or issued[0]() is not receipt or issued[1] != receipt.custody_preflight_hash or issued[2]() is not receipt._public_replay or issued[3] != receipt.public_authority_set_hash:
        _fail("D0 preflight factory custody differs")
    replay = replay_required_d0_public_authorities_v1()
    if replay != receipt._public_replay:
        _fail("D0 public replay custody differs")
    expected = _build_preflight_receipt_v1(receipt._public_replay, real=receipt.custody_mode == REAL_CUSTODY_PREFLIGHT)
    if receipt != expected or receipt.to_public_dict() != expected.to_public_dict():
        _fail("D0 preflight semantic replay differs")
    if require_real and receipt.custody_mode != REAL_CUSTODY_PREFLIGHT:
        _fail("real D0 custody preflight required")
    return receipt.custody_preflight_hash


def _load_bindings_v1() -> dict[str, str]:
    path = _repository_root_v1() / ".env.custody.local"
    try:
        if path.is_symlink() or not path.is_file():
            _fail("D0 private custody bindings unavailable")
        values: dict[str, str] = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line:
                continue
            match = _BINDING_PATTERN.fullmatch(line)
            if match is None or match.group(1) not in _APPROVED_BINDING_KEYS or match.group(1) in values:
                _fail("D0 private custody bindings invalid")
            values[match.group(1)] = match.group(2).replace("'\"'\"'", "'")
        for key in (HAI_DATA_ROOT_ENV, PREPROCESSING_ENV, MODEL_ENV, THRESHOLD_ENV):
            if key not in values:
                _fail("D0 private custody binding missing")
        return values
    except D0ExecutionAuthorizationV1Error:
        raise
    except BaseException:
        _fail("D0 private custody bindings invalid")


def _private_regular_file_v1(value: str) -> Path:
    try:
        path = Path(value)
        resolved = path.resolve(strict=True)
        repository = _repository_root_v1().resolve()
        if not path.is_absolute() or path.is_symlink() or not path.is_file() or resolved == repository or repository in resolved.parents:
            _fail("D0 private artifact custody invalid")
        return path
    except D0ExecutionAuthorizationV1Error:
        raise
    except BaseException:
        _fail("D0 private artifact custody invalid")


def _canonical_float_hex_v1(value: object) -> bool:
    if type(value) is not str:
        return False
    try:
        number = float.fromhex(value)
        return math.isfinite(number) and number.hex() == value
    except BaseException:
        return False


def _load_private_json_once_v1(value: str, expected_hash: str) -> dict[str, Any]:
    path = _private_regular_file_v1(value)
    try:
        document = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_closed_json_object_v1)
        if type(document) is not dict or document.get("artifact_hash") != expected_hash:
            _fail("D0 private artifact identity differs")
        payload = dict(document)
        payload.pop("artifact_hash")
        if stable_hash_v1(payload) != expected_hash:
            _fail("D0 private artifact self-hash differs")
        return document
    except D0ExecutionAuthorizationV1Error:
        raise
    except BaseException:
        _fail("D0 private artifact invalid")


def _validate_preprocessing_v1(document: Mapping[str, Any]) -> None:
    expected_keys = {
        "artifact_type", "schema_version", "detector_id", "design_hash", "feature_order_hash",
        "train1_sha256", "train2_sha256", "combined_row_count", "python_version", "numpy_version",
        "means_float_hex", "scales_float_hex", "artifact_hash",
    }
    means, scales = document.get("means_float_hex"), document.get("scales_float_hex")
    if (
        set(document) != expected_keys
        or document.get("artifact_type") != "task039e3_r2r_d0_preprocessing_artifact_v1"
        or document.get("schema_version") != "1.0.0"
        or document.get("detector_id") != DETECTOR_ID
        or document.get("design_hash") != D0_DESIGN_HASH
        or document.get("feature_order_hash") != FEATURE_ORDER_HASH
        or document.get("train1_sha256") != TRAIN1_SHA256
        or document.get("train2_sha256") != TRAIN2_SHA256
        or document.get("combined_row_count") != COMBINED_FIT_ROWS
        or document.get("python_version") != PYTHON_VERSION
        or document.get("numpy_version") != NUMPY_VERSION
        or type(means) is not list or len(means) != FEATURE_COUNT
        or type(scales) is not list or len(scales) != FEATURE_COUNT
        or not all(_canonical_float_hex_v1(item) for item in means + scales)
    ):
        _fail("D0 preprocessing custody differs")


def _validate_model_v1(document: Mapping[str, Any]) -> None:
    expected_keys = {
        "artifact_type", "schema_version", "detector_id", "design_hash", "preprocessing_hash",
        "feature_order_hash", "train1_sha256", "train2_sha256", "fit_row_count", "python_version",
        "numpy_version", "selected_k", "explained_variance_target", "eigenvalues_float_hex",
        "retained_loadings_float_hex", "labels_used", "test_accessed", "artifact_hash",
    }
    eigenvalues = document.get("eigenvalues_float_hex")
    loadings = document.get("retained_loadings_float_hex")
    loading_shape = type(loadings) is list and len(loadings) == FEATURE_COUNT and all(type(row) is list and len(row) == SELECTED_K for row in loadings)
    if (
        set(document) != expected_keys
        or document.get("artifact_type") != "task039e3_r2r_d0_pca_model_artifact_v1"
        or document.get("schema_version") != "1.0.0"
        or document.get("detector_id") != DETECTOR_ID
        or document.get("design_hash") != D0_DESIGN_HASH
        or document.get("preprocessing_hash") != PREPROCESSING_CONTENT_HASH
        or document.get("feature_order_hash") != FEATURE_ORDER_HASH
        or document.get("train1_sha256") != TRAIN1_SHA256
        or document.get("train2_sha256") != TRAIN2_SHA256
        or document.get("fit_row_count") != COMBINED_FIT_ROWS
        or document.get("python_version") != PYTHON_VERSION
        or document.get("numpy_version") != NUMPY_VERSION
        or document.get("selected_k") != SELECTED_K
        or document.get("explained_variance_target") != PCA_VARIANCE_TARGET
        or document.get("labels_used") is not False
        or document.get("test_accessed") is not False
        or type(eigenvalues) is not list or len(eigenvalues) != FEATURE_COUNT
        or not all(_canonical_float_hex_v1(item) for item in eigenvalues)
        or not loading_shape
        or not all(_canonical_float_hex_v1(item) for row in loadings for item in row)
    ):
        _fail("D0 model custody differs")


def _validate_threshold_v1(document: Mapping[str, Any]) -> None:
    expected_keys = {
        "artifact_type", "schema_version", "detector_id", "design_hash", "model_hash", "train3_sha256",
        "calibration_row_count", "alpha", "upper_quantile", "q_index", "order_statistic_policy",
        "threshold_float_hex", "comparison_operator", "labels_used", "test_used", "artifact_hash",
    }
    if (
        set(document) != expected_keys
        or document.get("artifact_type") != "task039e3_r2r_d0_threshold_artifact_v1"
        or document.get("schema_version") != "1.0.0"
        or document.get("detector_id") != DETECTOR_ID
        or document.get("design_hash") != D0_DESIGN_HASH
        or document.get("model_hash") != MODEL_CONTENT_HASH
        or document.get("train3_sha256") != TRAIN3_SHA256
        or document.get("calibration_row_count") != TRAIN3_ROWS
        or document.get("alpha") != THRESHOLD_ALPHA
        or document.get("upper_quantile") != 0.999
        or document.get("q_index") != THRESHOLD_Q_INDEX
        or document.get("order_statistic_policy") != "ceil(0.999*n)-1_zero_based_after_ascending_sort_no_interpolation"
        or document.get("comparison_operator") != THRESHOLD_COMPARATOR
        or document.get("labels_used") is not False
        or document.get("test_used") is not False
        or not _canonical_float_hex_v1(document.get("threshold_float_hex"))
    ):
        _fail("D0 threshold custody differs")


def _raw_sha256_once_v1(path: Path, expected_size: int) -> str:
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size != expected_size:
            _fail("D0 test1 raw custody differs")
        digest = sha256()
        with path.open("rb") as stream:
            while True:
                chunk = stream.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
        return digest.hexdigest()
    except D0ExecutionAuthorizationV1Error:
        raise
    except BaseException:
        _fail("D0 test1 raw custody invalid")


def _validate_numeric_backend_v1() -> None:
    try:
        import numpy as np
        if platform.python_implementation() != "CPython" or platform.python_version() != PYTHON_VERSION or str(np.__version__) != NUMPY_VERSION:
            _fail("D0_AUTHORIZATION_BLOCKED_NUMERIC_BACKEND_MISMATCH")
    except D0ExecutionAuthorizationV1Error:
        raise
    except BaseException:
        _fail("D0_AUTHORIZATION_BLOCKED_NUMERIC_BACKEND_MISMATCH")


def perform_d0_inner_execution_custody_preflight_v1() -> D0InnerExecutionCustodyPreflightReceiptV1:
    """Perform the single authorized raw-byte/private-document preflight."""
    global _REAL_PREFLIGHT_ATTEMPTED
    if _REAL_PREFLIGHT_ATTEMPTED:
        _fail("real D0 custody preflight already attempted")
    _REAL_PREFLIGHT_ATTEMPTED = True
    replay = replay_required_d0_public_authorities_v1()
    _validate_numeric_backend_v1()
    bindings = _load_bindings_v1()
    preprocessing = _load_private_json_once_v1(bindings[PREPROCESSING_ENV], PREPROCESSING_CONTENT_HASH)
    _validate_preprocessing_v1(preprocessing)
    model = _load_private_json_once_v1(bindings[MODEL_ENV], MODEL_CONTENT_HASH)
    _validate_model_v1(model)
    threshold = _load_private_json_once_v1(bindings[THRESHOLD_ENV], THRESHOLD_CONTENT_HASH)
    _validate_threshold_v1(threshold)
    try:
        root = Path(bindings[HAI_DATA_ROOT_ENV])
        repository = _repository_root_v1().resolve()
        resolved = root.resolve(strict=True)
        if not root.is_absolute() or root.is_symlink() or not root.is_dir() or resolved == repository or repository in resolved.parents:
            _fail("D0 HAI custody invalid")
        feature_path = root / "hai-23.05" / TEST1_FEATURE_FILENAME
        label_path = root / "hai-23.05" / TEST1_LABEL_FILENAME
        feature_hash = _raw_sha256_once_v1(feature_path, TEST1_FEATURE_BYTE_SIZE)
        label_hash = _raw_sha256_once_v1(label_path, TEST1_LABEL_BYTE_SIZE)
        if feature_hash != TEST1_FEATURE_SHA256 or label_hash != TEST1_LABEL_SHA256:
            _fail("D0 test1 raw hashes differ")
    except D0ExecutionAuthorizationV1Error:
        raise
    except BaseException:
        _fail("D0 HAI custody invalid")
    return _issue_preflight_v1(_build_preflight_receipt_v1(replay, real=True))


@dataclass(frozen=True)
class D0InnerExecutionAuthorizationV1:
    authorization_version: str
    authorization_scope: str
    authorization_status: str
    custody_preflight_hash: str
    public_authority_set_hash: str
    training_receipt_hash: str
    integrity_receipt_hash: str
    detector_id: str
    detector_family: str
    design_hash: str
    feature_count: int
    feature_set_hash: str
    feature_order_hash: str
    preprocessing_content_hash: str
    model_content_hash: str
    threshold_content_hash: str
    selected_k: int
    residual_dimensions: int
    threshold_alpha: float
    threshold_q_index: int
    threshold_comparison_operator: str
    python_version: str
    python_runtime_identity: str
    numpy_version: str
    numeric_backend: str
    dataset_manifest_id: str
    inner_split_id: str
    test1_feature_sha256: str
    test1_label_sha256: str
    expected_test1_rows: int
    alarm_episode_policy: str
    attack_event_recall_formula: str
    normal_far_formula: str
    future_prediction_artifact_family: str
    future_prediction_artifact_label_blind: bool
    future_prediction_label_fields_authorized: bool
    future_prediction_d1_fields_authorized: bool
    future_prediction_metric_fields_authorized: bool
    future_execution_order: tuple[str, ...]
    frozen_d1_rule_prediction_hash_for_future_d2: str
    d0_inner_execution_authorized: bool
    d0_detector_prediction_authorized: bool
    test1_feature_scientific_parsing_authorized: bool
    label_metric_evaluation_authorized: bool
    label_access_before_prediction_freeze_authorized: bool
    d1_execution_authorized: bool
    d1_rerun_authorized: bool
    d2_authorized: bool
    fusion_authorized: bool
    outer_authorized: bool
    test2_authorized: bool
    retraining_authorized: bool
    recalibration_authorized: bool
    threshold_change_authorized: bool
    feature_change_authorized: bool
    model_change_authorized: bool
    d0_executed: bool
    authorization_hash: str
    _preflight_receipt: D0InnerExecutionCustodyPreflightReceiptV1 = field(repr=False, compare=False)

    def _payload(self) -> dict[str, object]:
        return {key: value for key, value in self.__dict__.items() if not key.startswith("_") and key != "authorization_hash"}

    def to_public_dict(self) -> dict[str, object]:
        return {**self._payload(), "artifact_hash": self.authorization_hash}


_ISSUED_AUTHORIZATIONS: dict[int, tuple[weakref.ReferenceType[D0InnerExecutionAuthorizationV1], str, weakref.ReferenceType[D0InnerExecutionCustodyPreflightReceiptV1], str]] = {}
_REAL_AUTHORIZATION_ISSUED = False


def _build_authorization_v1(receipt: D0InnerExecutionCustodyPreflightReceiptV1) -> D0InnerExecutionAuthorizationV1:
    real = receipt.custody_mode == REAL_CUSTODY_PREFLIGHT
    provisional = D0InnerExecutionAuthorizationV1(
        authorization_version=D0_EXECUTION_AUTHORIZATION_VERSION,
        authorization_scope=D0_EXECUTION_AUTHORIZATION_SCOPE,
        authorization_status="AUTHORIZED_FOR_FUTURE_D0_INNER_EXECUTION" if real else SYNTHETIC_CONTRACT_ONLY,
        custody_preflight_hash=receipt.custody_preflight_hash,
        public_authority_set_hash=receipt.public_authority_set_hash,
        training_receipt_hash=TRAINING_RECEIPT_HASH,
        integrity_receipt_hash=INTEGRITY_RECEIPT_HASH,
        detector_id=DETECTOR_ID,
        detector_family=DETECTOR_FAMILY,
        design_hash=D0_DESIGN_HASH,
        feature_count=FEATURE_COUNT,
        feature_set_hash=FEATURE_SET_HASH,
        feature_order_hash=FEATURE_ORDER_HASH,
        preprocessing_content_hash=PREPROCESSING_CONTENT_HASH,
        model_content_hash=MODEL_CONTENT_HASH,
        threshold_content_hash=THRESHOLD_CONTENT_HASH,
        selected_k=SELECTED_K,
        residual_dimensions=RESIDUAL_DIMENSIONS,
        threshold_alpha=THRESHOLD_ALPHA,
        threshold_q_index=THRESHOLD_Q_INDEX,
        threshold_comparison_operator=THRESHOLD_COMPARATOR,
        python_version=PYTHON_VERSION,
        python_runtime_identity=PYTHON_RUNTIME_IDENTITY,
        numpy_version=NUMPY_VERSION,
        numeric_backend=NUMERIC_BACKEND,
        dataset_manifest_id=DATASET_MANIFEST_ID,
        inner_split_id=INNER_SPLIT_ID,
        test1_feature_sha256=TEST1_FEATURE_SHA256,
        test1_label_sha256=TEST1_LABEL_SHA256,
        expected_test1_rows=TEST1_PHYSICAL_ROWS,
        alarm_episode_policy=ALARM_EPISODE_POLICY,
        attack_event_recall_formula=ATTACK_EVENT_RECALL_FORMULA,
        normal_far_formula=NORMAL_FAR_FORMULA,
        future_prediction_artifact_family=FUTURE_PREDICTION_ARTIFACT_FAMILY,
        future_prediction_artifact_label_blind=True,
        future_prediction_label_fields_authorized=False,
        future_prediction_d1_fields_authorized=False,
        future_prediction_metric_fields_authorized=False,
        future_execution_order=FUTURE_EXECUTION_ORDER,
        frozen_d1_rule_prediction_hash_for_future_d2=D1_RULE_PREDICTION_HASH,
        d0_inner_execution_authorized=real,
        d0_detector_prediction_authorized=real,
        test1_feature_scientific_parsing_authorized=real,
        label_metric_evaluation_authorized=real,
        label_access_before_prediction_freeze_authorized=False,
        d1_execution_authorized=False,
        d1_rerun_authorized=False,
        d2_authorized=False,
        fusion_authorized=False,
        outer_authorized=False,
        test2_authorized=False,
        retraining_authorized=False,
        recalibration_authorized=False,
        threshold_change_authorized=False,
        feature_change_authorized=False,
        model_change_authorized=False,
        d0_executed=False,
        authorization_hash="",
        _preflight_receipt=receipt,
    )
    return replace(provisional, authorization_hash=stable_hash_v1(provisional._payload()))


def _issue_authorization_v1(value: D0InnerExecutionAuthorizationV1) -> D0InnerExecutionAuthorizationV1:
    object_id = id(value)
    def cleanup(dead: object) -> None:
        issued = _ISSUED_AUTHORIZATIONS.get(object_id)
        if issued is not None and (issued[0] is dead or issued[2] is dead):
            _ISSUED_AUTHORIZATIONS.pop(object_id, None)
    auth_ref = weakref.ref(value, cleanup)
    receipt_ref = weakref.ref(value._preflight_receipt, cleanup)
    _ISSUED_AUTHORIZATIONS[object_id] = (auth_ref, value.authorization_hash, receipt_ref, value.custody_preflight_hash)
    return value


def issue_d0_inner_execution_authorization_v1(receipt: D0InnerExecutionCustodyPreflightReceiptV1) -> D0InnerExecutionAuthorizationV1:
    global _REAL_AUTHORIZATION_ISSUED
    validate_d0_inner_execution_custody_preflight_receipt_v1(receipt)
    if receipt.custody_mode == REAL_CUSTODY_PREFLIGHT:
        if _REAL_AUTHORIZATION_ISSUED:
            _fail("real D0 authorization already issued")
        _REAL_AUTHORIZATION_ISSUED = True
    return _issue_authorization_v1(_build_authorization_v1(receipt))


def validate_d0_inner_execution_authorization_v1(authorization: D0InnerExecutionAuthorizationV1, receipt: D0InnerExecutionCustodyPreflightReceiptV1, *, require_real: bool = False) -> str:
    if type(authorization) is not D0InnerExecutionAuthorizationV1:
        _fail("D0 authorization type differs")
    issued = _ISSUED_AUTHORIZATIONS.get(id(authorization))
    if issued is None or issued[0]() is not authorization or issued[1] != authorization.authorization_hash or issued[2]() is not receipt or issued[3] != receipt.custody_preflight_hash:
        _fail("D0 authorization factory custody differs")
    validate_d0_inner_execution_custody_preflight_receipt_v1(receipt, require_real=require_real)
    if authorization._preflight_receipt is not receipt:
        _fail("D0 authorization preflight custody differs")
    expected = _build_authorization_v1(receipt)
    if authorization != expected or authorization.to_public_dict() != expected.to_public_dict():
        _fail("D0 authorization semantic replay differs")
    if require_real and (
        authorization.d0_inner_execution_authorized is not True
        or authorization.d0_detector_prediction_authorized is not True
        or authorization.test1_feature_scientific_parsing_authorized is not True
        or authorization.label_metric_evaluation_authorized is not True
        or authorization.label_access_before_prediction_freeze_authorized is not False
        or authorization.d0_executed is not False
    ):
        _fail("real D0 authorization required")
    return authorization.authorization_hash


__all__ = [
    "D0_EXECUTION_AUTHORIZATION_SCOPE",
    "D0_EXECUTION_AUTHORIZATION_VERSION",
    "D0ExecutionAuthorizationV1Error",
    "D0InnerExecutionAuthorizationV1",
    "D0InnerExecutionCustodyPreflightReceiptV1",
    "D0PublicAuthorityReplayV1",
    "build_synthetic_d0_inner_execution_custody_preflight_receipt_v1",
    "issue_d0_inner_execution_authorization_v1",
    "perform_d0_inner_execution_custody_preflight_v1",
    "replay_required_d0_public_authorities_v1",
    "validate_d0_inner_execution_authorization_v1",
    "validate_d0_inner_execution_custody_preflight_receipt_v1",
]
