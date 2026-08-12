"""Independent C1 source-freeze and pre-contact audit oracle.

The oracle resolves project imports from exact Git objects at Completion
Commit A.  It does not trust the C1 manifest's asserted closure/counts and it
never constructs a real credential, provider transport, or private-data root.
"""

from __future__ import annotations

import ast
from dataclasses import replace
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
from typing import Any, Callable
import unittest

from paperworks.v6.task039e3_r2r_authorization_v1 import (
    DIRECT_NUMBER_PROMPT_HASH,
    DIRECT_NUMBER_SCHEMA_HASH,
    EXACT_ENDPOINT,
    EXACT_MODEL,
    MAIN_PROMPT_HASH,
    RECOVERY_SCHEMA_V2_HASH,
    RELATION_SCHEDULE_HASH,
    T2_FOLLOWUP_PROMPT_HASH,
)
from paperworks.v6.task039e3_r2r_precontact_v1 import (
    GuardedR2RRootsV1,
    R2RLivePathDependenciesV1,
    R2RObservedIntegrityStateV1,
    R2RPostContactIntegrityGuardV1,
    R2RSourceBlobIdentityV1,
    R2R_SCIENTIFIC_ACCOUNTING_BEHAVIOR_HASH_V1,
    capture_r2r_integrity_snapshot_v1,
    run_r2r_live_execution_path_v1,
)


ROOT = Path(__file__).resolve().parents[1]
BASE = "9d7c165725cff2f36f6f2fbab9f6ad8037eb2540"
C1_A = "3aa63588b08692b0333de26d3042b717e62014f2"
C1_B = "c6e34440ee362df51e95b6181853f3f89fe4310e"
ENTRYPOINT = "scripts/run_task039e3_r2r_scientific_execution_v1.py"
MANIFEST_PATH = "docs/task_reports/TASK-039E3_R2R_C1_SOURCE_FREEZE.json"
MANIFEST_HASH = "35e73804156c097b27ae3d216575af6867a6330d346ddc71c888b5917a60859a"
OLD_MANIFEST_PATH = "docs/task_reports/TASK-039E3_R2R_SOURCE_FREEZE.json"
OLD_MANIFEST_HASH = "4d6d3b080b545b2effb98240d413ae085ad1c912ab39e489edd6dc582fa65655"
AUTHORIZATION_SCHEMA = (
    "schemas/v6/task039e3_r2r_execution_authorization_v1_schema.json"
)
REPORTS_ONLY = {
    "docs/task_reports/TASK-039E3_R2R_C1_IMPLEMENTATION_RECEIPT.json",
    "docs/task_reports/TASK-039E3_R2R_C1_REPORT.md",
    "docs/task_reports/TASK-039E3_R2R_C1_SOURCE_FREEZE.json",
    "docs/task_reports/TASK-039E3_R2R_C1_TEST_REPORT.json",
}


def _git_bytes(*arguments: str) -> bytes:
    return subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def _git_text(*arguments: str) -> str:
    return _git_bytes(*arguments).decode("utf-8").strip()


def _blob(commit: str, repository_path: str) -> bytes:
    return _git_bytes("show", f"{commit}:{repository_path}")


def _parent(commit: str) -> str:
    lineage = _git_text("rev-list", "--parents", "-n", "1", commit).split()
    if len(lineage) != 2:
        raise AssertionError(f"one parent required for {commit}: {lineage[1:]}")
    return lineage[1]


