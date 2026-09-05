"""Freeze public-safe multi-panel authorities without attack or label reads."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research_control_center/validation_v2/multipanel_pre_dg05"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def sha_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def write_json(name: str, body: dict) -> str:
    payload = dict(body)
    payload["self_hash"] = sha256(canonical(payload)).hexdigest()
    path = OUT / name
    path.write_bytes(canonical(payload) + b"\n")
    return payload["self_hash"]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    base = "3e8799155ede1e4e6b7b835e8e8866c4e21b6d16"
    fusion = "587868f42fbdaedbd802541763e0390c09d2f04e4ba5944c45ad7e6e6593cbcc"
    portfolios = {
        "HAI23": {"T0": "d95c0bb8234304f2b769e088f4399b6c071b2156982c9e1fadd175dbab5dba02", "T2": "bc2b5996989228f198dbcbf38cbedaf38516366f55d5011978ecda94ccf699b6", "V2A": "ec0b3e2a32d457287cb8b101bec39059e99335be3fd85a3d1fb98668224c52aa"},
        "HAI22": {"T0": "94f130408361e6b4a8051ed4a72a0ad385e90cb3212e2bf0d27af300f481503f", "T2": "b58313cd142256d000f89fd4a40512763b35e6b50752229109646bafc243fb5c"},
        "HAI21": {"T0": "f9cad3c00c422614012b2147f3c21951632f8738ce2d8f9f1108d61ae69d6ef3", "T2": "9815c9a66debed593e21364377113d18422a840389d306a4a7648d5f035599dc"},
    }
    exp04 = json.loads((ROOT / "research_control_center/validation_v2/gdn_front_exp04_001/contracts/EXP04_EXECUTION_FREEZE_V1.json").read_text(encoding="utf-8"))
    canonical_pca = json.loads((OUT / "PCA_SPE_CANONICAL_AUTHORITY_V1.json").read_text(encoding="utf-8"))
    hai23_private = json.loads((OUT / "HAI23_DETECTOR_PRIVATE_HASH_BINDING_V1.json").read_text(encoding="utf-8"))
    external = {v: json.loads((OUT / f"{v}_DETECTOR_AUTHORITY_V1.json").read_text(encoding="utf-8")) for v in ("HAI22", "HAI21")}
    hai23_hash = write_json("HAI23_DETECTOR_REPLAY_AUTHORITY_V1.json", {
        "schema": "hai23_detector_replay_authority_v1", "source_commit": base,
        "status": "IMMUTABLE_REPLAY_NOT_REFIT", "feature_count": 37,
        "feature_order": "FROZEN_P1_FEATURE_ORDER_37", "fit_splits": ["train1", "train2"], "calibration_split": "train3",
        "pca_method_id": "V2_D0_PCA_SPE_NORMAL_ONLY_V1", "pca_method_config_hash": "6e953ba3872fe7b5ad70600e90ef4ae7e7deb5dd99204f4f665a916fdc9d5180",
        "pca_preregistration_hash": "9e52cf7755c6fc4fff5388839cf2d0e14577e6237ed78bffb029be8d29f1474b",
        "if_method_id": "V2_ISOLATION_FOREST_FIXED_NORMAL_ONLY_V1", "if_method_config_hash": "ad497f6e816544439e301ba5b4f093a22f1a8837854def6c15d1cf4ab8cef59b",
        "if_preregistration_hash": "b5c1db05262dd94908108bc570ae01a305df47ce1ebccd0116d6e92b1631bacc",
        "canonical_pca_authority_hash": canonical_pca["self_hash"], "exp04_execution_freeze_hash": exp04["self_hash"],
        "private_hash_binding": hai23_private["self_hash"],
        "private_model_bytes": "EXACT_HASH_BOUND_LOCAL_ONLY",
        "private_model_bytes_hash": hai23_private["private_model_bytes_hash"],
        "pca_fit_authority_hash": hai23_private["pca_fit_authority_hash"],
        "pca_threshold_authority_hash": hai23_private["pca_threshold_authority_hash"],
        "if_fit_authority_hash": hai23_private["if_fit_authority_hash"],
        "if_threshold_authority_hash": hai23_private["if_threshold_authority_hash"],
        "attack_accesses": 0, "labels_accessed": 0,
    })
    bundle_hash = write_json("MULTIPANEL_METHOD_BUNDLE_AUTHORITY_V1.json", {
        "schema": "multipanel_method_bundle_authority_v1", "source_commit": base, "status": "PRE_DG05_FROZEN",
        "operational_order": ["HAI23_TEST2_PRIMARY_HELDOUT_V1", "HAI22_EXTERNAL_REPLICATION_V1", "HAI21_EXTERNAL_REPLICATION_V1"],
        "primary_methods": ["M0_PCA_SPE", "M1_T0_RULE_ONLY", "M2_T2_RULE_ONLY", "M3_PCA_PLUS_T0", "M4_PCA_PLUS_T2"],
        "secondary": {"HAI23": ["ISOLATION_FOREST", "ISOLATION_FOREST_PLUS_T2", "V2A_RULE_ONLY_REFERENCE", "HISTORICAL_PCA_PLUS_V2A_CONTINUITY"],
                      "HAI22": ["ISOLATION_FOREST", "ISOLATION_FOREST_PLUS_T2"], "HAI21": ["ISOLATION_FOREST", "ISOLATION_FOREST_PLUS_T2"]},
        "portfolio_hashes": portfolios, "detector_authorities": {"HAI23": hai23_hash, "HAI22": external["HAI22"]["self_hash"], "HAI21": external["HAI21"]["self_hash"]},
        "fusion_policy_hash": fusion, "fusion_semantics": "BASE_OR_SAME_FILE_ROW_FAIL_WITH_AT_LEAST_TWO_DISTINCT_PHYSICAL_SOURCES",
        "no_point_adjustment": True, "post_result_method_change_allowed": False, "attack_accesses": 0,
    })
    fusion_replay_hash = write_json("FUSION_AUTHORITY_REPLAY_V1.json", {
        "schema":"multipanel_fusion_authority_replay_v1", "authority_hash":fusion,
        "same_physical_file":True, "same_physical_timestamp_second":True, "rule_outcome":"FAIL_ONLY",
        "minimum_distinct_physical_sources":2, "base_alarm":"PRESERVED_POINTWISE_OR",
        "applies_to":["PCA_PLUS_T0","PCA_PLUS_T2"], "new_fusion_created":False,
        "implementation_hash":sha_file(ROOT/"src/paperworks/validation_v2/exp04_protocol_v1.py"), "attack_accesses":0,
    })
    burden_hash = write_json("NORMAL_FALSE_BURDEN_AUTHORITY_V1.json", {
        "schema":"normal_false_burden_authority_v1", "HAI23":{"class":"GUARD_CONDITIONED_NORMAL"},
        "HAI22":{"class":"POST_FREEZE_NORMAL_AUDIT","components":["train5","train6"],"combined":"EXPOSURE_WEIGHTED_RATIO_OF_SUMS"},
        "HAI21":{"class":"GUARD_CONDITIONED_NORMAL","component":"train3_Block_B_[239430,478801)"},
        "file_local_episodes":True,"cross_version_pooling":"PROHIBITED","equal_independence_claim":False,
    })
    metric_hash = write_json("MULTIPANEL_METRIC_AUTHORITY_V1.json", {
        "schema": "multipanel_metric_authority_v1", "status": "FROZEN_BEFORE_DG05", "source_commit": base,
        "primary_unit": "OFFICIAL_ATTACK_SCENARIO", "primary_scope": "P1_ELIGIBLE_ONLY", "primary_metric": "SCENARIO_RECALL_MICRO_WITHIN_VERSION",
        "wilson": "TWO_SIDED_95_PERCENT", "delay": "FIRST_IN_INTERVAL_ALARM_MINUS_OFFICIAL_START_FILE_LOCAL", "miss_delay": "NOT_DETECTED",
        "false_burden": "FILE_LOCAL_EPISODES_RATIO_OF_SUMS_WITHIN_AUTHORITY", "cross_version_false_burden_pooling": "PROHIBITED",
        "etapr": {"source_commit": "af9e7aed35cfd160cbe0d04c8ec4c102502cb677", "theta_p": 0.5, "theta_r": 0.1, "delta": 0.0,
                  "binding": "FILE_NAMESPACED_DISJOINT_RANGE_UNION", "separator_safe_test_set": [1, 7, 101, 1024],
                  "target_scope": "P1_ELIGIBLE_OFFICIAL_SCENARIO_RANGES_WITH_ALL_FILE_LOCAL_PREDICTION_RANGES", "existing_conformance": "109_OF_109_PASS"},
        "empty": {"scenario_gt_positive_prediction_empty": 0.0, "scenario_gt_empty": "NOT_EVALUABLE", "normal_positive_exposure_no_alarm": 0.0,
                  "normal_zero_exposure": "INVALID_AUTHORITY", "etapr_gt_positive_prediction_empty": [0.0, 0.0, 0.0], "etapr_gt_empty": "NOT_APPLICABLE"},
        "contrasts": [["M2", "M1"], ["M4", "M0"], ["M3", "M0"], ["M4", "M3"]],
        "mcnemar": "EXACT_TWO_SIDED_BINOMIAL_WITHIN_VERSION_ONLY", "primary_cross_version_pooling": "PROHIBITED", "point_adjustment": "NONE",
        "implementation_hashes": {name: sha_file(ROOT / name) for name in ["src/paperworks/validation_v2/multipanel_metrics_v1.py", "src/paperworks/validation_v2/multipanel_etapr_v2.py", "src/paperworks/validation_v2/etapr_exchange_v1.py"]},
        "attack_accesses": 0, "label_accesses": 0,
    })
    etapr_conformance_hash = write_json("ETAPR_MULTIFILE_CONFORMANCE_V1.json", {
        "schema":"etapr_multifile_conformance_v1","status":"PASS","official_source_commit":"af9e7aed35cfd160cbe0d04c8ec4c102502cb677",
        "prior_cases":"109_OF_109_PASS_UNCHANGED","new_tests":{"file_order_invariance":True,"separator_invariance":True,
        "separators":[1,7,101,1024],"no_cross_file_merge":True,"independent_block_diagonal_oracle_equality":True,
        "empty_gt_guard":True,"empty_prediction_guard":True},"parameters":{"theta_p":0.5,"theta_r":0.1,"delta":0.0},
        "test_source_hash":sha_file(ROOT/"tests/test_multipanel_etapr_official_v2.py"),"attack_accesses":0,"labels_accessed":0,
    })
    statistics_hash = write_json("STATISTICAL_ANALYSIS_CONTRACT_V1.json", {
        "schema":"multipanel_statistical_analysis_contract_v1","primary_unit":"OFFICIAL_P1_ELIGIBLE_SCENARIO",
        "within_version_recall":"MICRO_EXACT_NUMERATOR_DENOMINATOR","uncertainty":"WILSON_95_PERCENT",
        "paired_contrasts":{"C1":["M2","M1"],"C2":["M4","M0"],"C3":["M3","M0"],"C4":["M4","M3"]},
        "paired_table":["both_hit","A_only","B_only","neither"],"mcnemar":"EXACT_TWO_SIDED_BINOMIAL_WHEN_ALIGNED",
        "pooled_cross_version_recall":"PROHIBITED","pooled_cross_version_mcnemar":"PROHIBITED","iid_146_claim":False,
        "descriptive_synthesis":["direction","heterogeneity","portfolio_size","hit_miss_patterns","confidence_intervals","version_specific_burden"],
    })
    p1_hash = write_json("P1_ELIGIBILITY_CUSTODIAN_AUTHORITY_V1.json", {
        "schema": "p1_eligibility_custodian_authority_v1", "status": "DESIGN_ONLY_FROZEN_BEFORE_DG05", "source_commit": base,
        "input": ["dataset_version", "file_id", "official_scenario_id", "official_attacked_identities", "official_explicit_affected_processes", "frozen_mapping_authority_hash"],
        "output": ["P1_ELIGIBLE", "CROSS_PROCESS_P1_RELEVANT", "OUT_OF_SCOPE", "UNRESOLVED"],
        "precedence": ["ANY_DIRECT_P1_IS_P1_ELIGIBLE", "ANY_UNRESOLVED_WITHOUT_DIRECT_P1_IS_UNRESOLVED", "EXPLICIT_OFFICIAL_P1_EFFECT_IS_CROSS_PROCESS", "OTHERWISE_OUT_OF_SCOPE"],
        "primary_denominator": ["P1_ELIGIBLE"], "cross_process": "SECONDARY_DESCRIPTIVE_ONLY", "method_prediction_input": False,
        "implementation_hash": sha_file(ROOT / "src/paperworks/validation_v2/p1_eligibility_custodian_v1.py"), "real_eligibility_generated": False,
    })
    custody_hash = write_json("GLOBAL_PREDICTION_CUSTODY_AUTHORITY_V1.json", {
        "schema": "global_prediction_custody_authority_v1", "status": "DESIGN_ONLY_FROZEN_BEFORE_DG05", "source_commit": base,
        "states": ["ATTACK_CONTAINER_CUSTODIED_LABEL_LOCKED", "ATTACK_FEATURE_PROJECTION_READY_LABEL_LOCKED", "PREDICTIONS_IN_PROGRESS_LABEL_LOCKED", "GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED", "LABEL_SCENARIO_LEASE_OPEN", "RESULTS_COMPUTED"],
        "transition_policy": "ADJACENT_ONLY_NO_SKIP", "prediction_order": ["HAI23", "HAI22", "HAI21"], "labels_between_panels": False,
        "expected_cell_dimensions": ["version", "physical_attack_file", "primary_or_secondary_method"],
        "terminal_cell_statuses": ["SUCCESS", "METHOD_FAILURE"], "method_failure_is_not": ["NO_ALARM", "NO_RULE", "MISS"],
        "lease_precondition": "EXACT_GLOBAL_CELL_CENSUS_AND_GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED", "lease_count": 1,
        "post_label_prediction_mutation": "PROHIBITED", "attack_projection": "TIMESTAMP_PLUS_FROZEN_FEATURE_POSITIVE_ALLOWLIST",
        "implementation_hash": sha_file(ROOT / "src/paperworks/validation_v2/multipanel_custody_v1.py"), "attack_accesses": 0, "label_accesses": 0,
    })
    prereg_hash = write_json("MULTIPANEL_PREREGISTRATION_V1.json", {
        "schema": "multipanel_preregistration_v1", "status": "PRE_DG05_FROZEN", "source_commit": base,
        "panels": [{"panel_id":"HAI23_TEST2_PRIMARY_HELDOUT_V1","nominal_scenarios":38}, {"panel_id":"HAI22_EXTERNAL_REPLICATION_V1","nominal_scenarios":58}, {"panel_id":"HAI21_EXTERNAL_REPLICATION_V1","nominal_scenarios":50}],
        "method_bundle_authority_hash": bundle_hash, "metric_authority_hash": metric_hash, "eligibility_authority_hash": p1_hash, "custody_authority_hash": custody_hash,
        "fusion_replay_hash":fusion_replay_hash,"normal_burden_authority_hash":burden_hash,"etapr_conformance_hash":etapr_conformance_hash,"statistical_analysis_hash":statistics_hash,
        "dg05_status": "USER_DECISION_REQUIRED", "phase_a": "FEATURE_ONLY_AND_ALL_PANEL_PREDICTION", "phase_b": "CONDITIONAL_ONE_SHOT_LABEL_SCENARIO_LEASE_AFTER_GLOBAL_FREEZE",
        "no_primary_pooled_recall": True, "post_result_tuning": False, "attack_accesses": 0,
    })
    brief = f"""# DG-05 — Multi-Panel Attack Feature + Conditional Label/Scenario Access\n\nStatus: `USER_DECISION_REQUIRED`\n\nNo attack/test payload, label value, scenario interval, scenario target, or real eligibility was accessed while preparing this gate.\n\n## Scope\n\nOne conditional approval covers exactly HAI23 test2 (38 nominal scenarios), HAI22 (58), and HAI21 (50). Phase A permits positive-allowlist feature projection and all frozen-method predictions in the fixed HAI23 → HAI22 → HAI21 operational order. Phase B is technically gated and becomes usable only after the exact global cell census and `GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED` receipt validate.\n\n## Frozen authorities\n\n- method bundle: `{bundle_hash}`\n- metric authority: `{metric_hash}`\n- P1 custodian: `{p1_hash}`\n- global custody: `{custody_hash}`\n- preregistration: `{prereg_hash}`\n- Fusion: `{fusion}`\n- HAI23 detector replay: `{hai23_hash}`\n- HAI23 detector private hash binding: `{hai23_private['self_hash']}`\n- HAI23 PCA fit/threshold: `{hai23_private['pca_fit_authority_hash']}` / `{hai23_private['pca_threshold_authority_hash']}`\n- HAI23 IF fit/threshold: `{hai23_private['if_fit_authority_hash']}` / `{hai23_private['if_threshold_authority_hash']}`\n- HAI22 detector: `{external['HAI22']['self_hash']}`\n- HAI21 detector: `{external['HAI21']['self_hash']}`\n\n## Non-negotiable execution\n\nAll primary and secondary prediction cells must terminate as `SUCCESS` or explicit `METHOD_FAILURE`; failure is never coerced to no alarm, no rule, or miss. No label/scenario value may be read between panels. After lease opening, predictions, models, portfolios, thresholds, Fusion, and eligibility logic are immutable. Independent QA recomputes denominators, hits/misses, Wilson intervals, delays, false burden, eTaPR, paired tables, overlap, and incremental metrics from frozen authorities only.\n\nNo provider call, GDN training, method redesign, point adjustment, cross-version IID pooling, or professor submission is authorized.\n"""
    (OUT / "DG05_MULTI_PANEL_ATTACK_ACCESS_BRIEF_V1.md").write_text(brief, encoding="utf-8", newline="\n")
    (OUT / "RESULT_INTEGRITY_QA_PLAN_V1.md").write_text("""# Independent post-label result-integrity QA\n\nA read-only QA runner will independently recompute the P1 denominator, scenario hits/misses, Wilson 95% intervals, file-local false burden, namespaced-union eTaPR, paired tables, exact McNemar, detection delays, overlap, incremental Recall, and incremental FAR from the frozen prediction/label authorities. It cannot call a provider, mutate predictions, refit detectors, revise Rules, retrain GDN, or change eligibility. Any corrupt post-freeze prediction is an integrity blocker, not a rerun authorization.\n""", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
