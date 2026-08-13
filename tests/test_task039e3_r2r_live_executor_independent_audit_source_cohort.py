"""Independent source-authority and full-cohort audit for the R2R adapter.

All provider behavior is supplied by deterministic in-process fixtures.  The
test never reads credentials, private roots, or real E1 evidence and never
opens a network socket.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
from typing import Any
import unittest

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_execution_prep_v1 import MAXIMUM_SCIENTIFIC_SLOTS
from paperworks.v6.task039e3_orchestration_v1 import (
    ConstructionOutcomeLedgerV1,
    ConstructionProposalLedgerV1,
)
from paperworks.v6.task039e3_r2r_authorization_v1 import (
    DIRECT_NUMBER_PROMPT_HASH,
    DIRECT_NUMBER_SCHEMA_HASH,
    EXACT_ENDPOINT,
    EXACT_MODEL,
    MAIN_PROMPT_HASH,
    RECOVERY_SCHEMA_V2_HASH,
    T2_FOLLOWUP_PROMPT_HASH,
)
from paperworks.v6.task039e3_r2r_execution_v1 import (
    R2R_ARM_RUNNERS_V1,
    build_lifetime_accounting_v1,
    run_injected_r2r_scientific_cohort_v1,
)
from paperworks.v6.task039e3_r2r_live_transport_v1 import (
    R2RLiveOpenAIChatCompletionsTransportV1,
)
from paperworks.v6.task039e3_r2r_precontact_v1 import (
    R2RIntegrityGuardedTransportV1,
    R2RObservedIntegrityStateV1,
    R2RPostContactIntegrityGuardV1,
    R2RSourceBlobIdentityV1,
    R2R_SCIENTIFIC_ACCOUNTING_BEHAVIOR_HASH_V1,
    capture_r2r_integrity_snapshot_v1,
)
from paperworks.v6.task039e3_r2r_request_contract_v1 import (
    DIRECT_NUMBER_PROVIDER_SCHEMA_V1_HASH,
    RECOVERY_MAIN_PROVIDER_SCHEMA_V2_HASH,
)
from paperworks.v6.task039e3_recovery_execution_v3 import (
    TransactionalScientificProviderLedgerV3,
)
from paperworks.v6.task039e3_recovery_science_v2 import ScientificLedgersV2
from paperworks.v6.task039e3_recovery_transactional_custody_v3 import (
    TransactionalHashChainCustodyV3,
)
from task039e3_support import direct_number_payload, make_evidence, valid_core_document


ROOT = Path(__file__).resolve().parents[1]
REMEDIATION_A = "f10365adbdde5bb2070df429770174d215829dc6"
REMEDIATION_B = "067dcffc441170064180c677b0bd7845a93ce5ef"
PREVIOUS_IMPLEMENTATION_A = "eb62b449e06ea5f6c4a2d445223f6ca98de3690c"
ENTRYPOINT = "scripts/run_task039e3_r2r_scientific_execution_v1.py"
AUTHORIZATION_SCHEMA = "schemas/v6/task039e3_r2r_execution_authorization_v1_schema.json"
MANIFEST_PATH = (
    "docs/task_reports/"
    "TASK-039E3_R2R_LIVE_EXECUTOR_REMEDIATION_SOURCE_FREEZE.json"
)
MANIFEST_HASH = "a58b5e3480fb7d1b88029cf2c2ff018cfdaae84be3a5861299eed003c13ad235"
PREVIOUS_MANIFEST_PATH = (
    "docs/task_reports/"
    "TASK-039E3_R2R_FINALIZATION_REMEDIATION_SOURCE_FREEZE.json"
)
PREVIOUS_MANIFEST_HASH = (
    "01c8e23f2eb15f321295bf0163dcbd81df67ed0179817acb725614a45bfede1d"
)
CHANGED_ACTIVE_SOURCE = "src/paperworks/v6/task039e3_r2r_precontact_v1.py"
EXPECTED_SCHEMA_V2_HASH = (
    "bcbc9debc32ec9e4b02d5781c7f8b512023752ccb90f60154648bb5d9de67aa1"
)


def _git_bytes(*arguments: str) -> bytes:
    return subprocess.run(
        ["git", "-c", f"safe.directory={ROOT}", *arguments],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def _git_text(*arguments: str) -> str:
    return _git_bytes(*arguments).decode("utf-8").strip()


def _blob(commit: str, repository_path: str) -> bytes:
    return _git_bytes("show", f"{commit}:{repository_path}")


def _canonical_hash(document: object) -> str:
    return hashlib.sha256(
        json.dumps(
            document,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _self_hashed_document(commit: str, path: str) -> dict[str, Any]:
    document = json.loads(_blob(commit, path))
    if not isinstance(document, dict):
        raise AssertionError(f"JSON object required: {path}")
    supplied = document.pop("artifact_hash", None)
    if supplied != _canonical_hash(document):
        raise AssertionError(f"self-hash mismatch: {path}")
    return {"artifact_hash": supplied, **document}


def _tracked_paths(commit: str) -> set[str]:
    return set(_git_text("ls-tree", "-r", "--name-only", commit).splitlines())


def _package_for_path(path: str) -> str:
    parts = path.removeprefix("src/").removesuffix(".py").split("/")
    parts.pop()
    return ".".join(parts)


def _module_paths(module: str, tracked: set[str]) -> set[str]:
    if not (module == "paperworks" or module.startswith("paperworks.")):
        return set()
    parts = module.split(".")
    resolved: set[str] = set()
    for index in range(1, len(parts)):
        initializer = f"src/{'/'.join(parts[:index])}/__init__.py"
        if initializer in tracked:
            resolved.add(initializer)
    stem = f"src/{module.replace('.', '/')}"
    for candidate in (f"{stem}.py", f"{stem}/__init__.py"):
        if candidate in tracked:
            resolved.add(candidate)
    return resolved


def _qualified_name(node: ast.expr, aliases: dict[str, str]) -> str:
    parts: list[str] = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(aliases.get(current.id, current.id))
    return ".".join(reversed(parts))


def _reconstruct_closure(commit: str) -> tuple[set[str], set[str], set[str]]:
    """Resolve project imports directly from the exact raw Git blobs."""

    tracked = _tracked_paths(commit)
    pending = [ENTRYPOINT]
    closure: set[str] = set()
    dynamic_observations: set[str] = set()
    unresolved: set[str] = set()
    dynamic_functions = {
        "__import__",
        "importlib.import_module",
        "importlib.util.spec_from_file_location",
        "importlib.machinery.SourceFileLoader",
    }
    while pending:
        path = pending.pop()
        if path in closure:
            continue
        closure.add(path)
        tree = ast.parse(_blob(commit, path).decode("utf-8"), filename=path)
        aliases: dict[str, str] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    bound = alias.asname or alias.name.split(".")[0]
                    aliases[bound] = alias.name if alias.asname else bound
            elif isinstance(node, ast.ImportFrom) and node.module:
                for alias in node.names:
                    aliases[alias.asname or alias.name] = f"{node.module}.{alias.name}"

        for node in ast.walk(tree):
            modules: list[str] = []
            if isinstance(node, ast.Import):
                modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    relative = "." * node.level + (node.module or "")
                    module = importlib.util.resolve_name(
                        relative, _package_for_path(path)
                    )
                else:
                    module = node.module or ""
                if module:
                    modules.append(module)
                    modules.extend(f"{module}.{alias.name}" for alias in node.names)
            for module in modules:
                pending.extend(_module_paths(module, tracked) - closure)

            if not isinstance(node, ast.Call):
                continue
            name = _qualified_name(node.func, aliases)
            if name not in dynamic_functions:
                continue
            observation = f"{path}:{name}"
            dynamic_observations.add(observation)
            if not node.args or not isinstance(node.args[0], ast.Constant):
                unresolved.add(f"{observation}:nonliteral")
                continue
            value = node.args[0].value
            if not isinstance(value, str):
                unresolved.add(f"{observation}:nonstr")
                continue
            if name in {"__import__", "importlib.import_module"}:
                dynamic_paths = _module_paths(value, tracked)
            else:
                normalized = value.replace("\\", "/")
                dynamic_paths = {normalized} if normalized in tracked else set()
            if dynamic_paths:
                pending.extend(dynamic_paths - closure)
            elif value.startswith(("paperworks", "src/paperworks")):
                unresolved.add(f"{observation}:{value}")
    return closure, dynamic_observations, unresolved


class _HTTPResponse:
    status = 200
    headers: dict[str, str] = {}

    def __init__(self, document: object) -> None:
        self._raw = json.dumps(
            document,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

    def __enter__(self) -> "_HTTPResponse":
        return self

    def __exit__(self, *_arguments: object) -> None:
        return None

    def read(self, _size: int = -1) -> bytes:
        return self._raw


def _provider_document(payload: object, sequence: int) -> dict[str, object]:
    return {
        "id": f"chatcmpl-independent-offline-{sequence:04d}",
        "model": EXACT_MODEL,
        "choices": [
            {
                "finish_reason": "stop",
                "message": {
                    "content": json.dumps(
                        payload,
                        ensure_ascii=True,
                        allow_nan=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                    "refusal": None,
                },
            }
        ],
        "usage": {
            "prompt_tokens": 11,
            "completion_tokens": 7,
            "total_tokens": 18,
        },
        "system_fingerprint": "fp-independent-offline-r2r-audit",
    }


class _OfflineSuccessOpener:
    """In-process response source with no socket or network capability."""

    def __init__(self, payloads: list[object]) -> None:
        self._payloads = list(payloads)
        self.request_bodies: list[dict[str, object]] = []
        self.calls = 0

    @property
    def remaining(self) -> int:
        return len(self._payloads)

    def __call__(self, request: object, *, timeout: float) -> _HTTPResponse:
        if timeout != 30.0:
            raise AssertionError("frozen timeout differs")
        data = getattr(request, "data", None)
        if not isinstance(data, bytes):
            raise AssertionError("serialized request bytes required")
        body = json.loads(data.decode("utf-8"))
        if not isinstance(body, dict):
            raise AssertionError("request body must be an object")
        self.request_bodies.append(body)
        self.calls += 1
        if not self._payloads:
            raise AssertionError("offline response script exhausted")
        return _HTTPResponse(_provider_document(self._payloads.pop(0), self.calls))


class _DirectLedger:
    def __init__(self) -> None:
        self._records: list[object] = []

    @property
    def records(self) -> tuple[object, ...]:
        return tuple(self._records)

    def append(self, value: object) -> None:
        self._records.append(value)


def _integrity_state() -> R2RObservedIntegrityStateV1:
    return R2RObservedIntegrityStateV1(
        execution_commit=REMEDIATION_A,
        source_manifest_hash=MANIFEST_HASH,
        source_blobs=(
            R2RSourceBlobIdentityV1("src/synthetic.py", "b" * 40, "2" * 64),
        ),
        authorization_hash="3" * 64,
        recovery_main_provider_schema_v2_hash=RECOVERY_MAIN_PROVIDER_SCHEMA_V2_HASH,
        main_prompt_hash=MAIN_PROMPT_HASH,
        t2_followup_prompt_hash=T2_FOLLOWUP_PROMPT_HASH,
        direct_number_prompt_hash=DIRECT_NUMBER_PROMPT_HASH,
        direct_number_schema_hash=DIRECT_NUMBER_PROVIDER_SCHEMA_V1_HASH,
        exact_model=EXACT_MODEL,
        endpoint=EXACT_ENDPOINT,
        sampling_configuration_hash="4" * 64,
        timeout_seconds=30.0,
        retry_policy_hash="5" * 64,
        relation_schedule_hash=(
            "6db63485387924b28e9ce498aae46412a127ba69055a28e72880e1afffa4c4ca"
        ),
        scientific_concurrency=1,
        scientific_call_budget_hash="6" * 64,
        scientific_accounting_behavior_hash=R2R_SCIENTIFIC_ACCOUNTING_BEHAVIOR_HASH_V1,
        recovery_execution_configuration_hash="7" * 64,
    )


def _offline_transport(
    payloads: list[object],
) -> tuple[
    R2RIntegrityGuardedTransportV1,
    R2RLiveOpenAIChatCompletionsTransportV1,
    _OfflineSuccessOpener,
    list[float],
    list[int],
]:
    opener = _OfflineSuccessOpener(payloads)
    sleeps: list[float] = []
    raw = R2RLiveOpenAIChatCompletionsTransportV1(
        api_key="synthetic-offline-audit-value",
        opener=opener,
        sleeper=sleeps.append,
    )
    state = _integrity_state()
    checks: list[int] = []

    def load() -> R2RObservedIntegrityStateV1:
        checks.append(1)
        return state

    guard = R2RPostContactIntegrityGuardV1(
        capture_r2r_integrity_snapshot_v1(state), load
    )
    return R2RIntegrityGuardedTransportV1(raw, guard), raw, opener, sleeps, checks


def _transactional_ledger(
    root: Path, transport: R2RIntegrityGuardedTransportV1
) -> tuple[TransactionalScientificProviderLedgerV3, TransactionalHashChainCustodyV3]:
    custody = TransactionalHashChainCustodyV3(
        root,
        ledger_kind="scientific_provider",
        allowed_logical_call_kind="scientific",
    )
    return (
        TransactionalScientificProviderLedgerV3(
            custody, attempt_supplier=lambda: transport.attempt_custody
        ),
        custody,
    )


def _provider_schema_hash(body: dict[str, object]) -> str:
    response_format = body["response_format"]
    if not isinstance(response_format, dict):
        raise AssertionError("response_format must be an object")
    json_schema = response_format["json_schema"]
    if not isinstance(json_schema, dict):
        raise AssertionError("json_schema must be an object")
    schema = json_schema["schema"]
    if not isinstance(schema, dict):
        raise AssertionError("schema must be an object")
    return stable_hash_v1(schema)


class R2RLiveExecutorIndependentAuditSourceCohortTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = _self_hashed_document(REMEDIATION_B, MANIFEST_PATH)
        cls.previous_manifest = _self_hashed_document(
            REMEDIATION_B, PREVIOUS_MANIFEST_PATH
        )
        cls.closure, cls.dynamic_observations, cls.unresolved = (
            _reconstruct_closure(REMEDIATION_A)
        )

    def test_independent_closure_reproduces_complete_manifest(self) -> None:
        records = self.manifest["source_records"]
        frozen = {str(record["repository_path"]) for record in records}
        self.assertEqual(self.manifest["artifact_hash"], MANIFEST_HASH)
        self.assertEqual(self.manifest["described_commit"], REMEDIATION_A)
        self.assertEqual(self.manifest["closure_entrypoint"], ENTRYPOINT)
        self.assertEqual(len(self.closure), 49)
        self.assertEqual(len(self.closure - {ENTRYPOINT}), 48)
        self.assertEqual(self.dynamic_observations, set())
        self.assertEqual(self.unresolved, set())
        self.assertEqual(self.closure - frozen, set())
        self.assertEqual(frozen - self.closure, {AUTHORIZATION_SCHEMA})
        self.assertEqual(self.manifest["material_path_count"], 49)
        self.assertEqual(self.manifest["source_record_count"], 50)
        self.assertEqual(self.manifest["dynamic_imports_found"], 0)
        self.assertEqual(self.manifest["unresolved_dynamic_imports"], 0)
        self.assertEqual(self.manifest["unresolved_project_local_imports"], [])
        self.assertEqual(
            self.manifest["unbound_material_project_local_dependency_count"], 0
        )

    def test_all_records_match_git_objects_and_only_adapter_identity_changed(self) -> None:
        current_records = self.manifest["source_records"]
        paths = [str(record["repository_path"]) for record in current_records]
        self.assertEqual(paths, sorted(paths))
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(len(paths), 50)
        for record in current_records:
            path = str(record["repository_path"])
            raw = _blob(REMEDIATION_A, path)
            with self.subTest(path=path):
                self.assertEqual(
                    _git_text("rev-parse", f"{REMEDIATION_A}:{path}"),
                    record["git_blob_sha"],
                )
                self.assertEqual(hashlib.sha256(raw).hexdigest(), record["sha256"])
                self.assertEqual(_blob(REMEDIATION_B, path), raw)

        previous = {
            str(record["repository_path"]): record
            for record in self.previous_manifest["source_records"]
        }
        current = {
            str(record["repository_path"]): record for record in current_records
        }
        self.assertEqual(self.previous_manifest["artifact_hash"], PREVIOUS_MANIFEST_HASH)
        self.assertEqual(self.previous_manifest["described_commit"], PREVIOUS_IMPLEMENTATION_A)
        self.assertEqual(set(previous), set(current))
        changed = {path for path in current if previous[path] != current[path]}
        self.assertEqual(changed, {CHANGED_ACTIVE_SOURCE})
        self.assertIn(CHANGED_ACTIVE_SOURCE, self.closure)

    def test_frozen_schema_prompts_and_scientific_sources_are_unchanged(self) -> None:
        self.assertEqual(RECOVERY_MAIN_PROVIDER_SCHEMA_V2_HASH, EXPECTED_SCHEMA_V2_HASH)
        self.assertEqual(RECOVERY_SCHEMA_V2_HASH, EXPECTED_SCHEMA_V2_HASH)
        self.assertEqual(
            MAIN_PROMPT_HASH,
            "a251e4b9da31c33e72d14dd81da6b2b1d0d1437fdf37ca311330eccce226f1ba",
        )
        self.assertEqual(
            T2_FOLLOWUP_PROMPT_HASH,
            "a633067a7c9927be158f68ce714236f4c18c09433d49c903dac941a9774eeca5",
        )
        self.assertEqual(
            DIRECT_NUMBER_PROMPT_HASH,
            "fb01d8990ee3a7affe540dfdf3556b46d7bd744cd1e3a04d6fd9d79772dd2769",
        )
        self.assertEqual(
            DIRECT_NUMBER_SCHEMA_HASH,
            "b1b91bf27fd191da57984be625a2547e4e5ee96a0aca52535df071af92bfd6ca",
        )
        self.assertEqual(EXACT_MODEL, "gpt-5.4-2026-03-05")
        self.assertEqual(EXACT_ENDPOINT, "https://api.openai.com/v1/chat/completions")
        self.assertEqual(MAXIMUM_SCIENTIFIC_SLOTS, 336)

    def test_full_42_relation_minimum_cohort_completes_with_252_calls(self) -> None:
        evidence_records = tuple(make_evidence(index) for index in range(1, 43))
        payloads: list[object] = []
        for evidence in evidence_records:
            payloads.extend(valid_core_document(evidence) for _ in range(5))
            payloads.append(direct_number_payload())
        guarded, raw, opener, sleeps, checks = _offline_transport(payloads)
        proposal = ConstructionProposalLedgerV1()
        outcome = ConstructionOutcomeLedgerV1()
        direct = _DirectLedger()
        self.assertEqual((proposal.records, outcome.records, direct.records), ((), (), ()))
        with tempfile.TemporaryDirectory(prefix="r2r-independent-cohort-") as temporary:
            provider, custody = _transactional_ledger(Path(temporary), guarded)
            result = run_injected_r2r_scientific_cohort_v1(
                relation_identities=tuple(
                    item.relation.relation_identity for item in evidence_records
                ),
                evidence_records=evidence_records,
                transport=guarded,
                ledgers=ScientificLedgersV2(provider, proposal, outcome, direct),
                progress=lambda _message: None,
            )
            reconstructed = custody.reconstruct()
        self.assertEqual(result.relation_count, 42)
        self.assertEqual(result.t0_outcomes, 42)
        self.assertEqual(result.t1_logical_calls, 42)
        self.assertEqual(result.t1b_logical_calls, 126)
        self.assertEqual(result.t2_logical_calls, 42)
        self.assertEqual(result.direct_number_logical_calls, 42)
        self.assertEqual(result.scientific_logical_calls, 252)
        self.assertEqual((raw.calls, opener.calls, len(checks)), (252, 252, 252))
        self.assertEqual(len(guarded.request_hashes), 252)
        self.assertEqual(len(guarded.attempt_custody), 252)
        self.assertEqual(opener.remaining, 0)
        self.assertEqual(sleeps, [])
        self.assertEqual(reconstructed.authoritative_record_count, 252)
        self.assertFalse(reconstructed.orphan_record_hashes)
        self.assertFalse(reconstructed.pending_files)
        self.assertEqual(len(outcome.records), 168)
        self.assertEqual(len(direct.records), 42)
        self.assertEqual(
            sum(record.slot.arm == "T1-B" for record in provider.records), 126
        )
        for offset in range(0, 252, 6):
            self.assertTrue(
                all(
                    _provider_schema_hash(body)
                    == RECOVERY_MAIN_PROVIDER_SCHEMA_V2_HASH
                    for body in opener.request_bodies[offset : offset + 5]
                )
            )
            self.assertEqual(
                _provider_schema_hash(opener.request_bodies[offset + 5]),
                DIRECT_NUMBER_PROVIDER_SCHEMA_V1_HASH,
            )
        self.assertTrue(all(record.slot.scientific for record in provider.records))
        accounting = build_lifetime_accounting_v1(result.scientific_logical_calls)
        self.assertEqual(accounting.historical_aborted_r2_scientific_logical_calls, 1)
        self.assertEqual(accounting.recovery_cohort_scientific_logical_calls, 252)
        self.assertEqual(accounting.lifetime_scientific_logical_call_attempts, 253)

    def test_t2_three_call_bound_supports_frozen_336_call_ceiling(self) -> None:
        evidence = make_evidence(43)
        guarded, raw, opener, sleeps, checks = _offline_transport(
            [valid_core_document(evidence) for _ in range(3)]
        )
        with tempfile.TemporaryDirectory(prefix="r2r-independent-t2-bound-") as temporary:
            provider, custody = _transactional_ledger(Path(temporary), guarded)
            result = R2R_ARM_RUNNERS_V1.t2(
                relation_schedule_index=0,
                evidence=evidence,
                transport=guarded,
                call_ledger=provider,
                proposal_ledger=ConstructionProposalLedgerV1(),
                outcome_ledger=ConstructionOutcomeLedgerV1(),
                retrieval_identity=evidence.approved_evidence_identities[0],
                synthetic_validity_faults=(
                    "SYNTHETIC_REPAIRABLE_RETRIEVE",
                    "SYNTHETIC_REPAIRABLE_RETRIEVE",
                    "SYNTHETIC_REPAIRABLE_RETRIEVE",
                ),
            )
            reconstructed = custody.reconstruct()
        self.assertEqual(result.outcome, "no_rule")
        self.assertEqual(result.generation_calls_consumed, 3)
        self.assertEqual(result.retrieval_count, 1)
        self.assertLessEqual(result.revise_count, 2)
        self.assertEqual((raw.calls, opener.calls, len(checks)), (3, 3, 3))
        self.assertEqual(sleeps, [])
        self.assertEqual(reconstructed.authoritative_record_count, 3)
        self.assertTrue(
            all(
                _provider_schema_hash(body) == RECOVERY_MAIN_PROVIDER_SCHEMA_V2_HASH
                for body in opener.request_bodies
            )
        )
        maximum_total = 42 + 126 + (42 * 3) + 42
        self.assertEqual(maximum_total, MAXIMUM_SCIENTIFIC_SLOTS)
        accounting = build_lifetime_accounting_v1(maximum_total)
        self.assertEqual(accounting.recovery_cohort_scientific_logical_calls, 336)
        self.assertEqual(accounting.lifetime_scientific_logical_call_attempts, 337)


if __name__ == "__main__":
    unittest.main()
