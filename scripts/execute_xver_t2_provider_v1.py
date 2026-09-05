"""Approved HAI22/HAI21 external T2 provider execution.

The first scheduled HAI22 call is the receipt-first probe.  This program has
no retry, fallback, tool or concurrency path.  It never opens train3/train4;
post-provider normal closure is a separate program.
"""
from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
import argparse
import json
import os
from pathlib import Path
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from xver_execution_common import (
    ROOT, PUB, private_root, document, version_authorities, publish, seal,
    require, digest, sha256_file,
)
from paperworks.validation_v2.exp03b_contract_v1 import encoded
from paperworks.validation_v2.exp03b_execution_v2 import admit
from paperworks.validation_v2.exp03b_hidden_v2 import (
    Train2HiddenVerifierAuthorityV2, Train2SemanticEvidenceV2, feedback, verify,
)
from paperworks.validation_v2.exp03b_semantic_v2 import (
    SemanticTupleV1, StructuralTupleEvidenceV1,
    parse_proposal, proposal_document,
)
from paperworks.validation_v2.exp03b_custody_v1 import replay
from paperworks.validation_v2.xver_prompt_v1 import request_body, validate_global_retrieval
from paperworks.validation_v2.xver_provider_execution_v1 import (
    VERSIONS, XverCombinedProviderGateV1, validate_call_inventory,
    validate_serialized_request,
)


PUBLIC = PUB / "provider_execution_v1"
RUNROOT = private_root() / "provider_t2_v1"
ENDPOINT = "https://api.openai.com/v1/responses"


class ParsedResponseFailure(ValueError):
    pass


def _read(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8")); replay(value); return value


def _transport(body: dict) -> dict:
    """Exactly one HTTP attempt; credential is read only at dispatch."""
    key = os.environ.get("OPENAI_API_KEY")
    require(bool(key), "APPROVED_PROVIDER_CREDENTIAL_UNAVAILABLE")
    request = Request(
        ENDPOINT,
        data=encoded(body),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + key},
        method="POST",
    )
    try:
        with urlopen(request, timeout=60) as response:
            require(response.status == 200, "PROVIDER_HTTP_FAILURE")
            return json.loads(response.read())
    except HTTPError as error:
        if error.code in (401, 403):
            raise RuntimeError("AUTH_OR_AUTHORIZATION_FAILURE") from None
        if error.code in (429,):
            raise RuntimeError("AUTH_OR_QUOTA_FAILURE") from None
        raise RuntimeError("PROVIDER_HTTP_FAILURE") from None
    except (URLError, TimeoutError, json.JSONDecodeError) as error:
        raise RuntimeError("PROVIDER_SYSTEM_FAILURE") from None


def _response_proposal(response: dict):
    output = response.get("output", [])
    require(type(output) is list, "SCHEMA_CONTRACT_MISMATCH")
    no_tools = all(item.get("type") in ("reasoning", "message") for item in output)
    require(no_tools, "PROVIDER_TOOL_INVOCATION")
    text = "".join(
        part.get("text", "")
        for item in output if item.get("type") == "message"
        for part in item.get("content", []) if part.get("type") == "output_text"
    )
    try:
        require(bool(text), "EMPTY_RESPONSE")
        proposal = parse_proposal(json.loads(text))
    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
        raise ParsedResponseFailure("PARSE_FAILURE") from error
    return proposal, no_tools


def _structural(value: dict) -> Train2SemanticEvidenceV2:
    rows = tuple(
        StructuralTupleEvidenceV1(
            SemanticTupleV1(**row["semantic"]),
            **{key: item for key, item in row.items() if key != "semantic"},
        ) for row in value["rows"]
    )
    return Train2SemanticEvidenceV2(
        value["candidate_id"], value["source"], value["target"], value["input_hash"], rows
    )


