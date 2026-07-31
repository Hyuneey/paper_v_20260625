import ast
import functools
import hashlib
import json
import os
import subprocess
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_HEAD = "337769066f62b8f4fcd8e48a9a8f8d3651e3818a"
INVENTORY_PATH = ROOT / "docs/task_reports/TASK-039P0_PUBLIC_SYMBOL_INVENTORY.json"
MATRIX_PATH = ROOT / "docs/task_reports/TASK-039P0_MIGRATION_MATRIX.json"
CONFIG_PATH = ROOT / "configs/v6/task039p0_alignment_freeze.json"

ALLOWED_ROOT_FILES = {
    "AGENTS.md",
    "IMPLEMENTATION_PLAN.md",
    "README.md",
    "THIRD_PARTY_NOTICES.md",
    "pyproject.toml",
}
ALLOWED_ROOT_DIRS = {
    "TASKS",
    "TEMPLATES",
    "configs",
    "docs",
    "fixtures",
    "prompts",
    "schemas",
    "scripts",
    "src",
    "tests",
}
PROHIBITED_ROOT_PARTS = {
    "artifacts",
    "data",
    "external",
    "private",
    ".git",
    ".venv",
    "venv",
    "__pycache__",
}
PROHIBITED_TOKENS = {
    "private_argos",
    "private_artifact",
    "raw_data",
    "secret",
    "credential",
}

ALLOWED_CLASSIFICATIONS = {
    "canonical_v6_core",
    "reusable_with_v2_adapter",
    "legacy_read_only",
    "frozen_reference_only",
    "engineering_support",
    "new_implementation_required",
    "unresolved_research_decision",
}

CANONICAL_MODULES = {
    "paperworks.contracts.rule_v1",
    "paperworks.contracts.graph_v1",
    "paperworks.contracts.evidence_v1",
    "paperworks.contracts.parameter_v1",
    "paperworks.contracts.verifier_v1",
    "paperworks.contracts.runtime_authority",
    "paperworks.contracts.runtime_v1",
    "paperworks.contracts.explanation_v1",
}
ENGINEERING_MODULES = {
    "paperworks",
    "paperworks.contracts",
    "paperworks.contracts.accepted_rule",
    "paperworks.contracts.artifact_hashing",
    "paperworks.contracts.models",
    "paperworks.contracts.schema_registry",
    "paperworks.contracts.vertical_slice_v1",
    "paperworks.candidates.smoke",
}
LEGACY_MODULES = {
    "paperworks.contracts.legacy_adapter",
    "paperworks.contracts.phase1_adapters",
}
REUSABLE_EXACT_MODULES = {
    "paperworks.candidates",
    "paperworks.candidates.universe",
    "paperworks.gdn.masked",
    "paperworks.profiling",
    "paperworks.profiling.relations",
    "paperworks.evaluation",
    "paperworks.evaluation.harness",
}
REUSABLE_PREFIXES = ("paperworks.data", "paperworks.metadata")
LEGACY_PREFIXES = (
    "paperworks.dsl",
    "paperworks.planning",
    "paperworks.verification",
    "paperworks.runtime",
    "paperworks.e2e",
)
DATASET_MARKERS = (
    "SWAT_DATA_ROOT",
    "DEC-007",
    "SWaT",
    "WADI",
    "merged.csv",
    "HAI",
)

