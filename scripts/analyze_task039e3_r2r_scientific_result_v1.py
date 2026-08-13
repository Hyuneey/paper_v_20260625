#!/usr/bin/env python3
"""Deterministic, read-only analysis of the evaluable TASK-039E3 R2R result."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import statistics
from typing import Any, Iterable, Mapping, Sequence

from paperworks.v6.common import stable_hash_v1


EXECUTION_RECEIPT_HASH = "d164f00da3121e345907fe9076e62f4697493f26dde7448cc8527b895cbffa6e"
CUSTODY_AUDIT_RECEIPT_HASH = "5578202038dbd2e04972447467afc021a230c08dd6a821e81d9dd23bfb2b8986"
ARMS = ("T0", "T1", "T1-B", "T2")
ROLES = (
    "source_step_threshold",
    "source_stability_tolerance",
    "target_noise_scale",
)
ORIGINS = ("META", "STAT", "GDN")
PUBLIC_NAMES = {
    "construction": "TASK-039E3_R2R_CONSTRUCTION_METRICS.json",
    "direct": "TASK-039E3_R2R_DIRECT_NUMBER_METRICS.json",
    "summary": "TASK-039E3_R2R_EXECUTION_SUMMARY.json",
    "receipt": "TASK-039E3_R2R_EXECUTION_RECEIPT.json",
}
PRIVATE_NAMES = {
    "provider": "TASK039E3_R2R_SCIENTIFIC_PROVIDER_LEDGER.json",
    "proposals": "TASK039E3_R2R_PROPOSAL_VALIDITY_LEDGER.json",
    "outcomes": "TASK039E3_R2R_CONSTRUCTION_OUTCOME_LEDGER.json",
    "direct": "TASK039E3_R2R_DIRECT_NUMBER_LEDGER.json",
}


class ResultAnalysisError(ValueError):
    """Preserved result custody cannot support the requested analysis."""


def _read_verified(path: Path, *, expected_hash: str | None = None) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ResultAnalysisError(f"JSON object required: {path.name}")
    artifact_hash = value.get("artifact_hash")
    if stable_hash_v1({key: item for key, item in value.items() if key != "artifact_hash"}) != artifact_hash:
        raise ResultAnalysisError(f"artifact self-hash differs: {path.name}")
    if expected_hash is not None and artifact_hash != expected_hash:
        raise ResultAnalysisError(f"artifact authority differs: {path.name}")
    return value


def _records(document: Mapping[str, Any], expected: int) -> list[dict[str, Any]]:
    records = document.get("records")
    if not isinstance(records, list) or len(records) != expected or document.get("record_count") != expected:
        raise ResultAnalysisError("authoritative record count differs")
    if not all(isinstance(item, dict) for item in records):
        raise ResultAnalysisError("record must be an object")
    return records


def quantile_type7(values: Sequence[float], probability: float) -> float:
    """Hyndman-Fan type 7 quantile (linear interpolation, h=(n-1)p)."""

    if not values or not 0.0 <= probability <= 1.0:
        raise ResultAnalysisError("quantile input differs")
    ordered = sorted(float(value) for value in values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def describe(values: Sequence[float]) -> dict[str, Any]:
    if len(values) != 42 or not all(math.isfinite(value) for value in values):
        raise ResultAnalysisError("direct-number role must contain 42 finite values")
    return {
        "count": len(values),
        "mean": statistics.fmean(values),
        "median": statistics.median(values),
        "population_standard_deviation": statistics.pstdev(values),
        "q1_type7": quantile_type7(values, 0.25),
        "q3_type7": quantile_type7(values, 0.75),
        "p90_type7": quantile_type7(values, 0.90),
        "minimum": min(values),
        "maximum": max(values),
        "threshold_exceedance_counts": {
            "gt_0_10": sum(value > 0.10 for value in values),
            "gt_0_25": sum(value > 0.25 for value in values),
            "gt_0_50": sum(value > 0.50 for value in values),
            "gt_1_00": sum(value > 1.00 for value in values),
        },
    }


def exact_paired_binomial_p(left_only: int, right_only: int) -> float:
    """Two-sided exact McNemar/binomial p-value for discordant pairs."""

    discordant = left_only + right_only
    if discordant == 0:
        return 1.0
    tail = sum(math.comb(discordant, index) for index in range(min(left_only, right_only) + 1)) / (2 ** discordant)
    return min(1.0, 2.0 * tail)


def _relation_source_targets(proposals: Sequence[Mapping[str, Any]]) -> dict[str, tuple[str, str]]:
    mapping: dict[str, tuple[str, str]] = {}
    for record in proposals:
        project = record["project_proposal"]
        key = (project["source"], project["target"])
        identity = record["relation_identity"]
        prior = mapping.setdefault(identity, key)
        if prior != key:
            raise ResultAnalysisError("relation source/target binding differs")
    return mapping


def analyze_result(
    *,
    public_root: Path,
    private_root: Path,
    candidate_cohort_path: Path,
    custody_audit_receipt_path: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    public = {key: _read_verified(public_root / name) for key, name in PUBLIC_NAMES.items()}
    if public["receipt"]["artifact_hash"] != EXECUTION_RECEIPT_HASH:
        raise ResultAnalysisError("execution receipt authority differs")
    audit = _read_verified(custody_audit_receipt_path, expected_hash=CUSTODY_AUDIT_RECEIPT_HASH)
    if not audit.get("scientific_result_evaluable") or audit.get("blocking_finding_count") != 0:
        raise ResultAnalysisError("scientific result is not evaluable")
    final_root = private_root / "final_authoritative_r2r_v1"
    private_docs = {key: _read_verified(final_root / name) for key, name in PRIVATE_NAMES.items()}
    provider = _records(private_docs["provider"], 252)
    proposals = _records(private_docs["proposals"], 251)
    outcomes = _records(private_docs["outcomes"], 168)
    direct = _records(private_docs["direct"], 42)
    cohort = _read_verified(candidate_cohort_path)
    candidates = cohort.get("candidates")
    if not isinstance(candidates, list):
        raise ResultAnalysisError("candidate-origin cohort differs")

    by_relation: dict[str, dict[str, Mapping[str, Any]]] = defaultdict(dict)
    for record in outcomes:
        identity, arm = record["relation_identity"], record["arm"]
        if arm in by_relation[identity]:
            raise ResultAnalysisError("duplicate relation-arm outcome")
        by_relation[identity][arm] = record
    if len(by_relation) != 42 or any(set(value) != set(ARMS) for value in by_relation.values()):
        raise ResultAnalysisError("paired relation coverage differs")
    ordered_relations = sorted(by_relation)
    paired_matrix = [
        {
            "relation_identity": identity,
            **{arm: by_relation[identity][arm]["outcome"] for arm in ARMS},
        }
        for identity in ordered_relations
    ]

    construction: dict[str, Any] = {"relation_count": 42, "arms": {}}
    for arm in ARMS:
        records = [by_relation[identity][arm] for identity in ordered_relations]
        accepted = sum(record["outcome"] == "accepted_proposal" for record in records)
        no_rule = sum(record["outcome"] == "no_rule" for record in records)
        construction["arms"][arm] = {
            "accepted": accepted,
            "accepted_rate": accepted / 42,
            "no_rule": no_rule,
            "no_rule_rate": no_rule / 42,
        }
    construction["relation_level_validity_ceiling_observed"] = all(
        construction["arms"][arm]["accepted"] == 42 for arm in ("T0", "T1", "T1-B")
    )
    comparisons = {}
    for left, right in (("T1", "T1-B"), ("T1", "T2"), ("T1-B", "T2"), ("T0", "T1"), ("T0", "T1-B"), ("T0", "T2")):
        both = left_only = right_only = neither = 0
        for identity in ordered_relations:
            left_ok = by_relation[identity][left]["outcome"] == "accepted_proposal"
            right_ok = by_relation[identity][right]["outcome"] == "accepted_proposal"
            if left_ok and right_ok:
                both += 1
            elif left_ok:
                left_only += 1
            elif right_ok:
                right_only += 1
            else:
                neither += 1
        comparisons[f"{left}_vs_{right}"] = {
            "both_accepted": both,
            "left_only_accepted": left_only,
            "right_only_accepted": right_only,
            "neither_accepted": neither,
            "accepted_rate_difference_percentage_points_left_minus_right": 100.0 * (left_only - right_only) / 42,
            "exact_two_sided_mcnemar_binomial_p": exact_paired_binomial_p(left_only, right_only),
            "inferential_role": "supplementary",
        }
    construction["paired_comparisons"] = comparisons

    provider_by_relation: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    binding_to_identity: dict[str, str] = {}
    proposal_by_key: dict[tuple[str, str, int], Mapping[str, Any]] = {}
    proposal_counts: dict[str, Counter[str]] = {arm: Counter() for arm in ARMS}
    for record in proposals:
        identity, arm, call = record["relation_identity"], record["arm"], record["call_number"]
        proposal_by_key[(identity, arm, call)] = record
        binding = record["project_proposal"]["relation_binding_hash"]
        if binding in binding_to_identity and binding_to_identity[binding] != identity:
            raise ResultAnalysisError("relation binding is not unique")
        binding_to_identity[binding] = identity
        proposal_counts[arm]["materialized"] += 1
        if record["validity_result"]["status"] == "admissible":
            proposal_counts[arm]["admissible"] += 1
        else:
            proposal_counts[arm]["rejected"] += 1
    parse_by_arm: dict[str, Counter[str]] = defaultdict(Counter)
    request_hashes_by_index: dict[int, list[str]] = defaultdict(list)
    direct_provider = 0
    for record in provider:
        slot = record["slot"]
        arm = slot["arm"]
        parse_by_arm[arm][record["parse_status"]] += 1
        if arm == "T1-DIRECT-NUMBER":
            direct_provider += 1
            continue
        identity = binding_to_identity.get(slot["relation_binding_hash"])
        if identity is None:
            raise ResultAnalysisError("provider relation binding is unresolved")
        provider_by_relation[identity].append(record)
        request_hashes_by_index[slot["relation_schedule_index"]].append(record["request_hash"])
    initial_fairness = {
        "relations_compared": len(request_hashes_by_index),
        "relations_with_identical_t1_t1b_t2_initial_request_hashes": sum(
            len(hashes) == 5 and len(set(hashes)) == 1 for hashes in request_hashes_by_index.values()
        ),
        "request_hash_mismatches": sum(len(set(hashes)) != 1 for hashes in request_hashes_by_index.values()),
        "arm_identity_model_visible": False,
    }

    call_counts = Counter(record["slot"]["arm"] for record in provider)
    efficiency = {"arms": {}, "deterministic_baseline": {"arm": "T0", "provider_calls": 0, "accepted_relations": 42}}
    for arm, provider_arm in (("T1", "T1"), ("T1-B", "T1-B"), ("T2", "T2")):
        calls = call_counts[provider_arm]
        accepted = construction["arms"][arm]["accepted"]
        efficiency["arms"][arm] = {
            "provider_logical_calls": calls,
            "accepted_relations": accepted,
            "no_rule_relations": construction["arms"][arm]["no_rule"],
            "logical_calls_per_accepted_relation": calls / accepted,
            "accepted_relations_per_provider_call": accepted / calls,
            "parse_failures": parse_by_arm[provider_arm]["schema_parse_failure"],
            "proposal_rejections": proposal_counts[arm]["rejected"],
            "feedback_calls": sum(by_relation[identity][arm]["generation_calls_consumed"] - 1 for identity in ordered_relations) if arm == "T2" else 0,
        }
    efficiency["construction_validity_cost_frontier"] = {
        "T1": "non_dominated_provider_arm",
        "T1-B": "pareto_dominated_by_T1_same_yield_three_times_calls",
        "T2": "pareto_dominated_by_T1_lower_yield_same_calls",
        "T0": "deterministic_zero_provider_baseline_not_a_utility_winner",
    }

    t1b_relations = []
    selected = Counter()
    admissible_distribution = Counter()
    structured_distribution = Counter()
    rejected_distribution = Counter()
    per_call = {call: Counter() for call in (1, 2, 3)}
    cumulative_yield = Counter()
    selected_earliest_admissible = 0
    for identity in ordered_relations:
        calls = sorted(
            [record for record in provider_by_relation[identity] if record["slot"]["arm"] == "T1-B"],
            key=lambda record: record["slot"]["arm_local_call_number"],
        )
        if [record["slot"]["arm_local_call_number"] for record in calls] != [1, 2, 3]:
            raise ResultAnalysisError("T1-B did not consume exactly three calls")
        valid = admissible = parse_failures = rejected = 0
        admissible_calls: list[int] = []
        for call_record in calls:
            call = call_record["slot"]["arm_local_call_number"]
            proposal = proposal_by_key.get((identity, "T1-B", call))
            if proposal is None:
                parse_failures += 1
                per_call[call]["parse_failure"] += 1
                continue
            valid += 1
            if proposal["validity_result"]["status"] == "admissible":
                admissible += 1
                admissible_calls.append(call)
                per_call[call]["admissible"] += 1
            else:
                rejected += 1
                per_call[call]["rejected"] += 1
        selected_call = by_relation[identity]["T1-B"]["accepted_call_index"]
        selected[selected_call] += 1
        admissible_distribution[admissible] += 1
        structured_distribution[valid] += 1
        rejected_distribution[rejected] += 1
        selected_earliest_admissible += bool(admissible_calls) and selected_call == min(admissible_calls)
        for call in (1, 2, 3):
            cumulative_yield[call] += any(item <= call for item in admissible_calls)
        t1b_relations.append({
            "valid_proposals": valid,
            "admissible_proposals": admissible,
            "parse_failures": parse_failures,
            "rejected_proposals": rejected,
            "selected_call_index": selected_call,
        })
    t1b = {
        "provider_calls": call_counts["T1-B"],
        "materialized_proposals": proposal_counts["T1-B"]["materialized"],
        "valid_structured": parse_by_arm["T1-B"]["valid_structured"],
        "schema_parse_failures": parse_by_arm["T1-B"]["schema_parse_failure"],
        "admissible_materialized_proposals": proposal_counts["T1-B"]["admissible"],
        "rejected_materialized_proposals": proposal_counts["T1-B"]["rejected"],
        "final_accepted_relations": construction["arms"]["T1-B"]["accepted"],
        "admissible_proposals_per_relation_distribution": {str(key): admissible_distribution[key] for key in range(4)},
        "structured_proposals_per_relation_distribution": {str(key): structured_distribution[key] for key in range(4)},
        "rejected_proposals_per_relation_distribution": {str(key): rejected_distribution[key] for key in range(4)},
        "per_call_proposal_status": {
            str(call): {
                "admissible": per_call[call]["admissible"],
                "rejected": per_call[call]["rejected"],
                "parse_failure": per_call[call]["parse_failure"],
            }
            for call in (1, 2, 3)
        },
        "selected_call_distribution": {str(key): selected[key] for key in (1, 2, 3)},
        "selected_earliest_admissible_relations": selected_earliest_admissible,
        "cumulative_relation_yield": {"after_call_1": cumulative_yield[1], "after_calls_1_2": cumulative_yield[2], "after_calls_1_2_3": cumulative_yield[3]},
        "incremental_recovery": {"call_2": cumulative_yield[2] - cumulative_yield[1], "call_3": cumulative_yield[3] - cumulative_yield[2]},
        "additional_provider_calls": {"call_2_stage": 42, "call_3_stage": 42, "beyond_first_call_total": 84},
        "schema_failure_relation_remained_accepted": True,
    }

    issue_categories: Counter[tuple[str, str, str, str]] = Counter()
    t2_terminal = Counter()
    feedback_eligible = recovery = 0
    for identity in ordered_relations:
        outcome = by_relation[identity]["T2"]
        if outcome["outcome"] == "accepted_proposal":
            t2_terminal["accepted_proposal_call_1"] += 1
        else:
            t2_terminal[f"no_rule_{outcome['no_rule_reason']}"] += 1
        proposal = proposal_by_key[(identity, "T2", 1)]
        for issue in proposal["validity_result"]["issues"]:
            issue_categories[(issue["code"], issue["field"], issue["repairability"], issue["t2_action_class"])] += 1
            feedback_eligible += issue["t2_action_class"] in {"revise", "retrieve"}
        recovery += outcome["accepted_call_index"] not in (None, 1)
    revise = sum(by_relation[identity]["T2"]["revise_count"] for identity in ordered_relations)
    retrieve = sum(by_relation[identity]["T2"]["retrieval_count"] for identity in ordered_relations)
    followups = sum(max(0, by_relation[identity]["T2"]["generation_calls_consumed"] - 1) for identity in ordered_relations)
    t2 = {
        "provider_calls": call_counts["T2"],
        "accepted_relations": construction["arms"]["T2"]["accepted"],
        "no_rule_relations": construction["arms"]["T2"]["no_rule"],
        "all_terminated_after_call_1": all(by_relation[identity]["T2"]["generation_calls_consumed"] == 1 for identity in ordered_relations),
        "terminal_categories": dict(sorted(t2_terminal.items())),
        "sanitized_issue_categories": [
            {"code": key[0], "field_category": key[1], "repairability": key[2], "controller_action": key[3], "count": count}
            for key, count in sorted(issue_categories.items())
        ],
        "feedback_eligible_rejections": feedback_eligible,
        "revise_actions": revise,
        "retrieve_actions": retrieve,
        "follow_up_generations": followups,
        "feedback_activation_rate": (revise + retrieve) / 42,
        "successful_recoveries": recovery,
        "feedback_path_empirically_exercised": (revise + retrieve + followups) > 0,
    }
    construction["proposal_level"] = {
        arm: {
            "materialized": proposal_counts[arm]["materialized"],
            "admissible": proposal_counts[arm]["admissible"],
            "rejected": proposal_counts[arm]["rejected"],
            "parse_failures": parse_by_arm[arm]["schema_parse_failure"],
        }
        for arm in ARMS
    }
    construction["initial_request_fairness"] = initial_fairness

    direct_by_relation = {record["relation_identity"]: record for record in direct}
    if set(direct_by_relation) != set(ordered_relations):
        raise ResultAnalysisError("direct-number relation coverage differs")
    role_values = {role: [direct_by_relation[identity]["normalized_absolute_errors"][role] for identity in ordered_relations] for role in ROLES}
    direct_analysis = {
        "relation_count": 42,
        "quantile_method": "Hyndman-Fan type 7 linear interpolation",
        "standard_deviation_method": "population standard deviation over the complete 42-relation cohort",
        "missing_number_count": sum(record["missing_number"] for record in direct),
        "nonfinite_or_parse_failure_count": sum(record["nonfinite_or_parse_failure"] for record in direct),
        "sign_domain_violation_count": sum(bool(record["sign_domain_violation_roles"]) for record in direct),
        "roles": {role: describe(role_values[role]) for role in ROLES},
    }

    source_targets = _relation_source_targets(proposals)
    origins_by_pair = {}
    for candidate in candidates:
        pair = (candidate["source"], candidate["target"])
        if pair in origins_by_pair:
            raise ResultAnalysisError("duplicate candidate pair")
        origins_by_pair[pair] = tuple(candidate["origin_arms"])
    relation_origins: dict[str, tuple[str, ...]] = {}
    for identity in ordered_relations:
        pair = source_targets[identity]
        if pair not in origins_by_pair:
            raise ResultAnalysisError("relation has no frozen candidate origin")
        relation_origins[identity] = origins_by_pair[pair]
    membership_pattern_counts = Counter("+".join(relation_origins[identity]) for identity in ordered_relations)
    t2_no_rule_pattern_counts = Counter(
        "+".join(relation_origins[identity])
        for identity in ordered_relations
        if by_relation[identity]["T2"]["outcome"] == "no_rule"
    )
    origin = {
        "memberships_nonexclusive": True,
        "all_relations_mapped": len(relation_origins) == 42,
        "membership_pattern_counts": dict(sorted(membership_pattern_counts.items())),
        "t2_no_rule_by_membership_pattern": dict(sorted(t2_no_rule_pattern_counts.items())),
        "origins": {},
    }
    for membership in ORIGINS:
        identities = [identity for identity in ordered_relations if membership in relation_origins[identity]]
        if not identities:
            raise ResultAnalysisError("candidate origin membership is empty")
        t1b_parse = t1b_reject = 0
        for identity in identities:
            for call in provider_by_relation[identity]:
                if call["slot"]["arm"] == "T1-B" and call["parse_status"] == "schema_parse_failure":
                    t1b_parse += 1
            t1b_reject += sum(
                proposal_by_key[(identity, "T1-B", call)]["validity_result"]["status"] != "admissible"
                for call in (1, 2, 3) if (identity, "T1-B", call) in proposal_by_key
            )
        origin["origins"][membership] = {
            "eligible_relations": len(identities),
            "accepted_relations_by_arm": {
                arm: sum(by_relation[identity][arm]["outcome"] == "accepted_proposal" for identity in identities)
                for arm in ARMS
            },
            "t2_no_rule": sum(by_relation[identity]["T2"]["outcome"] == "no_rule" for identity in identities),
            "t1b_proposal_rejections": t1b_reject,
            "t1b_parse_failures": t1b_parse,
            "direct_number_by_role": {
                role: {
                    "mean_normalized_absolute_error": statistics.fmean(direct_by_relation[identity]["normalized_absolute_errors"][role] for identity in identities),
                    "median_normalized_absolute_error": statistics.median(direct_by_relation[identity]["normalized_absolute_errors"][role] for identity in identities),
                }
                for role in ROLES
            },
        }

    summary = public["summary"]
    accounting = {
        "historical_scientific_logical_calls": summary["historical_scientific_logical_calls_total"],
        "fresh_scientific_logical_calls": summary["r2r_scientific_logical_calls"],
        "lifetime_scientific_logical_calls": summary["lifetime_scientific_logical_call_attempts"],
        "historical_partial_records_reused": summary["historical_partial_results_reused"],
    }
    if accounting != {
        "historical_scientific_logical_calls": 6,
        "fresh_scientific_logical_calls": 252,
        "lifetime_scientific_logical_calls": 258,
        "historical_partial_records_reused": 0,
    }:
        raise ResultAnalysisError("scientific call accounting differs")

    analysis = {
        "input_authority": {
            "execution_receipt_hash": EXECUTION_RECEIPT_HASH,
            "custody_audit_receipt_hash": CUSTODY_AUDIT_RECEIPT_HASH,
            "scientific_result_evaluable": True,
            "public_artifacts_verified": 4,
            "private_artifacts_verified": 4,
        },
        "construction": construction,
        "efficiency": efficiency,
        "t1b": t1b,
        "t2": t2,
        "direct_number": direct_analysis,
        "origin": origin,
        "accounting": accounting,
        "privacy": {"relation_identities_in_sanitized_output": False, "private_paths_in_sanitized_output": False},
    }
    analysis["analysis_hash"] = stable_hash_v1(analysis)
    return analysis, paired_matrix


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--public-root", required=True, type=Path)
    parser.add_argument("--private-root", required=True, type=Path)
    parser.add_argument("--candidate-cohort", required=True, type=Path)
    parser.add_argument("--custody-audit-receipt", required=True, type=Path)
    parser.add_argument("--sanitized-output", required=True, type=Path)
    parser.add_argument("--private-paired-output", required=True, type=Path)
    arguments = parser.parse_args()
    analysis, matrix = analyze_result(
        public_root=arguments.public_root.resolve(strict=True),
        private_root=arguments.private_root.resolve(strict=True),
        candidate_cohort_path=arguments.candidate_cohort.resolve(strict=True),
        custody_audit_receipt_path=arguments.custody_audit_receipt.resolve(strict=True),
    )
    _write_json(arguments.sanitized_output, analysis)
    private_matrix = {
        "artifact_type": "task039e3_r2r_private_paired_relation_matrix_v1",
        "record_count": len(matrix),
        "records": matrix,
    }
    private_matrix["artifact_hash"] = stable_hash_v1(private_matrix)
    _write_json(arguments.private_paired_output, private_matrix)
    print(json.dumps({"relations": len(matrix), "status": "analysis_complete"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
