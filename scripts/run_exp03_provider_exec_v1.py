"""Freeze and execute the separately authorized reference-only EXP-03 study.

Only this coordinator entrypoint owns provider outputs. No dataset reader,
detector, runtime execution, or historical scientific producer is imported.
"""
from __future__ import annotations

import argparse
from dataclasses import fields
from datetime import datetime, timezone
from hashlib import sha256
import json
import platform
from pathlib import Path
import subprocess
import sys

from paperworks.validation_v2 import exp03_construction_v1 as e
from paperworks.validation_v2 import exp03_live_contract_v1 as c
from paperworks.validation_v2.exp03_live_custody_v1 import SingleWriterLedger, encoded, replay_ledger
from paperworks.validation_v2.formal_v4_authority_v1 import FormalV4ArtifactBindingV1, load_formal_v4_numeric_value_map_v1
from paperworks.validation_v2.numeric_policy_v1 import ConfirmedRelationIdentityV1, ConfirmedCohortAuthorityV1, validate_confirmed_cohort_authority_v1
from paperworks.validation_v2.private_vault_v1 import validate_private_path_v1, publish_private_bytes_v1

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = Path("research_control_center/validation_v2/exp03/execution_v1")
CORE = Path("research_control_center/validation_v2/core_v2a/authorities")
CODE = (
    "src/paperworks/validation_v2/exp03_live_contract_v1.py",
    "src/paperworks/validation_v2/exp03_live_custody_v1.py",
    "scripts/run_exp03_provider_exec_v1.py",
    "src/paperworks/validation_v2/exp03_construction_v1.py",
    "src/paperworks/validation_v2/formal_v4_authority_v1.py",
    "src/paperworks/validation_v2/numeric_policy_v1.py",
    "src/paperworks/validation_v2/private_vault_v1.py",
)
AUTHORITIES = (
    str(CORE / "V2A_CONFIRMED_COHORT_AUTHORITY.json"),
    str(CORE / "V2A_FORMAL_V4_PORTFOLIO_AUTHORITY.json"),
    str(CORE / "EXP02_SELECTED_POLICY_AUTHORITY_V2A.json"),
    "research_control_center/validation_v2/preregistration/EXP03_PREREGISTRATION_V2.json",
    "research_control_center/validation_v2/staging/EXP03_PREREGISTRATION_DRAFT.json",
    "research_control_center/validation_v2/exp03/DG03_FIXED_SNAPSHOT_APPROVAL_V1.json",
    "research_control_center/validation_v2/exp03/MODEL_ACCESS_RECEIPT_V1.json",
    "research_control_center/validation_v2/exp03/EXP03_EXECUTION_METHOD_V1.md",
)


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def seal(doc):
    return {**doc, "self_hash": c.h(doc)}


def replay(doc):
    if doc["self_hash"] != c.h({k: v for k, v in doc.items() if k != "self_hash"}):
        raise ValueError("SELF_HASH_MISMATCH")


def write(path, doc):
    publish_private_bytes_v1(Path(path), encoded(doc) + b"\n")


def vault_root():
    common = Path(git("rev-parse", "--git-common-dir"))
    if not common.is_absolute():
        common = ROOT / common
    return common.resolve().parent.parent / "paper_v_20260625_private_vault"


