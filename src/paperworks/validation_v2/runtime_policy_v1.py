"""Immutable policy identities shared by the Formal V4 authority and runtime."""

from __future__ import annotations

from hashlib import sha256
import json
from typing import Any, Mapping


def _policy_hash(document: Mapping[str, Any]) -> str:
    raw = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return sha256(raw).hexdigest()


FORMAL_V4_TRIGGER_POLICY = {
    "amplitude": "median(post)-median(pre)",
    "direction": "strict_sign_match",
    "isolation": "distance_gte_configured_radius",
    "refractory": "elapsed_gte_configured_seconds",
    "stability": "pre_and_post_fraction_within_tolerance",
    "threshold": "absolute_amplitude_gte_threshold",
}
FORMAL_V4_RESPONSE_POLICY = {
    "baseline": "median(target_baseline)",
    "decrease": "median(response)-baseline<-noise_scale",
    "horizon": "response_start_index=event_index+selected_horizon_seconds",
    "increase": "median(response)-baseline>noise_scale",
    "missing_future": "ABSTAIN",
}
FORMAL_V4_TRACE_CONTRACT = {
    "fields": [
        "alarm_emitted",
        "authorization_hash",
        "descriptor_hash",
        "execution_context_hash",
        "final_outcome",
        "opportunity_id",
        "reason",
        "relation_id",
    ],
    "raw_values_embedded": False,
}
FORMAL_V4_TRIGGER_POLICY_HASH = _policy_hash(FORMAL_V4_TRIGGER_POLICY)
FORMAL_V4_RESPONSE_POLICY_HASH = _policy_hash(FORMAL_V4_RESPONSE_POLICY)
FORMAL_V4_TRACE_CONTRACT_HASH = _policy_hash(FORMAL_V4_TRACE_CONTRACT)
