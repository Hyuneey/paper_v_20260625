"""The single release-bound V11R2R1 entrypoint.

``REAL_PREFLIGHT_ONLY`` and ``REAL_HELDOUT_EXECUTION`` deliberately call the
same complete, read-only preflight function.  The latter calls it again before
it can atomically consume the release-scoped execution ledger.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [
    str(ROOT),
    str(ROOT / "src"),
    str(ROOT / "artifacts/validation_v2/dg04_xver_prep/metric_source/af9e7aed35cfd160cbe0d04c8ec4c102502cb677"),
    str(ROOT / "artifacts/validation_v2/dg04_xver_prep/metric_dependencies"),
]

from paperworks.validation_v2.dg05_production_chain_v11 import (  # noqa: E402
    PREACCESS_MODE,
    REAL_MODE,
    canonical_bytes,
    load_self_hashed,
    self_hashed,
)
from paperworks.validation_v2.dg05_production_chain_v11r2r1 import (  # noqa: E402
    PREACCESS_FROZEN_KERNEL_REHEARSAL,
    REAL_PREFLIGHT_ONLY,
    initialize,
    load_candidate,
    verify_runtime_approval_v11r2r1,
)
from paperworks.validation_v2.dg05_v11r1_resource_materializer import (  # noqa: E402
    build_materialization_contract_v11r1,
    materialize_runtime_plan_v11r1,
)
from paperworks.validation_v2.dg05_v11r1_route_core import execute_dg05_v11r1  # noqa: E402
from paperworks.validation_v2.dg05_v11r2_execution_ledger import (  # noqa: E402
    append_contact_guard_v11r2,
    append_terminal_state_v11r2,
    start_real_execution_v11r2,
)
from paperworks.validation_v2.dg05_v11r2r1_preflight import (  # noqa: E402
    replay_all_real_preconditions_v11r2r1,
)
from paperworks.validation_v2.dg05_v11r2r1_preflight_receipt import (  # noqa: E402
    build_real_preflight_receipt_v11r2r1,
    persist_real_preflight_receipt_v11r2r1,
    verify_real_preflight_receipt_v11r2r1,
)
from paperworks.validation_v2.dg05_v11r2_execution_ledger import ledger_scope_status_v11r2  # noqa: E402
from paperworks.validation_v2.etapr_exchange_v1 import OfficialEtaprV1  # noqa: E402


class DG05V11R2R1RunnerError(ValueError):
    """The only V11R2R1 runner rejected a release-bound input."""


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        required=True,
        choices=(PREACCESS_FROZEN_KERNEL_REHEARSAL, PREACCESS_MODE, REAL_PREFLIGHT_ONLY, REAL_MODE),
    )
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--expected-hash", required=True)
    parser.add_argument("--execution-binding", type=Path)
    parser.add_argument("--final-closure", type=Path)
    parser.add_argument("--user-approved-release-hash")
    parser.add_argument("--user-approved-final-closure-hash")
    parser.add_argument("--user-approved-execution-binding-hash")
    parser.add_argument("--preflight-receipt", type=Path)
    parser.add_argument("--execution-ledger-root", type=Path)
    parser.add_argument("--physical-custody-receipt", type=Path)
    parser.add_argument("--resource-plan", type=Path)
    parser.add_argument("--resource-root", type=Path, action="append", default=[])
    parser.add_argument("--scenario-authority", type=Path, required=True)
    parser.add_argument("--p1-authority", type=Path, required=True)
    parser.add_argument("--legacy-v10-release", type=Path, required=True)
    parser.add_argument("--predecessor-v4-manifest", type=Path, required=True)
    parser.add_argument("--predecessor-v4-closure", type=Path, required=True)
    parser.add_argument("--historical-v1-manifest", type=Path, required=True)
    parser.add_argument("--metric-contract", type=Path, required=True)
    parser.add_argument("--normal-registry", type=Path, required=True)
    parser.add_argument("--normal-closure", type=Path)
    parser.add_argument("--private-normal-manifest", type=Path, required=True)
    parser.add_argument("--expected-private-normal-hash", required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    return parser.parse_args()


def _require_real_inputs(args: argparse.Namespace) -> None:
    required = (
        args.execution_binding,
        args.final_closure,
        args.user_approved_release_hash,
        args.user_approved_final_closure_hash,
        args.user_approved_execution_binding_hash,
        args.physical_custody_receipt,
        args.execution_ledger_root,
        args.normal_closure,
    )
    if any(value is None for value in required):
        raise DG05V11R2R1RunnerError("REAL_RUNTIME_APPROVAL_AND_REPLAY_INPUTS_REQUIRED")
    if args.resource_plan is None and not args.resource_root:
        raise DG05V11R2R1RunnerError("REAL_RUNTIME_RESOURCE_INPUTS_REQUIRED")


def _load_or_materialize_plan(args: argparse.Namespace, manifest: Mapping[str, Any]) -> Mapping[str, Any]:
    """Use a private runtime plan, never a path-bearing scientific authority."""
    if args.resource_plan is not None:
        return load_self_hashed(args.resource_plan, "dg05_v11r1_protected_resource_plan_v1")
    materializer_rows = [
        row for row in manifest["implementation_authorities"]
        if row["logical_name"] == "resource_materializer"
    ]
    if len(materializer_rows) != 1:
        raise DG05V11R2R1RunnerError("RESOURCE_MATERIALIZER_BINDING_REQUIRED")
    contract = build_materialization_contract_v11r1(
        custody_receipt_path=args.physical_custody_receipt,
        implementation_hash=materializer_rows[0]["byte_hash"],
        source_commit=manifest["implementation_source_commit"],
    )
    plan, _receipt = materialize_runtime_plan_v11r1(contract=contract, authorized_roots=args.resource_root)
    return plan


class _RealLifecycle:
    """Thin runner adapter around the durable release-scoped ledger."""

    def __init__(self, *, ledger_root: Path, approval: Mapping[str, Any], preflight: Mapping[str, Any], physical_custody_hash: str, output_root: Path) -> None:
        self.ledger_root = ledger_root
        self.current = start_real_execution_v11r2(
            ledger_root=ledger_root,
            release_hash=approval["release_hash"],
            final_closure_hash=approval["final_closure_hash"],
            execution_binding_hash=approval["execution_binding_hash"],
            preflight_receipt_hash=preflight["self_hash"],
            physical_custody_hash=physical_custody_hash,
            output_namespace=str(output_root),
        )

    def commit_contact_guard(self) -> None:
        self.current = append_contact_guard_v11r2(ledger_root=self.ledger_root, start_state=self.current)

    def mark_predictions_frozen(self) -> None:
        self.current = append_terminal_state_v11r2(ledger_root=self.ledger_root, predecessor=self.current, state_name="PREDICTIONS_FROZEN")

    def mark_metrics_frozen(self) -> None:
        self.current = append_terminal_state_v11r2(ledger_root=self.ledger_root, predecessor=self.current, state_name="METRICS_FROZEN")

    def mark_terminal_complete(self) -> Mapping[str, Any]:
        self.current = append_terminal_state_v11r2(ledger_root=self.ledger_root, predecessor=self.current, state_name="TERMINAL_COMPLETE")
        return self.current

    def fail(self) -> None:
        try:
            state = "PRECONTACT_ABORTED" if self.current["state"] == "REAL_EXECUTION_STARTED" else "TERMINAL_FAILED_AFTER_SCIENTIFIC_CONTACT"
            self.current = append_terminal_state_v11r2(ledger_root=self.ledger_root, predecessor=self.current, state_name=state)
        except Exception:
            # A contact guard written before a crash remains the fail-closed
            # authorization boundary even if a terminal receipt cannot persist.
            pass


def _fresh_replay(*, args: argparse.Namespace, manifest: Mapping[str, Any], plan: Mapping[str, Any], approval: Mapping[str, Any]) -> dict[str, Any]:
    return replay_all_real_preconditions_v11r2r1(
        repository_root=ROOT,
        manifest=manifest,
        execution_binding_path=args.execution_binding,
        legacy_release_path=args.legacy_v10_release,
        predecessor_v4_path=args.predecessor_v4_manifest,
        predecessor_v4_closure_path=args.predecessor_v4_closure,
        historical_v1_manifest_path=args.historical_v1_manifest,
        custody_receipt_path=args.physical_custody_receipt,
        plan=plan,
        metric_contract_path=args.metric_contract,
        normal_registry_path=args.normal_registry,
        normal_closure_path=args.normal_closure,
        private_normal_manifest_path=args.private_normal_manifest,
        expected_private_normal_hash=args.expected_private_normal_hash,
        scenario_path=args.scenario_authority,
        p1_path=args.p1_authority,
        ledger_root=args.execution_ledger_root,
        final_closure_hash=approval["final_closure_hash"],
    )


def _run_preaccess(args: argparse.Namespace) -> None:
    """Qualification-only route; it never constructs a production preflight."""
    wrapper = OfficialEtaprV1(ROOT / "artifacts/validation_v2/dg04_xver_prep/metric_source/af9e7aed35cfd160cbe0d04c8ec4c102502cb677")
    receipt = execute_dg05_v11r1(
        repository_root=ROOT,
        work_root=args.output_root,
        manifest_path=args.manifest,
        expected_hash=args.expected_hash,
        mode=PREACCESS_MODE,
        user_approved_release_hash=None,
        legacy_release_path=args.legacy_v10_release,
        predecessor_v4_path=args.predecessor_v4_manifest,
        predecessor_v4_closure_path=args.predecessor_v4_closure,
        historical_v1_manifest_path=args.historical_v1_manifest,
        metric_contract_path=args.metric_contract,
        normal_registry_path=args.normal_registry,
        private_normal_manifest_path=args.private_normal_manifest,
        expected_private_normal_hash=args.expected_private_normal_hash,
        unified_scenario_path=args.scenario_authority,
        unified_p1_path=args.p1_authority,
        wrapper=wrapper,
        manifest_schema="dg05_executable_v11r2r1_candidate_manifest_v1",
        initialize_fn=initialize,
    )
    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "V11R2R1_SHARED_ROUTE_RECEIPT.json").write_bytes(canonical_bytes(receipt) + b"\n")
    print(json.dumps({"status": receipt["status"], "heldout_rows_parsed": 0}, sort_keys=True))


def main() -> None:
    args = _arguments()
    if args.mode in (PREACCESS_FROZEN_KERNEL_REHEARSAL, PREACCESS_MODE):
        _run_preaccess(args)
        return

    _require_real_inputs(args)
    manifest = load_candidate(manifest_path=args.manifest, expected_hash=args.expected_hash, repository_root=ROOT)
    approval = verify_runtime_approval_v11r2r1(
        manifest=manifest,
        final_closure_path=args.final_closure,
        approved_release_hash=args.user_approved_release_hash,
        approved_final_closure_hash=args.user_approved_final_closure_hash,
        approved_execution_binding_hash=args.user_approved_execution_binding_hash,
    )
    plan = _load_or_materialize_plan(args, manifest)
    fresh = _fresh_replay(args=args, manifest=manifest, plan=plan, approval=approval)

    if args.mode == REAL_PREFLIGHT_ONLY:
        if args.preflight_receipt is None or args.preflight_receipt.exists():
            raise DG05V11R2R1RunnerError("PREFLIGHT_RECEIPT_APPEND_ONLY_REQUIRED")
        ledger_status = ledger_scope_status_v11r2(
            ledger_root=args.execution_ledger_root,
            release_hash=approval["release_hash"],
            final_closure_hash=approval["final_closure_hash"],
            execution_binding_hash=approval["execution_binding_hash"],
        )
        receipt = build_real_preflight_receipt_v11r2r1(
            manifest=manifest, approval_replay=approval,
            replay_bundle=fresh, ledger_status=ledger_status,
        )
        persist_real_preflight_receipt_v11r2r1(path=args.preflight_receipt, receipt=receipt)
        print(json.dumps({"status": receipt["status"], "heldout_rows_parsed": 0}, sort_keys=True))
        return

    if args.preflight_receipt is None:
        raise DG05V11R2R1RunnerError("PREFLIGHT_RECEIPT_REQUIRED")
    ledger_status = ledger_scope_status_v11r2(
        ledger_root=args.execution_ledger_root,
        release_hash=approval["release_hash"],
        final_closure_hash=approval["final_closure_hash"],
        execution_binding_hash=approval["execution_binding_hash"],
    )
    stored = verify_real_preflight_receipt_v11r2r1(
        receipt_path=args.preflight_receipt, manifest=manifest,
        approval_replay=approval, fresh_replay_bundle=fresh,
        ledger_status=ledger_status,
    )
    lifecycle = _RealLifecycle(
        ledger_root=args.execution_ledger_root,
        approval=approval,
        preflight=stored,
        physical_custody_hash=manifest["physical_custody_hash"],
        output_root=args.output_root,
    )
    try:
        wrapper = OfficialEtaprV1(ROOT / "artifacts/validation_v2/dg04_xver_prep/metric_source/af9e7aed35cfd160cbe0d04c8ec4c102502cb677")
        receipt = execute_dg05_v11r1(
            repository_root=ROOT,
            work_root=args.output_root,
            manifest_path=args.manifest,
            expected_hash=args.expected_hash,
            mode=REAL_MODE,
            user_approved_release_hash=args.user_approved_release_hash,
            legacy_release_path=args.legacy_v10_release,
            predecessor_v4_path=args.predecessor_v4_manifest,
            predecessor_v4_closure_path=args.predecessor_v4_closure,
            historical_v1_manifest_path=args.historical_v1_manifest,
            metric_contract_path=args.metric_contract,
            normal_registry_path=args.normal_registry,
            private_normal_manifest_path=args.private_normal_manifest,
            expected_private_normal_hash=args.expected_private_normal_hash,
            unified_scenario_path=args.scenario_authority,
            unified_p1_path=args.p1_authority,
            wrapper=wrapper,
            resource_plan=plan,
            manifest_schema="dg05_executable_v11r2r1_candidate_manifest_v1",
            initialize_fn=initialize,
            lifecycle=lifecycle,
        )
    except Exception:
        lifecycle.fail()
        raise
    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "V11R2R1_SHARED_ROUTE_RECEIPT.json").write_bytes(canonical_bytes(receipt) + b"\n")
    print(json.dumps({"status": receipt["status"]}, sort_keys=True))


if __name__ == "__main__":
    main()