def load_inputs():
    cohort = read(ROOT / CORE / "V2A_CONFIRMED_COHORT_AUTHORITY.json")
    kwargs = {f.name: cohort[f.name] for f in fields(ConfirmedCohortAuthorityV1)}
    kwargs["relations"] = tuple(ConfirmedRelationIdentityV1(**r) for r in kwargs["relations"])
    typed = ConfirmedCohortAuthorityV1(**kwargs)
    if validate_confirmed_cohort_authority_v1(typed) != c.COHORT_HASH:
        raise ValueError("COHORT_AUTHORITY_MISMATCH")
    portfolio = read(ROOT / CORE / "V2A_FORMAL_V4_PORTFOLIO_AUTHORITY.json")
    if portfolio["authority_hash"] != c.PORTFOLIO_HASH or c.h({k: v for k, v in portfolio.items() if k != "authority_hash"}) != c.PORTFOLIO_HASH:
        raise ValueError("PORTFOLIO_AUTHORITY_MISMATCH")
    descriptors = tuple(c.descriptor_from_json(r) for r in portfolio["descriptors"])
    if len(descriptors) != 39 or {d.relation_id for d in descriptors} != {r.relation_id for r in typed.relations}:
        raise ValueError("FULL_39_COHORT_REQUIRED")
    for descriptor in descriptors:
        relation = next(r for r in typed.relations if r.relation_id == descriptor.relation_id)
        for field in ("source", "target", "source_direction", "target_direction", "selected_horizon_seconds", "relation_binding_hash"):
            if getattr(descriptor, field) != getattr(relation, field):
                raise ValueError("COHORT_DESCRIPTOR_BINDING_MISMATCH")
    # Exact recorded private object, not a scan or a runtime/test1 loader.
    numeric = portfolio["numeric_authority_binding"]
    relative = "objects/V2A_NUMERIC_AUTHORITY/" + numeric["content_sha256"]
    path = validate_private_path_v1(vault_root() / relative, allowed_root=vault_root())
    if not path.is_file() or sha256(path.read_bytes()).hexdigest() != numeric["content_sha256"]:
        raise ValueError("BLOCKED_EXP03_NUMERIC_CUSTODY")
    binding = FormalV4ArtifactBindingV1(numeric["artifact_id"], relative, numeric["content_sha256"])
    checked = load_formal_v4_numeric_value_map_v1(descriptors=descriptors, numeric_authority_binding=binding, repository_root=vault_root())
    if len(checked) != 39 or any(len(values) != 10 for _, values in checked):
        raise ValueError("NUMERIC_REFERENCE_COVERAGE_MISMATCH")
    del checked
    return descriptors, cohort, numeric["content_sha256"]


def build_bundle():
    c.validate_approval(read(ROOT / "research_control_center/validation_v2/exp03/DG03_FIXED_SNAPSHOT_APPROVAL_V1.json"))
    descriptors, cohort, numeric_hash = load_inputs()
    projections = [c.projection_payload(d, cohort["confirmation_artifact_hash"]) for d in descriptors]
    projection_hash = c.h({"projections": projections})
    policy = c.model_policy()
    config = {"schema": "exp03_execution_configuration_v1", "policy": policy,
              "cohort_hash": c.COHORT_HASH, "portfolio_hash": c.PORTFOLIO_HASH,
              "projection_hash": projection_hash, "prompt_hash": c.h({"prompt": c.PROMPT}),
              "schema_hash": c.h(c.schema()), "numeric_custody_hash": numeric_hash,
              "summary_semantics": "PUBLIC_CONFIRMED_IDENTITY_ONLY_NO_RAW_STATISTICS",
              "construction_semantics": "EXACT_BOUND_FORMAL_V4_REFERENCE_CONSTRUCTION",
              "no_rule_metric": "STRUCTURAL_CONTRACT_CONFIRMATION_NOT_EXPERT_APPROPRIATENESS",
              "schedule_policy": "EXISTING_SORTED_RELATION_ARM_REPEAT_SCHEDULE",
              "test1_allowed": False, "test2_allowed": False, "heldout_allowed": False}
    auth = e.build_provider_execution_authorization_v1(
        dg03_approved=True, approval_reference="DG03_FIXED_SNAPSHOT_APPROVAL_V1",
        provider_id="OPENAI_RESPONSES", model_snapshot=c.MODEL, natural_relation_count=39,
        maximum_input_tokens_per_call=c.INPUT_CAP, maximum_output_tokens_per_call=c.OUTPUT_CAP,
        maximum_total_tokens=c.TOTAL_TOKENS, config_hash=c.h(config), evidence_projection_hash=projection_hash,
        model_policy_hash=c.h(policy), template_hash=c.h({"prompt": c.PROMPT, "schema": c.schema()}),
        privacy_assessment_hash=c.h({"closed_projection": True, "private_values_sent": False, "dataset_reads": False}),
        expected_artifact_hash=c.h({"terminals": 390, "max_calls": 819, "private_append_only": True}),
    )
    schedule = e.build_natural_schedule_v1(relation_ids=[d.relation_id for d in descriptors], cohort_hash=c.COHORT_HASH,
                                          config_hash=auth.config_hash, evidence_projection_hash=projection_hash)
    upper_bounds = []
    for projection in projections:
        for feedback in (None, {"action": "retrieve", "issue_codes": ["NUMERIC_REFERENCE_MISMATCH"], "same_corpus_numeric_reference_ids": projection["numeric_reference_ids"]},
                         {"action": "revise", "issue_codes": ["NUMERIC_REFERENCE_MISMATCH"], "same_corpus_numeric_reference_ids": []}):
            request = c.request_document(projection, auth, feedback)
            upper_bounds.append(c.input_upper_bound(request))
    if max(upper_bounds) > c.INPUT_CAP:
        raise ValueError("FROZEN_REQUEST_TOO_LARGE_FOR_INPUT_CAP")
    return descriptors, projections, config, auth, schedule, max(upper_bounds)


