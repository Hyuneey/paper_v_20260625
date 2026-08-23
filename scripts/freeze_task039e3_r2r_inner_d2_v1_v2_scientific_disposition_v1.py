"""Freeze the public-metadata-only D2 V1/V2 scientific disposition."""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping, NoReturn


ROOT = Path(__file__).resolve().parents[1]
REPORT_ROOT = ROOT / "docs/task_reports"
TASK_ID = "TASK-039E3-R2R-UTILITY-INNER-D2-V1-V2-SCIENTIFIC-DISPOSITION-V1"
STATUS = "passed_task039e3_r2r_utility_inner_d2_v1_v2_scientific_disposition_v1"
BRANCH = "task-039e3-r2r-utility-inner-d2-v1-v2-scientific-disposition-v1"
BASE = "9287d5f63dc8df2811c53429b1f141634dd971bc"
NEXT_TASK = "TASK-039E3-R2R-UTILITY-OUTER-D0-D1-D2V1-PREREGISTRATION-AND-AUTHORIZATION-V1"
V1_ID = "D2_D0_PLUS_VERIFIED_RULE_CORROBORATION_V1"
V2_ID = "D2_V2_D0_PLUS_NATIVE_HORIZON_MULTI_SOURCE_CORROBORATION_V1"
V2_DISPOSITION = "RETAIN_AS_DEVELOPMENTAL_NEGATIVE_ABLATION"
OUTER_DISPOSITION = "PREREGISTER_D0_D1_D2V1_THREE_ARM_CONFIRMATORY_EVALUATION"
OUTER_ARMS = ("D0_DETECTOR_ONLY", "D1_RULE_ONLY", "D2_V1_COMBINED")
SCHEME = "MARKDOWN_BODY_SHA256_BEFORE_INTEGRITY_FOOTER_V1"

ARM_PATH = REPORT_ROOT / "TASK-039E3_R2R_UTILITY_INNER_D0_D1_D2_COMPARISON_V1_ARM_METRICS.json"
OVERLAP_PATH = REPORT_ROOT / "TASK-039E3_R2R_UTILITY_INNER_D0_D1_D2_COMPARISON_V1_EVENT_OVERLAP.json"
RECOVERY_PATH = REPORT_ROOT / "TASK-039E3_R2R_UTILITY_INNER_D0_D1_D2_COMPARISON_V1_RECOVERY_ANALYSIS.json"
V1_PATH = REPORT_ROOT / "TASK-039E3_R2R_UTILITY_INNER_D2_RESULT_INTEGRITY_V1_METRIC_ORACLE.json"
DIAGNOSTIC_PATH = REPORT_ROOT / "TASK-039E3_R2R_UTILITY_INNER_D2_RECOVERY_SIGNAL_FAILURE_DIAGNOSTIC_V1_GATE_FAILURE.json"
V2_PATH = REPORT_ROOT / "TASK-039E3_R2R_UTILITY_INNER_D2_V2_RESULT_INTEGRITY_COMPLETION_V1.json"
AUTHORITIES = {
    ARM_PATH: "4704d3a526eab806ece1c511094fc2d2798ff63bac537273d35811ce4e9bbb81",
    OVERLAP_PATH: "51589bbf1bd90b2f04504595af465eb7e514061ef21d16ad731e02508072f1b3",
    RECOVERY_PATH: "32f008bfbcc0d1eea3efa3f27d6684823f6a02c1eab7b38333544198adc6892a",
    V1_PATH: "d933d62b4a067e0f71f6dac22b11b32ff1811857b047fde9e4d1f7e947116483",
    DIAGNOSTIC_PATH: "b006b4c79262906087b7a5c52160b9a09926318776339940018d56b3077ef96a",
    V2_PATH: "b7034829527d7469459298735d253693b41f20bde6f0ab867bac71e804fa7d06",
}

PREFIX = "TASK-039E3_R2R_UTILITY_INNER_D2_V1_V2_DISPOSITION_V1_"
FILES = {
    "PRIMARY_COMPARISON": PREFIX + "PRIMARY_COMPARISON.json",
    "RULE_SIGNAL": PREFIX + "RULE_SIGNAL.json",
    "FUSION_FINDING": PREFIX + "FUSION_FINDING.json",
    "V1_V2_COMPARISON": PREFIX + "V1_V2_COMPARISON.json",
    "THESIS_CLAIMS": PREFIX + "THESIS_CLAIMS.json",
    "OUTER_CANDIDATE": PREFIX + "OUTER_CANDIDATE.json",
    "INDEPENDENT_AUDIT": PREFIX + "INDEPENDENT_AUDIT.json",
    "READINESS": PREFIX + "READINESS.json",
    "BUNDLE": PREFIX + "BUNDLE.json",
    "RECEIPT": PREFIX + "RECEIPT.json",
    "REPORT": PREFIX + "REPORT.md",
}


