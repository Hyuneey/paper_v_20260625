"""Project-owned manifest contract for future detector artifacts."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Mapping


SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
REQUIRED_HASH_FIELDS = (
    "split_manifest_hash",
    "checkpoint_hash",
    "normalization_hash",
    "generation_score_hash",
    "inner_score_hash",
    "outer_score_hash",
    "generation_prediction_hash",
    "inner_prediction_hash",
    "outer_prediction_hash",
    "threshold_protocol_hash",
    "incorrect_indices_generation_hash",
)


class DetectorArtifactContractError(ValueError):
    pass


@dataclass(frozen=True)
class DetectorArtifactManifest:
    detector_id: str
    detector_family: str
    detector_variant: str
    detector_role: str
    source_commit: str
    source_file_hashes: tuple[tuple[str, str], ...]
    config_hash: str
    environment_hash: str
    seed: int
    kpi_id: str
    split_manifest_hash: str
    checkpoint_hash: str
    normalization_hash: str
    generation_score_hash: str
    inner_score_hash: str
    outer_score_hash: str
    generation_prediction_hash: str
    inner_prediction_hash: str
    outer_prediction_hash: str
    threshold: float
    threshold_protocol_hash: str
    incorrect_indices_generation_hash: str
    artifact_status: str


def validate_detector_manifest(document: Mapping[str, object]) -> DetectorArtifactManifest:
    required = set(DetectorArtifactManifest.__dataclass_fields__)
    if set(document) != required:
        raise DetectorArtifactContractError("DETECTOR_ARTIFACT_FIELDS_INVALID")
    if document["detector_family"] != "LSTMAD":
        raise DetectorArtifactContractError("DETECTOR_ARTIFACT_FAMILY_INVALID")
    if document["detector_variant"] not in ("LSTMADalpha", "LSTMADbeta"):
        raise DetectorArtifactContractError("DETECTOR_ARTIFACT_VARIANT_INVALID")
    if "test" in " ".join(document).lower():
        raise DetectorArtifactContractError("DETECTOR_TEST_ARTIFACT_PROHIBITED")
    for field in REQUIRED_HASH_FIELDS + ("config_hash", "environment_hash"):
        if not isinstance(document[field], str) or not SHA256_RE.fullmatch(str(document[field])):
            raise DetectorArtifactContractError(f"DETECTOR_ARTIFACT_HASH_INVALID:{field}")
    source_hashes = document["source_file_hashes"]
    if not isinstance(source_hashes, (list, tuple)) or not source_hashes:
        raise DetectorArtifactContractError("DETECTOR_SOURCE_HASHES_MISSING")
    normalized = tuple(sorted((str(path), str(digest)) for path, digest in source_hashes))
    if any(not SHA256_RE.fullmatch(digest) for _, digest in normalized):
        raise DetectorArtifactContractError("DETECTOR_SOURCE_HASH_INVALID")
    values = dict(document)
    values["source_file_hashes"] = normalized
    return DetectorArtifactManifest(**values)  # type: ignore[arg-type]


def argos_compatibility_layout(kpi_id: str) -> dict[str, str]:
    if not kpi_id or "/" in kpi_id or "\\" in kpi_id:
        raise DetectorArtifactContractError("DETECTOR_KPI_ID_INVALID")
    return {
        "train_labels": f"TrainLabels/{kpi_id}.npy",
        "incorrect_indices": "IncorrectIndices/train.json",
        "test_labels": "prohibited_until_joint_sealed_test_approval",
    }
