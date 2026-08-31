"""Authority-gated EXP-01 corrected-GDN arm runner.

The runner is deliberately narrow: an already-authorized normal-only input is
consumed once for the three preregistered seeds.  It never loads data, labels,
test partitions, or provider state itself.  Importing this module does not load
Torch and does not execute scientific work.
"""

from __future__ import annotations

from dataclasses import dataclass

from paperworks.gdn.upstream_candidate_backend_v1 import UpstreamGDNTrainingConfigV1
from paperworks.gdn.upstream_candidate_backend_v2 import (
    Exp01AuthorizedTrainingInputV2,
    Exp01RunAuthorizationV2,
    Exp01SeedRunReceiptV2,
    GDNNeighborPolicyV2,
    train_authorized_upstream_aligned_seed_v2,
)
from paperworks.validation_v2.exp01_gdn_v1 import (
    EXP01_SEEDS,
    Exp01ContractError,
    Exp01PreregistrationV1,
)
from paperworks.v6.common import require_sha256, stable_hash_v1


EXP01_BUNDLE_SCHEMA = "paperworks.validation_v2.exp01_seed_bundle_receipt_v1"


@dataclass(frozen=True)
class Exp01SeedBundleReceiptV1:
    preregistration_hash: str
    authorization_hash: str
    input_hash: str
    seed_receipt_hashes: tuple[str, str, str]
    seed_graph_hashes: tuple[str, str, str]
    schema: str = EXP01_BUNDLE_SCHEMA
    schema_version: str = "1.0.0"
    bundle_hash: str = ""

    def __post_init__(self) -> None:
        if self.schema != EXP01_BUNDLE_SCHEMA or self.schema_version != "1.0.0":
            raise Exp01ContractError("EXP-01 seed-bundle schema changed")
        for name in ("preregistration_hash", "authorization_hash", "input_hash"):
            require_sha256(getattr(self, name), name)
        if len(self.seed_receipt_hashes) != 3 or len(self.seed_graph_hashes) != 3:
            raise Exp01ContractError("EXP-01 bundle requires the three preregistered seeds")
        for index, value in enumerate((*self.seed_receipt_hashes, *self.seed_graph_hashes)):
            require_sha256(value, f"bundle_hashes[{index}]")
        if self.bundle_hash:
            require_sha256(self.bundle_hash, "bundle_hash")
            if self.bundle_hash != stable_hash_v1(self.to_dict(include_hash=False)):
                raise Exp01ContractError("EXP-01 seed-bundle replay mismatch")

    def to_dict(self, *, include_hash: bool = True) -> dict[str, object]:
        document: dict[str, object] = {
            "schema": self.schema,
            "schema_version": self.schema_version,
            "preregistration_hash": self.preregistration_hash,
            "authorization_hash": self.authorization_hash,
            "input_hash": self.input_hash,
            "seeds": list(EXP01_SEEDS),
            "seed_receipt_hashes": list(self.seed_receipt_hashes),
            "seed_graph_hashes": list(self.seed_graph_hashes),
        }
        if include_hash:
            document["bundle_hash"] = self.bundle_hash
        return document


def _validate_run_bindings_v1(
    *,
    preregistration: Exp01PreregistrationV1,
    authorization: Exp01RunAuthorizationV2,
    inputs: Exp01AuthorizedTrainingInputV2,
    config: UpstreamGDNTrainingConfigV1,
) -> None:
    if not preregistration.preregistration_hash or not authorization.authorization_hash or not inputs.input_hash:
        raise Exp01ContractError("self-hashed preregistration, authorization, and input are required")
    expected = (
        preregistration.preregistration_hash,
        preregistration.data_authority_hash,
        preregistration.feature_contract_hash,
        preregistration.candidate_universe_hash,
        preregistration.training_config_hash,
        preregistration.neighbor_policy_hash,
        preregistration.source_commit,
    )
    observed = (
        authorization.preregistration_hash,
        authorization.data_authority_hash,
        authorization.feature_contract_hash,
        authorization.candidate_universe_hash,
        authorization.training_config_hash,
        authorization.neighbor_policy_hash,
        authorization.source_commit,
    )
    if observed != expected:
        raise Exp01ContractError("EXP-01 run authorization does not replay the preregistration")
    if (
        inputs.data_authority_hash,
        inputs.feature_contract_hash,
        inputs.candidate_universe_hash,
    ) != expected[1:4]:
        raise Exp01ContractError("EXP-01 input does not replay the preregistered authority")
    if config.hyperparameter_hash != preregistration.training_config_hash:
        raise Exp01ContractError("EXP-01 training configuration does not replay the preregistration")
    if GDNNeighborPolicyV2().policy_hash != preregistration.neighbor_policy_hash:
        raise Exp01ContractError("EXP-01 neighbor policy does not replay the preregistration")


def execute_exp01_corrected_arm_v1(
    *,
    preregistration: Exp01PreregistrationV1,
    authorization: Exp01RunAuthorizationV2,
    inputs: Exp01AuthorizedTrainingInputV2,
    config: UpstreamGDNTrainingConfigV1,
) -> tuple[tuple[Exp01SeedRunReceiptV2, Exp01SeedRunReceiptV2, Exp01SeedRunReceiptV2], Exp01SeedBundleReceiptV1]:
    """Execute exactly seeds 11/23/37 after replaying every authority binding."""

    _validate_run_bindings_v1(
        preregistration=preregistration,
        authorization=authorization,
        inputs=inputs,
        config=config,
    )
    receipts = tuple(
        train_authorized_upstream_aligned_seed_v2(
            authorization=authorization,
            inputs=inputs,
            seed=seed,
            config=config,
        )
        for seed in EXP01_SEEDS
    )
    if tuple(receipt.seed for receipt in receipts) != EXP01_SEEDS:
        raise Exp01ContractError("EXP-01 seed receipt order changed")
    if any(
        not receipt.receipt_hash
        or receipt.preregistration_hash != preregistration.preregistration_hash
        or receipt.authorization_hash != authorization.authorization_hash
        or receipt.input_hash != inputs.input_hash
        or receipt.neighbor_policy_hash != preregistration.neighbor_policy_hash
        or receipt.training_config_hash != preregistration.training_config_hash
        or receipt.forward_internal_graph_hash != receipt.extraction_internal_graph_hash
        for receipt in receipts
    ):
        raise Exp01ContractError("EXP-01 seed receipt authority mismatch")
    provisional = Exp01SeedBundleReceiptV1(
        preregistration_hash=preregistration.preregistration_hash,
        authorization_hash=authorization.authorization_hash,
        input_hash=inputs.input_hash,
        seed_receipt_hashes=tuple(receipt.receipt_hash for receipt in receipts),
        seed_graph_hashes=tuple(receipt.graph_hash for receipt in receipts),
    )
    bundle = Exp01SeedBundleReceiptV1(
        **{
            **provisional.__dict__,
            "bundle_hash": stable_hash_v1(provisional.to_dict(include_hash=False)),
        }
    )
    return receipts, bundle


__all__ = [
    "EXP01_BUNDLE_SCHEMA",
    "Exp01SeedBundleReceiptV1",
    "execute_exp01_corrected_arm_v1",
]