def _authorities():
    freeze = document(PUBLIC / "XVER_T2_PROVIDER_EXECUTION_FREEZE_V2.json")
    approval = document(PUBLIC / "XVER_T2_PROVIDER_APPROVAL_RECEIPT_V2.json")
    for relative, expected in freeze["implementation_hashes"].items():
        require(sha256_file(ROOT / relative) == expected, "EXECUTION_CODE_CHANGED")
    require(freeze["integration_baseline"] == "be3ff48bd2abfafc81544357af0daff69a6721a2", "SOURCE_AUTHORITY_MISMATCH")
    budgets = {v: document(PUB / f"HAI{v[:2]}_T2_PROVIDER_BUDGET_V1.json") for v in VERSIONS}
    profiles = {v: document(PUB / f"HAI{v[:2]}_T2_TOKEN_PROFILE_V1.json") for v in VERSIONS}
    require({v: budgets[v]["self_hash"] for v in VERSIONS} == freeze["budget_hashes"], "BUDGET_AUTHORITY_MISMATCH")
    require(document(PUB / "XVER_PROVIDER_SERIALIZER_FREEZE_V1.json")["self_hash"] == freeze["serializer_hash"], "SERIALIZER_AUTHORITY_MISMATCH")
    require(document(PUB / "INDEPENDENT_EXECUTION_QA_V1.json")["self_hash"] == freeze["preexecution_QA_hash"], "INDEPENDENT_QA_CHANGED")
    require(document(PUB / "SEMANTIC_EXECUTION_AUTHORITY_V1.json")["self_hash"] == freeze["semantic_execution_hash"], "SEMANTIC_AUTHORITY_CHANGED")
    require(document(PUB / "GDN_EXECUTION_AUTHORITY_V2.json")["self_hash"] == freeze["GDN_execution_hash"], "GDN_AUTHORITY_CHANGED")
    for version in VERSIONS:
        require(version_authorities(version)[1]["self_hash"] == freeze["candidate_hashes"][version], "CANDIDATE_AUTHORITY_CHANGED")
        require(document(PUB / f"HAI{version[:2]}_EVIDENCE_FREEZE_V1.json")["self_hash"] == freeze["evidence_hashes"][version] == budgets[version]["evidence_hash"], "EVIDENCE_AUTHORITY_CHANGED")
    return freeze, approval, budgets, profiles


def _pack_paths(version: str, candidate_id: str) -> tuple[Path, Path, Path]:
    base = private_root() / "semantic" / ("HAI" + version[:2])
    return (
        base / "provider" / f"{candidate_id}.json",
        base / "retrieval" / f"{candidate_id}.json",
        base / "train2" / "structural" / f"{candidate_id}.json",
    )


def _preflight_all_frozen_packs(budgets, profiles) -> str:
    """Replay every approved pack before the first credential read."""
    receipts = []
    for version in VERSIONS:
        _, _, _, pairs = version_authorities(version)
        expected_ids = tuple("EXP03B-CAND-" + digest({"source": s, "target": t})[:20] for s, t in pairs)
        profile_rows = {row["candidate_id"]: row for row in profiles[version]["profiles"]}
        require(tuple(profile_rows) == expected_ids, "PROFILE_CANDIDATE_ORDER")
        for candidate_id in expected_ids:
            provider_path, retrieval_path, structural_path = _pack_paths(version, candidate_id)
            row = profile_rows[candidate_id]
            require(sha256_file(provider_path) == row["provider_pack_hash"], "PROVIDER_PACK_BINDING")
            require(sha256_file(retrieval_path) == row["retrieval_pack_hash"], "RETRIEVAL_PACK_BINDING")
            evidence = json.loads(provider_path.read_text(encoding="utf-8"))
            retrieval_pack = json.loads(retrieval_path.read_text(encoding="utf-8"))
            request = request_body(evidence)
            validate_serialized_request(request)
            validate_global_retrieval(retrieval_pack)
            hidden = _structural(json.loads(structural_path.read_text(encoding="utf-8")))
            require(hidden.candidate_id == candidate_id and evidence["candidate_id"] == candidate_id, "PACK_CANDIDATE_IDENTITY")
            receipts.append((version, candidate_id, row["provider_pack_hash"], row["retrieval_pack_hash"], digest(request)))
    require(len(receipts) == 58, "FROZEN_PROVIDER_COHORT")
    return digest(receipts)


