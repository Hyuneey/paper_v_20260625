#!/usr/bin/env python3
"""Refresh every generated RCC view without executing scientific code."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Sequence

from build_dashboard import load_registry


def _run(script: Path, *arguments: str) -> None:
    completed = subprocess.run(
        [sys.executable, str(script), *arguments],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if completed.stdout:
        print(completed.stdout.rstrip())
    if completed.returncode:
        raise RuntimeError(f"RCC refresh blocked at {script.name}")


def refresh(rcc_root: Path) -> None:
    root = rcc_root.resolve()
    scripts = root / "scripts"
    root_arg = str(root)

    _run(scripts / "validate_registry.py", "--rcc-root", root_arg, "--registry-only")
    _run(scripts / "build_dashboard.py", "--rcc-root", root_arg, "--dashboard-only")
    _run(scripts / "build_dashboard.py", "--rcc-root", root_arg, "--summaries-only")
    _run(scripts / "validate_registry.py", "--rcc-root", root_arg)

    data = load_registry(root)
    unresolved = sum(row["status"] == "OPEN" for row in data["decisions"])
    print(
        "RCC_REFRESH_PASS "
        f"components={len(data['components'])} experiments={len(data['experiments'])} "
        f"claims={len(data['claims'])} history_events={len(data['timeline'])} "
        f"history_decisions={len(data['decisions'])} unresolved_decisions={unresolved} "
        "scientific_executions=0 private_exposures=0"
    )


def main(argv: Sequence[str] | None = None) -> int:
    root = Path(__file__).resolve().parents[1]
    try:
        refresh(root)
    except RuntimeError as exc:
        print(f"RCC_REFRESH_BLOCKED: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
