"""Normal-only post-provider closure for HAI22 and HAI21 external T2."""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from decimal import Decimal
from fractions import Fraction
import json
from pathlib import Path

from xver_execution_common import (
    ROOT, PUB, private_root, document, version_authorities, load_projection,
    publish, seal, require, digest, sha256_file,
)
from run_xver_semantic_execution_v1 import audit_fixed_portfolio
from paperworks.validation_v2.exp03b_contract_v1 import SemanticTupleV1, StructuralTupleEvidenceV1
from paperworks.validation_v2.exp03b_semantic_v2 import (
    parse_proposal, proposal_document,
)
from paperworks.validation_v2.exp03b_hidden_v2 import Train2HiddenVerifierAuthorityV2, Train2SemanticEvidenceV2, verify
from paperworks.validation_v2.exp03b_execution_v2 import admit
from paperworks.validation_v2.exp03b_numeric_v1 import summarize_column
from paperworks.validation_v2.exp03b_binder_v2 import POLICY
from paperworks.validation_v2.exp03b_conversion import convert
from paperworks.validation_v2.exp03b_evaluation import run_guard_portfolio
from paperworks.validation_v2.exp03b_guard_v1 import Train4HiddenGuardAuthorityV1
from paperworks.validation_v2.exp03b_metrics_v1 import strict_metrics
from paperworks.validation_v2.xver_t2_closure_v1 import authorize_t2_binding, bind_t2_rule


PUBLIC = PUB / "provider_execution_v1"
RUNROOT = private_root() / "provider_t2_v2"
VERSIONS = ("22.04", "21.03")


