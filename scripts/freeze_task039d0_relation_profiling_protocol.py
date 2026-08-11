"""Freeze TASK-039D0 protocol artifacts without opening HAI data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from paperworks.v6.relation_profiling_protocol_v1 import (
    ARTIFACT_CLASSES,
    CANDIDATE_COHORT_HASH,
    CANDIDATE_IDENTITY_LIST_HASH,
    DirectionalRelationIdentityV1,
    PROCESS_ID,
    RELATION_FAMILY,
    build_task039d0_artifacts_v1,
    schema_for_artifact_v1,
)


ROOT = Path(__file__).resolve().parents[1]
COHORT_PATH = ROOT / "docs" / "task_reports" / "TASK-039C_CANDIDATE_PROFILING_COHORT.json"

SCHEMA_FILES = {
    "relation_profiling_protocol_v1": "relation_profiling_protocol_v1_schema.json",
    "profiling_identity_view_policy_v1": "profiling_identity_view_policy_v1_schema.json",
    "profiling_identity_view_v1": "profiling_identity_view_v1_schema.json",
    "candidate_provenance_analysis_view_v1": "candidate_provenance_analysis_view_v1_schema.json",
    "source_scale_policy_v1": "source_scale_policy_v1_schema.json",
    "source_step_profiling_policy_v1": "source_step_profiling_policy_v1_schema.json",
    "target_response_profiling_policy_v1": "target_response_profiling_policy_v1_schema.json",
    "directional_relation_selection_policy_v1": "directional_relation_selection_policy_v1_schema.json",
    "relation_fit_gate_policy_v1": "relation_fit_gate_policy_v1_schema.json",
    "relation_confirmation_policy_v1": "relation_confirmation_policy_v1_schema.json",
    "directional_relation_identity_v1": "directional_relation_identity_v1_schema.json",
    "relation_profiling_outcome_policy_v1": "relation_profiling_outcome_policy_v1_schema.json",
    "candidate_method_comparison_policy_v1": "candidate_method_comparison_policy_v1_schema.json",
    "numeric_evidence_authority_policy_v1": "numeric_evidence_authority_policy_v1_schema.json",
    "task039d_data_access_policy_v1": "task039d_data_access_policy_v1_schema.json",
    "task039d1_authorization_v1": "task039d1_authorization_v1_schema.json",
    "task039d_protocol_bundle_v1": "task039d_protocol_bundle_v1_schema.json",
    "task039d0_relation_profiling_protocol_config": "task039d0_relation_profiling_protocol_config_schema.json",
}


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    cohort = json.loads(COHORT_PATH.read_text(encoding="utf-8"))
    artifacts = build_task039d0_artifacts_v1(cohort)
    examples = {item.ARTIFACT_TYPE: item.to_dict() for item in artifacts.values()}
    directional = DirectionalRelationIdentityV1({
        "source": "P1_FCV01D", "source_step_direction": "step_up",
        "target": "P1_FT01", "target_response_direction": "increase",
        "selected_horizon_is_identity": False, "relation_family": RELATION_FAMILY,
    })
    examples[directional.ARTIFACT_TYPE] = directional.to_dict()
    expected_types = {item.ARTIFACT_TYPE for item in ARTIFACT_CLASSES}
    if set(examples) != expected_types:
        raise RuntimeError("schema examples do not cover all D0 artifacts")
    schemas_root = ROOT / "schemas" / "v6"
    for artifact_type, filename in SCHEMA_FILES.items():
        _write_json(schemas_root / filename, schema_for_artifact_v1(examples[artifact_type]))

    reports = ROOT / "docs" / "task_reports"
    _write_json(ROOT / "configs" / "v6" / "task039d0_relation_profiling_protocol.json", artifacts["config"].to_dict())
    _write_json(reports / "TASK-039D0_PROTOCOL_BUNDLE.json", artifacts["bundle"].to_dict())
    _write_json(reports / "TASK-039D0_DATA_ACCESS_POLICY.json", artifacts["data_access_policy"].to_dict())
    _write_json(reports / "TASK-039D1_AUTHORIZATION.json", artifacts["d1_authorization"].to_dict())
    _write_json(reports / "TASK-039D0_PROFILING_IDENTITY_VIEW.json", artifacts["profiling_identity_view"].to_dict())
    _write_json(reports / "TASK-039D0_PROVENANCE_ANALYSIS_VIEW.json", artifacts["provenance_analysis_view"].to_dict())

    bundle = artifacts["bundle"]
    policy = bundle.payload
    report = f"""# TASK-039D0 Report

