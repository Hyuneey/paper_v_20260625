"""Version-bound provider gate for the approved external T2 execution.

This module is deliberately transport-free.  It validates the exact frozen
request, reserves both per-version and combined budgets, and reconciles one
server response at a time.  HAI22 and HAI21 candidate IDs may collide, so a
version is part of every scientific slot identity.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
import json
import re
from pathlib import Path

from .exp03b_contract_v1 import digest, encoded, require
from .exp03b_custody_v1 import replay, seal
from .exp03b_firewall_v2 import assert_clean
from .xver_prompt_v1 import request_body


VERSIONS = ("22.04", "21.03")
VERSION_CODES = {"22.04": "HAI22", "21.03": "HAI21"}
EXPECTED_MODEL = "gpt-5.4-mini-2026-03-17"
EXPECTED_BUDGET_HASHES = {
    "22.04": "42de5ca54b478874d53a756a7ed16eba67957abc1a57413cc1b6119a33877ebb",
    "21.03": "51bef64337cc5a4d965945b09b39d4e03d84ef56414a479e9436b728bb345313",
}
COMBINED_LIMITS = {
    "maximum_calls": 174,
    "maximum_input_tokens": 3_266_560,
    "maximum_output_tokens": 356_352,
    "maximum_total_tokens": 3_622_912,
    "cost_ceiling_usd": "4.06",
}


@dataclass(frozen=True)
class XverReservationV1:
    index: int
    version: str
    slot: str
    candidate_id: str
    call_ordinal: int
    phase: str
    input_cap: int
    output_cap: int
    request_hash: str
    provider_pack_hash: str
    retrieval_pack_hash: str
    budget_hash: str
    prompt_hash: str
    schema_hash: str
    config_hash: str


def _profile_index(profile: dict) -> dict[str, dict]:
    replay(profile)
    return {row["candidate_id"]: row for row in profile["profiles"]}


def validate_budget(version: str, budget: dict, profile: dict) -> None:
    replay(budget)
    require(version in VERSIONS and budget["version"] == version, "VERSION_BUDGET_IDENTITY")
    require(budget["self_hash"] == EXPECTED_BUDGET_HASHES[version], "BUDGET_AUTHORITY_MISMATCH")
    require(
        budget["model"] == EXPECTED_MODEL
        and budget["gate"] == "DG-XVER-PROVIDER"
        and budget["maximum_calls"] == 87
        and budget["maximum_input_tokens"] == 1_633_280
        and budget["maximum_output_tokens"] == 178_176
        and budget["maximum_total_tokens"] == 1_811_456
        and budget["prospective_standard_price_ceiling_usd"] == "2.03",
        "BUDGET_AUTHORITY_MISMATCH",
    )
    config = budget["config"]
    require(
        config["model"] == EXPECTED_MODEL
        and config["endpoint"] == "https://api.openai.com/v1/responses"
        and config["reasoning"] == {"effort": "none"}
        and config["temperature"] == 0.7
        and config["top_p"] == 1.0
        and config["store"] is False
        and config["service_tier"] == "default"
        and config["timeout_seconds"] == 60
        and config["automatic_retries"] == 0
        and config["scientific_concurrency"] == 1
        and config["tools"] == []
        and config["event_evidence_allowed"] is False,
        "FROZEN_PROVIDER_SETTINGS_CHANGED",
    )
    require(
        profile["self_hash"] == budget["profile_hash"]
        and profile["version"] == version
        and len(_profile_index(profile)) == budget["N"] == 29,
        "BUDGET_COHORT",
    )


def validate_approval(approval: dict, budgets: dict[str, dict], execution_freeze_hash: str) -> None:
    replay(approval)
    require(
        approval["gate"] == "DG-XVER-PROVIDER"
        and approval["status"] == "APPROVED"
        and approval["integration_baseline"] == "be3ff48bd2abfafc81544357af0daff69a6721a2"
        and approval["model"] == EXPECTED_MODEL
        and approval["execution_freeze_hash"] == execution_freeze_hash
        and approval["budget_hashes"] == {v: budgets[v]["self_hash"] for v in VERSIONS}
        and approval["combined_limits"] == COMBINED_LIMITS
        and approval["retry"] == 0
        and approval["concurrency"] == 1
        and approval["provider_tools"] is False
        and approval["fallback"] is False
        and approval["attack_access"] is False,
        "DG_XVER_PROVIDER_USER_APPROVAL_REQUIRED",
    )


def validate_serialized_request(request: dict) -> None:
    """Validate the exact serialized body immediately before transport."""
    require(type(request) is dict and request.get("model") == EXPECTED_MODEL, "MODEL_SNAPSHOT_MISMATCH")
    require(request.get("store") is False and request.get("tools") == [], "FROZEN_PROVIDER_SETTINGS_CHANGED")
    require(request.get("reasoning") == {"effort": "none"}, "FROZEN_PROVIDER_SETTINGS_CHANGED")
    content = json.loads(request["input"])
    assert_clean(content)
    lowered = encoded(content).decode("utf-8").lower()
    for token in (
        "event_conditioned", "event10", "auxiliary_event", "train3", "train4",
        "block_b", "t0_output", "numeric_policy", "meta_rank", "meta_tier",
        "attack_label", "scenario_id", "heldout", "private_path",
    ):
        require(token not in lowered, "PRIVACY_OR_INFORMATION_FIREWALL_VIOLATION")


class XverCombinedProviderGateV1:
    def __init__(self, budgets: dict[str, dict], profiles: dict[str, dict], approval: dict, execution_freeze_hash: str):
        require(tuple(budgets) == VERSIONS and tuple(profiles) == VERSIONS, "VERSION_ORDER")
        for version in VERSIONS:
            validate_budget(version, budgets[version], profiles[version])
        validate_approval(approval, budgets, execution_freeze_hash)
        self.budgets = budgets
        self.profiles = profiles
        self.reservations: list[XverReservationV1] = []
        self.receipts: list[dict] = []
        self.in_flight: XverReservationV1 | None = None
        self.one_call_pass = False

    def reserve(
        self,
        *,
        version: str,
        candidate_id: str,
        call_ordinal: int,
        request: dict,
        provider_pack_hash: str,
        retrieval_pack_hash: str,
        input_upper_bound: int,
        evidence: dict,
        repair: dict | None,
    ) -> XverReservationV1:
        require(version in VERSIONS and call_ordinal in (1, 2, 3), "CALL_SLOT_INVALID")
        budget = self.budgets[version]
        profile = _profile_index(self.profiles[version])
        require(candidate_id in profile, "CALL_SLOT_INVALID")
        row = profile[candidate_id]
        require(
            provider_pack_hash == row["provider_pack_hash"]
            and retrieval_pack_hash == row["retrieval_pack_hash"],
            "PROVIDER_PACK_BINDING",
        )
        require(request == request_body(evidence, repair=repair), "FROZEN_REQUEST_CONFIG")
        validate_serialized_request(request)
        require((repair is None) == (call_ordinal == 1), "REPAIR_CALL_BINDING")
        if repair is not None:
            require(repair["feedback"]["remaining_call_budget"] == 3 - call_ordinal + 1, "REPAIR_CALL_BINDING")
        slot = f"{VERSION_CODES[version]}.{candidate_id}.T2.C{call_ordinal}"
        require(re.fullmatch(r"HAI(22|21)\.EXP03B-CAND-[0-9a-f]{20}\.T2\.C[123]", slot) is not None, "CALL_SLOT_INVALID")
        require(self.in_flight is None, "CONCURRENCY_ONE")
        require(not self.reservations or self.one_call_pass, "ONE_CALL_RECEIPT_FIRST")
        require(slot not in {r.slot for r in self.reservations}, "CALL_COUNT_OR_DUPLICATE")
        if call_ordinal > 1:
            previous = slot[:-1] + str(call_ordinal - 1)
            require(previous in {r.slot for r in self.reservations}, "CALL_SEQUENCE")
        version_rows = [r for r in self.reservations if r.version == version]
        require(len(version_rows) < budget["maximum_calls"], "CALL_COUNT_OR_DUPLICATE")
        require(len(self.reservations) < COMBINED_LIMITS["maximum_calls"], "CALL_COUNT_OR_DUPLICATE")
        phase = "initial" if call_ordinal == 1 else "repair"
        cap = budget["hard_phase_input_caps"][phase]
        require(
            type(input_upper_bound) is int
            and len(encoded(request)) + budget["framing_allowance"] <= input_upper_bound <= cap,
            "CALL_INPUT_CAP",
        )
        output = budget["output_cap_per_call"]
        version_input = sum(r.input_cap for r in version_rows) + cap
        version_output = sum(r.output_cap for r in version_rows) + output
        require(
            version_input <= budget["maximum_input_tokens"]
            and version_output <= budget["maximum_output_tokens"],
            "BUDGET_EXHAUSTED",
        )
        combined_input = sum(r.input_cap for r in self.reservations) + cap
        combined_output = sum(r.output_cap for r in self.reservations) + output
        require(
            combined_input <= COMBINED_LIMITS["maximum_input_tokens"]
            and combined_output <= COMBINED_LIMITS["maximum_output_tokens"]
            and combined_input + combined_output <= COMBINED_LIMITS["maximum_total_tokens"],
            "BUDGET_EXHAUSTED",
        )
        cost = (Decimal(combined_input) * Decimal("0.75") + Decimal(combined_output) * Decimal("4.50")) / 1_000_000
        require(cost <= Decimal(COMBINED_LIMITS["cost_ceiling_usd"]), "BUDGET_EXHAUSTED")
        reservation = XverReservationV1(
            index=len(self.reservations) + 1,
            version=version,
            slot=slot,
            candidate_id=candidate_id,
            call_ordinal=call_ordinal,
            phase=phase,
            input_cap=cap,
            output_cap=output,
            request_hash=digest(request),
            provider_pack_hash=provider_pack_hash,
            retrieval_pack_hash=retrieval_pack_hash,
            budget_hash=budget["self_hash"],
            prompt_hash=budget["prompt_hash"],
            schema_hash=budget["output_schema_hash"],
            config_hash=budget["config_hash"],
        )
        self.reservations.append(reservation)
        self.in_flight = reservation
        return reservation

    def reconcile(
        self,
        *,
        input_tokens: int,
        output_tokens: int,
        response_hash: str,
        response_id: str,
        model: str,
        latency_seconds: float,
        no_tool_invocation: bool,
    ) -> dict:
        reservation = self.in_flight
        require(reservation is not None, "NO_INFLIGHT_CALL")
        require(
            type(input_tokens) is int and type(output_tokens) is int
            and 0 <= input_tokens <= reservation.input_cap
            and 0 <= output_tokens <= reservation.output_cap,
            "PROVIDER_USAGE_CAP",
        )
        require(model == EXPECTED_MODEL, "MODEL_SNAPSHOT_MISMATCH")
        require(type(response_id) is str and bool(response_id), "PROVIDER_RESPONSE_IDENTITY")
        require(re.fullmatch(r"[0-9a-f]{64}", response_hash) is not None, "PROVIDER_RESPONSE_IDENTITY")
        require(no_tool_invocation, "PROVIDER_TOOL_INVOCATION")
        receipt = {
            **asdict(reservation),
            "response_hash": response_hash,
            "response_id": response_id,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "latency_seconds": float(latency_seconds),
            "model": model,
            "no_tool_invocation": True,
        }
        self.receipts.append(receipt)
        self.in_flight = None
        return receipt

    def accept_one_call_receipt(
        self,
        receipt_hash: str,
        *,
        persisted_and_replayed: bool,
        privacy_pass: bool,
        schema_pass: bool,
    ) -> None:
        require(
            len(self.receipts) == 1
            and self.receipts[0]["version"] == "22.04"
            and self.in_flight is None
            and digest(self.receipts[0]) == receipt_hash
            and persisted_and_replayed and privacy_pass and schema_pass,
            "ONE_CALL_PROBE_FAILED",
        )
        self.one_call_pass = True


def validate_call_inventory(runroot: Path, maximum_calls: int = 174) -> int:
    groups = {kind: set() for kind in ("request", "response", "receipt")}
    calls = runroot / "calls"
    if not calls.exists():
        return 0
    for path in calls.glob("*.json"):
        match = re.fullmatch(r"([0-9]{4})\.(request|response|receipt)\.json", path.name)
        require(match is not None and not path.is_symlink(), "CALL_LEDGER_FILENAME")
        index = int(match[1])
        require(1 <= index <= maximum_calls, "CALL_LEDGER_INDEX")
        groups[match[2]].add(index)
    indices = set().union(*groups.values())
    require(all(values == indices for values in groups.values()), "UNRESOLVED_PROVIDER_REQUEST_NO_AUTORETRY")
    require(indices == set(range(1, len(indices) + 1)), "UNRESOLVED_OR_NONCONTIGUOUS_CALL_LEDGER")
    return len(indices)


def sealed_receipt(receipt: dict) -> dict:
    return seal(receipt)