def safe(value):
    if isinstance(value, Fraction):
        return {"numerator": value.numerator, "denominator": value.denominator}
    if isinstance(value, dict):
        return {key: safe(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [safe(item) for item in value]
    return value


def read(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"));
    from paperworks.validation_v2.exp03b_custody_v1 import replay
    replay(value); return value


def structural(value: dict) -> Train2SemanticEvidenceV2:
    rows = tuple(
        StructuralTupleEvidenceV1(
            SemanticTupleV1(**row["semantic"]),
            **{key: item for key, item in row.items() if key != "semantic"},
        ) for row in value["rows"]
    )
    return Train2SemanticEvidenceV2(value["candidate_id"], value["source"], value["target"], value["input_hash"], rows)


def _provider_barrier(freeze: dict) -> tuple[dict, dict[str, dict]]:
    require(not (RUNROOT / "SINGLE_WRITER.lock").exists(), "PROVIDER_WRITER_ACTIVE")
    closed = read(RUNROOT / "PROVIDER_PHASE_CLOSED.json")
    combined = read(RUNROOT / "ALL_XVER_PROVIDER_OUTPUTS_FROZEN.json")
    require(
        closed["provider_calls_allowed"] is False
        and closed["output_bundle_hash"] == combined["self_hash"]
        and closed["execution_freeze_hash"] == freeze["self_hash"]
        and combined["all_outputs_and_admissions_frozen"] is True,
        "PROVIDER_PHASE_NOT_CLOSED",
    )
    bundles = {}
    for version in VERSIONS:
        bundle = read(RUNROOT / ("HAI" + version[:2]) / "PROVIDER_OUTPUTS_FROZEN.json")
        require(combined["version_bundles"][version] == bundle["self_hash"] and bundle["candidate_count"] == 29, "INCOMPLETE_VERSION_BUNDLE")
        bundles[version] = bundle
    publish(RUNROOT / "POST_PROVIDER_BARRIER_PASS.json", seal({
        "combined_output_hash": combined["self_hash"],
        "version_bundle_hashes": {version: bundles[version]["self_hash"] for version in VERSIONS},
        "provider_calls_allowed": False, "hidden_confirmation_may_begin": True,
    }))
    return combined, bundles


def _actual_usage(version: str) -> dict:
    rows = []
    for path in sorted((RUNROOT / "calls").glob("*.receipt.json")):
        row = read(path)
        if row["version"] == version:
            rows.append(row)
    input_tokens = sum(row["input_tokens"] for row in rows)
    output_tokens = sum(row["output_tokens"] for row in rows)
    prospective = (Decimal(input_tokens) * Decimal("0.75") + Decimal(output_tokens) * Decimal("4.50")) / 1_000_000
    return {
        "calls": len(rows), "input_tokens": input_tokens, "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "standard_price_estimate_usd": format(prospective, ".6f"),
        "not_actual_billing": True,
    }


def finalize_version(version: str, freeze: dict, bundle: dict) -> dict:
    execution, context, candidate, roles, pairs = __import__("run_xver_semantic_execution_v1").replay_authority(version)
    directory = RUNROOT / ("HAI" + version[:2])
    evidence_dir = private_root() / "semantic" / ("HAI" + version[:2])
    ids = tuple("EXP03B-CAND-" + digest({"source": s, "target": t})[:20] for s, t in pairs)
    require(bundle["candidate_ids"] == list(ids), "CANDIDATE_ORDER_CHANGED")
    admitted = {}; terminal_rows = []
    for candidate_id in ids:
        row = read(directory / "outputs" / f"{candidate_id}.json")
        terminal_rows.append(row)
        if row["admission_hash"] is None:
            admitted[candidate_id] = None; continue
        proposal = parse_proposal(row["raw"][-1])
        train1 = json.loads((evidence_dir / "provider" / f"{candidate_id}.json").read_text(encoding="utf-8"))
        hidden = structural(json.loads((evidence_dir / "train2" / "structural" / f"{candidate_id}.json").read_text(encoding="utf-8")))
        provider_ids = frozenset(item[7] for item in train1["structural_rows"])
        authority = Train2HiddenVerifierAuthorityV2(hidden, provider_ids)
        retrieval_ids = frozenset()
        if row["feedback"]:
            retrieval_pack = json.loads((evidence_dir / "retrieval" / f"{candidate_id}.json").read_text(encoding="utf-8"))
            retrieval_ids = frozenset(item["evidence_slice_id"] for item in retrieval_pack["alternatives"])
        result = verify(proposal, authority, retrieval_ids=retrieval_ids)
        # JSON custody canonicalizes tuple issue records to arrays.
        require(digest(asdict(result)) == digest(row["verifier_results"][-1]) and result.status == "ACCEPTED", "ADMISSION_REPLAY_CHANGED")
        value = admit(
            proposal, authority, implementation_hash=freeze["implementation_bundle_hash"],
            config_hash=document(PUB / f"HAI{version[:2]}_T2_PROVIDER_BUDGET_V1.json")["config_hash"],
            retrieval_ids=retrieval_ids,
        )
        require(value.receipt == row["admission_receipt"] and value.receipt["self_hash"] == row["admission_hash"], "ADMISSION_REPLAY_CHANGED")
        admitted[candidate_id] = value

    # The reference is first opened here, after the global two-version barrier.
    reference = read(evidence_dir / "NORMAL_REFERENCE_FROZEN.json")
    t0 = document(PUB / f"HAI{version[:2]}_T0_PORTFOLIO_AUTHORITY_V1.json")
    require(reference["self_hash"] == t0["reference_hash"], "NORMAL_REFERENCE_CHANGED")
    truth = {
        row["candidate_id"]: tuple(sorted(SemanticTupleV1(**relation) for relation in row["relations"]))
        for row in reference["records"]
    }
    predictions = {candidate_id: value.proposal.semantic_set() if value else None for candidate_id, value in admitted.items()}
    evaluations = []
    for candidate_id in ids:
        value = admitted[candidate_id]
        evaluations.append({
            "candidate_id": candidate_id, "admitted": value is not None,
            "semantic_exact": value is not None and value.proposal.semantic_set() == truth[candidate_id],
            "confirmed_rule_count": sum(rule.semantic in truth[candidate_id] for rule in value.proposal.rules) if value else 0,
        })
    evaluation = seal({
        "schema": "xver_t2_semantic_evaluation_frozen_v1", "version": version,
        "execution_hash": freeze["self_hash"], "semantic_execution_hash": execution["self_hash"],
        "provider_bundle_hash": bundle["self_hash"],
        "reference_hash": reference["self_hash"], "records": evaluations,
        "strict_metrics": safe(strict_metrics(truth, predictions)), "provider_calls_allowed": False,
    })
    publish(directory / "SEMANTIC_EVALUATION_FROZEN.json", evaluation)
    capability = authorize_t2_binding(
        RUNROOT, directory, version=version, candidate_ids=ids,
        execution_hash=freeze["self_hash"], reference=reference, evaluation=evaluation,
        read_document=read,
    )

    matrix1, order1, receipt1 = load_projection(version, "train1")
    matrix2, order2, receipt2 = load_projection(version, "train2")
    require(order1 == order2, "NUMERIC_FEATURE_ORDER")
    summaries = [
        {name: summarize_column(matrix[:, index]) for index, name in enumerate(order1)}
        for matrix in (matrix1, matrix2)
    ]
    bound = []; rejected = []; semantic_confirmed = 0
    for pair, candidate_id in zip(pairs, ids):
        value = admitted[candidate_id]
        if value is None:
            continue
        for index, rule in enumerate(value.proposal.rules):
            if rule.semantic not in truth[candidate_id]:
                continue
            semantic_confirmed += 1
            try:
                bound.append(bind_t2_rule(
                    capability, value, index, pair=pair,
                    train1_summary=(summaries[0][pair[0]], summaries[0][pair[1]]),
                    train2_summary=(summaries[1][pair[0]], summaries[1][pair[1]]),
                ))
            except ValueError as error:
                require(str(error) in ("UNMATERIALIZABLE_NORMAL_OPTION", "NONFINITE_NUMERIC_AUTHORITY", "NUMERIC_SCALE_INVALID"), "UNEXPECTED_NUMERIC_FAILURE")
                rejected.append({"candidate_id": candidate_id, "semantic": asdict(rule.semantic), "status": str(error)})
    numeric = seal({
        "version": version, "rules": [asdict(rule) for rule in bound], "rejections": rejected,
        "policy": POLICY, "evaluation_hash": evaluation["self_hash"], "provider_calls_allowed": False,
    })
    publish(directory / "NUMERIC_BOUND_PRIVATE.json", numeric)
    descriptors = convert(private_root(), directory / "formal_v4", tuple(bound))
    if version == "22.04":
        guard_matrix, guard_order, guard_receipt = load_projection(version, "train4")
        guard_hash = guard_receipt["projection_hash"]; file_id = "HAI22_TRAIN4"
    else:
        matrix3, guard_order, receipt3 = load_projection(version, "train3")
        guard_matrix = matrix3[239430:478801]
        guard_hash = digest({"projection": receipt3["projection_hash"], "rows": [239430, 478801]})
        file_id = "HAI21_TRAIN3_BLOCK_B"
    require(guard_order == order1, "GUARD_FEATURE_ORDER")
    states, burden = run_guard_portfolio(
        authority=Train4HiddenGuardAuthorityV1(guard_hash, file_id, len(guard_matrix)),
        matrix=guard_matrix, feature_order=order1, rules=tuple(bound),
    )
    retained = [rule for rule, state in zip(bound, states) if state[2] == "RETAINED"]
    retained_descriptors = [descriptor for descriptor, state in zip(descriptors, states) if state[2] == "RETAINED"]
    guard = seal({
        "version": version,
        "states": [{"candidate_id": cid, "semantic": asdict(semantic), "status": status} for cid, semantic, status in states],
        "retained_burden": safe(burden), "guard_projection_hash": guard_hash,
        "one_way": True, "provider_calls_allowed": False,
    })
    publish(directory / "GUARD_FROZEN.json", guard)
    private_portfolio = seal({
        "version": version, "rules": [asdict(rule) for rule in retained],
        "descriptor_hashes": [descriptor.descriptor_hash for descriptor in retained_descriptors],
        "guard_hash": guard["self_hash"], "provider_bundle_hash": bundle["self_hash"],
    })
    publish(directory / "PORTFOLIO_PRIVATE.json", private_portfolio)

    usage = _actual_usage(version)
    terminal_counts = Counter(row["terminal"] for row in terminal_rows)
    call_accepts = Counter(
        row["call_count"] for row in terminal_rows
        if row["terminal"] in ("ACCEPTED_RULE_SET", "INTENTIONAL_NO_RULE")
    )
    feedback_pairs = sum(bool(row["feedback"]) for row in terminal_rows)
    public = seal({
        "schema": "xver_t2_agentic_heldout_candidate_v1",
        "portfolio_id": f"HAI{version[:2]}_T2_AGENTIC_HELDOUT_CANDIDATE_V1",
        "version": version, "status": "HELDOUT_CANDIDATE_NOT_ATTACK_VALIDATED_NOT_PRODUCTION",
        "candidate_hash": candidate["self_hash"], "candidate_N": len(ids),
        "evidence_hash": document(PUB / f"HAI{version[:2]}_EVIDENCE_FREEZE_V1.json")["self_hash"],
        "provider_bundle_hash": bundle["self_hash"], "reference_hash": reference["self_hash"],
        "evaluation_hash": evaluation["self_hash"], "numeric_hash": numeric["self_hash"],
        "guard_hash": guard["self_hash"], "execution_freeze_hash": freeze["self_hash"],
        "calls": usage["calls"], "input_tokens": usage["input_tokens"], "output_tokens": usage["output_tokens"],
        "total_tokens": usage["total_tokens"], "standard_price_estimate_usd": usage["standard_price_estimate_usd"],
        "terminal_counts": dict(terminal_counts), "first_call_accepts": call_accepts[1],
        "second_call_accepts": call_accepts[2], "third_call_accepts": call_accepts[3],
        "feedback_actions": sum(len(row["feedback"]) for row in terminal_rows),
        "distinct_feedback_pairs": feedback_pairs,
        "train2_admitted_pairs": sum(value is not None for value in admitted.values()),
        "train2_admitted_rules": sum(len(value.proposal.rules) for value in admitted.values() if value),
        "semantic_confirmed_rules": semantic_confirmed, "numeric_bound_rules": len(bound),
        "numeric_rejection_counts": dict(Counter(row["status"] for row in rejected)),
        "Formal_V4_rules": len(descriptors), "guard_retained_rules": len(retained),
        "final_pair_count": len({(rule.source, rule.target) for rule in retained}),
        "rules": [
            {"relation_id": descriptor.relation_id, "source": rule.source, "target": rule.target,
             "semantic": asdict(rule.semantic), "descriptor_hash": descriptor.descriptor_hash}
            for rule, descriptor in zip(retained, retained_descriptors)
        ],
        "strict_metrics": safe(strict_metrics(truth, predictions)),
        "guard_state_counts": dict(Counter(state[2] for state in states)),
        "normal_burden": safe(burden), "provider_information_roles": ["STRUCTURAL20", "STAT_TRAIN1", "GLOBAL5_TRAIN1"],
        "event_evidence_transmitted": False, "selection_between_T0_T2": False,
        "attack_accesses": 0, "policy_searches": 0,
    })
    publish(PUBLIC / f"HAI{version[:2]}_T2_PORTFOLIO_AUTHORITY_V1.json", public)
    if version == "22.04":
        for split in ("train5", "train6"):
            matrix, feature_order, receipt = load_projection(version, split)
            require(feature_order == order1, "AUDIT_FEATURE_ORDER")
            result = audit_fixed_portfolio(matrix, feature_order, tuple(retained), "HAI22_" + split.upper())
            publish(PUBLIC / f"HAI22_T2_{split.upper()}_POSTFREEZE_AUDIT_V1.json", seal({
                "version": version, "split": split, "role": "POSTFREEZE_OBSERVATION_NO_SELECTION",
                "portfolio_hash": public["self_hash"], "projection_hash": receipt["projection_hash"],
                "burden": safe(result), "membership_changed": False, "numeric_changed": False,
                "provider_calls_after_audit": 0, "attack_accesses": 0,
            }))
    return public


def main() -> None:
    freeze = document(PUBLIC / "XVER_T2_PROVIDER_EXECUTION_FREEZE_V3.json")
    repair = document(PUBLIC / "XVER_T2_POSTPROVIDER_REPAIR_V1.json")
    require(
        repair["provider_execution_freeze_hash"] == freeze["self_hash"]
        and repair["scientific_method_changed"] is False
        and repair["provider_outputs_changed"] is False
        and repair["new_finalizer_hash"] == sha256_file(ROOT / "scripts/finalize_xver_t2_provider_v1.py"),
        "POSTPROVIDER_REPAIR_AUTHORITY",
    )
    combined, bundles = _provider_barrier(freeze)
    results = {version: finalize_version(version, freeze, bundles[version]) for version in VERSIONS}
    combined_usage = {version: _actual_usage(version) for version in VERSIONS}
    result = seal({
        "schema": "xver_t2_provider_execution_result_v1", "status": "COMPLETE_NORMAL_ONLY",
        "execution_freeze_hash": freeze["self_hash"], "provider_bundle_hash": combined["self_hash"],
        "portfolio_hashes": {version: results[version]["self_hash"] for version in VERSIONS},
        "usage": combined_usage,
        "combined": {
            "calls": sum(row["calls"] for row in combined_usage.values()),
            "input_tokens": sum(row["input_tokens"] for row in combined_usage.values()),
            "output_tokens": sum(row["output_tokens"] for row in combined_usage.values()),
            "total_tokens": sum(row["total_tokens"] for row in combined_usage.values()),
            "standard_price_estimate_usd": format(sum(Decimal(row["standard_price_estimate_usd"]) for row in combined_usage.values()), ".6f"),
        },
        "provider_calls_after_hidden_confirmation": 0, "attack_accesses": 0,
        "next": "MULTIPANEL-PRE-DG05-FREEZE-001",
    })
    publish(PUBLIC / "XVER_T2_PROVIDER_EXECUTION_RESULT_V1.json", result)
    print(json.dumps({"status": result["status"], "portfolio_hashes": result["portfolio_hashes"]}))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(json.dumps({"status": "FAIL_CLOSED", "error_type": type(error).__name__, "code": str(error)}))
        raise SystemExit(2)