VIRTUAL_COMPONENTS = (
    {
        "component_id": "paperworks.data.v2.dataset_manifest",
        "classification": "new_implementation_required",
        "reason": "Dataset-neutral HAI provenance and file-manifest contract.",
        "planned_task": "TASK-039P1/TASK-039A",
    },
    {
        "component_id": "paperworks.data.v2.split_manifest",
        "classification": "new_implementation_required",
        "reason": "Dataset-neutral construction, validity, utility, outer, and sealed roles.",
        "planned_task": "TASK-039P1",
    },
    {
        "component_id": "paperworks.contracts.normal_relation_evidence_v2",
        "classification": "new_implementation_required",
        "reason": "Normal-only relation evidence distinct from EvidencePackageV1.",
        "planned_task": "TASK-039P1",
    },
    {
        "component_id": "paperworks.contracts.detector_error_context_v1",
        "classification": "new_implementation_required",
        "reason": "Optional inner detector-error context that cannot replace normal evidence.",
        "planned_task": "TASK-039P1",
    },
    {
        "component_id": "paperworks.contracts.construction_outcome_v1",
        "classification": "new_implementation_required",
        "reason": "Typed no_rule and failure outcomes separate from no_op and abstain.",
        "planned_task": "TASK-039P1",
    },
    {
        "component_id": "paperworks.planning.v6.bounded_construction",
        "classification": "new_implementation_required",
        "reason": "Common T0/T1/T1-B/T2 budget and state contract.",
        "planned_task": "TASK-039F",
    },
    {
        "component_id": "paperworks.governance.rule_utility_v1",
        "classification": "new_implementation_required",
        "reason": "No-op-aware utility selection outside validity acceptance.",
        "planned_task": "TASK-039G",
    },
    {
        "component_id": "paperworks.detectors.fn_correction_v1",
        "classification": "new_implementation_required",
        "reason": "Primary detector false-negative correction adapter.",
        "planned_task": "TASK-039H",
    },
    {
        "component_id": "paperworks.explanation.observed_fact_binding_v2",
        "classification": "new_implementation_required",
        "reason": "Observed facts, satisfaction traces, and provenance-bound explanations.",
        "planned_task": "TASK-039I",
    },
    {
        "component_id": "paperworks.gdn.torch_backend_fidelity",
        "classification": "unresolved_research_decision",
        "reason": "Requires source-fidelity and optional-import evidence.",
        "planned_task": "TASK-039P1",
    },
    {
        "component_id": "paperworks.detectors.primary_detector",
        "classification": "unresolved_research_decision",
        "reason": "Primary detector identity and selection policy are not frozen.",
        "planned_task": "future protocol decision",
    },
    {
        "component_id": "paperworks.contracts.rule_v2",
        "classification": "unresolved_research_decision",
        "reason": "Retain, simplify, or defer Rule v1 severity and persistence.",
        "planned_task": "TASK-039P1",
    },
)


def _git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def tracked_paths(
    pathspecs: Iterable[str], *, skip_prohibited_paths: bool = False
) -> list[Path]:
    raw = _git("ls-files", "-z", "--", *pathspecs)
    paths = []
    for item in raw.decode("utf-8").split("\0"):
        if not item:
            continue
        candidate = ROOT / item
        try:
            assert_public_tracked_path(candidate)
        except ValueError as exc:
            if skip_prohibited_paths and str(exc) in {
                "prohibited root",
                "prohibited cache path",
                "prohibited token",
            }:
                continue
            raise
        paths.append(candidate)
    return sorted(paths)


def assert_public_tracked_path(path: Path) -> None:
    candidate = path if path.is_absolute() else ROOT / path
    resolved = candidate.resolve(strict=False)
    try:
        relative = resolved.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ValueError("path resolves outside repository") from exc

    parts_lower = [part.lower() for part in relative.parts]
    relative_lower = relative.as_posix().lower()
    if parts_lower and parts_lower[0] in PROHIBITED_ROOT_PARTS:
        raise ValueError("prohibited root")
    if "__pycache__" in parts_lower:
        raise ValueError("prohibited cache path")
    if any(token in relative_lower for token in PROHIBITED_TOKENS):
        raise ValueError("prohibited token")
    if not relative.parts:
        raise ValueError("repository root is not a readable file")
    if len(relative.parts) == 1:
        if relative.as_posix() not in ALLOWED_ROOT_FILES:
            raise ValueError("root file is not allowed")
    elif relative.parts[0] not in ALLOWED_ROOT_DIRS:
        raise ValueError("path is outside allowed public roots")

    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", relative.as_posix()],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError("path is not Git-tracked")


