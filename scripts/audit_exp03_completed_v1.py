"""Read-only completed EXP03 custody replay; never a provider/data runner."""
from __future__ import annotations
from dataclasses import fields, is_dataclass
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import sys
import types
from typing import get_args, get_origin, get_type_hints, Union

from paperworks.validation_v2 import exp03_construction_v1 as e
from paperworks.validation_v2 import exp03_live_contract_v1 as c
from paperworks.validation_v2.exp03_live_custody_v1 import replay_ledger, exact_request_guard, encoded
from paperworks.validation_v2.private_vault_v1 import validate_private_path_v1

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "research_control_center/validation_v2/exp03/execution_v1"


def decode(kind, value):
    if value is None:
        return None
    origin, arguments = get_origin(kind), get_args(kind)
    if origin in (Union, types.UnionType):
        return decode(next(t for t in arguments if t is not type(None)), value)
    if origin is tuple:
        return tuple(decode(arguments[0], item) for item in value)
    if isinstance(kind, type) and is_dataclass(kind):
        hints = get_type_hints(kind)
        result = kind(**{f.name: decode(hints[f.name], value[f.name]) for f in fields(kind)})
        assert result.to_dict() == value
        return result
    return value


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def vault_root():
    common = Path(subprocess.check_output(["git", "rev-parse", "--git-common-dir"], cwd=ROOT, text=True).strip())
    if not common.is_absolute():
        common = ROOT / common
    return common.resolve().parent.parent / "paper_v_20260625_private_vault"


