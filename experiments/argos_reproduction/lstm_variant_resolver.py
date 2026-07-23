"""Source-only resolution policy for the ARGOS KPI LSTMAD identity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence


IDENTITY_STATUSES = frozenset(
    {
        "exact_variant_and_config_recovered",
        "exact_variant_recovered_config_partial",
        "detector_family_recovered_variant_ambiguous",
        "detector_identity_unrecoverable",
    }
)


@dataclass(frozen=True)
class VariantResolution:
    identity_status: str
    detector_family: str
    retained_variants: tuple[str, ...]
    detector_role: str
    selection_between_variants: str
    source_reasons: tuple[str, ...]


def resolve_lstm_variant(
    *,
    argos_names: Sequence[str],
    easytsad_variants: Mapping[str, bool],
    explicit_variant_evidence: str | None = None,
) -> VariantResolution:
    """Resolve identity without using detector performance."""
    if "LSTMAD" not in set(argos_names):
        return VariantResolution(
            "detector_identity_unrecoverable",
            "LSTMAD",
            (),
            "blocked",
            "prohibited",
            ("ARGOS does not identify LSTMAD as a baseline",),
        )
    available = tuple(
        name for name in ("LSTMADalpha", "LSTMADbeta") if easytsad_variants.get(name) is True
    )
    if explicit_variant_evidence in available:
        return VariantResolution(
            "exact_variant_recovered_config_partial",
            "LSTMAD",
            (explicit_variant_evidence,),
            "paper_aligned_exact_variant",
            "not_applicable",
            ("ARGOS source explicitly identifies the EasyTSAD class",),
        )
    if available == ("LSTMADalpha", "LSTMADbeta"):
        return VariantResolution(
            "detector_family_recovered_variant_ambiguous",
            "LSTMAD",
            available,
            "paper_aligned_family_sensitivity",
            "prohibited",
            (
                "ARGOS paper and repository use only the generic LSTMAD name",
                "the time-bounded official EasyTSAD source exposes alpha and beta",
            ),
        )
    return VariantResolution(
        "detector_identity_unrecoverable",
        "LSTMAD",
        available,
        "blocked",
        "prohibited",
        ("the complete official EasyTSAD LSTMAD family is unavailable",),
    )
