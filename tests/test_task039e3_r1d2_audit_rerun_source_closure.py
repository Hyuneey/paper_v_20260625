"""Independent complete-source oracle for the R1D2 audit rerun.

The oracle resolves imports from exact Git blobs at the executable commit.  It
does not rely on the SF1 closure implementation, worktree line endings, or the
historical blocked audit's asserted counts.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import unittest


R1D2_A = "2653f2b7349a049f9ca4828d736dfea9462c4748"
R1D2_B = "3da8b7007b7dd78d934554b299e6cb264a0e6470"
BLOCKED_AUDIT_B = "460cc11a038ba2fd5604a4b2b0b57616b70c97cc"
SF1_A = "86e7b38c36286a140f2549cff388b6700ab5d363"
SF1_B = "5296cf7a054d4fc3bbfdf742b70585bc0dc90515"
ENTRYPOINT = "scripts/run_task039e3_recovery_execution_v3.py"
MANIFEST_PATH = (
    "docs/task_reports/TASK-039E3_R1D2_SF1_COMPLETE_SOURCE_FREEZE.json"
)
OLD_MANIFEST_PATH = "docs/task_reports/TASK-039E3_R1D2_SOURCE_FREEZE.json"
COMPLETE_MANIFEST_HASH = (
    "e8f236a8238bad744eced3009e2000bab9597094cab04446d920df0a0ddf9283"
)
EXTRA_RUNTIME_SUPPORT_RECORD = (
    "schemas/v6/task039e3_recovery_execution_authorization_v3_schema.json"
)


def _repository() -> Path:
    return Path(__file__).resolve().parents[1]


def _git_bytes(*arguments: str) -> bytes:
    return subprocess.run(
        ["git", *arguments],
        cwd=_repository(),
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
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _self_hashed_document(commit: str, path: str) -> dict[str, object]:
    document = json.loads(_blob(commit, path))
    supplied = str(document.pop("artifact_hash"))
    if supplied != _canonical_hash(document):
        raise AssertionError(f"self-hash mismatch: {path}")
    return {"artifact_hash": supplied, **document}


def _tracked_paths(commit: str) -> set[str]:
    return set(_git_text("ls-tree", "-r", "--name-only", commit).splitlines())


def _package_for_path(path: str) -> str:
    relative = path.removeprefix("src/").removesuffix(".py")
    parts = relative.split("/")
    if parts[-1] == "__init__":
        parts.pop()
    else:
        parts.pop()
    return ".".join(parts)


def _module_paths(module: str, tracked: set[str]) -> set[str]:
    """Resolve a module plus every project package initializer Python loads."""

    if not module.startswith("paperworks"):
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


def _qualified_call_name(node: ast.expr, aliases: dict[str, str]) -> str:
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
    """Return closure, deterministically resolved dynamic imports, unresolved ones."""

    tracked = _tracked_paths(commit)
    pending = [ENTRYPOINT]
    closure: set[str] = set()
    resolved_dynamic: set[str] = set()
    unresolved_dynamic: set[str] = set()
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
                    bound_name = alias.asname or alias.name.split(".")[0]
                    aliases[bound_name] = alias.name if alias.asname else bound_name
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
            call_name = _qualified_call_name(node.func, aliases)
            if call_name not in dynamic_functions:
                continue
            if not node.args or not isinstance(node.args[0], ast.Constant):
                unresolved_dynamic.add(f"{path}:{call_name}:nonliteral")
                continue
            value = node.args[0].value
            if not isinstance(value, str):
                unresolved_dynamic.add(f"{path}:{call_name}:nonstr")
                continue
            if call_name in {"__import__", "importlib.import_module"}:
                dynamic_paths = _module_paths(value, tracked)
            else:
                normalized = value.replace("\\", "/")
                dynamic_paths = {normalized} if normalized in tracked else set()
            if dynamic_paths:
                resolved_dynamic.update(dynamic_paths)
                pending.extend(dynamic_paths - closure)
            elif value.startswith("paperworks") or value.startswith("src/paperworks"):
                unresolved_dynamic.add(f"{path}:{call_name}:{value}")
    return closure, resolved_dynamic, unresolved_dynamic


class R1D2AuditRerunSourceClosureTests(unittest.TestCase):
    def test_complete_manifest_self_hash_and_provenance(self) -> None:
        manifest = _self_hashed_document(SF1_B, MANIFEST_PATH)
        self.assertEqual(manifest["artifact_hash"], COMPLETE_MANIFEST_HASH)
        self.assertEqual(manifest["described_execution_commit"], R1D2_A)
        self.assertEqual(manifest["source_record_count"], 41)
        self.assertEqual(manifest["unbound_material_dependency_count"], 0)
        self.assertTrue(manifest["active_source_freeze_complete"])
        self.assertEqual(_git_text("rev-parse", f"{SF1_A}^"), BLOCKED_AUDIT_B)
        self.assertEqual(_git_text("rev-parse", f"{SF1_B}^"), SF1_A)

    def test_independent_transitive_closure_is_fully_covered(self) -> None:
        closure, resolved_dynamic, unresolved_dynamic = reconstruct_active_closure(
            R1D2_A
        )
        manifest = _self_hashed_document(SF1_B, MANIFEST_PATH)
        records = manifest["source_records"]
        assert isinstance(records, list)
        frozen = {str(record["repository_path"]) for record in records}
        self.assertEqual(len(closure), 40)
        self.assertEqual(len(closure - {ENTRYPOINT}), 39)
        self.assertEqual(resolved_dynamic, set())
        self.assertEqual(unresolved_dynamic, set())
        self.assertEqual(closure - frozen, set())
        self.assertEqual(frozen - closure, {EXTRA_RUNTIME_SUPPORT_RECORD})

    def test_all_41_records_reproduce_from_exact_git_objects(self) -> None:
        manifest = _self_hashed_document(SF1_B, MANIFEST_PATH)
        records = manifest["source_records"]
        assert isinstance(records, list)
        paths = [str(record["repository_path"]) for record in records]
        self.assertEqual(paths, sorted(paths))
        self.assertEqual(len(paths), 41)
        self.assertEqual(len(paths), len(set(paths)))
        for record in records:
            path = str(record["repository_path"])
            raw = _blob(R1D2_A, path)
            with self.subTest(path=path):
                self.assertEqual(
                    _git_text("rev-parse", f"{R1D2_A}:{path}"),
                    record["git_blob_sha"],
                )
                self.assertEqual(hashlib.sha256(raw).hexdigest(), record["sha256"])
                self.assertEqual(_blob(R1D2_B, path), raw)
                self.assertEqual(_blob(SF1_B, path), raw)

    def test_old_manifest_omissions_are_exactly_the_25_sf1_additions(self) -> None:
        closure, _, _ = reconstruct_active_closure(R1D2_A)
        old = _self_hashed_document(R1D2_B, OLD_MANIFEST_PATH)
        complete = _self_hashed_document(SF1_B, MANIFEST_PATH)
        old_paths = {
            str(record["repository_path"]) for record in old["source_records"]
        }
        complete_paths = {
            str(record["repository_path"]) for record in complete["source_records"]
        }
        omitted = closure - old_paths
        self.assertEqual(len(old_paths), 16)
        self.assertEqual(len(omitted), 25)
        self.assertEqual(complete_paths, old_paths | omitted)
        self.assertEqual(omitted - complete_paths, set())


if __name__ == "__main__":
    unittest.main()