class DispositionError(RuntimeError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def fail(code: str) -> NoReturn:
    raise DispositionError(code)


def stable_hash(value: Mapping[str, Any]) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
        ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def seal(value: Mapping[str, Any]) -> dict[str, Any]:
    if "artifact_hash" in value or any(k.endswith("artifact_hash") for k in value):
        fail("D2_DISPOSITION_HASH_FIELD_COLLISION")
    result = dict(value)
    result["artifact_hash"] = stable_hash(result)
    return result


def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            fail("D2_DISPOSITION_DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def strict_json(raw: bytes) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=strict_object)
    except (UnicodeDecodeError, json.JSONDecodeError):
        fail("D2_DISPOSITION_JSON_REJECTED")
    if not isinstance(value, dict):
        fail("D2_DISPOSITION_JSON_REJECTED")
    return value


def validate_self_hash(document: Mapping[str, Any], expected: str) -> None:
    core = {k: v for k, v in document.items() if k != "artifact_hash"}
    if document.get("artifact_hash") != expected or stable_hash(core) != expected:
        fail("D2_DISPOSITION_AUTHORITY_HASH_REJECTED")


@dataclass(frozen=True)
class ArmResult:
    arm_id: str
    recall: float
    normal_far_per_hour: float
    detected_attack_events: int
    normal_false_alarm_episodes: int
    d0_misses_recovered: int | None
    d0_miss_count: int | None
    incremental_recall_vs_d0: float | None
    incremental_normal_far_vs_d0: float | None
    role: str


@dataclass(frozen=True)
class FrozenEvidence:
    d0: ArmResult
    d1: ArmResult
    d2_v1: ArmResult
    d2_v2: ArmResult
    attack_event_count: int
    d0_misses_detected_by_d1: int
    d0_d1_union_coverage: int
    v1_rule_recovery_false_alarm_episodes: int
    v2_native_horizon_corroboration_points: int
    v2_rule_recovery_points: int


@dataclass(frozen=True)
class Disposition:
    v2_v1_far_ratio: float
    v1_pareto_dominates_v2: bool
    rule_complementary_signal_supported: bool
    rule_only_operational_utility_supported: bool
    combined_incremental_utility_supported: bool
    d2_v2_fixed_v1_failure: bool
    further_inner_fusion_redesign_recommended: bool
    inner_fusion_development_closed: bool
    d2_v2_disposition: str
    final_combined_candidate: str
    combined_improvement_claim_supported: bool
    thesis_fatal_blocker: bool
    thesis_claim_adjustment_required: bool
    proposed_outer_arm_count: int
    proposed_outer_arms: tuple[str, ...]
    outer_disposition: str
    outer_authorized: bool


EXPECTED = FrozenEvidence(
    d0=ArmResult("D0_PCA_SPE_V1", 0.7857142857142857, 0.4939336325682589,
        11, 7, None, None, None, None, "REFERENCE_DETECTOR_BASELINE"),
    d1=ArmResult("COMMON_42_VERIFIED_RULE_ONLY", 0.9285714285714286,
        40.50255787059723, 13, 574, 3, 3, None, None,
        "HIGH_SENSITIVITY_HIGH_FALSE_ALARM_COMPLEMENTARY_RULE_SIGNAL"),
    d2_v1=ArmResult(V1_ID, 0.7857142857142857, 0.7056194750975128,
        11, 10, 0, 3, 0.0, 0.21168584252925388,
        "COMBINED_V1_NO_INCREMENTAL_UTILITY"),
    d2_v2=ArmResult(V2_ID, 0.7857142857142857, 6.915070855955625,
        11, 98, 0, 3, 0.0, 6.421137223387365,
        "COMBINED_V2_NO_INCREMENTAL_UTILITY_HIGHER_FALSE_ALARM_COST"),
    attack_event_count=14, d0_misses_detected_by_d1=3,
    d0_d1_union_coverage=14, v1_rule_recovery_false_alarm_episodes=3,
    v2_native_horizon_corroboration_points=1335, v2_rule_recovery_points=1272,
)


SUPPORTED_CLAIMS = (
    "RULE_CONSTRUCTION_PRODUCES_EXECUTABLE_VERIFIED_RULES",
    "RULE_LAYER_DETECTS_ATTACK_EVENTS",
    "RULE_LAYER_HAS_DETECTOR_COMPLEMENTARY_EVENT_INFORMATION",
    "D0_D1_EVENT_LEVEL_COMPLEMENTARITY_EXISTS_ON_INNER",
    "RULE_ONLY_HAS_HIGH_FALSE_ALARM_BURDEN",
    "D2_V1_DOES_NOT_IMPROVE_D0_ON_INNER",
    "D2_V2_DOES_NOT_IMPROVE_D0_ON_INNER",
    "NATIVE_HORIZON_MEMORY_DOES_NOT_SOLVE_FUSION_UTILITY_ON_INNER",
    "NEGATIVE_FUSION_RESULTS_ARE_REPRODUCIBLE_AND_INTEGRITY_AUDITED",
)
UNSUPPORTED_CLAIMS = (
    "COMBINED_METHOD_IMPROVES_ATTACK_RECALL",
    "COMBINED_METHOD_REDUCES_FALSE_ALARMS",
    "RULE_ONLY_IS_OPERATIONALLY_DEPLOYABLE_AS_IS",
    "NATIVE_HORIZON_FUSION_IS_SUPERIOR",
    "D2_V1_IS_SUPERIOR_TO_D0",
    "D2_V2_IS_SUPERIOR_TO_D0",
    "CAUSAL_ROOT_CAUSE_IDENTIFICATION",
    "GENERALIZATION_TO_OUTER",
)


def derive_disposition(evidence: FrozenEvidence) -> Disposition:
    if evidence != EXPECTED:
        fail("D2_DISPOSITION_FROZEN_EVIDENCE_MISMATCH")
    ratio = evidence.d2_v2.normal_far_per_hour / evidence.d2_v1.normal_far_per_hour
    pareto = (evidence.d2_v1.recall >= evidence.d2_v2.recall and
              evidence.d2_v1.normal_far_per_hour < evidence.d2_v2.normal_far_per_hour)
    return Disposition(
        ratio, pareto, True, False, False, False, False, True,
        V2_DISPOSITION, V1_ID, False, False, True, 3, OUTER_ARMS,
        OUTER_DISPOSITION, False,
    )


def validate_authorities(documents: Mapping[Path, Mapping[str, Any]]) -> FrozenEvidence:
    if set(documents) != set(AUTHORITIES):
        fail("D2_DISPOSITION_AUTHORITY_SET_REJECTED")
    for path, expected_hash in AUTHORITIES.items():
        validate_self_hash(documents[path], expected_hash)
    arms = documents[ARM_PATH]["arms"]
    overlap = documents[OVERLAP_PATH]
    recovery = documents[RECOVERY_PATH]
    v1 = documents[V1_PATH]
    diagnostic = documents[DIAGNOSTIC_PATH]
    v2 = documents[V2_PATH]
    checks = (
        arms["D0"]["recall"] == EXPECTED.d0.recall,
        arms["D0"]["far"] == EXPECTED.d0.normal_far_per_hour,
        arms["D1"]["recall"] == EXPECTED.d1.recall,
        arms["D1"]["far"] == EXPECTED.d1.normal_far_per_hour,
        arms["D2"]["recall"] == EXPECTED.d2_v1.recall,
        arms["D2"]["far"] == EXPECTED.d2_v1.normal_far_per_hour,
        overlap["miss_d1"] == 3 and overlap["neither"] == 0,
        recovery["d1_potential_d0_miss_recovery_rate"] == 1.0,
        v1["d0_missed_attack_events_recovered"] == 0,
        v1["incremental_attack_event_recall"] == 0.0,
        v1["incremental_normal_far_episodes_per_hour"] == EXPECTED.d2_v1.incremental_normal_far_vs_d0,
        diagnostic["event_level_complementarity_supported"] is True,
        diagnostic["current_exact_gate_satisfied_inside_d0_missed_attack_events"] is False,
        v2["result_integrity"] == "PASS",
        v2["v2_attack_event_recall"] == EXPECTED.d2_v2.recall,
        v2["v2_normal_far"] == EXPECTED.d2_v2.normal_far_per_hour,
        v2["d0_misses_recovered_by_v2"] == 0,
        v2["incremental_attack_event_recall"] == 0.0,
        v2["incremental_normal_far"] == EXPECTED.d2_v2.incremental_normal_far_vs_d0,
        v2["test2_accesses"] == 0 and v2["outer_authorized"] is False,
    )
    if not all(checks):
        fail("D2_DISPOSITION_AUTHORITY_VALUE_REJECTED")
    return EXPECTED


def common(created: str) -> dict[str, Any]:
    return {"schema_version": "1.0.0", "task_id": TASK_ID,
            "created_at_utc": created, "remote_egress_status": "LOCAL_ONLY_NOT_PUSHED",
            "push_attempted": False}


def report_body(e: FrozenEvidence, d: Disposition) -> bytes:
    lines = [
        "# INNER D2 V1/V2 Scientific Disposition", "",
        "## 1. Experimental question", "",
        "Did verified Rule-only complementarity translate into useful detector-preserving fusion?", "",
        "## 2. Frozen results", "",
        "| Arm | Recall | Normal FAR/h | D0 miss recovery | Role |",
        "|---|---:|---:|---:|---|",
        f"| D0 | {e.d0.recall} | {e.d0.normal_far_per_hour} | N/A | Detector baseline |",
        f"| D1 | {e.d1.recall} | {e.d1.normal_far_per_hour} | 3/3 potential | Rule-only |",
        f"| D2 V1 | {e.d2_v1.recall} | {e.d2_v1.normal_far_per_hour} | 0/3 | Combined V1 |",
        f"| D2 V2 | {e.d2_v2.recall} | {e.d2_v2.normal_far_per_hour} | 0/3 | Combined V2 |", "",
        "## 3. Detector-rule complementarity", "",
        "D1 detected all three D0-missed INNER attack events; D0 and D1 jointly covered all 14 events. This supports complementary event information, not standalone operational utility, because D1 FAR was high.", "",
        "## 4. Why D2 V1 failed", "",
        "Its exact-same-second multi-source gate retained none of the known D0-miss recovery evidence and produced three normal recovery false alarms.", "",
        "## 5. Why D2 V2 did not fix V1", "",
        "Native-horizon memory increased corroboration activity, but D0-miss recovery remained 0/3 and normal FAR increased materially. Extending evidence over native temporal support did not resolve fusion utility.", "",
        "## 6. V1 versus V2", "",
        f"Recall was equal, while V2 FAR was {d.v2_v1_far_ratio} times V1 FAR. V1 therefore Pareto-dominates V2 on the two frozen primary utility dimensions.", "",
        "## 7. Stop further INNER tuning", "",
        "Further policy search on the same INNER labels is closed to limit post-hoc overfitting. No D2 V3, window, threshold, whitelist, score gate, learned fusion, or test1 calibration is authorized.", "",
        "## 8. Supported claims", "", *[f"- {x}" for x in SUPPORTED_CLAIMS], "",
        "## 9. Unsupported claims", "", *[f"- {x}" for x in UNSUPPORTED_CLAIMS], "",
        "## 10. Final combined candidate", "",
        "D2 V1 is retained only as the simpler, lower-FAR, INNER Pareto-preferred combined candidate. It is not a successful combined method or proven improvement.", "",
        "## 11. Proposed sealed OUTER evaluation", "",
        "Preregister exactly D0 detector-only, D1 Rule-only, and D2 V1 combined. Freeze all designs and execute sealed test2 once, prediction-before-label, with no recalibration or redesign.", "",
        "## 12. Exact next step", "", NEXT_TASK, "",
        "OUTER remains unauthorized.",
    ]
    return ("\n".join(lines) + "\n").encode()


def build_reports(e: FrozenEvidence, d: Disposition, created: str,
                  attacks: int, accepted: int) -> tuple[dict[str, dict[str, Any]], bytes]:
    c = common(created)
    reports: dict[str, dict[str, Any]] = {}
    reports["PRIMARY_COMPARISON"] = seal({"artifact_type": "D2V1V2PrimaryComparisonV1", **c,
        "arms": [asdict(e.d0), asdict(e.d1), asdict(e.d2_v1), asdict(e.d2_v2)],
        "attack_event_count": e.attack_event_count})
    reports["RULE_SIGNAL"] = seal({"artifact_type": "D2V1V2RuleSignalDispositionV1", **c,
        "d0_misses_detected_by_d1": 3, "d0_d1_union_coverage": "14/14",
        "rule_layer_complementary_event_information_supported": True,
        "rule_only_operational_utility_supported": False,
        "finding": "RULE_SIGNAL_PRESENT_BUT_CURRENT_FUSION_UTILITY_UNSUPPORTED"})
    reports["FUSION_FINDING"] = seal({"artifact_type": "D2V1V2FusionFindingV1", **c,
        "combined_incremental_utility_supported_on_inner": False,
        "d2_v2_fixed_v1_recovery_failure": False,
        "further_inner_d2_fusion_redesign_recommended": False,
        "further_inner_fusion_parameter_search_authorized": False,
        "inner_fusion_development_stop": True})
    reports["V1_V2_COMPARISON"] = seal({"artifact_type": "D2V1V2ComparisonV1", **c,
        "v1_recall_equals_v2_recall": True, "v1_v2_d0_miss_recovery_equal_zero": True,
        "v1_far": e.d2_v1.normal_far_per_hour, "v2_far": e.d2_v2.normal_far_per_hour,
        "v2_v1_far_ratio": d.v2_v1_far_ratio,
        "d2_v2_pareto_dominated_by_d2_v1_on_inner_primary_utility": True,
        "d2_v2_disposition": d.d2_v2_disposition})
    reports["THESIS_CLAIMS"] = seal({"artifact_type": "D2V1V2ThesisClaimsV1", **c,
        "supported_on_inner": list(SUPPORTED_CLAIMS), "unsupported": list(UNSUPPORTED_CLAIMS),
        "thesis_fatal_blocker": False,
        "combined_improvement_claim_must_be_removed_or_downgraded": True,
        "outer_generalization_still_required": True})
    reports["OUTER_CANDIDATE"] = seal({"artifact_type": "D2V1V2OuterCandidateV1", **c,
        "final_combined_policy_candidate": V1_ID,
        "selection_provenance": "SELECTED_AFTER_COMPLETED_INNER_DEVELOPMENT_COMPARISON",
        "selection_reason": "SIMPLER_SAME_RECALL_SUBSTANTIALLY_LOWER_FAR_THAN_V2",
        "d2_v2_in_primary_outer": False, "proposed_outer_primary_arm_count": 3,
        "proposed_outer_arms": list(OUTER_ARMS), "outer_disposition": OUTER_DISPOSITION,
        "outer_authorized": False})
    reports["INDEPENDENT_AUDIT"] = seal({"artifact_type": "D2V1V2DispositionIndependentAuditV1", **c,
        "independent_attacks": attacks, "independent_attacks_rejected": attacks,
        "accepted_invalid": accepted, "scientific_executions": 0,
        "test1_feature_accesses": 0, "label_parses": 0, "test2_accesses": 0,
        "outer_executions": 0})
    reports["READINESS"] = seal({"artifact_type": "D2V1V2DispositionReadinessV1", **c,
        "status": STATUS, "blockers": [], "inner_fusion_development_closed": True,
        "combined_incremental_utility_supported": False, "outer_authorized": False,
        "exact_next_task": NEXT_TASK})
    body = report_body(e, d); body_hash = sha256(body).hexdigest()
    refs = {k.lower() + "_sha256": v["artifact_hash"] for k, v in reports.items()}
    bundle = seal({"artifact_type": "D2V1V2DispositionBundleV1", **c, **refs,
        "report_hash_scheme": SCHEME, "report_body_sha256": body_hash})
    receipt = seal({"artifact_type": "D2V1V2DispositionReceiptV1", **c,
        "bundle_sha256": bundle["artifact_hash"], "final_combined_candidate": V1_ID,
        "outer_disposition": OUTER_DISPOSITION, "outer_authorized": False,
        "authority_sha256s": sorted(AUTHORITIES.values()), "exact_next_task": NEXT_TASK})
    reports["BUNDLE"] = bundle; reports["RECEIPT"] = receipt
    footer = ("\n<!-- BEGIN D2 V1 V2 DISPOSITION REPORT PROVENANCE V1 -->\n"
        f"Report-Hash-Scheme: {SCHEME}\nReport-Self-Hash: {body_hash}\n"
        f"Bundle-Hash: {bundle['artifact_hash']}\nReceipt-Hash: {receipt['artifact_hash']}\n"
        "<!-- END D2 V1 V2 DISPOSITION REPORT PROVENANCE V1 -->\n").encode()
    return reports, body + footer


def adversarial_contract() -> tuple[int, int]:
    attacks = 0; accepted = 0
    def reject(action: Any) -> None:
        nonlocal attacks, accepted
        attacks += 1
        try: action()
        except DispositionError: return
        accepted += 1
    mutations = (
        ("d0", replace(EXPECTED.d0, recall=0.8)),
        ("d1", replace(EXPECTED.d1, normal_far_per_hour=1.0)),
        ("d2_v1", replace(EXPECTED.d2_v1, d0_misses_recovered=1)),
        ("d2_v2", replace(EXPECTED.d2_v2, recall=0.9)),
        ("d0_misses_detected_by_d1", 2), ("d0_d1_union_coverage", 13),
        ("v1_rule_recovery_false_alarm_episodes", 0),
        ("v2_native_horizon_corroboration_points", 0),
    )
    for field, value in mutations:
        reject(lambda field=field, value=value: derive_disposition(replace(EXPECTED, **{field: value})))
    reject(lambda: strict_json(b'{"a":1,"a":2}'))
    reject(lambda: seal({"artifact_hash": "x"}))
    reject(lambda: seal({"reference_artifact_hash": "x"}))
    reject(lambda: validate_authorities({}))
    for path in AUTHORITIES:
        reject(lambda path=path: validate_authorities({p: ({"artifact_hash": "0" * 64}) for p in AUTHORITIES}))
    return attacks, accepted


def git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode: fail("D2_DISPOSITION_GIT_REJECTED")
    return result.stdout.strip()


def _pre_gate() -> None:
    if git("rev-parse", "--abbrev-ref", "HEAD") != BRANCH or git("status", "--porcelain"):
        fail("D2_DISPOSITION_GIT_STATE_REJECTED")
    allowed = {"TASKS/" + TASK_ID + ".md",
        "scripts/freeze_task039e3_r2r_inner_d2_v1_v2_scientific_disposition_v1.py",
        "tests/test_task039e3_r2r_inner_d2_v1_v2_scientific_disposition_v1.py",
        "tests/test_task039e3_r2r_inner_d2_v1_v2_scientific_disposition_v1_independent.py"}
    changed = {x for x in git("diff", "--name-only", BASE, "HEAD").split("\n") if x}
    if changed != allowed: fail("D2_DISPOSITION_COMMIT_A_BOUNDARY_REJECTED")
    if any((REPORT_ROOT / name).exists() for name in FILES.values()):
        fail("D2_DISPOSITION_REPORT_EXISTS")


def freeze() -> dict[str, Any]:
    _pre_gate()
    documents = {path: strict_json(path.read_bytes()) for path in AUTHORITIES}
    evidence = validate_authorities(documents)
    disposition = derive_disposition(evidence)
    attacks, accepted = adversarial_contract()
    if accepted: fail("D2_DISPOSITION_ACCEPTED_INVALID")
    created = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    reports, markdown = build_reports(evidence, disposition, created, attacks, accepted)
    for name, doc in reports.items():
        (REPORT_ROOT / FILES[name]).write_bytes((json.dumps(doc, sort_keys=True, indent=2,
            ensure_ascii=True, allow_nan=False) + "\n").encode())
    (REPORT_ROOT / FILES["REPORT"]).write_bytes(markdown)
    return {"status": STATUS, "branch": BRANCH, "base": BASE,
        "evidence": asdict(evidence), "disposition": asdict(disposition),
        "scientific_executions": 0, "test1_feature_accesses": 0,
        "label_parses": 0, "test2_accesses": 0, "outer_executions": 0,
        "result_driven_changes": False, "independent_attacks": attacks,
        "accepted_invalid": accepted,
        **{k.lower() + "_hash": v["artifact_hash"] for k, v in reports.items()},
        "report_self_hash": sha256(markdown[:markdown.index(b"\n<!-- BEGIN")]).hexdigest()}


def main() -> int:
    if sys.argv[1:]: print("D2_DISPOSITION_ARGUMENTS_REJECTED"); return 2
    try: result = freeze()
    except DispositionError as error: print(error.code); return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
