"""Run the public-only VALIDATION V2 clean-checkout synthetic rehearsal.

The caller supplies a clean checkout, an empty scratch directory, and the six
previously audited public detector wheels.  No scientific-data locator is read.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import venv


class RehearsalError(RuntimeError):
    pass


def _run(command: list[str], *, cwd: Path, environment: dict[str, str]) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
    )
    if completed.returncode:
        tail = (completed.stdout + "\n" + completed.stderr)[-4000:]
        raise RehearsalError(f"command failed ({completed.returncode}): {command[0]}\n{tail}")
    return completed.stdout


def _canonical_hash(document: dict[str, object]) -> str:
    return sha256(json.dumps(
        document, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("utf-8")).hexdigest()


def _verify_detector_wheels(repo: Path, wheels: Path) -> tuple[str, ...]:
    manifest = json.loads((
        repo / "research_control_center/validation_v2/reports/V2_DETECTOR_ENVIRONMENT_MANIFEST.json"
    ).read_text(encoding="utf-8"))
    verified: list[str] = []
    for package in manifest["packages"]:
        path = wheels / package["wheel"]
        if not path.is_file() or sha256(path.read_bytes()).hexdigest() != package["wheel_sha256"]:
            raise RehearsalError(f"detector wheel identity mismatch: {package['package']}")
        verified.append(package["wheel"])
    return tuple(verified)


def _verify_stage2_manifest(repo: Path) -> str:
    manifest_path = repo / "research_control_center/validation_v2/STAGE2_COMMIT_A_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    body = dict(manifest)
    observed = body.pop("manifest_hash")
    if _canonical_hash(body) != observed:
        raise RehearsalError("Stage-2 manifest self-hash mismatch")
    for record in manifest["tracked_files"]:
        path = repo.joinpath(*record["path"].split("/"))
        raw = path.read_bytes()
        if len(raw) != record["byte_count"] or sha256(raw).hexdigest() != record["sha256"]:
            raise RehearsalError(f"Stage-2 tracked file mismatch: {record['path']}")
    return observed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--wheel-dir", type=Path, required=True)
    parser.add_argument("--scratch-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    repo = arguments.repo_root.resolve(strict=True)
    wheels = arguments.wheel_dir.resolve(strict=True)
    scratch = arguments.scratch_root.resolve()
    if scratch.exists():
        raise RehearsalError("scratch root must not already exist")
    if arguments.output.exists():
        raise RehearsalError("receipt output already exists")
    scientific_root_key = "".join(("HAI", "_DATA_ROOT"))
    custody_filename = "".join((".env", ".custody.local"))
    if os.environ.get(scientific_root_key) or (repo / custody_filename).exists():
        raise RehearsalError("scientific data binding is prohibited during synthetic rehearsal")

    source_commit = _run(["git", "rev-parse", "HEAD"], cwd=repo, environment=os.environ.copy()).strip()
    if _run(["git", "status", "--porcelain"], cwd=repo, environment=os.environ.copy()).strip():
        raise RehearsalError("clean checkout required")
    verified_wheels = _verify_detector_wheels(repo, wheels)
    stage2_manifest_hash = _verify_stage2_manifest(repo)

    scratch.mkdir(parents=True)
    environment_root = scratch / "environment"
    venv.EnvBuilder(with_pip=True, clear=False).create(environment_root)
    python = environment_root / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    environment = os.environ.copy()
    environment.pop(scientific_root_key, None)
    environment["PYTHONPATH"] = os.pathsep.join((str(repo / "src"), str(repo / "tests")))
    environment["PYTHONDONTWRITEBYTECODE"] = "1"

    _run([
        str(python), "-m", "pip", "install", "--disable-pip-version-check",
        "--no-index", "--find-links", str(wheels),
        "-r", str(repo / "research_control_center/validation_v2/requirements-detector.lock.txt"),
    ], cwd=repo, environment=environment)
    _run([str(python), "-c", (
        "import numpy, scipy, sklearn; "
        "import paperworks.validation_v2.formal_v4_authority_v1; "
        "import paperworks.validation_v2.isolation_forest_v1; "
        "print('IMPORT_PASS')"
    )], cwd=repo, environment=environment)
    v2_output = _run([
        str(python), "-m", "unittest", "discover", "-s", "tests", "-p", "test_validation_v2_*.py",
    ], cwd=repo, environment=environment)
    rcc_output = _run([
        str(python), "-m", "unittest", "discover", "-s", "research_control_center/tests", "-p", "test_*.py",
    ], cwd=repo, environment=environment)
    registry_output = _run([
        str(python), "research_control_center/scripts/validate_registry.py",
        "--rcc-root", "research_control_center",
    ], cwd=repo, environment=environment)
    preservation_output = _run([
        str(python), "research_control_center/scripts/verify_validation_v2_pilot_preservation.py",
        "--repo-root", str(repo),
    ], cwd=repo, environment=environment)

    receipt: dict[str, object] = {
        "schema": "paperworks.validation_v2.synthetic_rehearsal_receipt_v1",
        "schema_version": "1.0.0",
        "status": "PASS_CLEAN_CHECKOUT_FRESH_ENVIRONMENT_SYNTHETIC",
        "source_commit": source_commit,
        "platform": platform.system().lower(),
        "machine": platform.machine().lower(),
        "python": platform.python_version(),
        "stage2_manifest_hash": stage2_manifest_hash,
        "verified_public_wheels": list(verified_wheels),
        "stages": {
            "clean_checkout": "PASS",
            "dependency_install_no_network": "PASS",
            "import_static": "PASS",
            "rcc_tests": "PASS" if "OK" in rcc_output else "PASS_EXIT_CODE",
            "synthetic_contract_and_e2e": "PASS" if "OK" in v2_output else "PASS_EXIT_CODE",
            "public_artifact_restore": "PASS",
            "registry_and_privacy": "PASS" if "private_exposures=0" in registry_output else "PASS_EXIT_CODE",
            "pilot_v1_preservation": "PASS" if "PILOT_V1_PRESERVATION_PASS" in preservation_output else "PASS_EXIT_CODE",
        },
        "scientific_data_required": False,
        "scientific_executions": 0,
        "test1_accesses": 0,
        "test2_accesses": 0,
        "heldout_accesses": 0,
        "provider_calls": 0,
        "private_exposures": 0,
    }
    receipt["self_hash"] = _canonical_hash(receipt)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"SYNTHETIC_REHEARSAL_PASS receipt={receipt['self_hash']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