def read_public_text(path: Path) -> str:
    assert_public_tracked_path(path)
    return path.read_text(encoding="utf-8")


def read_public_bytes(path: Path) -> bytes:
    assert_public_tracked_path(path)
    return path.read_bytes()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_json(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return sha256_bytes(encoded)


def module_name_for(path: Path) -> str:
    relative = path.relative_to(ROOT / "src").with_suffix("")
    parts = list(relative.parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


@functools.lru_cache(maxsize=1)
def tracked_source_paths() -> frozenset[Path]:
    return frozenset(
        path.resolve()
        for path in tracked_paths(
            (
                ":(glob)src/paperworks/*.py",
                ":(glob)src/paperworks/**/*.py",
            )
        )
    )


def path_for_module(module_name: str) -> Path | None:
    if not module_name.startswith("paperworks"):
        return None
    relative = Path(*module_name.split("."))
    direct = ROOT / "src" / relative.with_suffix(".py")
    package = ROOT / "src" / relative / "__init__.py"
    tracked = tracked_source_paths()
    if direct.resolve() in tracked:
        return direct
    if package.resolve() in tracked:
        return package
    return None


def classify_module(module_name: str) -> str:
    if module_name in CANONICAL_MODULES:
        return "canonical_v6_core"
    if module_name in ENGINEERING_MODULES:
        return "engineering_support"
    if module_name in LEGACY_MODULES or module_name.startswith(LEGACY_PREFIXES):
        return "legacy_read_only"
    if module_name in {"paperworks.gdn", "paperworks.gdn.torch_backend"}:
        return "unresolved_research_decision"
    if module_name in REUSABLE_EXACT_MODULES or module_name.startswith(
        REUSABLE_PREFIXES
    ):
        return "reusable_with_v2_adapter"
    return "engineering_support"


def resolve_import_from(current_module: str, node: ast.ImportFrom) -> str:
    if node.level == 0:
        return node.module or ""
    package_parts = current_module.split(".")
    current_path = path_for_module(current_module)
    if current_path is not None and current_path.name != "__init__.py":
        package_parts.pop()
    keep = max(0, len(package_parts) - node.level + 1)
    base = package_parts[:keep]
    if node.module:
        base.extend(node.module.split("."))
    return ".".join(base)


def literal_all_names(tree: ast.Module) -> list[str]:
    names = []
    for node in tree.body:
        target_name = None
        value = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            if isinstance(node.targets[0], ast.Name):
                target_name = node.targets[0].id
            value = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            target_name = node.target.id
            value = node.value
        if target_name != "__all__" or not isinstance(value, (ast.List, ast.Tuple)):
            continue
        for item in value.elts:
            if isinstance(item, ast.Constant) and isinstance(item.value, str):
                names.append(item.value)
    return names


def import_origins(
    tree: ast.Module, current_module: str
) -> dict[str, tuple[str, str]]:
    origins = {}
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            source_module = resolve_import_from(current_module, node)
            for alias in node.names:
                origins[alias.asname or alias.name] = (source_module, alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                public_name = alias.asname or alias.name.split(".")[-1]
                origins[public_name] = (alias.name, alias.name.split(".")[-1])
    return origins


def public_symbols(
    tree: ast.Module, module_name: str
) -> list[dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for node in tree.body:
        name = None
        kind = None
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            name, kind = node.name, "function"
        elif isinstance(node, ast.ClassDef):
            name, kind = node.name, "class"
        elif isinstance(node, ast.Assign):
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                name, kind = node.targets[0].id, "constant"
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            name, kind = node.target.id, "constant"
        if name and not name.startswith("_") and name != "__all__":
            records[name] = {
                "name": name,
                "qualified_name": f"{module_name}.{name}",
                "kind": kind,
                "line": node.lineno,
                "classification": classify_module(module_name),
                "origin_module": module_name,
            }

    origins = import_origins(tree, module_name)
    for name in literal_all_names(tree):
        if name in records:
            continue
        source_module, source_name = origins.get(name, (module_name, name))
        records[name] = {
            "name": name,
            "qualified_name": f"{module_name}.{name}",
            "kind": "reexport",
            "line": None,
            "classification": classify_module(source_module),
            "origin_module": source_module,
            "origin_symbol": source_name,
        }
    return [records[name] for name in sorted(records)]


def imported_modules(tree: ast.Module, module_name: str) -> list[str]:
    imports = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add(resolve_import_from(module_name, node))
    return sorted(imports)


def module_reason(classification: str) -> str:
    return {
        "canonical_v6_core": (
            "TASK-032 versioned scientific contract retained as the v6 path; "
            "EvidencePackageV1 remains limited to its original scope."
        ),
        "reusable_with_v2_adapter": (
            "Reusable producer logic with data, split, provenance, or dataset "
            "assumptions that require a v2 adapter."
        ),
        "legacy_read_only": (
            "Historical Phase-1/RuleAst compatibility path; future v6 "
            "dependencies are prohibited."
        ),
        "engineering_support": (
            "Infrastructure, hashing, schema, packaging, or historical support "
            "without independent v6 scientific authority."
        ),
        "unresolved_research_decision": (
            "Requires explicit fidelity or schema evidence before v6 reuse."
        ),
    }[classification]


def build_inventory() -> dict[str, Any]:
    source_paths = tracked_paths(
        (
            ":(glob)src/paperworks/*.py",
            ":(glob)src/paperworks/**/*.py",
        )
    )
    modules = []
    all_symbols = []
    source_hash_records = []
    for path in source_paths:
        text = read_public_text(path)
        tree = ast.parse(text, filename=str(path))
        module_name = module_name_for(path)
        classification = classify_module(module_name)
        imports = imported_modules(tree, module_name)
        symbols = public_symbols(tree, module_name)
        markers = []
        for line_number, line in enumerate(text.splitlines(), start=1):
            for marker in DATASET_MARKERS:
                if marker in line:
                    markers.append({"marker": marker, "line": line_number})
        relative = path.relative_to(ROOT).as_posix()
        file_hash = sha256_bytes(read_public_bytes(path))
        modules.append(
            {
                "path": relative,
                "module": module_name,
                "sha256": file_hash,
                "classification": classification,
                "reason": module_reason(classification),
                "imports": imports,
                "legacy_imports": [
                    item
                    for item in imports
                    if item == "paperworks.dsl"
                    or item.startswith("paperworks.dsl.")
                    or item == "paperworks.verification"
                    or item.startswith("paperworks.verification.")
                    or item == "paperworks.runtime"
                    or item.startswith("paperworks.runtime.")
                ],
                "phase1_adapter_import": (
                    "paperworks.contracts.phase1_adapters" in imports
                ),
                "unconditional_torch_import": any(
                    item == "torch" or item.startswith("torch.")
                    for item in imports
                ),
                "dataset_markers": markers,
                "public_symbol_count": len(symbols),
                "public_symbols": symbols,
            }
        )
        source_hash_records.append({"path": relative, "sha256": file_hash})
        all_symbols.extend(
            {"module": module_name, "path": relative, **symbol}
            for symbol in symbols
        )

    schemas = []
    for path in tracked_paths((":(glob)schemas/*.json",)):
        schemas.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "sha256": sha256_bytes(read_public_bytes(path)),
                "classification": "canonical_v6_core",
                "scope": (
                    "Existing v1 schema retained without modification; it does "
                    "not silently define v6 normal evidence or Rule v2."
                ),
            }
        )

    fixture_paths = tracked_paths(
        (
            ":(glob)fixtures/task030/**/*.json",
            ":(glob)fixtures/task032*/**/*.json",
        )
    )
    fixture_records = [
        {
            "path": path.relative_to(ROOT).as_posix(),
            "sha256": sha256_bytes(read_public_bytes(path)),
        }
        for path in fixture_paths
    ]

    test_paths = tracked_paths(
        (
            ":(glob)tests/*.py",
            ":(glob)tests/**/*.py",
        ),
        skip_prohibited_paths=True,
    )
    test_records = []
    for path in test_paths:
        text = read_public_text(path)
        tree = ast.parse(text, filename=str(path))
        imports = imported_modules(tree, "tests")
        name = path.name.lower()
        test_records.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "sha256": sha256_bytes(text.encode("utf-8")),
                "task030_032_contract_test": any(
                    token in name
                    for token in ("task030", "task031", "task032")
                ),
                "task001_014_test": any(
                    f"task{number:03d}" in name for number in range(1, 15)
                ),
                "task022_038_boundary_test": any(
                    f"task{number:03d}" in name for number in range(22, 39)
                ),
                "imports_torch": any(
                    item == "torch" or item.startswith("torch.")
                    for item in imports
                ),
            }
        )

    module_counts = Counter(record["classification"] for record in modules)
    symbol_counts = Counter(record["classification"] for record in all_symbols)
    inventory = {
        "schema_version": "1.0",
        "artifact_type": "v6_public_symbol_inventory",
        "task_id": "TASK-039P0",
        "repository_head": EXPECTED_HEAD,
        "inventory_method": "git_tracked_public_allowlist_static_ast",
        "scope": {
            "production_public_symbol_root": "src/paperworks",
            "test_and_fixture_role": "boundary_evidence_not_production_symbols",
            "excluded_reference_path": (
                "ARGOS source is outside the R1 public allowlist and remains "
                "frozen by committed aggregate documentation."
            ),
            "public_symbol_rule": (
                "Top-level non-private class, function, or assignment plus "
                "literal __all__ re-exports."
            ),
        },
        "summary": {
            "production_module_count": len(modules),
            "production_public_symbol_count": len(all_symbols),
            "schema_count": len(schemas),
            "contract_fixture_count": len(fixture_records),
            "tracked_test_file_count": len(test_records),
            "task030_032_contract_test_count": sum(
                record["task030_032_contract_test"] for record in test_records
            ),
            "task001_014_test_count": sum(
                record["task001_014_test"] for record in test_records
            ),
            "task022_038_boundary_test_count": sum(
                record["task022_038_boundary_test"] for record in test_records
            ),
            "virtual_component_count": len(VIRTUAL_COMPONENTS),
            "module_classification_counts": dict(sorted(module_counts.items())),
            "symbol_classification_counts": dict(sorted(symbol_counts.items())),
        },
        "source_tree_hash": sha256_json(source_hash_records),
        "modules": modules,
        "schemas": schemas,
        "contract_fixtures": fixture_records,
        "test_audit": test_records,
        "virtual_components": list(VIRTUAL_COMPONENTS),
    }
    inventory["report_hash"] = sha256_json(inventory)
    return inventory