def freeze():
    descriptors, projections, config, auth, schedule, max_input = build_bundle()
    access = read(ROOT / "research_control_center/validation_v2/exp03/MODEL_ACCESS_RECEIPT_V1.json")
    replay(access)
    if access["status"] != "MODEL_METADATA_ACCESS_PASS" or access["model_snapshot"] != c.MODEL:
        raise ValueError("MODEL_ACCESS_REQUIRED")
    commit = git("rev-parse", "HEAD")
    bindings = {}
    imported = {str(Path(module.__file__).resolve().relative_to(ROOT)).replace("\\", "/")
                for name, module in sys.modules.items() if name.startswith("paperworks") and getattr(module, "__file__", None)}
    for relative in sorted({*CODE, *AUTHORITIES, *imported}):
        relative = relative.replace("\\", "/")
        raw = (ROOT / relative).read_bytes()
        frozen = subprocess.check_output(["git", "show", commit + ":" + relative], cwd=ROOT)
        if raw != frozen:
            raise ValueError("UNCOMMITTED_EXECUTION_DEPENDENCY")
        bindings[relative] = sha256(raw).hexdigest()
    bundle = seal({"schema": "exp03_provider_execution_freeze_v1", "source_commit": commit,
        "created_utc": datetime.now(timezone.utc).isoformat(), "bindings": bindings,
        "configuration": config, "authorization": auth.to_dict(), "schedule": schedule.to_dict(),
        "projections": projections, "maximum_request_input_upper_bound": max_input,
        "response_schema": c.schema(), "prompt": c.PROMPT,
        "one_call_gate": "FIRST_SCHEDULED_T1_CALL_TRANSPORT_SCHEMA_MODEL_USAGE_CUSTODY_PASS_BEFORE_REMAINING",
        "full_schedule_generation_authorized": True, "test_data_access_authorized": False,
        "private_numeric_replay": "PASS_39_RELATIONS_390_REFERENCES",
        "environment": {"python": platform.python_version(), "implementation": platform.python_implementation(),
                        "os": platform.system(), "machine": platform.machine(), "transport": "stdlib.http.client.HTTPSConnection"}})
    write(ROOT / PUBLIC / "EXP03_EXECUTION_FREEZE_V1.json", bundle)
    print(json.dumps({"status": "FROZEN_PENDING_INDEPENDENT_QA_COMMIT", "self_hash": bundle["self_hash"], "max_input_upper_bound": max_input}))


