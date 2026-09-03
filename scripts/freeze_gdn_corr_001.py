#!/usr/bin/env python3
"""Freeze GDN-CORR-001 corrections before any corrected result access."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
from typing import Any, Mapping

from paperworks.validation_v2.gdn_corr_contract_v1 import (
    exp01b_r1_contract_document_v1,
    exp01c_preregistration_document_v1,
)


R1_CONTRACT = Path(
    "research_control_center/validation_v2/gdn_corr_001/contracts/"
    "EXP01B_R1_CORRECTION_CONTRACT.json"
)
EXP01C_PREREG = Path(
    "research_control_center/validation_v2/gdn_corr_001/exp01c_gdn_hai/"
    "preregistration/EXP01C_PREREGISTRATION.json"
)
IMPLEMENTATION_FILES = (
    "src/paperworks/validation_v2/gdn_corr_v1.py",
    "src/paperworks/validation_v2/gdn_corr_contract_v1.py",
    "src/paperworks/validation_v2/exp01c_backend_v1.py",
    "scripts/freeze_gdn_corr_001.py",
)


class FreezeError(RuntimeError):
    pass


def _canonical(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        dict(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8") + b"\n"


def _head(root: Path) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True,
    ).strip()


def _hashes(root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for relative in IMPLEMENTATION_FILES:
        path = root / relative
        if not path.is_file():
            raise FreezeError(f"GDN_CORR_IMPLEMENTATION_MISSING:{relative}")
        result[relative] = sha256(path.read_bytes()).hexdigest()
    return result


def _write_new(root: Path, relative: Path, value: Mapping[str, Any]) -> None:
    target = root / relative
    payload = _canonical(value)
    if target.exists():
        if target.read_bytes() != payload:
            raise FreezeError(f"GDN_CORR_EXISTING_FREEZE_MISMATCH:{relative.as_posix()}")
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb", closefd=False) as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        os.close(descriptor)
    if target.read_bytes() != payload:
        raise FreezeError(f"GDN_CORR_FREEZE_REOPEN_FAILED:{relative.as_posix()}")


def freeze(root: Path) -> None:
    source_commit = _head(root)
    implementation_hashes = _hashes(root)
    r1 = exp01b_r1_contract_document_v1(
        source_commit=source_commit, implementation_hashes=implementation_hashes,
    )
    prereg = exp01c_preregistration_document_v1(
        source_commit=source_commit, implementation_hashes=implementation_hashes,
    )
    _write_new(root, R1_CONTRACT, r1)
    _write_new(root, EXP01C_PREREG, prereg)
    print(json.dumps({
        "status": "PASS_FROZEN_BEFORE_CORRECTED_RESULT_ACCESS",
        "source_commit": source_commit,
        "r1_contract_hash": r1["contract_hash"],
        "exp01c_preregistration_hash": prereg["preregistration_hash"],
        "test1_accesses": 0, "label_accesses": 0,
        "test2_accesses": 0, "heldout_accesses": 0,
    }, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    freeze(Path(args.root).resolve())


if __name__ == "__main__":
    main()
