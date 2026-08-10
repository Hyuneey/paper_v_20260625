"""Run unittest modules from a Git-tracked public test allowlist.

Known optional import boundaries are reported instead of loaded. Every other
loader error and every runnable assertion failure remains fatal.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import unittest
from pathlib import Path


def _tracked_test_modules(repository_root: Path) -> tuple[str, ...]:
    output = subprocess.run(
        ["git", "ls-files", "--", "tests/test*.py"],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return tuple(
        path[:-3].replace("/", ".").replace("\\", ".")
        for path in output.splitlines()
        if path
    )


def _optional_category(error: str) -> str | None:
    if "No module named 'jsonschema'" in error:
        return "jsonschema"
    if "No module named 'pytest'" in error:
        return "pytest"
    if any(
        token in error
        for token in (
            "GDN_OPTIONAL_DEPENDENCY_UNAVAILABLE",
            "No module named 'torch'",
            "No module named 'torch_geometric'",
        )
    ):
        return "torch_pyg"
    return None


def run(repository_root: Path) -> tuple[unittest.TestResult, dict[str, object]]:
    modules = _tracked_test_modules(repository_root)
    combined = unittest.TestSuite()
    optional = {"jsonschema": 0, "pytest": 0, "torch_pyg": 0}
    unexplained: list[dict[str, str]] = []
    for module in modules:
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromName(module)
        if loader.errors:
            error = "\n".join(loader.errors)
            category = _optional_category(error)
            if category is None:
                unexplained.append({"module": module, "error": error})
            else:
                optional[category] += 1
            continue
        combined.addTests(suite)
    if unexplained:
        raise RuntimeError(json.dumps({"unexplained": unexplained}, sort_keys=True))
    runnable = combined.countTestCases()
    result = unittest.TextTestRunner(verbosity=1).run(combined)
    summary: dict[str, object] = {
        "tracked_test_modules": len(modules),
        "runnable_tests": runnable,
        "known_optional_import_errors": optional,
        "known_optional_import_error_total": sum(optional.values()),
        "failures": len(result.failures),
        "errors": len(result.errors),
    }
    return result, summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    root = args.repository_root.resolve()
    source_root = root / "src"
    tests_root = root / "tests"
    for path in (root, source_root, tests_root):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
    result, summary = run(root)
    print(json.dumps(summary, sort_keys=True))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