def _replay_calls(gate, profiles, freeze):
    count = validate_call_inventory(RUNROOT, 174)
    by_slot = {}
    for index in range(1, count + 1):
        request_doc = _read(RUNROOT / "calls" / f"{index:04d}.request.json")
        response_doc = _read(RUNROOT / "calls" / f"{index:04d}.response.json")
        receipt_doc = _read(RUNROOT / "calls" / f"{index:04d}.receipt.json")
        content = json.loads(request_doc["request"]["input"])
        reservation = gate.reserve(
            version=request_doc["version"], candidate_id=request_doc["candidate_id"],
            call_ordinal=request_doc["call_ordinal"], request=request_doc["request"],
            provider_pack_hash=request_doc["provider_pack_hash"],
            retrieval_pack_hash=request_doc["retrieval_pack_hash"],
            input_upper_bound=request_doc["input_upper_bound"], evidence=content["evidence"],
            repair=content.get("repair"),
        )
        require(asdict(reservation) == request_doc["reservation"], "CALL_RESERVATION_REPLAY")
        response = response_doc["response"]
        usage = response_doc["usage"]
        _, no_tools = _response_proposal(response) if response_doc["parse_status"] == "PASS" else (None, response_doc["no_tool_invocation"])
        actual = gate.reconcile(
            input_tokens=usage["input_tokens"], output_tokens=usage["output_tokens"],
            response_hash=digest(response), response_id=response["id"], model=response["model"],
            latency_seconds=response_doc["latency_seconds"], no_tool_invocation=no_tools,
        )
        require(seal(actual) == receipt_doc, "CALL_RECEIPT_REPLAY")
        if index == 1:
            probe = _read(RUNROOT / "ONE_CALL_RECEIPT_FIRST_PASS.json")
            require(probe["call_receipt_hash"] == digest(actual) and probe["status"] == "PASS", "ONE_CALL_RECEIPT_REPLAY")
            gate.accept_one_call_receipt(digest(actual), persisted_and_replayed=True, privacy_pass=True, schema_pass=True)
        by_slot[reservation.slot] = (request_doc, response_doc)
    return by_slot


