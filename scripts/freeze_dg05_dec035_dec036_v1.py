"""Write the two explicitly user-approved, prospective decision records."""
from __future__ import annotations

import argparse
from pathlib import Path

from paperworks.validation_v2.dg05_hai_official_scenario_v1 import canonical_bytes, self_hashed


def write(path: Path, value: dict) -> None:
    path.write_bytes(canonical_bytes(self_hashed(value)) + b"\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    frozen = {"heldout_feature_values_used_for_method_design": 0, "heldout_predictions_observed": 0, "heldout_metrics_observed": 0, "method_comparisons_observed": 0, "result_driven_changes": 0}
    write(args.output / "DEC035_HAI21_OFFICIAL_SCENARIO_BOUNDARY_SOURCE_ROLE_AMENDMENT_V1.json", {
        "schema": "dg05_scientific_decision_v1", "decision_id": "DEC-035", "status": "APPROVED_AND_FROZEN", "approved_at": "2026-09-07 Asia/Seoul",
        "title": "HAI21 Official Scenario Boundary Source-Role Amendment", "classification": "VERSION_SPECIFIC_OFFICIAL_SOURCE_ROLE_RESOLUTION_BEFORE_OUTCOME_OBSERVATION",
        "roles": {"technical_manual": "SCENARIO_IDENTITY_AND_DIRECT_TARGET_AUTHORITY", "overall_attack_label": "EXACT_PHYSICAL_INTERVAL_AUTHORITY", "README": "PANEL_CENSUS_AUTHORITY", "manual_start_and_duration": "CORROBORATIVE_OCCURRENCE_METADATA_NOT_INTERVAL_OVERRIDE"},
        "residual_rule": {"A209": "UNIQUE_RESIDUAL_OFFICIAL_SOURCE_BIJECTION", "A512": "UNIQUE_RESIDUAL_OFFICIAL_SOURCE_BIJECTION"},
        "rationale": {"manual_and_labels_total_occurrences": 50, "file_census": [5,20,8,5,12], "compatible_occurrences": 48, "boundary_incompatible_occurrences": ["A209", "A512"]},
        "does_not_change": ["scenario_count", "manual_ids", "Target Point(s)", "Target Controller", "AP/scenario metadata", "DEC-031", "metric formulas", "detectors", "Rules", "thresholds"], "performance_contact": frozen,
    })
    write(args.output / "DEC036_HAI22_PROSPECTIVE_DIRECT_TARGET_PROCESS_SCOPE_AMENDMENT_V1.json", {
        "schema": "dg05_scientific_decision_v1", "decision_id": "DEC-036", "status": "APPROVED_AND_FROZEN", "approved_at": "2026-09-07 Asia/Seoul",
        "title": "HAI22 Prospective Direct-Target Process Scope Amendment", "semantic": "ANY_VERIFIED_P1_DIRECT_TARGET", "dataset_version": "22.04",
        "source_restriction": "HAI22_VERSION_BOUND_OFFICIAL_SOURCES_ONLY_NO_HAI23_MAPPING_OR_ALIAS_REUSE", "historical_predecessor": {"authority_id":"FULL_PROCESS_SCOPE_AUTHORITY_V1", "authority_sha256":"0e4fb08ca07cf713df2e5021d9e2fe1721ec99a308cf7656ac63894b40ffe619"},
        "existing_evidence": {"scenario_authority_sha256":"34c53aef62a248a4d384083f187e47a4854df045d762533a4b8939fe54c707fb", "scenario_receipt_sha256":"b8d5bafc7f0dcdd0ebfffa2f203943fcbd0b1aa3f4b9dcf5b2a0d8c9b8b4fc6d", "replay_sha256":"a4676d7f51946e0855a146245ba964e3bedca851bdfeb4a81b099943ff8bafeb", "decision_brief_sha256":"58fb41f513971cb2d965f97be2ef4198868c687c4db1776afcabe6b19a92560d"},
        "does_not_change": ["HAI23 scope", "DEC-034", "historical V1 bytes", "detectors", "Rules", "thresholds", "P1 aggregation semantics"], "performance_contact": frozen,
    })


if __name__ == "__main__":
    main()