def request_result(call, descriptor):
    response = call["response"]
    content = [part for item in response.get("output", []) if item.get("type") == "message" for part in item.get("content", [])]
    if any(part.get("type") == "refusal" for part in content):
        return None, {"status": "PROVIDER_ERROR", "issues": [], "projection_hash": None}, "PROVIDER_ERROR"
    if response.get("status") != "completed":
        return None, {"status": "EMPTY_RESPONSE", "issues": [], "projection_hash": None}, "EMPTY_RESPONSE"
    texts = [part["text"] for part in content if part.get("type") == "output_text"]
    if len(texts) != 1 or not texts[0].strip():
        return None, {"status": "EMPTY_RESPONSE", "issues": [], "projection_hash": None}, "EMPTY_RESPONSE"
    try:
        proposal = c.strict_parse(texts[0])
    except (ValueError, TypeError):
        return None, {"status": "PARSE_FAILURE", "issues": [], "projection_hash": None}, "NONEMPTY_RESPONSE"
    return proposal, c.verify_proposal(proposal, descriptor), "NONEMPTY_RESPONSE"


def make_call_receipt(call, key, proposal, completion, auth):
    attempt = e.build_provider_attempt_receipt_v1(authorization=auth, relation_id=key[0], arm=e.ConstructionArmV1(key[1]),
        repeat_index=key[2], call_index=call["index"], attempt_index=1,
        request_hash=call["request_hash"], response_hash=call["response_hash"],
        result_class="TERMINAL_PROVIDER_ERROR" if completion == "PROVIDER_ERROR" else "SUCCESS",
        input_tokens=call["input_tokens"], output_tokens=call["output_tokens"], latency_ms=call["latency_ms"])
    return e.build_provider_call_receipt_v1(authorization=auth, attempts=(attempt,), completion_class=completion,
        parsed_proposal_hash=c.h(proposal) if proposal is not None else None)


def no_rule_receipt(proposal, response_hash, relation_id, auth):
    if proposal is None or proposal["decision"] != "NO_RULE":
        return None
    eligibility = e.build_no_rule_eligibility_projection_v1(relation_id=relation_id,
        evidence_projection_hash=auth.evidence_projection_hash, variable_supported=True,
        evidence_complete=True, numeric_authority_complete=True)
    return e.validate_semantic_no_rule_v1(projection=eligibility, outcome=e.ConstructionOutcomeV1.INTENTIONAL_NO_RULE,
        structured_response_hash=response_hash, structured_reason_code=proposal["reason"])


def terminal_kwargs(verdict, proposal, no_rule):
    status = verdict["status"]
    return dict(outcome=e.ConstructionOutcomeV1(status),
        reason_code="VERIFIER_ACCEPTED" if status == "ACCEPTED_PROPOSAL" else e.TERMINAL_REASON_CODES[status],
        proposal_hash=c.h(proposal) if proposal is not None else None,
        verifier_result_hash=c.h(verdict) if proposal is not None else None,
        executable_projection_hash=verdict.get("projection_hash"),
        semantic_no_rule_confirmed=True if no_rule else None,
        semantic_no_rule_validation_receipt=no_rule)


def synthetic_stress():
    definitions = (
        ("INTENTIONAL_NO_RULE", {"structured_no_rule": True}, ()),
        ("UNSUPPORTED_EVIDENCE", {"evidence_complete": False}, ()),
        ("PROVIDER_ERROR", {"transport_state": "TERMINAL_ERROR"}, ()),
        ("EMPTY_RESPONSE", {"response_state": "EMPTY"}, ()),
        ("PARSE_FAILURE", {"strict_parse_valid": False}, ()),
        ("VERIFIER_REJECTION", {"verifier_state": "REJECTED_FINAL"}, ()),
        ("BUDGET_EXHAUSTION", {"verifier_state": "REJECTED_REPAIRABLE", "calls_used": 3}, ("revise", "revise")),
        ("RETRIEVAL_FAILURE", {"retrieval_state": "IDENTITY_FAILURE"}, ("retrieve",)),
        ("SYSTEM_ERROR", {"custody_valid": False}, ()),
        ("UNSUPPORTED_EVIDENCE", {"numeric_authority_complete": False}, ()),
    )
    fixtures = []
    for ordinal in range(39):
        for index, (terminal, kwargs, actions) in enumerate(definitions):
            fixture_id = f"SYNTHETIC-{ordinal:02d}-{index:02d}"
            inputs = e.build_stress_classifier_input_v1(fixture_id=fixture_id, **kwargs)
            fixtures.append(e.build_stress_fixture_receipt_v1(fixture_id=fixture_id,
                expected_terminal=e.ConstructionTerminalClassV1(terminal), classifier_input=inputs, controller_actions=actions))
    return e.aggregate_stress_metrics_v1(fixtures), fixtures