def audit():
    if sys.flags.optimize:
        raise ValueError("OPTIMIZED_AUDIT_PROHIBITED")
    vault = vault_root()
    private = validate_private_path_v1(vault / "exp03-provider-exec-001", allowed_root=vault)
    def private_read(name, raw=False):
        if "/" in name or "\\" in name or name in {".", ".."}:
            raise ValueError("UNSAFE_AUDIT_MEMBER")
        path = validate_private_path_v1(private / name, allowed_root=vault)
        return path.read_bytes() if raw else read(path)
    bundle = read(PUBLIC / "EXP03_EXECUTION_FREEZE_V1.json")
    results = read(PUBLIC / "EXP03_NATURAL_RESULTS_V1.json")
    for document in (bundle, results):
        assert document["self_hash"] == c.h({k: v for k, v in document.items() if k != "self_hash"})
    assert results["execution_freeze_hash"] == bundle["self_hash"]
    for path, digest in bundle["bindings"].items():
        assert sha256((ROOT / path).read_bytes()).hexdigest() == digest
    ledger_path = validate_private_path_v1(private / "CALL_OUTPUT_COST_LATENCY_LEDGER.jsonl", allowed_root=vault)
    before = sha256(ledger_path.read_bytes()).hexdigest()
    ledger = replay_ledger(ledger_path)
    assert ledger[-1]["kind"] == "RUN_COMPLETE"
    assert all(r["contract_hash"] == bundle["self_hash"] for r in ledger)
    assert ledger[-1]["payload"]["results_hash"] == results["self_hash"]
    assert not any("FAILED" in r["kind"] or "UNRESOLVED" in r["kind"] for r in ledger)
    reservations = [r for r in ledger if r["kind"] == "CALL_RESERVED"]
    settled = [r for r in ledger if r["kind"] == "CALL_SETTLED"]
    gate = [r for r in ledger if r["kind"] == "ONE_CALL_GATE_PASS"]
    assert len(gate) == 1 and settled[0]["sequence"] < gate[0]["sequence"] < reservations[1]["sequence"]
    first = private_read("ONE_CALL_GATE_V1.json")
    assert first["self_hash"] == c.h({k: v for k, v in first.items() if k != "self_hash"}) == gate[0]["payload"]["receipt_hash"]
    assert first["execution_freeze_hash"] == bundle["self_hash"] and first["status"] == "PASS" and first["calls"] == 1
    for key in ("request_hash", "response_hash", "model", "input_tokens", "output_tokens", "cost_usd"):
        assert first[key] == settled[0]["payload"][key]
    assert len(reservations) == len(settled) == results["actual_calls"]
    assert len({r["payload"]["slot"] for r in reservations}) == len(reservations)
    it = ot = 0
    usd = Decimal(0)
    call_map = {}
    verdicts = [r for r in ledger if r["kind"] == "VERIFIER_CONTROLLER"]
    assert len(verdicts) == len(settled)
    descriptors = {d["relation_id"]: c.descriptor_from_json(d) for d in read(ROOT / "research_control_center/validation_v2/core_v2a/authorities/V2A_FORMAL_V4_PORTFOLIO_AUTHORITY.json")["descriptors"]}
    projections = {p["relation_id"]: p for p in bundle["projections"]}
    auth = decode(e.ProviderExecutionAuthorizationV1, bundle["authorization"])
    feedback_by_key, actions_by_key = {}, {}
    for ordinal, (reservation, settlement, recorded_verdict) in enumerate(zip(reservations, settled, verdicts), 1):
        r, s = reservation["payload"], settlement["payload"]
        assert re.fullmatch(r"[0-9]{4}-[123]", r["slot"])
        assert r["slot"] == s["slot"] and reservation["sequence"] < settlement["sequence"]
        request_raw = private_read(r["slot"] + "-request.json", True)
        response_raw = private_read(r["slot"] + "-response.json", True)
        assert sha256(request_raw).hexdigest() == r["request_hash"] == s["request_hash"]
        assert sha256(response_raw).hexdigest() == s["response_hash"]
        assert private_read(r["slot"] + "-dispatch.once")["reservation_hash"] == reservation["self_hash"]
        request, response = json.loads(request_raw), json.loads(response_raw)
        exact_request_guard(request)
        key = tuple(r["key"])
        assert r["key"] == s["key"] == recorded_verdict["payload"]["key"] and r["index"] == s["index"]
        assert request == c.request_document(projections[key[0]], auth, feedback_by_key.get(key))
        content = [part for item in response.get("output", []) if item.get("type") == "message" for part in item.get("content", [])]
        proposal = None
        if any(part.get("type") == "refusal" for part in content):
            verdict = {"status": "PROVIDER_ERROR", "issues": [], "projection_hash": None}
        elif response.get("status") != "completed":
            verdict = {"status": "EMPTY_RESPONSE", "issues": [], "projection_hash": None}
        else:
            texts = [part["text"] for part in content if part.get("type") == "output_text"]
            if len(texts) != 1 or not texts[0].strip():
                verdict = {"status": "EMPTY_RESPONSE", "issues": [], "projection_hash": None}
            else:
                try:
                    proposal = c.strict_parse(texts[0])
                    verdict = c.verify_proposal(proposal, descriptors[key[0]])
                except (ValueError, TypeError):
                    verdict = {"status": "PARSE_FAILURE", "issues": [], "projection_hash": None}
        actions = actions_by_key.setdefault(key, [])
        next_feedback = None
        if key[1] == "T2" and verdict["status"] == "VERIFIER_REJECTION":
            try:
                next_feedback = c.feedback_for(verdict, "retrieve" in actions, projections[key[0]])
            except ValueError:
                pass
        continuing = next_feedback is not None and s["index"] < 3
        if next_feedback is not None and s["index"] == 3:
            verdict = {**verdict, "status": "BUDGET_EXHAUSTION"}
        assert recorded_verdict["payload"]["verdict"] == verdict
        assert recorded_verdict["payload"]["continue_t2"] == continuing
        assert settlement["sequence"] < recorded_verdict["sequence"]
        if continuing:
            actions.append(next_feedback["action"])
            feedback_by_key[key] = next_feedback
        if s["index"] > 1 and key[1] == "T2":
            assert call_map[(*key, s["index"] - 1)]["continuing"]
        call_map[(*key, s["index"])] = {"settled": s, "proposal": proposal, "verdict": verdict, "continuing": continuing}
        assert response["model"] == c.MODEL
        assert response["usage"]["input_tokens"] == s["input_tokens"]
        assert response["usage"]["output_tokens"] == s["output_tokens"]
        assert c.cost(s["input_tokens"], s["output_tokens"]) == Decimal(s["cost_usd"])
        it += s["input_tokens"]
        ot += s["output_tokens"]
        usd += Decimal(s["cost_usd"])
        c.budget_guard(ordinal, it, ot, usd)
    terminal_set = private_read("TERMINAL_SET_V1.json")
    assert terminal_set["self_hash"] == c.h({"records": terminal_set["records"]})
    records = tuple(decode(e.ConstructionTerminalRecordV1, row) for row in terminal_set["records"])
    schedule = decode(e.NaturalScheduleReceiptV1, bundle["schedule"])
    e.validate_complete_natural_schedule_v1(schedule, records, auth)
    aggregate = e.aggregate_natural_metrics_v1(records, auth, schedule=schedule)
    assert aggregate.to_dict() == private_read("NATURAL_METRICS_FULL_V1.json")
    assert aggregate.self_hash == results["natural_metrics_hash"]
    assert it == results["input_tokens"] == aggregate.input_tokens
    assert ot == results["output_tokens"] == aggregate.output_tokens
    assert it + ot == results["total_tokens"]
    assert len(records) == results["terminal_count"]
    assert usd == Decimal(results["standard_api_cost_upper_bound_usd"])
    assert results == private_read("RESULTS_V1.json")
    frozen_terminals = [r["payload"] for r in ledger if r["kind"] == "TERMINAL_FROZEN"]
    assert len(frozen_terminals) == len(records)
    joined_calls = 0
    for index, record in enumerate(records):
        assert private_read(f"terminal-{index:04d}.json") == record.to_dict()
        assert frozen_terminals[index] == {"key": list(record.key), "terminal_hash": c.h(record.to_dict()), "outcome": record.outcome}
        outcomes = []
        for call in record.call_receipts:
            joined_calls += 1
            item = call_map[(*record.key, call.call_index)]
            s, proposal, verdict = item["settled"], item["proposal"], item["verdict"]
            assert call.request_hash == s["request_hash"]
            assert call.attempt_receipts[0].response_hash == s["response_hash"]
            assert call.parsed_proposal_hash == (c.h(proposal) if proposal is not None else None)
            assert (call.input_tokens, call.output_tokens, call.latency_ms) == (s["input_tokens"], s["output_tokens"], s["latency_ms"])
            outcomes.append(item)
        if record.arm == "T0":
            proposal = c.template_proposal(projections[record.relation_id])
            verdict = c.verify_proposal(proposal, descriptors[record.relation_id])
        elif record.arm == "T1-B":
            for draw, item in zip(record.t1b_selection_receipt.draw_outcomes, outcomes):
                assert draw.outcome == item["verdict"]["status"]
                assert draw.proposal_hash == (c.h(item["proposal"]) if item["proposal"] is not None else None)
                assert draw.verifier_result_hash == (c.h(item["verdict"]) if item["proposal"] is not None else None)
            selected = next((i for i, item in enumerate(outcomes, 1) if item["verdict"]["status"] == "ACCEPTED_PROPOSAL"), None)
            assert selected == record.t1b_selection_receipt.selected_draw_index
            proposal = outcomes[selected - 1]["proposal"] if selected else None
            verdict = outcomes[selected - 1]["verdict"] if selected else {"status": "ALL_DRAWS_FAILED", "projection_hash": None}
        else:
            proposal, verdict = outcomes[-1]["proposal"], outcomes[-1]["verdict"]
        assert record.outcome == verdict["status"]
        assert record.proposal_hash == (c.h(proposal) if proposal is not None else None)
        assert record.verifier_result_hash == (c.h(verdict) if proposal is not None else None)
        assert record.executable_projection_hash == verdict.get("projection_hash")
        assert list(record.controller_actions) == actions_by_key.get(record.key, [])
    assert joined_calls == len(call_map) == len(settled)
    assert len(results["arm_metrics"]) == 4 and {r["arm"] for r in results["arm_metrics"]} == {"T0", "T1", "T1-B", "T2"}
    for arm in results["arm_metrics"]:
        rows = [r for r in records if r.arm == arm["arm"]]
        assert len(rows) == arm["scheduled"]
        assert sum(r.outcome == "ACCEPTED_PROPOSAL" for r in rows) == arm["accepted"]
        assert sum(r.generation_calls for r in rows) == arm["calls"]
        assert sum(bool(r.controller_actions) for r in rows) == arm["feedback_activated"]
        assert sum(r.executable_projection_hash is not None for r in rows) == arm["executable_projections"]
        activated = [r for r in rows if r.controller_actions]
        assert len(activated) == arm["feedback_repair_denominator"]
        assert sum(r.outcome == "ACCEPTED_PROPOSAL" for r in activated) == arm["feedback_repair_success"]
        assert sum((r.t1b_selection_receipt.draw_outcomes[0].outcome == "ACCEPTED_PROPOSAL") if r.t1b_selection_receipt else r.outcome == "ACCEPTED_PROPOSAL" and r.generation_calls <= 1 for r in rows) == arm["first_call_accepted"]
        assert set(arm["terminal_counts"]) == {*e.TERMINAL_CLASSES, "ACCEPTED_PROPOSAL", "ALL_DRAWS_FAILED"}
        for outcome, count in arm["terminal_counts"].items():
            assert sum(r.outcome == outcome for r in rows) == count
        expected_repeats = {0} if arm["arm"] == "T0" else {1, 2, 3}
        assert len(arm["by_repeat"]) == len(expected_repeats) and {r["repeat"] for r in arm["by_repeat"]} == expected_repeats
        for repeat in arm["by_repeat"]:
            rr = [r for r in rows if r.repeat_index == repeat["repeat"]]
            assert len(rr) == repeat["scheduled"] and sum(r.outcome == "ACCEPTED_PROPOSAL" for r in rr) == repeat["accepted"]
    assert before == sha256(validate_private_path_v1(ledger_path, allowed_root=vault).read_bytes()).hexdigest()
    return {"status": "PASS", "freeze_hash": bundle["self_hash"], "results_hash": results["self_hash"],
        "ledger_file_hash": before, "ledger_tip": ledger[-1]["self_hash"], "records": len(records),
        "requests_responses_replayed": len(settled), "input_tokens": it, "output_tokens": ot,
        "standard_api_cost_upper_bound_usd": str(usd), "private_outputs_written": 0,
        "provider_calls": 0, "dataset_reads": 0,
        "repeat_stable_terminal_groups": aggregate.repeat_stable_terminal_groups,
        "repeat_stable_projection_groups": aggregate.repeat_stable_executable_projection_groups,
        "repeat_groups": aggregate.repeat_stability_denominator,
        "latency_total_ms": aggregate.latency_total_ms}


if __name__ == "__main__":
    try:
        print(json.dumps(audit(), sort_keys=True))
    except Exception:
        print('{"status":"FAIL_CLOSED_COMPLETED_REPLAY"}')
        raise SystemExit(2)