def main(*, probe_only: bool) -> None:
    freeze, approval, budgets, profiles = _authorities()
    pack_replay_hash = _preflight_all_frozen_packs(budgets, profiles)
    require(not (RUNROOT / "PROVIDER_PHASE_CLOSED.json").exists(), "PROVIDER_PHASE_PERMANENTLY_CLOSED")
    RUNROOT.mkdir(parents=True, exist_ok=True)
    lock = RUNROOT / "SINGLE_WRITER.lock"
    with lock.open("x", encoding="utf-8") as stream:
        stream.write("XVER_T2_SINGLE_PROVIDER_WRITER")
    try:
        publish(RUNROOT / "USER_APPROVAL_RECEIPT.json", approval)
        publish(RUNROOT / "PRETRANSPORT_AUTHORITY_REPLAY_PASS.json", seal({
            "execution_freeze_hash": freeze["self_hash"], "approval_hash": approval["self_hash"],
            "pack_replay_hash": pack_replay_hash, "provider_pack_count": 58,
            "hidden_retrieval_pack_count": 58, "credential_reads_before_replay": 0,
            "attack_accesses": 0,
        }))
        gate = XverCombinedProviderGateV1(budgets, profiles, approval, freeze["self_hash"])
        existing = _replay_calls(gate, profiles, freeze)
        if probe_only and gate.one_call_pass:
            print(json.dumps({"status": "ONE_CALL_RECEIPT_PASS", "full_schedule_started": False}))
            return

        def call(version, candidate_id, call_ordinal, evidence, repair, provider_hash, retrieval_hash):
            slot = f"HAI{version[:2]}.{candidate_id}.T2.C{call_ordinal}"
            body = request_body(evidence, repair=repair)
            validate_serialized_request(body)
            if slot in existing:
                request_doc, response_doc = existing[slot]
                require(request_doc["request_hash"] == digest(body), "RESUMED_PROMPT_CHANGED")
                if response_doc["parse_status"] != "PASS":
                    raise ParsedResponseFailure(response_doc["parse_status"])
                return _response_proposal(response_doc["response"])[0]
            budget = budgets[version]
            phase = "initial" if call_ordinal == 1 else "repair"
            bound = len(encoded(body)) + budget["framing_allowance"]
            reservation = gate.reserve(
                version=version, candidate_id=candidate_id, call_ordinal=call_ordinal,
                request=body, provider_pack_hash=provider_hash,
                retrieval_pack_hash=retrieval_hash, input_upper_bound=bound,
                evidence=evidence, repair=repair,
            )
            request_doc = seal({
                "version": version, "candidate_id": candidate_id,
                "call_ordinal": call_ordinal, "slot": reservation.slot,
                "provider_pack_hash": provider_hash, "retrieval_pack_hash": retrieval_hash,
                "request_hash": digest(body), "input_upper_bound": bound,
                "reservation": asdict(reservation), "request": body,
            })
            publish(RUNROOT / "calls" / f"{reservation.index:04d}.request.json", request_doc)
            start = time.perf_counter()
            response = _transport(body)
            elapsed = time.perf_counter() - start
            usage = response.get("usage")
            require(type(usage) is dict and type(usage.get("input_tokens")) is int and type(usage.get("output_tokens")) is int, "PROVIDER_USAGE_UNAVAILABLE")
            require(response.get("model") == budgets[version]["model"], "MODEL_SNAPSHOT_MISMATCH")
            require(type(response.get("id")) is str and bool(response["id"]), "PROVIDER_RESPONSE_IDENTITY")
            try:
                proposal, no_tools = _response_proposal(response)
                parse_status = "PASS"
            except ParsedResponseFailure:
                proposal = None
                no_tools = all(item.get("type") in ("reasoning", "message") for item in response.get("output", []))
                parse_status = "PARSE_FAILURE"
            response_doc = seal({
                "version": version, "candidate_id": candidate_id,
                "slot": reservation.slot, "response": response, "usage": usage,
                "latency_seconds": elapsed, "request_hash": digest(body),
                "parse_status": parse_status, "no_tool_invocation": no_tools,
            })
            publish(RUNROOT / "calls" / f"{reservation.index:04d}.response.json", response_doc)
            receipt = gate.reconcile(
                input_tokens=usage["input_tokens"], output_tokens=usage["output_tokens"],
                response_hash=digest(response), response_id=response["id"], model=response["model"],
                latency_seconds=elapsed, no_tool_invocation=no_tools,
            )
            publish(RUNROOT / "calls" / f"{reservation.index:04d}.receipt.json", seal(receipt))
            persisted = _read(RUNROOT / "calls" / f"{reservation.index:04d}.receipt.json")
            require(persisted == seal(receipt), "CALL_RECEIPT_DURABILITY")
            if reservation.index == 1:
                require(proposal is not None, "ONE_CALL_SCHEMA_PROBE_FAILED")
                gate.accept_one_call_receipt(digest(receipt), persisted_and_replayed=True, privacy_pass=True, schema_pass=True)
                publish(RUNROOT / "ONE_CALL_RECEIPT_FIRST_PASS.json", seal({
                    "status": "PASS", "call_receipt_hash": digest(receipt),
                    "request_hash": digest(body), "response_id_hash": digest(response["id"]),
                    "model": response["model"], "budget_hash": budget["self_hash"],
                    "execution_freeze_hash": freeze["self_hash"], "store": False,
                    "no_tools": True, "fallback": False, "retry": 0,
                }))
                if probe_only:
                    raise StopIteration
            if proposal is None:
                raise ParsedResponseFailure(parse_status)
            return proposal

        for version in VERSIONS:
            _, _, _, pairs = version_authorities(version)
            records = []
            terminal_hashes = []
            for source, target in pairs:
                candidate_id = "EXP03B-CAND-" + digest({"source": source, "target": target})[:20]
                output_path = RUNROOT / ("HAI" + version[:2]) / "outputs" / f"{candidate_id}.json"
                if output_path.exists():
                    row = _read(output_path)
                    require(row["version"] == version and row["candidate_id"] == candidate_id, "OUTPUT_VERSION_IDENTITY")
                    records.append(row); terminal_hashes.append(row["self_hash"]); continue
                provider_path, retrieval_path, structural_path = _pack_paths(version, candidate_id)
                profile = next(r for r in profiles[version]["profiles"] if r["candidate_id"] == candidate_id)
                require(sha256_file(provider_path) == profile["provider_pack_hash"], "PROVIDER_PACK_BINDING")
                require(sha256_file(retrieval_path) == profile["retrieval_pack_hash"], "RETRIEVAL_PACK_BINDING")
                evidence = json.loads(provider_path.read_text(encoding="utf-8"))
                retrieval_pack = json.loads(retrieval_path.read_text(encoding="utf-8"))
                validate_global_retrieval(retrieval_pack)
                hidden = _structural(json.loads(structural_path.read_text(encoding="utf-8")))
                provider_ids = frozenset(row[7] for row in evidence["structural_rows"])
                authority = Train2HiddenVerifierAuthorityV2(hidden, provider_ids)
                raw = []; verifier_results = []; feedback_rows = []
                retrieval_ids = frozenset(); repair = None; admitted = None; terminal = None
                for ordinal in (1, 2, 3):
                    try:
                        proposal = call(version, candidate_id, ordinal, evidence, repair, profile["provider_pack_hash"], profile["retrieval_pack_hash"])
                    except ParsedResponseFailure:
                        raw.append(None); verifier_results.append(None); terminal = "PARSE_FAILURE"; break
                    raw.append(proposal_document(proposal))
                    result = verify(proposal, authority, retrieval_ids=retrieval_ids)
                    verifier_results.append(asdict(result))
                    if result.status == "ACCEPTED":
                        admitted = admit(
                            proposal, authority, implementation_hash=freeze["implementation_bundle_hash"],
                            config_hash=budgets[version]["config_hash"], retrieval_ids=retrieval_ids,
                        )
                        terminal = "INTENTIONAL_NO_RULE" if proposal.decision == "NO_RULE" else "ACCEPTED_RULE_SET"
                        break
                    if result.status == "REJECTED":
                        terminal = "VERIFIER_REJECTION"; break
                    if ordinal == 3:
                        terminal = "NEEDS_REPAIR_BUDGET_EXHAUSTED"; break
                    bounded_feedback = feedback(proposal, result, ordinal)
                    feedback_rows.append(bounded_feedback)
                    retrieval_ids |= frozenset(row["evidence_slice_id"] for row in retrieval_pack["alternatives"])
                    repair = {
                        "previous_proposal": proposal_document(proposal),
                        "feedback": bounded_feedback,
                        "retrieval": retrieval_pack,
                    }
                require(terminal is not None and 1 <= len(raw) <= 3, "TERMINAL_STATE")
                row = seal({
                    "schema": "xver_t2_provider_terminal_v1", "version": version,
                    "candidate_id": candidate_id, "source": source, "target": target,
                    "provider_pack_hash": profile["provider_pack_hash"],
                    "retrieval_pack_hash": profile["retrieval_pack_hash"],
                    "budget_hash": budgets[version]["self_hash"],
                    "prompt_hash": budgets[version]["prompt_hash"],
                    "schema_hash": budgets[version]["output_schema_hash"],
                    "raw": raw, "verifier_results": verifier_results,
                    "feedback": feedback_rows, "call_count": len(raw), "terminal": terminal,
                    "admission_receipt": admitted.receipt if admitted else None,
                    "admission_hash": admitted.receipt["self_hash"] if admitted else None,
                })
                publish(output_path, row); records.append(row); terminal_hashes.append(row["self_hash"])
            phase_calls = sum(1 for r in gate.receipts if r["version"] == version)
            bundle = seal({
                "schema": "xver_t2_provider_outputs_frozen_v1", "version": version,
                "candidate_count": len(records), "candidate_ids": [r["candidate_id"] for r in records],
                "terminal_hashes": terminal_hashes, "calls": phase_calls,
                "budget_hash": budgets[version]["self_hash"], "execution_freeze_hash": freeze["self_hash"],
                "train2_admissions_frozen": True, "hidden_confirmation_allowed": False,
                "attack_accesses": 0,
            })
            publish(RUNROOT / ("HAI" + version[:2]) / "PROVIDER_OUTPUTS_FROZEN.json", bundle)
        combined = seal({
            "schema": "xver_t2_all_provider_outputs_frozen_v1",
            "version_bundles": {
                version: _read(RUNROOT / ("HAI" + version[:2]) / "PROVIDER_OUTPUTS_FROZEN.json")["self_hash"]
                for version in VERSIONS
            },
            "calls": len(gate.receipts), "maximum_calls": 174,
            "execution_freeze_hash": freeze["self_hash"], "all_outputs_and_admissions_frozen": True,
            "hidden_confirmation_allowed": True, "attack_accesses": 0,
        })
        publish(RUNROOT / "ALL_XVER_PROVIDER_OUTPUTS_FROZEN.json", combined)
        publish(RUNROOT / "PROVIDER_PHASE_CLOSED.json", seal({
            "output_bundle_hash": combined["self_hash"], "execution_freeze_hash": freeze["self_hash"],
            "provider_calls_allowed": False, "no_provider_calls_after_hidden_confirmation": True,
        }))
        print(json.dumps({"status": "ALL_XVER_PROVIDER_OUTPUTS_FROZEN", "calls": len(gate.receipts)}))
    except StopIteration:
        print(json.dumps({"status": "ONE_CALL_RECEIPT_PASS", "full_schedule_started": False}))
    finally:
        if lock.exists():
            lock.unlink()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe-only", action="store_true")
    args = parser.parse_args()
    try:
        main(probe_only=args.probe_only)
    except Exception as error:
        code = str(error) if isinstance(error, (ValueError, RuntimeError)) else type(error).__name__
        print(json.dumps({"status": "FAIL_CLOSED", "error": code}))
        raise SystemExit(2)