def verify_source_commit(bundle):
    if subprocess.run(["git", "merge-base", "--is-ancestor", bundle["source_commit"], "HEAD"], cwd=ROOT, capture_output=True).returncode:
        raise ValueError("EXECUTION_SOURCE_ANCESTRY")
    branch = git("branch", "--show-current")
    if branch not in {"validation-v2", "validation-v2-exp03-provider-exec-001"}:
        raise ValueError("WRONG_SCIENTIFIC_BRANCH")
    remote = git("ls-remote", "origin", "refs/heads/" + branch)
    if not remote or remote.split()[0] != git("rev-parse", "HEAD"):
        raise ValueError("EXECUTION_ORIGIN_PARITY")
    for name in ("EXP03_EXECUTION_FREEZE_V1.json", "PREEXECUTION_QA_V1.json"):
        relative = (PUBLIC / name).as_posix()
        if subprocess.check_output(["git", "show", "HEAD:" + relative], cwd=ROOT) != (ROOT / relative).read_bytes():
            raise ValueError("UNCOMMITTED_EXECUTION_FREEZE_OR_QA")


def run():
    bundle = read(ROOT / PUBLIC / "EXP03_EXECUTION_FREEZE_V1.json")
    replay(bundle)
    qa = read(ROOT / PUBLIC / "PREEXECUTION_QA_V1.json")
    replay(qa)
    if qa["status"] != "PASS" or qa["execution_freeze_hash"] != bundle["self_hash"]:
        raise ValueError("INDEPENDENT_PREEXECUTION_QA_REQUIRED")
    verify_source_commit(bundle)
    for relative, digest in bundle["bindings"].items():
        if sha256((ROOT / relative).read_bytes()).hexdigest() != digest:
            raise ValueError("EXECUTION_BINDING_CHANGED")
    if bundle["environment"]["python"] != platform.python_version() or bundle["environment"]["os"] != platform.system():
        raise ValueError("FROZEN_ENVIRONMENT_CHANGED")
    descriptors, projections, config, auth, schedule, _ = build_bundle()
    if auth.to_dict() != bundle["authorization"] or schedule.to_dict() != bundle["schedule"] or config != bundle["configuration"] or projections != bundle["projections"]:
        raise ValueError("EXECUTION_FREEZE_REPLAY_MISMATCH")
    if git("status", "--porcelain"):
        raise ValueError("CLEAN_WORKTREE_REQUIRED")
    private = vault_root() / "exp03-provider-exec-001"
    keys = [(r.relation_id, r.arm, r.repeat_index) for r in schedule.entries]
    ledger = SingleWriterLedger(private, allowed_root=vault_root(), contract_hash=bundle["self_hash"], schedule=keys,
        projections={p["relation_id"]: p for p in projections}, authorization=auth)
    stress, stress_fixtures = synthetic_stress()
    write(private / "SYNTHETIC_STRESS_FIXTURES_V1.json", seal({"fixtures": [f.to_dict() for f in stress_fixtures]}))
    write(private / "SYNTHETIC_STRESS_METRICS_V1.json", stress.to_dict())
    by_relation = {d.relation_id: (d, p) for d, p in zip(descriptors, projections)}
    terminals = []
    shared = dict(authorization=auth, config_hash=auth.config_hash, evidence_projection_hash=auth.evidence_projection_hash,
                  model_policy_hash=auth.model_policy_hash, template_hash=auth.template_hash)
    for key in keys:
        descriptor, projection = by_relation[key[0]]
        receipts, actions, draws, draw_details = [], [], [], []
        feedback, semantic = None, None
        if key[1] == "T0":
            proposal = c.template_proposal(projection)
            verdict = c.verify_proposal(proposal, descriptor)
        else:
            for index in range(1, (1 if key[1] == "T1" else 3) + 1):
                request = c.request_document(projection, auth, feedback)
                call = ledger.call(key, index, request)
                proposal, verdict, completion = request_result(call, descriptor)
                receipt = make_call_receipt(call, key, proposal, completion, auth)
                receipts.append(receipt)
                semantic = no_rule_receipt(proposal, receipt.response_hash, key[0], auth)
                can_continue, next_feedback = False, None
                if key[1] == "T2" and verdict["status"] == "VERIFIER_REJECTION":
                    try:
                        next_feedback = c.feedback_for(verdict, "retrieve" in actions, projection)
                    except ValueError:
                        next_feedback = None
                    if next_feedback is not None:
                        if index == 3:
                            verdict = {**verdict, "status": "BUDGET_EXHAUSTION"}
                        else:
                            can_continue = True
                ledger.verdict(key, verdict, continue_t2=can_continue)
                if ledger.calls == 1:
                    if proposal is None:
                        ledger.append("ONE_CALL_GATE_FAILED", {"issue_code": "FIRST_SCIENTIFIC_CALL_SCHEMA_GATE_FAILED", "automatic_resend": False, "calls": 1})
                        raise ValueError("FIRST_SCIENTIFIC_CALL_SCHEMA_GATE_FAILED")
                    one = seal({"schema": "exp03_one_call_gate_v1", "status": "PASS", "calls": 1,
                        "execution_freeze_hash": bundle["self_hash"], "request_hash": call["request_hash"],
                        "response_hash": call["response_hash"], "model": c.MODEL,
                        "input_tokens": call["input_tokens"], "output_tokens": call["output_tokens"],
                        "cost_usd": call["cost_usd"], "accepted_not_required_for_gate": True})
                    write(private / "ONE_CALL_GATE_V1.json", one)
                    ledger.append("ONE_CALL_GATE_PASS", {"receipt_hash": one["self_hash"]})
                    print(json.dumps({"status": "ONE_CALL_GATE_PASS", "calls": 1}), flush=True)
                if key[1] == "T1-B":
                    kwargs = terminal_kwargs(verdict, proposal, semantic)
                    draws.append(e.build_t1b_draw_v1(authorization=auth, draw_index=index, call_receipt=receipt,
                        **{k: v for k, v in kwargs.items() if k not in {"executable_projection_hash", "semantic_no_rule_confirmed"}}))
                    draw_details.append((proposal, verdict, semantic))
                elif can_continue:
                    feedback = next_feedback
                    actions.append(feedback["action"])
                else:
                    break
        selection = None
        if key[1] == "T1-B":
            selection = e.select_t1b_lowest_admissible_v1(draws, auth)
            if selection.selected_draw_index is not None:
                proposal, verdict, semantic = draw_details[selection.selected_draw_index - 1]
            else:
                proposal, semantic = None, None
                verdict = {"status": "ALL_DRAWS_FAILED", "projection_hash": None, "issues": []}
        terminal = e.build_terminal_record_v1(**shared, relation_id=key[0], arm=e.ConstructionArmV1(key[1]), repeat_index=key[2],
            **terminal_kwargs(verdict, proposal, semantic), call_receipts=receipts,
            t1b_selection_receipt=selection, controller_actions=actions)
        ledger.terminal(key, terminal.to_dict())
        terminals.append(terminal)
        if len(terminals) % 10 == 0:
            print(json.dumps({"status": "RUNNING", "completed_relations": len(terminals) // 10,
                              "total_relations": 39, "calls": ledger.calls, "cost_usd": str(ledger.usd)}), flush=True)
    e.validate_complete_natural_schedule_v1(schedule, terminals, auth)
    aggregate = e.aggregate_natural_metrics_v1(terminals, auth, schedule=schedule)
    write(private / "NATURAL_METRICS_FULL_V1.json", aggregate.to_dict())
    # Independently accessible complete private record set for read-only QA.
    write(private / "TERMINAL_SET_V1.json", seal({"records": [r.to_dict() for r in terminals]}))
    arm_metrics = []
    for arm in ("T0", "T1", "T1-B", "T2"):
        rows = [r for r in terminals if r.arm == arm]
        accepted = [r for r in rows if r.outcome == "ACCEPTED_PROPOSAL"]
        activated = [r for r in rows if r.controller_actions]
        arm_metrics.append({"arm": arm, "scheduled": len(rows), "accepted": len(accepted),
            "first_call_accepted": sum((r.t1b_selection_receipt.draw_outcomes[0].outcome == "ACCEPTED_PROPOSAL") if r.t1b_selection_receipt else r.outcome == "ACCEPTED_PROPOSAL" and r.generation_calls <= 1 for r in rows),
            "executable_projections": sum(r.executable_projection_hash is not None for r in rows),
            "feedback_activated": len(activated), "feedback_repair_success": sum(r.outcome == "ACCEPTED_PROPOSAL" for r in activated),
            "feedback_repair_denominator": len(activated),
            "calls": sum(r.generation_calls for r in rows),
            "terminal_counts": {name: sum(r.outcome == name for r in rows) for name in (*e.TERMINAL_CLASSES, "ACCEPTED_PROPOSAL", "ALL_DRAWS_FAILED")},
            "by_repeat": [{"repeat": repeat, "scheduled": sum(r.repeat_index == repeat for r in rows),
                           "accepted": sum(r.repeat_index == repeat and r.outcome == "ACCEPTED_PROPOSAL" for r in rows)} for repeat in ((0,) if arm == "T0" else (1, 2, 3))]})
    final = seal({"schema": "exp03_natural_results_v1", "status": "COMPLETE_PENDING_INDEPENDENT_QA",
        "execution_freeze_hash": bundle["self_hash"], "terminal_count": len(terminals), "arm_metrics": arm_metrics,
        "actual_calls": ledger.calls, "input_tokens": ledger.input_tokens, "output_tokens": ledger.output_tokens,
        "total_tokens": ledger.input_tokens + ledger.output_tokens, "standard_api_cost_upper_bound_usd": str(ledger.usd),
        "model_snapshot": c.MODEL, "natural_metrics_hash": aggregate.self_hash,
        "raw_response_replay": "REQUIRED_INDEPENDENT_QA", "test1_accesses": 0, "test2_accesses": 0,
        "heldout_accesses": 0, "dataset_payload_reads": 0, "numeric_values_sent": 0,
        "portfolio_changes": 0, "next_gate": "DG-04"})
    write(private / "RESULTS_V1.json", final)
    write(ROOT / PUBLIC / "EXP03_NATURAL_RESULTS_V1.json", final)
    write(ROOT / PUBLIC / "EXP03_SYNTHETIC_STRESS_METRICS_V1.json", stress.to_dict())
    ledger.append("RUN_COMPLETE", {"results_hash": final["self_hash"], "calls": ledger.calls})
    print(json.dumps({"status": "COMPLETE_PENDING_INDEPENDENT_QA", "calls": ledger.calls, "cost_usd": str(ledger.usd)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("freeze", "execute"))
    args = parser.parse_args()
    try:
        freeze() if args.mode == "freeze" else run()
    except Exception as error:
        # Safe constant status only. Full exception text could include private data.
        safe_codes = {"BLOCKED_EXP03_NUMERIC_CUSTODY", "FROZEN_REQUEST_TOO_LARGE_FOR_INPUT_CAP", "UNCOMMITTED_EXECUTION_DEPENDENCY", "CLEAN_WORKTREE_REQUIRED"}
        from paperworks.validation_v2.exp03_live_custody_v1 import ProviderCustodyStop
        code = str(error) if isinstance(error, ProviderCustodyStop) or str(error) in safe_codes else "EXP03_LOCAL_CONTRACT_GATE_FAILED"
        print(json.dumps({"status": "BLOCKED", "issue_code": code}), flush=True)
        raise SystemExit(2)