class Task039P0PublicPathGuardTests(unittest.TestCase):
    def test_tracked_allowed_file_passes(self) -> None:
        assert_public_tracked_path(ROOT / "README.md")

    def test_untracked_temporary_file_fails(self) -> None:
        handle, name = tempfile.mkstemp(
            prefix="task039p0_untracked_", suffix=".tmp", dir=ROOT / "tests"
        )
        os.close(handle)
        Path(name).unlink()
        try:
            Path(name).write_text("synthetic", encoding="utf-8")
            with self.assertRaises(ValueError):
                assert_public_tracked_path(Path(name))
        finally:
            Path(name).unlink(missing_ok=True)

    def test_parent_traversal_fails(self) -> None:
        with self.assertRaises(ValueError):
            assert_public_tracked_path(ROOT / ".." / "outside.txt")

    def test_synthetic_prohibited_artifact_path_fails(self) -> None:
        synthetic = ROOT / "artifacts" / "private_example" / "result.json"
        with self.assertRaises(ValueError):
            assert_public_tracked_path(synthetic)

    def test_synthetic_git_path_fails(self) -> None:
        with self.assertRaises(ValueError):
            assert_public_tracked_path(ROOT / ".git" / "config")

    def test_external_absolute_path_fails(self) -> None:
        external = Path("C:/task039p0_external/result.json")
        with self.assertRaises(ValueError):
            assert_public_tracked_path(external)

    def test_allowed_root_untracked_path_fails(self) -> None:
        synthetic = ROOT / "docs" / "task039p0_untracked_probe.md"
        with self.assertRaises(ValueError):
            assert_public_tracked_path(synthetic)