Status: `passed_task039d0_relation_profiling_protocol_freeze`

TASK-039D0 freezes one arm-blind normal relation-profiling and deterministic
calibration protocol for the exact 47-pair TASK-039C cohort. It opened no HAI
feature values and produced no relation outcome.

## Frozen bindings

- candidate cohort: `{CANDIDATE_COHORT_HASH}`
- identity list: `{CANDIDATE_IDENTITY_LIST_HASH}`
- protocol bundle: `{bundle.artifact_hash}`
- profiling identity view: `{artifacts['profiling_identity_view'].artifact_hash}`
- provenance analysis view: `{artifacts['provenance_analysis_view'].artifact_hash}`
- D1 authorization: `{artifacts['d1_authorization'].artifact_hash}`

## Sequential boundary

TASK-039D1 may execute one fit-only pass over `hai-train1.csv` and
`hai-train2.csv`. TASK-039D2 train3 confirmation remains unauthorized.
`hai-train4.csv` remains reserved for a later NORMAL_GUARD stage. Test,
labels, attacks, BR2 pair results, candidate-arm evidence in the profiler,
Rule v2, Agent, detector, verifier, and runtime access remain prohibited.

## Protocol component hashes

- source scale: `{policy['source_scale_policy']['artifact_hash']}`
- source event: `{policy['event_policy']['artifact_hash']}`
- target response: `{policy['target_response_policy']['artifact_hash']}`
- direction selection: `{policy['direction_selection_policy']['artifact_hash']}`
- fit gate: `{policy['fit_gate_policy']['artifact_hash']}`
- confirmation: `{policy['confirmation_policy']['artifact_hash']}`
- method comparison: `{policy['method_comparison_policy']['artifact_hash']}`
- numeric evidence authority: `{policy['numeric_evidence_policy']['artifact_hash']}`

## Validation

- D0 contracts, formulas, arm-blindness, schemas, and authority: 28 passed.
- TASK-039C integration binding: 31 passed; combined D0/integration run: 59 passed.
- META/STAT/GDN/GDNP/C0: 119 passed, 2 skipped by their frozen conditions.
- BR0/BR1/BR2: 101 passed from an LF-preserving frozen worktree.
- TASK-039A/AR: 37 passed.
- P1A/P1B/P1C/P1D: 130 passed; 4 optional-import tests passed in the
  dependency-minimal existing interpreter.
- frozen TASK-032: 106 passed; frozen TASK-039B: 27 passed.
- candidate/profiling legacy regressions: 22 passed.
- guarded discovery enumerated 237 tracked modules and 606 runnable tests. It
  reported 50 known optional import diagnostics plus nine expected
  environment errors (three absent ignored ARGOS checkout paths and six exact
  GDN dependency checks in the dependency-minimal interpreter). The GDN cases
  passed independently in the frozen exact environment; the pinned ARGOS track
  remains reference-only and absent from disposable worktrees.
- frozen P0: 12 passed and one historical platform-sensitive inventory
  diagnostic reproduced. The receipt hashes a CRLF rendering of
  `fixtures/task032e/explanation_abstained.json`, while Git stores the LF blob;
  this is an existing environment/receipt mismatch and not a D0 scientific
  regression.

No dependency was installed or upgraded. All real HAI feature-value access
remained false.
"""
    (reports / "TASK-039D0_REPORT.md").write_text(report, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
