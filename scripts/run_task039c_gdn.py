"""Generate TASK-039C-GDN Phase-A and fail-closed result artifacts."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from paperworks.candidates.gdn_candidate_discovery_v1 import (  # noqa: E402
    build_blocked_gdn_result_v1,
)
from paperworks.gdn.fidelity_v1 import GDNFidelityFreezeV1  # noqa: E402
from paperworks.gdn.upstream_candidate_backend_v1 import (  # noqa: E402
    TASK039C0_GDN_POLICY_HASH,
    TASK039C0_PAIR_UNIVERSE_HASH,
    TASK039C0_PROTOCOL_BUNDLE_HASH,
    TASK039C_GDN_STARTING_COMMIT,
    UPSTREAM_GDN_COMMIT,
    build_dependency_status_v1,
    build_fidelity_receipt_v1,
    inspect_current_dependency_environment_v1,
    inspect_python_executable_v1,
    verify_pinned_upstream_checkout_v1,
)
from paperworks.v6.candidate_discovery_protocol_v1 import (  # noqa: E402
    CandidateDiscoveryProtocolBundleV1,
)
from paperworks.v6.common import canonical_json_v1, stable_hash_v1  # noqa: E402


C0_BUNDLE = ROOT / "docs/task_reports/TASK-039C0_PROTOCOL_BUNDLE.json"
P1D_FREEZE = ROOT / "configs/v6/task039p1d_gdn_fidelity_freeze.json"
GDN_CONFIG = ROOT / "configs/v6/task039c_gdn_backend_v1.json"
UPSTREAM_ROOT = ROOT / "external/gdn"
FIDELITY_OUTPUT = ROOT / "docs/task_reports/TASK-039C_GDN_FIDELITY.json"
RESULT_OUTPUT = ROOT / "docs/task_reports/TASK-039C_GDN_RESULT.json"
ACCESS_OUTPUT = ROOT / "docs/task_reports/TASK-039C_GDN_DATA_ACCESS_AUDIT.json"
REPORT_OUTPUT = ROOT / "docs/task_reports/TASK-039C_GDN_REPORT.md"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _git(*arguments: str) -> str:
    result = subprocess.run(
        [
            "git",
            "-c",
            f"safe.directory={ROOT.resolve().as_posix()}",
            "-C",
            str(ROOT),
            *arguments,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()


def _created_at(value: str | None) -> str:
    return value or datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _validate_frozen_inputs(*, phase_a: bool) -> CandidateDiscoveryProtocolBundleV1:
    if _git("branch", "--show-current") != "task-039c-gdn":
        raise RuntimeError("blocked_task039c_gdn_base_mismatch: wrong branch")
    head = _git("rev-parse", "HEAD")
    if phase_a and head != TASK039C_GDN_STARTING_COMMIT:
        raise RuntimeError("blocked_task039c_gdn_base_mismatch: wrong Phase-A base")
    if _git("merge-base", "HEAD", TASK039C_GDN_STARTING_COMMIT) != TASK039C_GDN_STARTING_COMMIT:
        raise RuntimeError("blocked_task039c_gdn_base_mismatch: C0 is not an ancestor")
    bundle = CandidateDiscoveryProtocolBundleV1.from_dict(_load_json(C0_BUNDLE))
    if bundle.artifact_hash != TASK039C0_PROTOCOL_BUNDLE_HASH:
        raise RuntimeError("blocked_task039c_gdn_base_mismatch: protocol bundle mismatch")
    if bundle.gdn_policy.artifact_hash != TASK039C0_GDN_POLICY_HASH:
        raise RuntimeError("blocked_task039c_gdn_base_mismatch: GDN policy mismatch")
    if bundle.universe_policy.eligible_pair_universe_hash != TASK039C0_PAIR_UNIVERSE_HASH:
        raise RuntimeError("blocked_task039c_gdn_base_mismatch: universe mismatch")
    if (
        bundle.selected_process_id != "P1"
        or len(bundle.universe_policy.source_variables) != 12
        or len(bundle.universe_policy.target_variables) != 12
        or bundle.universe_policy.eligible_pair_count != 144
    ):
        raise RuntimeError("blocked_task039c_gdn_base_mismatch: P1 identity count mismatch")
    p1d = GDNFidelityFreezeV1.from_dict(_load_json(P1D_FREEZE))
    if p1d.upstream_commit != UPSTREAM_GDN_COMMIT:
        raise RuntimeError("blocked_task039c_gdn_base_mismatch: P1D upstream mismatch")
    config = _load_json(GDN_CONFIG)
    observed_config_hash = config.pop("config_hash")
    if stable_hash_v1(config) != observed_config_hash:
        raise RuntimeError("blocked_task039c_gdn_base_mismatch: GDN config self-hash mismatch")
    return bundle


def _dependency_status(environment_arguments: list[str]):
    environments = [inspect_current_dependency_environment_v1("bundled_CP3.12.13")]
    for item in environment_arguments:
        environment_id, separator, path = item.partition("=")
        if not separator:
            raise RuntimeError("--environment must use SANITIZED_ID=PATH")
        environments.append(
            inspect_python_executable_v1(
                environment_id=environment_id,
                executable=Path(path),
            )
        )
    return build_dependency_status_v1(environments)


def phase_a(args: argparse.Namespace) -> None:
    _validate_frozen_inputs(phase_a=True)
    source = verify_pinned_upstream_checkout_v1(UPSTREAM_ROOT)
    dependencies = _dependency_status(args.environment)
    receipt = build_fidelity_receipt_v1(
        source_verification=source,
        dependency_status=dependencies,
        implementation_path=ROOT / "src/paperworks/gdn/upstream_candidate_backend_v1.py",
        created_at=_created_at(args.created_at),
    )
    _write_json(FIDELITY_OUTPUT, receipt.to_dict())
    print(canonical_json_v1(receipt.to_dict()))


def _verify_fidelity_document() -> dict[str, Any]:
    receipt = _load_json(FIDELITY_OUTPUT)
    observed = receipt.pop("artifact_hash")
    if stable_hash_v1(receipt) != observed:
        raise RuntimeError("failed_gdn_fidelity: fidelity receipt self-hash mismatch")
    receipt["artifact_hash"] = observed
    return receipt


def record_blocked(args: argparse.Namespace) -> None:
    _validate_frozen_inputs(phase_a=False)
    if _git("rev-parse", "HEAD") != args.phase_a_commit:
        raise RuntimeError("blocked result must run from the exact Phase-A commit")
    receipt = _verify_fidelity_document()
    dependencies = _dependency_status(args.environment)
    if receipt["status"] != "passed_upstream_gdn_fidelity":
        status = "blocked_upstream_gdn_backend_unresolved"
        reason = "one or more mandatory upstream GDN fidelity fields remain unresolved"
    elif not dependencies.exact_backend_available:
        status = "blocked_optional_dependency"
        reason = (
            "no already-approved environment contains exact torch==2.12.1 and "
            "torch-geometric==2.8.0; no package installation, upgrade, or fallback was attempted"
        )
    else:
        raise RuntimeError("backend is available; blocked result would be invalid")
    created_at = _created_at(args.created_at)
    result = build_blocked_gdn_result_v1(
        status=status,
        phase_a_commit=args.phase_a_commit,
        fidelity_receipt_hash=receipt["artifact_hash"],
        dependency_environment_fingerprint=dependencies.environment_fingerprint,
        backend_classification=receipt["backend_classification"],
        blocking_reason=reason,
        created_at=created_at,
    )
    _write_json(RESULT_OUTPUT, result.to_dict())
    access_payload: dict[str, Any] = {
        "schema_version": "1.0.0",
        "artifact_type": "task039c_gdn_data_access_audit_v1",
        "task_id": "TASK-039C-GDN",
        "status": status,
        "access_gate": "blocked_before_real_hai_feature_access",
        "authorized_files": [
            "hai-23.05/hai-train1.csv",
            "hai-23.05/hai-train2.csv",
        ],
        "files_accessed": [],
        "real_hai_feature_values_accessed": False,
        "normal_candidate_fit_only": True,
        "br2_pair_artifacts_accessed": False,
        "meta_outputs_accessed": False,
        "stat_outputs_accessed": False,
        "train3_accessed": False,
        "train4_accessed": False,
        "test_accessed": False,
        "labels_accessed": False,
        "attacks_accessed": False,
        "p2_p3_p4_accessed": False,
        "raw_values_persisted": False,
        "checkpoint_persisted": False,
        "created_at": created_at,
    }
    access_payload["artifact_hash"] = stable_hash_v1(access_payload)
    _write_json(ACCESS_OUTPUT, access_payload)
    REPORT_OUTPUT.write_text(
        "\n".join(
            (
                "# TASK-039C-GDN Upstream-Aligned Candidate Discovery",
                "",
                f"Status: `{status}`",
                "",
                "Phase A verified the pinned upstream commit and all seven P1D-frozen Git blob and SHA-256 identities. "
                "The dedicated backend is classified `upstream_aligned_validated`; the existing deterministic and Torch/PyG project trainers remain synthetic smoke only.",
                "",
                "The arm stopped at the dependency gate. No already-approved environment contained both exact project-pinned dependencies (`torch==2.12.1`, `torch-geometric==2.8.0`). "
                "No install, upgrade, version guess, fallback backend, or HAI access occurred.",
                "",
                "No seed was attempted, no candidate was evaluated, and no top-10/20/40 or ranking was produced. "
                "BR2 pair supervision, META/STAT outputs, train3, train4, test, labels, attacks, attention-primary ranking, and post-hoc XAI were not used.",
                "",
                f"Fidelity receipt hash: `{receipt['artifact_hash']}`.",
                f"Dependency environment fingerprint: `{dependencies.environment_fingerprint}`.",
                "",
            )
        ),
        encoding="utf-8",
    )
    print(canonical_json_v1(result.to_dict()))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    phase = subparsers.add_parser("phase-a")
    phase.add_argument("--environment", action="append", default=[])
    phase.add_argument("--created-at")
    phase.set_defaults(handler=phase_a)
    blocked = subparsers.add_parser("record-blocked")
    blocked.add_argument("--phase-a-commit", required=True)
    blocked.add_argument("--environment", action="append", default=[])
    blocked.add_argument("--created-at")
    blocked.set_defaults(handler=record_blocked)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    args.handler(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