class Task039P0AlignmentAuditTests(unittest.TestCase):
    def test_inventory_is_complete_and_self_hashed(self) -> None:
        committed = json.loads(read_public_text(INVENTORY_PATH))
        observed_hash = committed.pop("report_hash")
        self.assertEqual(observed_hash, sha256_json(committed))
        expected = build_inventory()
        expected.pop("report_hash")
        self.assertEqual(committed, expected)

    def test_all_classifications_are_frozen_values(self) -> None:
        inventory = json.loads(read_public_text(INVENTORY_PATH))
        classifications = {
            record["classification"] for record in inventory["modules"]
        }
        classifications.update(
            symbol["classification"]
            for module in inventory["modules"]
            for symbol in module["public_symbols"]
        )
        classifications.update(
            item["classification"] for item in inventory["virtual_components"]
        )
        self.assertLessEqual(classifications, ALLOWED_CLASSIFICATIONS)

    def test_migration_matrix_and_config_are_self_hashed(self) -> None:
        for path, hash_field in (
            (MATRIX_PATH, "report_hash"),
            (CONFIG_PATH, "config_hash"),
        ):
            payload = json.loads(read_public_text(path))
            observed = payload.pop(hash_field)
            self.assertEqual(observed, sha256_json(payload))

    def test_v6_boundary_documents_are_consistent(self) -> None:
        required = (
            "TASKS/TASK-039P0_V6_CODEBASE_ALIGNMENT.md",
            "docs/v6/V6_CANONICAL_ARCHITECTURE.md",
            "docs/v6/V6_CODEBASE_INVENTORY.md",
            "docs/v6/V6_MIGRATION_MATRIX.md",
            "docs/v6/V6_SCIENTIFIC_BOUNDARIES.md",
            "docs/v6/V6_OPEN_DECISIONS.md",
            "docs/v6/V6_NEXT_TASK_SEQUENCE.md",
            "docs/task_reports/TASK-039P0_REPORT.md",
        )
        for relative in required:
            assert_public_tracked_path(ROOT / relative)
        combined = "\n".join(
            read_public_text(ROOT / relative)
            for relative in (
                "AGENTS.md",
                "IMPLEMENTATION_PLAN.md",
                "README.md",
                "docs/v6/V6_CANONICAL_ARCHITECTURE.md",
                "docs/v6/V6_SCIENTIFIC_BOUNDARIES.md",
            )
        )
        for term in (
            "HAI 23.05",
            "T1-B",
            "no_rule",
            "no_op",
            "abstain",
            "normal-only",
            "frozen reference",
        ):
            self.assertIn(term, combined)

    def test_canonical_contracts_do_not_import_primary_legacy_packages(self) -> None:
        inventory = json.loads(read_public_text(INVENTORY_PATH))
        canonical = [
            record
            for record in inventory["modules"]
            if record["classification"] == "canonical_v6_core"
        ]
        for record in canonical:
            self.assertEqual(record["legacy_imports"], [], record["module"])

    def test_no_recursive_workspace_enumeration_apis_are_used(self) -> None:
        tree = ast.parse(read_public_text(Path(__file__)), filename=__file__)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(
                node.func, ast.Attribute
            ):
                continue
            self.assertNotEqual(node.func.attr, "rglob")
            if (
                node.func.attr == "walk"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "os"
            ):
                self.fail("os.walk is prohibited")


def write_inventory() -> None:
    inventory = build_inventory()
    INVENTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    INVENTORY_PATH.write_text(
        json.dumps(inventory, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    import sys

    if "--write-inventory" in sys.argv:
        write_inventory()
    else:
        unittest.main()
