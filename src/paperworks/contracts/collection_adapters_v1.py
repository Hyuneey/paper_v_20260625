"""Legacy collection compatibility wrapper for the canonical protocol."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from paperworks.contracts.evidence_v1 import EvidencePackageV1
from paperworks.contracts.graph_v1 import CandidateGraphV1
from paperworks.contracts.parameter_v1 import CalibrationParameterV1
from paperworks.contracts.phase1_adapters import (
    DelayedResponseArtifactCollectionV1,
)


@dataclass(frozen=True)
class LegacyDelayedResponseCollectionAdapterV1:
    """Delegate without reserializing or replacing any TASK-032 artifact."""

    legacy_collection: DelayedResponseArtifactCollectionV1

    @property
    def graph(self) -> CandidateGraphV1:
        return self.legacy_collection.graph

    @property
    def evidence(self) -> EvidencePackageV1:
        return self.legacy_collection.evidence

    @property
    def parameters(self) -> tuple[CalibrationParameterV1, ...]:
        return self.legacy_collection.parameters

    @property
    def graph_by_id(self) -> Mapping[str, CandidateGraphV1]:
        return self.legacy_collection.graph_by_id

    @property
    def edge_by_id(self) -> Mapping[str, Any]:
        return self.legacy_collection.edge_by_id

    @property
    def evidence_by_id(self) -> Mapping[str, EvidencePackageV1]:
        return self.legacy_collection.evidence_by_id

    @property
    def normal_reference_by_id(self) -> Mapping[str, Any]:
        return self.legacy_collection.normal_reference_by_id

    @property
    def parameter_by_id(self) -> Mapping[str, CalibrationParameterV1]:
        return self.legacy_collection.parameter_by_id

    @property
    def rule_binding_verified(self) -> bool:
        return self.legacy_collection.rule_binding_verified

    @property
    def runtime_authorized(self) -> bool:
        return self.legacy_collection.runtime_authorized


def adapt_legacy_delayed_response_collection_v1(
    collection: DelayedResponseArtifactCollectionV1,
) -> LegacyDelayedResponseCollectionAdapterV1:
    """Expose the historical collection through the bounded protocol."""

    return LegacyDelayedResponseCollectionAdapterV1(collection)