def _canonical_hash(document: object) -> str:
    return hashlib.sha256(
        json.dumps(
            document,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
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
    relative = path.removeprefix("src/").removesuffix(".py")
    parts = relative.split("/")
    parts.pop()
    return ".".join(parts)


def _module_paths(module: str, tracked: set[str]) -> set[str]:
    """Resolve a local module and package initializers that Python imports."""

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


def reconstruct_active_closure(
    commit: str,
) -> tuple[set[str], set[str], set[str]]:
    """Parse raw Git blobs and return closure, dynamic observations, unresolved."""

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
                    package = _package_for_path(path)
                    relative = "." * node.level + (node.module or "")
                    module = importlib.util.resolve_name(relative, package)
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


def _manifest_state(manifest: dict[str, Any]) -> R2RObservedIntegrityStateV1:
    records = manifest["source_records"]
    blobs = tuple(
        R2RSourceBlobIdentityV1(
            str(record["repository_path"]),
            str(record["git_blob_sha"]),
            str(record["sha256"]),
        )
        for record in records
    )
    return R2RObservedIntegrityStateV1(
        execution_commit=C1_A,
        source_manifest_hash=MANIFEST_HASH,
        source_blobs=blobs,
        authorization_hash="a" * 64,
        recovery_main_provider_schema_v2_hash=RECOVERY_SCHEMA_V2_HASH,
        main_prompt_hash=MAIN_PROMPT_HASH,
        t2_followup_prompt_hash=T2_FOLLOWUP_PROMPT_HASH,
        direct_number_prompt_hash=DIRECT_NUMBER_PROMPT_HASH,
        direct_number_schema_hash=DIRECT_NUMBER_SCHEMA_HASH,
        exact_model=EXACT_MODEL,
        endpoint=EXACT_ENDPOINT,
        sampling_configuration_hash="b" * 64,
        timeout_seconds=30.0,
        retry_policy_hash="c" * 64,
        relation_schedule_hash=RELATION_SCHEDULE_HASH,
        scientific_concurrency=1,
        scientific_call_budget_hash="d" * 64,
        scientific_accounting_behavior_hash=(
            R2R_SCIENTIFIC_ACCOUNTING_BEHAVIOR_HASH_V1
        ),
        recovery_execution_configuration_hash="e" * 64,
    )


class _PrecontactSentinelFailure(RuntimeError):
    pass


def _synthetic_dependencies(
    *,
    manifest: dict[str, Any],
    failed_stage: str | None,
    events: list[str],
    credential_calls: list[int],
) -> R2RLivePathDependenciesV1[Any, ...]:
    state = _manifest_state(manifest)

    def step(name: str, result: Any) -> Callable[..., Any]:
        def invoke(*_arguments: Any) -> Any:
            events.append(name)
            if name == failed_stage:
                raise _PrecontactSentinelFailure(name)
            return result

        return invoke

    def credential() -> str:
        credential_calls.append(1)
        events.append("credential")
        return "synthetic-sentinel-not-a-secret"

    def integrity(*_arguments: Any) -> R2RPostContactIntegrityGuardV1:
        events.append("integrity")
        if failed_stage == "integrity":
            raise _PrecontactSentinelFailure("integrity")
        return R2RPostContactIntegrityGuardV1(
            capture_r2r_integrity_snapshot_v1(state), lambda: state
        )

    roots = GuardedR2RRootsV1(
        ROOT,
        ROOT.parent / "synthetic-e1-never-opened",
        ROOT.parent / "synthetic-capability-never-opened",
        ROOT.parent / "synthetic-recovery-never-written",
        ROOT.parent / "synthetic-public-never-written",
    )
    return R2RLivePathDependenciesV1(
        authorization_guard=step("authorization", "authorization"),
        git_source_manifest_guard=step("git_source", "git-source"),
        forensic_protocol_guard=step("forensic_protocol", "forensic"),
        capability_reuse_guard=step("capability_reuse", "PASS_REUSED"),
        execution_root_guard=step("roots", roots),
        fresh_ledger_guard=step("fresh_ledgers", "four-empty-ledgers"),
        integrity_snapshot_guard=integrity,
        credential_loader=credential,
        transport_factory=step("transport", "synthetic-transport"),
        e1_loader=step("e1", "synthetic-evidence"),
        scientific_runner=step("science", "synthetic-science"),
        success_finalizer=step("finalizer", {"status": "synthetic-pass"}),
        failure_finalizer=step("failure_finalizer", {}),
    )


class R2RIndependentAuditSourcePrecontactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = _self_hashed_document(C1_B, MANIFEST_PATH)
        cls.closure, cls.dynamic_observations, cls.unresolved = (
            reconstruct_active_closure(C1_A)
        )

    def test_exact_c1_lineage_and_reports_only_commit_b(self) -> None:
        self.assertEqual(_parent(C1_A), BASE)
        self.assertEqual(_parent(C1_B), C1_A)
        changes = _git_text(
            "diff", "--name-status", "--no-renames", C1_A, C1_B
        ).splitlines()
        self.assertTrue(all(line.startswith("A\t") for line in changes))
        self.assertEqual({line.split("\t", 1)[1] for line in changes}, REPORTS_ONLY)

    def test_complete_manifest_self_hash_and_independent_closure(self) -> None:
        manifest = self.manifest
        records = manifest["source_records"]
        frozen = {str(record["repository_path"]) for record in records}
        self.assertEqual(manifest["artifact_hash"], MANIFEST_HASH)
        self.assertEqual(manifest["described_commit"], C1_A)
        self.assertEqual(manifest["closure_entrypoint"], ENTRYPOINT)
        self.assertEqual(len(self.closure), 49)
        self.assertEqual(len(self.closure - {ENTRYPOINT}), 48)
        self.assertEqual(self.dynamic_observations, set())
        self.assertEqual(self.unresolved, set())
        self.assertEqual(self.closure - frozen, set())
        self.assertEqual(frozen - self.closure, {AUTHORIZATION_SCHEMA})
        self.assertEqual(manifest["material_path_count"], len(self.closure))
        self.assertEqual(manifest["source_record_count"], len(records))
        self.assertEqual(manifest["unbound_material_project_local_dependency_count"], 0)
        self.assertTrue(manifest["active_source_freeze_complete"])

    def test_all_records_are_exact_git_and_actual_worktree_bytes(self) -> None:
        records = self.manifest["source_records"]
        paths = [str(record["repository_path"]) for record in records]
        self.assertEqual(paths, sorted(paths))
        self.assertEqual(len(paths), 50)
        self.assertEqual(len(paths), len(set(paths)))
        for record in records:
            path = str(record["repository_path"])
            raw = _blob(C1_A, path)
            with self.subTest(path=path):
                self.assertEqual(
                    _git_text("rev-parse", f"{C1_A}:{path}"),
                    record["git_blob_sha"],
                )
                self.assertEqual(hashlib.sha256(raw).hexdigest(), record["sha256"])
                self.assertEqual(_blob(C1_B, path), raw)

    def test_isolated_eol_safe_checkout_reproduces_all_exact_bytes(self) -> None:
        """Prove the guarded future topology can reproduce Git bytes on Windows.

        The audit worktree inherits system ``core.autocrlf=true`` and is an
        inspection/test topology, not an eligible live-execution checkout.  A
        separate temporary index plus checkout with conversion disabled must
        reproduce every authority byte without changing this worktree.
        """

        records = self.manifest["source_records"]
        with tempfile.TemporaryDirectory(prefix="r2r-audit-exact-checkout-") as raw:
            destination = Path(raw) / "worktree"
            subprocess.run(
                [
                    "git",
                    "clone",
                    "--no-checkout",
                    "--shared",
                    str(ROOT),
                    str(destination),
                ],
                cwd=ROOT,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            subprocess.run(
                [
                    "git",
                    "-c",
                    "core.autocrlf=false",
                    "-c",
                    "core.eol=lf",
                    "checkout",
                    "--detach",
                    "-f",
                    C1_A,
                ],
                cwd=destination,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            for record in records:
                path = str(record["repository_path"])
                with self.subTest(path=path):
                    actual = (destination / path).read_bytes()
                    self.assertEqual(actual, _blob(C1_A, path))
                    self.assertEqual(hashlib.sha256(actual).hexdigest(), record["sha256"])

    def test_windows_audit_checkout_is_explicitly_not_the_live_topology(self) -> None:
        """Keep the current audit worktree's EOL transformation visible."""

        mismatches = {
            str(record["repository_path"])
            for record in self.manifest["source_records"]
            if (ROOT / str(record["repository_path"])).read_bytes()
            != _blob(C1_A, str(record["repository_path"]))
        }
        self.assertEqual(_git_text("config", "--get", "core.autocrlf"), "true")
        self.assertEqual(len(mismatches), 50)
        self.assertEqual(
            mismatches,
            {str(record["repository_path"]) for record in self.manifest["source_records"]},
        )

    def test_historical_manifest_is_not_future_live_authority(self) -> None:
        historical = _self_hashed_document(C1_B, OLD_MANIFEST_PATH)
        old_paths = {
            str(record["repository_path"])
            for record in historical["source_records"]
        }
        self.assertEqual(historical["artifact_hash"], OLD_MANIFEST_HASH)
        self.assertNotEqual(historical["described_commit"], C1_A)
        self.assertNotEqual(historical["artifact_hash"], MANIFEST_HASH)
        self.assertEqual(len(self.closure - old_paths), 10)
        self.assertTrue(
            self.manifest["historical_source_manifest_superseded_for_future_r2r"]
        )
        self.assertEqual(
            self.manifest["historical_source_manifest_hash"], OLD_MANIFEST_HASH
        )

    def test_every_material_active_source_mutation_blocks_the_next_attempt(self) -> None:
        initial = _manifest_state(self.manifest)
        by_path = {blob.repository_path: index for index, blob in enumerate(initial.source_blobs)}
        self.assertEqual(self.closure - set(by_path), set())
        detected: set[str] = set()
        for path in sorted(self.closure):
            index = by_path[path]
            original = initial.source_blobs[index]
            for field, changed_value in (
                ("git_blob_sha", "f" * 40),
                ("sha256", "f" * 64),
            ):
                with self.subTest(path=path, field=field):
                    changed = list(initial.source_blobs)
                    changed[index] = replace(original, **{field: changed_value})
                    holder = {
                        "state": replace(initial, source_blobs=tuple(changed))
                    }
                    guard = R2RPostContactIntegrityGuardV1(
                        capture_r2r_integrity_snapshot_v1(initial),
                        lambda: holder["state"],
                    )
                    attempts: list[str] = []
                    with self.assertRaises(Exception):
                        guard.invoke_guarded_provider_attempt(
                            lambda: attempts.append("forbidden")
                        )
                    self.assertEqual(attempts, [])
                    self.assertTrue(guard.blocked)
                    holder["state"] = initial
                    with self.assertRaisesRegex(Exception, "permanently blocked"):
                        guard.invoke_guarded_provider_attempt(
                            lambda: attempts.append("forbidden")
                        )
                    self.assertEqual(attempts, [])
            detected.add(path)
        self.assertEqual(detected, self.closure)

    def test_every_precontact_guard_family_blocks_before_credential(self) -> None:
        stages = (
            "authorization",
            "git_source",
            "forensic_protocol",
            "capability_reuse",
            "roots",
            "fresh_ledgers",
            "integrity",
        )
        for failed in stages:
            with self.subTest(failed=failed):
                events: list[str] = []
                credentials: list[int] = []
                with self.assertRaises(_PrecontactSentinelFailure):
                    run_r2r_live_execution_path_v1(
                        _synthetic_dependencies(
                            manifest=self.manifest,
                            failed_stage=failed,
                            events=events,
                            credential_calls=credentials,
                        )
                    )
                self.assertEqual(credentials, [])
                self.assertNotIn("transport", events)
                self.assertNotIn("e1", events)
                self.assertNotIn("science", events)

    def test_successful_sentinel_order_has_one_credential_and_no_capability_probe(self) -> None:
        events: list[str] = []
        credentials: list[int] = []
        result = run_r2r_live_execution_path_v1(
            _synthetic_dependencies(
                manifest=self.manifest,
                failed_stage=None,
                events=events,
                credential_calls=credentials,
            )
        )
        self.assertEqual(
            events,
            [
                "authorization",
                "git_source",
                "forensic_protocol",
                "capability_reuse",
                "roots",
                "fresh_ledgers",
                "integrity",
                "credential",
                "transport",
                "e1",
                "science",
                "finalizer",
            ],
        )
        self.assertEqual(credentials, [1])
        self.assertEqual(result.credential_loader_calls, 1)
        self.assertEqual(result.capability_probe_calls, 0)
        self.assertEqual(result.historical_partial_records_reused, 0)
        dependency_fields = set(R2RLivePathDependenciesV1.__dataclass_fields__)
        self.assertTrue(
            {"capability_probe", "capability_transport", "capability_request_builder"}.isdisjoint(
                dependency_fields
            )
        )
        for path in (
            ENTRYPOINT,
            "src/paperworks/v6/task039e3_r2r_precontact_v1.py",
            "src/paperworks/v6/task039e3_r2r_live_execution_v1.py",
        ):
            source = _blob(C1_A, path).decode("utf-8")
            self.assertNotIn("build_recovery_capability_request_v1", source)
            self.assertNotIn("execute_recovery_capability_probe_v3", source)


if __name__ == "__main__":
    unittest.main()
