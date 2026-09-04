#!/usr/bin/env python3
"""Build deterministic, public-safe RCC views from the frozen registries.

This module uses only the Python standard library.  It reads public RCC
metadata; it never imports or invokes scientific project code.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
from front_results_view import front_markdown
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


AUTHORITY_COMMIT = "2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e"
REGISTRY_FILES = (
    "current_state.yaml",
    "components.csv",
    "experiments.csv",
    "claims.csv",
    "risks.csv",
    "artifacts.csv",
    "decisions.csv",
    "timeline.csv",
    "history.yaml",
)

ARCHITECTURE_FILES = (
    "00_overview/ARCH_000_SOURCE_MAP.csv",
    "00_overview/ARCH_000_DATAFLOW.csv",
    "00_overview/ARCH_000_ARTIFACT_LINEAGE.csv",
    "00_overview/ARCH_000_COMPONENT_DETAIL.csv",
    "01_data_and_splits/ARCH_001_LEAKAGE_MATRIX.csv",
    "01_data_and_splits/ARCH_001_INPUT_CONTRACTS.csv",
    "01_data_and_splits/ARCH_001_FUNCTION_CATALOG.csv",
    "02_candidate_discovery/ARCH_002_ARM_COMPARISON.csv",
    "02_candidate_discovery/ARCH_002_CANDIDATE_PROVENANCE.csv",
    "02_candidate_discovery/ARCH_002_FUNCTION_CATALOG.csv",
    "02_candidate_discovery/ARCH_002_IO_CONTRACTS.csv",
    "03_relation_and_numeric/ARCH_003_RELATION_LINEAGE.csv",
    "03_relation_and_numeric/ARCH_003_NUMERIC_AUTHORITY.csv",
    "03_relation_and_numeric/ARCH_003_FUNCTION_CATALOG.csv",
    "03_relation_and_numeric/ARCH_003_IO_CONTRACTS.csv",
    "04_rule_construction/ARCH_004_EVIDENCE_LINEAGE.csv",
    "04_rule_construction/ARCH_004_ARM_OUTCOMES.csv",
    "04_rule_construction/ARCH_004_FUNCTION_CATALOG.csv",
    "04_rule_construction/ARCH_004_IO_CONTRACTS.csv",
    "05_verifier_common42/ARCH_005_VERIFIER_STAGES.csv",
    "05_verifier_common42/ARCH_005_VALIDITY_EQUIVALENCE.csv",
    "05_verifier_common42/ARCH_005_ARM_PORTFOLIO_MAPPING.csv",
    "05_verifier_common42/ARCH_005_HASH_CHAIN.csv",
    "05_verifier_common42/ARCH_005_FUNCTION_CATALOG.csv",
    "05_verifier_common42/ARCH_005_IO_CONTRACTS.csv",
    "06_runtime_trace_explanation/ARCH_006_TRACE_SCHEMA.csv",
    "06_runtime_trace_explanation/ARCH_006_FUNCTION_CATALOG.csv",
    "06_runtime_trace_explanation/ARCH_006_IO_CONTRACTS.csv",
    "07_d0_detector/ARCH_007_ARTIFACT_LINEAGE.csv",
    "07_d0_detector/ARCH_007_FUNCTION_CATALOG.csv",
    "07_d0_detector/ARCH_007_IO_CONTRACTS.csv",
    "08_d1_rule_only/ARCH_008_D0_D1_OVERLAP.csv",
    "08_d1_rule_only/ARCH_008_ARTIFACT_LINEAGE.csv",
    "08_d1_rule_only/ARCH_008_CLAIM_MATRIX.csv",
    "08_d1_rule_only/ARCH_008_FUNCTION_CATALOG.csv",
    "08_d1_rule_only/ARCH_008_IO_CONTRACTS.csv",
    "09_d2_fusion/ARCH_009_POLICY_COMPARISON.csv",
    "09_d2_fusion/ARCH_009_CLAIM_MATRIX.csv",
    "09_d2_fusion/ARCH_009_FUNCTION_CATALOG.csv",
    "09_d2_fusion/ARCH_009_IO_CONTRACTS.csv",
    "gap_000_pre_validation/GAP_000_RAW_FINDINGS.csv",
    "gap_000_pre_validation/GAP_000_ROOT_ISSUES.csv",
    "gap_000_pre_validation/GAP_000_REMEDIATION_MATRIX.csv",
    "gap_000_pre_validation/GAP_000_EXPERIMENT_GATES.csv",
    "11_outer_reproducibility/ARCH_011_ENVIRONMENT_MATRIX.csv",
    "11_outer_reproducibility/ARCH_011_PATH_MACHINE_ASSUMPTIONS.csv",
    "11_outer_reproducibility/ARCH_011_ARTIFACT_PORTABILITY.csv",
    "11_outer_reproducibility/ARCH_011_AUTHORITY_OPTIONS.csv",
)


def default_rcc_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_registry(rcc_root: Path) -> dict[str, Any]:
    """Load the JSON-compatible YAML state and every CSV registry."""

    registry_dir = rcc_root / "registry"
    state = json.loads((registry_dir / "current_state.yaml").read_text(encoding="utf-8"))
    history = json.loads((registry_dir / "history.yaml").read_text(encoding="utf-8"))
    data = {
        "state": state,
        "history": history,
        "components": _read_csv(registry_dir / "components.csv"),
        "experiments": _read_csv(registry_dir / "experiments.csv"),
        "claims": _read_csv(registry_dir / "claims.csv"),
        "risks": _read_csv(registry_dir / "risks.csv"),
        "artifacts": _read_csv(registry_dir / "artifacts.csv"),
        "decisions": _read_csv(registry_dir / "decisions.csv"),
        "timeline": _read_csv(registry_dir / "timeline.csv"),
    }
    detail = rcc_root / "architecture" / "00_overview" / "ARCH_000_COMPONENT_DETAIL.csv"
    data["architecture_details"] = _read_csv(detail) if detail.is_file() else []
    from front_results_view import load_front_results
    data["front_results"] = load_front_results(rcc_root.parent, state)
    return data


def registry_digest(rcc_root: Path) -> str:
    """Hash names and bytes of every file that can affect generated views."""

    digest = hashlib.sha256()
    registry_dir = rcc_root / "registry"
    for name in REGISTRY_FILES:
        payload = (registry_dir / name).read_bytes()
        digest.update(name.encode("utf-8"))
        digest.update(b"\x00")
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    architecture_dir = rcc_root / "architecture"
    for name in ARCHITECTURE_FILES:
        path = architecture_dir / name
        if not path.is_file():
            continue
        payload = path.read_bytes()
        digest.update(name.encode("utf-8"))
        digest.update(b"\x00")
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def _escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def _short_commit(commit: str) -> str:
    return commit[:12] + "\u2026"


def _badge_class(status: str) -> str:
    if status in {"IMPLEMENTED_EXECUTED_AUDITED", "AUDITED", "REPRODUCED", "CLAIM_READY", "COMPLETED", "ACTIVE", "ACTIVE_CONTEXT"}:
        return "badge-green"
    if status in {"IMPLEMENTED_EXECUTED", "IMPLEMENTED_NOT_EXECUTED", "CODE_IMPLEMENTED", "INTEGRATED", "SUPPORTED_IMPLEMENTATION"}:
        return "badge-blue"
    if status in {"PARTIAL", "EXECUTED_AUDITED_PILOT", "EXECUTED_AUDITED_DEVELOPMENT", "PILOT_ONLY", "CONDITIONAL", "MITIGATING", "CURRENT", "HISTORICAL"}:
        return "badge-yellow"
    if status in {"BLOCKED", "HIGH"}:
        return "badge-orange"
    if status in {"NOT_SUPPORTED", "DEVELOPMENT_NOT_SUPPORTED", "CRITICAL"}:
        return "badge-red"
    return "badge-gray"


STATUS_DISPLAY_LABELS = {
    "CODE_IMPLEMENTED": "구현 완료 (CODE_IMPLEMENTED)",
    "EXECUTED": "실제 실행 완료 (EXECUTED)",
    "EVIDENCE_REVIEWED": "근거 점검 완료 (EVIDENCE_REVIEWED)",
    "RESULT_INTEGRITY": "결과 무결성 확인 (RESULT_INTEGRITY)",
    "REPRODUCED": "독립 재현 완료 (REPRODUCED)",
    "UNVALIDATED": "미검증 (UNVALIDATED)",
    "PILOT_ONLY": "예비 실험 수준 (PILOT_ONLY)",
    "UNCONFIRMED": "미확인 (UNCONFIRMED)",
    "BLOCKED": "진행 전 해결 필요 (BLOCKED)",
    "CONDITIONAL": "조건부 (CONDITIONAL)",
    "READY_WITH_CONDITIONS": "조건부 진행 가능 (READY_WITH_CONDITIONS)",
    "NOT_REQUIRED": "현재 필요하지 않음 (NOT_REQUIRED)",
    "IMPLEMENTED_EXECUTED_AUDITED": "구현·실행·근거 점검 완료",
    "IMPLEMENTED_EXECUTED": "구현·실행 완료",
    "IMPLEMENTED_NOT_EXECUTED": "구현 완료·미실행",
    "EXECUTED_NOT_AUDITED": "실행 완료·근거 점검 대기",
    "EXECUTED_AUDITED_PILOT": "실행·근거 점검 완료·예비 실험",
    "EXECUTED_AUDITED_DEVELOPMENT": "실행·근거 점검 완료·개발 결과",
    "SUPPORTED_IMPLEMENTATION": "구현 근거로 지원됨",
    "NOT_SUPPORTED": "현재 근거로 지원되지 않음",
    "DEVELOPMENT_NOT_SUPPORTED": "현재 개발 결과로 지원되지 않음",
    "RESEARCH_ONLY": "연구 범위만 정의됨",
    "DESIGN_ONLY": "설계만 완료",
    "PARTIAL": "부분 완료",
    "NOT_STARTED": "미시작",
    "SUPERSEDED": "대체됨",
    "LEGACY_OR_SUPERSEDED": "과거 호환 또는 대체됨",
    "ACTIVE": "유효",
    "ACTIVE_CONTEXT": "현재 맥락",
    "CURRENT": "현재",
    "HISTORICAL": "과거 기록",
    "MITIGATING": "완화 중",
    "OPEN": "미결정",
    "COMPLETED": "완료",
    "COMPLETE": "완료",
    "READY": "진행 가능",
    "HIGH": "높음 (HIGH)",
    "MEDIUM": "중간 (MEDIUM)",
    "LOW": "낮음 (LOW)",
    "CRITICAL": "치명적 (CRITICAL)",
    "UNKNOWN": "미확인 (UNKNOWN)",
}

COMPONENT_STATUS_LABELS = {
    key: STATUS_DISPLAY_LABELS[key]
    for key in (
        "IMPLEMENTED_EXECUTED_AUDITED", "IMPLEMENTED_EXECUTED",
        "IMPLEMENTED_NOT_EXECUTED", "RESEARCH_ONLY", "DESIGN_ONLY",
        "PARTIAL", "BLOCKED", "LEGACY_OR_SUPERSEDED", "UNKNOWN",
    )
}

EXPERIMENT_STATUS_LABELS = {
    key: STATUS_DISPLAY_LABELS[key]
    for key in (
        "NOT_STARTED", "DESIGN_ONLY", "IMPLEMENTED_NOT_EXECUTED",
        "EXECUTED_NOT_AUDITED", "EXECUTED_AUDITED_PILOT", "EXECUTED_AUDITED_DEVELOPMENT", "BLOCKED",
        "SUPERSEDED", "UNKNOWN",
    )
}

GPT_EXPERIMENT_STATUS_LABELS = {
    "NOT_STARTED": "NOT STARTED",
    "DESIGN_ONLY": "DESIGNED ONLY",
    "IMPLEMENTED_NOT_EXECUTED": "CODE PRESENT · COMPARISON NOT EXECUTED",
    "EXECUTED_NOT_AUDITED": "EXECUTED · EVIDENCE REVIEW PENDING",
    "EXECUTED_AUDITED_PILOT": "EXECUTED · EVIDENCE-REVIEWED PILOT",
    "EXECUTED_AUDITED_DEVELOPMENT": "EXECUTED · EVIDENCE-REVIEWED DEVELOPMENT RESULT",
    "BLOCKED": "BLOCKED",
    "SUPERSEDED": "SUPERSEDED",
    "UNKNOWN": "UNKNOWN",
}

PHASE_DISPLAY_LABELS = {
    "ARCHITECTURE_COMPLETE": "아키텍처 감사 완료",
    "EVALUATION_SCOPE_EXPANSION": "평가 범위 확장",
    "HYPOTHESIS_VALIDATION": "가설 검증",
}

ARCHITECTURE_DISPLAY_LABELS = {
    "DATA": "데이터와 분할",
    "DISCOVERY": "후보 관계 탐색",
    "RELATION": "관계 프로파일링",
    "RULE": "규칙 구성",
    "VERIFIER": "결정론적 검증",
    "RUNTIME": "규칙 실행과 추적",
    "D0": "D0 기준 탐지기",
    "D1": "D1 관계 규칙 단독 방식",
    "D2": "D2 탐지기·규칙 결합",
    "METRICS": "지표와 결과 무결성",
    "REPRODUCIBILITY": "재현성과 OUTER",
}

COMPONENT_CARD_COPY = {
    "DATA_PROVENANCE": ("HAI 데이터 출처 고정", "데이터 판본과 공개 가능한 식별 정보를 고정한다."),
    "SPLIT_GOVERNANCE": ("데이터 분할 통제", "각 split의 허용 역할과 경계 제거 규칙을 강제한다."),
    "VARIABLE_ROLE_UNIVERSE": ("변수 역할과 후보 범위", "source·target 역할과 가능한 pair universe를 고정한다."),
    "META_DISCOVERY": ("META 후보 탐색", "실제 값 없이 metadata만으로 후보를 순위화한다."),
    "STAT_DISCOVERY": ("STAT 후보 탐색", "정상 데이터의 시간 지연 통계 연관성으로 후보를 순위화한다."),
    "GDN_DISCOVERY": ("GDN 후보 탐색", "학습 그래프의 후보 순위 근거를 만들며 인과관계로 해석하지 않는다."),
    "CANDIDATE_UNION": ("후보 합집합", "META·STAT·GDN 후보를 재점수화 없이 합친다."),
    "RELATION_PROFILING": ("정상 관계 프로파일링", "정상 반복 반응에서 방향과 시간 지연을 확인한다."),
    "NUMERIC_AUTHORITY": ("정상 전용 수치 권한", "시간·허용오차·지속성·크기 참조를 정상 근거에 결속한다."),
    "EVIDENCE_PACK": ("관계 근거 묶음 (Evidence Pack)", "고정 관계와 수치 참조, 근거 출처 추적(Provenance)을 구성 단계에 전달한다."),
    "RULE_DSL": ("규칙 제안 언어 (Rule DSL)", "제안 가능한 필드를 닫힌 구조로 제한하고 canonical Rule과 분리한다."),
    "T0_TEMPLATE": ("T0 결정론적 template", "LLM 없이 만드는 규칙 구성 비교 기준이다."),
    "T1_ONE_SHOT": ("T1 one-shot 구성", "제한된 LLM 1회 제안 비교군이다."),
    "T1B_REPEAT": ("T1-B 반복 예산 대조군", "T2와 같은 호출 예산으로 독립 생성을 반복한다."),
    "T2_AGENTIC_FEEDBACK": ("T2 검증 피드백 구성", "revise·retrieve·no_rule을 허용하는 제한된 제어 경로다."),
    "DETERMINISTIC_VERIFIER": ("결정론적 검증기", "label 없이 구조·근거·수치·실행 계약을 검사한다."),
    "COMMON42_FREEZE": ("COMMON-42 고정", "검증된 42개 관계 규칙 portfolio를 불변 상태로 고정한다."),
    "RULE_RUNTIME": ("LLM 없는 규칙 실행", "고정 규칙과 승인된 수치 참조를 결정론적으로 실행한다."),
    "SATISFACTION_TRACE": ("규칙 충족 추적 (Satisfaction Trace)", "관찰된 평가 단계와 권한 결속을 기록한다."),
    "EXPLANATION_RENDERER": ("추적 기반 설명 생성", "규칙과 trace에 있는 사실만 제한적으로 설명한다."),
    "D0_PCA_SPE": ("D0 PCA-SPE 기준 탐지기", "단순하고 결정론적인 정상 전용 다변량 기준선이다."),
    "D1_RULE_ONLY": ("D1 검증된 관계 규칙 단독 방식", "COMMON-42만으로 만드는 독립 이상 신호다."),
    "D2_V1": ("D2 V1 결합", "같은 초의 D0·D1 근거를 결합하는 고정 정책이다."),
    "D2_V2": ("D2 V2 결합", "native horizon 근거를 이용하는 test1-informed 개발 정책이다."),
    "EPISODE_CONSTRUCTION": ("알람 episode 구성", "연속 alarm second를 최대 연속 구간으로 묶는다."),
    "ATTACK_EVENT_RECALL": ("공격 사건 단위 재현율 (Attack-event Recall)", "alarm episode가 겹친 attack-event unit 비율을 측정한다."),
    "NORMAL_FAR": ("정상 FAR/hour", "정상 노출 시간당 비공격 alarm episode 수를 측정한다."),
    "RESULT_INTEGRITY": ("결과 무결성 점검", "prediction·metric·순서·누출 경계를 확인하며 성능 타당성을 대신하지 않는다."),
    "OUTER_EVALUATION": ("Held-out OUTER 평가", "일반화 검증 경로지만 현재 과학 결과는 없다."),
    "REPRODUCIBILITY": ("재현성 평가", "source pin·artifact 보존·복원 준비 수준을 구분한다."),
    "PROFESSOR_REPORTING": ("교수 보고", "고정 관찰과 주장 한계를 함께 전달한다."),
    "THESIS_DRAFT": ("논문 작업 초안", "잠정 서술 맥락이며 scientific authority를 대체하지 않는다."),
}

EXPERIMENT_CARD_COPY = {
    "EXP-01": ("변수 관계 탐색 방법 비교", "META·STAT·GDN의 고유하고 유용한 후보 기여가 있는지 비교한다."),
    "EXP-01B": ("GDN Prediction-XAI 추가 검증", "Embedding·Attention·EdgeMask·Source Occlusion을 동일 정상 관계 기준에서 비교한다."),
    "EXP-02": ("규칙 수치 기준 비교", "응답 시간·허용오차·지속성 기준이 validity와 utility에 미치는 영향을 비교한다."),
    "EXP-03": ("검증 피드백 기반 규칙 생성 비교", "T2 verifier feedback의 이점이 있는지 예산이 맞는 대조군과 비교한다."),
    "EXP-04": ("검증된 관계 규칙의 이상탐지 성능 비교", "D0·D1·D2의 attack response와 정상 false alarm 부담을 함께 비교한다."),
    "EXP-05": ("규칙 설명의 일치성 검증", "설명이 rule·trace·수치 출처·outcome을 벗어나지 않는지 검사한다."),
    "EXP-06": ("실시간 LLM 활용 비교", "고정 규칙 결과나 정답을 받지 않는 별도 runtime LLM 비교 가능성을 검토한다."),
}

CLAIM_CARD_COPY = {
    "CLAIM-A": ("HAI P1 INNER 아키텍처 구현", "구현은 확인됐지만 전체 방법의 일반화나 최종 검증을 뜻하지 않는다."),
    "CLAIM-B": ("정상 근거에서 실행 규칙으로 변환", "정상 관계 근거를 권한 통제 아래 실행 가능한 규칙으로 변환했다."),
    "CLAIM-C": ("결정론적 verifier의 계약 검사", "구조·근거·수치·split·실행 계약을 검사하지만 과학적 진실을 증명하지 않는다."),
    "CLAIM-D": ("고정 규칙 runtime의 LLM-free 실행", "고정 authority가 같으면 현재 runtime은 LLM 없이 결정론적으로 평가한다."),
    "CLAIM-E": ("GDN의 고유한 유용성", "EXP-01과 EXP-01B의 동결된 정상 전용 기준은 GDN의 핵심·보조 기여를 지원하지 않았다."),
    "CLAIM-F": ("Agentic feedback의 품질 향상", "현재 feedback action이 0이므로 이점은 지원되지 않는다."),
    "CLAIM-G": ("D1과 D0의 다른 pilot 반응", "현재 14-unit pilot에서 서로 다른 event response가 관찰됐다."),
    "CLAIM-H": ("Rule-only의 운영 유용성", "높은 event response와 높은 정상 FAR가 함께 있어 운영 유용성은 미검증이다."),
    "CLAIM-I": ("Detector+Rule 성능 향상", "현재 D2 V1/V2는 D0 Recall을 개선하지 못했다."),
    "CLAIM-J": ("Held-out 일반화", "OUTER 과학 결과가 없어 일반화는 확인되지 않았다."),
    "CLAIM-K": ("설명의 trace 충실도", "renderer 결속은 구현됐지만 전체 corpus의 fidelity는 조건부다."),
    "CLAIM-L": ("설명의 인간 유용성", "trace 기반 interface는 있으나 사람에게 유용한지는 평가하지 않았다."),
    "CLAIM-M": ("인과·root-cause 관계", "현재 근거는 시간 관계와 위반을 기록할 뿐 인과를 지원하지 않는다."),
}

RISK_CARD_COPY = {
    "RISK-01": ("14개 event unit의 작은 평가 범위", "통계적 독립성과 안정적 우수성을 추론할 수 없다."),
    "RISK-02": ("D1의 높은 정상 FAR", "Rule-only 운영 유용성이 아직 확립되지 않았다."),
    "RISK-03": ("현재 V2에서 GDN 기여 미지원", "EXP-01과 EXP-01B의 동결 기준은 GDN의 핵심·보조 기여를 지원하지 않았다."),
    "RISK-04": ("T2 feedback 이점 미검증", "현재 feedback repair action은 0이었다."),
    "RISK-05": ("D2의 D0 miss 회복 실패", "V1/V2 모두 세 D0 miss를 회복하지 못했다."),
    "RISK-06": ("Held-out 일반화 결과 부재", "새 승인과 preregistration 전에는 OUTER 주장을 할 수 없다."),
    "RISK-07": ("과학 데이터 재현 미완료", "Fresh-machine synthetic rehearsal은 PASS지만 private custody를 포함한 과학 재현은 아직이다."),
    "RISK-08": ("강한 다변량 baseline 부재", "현재 D0는 단순 PCA-SPE 기준선이다."),
    "RISK-09": ("설명의 인간 유용성 미검증", "자동 trace grounding은 사람의 이해 향상을 증명하지 않는다."),
    "RISK-10": ("과거 checkout과 authority 혼동", "RCC 화면은 고정 scientific authority를 계속 명시해야 한다."),
    "RISK-11": ("V2 D1 durable pre-label gate 완료", "PILOT V1의 조건은 유지하고 VALIDATION V2에 no-overwrite custody를 추가했다."),
    "RISK-12": ("분산된 split enforcement", "여러 task reader의 계약이 하나의 universal adapter로 증명되지 않았다."),
    "RISK-13": ("VALIDATION V2 Rule/runtime authority 결정 완료", "DEC-020과 GAP-FIX-001이 Formal V4를 선택·고정했으며 canonical RuleV1·VerifierV1 authority를 주장하지 않는다."),
    "RISK-14": ("no_rule failure taxonomy 혼합", "provider·parse·verifier·budget failure가 no_rule로 합쳐질 수 있다."),
    "RISK-15": ("GDN self-neighbor prospective correction", "PILOT V1은 보존하고 V2 실험은 corrected self-exclusion을 사용했다."),
    "RISK-16": ("metric portability 계약 부족", "1초·file-local 가정과 cross-arm aggregator 추적성이 불완전하다."),
}

HISTORY_CARD_COPY = {
    "EVENT-001": ("DHAG 확장·개념 증명 시기", "PoC에서 확인된 구조 한계로 DHAG가 논문의 주 방향에서 제외됐다."),
    "EVENT-002": ("ARGOS·LLMAD 탐색", "관련 연구와 차별화 방향을 다시 검토한 과거 탐색 단계다."),
    "EVENT-003": ("Faithfulness Verifier 중심 framing", "headline 방향은 대체됐지만 결정론적 검증과 trace 일치성 아이디어는 남았다."),
    "EVENT-005": ("Graph-guided verified-rule prototype 정립", "graph 후보·typed rule·결정론적 verifier·runtime의 초기 기반이 저장소에 형성됐다."),
    "EVENT-008": ("ARGOS reference track 고정", "ARGOS는 exact reproduction이 아니라 부분 방법론 참고로 고정됐다."),
    "EVENT-009": ("V6 authority layer 분리", "정상 근거·구성·validity·governance·runtime·설명의 권한을 분리했다."),
    "EVENT-013": ("Pairwise·Rule-only 범위 명확화", "pairwise-first와 D0/D1/D2 비교, 좁은 agent 용어를 연구 범위로 명확히 했다."),
    "EVENT-014": ("P1 Boiler 선택", "정상 전용 feasibility gate를 통과한 P1만 대상으로 고정했다."),
    "EVENT-020": ("COMMON-42와 정상 전용 authority 확정", "42-rule portfolio와 별도 numeric authority를 고정하고 점검했다."),
    "EVENT-021": ("첫 D1 Rule-only INNER 결과", "승인된 D1 실행과 결과 무결성 점검이 완료됐지만 운영 유용성은 미검증이다."),
    "EVENT-022": ("첫 D0 PCA-SPE INNER 결과", "승인된 D0 실행과 독립 결과 무결성 점검이 완료됐다."),
    "EVENT-025": ("OUTER 과학 결과 없음", "feature custody 단계에서 멈춰 byte·label·prediction·metric 결과가 생성되지 않았다."),
    "EVENT-026": ("교수용 첫 결과 package와 scientific checkpoint 고정", "교수용 종합 보고와 canonical scientific checkpoint 점검을 완료했으며, 이 package 자체는 새로운 교수 피드백이나 승인이 아니다."),
    "EVENT-027": ("통합 보고 준비 업데이트", "연구 책임자가 통합 보고 준비·업데이트였음을 확인했으며 자동으로 새 교수 피드백이 되지 않는다."),
    "EVENT-028": ("Research Control Center 구축·정규화", "RCC-001이 운영 뼈대를 만들고 RCC-002·002A가 현재 상태와 상태 의미를 분리해 채웠다."),
}

TODO_CARD_COPY = {
    "USER-ARCH011-001": ("기존 OUTER에 과학 결과가 없는 이유 이해", "custody blocker는 test2 성능 실패가 아니다."),
    "USER-ARCH011-002": ("같은 물리 test2의 새 연구 사용 여부 결정", "내용은 봉인됐지만 재사용 권한이 자동으로 생기지는 않는다."),
    "USER-ARCH011-003": ("5단계 재현성 수준 이해", "근거 추적(traceability)과 새 환경 재현을 구분해야 한다."),
    "USER-ARCH011-004": ("authority 선택지 검토 완료", "lossless bridge를 강제하지 않고 Formal V4를 별도 V2 권한으로 선택했다."),
    "USER-ARCH011-005": ("최종 scientific authority 결정 완료", "DEC-020은 Formal V4를 VALIDATION V2 authority로 고정한다."),
    "USER-ARCH011-006": ("PILOT V1 보존·VALIDATION V2 분리 확인", "승인된 정책은 모든 변경을 미래 V2에만 적용한다."),
    "USER-ARCH011-007": ("remediation 순서 승인", "authority와 custody를 portability rehearsal과 held-out보다 먼저 닫는다."),
    "USER-ARCH011-008": ("첫 remediation task 승인", "ARCH-011은 어떤 remediation도 실행하지 않았다."),
}

DECISION_CARD_COPY = {
    "DEC-012": ("결정론적 코드를 최종 verifier authority로 사용", "현재 유효하며 과학적 검증과 계속 구분해야 한다."),
    "DEC-013": ("LLM-free 고정 규칙 runtime baseline 사용", "현재 runtime authority로 유효하다."),
    "DEC-014": ("Detector·Rule-only·결합 arm 비교", "비교 아키텍처는 유효하지만 더 강한 검증은 새 preregistration이 필요하다."),
    "DEC-015": ("runtime LLM은 조건부 향후 비교로 유지", "현재 core에 포함되거나 실행 승인된 경로가 아니다."),
    "DEC-016": ("Graph-Guided·Agentic label을 잠정 유지", "현재 주장 경계로 유효하다."),
    "DEC-017": ("현재 INNER 결과를 예비 실험으로 분류", "현재 보고 경계이며 과거 기록을 고치지 않고 independent-event 표현만 교정한다."),
    "DEC-018": ("기존 OUTER는 결과 없음으로 두고 새 preregistration 요구", "향후 평가 경계로 유효하다."),
    "DEC-020": (
        "VALIDATION V2 Formal V4 authority 채택",
        "lossless canonical bridge를 주장하지 않고 relation·numeric value·evaluator·config·data contract·horizon을 재검증하는 별도 Formal V4 권한을 사용한다.",
    ),
    "DEC-021": ("Graph-Guided·Agentic 기여를 조건부로 유지", "ARCH-011에서 승인된 정책이며 향후 근거에 따라 기여 여부를 결정한다."),
}

KOREAN_TEXT = {
    "Architecture implementation and pilot operation are complete. Scientific validation is partial; expanded evaluation and hypothesis validation remain incomplete.": "아키텍처 구현과 예비 운영은 완료됐다. 과학적 검증은 일부에 그치며 확대 평가와 가설 검증은 아직 완료되지 않았다.",
    "The pinned HAI 23.05 P1 INNER architecture is implemented; source evidence is reviewed and named frozen pilot results have explicit integrity audits where registered.": "고정된 HAI 23.05 P1 INNER 아키텍처가 구현됐고 source evidence가 점검됐으며, 등록된 frozen pilot 결과에는 명시적인 결과 무결성 점검이 있다.",
    "Normal-only evidence was transformed into a 42-descriptor COMMON-42 V4 executable relation portfolio under task-specific authority controls.": "정상 전용 근거가 task-specific authority 아래 42-descriptor COMMON-42 V4 실행 관계 portfolio로 변환됐다.",
    "D0, D1, D2 V1, and D2 V2 have frozen integrity-audited INNER pilot results.": "D0·D1·D2 V1·D2 V2에는 고정되고 결과 무결성이 확인된 INNER pilot 결과가 있다.",
    "The OUTER path has a blocker record and no scientific result.": "OUTER 경로에는 blocker record만 있고 과학 결과는 없다.",
    "GDN unique and stable scientific contribution beyond META and STAT": "META·STAT 너머의 GDN 고유·안정적 과학 기여",
    "Agentic verifier-feedback advantage": "Agentic verifier-feedback 이점",
    "Practical Rule-only operational utility": "Rule-only의 실제 운영 유용성",
    "Detector-plus-Rule improvement": "Detector+Rule 성능 향상",
    "Detector-plus-Rule improvement beyond the tested negative pilot policies": "현재 negative pilot policy를 넘어선 Detector+Rule 향상",
    "Held-out generalization": "Held-out 일반화",
    "Human explanation usefulness": "설명의 인간 유용성",
    "Explain why old OUTER has no result and cannot simply retry.": "기존 OUTER에 결과가 없고 단순 재시도할 수 없는 이유를 설명한다.",
    "Decide same-physical-test2 eligibility only within a new preregistered study.": "같은 물리 test2의 사용 가능 여부는 새 preregistered study 안에서만 결정한다.",
    "Explain traceability, same-machine, fresh-machine synthetic/scientific, and external reproduction.": "근거 추적, 같은 환경 replay, 새 환경 synthetic/scientific 재현, 외부 재현을 구분해 설명한다.",
    "Review and approve the canonical-to-V4 bridge target or fallback.": "canonical-to-V4 bridge 목표 또는 fallback을 검토·승인한다.",
    "Confirm PILOT V1 preservation and VALIDATION V2 separation.": "PILOT V1 보존과 VALIDATION V2 분리를 확인한다.",
    "Approve the remediation order.": "remediation 순서를 승인한다.",
    "Approve GAP-FIX-001.": "GAP-FIX-001을 승인한다.",
    "Keep Graph-Guided and Agentic conditional on EXP-01 and EXP-03.": "Graph-Guided와 Agentic은 EXP-01·EXP-03 결과에 따라 조건부로 유지한다.",
    "Architecture substantially implemented; most frozen INNER paths executed.": "아키텍처는 대부분 구현됐고 주요 frozen INNER 경로가 실행됐다.",
    "Explicit integrity audits exist for frozen D0, D1, D2 V1, and D2 V2 INNER results; this checks result custody and arithmetic, not performance validity.": "D0·D1·D2 V1·D2 V2 INNER 결과의 명시적 무결성 점검이 있으며, 이는 custody와 산술을 확인할 뿐 성능 타당성을 뜻하지 않는다.",
    "Partial and incomplete; major performance and contribution hypotheses remain unvalidated or unsupported.": "부분적이고 미완료다. 주요 성능·기여 가설은 미검증이거나 현재 근거로 지원되지 않는다.",
    "Fresh-machine independent reproduction remains pending.": "새 환경 독립 재현(Fresh-machine Reproduction)은 아직이다.",
    "Held-out generalization remains unconfirmed because no OUTER scientific result exists.": "OUTER 과학 결과가 없어 held-out 일반화는 미확인이다.",
    "Only narrow implementation or contract claims are supported; claims.csv is the authoritative claim view.": "좁은 구현·계약 주장만 지원되며 `claims.csv`가 공식 주장 기준이다.",
    "ARCH-011 completed; prospective remediation decision next": "ARCH-011 완료; 다음은 향후 remediation 결정",
    "GAP-001 — choose and version the final Rule/verifier/runtime authority": "GAP-001 — 최종 Rule/verifier/runtime authority를 선택하고 version을 고정한다.",
    "GAP-002 — add a durable D1 prediction-before-label byte/state gate": "GAP-002 — label 접근 전 durable D1 prediction byte/state gate를 추가한다.",
    "GAP-003 — freeze validation, policy-selection, and final held-out roles": "GAP-003 — validation·policy 선택·최종 held-out 역할을 사전에 고정한다.",
    "GAP-004 — freeze event-unit scope, dependence interpretation, and analysis policy": "GAP-004 — event-unit 범위·의존성 해석·분석 policy를 사전에 고정한다.",
    "INTERPRETABLE_WITH_QUALIFICATIONS; INVALIDATED_ARTIFACTS=0": "조건을 명시하면 해석 가능; 무효화된 artifact 0개",
    "Preserve PILOT V1; all remediated future work is VALIDATION V2.": "PILOT V1은 그대로 보존하고, remediation을 적용한 향후 작업은 모두 VALIDATION V2로 분리한다.",
    "BEFORE_REMEDIATION_READ_ONLY": "remediation 전 읽기 전용 점검",
    "READY_WITH_CONDITIONS": "조건부 진행 가능 (READY_WITH_CONDITIONS)",
    "NOT_REQUIRED": "현재 필요하지 않음 (NOT_REQUIRED)",
    "Normal construction is label-blind. D0 and D2 persist predictions before labels; D1 constructs a label-blind hashed object first but lacks a durable file-before-label gate.": "정상 근거 구성은 label-blind다. D0와 D2는 label 접근 전에 prediction을 durable하게 저장하지만, D1은 label-blind hash object를 먼저 만들고도 file 기반 durable gate는 없다.",
    "NO VERIFIED LEAKAGE FOUND; two high qualifications are the D1 durable-ordering gap and test1-informed D2 V2 design.": "확인된 정보 누출은 없다. 다만 D1 durable ordering gap과 test1-informed D2 V2 설계라는 두 가지 중요한 조건이 남아 있다.",
    "Normal construction is label-blind. PILOT V1 D1 retains its weaker in-memory boundary; VALIDATION V2 now requires durable no-overwrite prediction freeze replay one-shot label lease and post-label byte verification.": "정상 근거 구성은 label-blind다. PILOT V1 D1의 약한 in-memory 경계는 역사적 조건으로 유지하고, VALIDATION V2는 no-overwrite prediction freeze·replay·one-shot label lease·label 이후 byte 확인을 요구한다.",
    "NO VERIFIED LEAKAGE FOUND. PILOT V1 retains its documented D1 custody qualification; GAP-FIX-002 closes the prospective VALIDATION V2 custody gap. D2 V2 remains test1-informed development.": "확인된 정보 누출은 없다. PILOT V1의 D1 custody 조건은 유지되며 GAP-FIX-002가 향후 VALIDATION V2 custody gap을 닫았다. D2 V2는 여전히 test1-informed development다.",
    "INNER development / 14 contiguous attack-event-unit pilot; statistical independence not established; not final validation": "INNER 개발용 14개 연속 attack-event unit 예비 실험이다. 통계적 독립성은 확립되지 않았고 최종 검증이 아니다.",
    "One custody-level file access attempt was rejected before byte read; held-out result unavailable.": "custody 단계의 file 접근 시도 1회가 byte read 전에 거부됐으며 held-out 결과는 없다.",
    "86 dataset points; 37-feature P1 frame; purpose-specific role and runtime subsets": "전체 86개 dataset point 중 37-feature P1 frame을 사용하며, 목적별 role·runtime subset을 둔다.",
    "candidate discovery, relation fit, normal numeric authority, D0 fit": "후보 탐색·관계 fit·정상 numeric authority·D0 fit",
    "independent file-local fit evidence paired with train1": "train1과 짝을 이루는 독립 file-local fit 근거",
    "one-way relation confirmation and D0 threshold calibration": "단방향 관계 확인과 D0 threshold calibration",
    "normal guard and D0 sanity evaluation": "정상 guard와 D0 sanity 평가",
    "INNER development predictions and post-freeze label metrics": "INNER 개발 prediction과 freeze 이후 label metric",
    "custody-blocked OUTER; no feature bytes, labels, predictions, metrics, or outcome": "custody에서 차단된 OUTER이며 feature byte·label·prediction·metric·outcome이 없다.",
    "12 ordered sources x 12 ordered targets = 144 directed pairs": "순서가 있는 source 12개 × target 12개 = 방향성 pair 144개",
    "unscored provenance-preserving set union of 47 unique pairs": "재점수화 없이 근거 출처 추적(Provenance)을 보존한 고유 pair 47개의 합집합",
    "reviewed P1 metadata and public physical graph": "점검된 P1 metadata와 공개 physical graph",
    "M1/M2/M3 deterministic domain-prior ranking": "M1/M2/M3 결정론적 domain-prior 순위화",
    "metadata-supported pair candidates": "metadata 근거가 있는 pair 후보",
    "file-local first-difference lagged Pearson stability": "file-local 1차 차분 지연 Pearson 안정성",
    "directional lagged-association candidates": "방향성 지연 연관 후보",
    "next-value prediction plus embedding-cosine learned graph": "다음 값 예측과 embedding-cosine 학습 graph",
    "normal train1/train2 full 37-node context": "normal train1/train2의 전체 37-node context",
    "learned-graph candidate edges": "학습 graph 후보 edge",
    "Candidate discovery proposes relationships. It does not establish causal or final temporal relations.": "후보 탐색은 관계 후보를 제안할 뿐 인과관계나 최종 시간 관계를 확립하지 않는다.",
    "Normal repeated response is not causal proof. All 420 shared numeric values matched E1 in the focused audit, but historical and runtime authority/reference identities remain separate.": "정상 구간의 반복 반응은 인과 증명이 아니다. 집중 점검에서 공유 numeric value 420개가 모두 E1과 일치했지만, historical authority와 runtime authority/reference identity는 별개다.",
    "Rule-construction acceptance is not detection performance, canonical portfolio membership, or runtime authorization.": "Rule 구성 단계의 acceptance는 탐지 성능·canonical portfolio 포함·실행 권한(Runtime Authorization)을 뜻하지 않는다.",
    "Bounded verifier-feedback capability is implemented. The frozen cohort exercised no revise or retrieve action, so no feedback improvement was demonstrated.": "제한된 verifier-feedback 기능은 구현됐다. 고정 cohort에서 revise·retrieve action이 0회였으므로 feedback 개선 효과는 입증되지 않았다.",
    "The frozen D1 runtime is label-blind, fixed-rule, and LLM-free; this does not make its trace canonical, its prediction durably pre-label persisted, or its explanation human-validated.": "고정 D1 runtime은 label-blind·fixed-rule·LLM-free다. 그렇다고 trace가 canonical이거나 prediction이 label 전에 durable하게 저장됐거나 설명이 사람 대상 검증을 마쳤다는 뜻은 아니다.",
    "D0 is a simple reference detector. SPE is not probability; FAR/hour is not point FPR; the 14-event result is pilot evidence only.": "D0는 단순 기준 detector다. SPE는 확률이 아니고 FAR/hour는 point FPR이 아니며 14-unit 결과는 예비 근거일 뿐이다.",
    "V2 is test1-informed development, not independent confirmation. Current V1/V2 results do not establish that Detector-plus-Rule is generally useless.": "V2는 test1-informed development이며 독립 확인이 아니다. 현재 V1/V2 결과로 Detector+Rule이 일반적으로 쓸모없다고 결론 내릴 수 없다.",
    "NOT_ESTABLISHED": "확립되지 않음 (NOT_ESTABLISHED)",
    "SEMANTICALLY_EQUIVALENT": "의미상 동등 (SEMANTICALLY_EQUIVALENT)",
    "FAIR_WITH_LIMITATIONS": "한계를 전제로 비교 가능 (FAIR_WITH_LIMITATIONS)",
    "STRONG_SUPPORTED": "강한 근거로 지원됨 (STRONG_SUPPORTED)",
    "PARTIAL_MODERATE": "부분적으로 가능 (PARTIAL_MODERATE)",
    "NOT_DEMONSTRATED_PARTIALLY_PREPARED": "아직 시연되지 않았고 일부 준비됨",
    "NOT_DEMONSTRATED_BLOCKED": "아직 시연되지 않았고 현재 차단됨",
    "PARTIAL_CODE_ONLY_FULL_SCIENCE_UNAVAILABLE": "코드 범위에서만 부분 가능하며 전체 과학 재현은 불가",
    "UNAVAILABLE": "결과 없음 (UNAVAILABLE)",
    "NOT_RETRYABLE_BY_PROTOCOL": "기존 protocol에서 재시도 불가",
    "STUDY_DESIGN_REQUIRED": "새 연구 설계 필요",
    "PRESERVED_IMMUTABLE_WITH_EXISTING_QUALIFICATIONS": "기존 조건을 유지한 채 불변 보존",
    "SEPARATE_PROSPECTIVE_METHOD_CONFIG_AUTHORITY_ENVIRONMENT_AND_EXPERIMENT_IDENTITIES": "향후 method·config·authority·environment·experiment identity를 별도 version으로 분리",
    "after authority/dependency/schema/entrypoint remediation and before held-out access": "authority·dependency·schema·entrypoint remediation 후, held-out 접근 전에 수행",
}


def _ko_text(value: object) -> str:
    """Translate only reviewed display copy while preserving unknown registry tokens verbatim."""

    text = str(value)
    return KOREAN_TEXT.get(text, text)


def _badge(status: str, label: str | None = None) -> str:
    displayed = label or STATUS_DISPLAY_LABELS.get(status, status)
    return f'<span class="badge {_badge_class(status)}">{_escape(displayed)}</span>'


def _cards(
    rows: Sequence[Mapping[str, str]],
    *,
    title_key: str,
    id_key: str,
    status_key: str,
    body_keys: Sequence[tuple[str, str]],
    status_labels: Mapping[str, str] | None = None,
    localized_copy: Mapping[str, tuple[str, str]] | None = None,
) -> str:
    rendered: list[str] = []
    for row in rows:
        status = row[status_key]
        localized = (localized_copy or {}).get(row[id_key])
        displayed_title = localized[0] if localized else row[title_key]
        displayed_summary = localized[1] if localized else ""
        searchable = " ".join(str(value) for value in row.values()).lower()
        details = "".join(
            f'<div class="card-field"><dt>{_escape(label)}</dt><dd>{_escape(row[key])}</dd></div>'
            for label, key in body_keys
        )
        rendered.append(
            "\n".join(
                (
                    f'<article class="registry-card" data-status="{_escape(status)}" data-search="{_escape(searchable)}">',
                    '<div class="card-heading">',
                    f'<div><p class="eyebrow">{_escape(row[id_key])}</p><h3>{_escape(displayed_title)}</h3></div>',
                    _badge(status, (status_labels or {}).get(status)),
                    "</div>",
                    f'<p class="card-summary">{_escape(displayed_summary)}</p>' if displayed_summary else "",
                    '<details class="registry-source"><summary>registry 원문 보기</summary>',
                    f'<p><strong>원문 제목:</strong> {_escape(row[title_key])}</p><dl>{details}</dl>',
                    "</details>",
                    "</article>",
                )
            )
        )
    return "\n".join(rendered)


def _bullet_list(items: Iterable[object], *, empty: str = "No items recorded.") -> str:
    values = list(items)
    if not values:
        return f'<p class="empty-state">{_escape(empty)}</p>'
    return "<ul>" + "".join(f"<li>{_escape(item)}</li>" for item in values) + "</ul>"


def _source_marker(state: Mapping[str, Any], digest: str) -> str:
    return (
        f'RCC_GENERATED registry_version={state["registry_version"]} '
        f'registry_digest={digest} authority={state["scientific_authority"]["commit"]}'
    )


def _render_dashboard_v1(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    authority = state["scientific_authority"]
    checkout = state["non_authoritative_checkout"]
    unresolved = [row for row in data["decisions"] if row["status"] == "OPEN"]
    current_events = sorted(
        (row for row in data["timeline"] if row["date_precision"] == "DAY"),
        key=lambda row: (row["date"], row["event_id"]),
        reverse=True,
    )
    all_statuses = sorted(
        {row["status"] for group in (data["components"], data["experiments"], data["claims"]) for row in group}
        | {row["severity"] for row in data["risks"]}
        | {"CRITICAL"}
    )
    status_options = "".join(
        f'<option value="{_escape(status)}">{_escape(STATUS_DISPLAY_LABELS.get(status, status))}</option>'
        for status in all_statuses
    )

    component_cards = _cards(
        data["components"],
        title_key="name",
        id_key="component_id",
        status_key="status",
        body_keys=(("연구 역할", "research_role"), ("기록된 lifecycle token", "lifecycle_stage"), ("다음 조치", "next_action")),
        status_labels=COMPONENT_STATUS_LABELS,
        localized_copy=COMPONENT_CARD_COPY,
    )
    experiment_cards = _cards(
        data["experiments"],
        title_key="name",
        id_key="experiment_id",
        status_key="status",
        body_keys=(("연구 질문", "research_question"), ("현재 근거", "current_evidence"), ("한계", "limitations"), ("다음 조치", "next_action")),
        status_labels=EXPERIMENT_STATUS_LABELS,
        localized_copy=EXPERIMENT_CARD_COPY,
    )
    claim_cards = _cards(
        data["claims"],
        title_key="claim_text",
        id_key="claim_id",
        status_key="status",
        body_keys=(("사용 가능한 문구", "allowed_wording"), ("피해야 할 문구", "forbidden_wording"), ("추가 검증", "validation_needed")),
        localized_copy=CLAIM_CARD_COPY,
    )
    risk_cards = _cards(
        data["risks"],
        title_key="description",
        id_key="risk_id",
        status_key="severity",
        body_keys=(("상태", "status"), ("발생 가능성", "likelihood"), ("근거", "evidence"), ("완화 조치", "mitigation"), ("담당", "owner")),
        localized_copy=RISK_CARD_COPY,
    )
    decision_content = _cards(
        unresolved,
        title_key="title",
        id_key="decision_id",
        status_key="status",
        body_keys=(("결정 내용", "decision"), ("필요한 이유", "reason")),
        localized_copy=DECISION_CARD_COPY,
    ) if unresolved else '<p class="empty-state">현재 미결정 사용자 항목이 없습니다.</p>'
    event_by_id = {row["event_id"]: row for row in data["timeline"]}
    history_events = [event_by_id[event_id] for event_id in data["history"]["dashboard_event_ids"]]
    history_markup = "".join(
        f'<article class="timeline-item"><time>{_escape(row["date"])}</time><div><strong>{_escape(HISTORY_CARD_COPY.get(row["event_id"], (row["title"], row["summary"]))[0])}</strong><p>{_escape(HISTORY_CARD_COPY.get(row["event_id"], (row["title"], row["summary"]))[1])}</p><details class="registry-source"><summary>registry 원문 보기</summary><small>{_escape(row["title"])} · {_escape(row["source"])} · {_escape(row["notes"])}</small></details></div>{_badge(row["status"])}</article>'
        for row in history_events
    )
    active_decisions = [row for row in data["decisions"] if row["status"] in {"ACTIVE", "CONDITIONAL"}]
    key_decisions_markup = "".join(
        f'<li><strong>{_escape(row["decision_id"])} · {_escape(DECISION_CARD_COPY.get(row["decision_id"], (row["title"], row["current_relevance"]))[0])}</strong><span>{_escape(DECISION_CARD_COPY.get(row["decision_id"], (row["title"], row["current_relevance"]))[1])}</span></li>'
        for row in active_decisions[-8:]
    )
    recent = current_events[:3]
    recent_markup = "".join(
        f'<article class="timeline-item"><time>{_escape(row["date"])}</time><div><strong>{_escape(HISTORY_CARD_COPY.get(row["event_id"], (row["title"], row["summary"]))[0])}</strong><p>{_escape(HISTORY_CARD_COPY.get(row["event_id"], (row["title"], row["summary"]))[1])}</p><details class="registry-source"><summary>registry 원문 보기</summary><small>{_escape(row["title"])} · {_escape(row["summary"])}</small></details></div>{_badge(row["status"])}</article>'
        for row in recent
    )
    phases = "".join(
        f'<li class="phase-step {"phase-current" if phase == state["current_phase"] else ""}">{_escape(PHASE_DISPLAY_LABELS.get(phase, phase))}</li>'
        for phase in state["phase_progression"]
    )
    components = data["components"]
    component_counts = {
        "전체": len(components),
        "구현 완료": sum(row["status"].startswith("IMPLEMENTED") for row in components),
        "실제 실행 완료": sum(row["executed"] == "true" for row in components),
        "근거 점검 완료 (Evidence-reviewed)": sum(row["audited"] == "true" for row in components),
        "독립 재현 완료": sum(row["reproduced"] == "true" for row in components),
    }
    experiment_counts = {
        "전체": len(data["experiments"]),
        "예비 실험": sum(row["status"] == "EXECUTED_AUDITED_PILOT" for row in data["experiments"]),
        "미검증": sum(row["status"] == "IMPLEMENTED_NOT_EXECUTED" for row in data["experiments"]),
        "조건부": sum(row["status"] == "DESIGN_ONLY" for row in data["experiments"]),
    }
    claim_counts = {
        "구현 근거로 지원됨": sum(row["status"] == "SUPPORTED_IMPLEMENTATION" for row in data["claims"]),
        "예비 실험 수준": sum(row["status"] == "PILOT_ONLY" for row in data["claims"]),
        "미검증": sum(row["status"] == "UNVALIDATED" for row in data["claims"]),
        "현재 근거로 지원되지 않음": sum(row["status"] == "NOT_SUPPORTED" for row in data["claims"]),
        "조건부": sum(row["status"] == "CONDITIONAL" for row in data["claims"]),
    }
    risk_counts = {
        "치명적·높음": sum(row["severity"] in {"CRITICAL", "HIGH"} for row in data["risks"]),
        "중간": sum(row["severity"] == "MEDIUM" for row in data["risks"]),
        "낮음": sum(row["severity"] == "LOW" for row in data["risks"]),
    }
    summaries = (("구현 구성요소", component_counts), ("실험", experiment_counts), ("연구 주장", claim_counts), ("위험", risk_counts))
    summary_markup = "".join(
        '<article class="summary-card"><h3>' + _escape(title) + "</h3><dl>" + "".join(
            f'<div><dt>{_escape(label)}</dt><dd>{count}</dd></div>' for label, count in counts.items()
        ) + "</dl></article>"
        for title, counts in summaries
    )
    component_by_id = {row["component_id"]: row for row in components}
    architecture_markup = "".join(
        "\n".join((
            f'<details class="architecture-detail" id="arch-{_slug(row["section_id"])}">',
            f'<summary><span>{_escape(row["section_id"])}</span><strong>{_escape(ARCHITECTURE_DISPLAY_LABELS.get(row["section_id"], row["name"]))}</strong></summary>',
            '<dl class="architecture-contract">',
            f'<div><dt>역할</dt><dd>{_escape(row["role"])}</dd></div>',
            f'<div><dt>입력</dt><dd>{_escape(row["input"])}</dd></div>',
            f'<div><dt>출력</dt><dd>{_escape(row["output"])}</dd></div>',
            f'<div><dt>코드</dt><dd><code>{_escape(row["code"])}</code></dd></div>',
            f'<div><dt>실행 여부</dt><dd>{_badge("IMPLEMENTED_EXECUTED" if row["executed"] == "true" else "UNKNOWN", "예" if row["executed"] == "true" else "아니오")}</dd></div>',
            f'<div><dt>고정 결과 사용 여부</dt><dd>{_badge("AUDITED" if row["frozen_result_used"] == "true" else "DESIGN_ONLY", "예" if row["frozen_result_used"] == "true" else "아니오")}</dd></div>',
            f'<div><dt>검증 상태</dt><dd>{_escape(row["validation_state"])}</dd></div>',
            f'<div><dt>다음 심층 점검</dt><dd>{_escape(row["next_deep_review"])}</dd></div>',
            '</dl></details>',
        ))
        for row in data["architecture_details"]
    )
    governance = state["data_governance"]
    split_markup = "".join(
        '<article class="summary-card"><p class="eyebrow">'
        + _escape({"NORMAL FIT": "정상 fit", "CONFIRMATION / CALIBRATION": "확인·보정", "SANITY": "정상 sanity", "PILOT EVALUATION": "예비 평가", "HELD-OUT / UNAVAILABLE": "held-out·결과 없음"}.get(item["badge"], item["badge"]))
        + "</p><h3>"
        + _escape(item["id"])
        + "</h3><p>"
        + _escape(_ko_text(item["role"]))
        + "</p></article>"
        for item in governance["splits"]
    )
    discovery = state["candidate_discovery"]
    discovery_markup = "".join(
        '<article class="summary-card"><p class="eyebrow">'
        + _escape(arm["id"])
        + "</p><h3>"
        + _escape(_ko_text(arm["method"]))
        + "</h3><dl>"
        + f'<div><dt>입력</dt><dd>{_escape(_ko_text(arm["input"]))}</dd></div>'
        + f'<div><dt>출력</dt><dd>{_escape(_ko_text(arm["output"]))}</dd></div>'
        + f'<div><dt>TOP-K</dt><dd>{_escape(arm["top_k"])}</dd></div>'
        + f'<div><dt>고정 실행 여부</dt><dd>{_badge("AUDITED", "예")}</dd></div>'
        + f'<div><dt>과학적 검증 여부</dt><dd>{_badge("UNVALIDATED")}</dd></div>'
        + "</dl></article>"
        for arm in discovery["arms"]
    )
    relation = state["relation_numeric_authority"]
    construction = state["rule_construction_authority"]
    verifier = state["verifier_common42_authority"]
    runtime = state["runtime_trace_explanation"]
    d0 = state["d0_detector"]
    d1 = state["d1_evaluation"]
    d2 = state["d2_fusion"]
    metrics = state["metric_integrity"]
    readiness = state["pre_validation_readiness"]
    outer = state["outer_reproducibility"]
    gate_markup = "".join(
        '<article class="summary-card"><p class="eyebrow">'
        + _escape(experiment)
        + '</p><h3>'
        + _escape(STATUS_DISPLAY_LABELS.get(status, status))
        + '</h3></article>'
        for experiment, status in readiness["experiment_gates"].items()
    )
    construction_arms = (
        ("T0", "아니오", "0", "없음", "0", "42/42 proposal 승인"),
        ("T1", "예", "1", "없음", "0", "42/42 proposal 승인"),
        ("T1-B", "예", "3회 고정", "feedback 없음", "0", "42/42 proposal 선택"),
        ("T2", "예", "최대 3회", "REVISE / RETRIEVE", "0", "39/42 승인; 3 no_rule"),
    )
    construction_markup = "".join(
        '<article class="summary-card"><p class="eyebrow">'
        + _escape(arm)
        + "</p><dl>"
        + f'<div><dt>LLM 사용</dt><dd>{_escape(llm)}</dd></div>'
        + f'<div><dt>호출 예산</dt><dd>{_escape(budget)}</dd></div>'
        + f'<div><dt>피드백 기능</dt><dd>{_escape(feedback)}</dd></div>'
        + f'<div><dt>실제 피드백</dt><dd>{_escape(observed)}</dd></div>'
        + f'<div><dt>고정 결과</dt><dd>{_escape(outcome)}</dd></div>'
        + '<div><dt>과학적 주장 범위</dt><dd>구현 / 예비 실험 수준</dd></div>'
        + "</dl></article>"
        for arm, llm, budget, feedback, observed, outcome in construction_arms
    )
    marker = _source_marker(state, digest)

    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="rcc-registry-version" content="{_escape(state['registry_version'])}">
  <meta name="rcc-registry-digest" content="{digest}">
  <meta name="rcc-scientific-authority" content="{_escape(authority['commit'])}">
  <!-- {marker} -->
  <title>연구 통제 센터 (Research Control Center)</title>
  <link rel="stylesheet" href="assets/rcc.css">
</head>
<body>
  <a class="skip-link" href="#main">본문으로 건너뛰기</a>
  <header class="hero">
    <div class="hero-inner">
      <p class="eyebrow">RESEARCH CONTROL CENTER · RCC {_escape(state['rcc_version'])}</p>
      <h1>근거와 한계를 함께 보는 논문 연구 현황</h1>
      <p class="hero-summary">아키텍처와 예비 실행은 완료됐지만, 확대 평가·독립 재현·held-out 일반화는 아직 완료되지 않았습니다.</p>
      <aside class="principle">구현 완료, 실행 완료, 결과 무결성 확인, 과학적 검증, 재현성, 일반화는 서로 다른 상태입니다.</aside>
      <aside class="principle">현재 성능 결과는 test1의 14개 연속 공격 구간 단위(contiguous attack-event units)를 이용한 예비 실험 결과이며, 최종 성능 검증 결과가 아닙니다.</aside>
      <div class="authority-strip">
        <div><span>공식 과학 기준 (Scientific authority)</span><strong title="{_escape(authority['commit'])}">{_escape(authority['ref'])} @ {_short_commit(authority['commit'])}</strong></div>
        <div class="authority-warning"><span>현재 과거 checkout</span><strong title="{_escape(checkout['commit'])}">{_escape(checkout['ref'])} @ {_short_commit(checkout['commit'])} · 공식 기준 아님</strong></div>
      </div>
      <ol class="phase-track" aria-label="연구 단계">{phases}</ol>
    </div>
  </header>

  <nav class="section-nav" aria-label="대시보드 메뉴">
    <a href="#current-state">현재 연구 상태</a><a href="#my-tasks">내가 해야 할 일</a><a href="#decisions">결정이 필요한 사항</a>
    <a href="#history">연구 진행 이력</a><a href="#architecture">전체 아키텍처</a><a href="#components">구현 현황</a>
    <a href="#experiments">실험 현황</a><a href="#claims">연구 주장과 근거</a><a href="#risks">위험 및 점검사항</a>
    <a href="#source-authority">공식 기준 코드·근거</a><a href="#outer-reproducibility">재현성</a>
    <a href="#pre-validation-readiness">본격 검증 준비 현황</a><a href="#recent-change">최근 변경사항</a>
    <a href="#data-governance">데이터</a><a href="#candidate-discovery">후보 탐색</a><a href="#relation-numeric">관계·수치 권한</a>
    <a href="#rule-construction">규칙 구성</a><a href="#verifier-common42">검증기(Verifier)</a><a href="#runtime-trace-explanation">실행·추적(Runtime·Trace)</a>
    <a href="#d0-detector">D0</a><a href="#d1-evaluation">D1</a><a href="#d2-fusion">D2</a><a href="#metrics-results">성능 지표(Metrics)</a>
  </nav>

  <main id="main">
    <section id="current-state" class="section panel-feature">
      <div class="section-heading"><p class="eyebrow">01</p><h2>현재 연구 상태</h2></div>
      <div class="two-column"><div><h3>현재 근거로 확인된 것</h3>{_bullet_list(_ko_text(item) for item in state['established_facts'])}</div><div><h3>아직 확인되지 않은 것</h3>{_bullet_list(_ko_text(item) for item in state['not_established'])}</div></div>
      <div class="status-snapshot">
        <div><span>구현 상태</span><strong>{_escape(_ko_text(state['research_status_summary']['engineering']))}</strong></div>
        <div><span>결과 무결성</span><strong>{_escape(_ko_text(state['research_status_summary']['result_integrity']))}</strong></div>
        <div><span>과학적 검증</span><strong>{_escape(_ko_text(state['research_status_summary']['scientific_validation']))}</strong></div>
        <div><span>재현성</span><strong>{_escape(_ko_text(state['research_status_summary']['reproducibility']))}</strong></div>
        <div><span>일반화</span><strong>{_escape(_ko_text(state['research_status_summary']['generalization']))}</strong></div>
        <div><span>연구 주장</span><strong>{_escape(_ko_text(state['research_status_summary']['claims']))}</strong></div>
      </div>
      <div class="summary-grid">{summary_markup}</div>
      <p class="summary-note">이 개수는 하나의 연구 완료율이 아닙니다. 근거 점검 완료(Evidence-reviewed)는 source 또는 evidence 상태를 확인했다는 뜻이며, 과학적 성능 검증과 결과 무결성 확인은 별도입니다. 연구 주장 개수는 <code>claims.csv</code>에서만 가져옵니다.</p>
      <aside class="principle">구현, 실행, 근거 점검, 결과 무결성, 독립 재현, 과학적 검증은 서로 다른 상태입니다.</aside>
    </section>

    <section id="pre-validation-readiness" class="section panel-history">
      <div class="section-heading"><p class="eyebrow">GAP-000</p><h2>본격 검증 준비 현황</h2></div>
      <p class="architecture-flow">120개 원시 finding → 19개 root issue → 조치 분류·우선순위 → 실험 gate</p>
      <div class="status-snapshot">
        <div><span>주 조치 분류: 확대 검증 전 수정</span><strong>{readiness['disposition_counts']['P0_FIX_BEFORE_EXPANDED_VALIDATION']}</strong></div>
        <div><span>주 조치 분류: 특정 실험 전 수정</span><strong>{readiness['disposition_counts']['P1_FIX_BEFORE_SPECIFIC_EXPERIMENT']}</strong></div>
        <div><span>실험 설계 요구사항</span><strong>{readiness['disposition_counts']['EXPERIMENT_DESIGN_REQUIREMENT']}</strong></div>
        <div><span>엔지니어링 강화</span><strong>{readiness['disposition_counts']['ENGINEERING_HARDENING']}</strong></div>
        <div><span>긴급도 P0 / P1</span><strong>{readiness['priority_counts']['P0']} / {readiness['priority_counts']['P1']}</strong></div>
        <div><span>긴급도 P2 / P3</span><strong>{readiness['priority_counts']['P2']} / {readiness['priority_counts']['P3']}</strong></div>
      </div>
      <div class="two-column"><div><h3>긴급도 P0 — 구현·계약</h3>{_bullet_list(_ko_text(item) for item in readiness['p0_global_fixes'])}</div><div><h3>긴급도 P0 — 실험 설계</h3>{_bullet_list(_ko_text(item) for item in readiness['p0_design_gates'])}</div></div>
      <h3>실험 gate</h3><div class="summary-grid">{gate_markup}</div>
      <aside class="principle">기존 예비 실험: {_escape(_ko_text(readiness['past_pilot']))}. {_escape(_ko_text(readiness['scientific_versioning']))}</aside>
      <aside class="principle">이 화면은 triage 지도이며 완료율이 아니고, 실험 실행 권한도 아닙니다.</aside>
      <p><a href="../architecture/gap_000_pre_validation/GAP_000_REPORT.md">triage 보고서 열기</a> · <a href="../architecture/gap_000_pre_validation/GAP_000_REMEDIATION_MATRIX.csv">remediation matrix</a> · <a href="../architecture/gap_000_pre_validation/GAP_000_EXPERIMENT_GATES.csv">실험 gate</a> · <a href="../architecture/gap_000_pre_validation/GAP_000_MINIMUM_THESIS_PATH.md">최소 논문 경로</a></p>
      <p><strong>다음:</strong> {_escape(state['exact_next_task'])} · {_escape(_ko_text(readiness['arch011_position']))}</p>
    </section>

    <section id="relation-numeric" class="section panel-history">
      <div class="section-heading"><p class="eyebrow">RELATION</p><h2>관계 프로파일링과 수치 권한 (Numeric Authority)</h2></div>
      <div class="status-snapshot">
        <div><span>후보 pair</span><strong>{relation['candidate_pairs']}</strong></div>
        <div><span>프로파일링 기회</span><strong>{relation['directional_opportunities']}</strong></div>
        <div><span>fit 근거 통과</span><strong>{relation['fit_supported_pair_contexts']} contexts / {relation['fit_supported_directions']} directions</strong></div>
        <div><span>최종 확인</span><strong>{relation['confirmed_pair_contexts']} contexts / {relation['confirmed_directions']} relations</strong></div>
        <div><span>구성 단계 결속</span><strong>462 references</strong></div>
        <div><span>runtime 결속</span><strong>420 references + descriptor horizon</strong></div>
      </div>
      <div class="two-column">
        <div><h3>프로파일링과 확인</h3><dl class="architecture-contract">
          <div><dt>source split</dt><dd>{_escape(relation['profiling_splits'])}</dd></div>
          <div><dt>source event</dt><dd>source의 앞·뒤 5-row median, 정상 근거 threshold·stability, 동일 source refractory, 전체 source isolation</dd></div>
          <div><dt>target response</dt><dd>고정된 5개 row horizon 중 하나에서 5-row baseline과 3-row response median을 비교</dd></div>
          <div><dt>확인 단계</dt><dd>normal train3에서 identity와 parameter를 고정한 채 확인하며 재탐색·재조정하지 않음</dd></div>
        </dl></div>
        <div><h3>수치 보관·결속</h3><dl class="architecture-contract">
          <div><dt>구성 단계</dt><dd>42 relations × 구성 전용 reference 11개 = 462 bindings</dd></div>
          <div><dt>runtime</dt><dd>별도 version의 normal-only MAIN registry: 42 relations × 10 roles = 420 records; 선택 horizon은 canonical descriptor에 유지</dd></div>
          <div><dt>두 권한의 관계</dt><dd>{_escape(relation['authority_relationship'])}</dd></div>
          <div><dt>근거 추적 (Traceability)</dt><dd>{_escape(relation['traceability'])}</dd></div>
        </dl></div>
      </div>
      <aside class="principle">{_escape(_ko_text(relation['warning']))}</aside>
      <p><a href="../architecture/03_relation_and_numeric/ARCH_003_REPORT.md">관계·수치 심층 점검 열기</a> · <a href="../architecture/03_relation_and_numeric/ARCH_003_CONSTRUCTION_RUNTIME_AUTHORITY.md">구성/runtime authority</a> · <a href="../architecture/03_relation_and_numeric/ARCH_003_MISMATCHES.md">관계·수치 불일치</a></p>
      <p><strong>다음 심층 점검:</strong> {_escape(_ko_text(relation['next_deep_review']))}</p>
    </section>

    <section id="rule-construction" class="section panel-feature">
      <div class="section-heading"><p class="eyebrow">RULE</p><h2>근거에 결속된 규칙 구성</h2></div>
      <p class="architecture-flow">근거 묶음(Evidence Pack) → 닫힌 Rule DSL → T0 / T1 / T1-B / T2 → 결정론적 validity handoff</p>
      <div class="two-column"><div><h3>입력되는 근거</h3><p>normal-only confirmed relation 42개, 고정 horizon, 승인된 numeric value/reference 10개, provenance identity, 제한된 process metadata</p></div><div><h3>의도적으로 제외되는 정보</h3><p>raw HAI row·label·attack·test/utility outcome·후보 arm 성능·D0/D1 결과·runtime authority</p></div></div>
      <div class="summary-grid">{construction_markup}</div>
      <aside class="principle">{_escape(_ko_text(construction['warning']))}</aside>
      <aside class="principle">{_escape(_ko_text(construction['agentic_claim']))}</aside>
      <p><a href="../architecture/04_rule_construction/ARCH_004_REPORT.md">규칙 구성 심층 점검 열기</a> · <a href="../architecture/04_rule_construction/ARCH_004_RULE_DSL.md">Rule DSL 경계</a> · <a href="../architecture/04_rule_construction/ARCH_004_AGENTIC_CLAIM_BOUNDARY.md">Agentic 주장 경계</a></p>
      <p><strong>다음 심층 점검:</strong> {_escape(_ko_text(construction['next_deep_review']))}</p>
    </section>

    <section id="verifier-common42" class="section panel-history">
      <div class="section-heading"><p class="eyebrow">VERIFIER</p><h2>결정론적 verifier·COMMON-42·실행 권한</h2></div>
      <p class="architecture-flow">Proposal → Task Validity → Executable Equivalence → COMMON-42 V4 Portfolio → Evaluator Authority → Committed D1 Grant</p>
      <div class="status-snapshot">
        <div><span>Canonical Verifier</span><strong>결정론적 20단계</strong></div>
        <div><span>task와 canonical 관계</span><strong>부분적으로 겹치지만 동등하지 않음</strong></div>
        <div><span>COMMON-42</span><strong>42 V4 descriptors</strong></div>
        <div><span>T2 utility</span><strong>권한 없음 (NOT AUTHORIZED)</strong></div>
        <div><span>고정 D1 authority</span><strong>V4 + evaluator + committed grant</strong></div>
        <div><span>D1 권장 명칭</span><strong>검증된 관계 규칙 단독 방식 (Verified Relational Rule-only)</strong></div>
      </div>
      <div class="two-column"><div><h3>결속되는 항목</h3><dl class="architecture-contract">
        <div><dt>COMMON-42</dt><dd>T0·T1·T1-B가 공유하는 실행 projection을 나타내며 normal-only runtime numeric authority에 다시 결속된 V4 CanonicalRuleDescriptorV4 42개</dd></div>
        <div><dt>D1 AUTHORITY</dt><dd>고정 D1은 V4 authority·evaluator bundle·private numeric resolver custody·committed one-attempt INNER grant를 사용했고 canonical RuntimeAuthorizationBundleV1은 사용하지 않음</dd></div>
        <div><dt>NUMERIC REBINDING</dt><dd>집중 점검에서 construction/runtime 공유 value 420개가 정확히 일치했으며 runtime reference·authority identity는 별도로 다시 결속되고 horizon은 descriptor에 유지됨</dd></div>
      </dl></div><div><h3>계속 분리되는 항목</h3><dl class="architecture-contract">
        <div><dt>TASK VS CANONICAL</dt><dd>부분적으로 겹치지만 설계상 동등하지 않으며, 고정 construction/D1 경로에는 proposal→DelayedResponseRuleV1 lossless bridge가 추적되지 않음</dd></div>
        <div><dt>T2</dt><dd>T2는 utility authority에서 제외됨. accepted projection 39개는 COMMON counterpart와 맞고 3개는 no_rule이며 COMMON-42 수는 바뀌지 않음</dd></div>
        <div><dt>NO_RULE</dt><dd>고정 T2 세 건은 non-repairable unsupported-variable validity outcome이지만 일반 orchestration은 response·parse·verifier·budget failure를 no_rule로 합칠 수 있음</dd></div>
      </dl></div></div>
      <aside class="principle">Verifier acceptance는 과학적 검증이 아닙니다.</aside>
      <aside class="principle">Verifier acceptance는 실행 권한(Runtime Authorization)과도 다릅니다.</aside>
      <p><a href="../architecture/05_verifier_common42/ARCH_005_REPORT.md">verifier·COMMON-42 심층 점검 열기</a> · <a href="../architecture/05_verifier_common42/ARCH_005_COMMON42.md">COMMON-42 정의</a> · <a href="../architecture/05_verifier_common42/ARCH_005_RUNTIME_AUTHORIZATION.md">실행 권한</a></p>
      <p><strong>다음 심층 점검:</strong> {_escape(_ko_text(verifier['next_deep_review']))}</p>
    </section>

    <section id="runtime-trace-explanation" class="section panel-feature">
      <div class="section-heading"><p class="eyebrow">RUNTIME</p><h2>규칙 실행·추적·설명</h2></div>
      <p class="architecture-flow">COMMON-42 → Rule Evaluation → Task Trace → D1 Prediction → In-memory Freeze → Label Access → Metrics</p>
      <div class="status-snapshot">
        <div><span>runtime authority</span><strong>V4 TASK-SPECIFIC</strong></div>
        <div><span>runtime LLM</span><strong>없음 — FROZEN R0/D1</strong></div>
        <div><span>결정론성</span><strong>{_escape(runtime['determinism'])}</strong></div>
        <div><span>trace authority</span><strong>TASK-SPECIFIC / NON-EQUIVALENT</strong></div>
        <div><span>label 전 durable freeze</span><strong>없음</strong></div>
        <div><span>설명의 인간 대상 검증</span><strong>{_badge("UNVALIDATED")}</strong></div>
      </div>
      <div class="two-column"><div><h3>runtime 계약</h3><dl class="architecture-contract">
        <div><dt>실행 근거 권한 (Authority)</dt><dd>고정 D1은 CanonicalRuleDescriptorV4 42개·고정 V4 evaluator bundle·normal-only Utility V4 numeric resolver·committed one-attempt INNER grant로 이루어진 task-specific V4 authority plane을 사용</dd></div>
        <div><dt>발동 조건 (Trigger)</dt><dd>source 앞·뒤 5-row median, authority-bound magnitude·stability, 방향 일치, 10초 동일-source clustering, ±2초 cross-source isolation</dd></div>
        <div><dt>대상 반응 (Target Response)</dt><dd>5-row target baseline과 descriptor-bound horizon에서 시작하는 3-row median을 비교하며 increase/decrease의 noise 방향을 구분</dd></div>
        <div><dt>허용오차·지속성 (Tolerance / Persistence)</dt><dd>source step threshold·stability tolerance·target noise scale은 runtime authority에서 해석한다. 독립 target-persistence predicate는 없고 source post-window 안정성과 3-row target median이 persistence 유사 역할을 한다.</dd></div>
      </dl></div><div><h3>prediction과 trace 경계</h3><dl class="architecture-contract">
        <div><dt>D1 PREDICTION</dt><dd>opportunity record 6,031개, anomalous rule record 788개, 고유 alarm decision second 630개, downstream metric episode 626개</dd></div>
        <div><dt>예측 고정 (Freeze)</dt><dd>D0/D2보다 약한 in-memory pre-label freeze; durable persistence = 없음</dd></div>
        <div><dt>정답 label 접근 (Label Access)</dt><dd>완성된 label-blind prediction을 검증하고 memory에서 shallow-freeze한 뒤 label-test1을 열며, public prediction byte는 label metric 이후에 저장됨</dd></div>
        <div><dt>실행 추적 (Trace)</dt><dd><code>task039e3_r2r_real_rule_execution_trace_v1</code> terminal hash preimage와 compact record; canonical RuntimeTraceV1과 동등하지 않음</dd></div>
        <div><dt>설명 (Explanation)</dt><dd>결정론적 canonical RuntimeTraceV1 renderer는 있지만 고정 V4 D1은 RuntimeTraceV1을 만들거나 renderer를 호출하지 않았고 고정 D1 explanation artifact도 없음</dd></div>
      </dl></div></div>
      <aside class="principle">{_escape(_ko_text(runtime['warning']))}</aside>
      <p><a href="../architecture/06_runtime_trace_explanation/ARCH_006_REPORT.md">runtime 심층 점검 열기</a> · <a href="../architecture/06_runtime_trace_explanation/ARCH_006_D1_FREEZE_BOUNDARY.md">D1 freeze 경계</a> · <a href="../architecture/06_runtime_trace_explanation/ARCH_006_TRACE_SCHEMA.csv">trace 비교</a> · <a href="../architecture/06_runtime_trace_explanation/ARCH_006_EXPLANATION_RENDERER.md">설명 경계</a></p>
      <p><strong>다음 심층 점검:</strong> {_escape(_ko_text(runtime['next_deep_review']))}</p>
    </section>

    <section id="d0-detector" class="section panel-history">
      <div class="section-heading"><p class="eyebrow">D0</p><h2>PCA-SPE 기준 탐지기</h2></div>
      <p class="architecture-flow">normal train1+train2 → scaler/PCA fit → normal train3 q=.999 보정 → test1 SPE → strict point alarm → durable prediction 고정 → label metric</p>
      <div class="status-snapshot">
        <div><span>연구 역할</span><strong>기준 탐지기 (Reference Detector)</strong></div>
        <div><span>입력</span><strong>순서가 고정된 P1 feature {d0['features']}개</strong></div>
        <div><span>PCA</span><strong>설명 분산 목표 0.95 → k={d0['selected_components']}</strong></div>
        <div><span>보정 (Calibration)</span><strong>train3 · q=.999</strong></div>
        <div><span>prediction</span><strong>test1 · 예비 실험</strong></div>
        <div><span>baseline 수준</span><strong>단순 기준선이며 SOTA가 아님</strong></div>
      </div>
      <div class="two-column"><div><h3>model과 판정</h3><dl class="architecture-contract">
        <div><dt>학습 적합 (Fit)</dt><dd>normal train1 + train2; label 사용 없음</dd></div>
        <div><dt>표준화 (Standardization)</dt><dd>custom NumPy population mean/std, ddof=0, 1e-12 scale floor</dd></div>
        <div><dt>SPE</dt><dd>timestamp별 standardized reconstruction residual 제곱합인 nonnegative float64 score</dd></div>
        <div><dt>임계값 (Threshold)</dt><dd>normal train3 empirical q=0.999 order statistic; interpolation 없음; zero-based q-index 125873</dd></div>
        <div><dt>비교 연산 (Comparator)</dt><dd><code>score &gt; threshold</code>; equality는 non-alarm</dd></div>
      </dl></div><div><h3>고정 pilot과 custody</h3><dl class="architecture-contract">
        <div><dt>label 접근 순서 (Label Order)</dt><dd>{_escape(d0['prediction_freeze'])}</dd></div>
        <div><dt>결정성 (Determinism)</dt><dd>{_escape(d0['determinism'])}</dd></div>
        <div><dt>공격 사건 단위 반응 (Attack Events)</dt><dd>{_escape(d0['attack_event_response'])}</dd></div>
        <div><dt>정상 오경보율 (Normal FAR)</dt><dd>{d0['normal_far_episodes_per_hour']} episodes/hour</dd></div>
        <div><dt>출력 단위 (Output Levels)</dt><dd>point alarm {d0['point_alarms']}개; alarm episode {d0['alarm_episodes']}개; normal false episode {d0['normal_false_alarm_episodes']}개</dd></div>
      </dl></div></div>
      <aside class="principle">{_escape(_ko_text(d0['warning']))}</aside>
      <p><a href="../architecture/07_d0_detector/ARCH_007_REPORT.md">D0 심층 점검 열기</a> · <a href="../architecture/07_d0_detector/ARCH_007_SPE_DEFINITION.md">SPE 정의</a> · <a href="../architecture/07_d0_detector/ARCH_007_FREEZE_BOUNDARY.md">prediction freeze</a> · <a href="../architecture/07_d0_detector/ARCH_007_OUTPUT_LEVELS.md">출력 단위</a></p>
      <p><strong>다음 심층 점검:</strong> {_escape(_ko_text(d0['next_deep_review']))}</p>
    </section>

    <section id="d1-evaluation" class="section panel-feature">
      <div class="section-heading"><p class="eyebrow">D1</p><h2>검증된 관계 규칙 단독 방식 예비 실험</h2></div>
      <p class="architecture-flow">COMMON-42 → label-blind prediction (opportunity 6,031 / anomalous record 788) → label 접근 → episode 626 → metric; static prediction 점검: 고유 alarm second 630</p>
      <div class="status-snapshot">
        <div><span>권장 명칭</span><strong>검증된 관계 규칙 단독 방식 (Verified Relational Rule-only)</strong></div>
        <div><span>예비 event unit</span><strong>{d1['pilot_events']}</strong></div>
        <div><span>공격 사건 단위 재현율 (Attack-event Recall)</span><strong>{d1['attack_events_detected']}/{d1['pilot_events']}</strong></div>
        <div><span>시간당 정상 오경보율 (Normal FAR/hour)</span><strong>{d1['normal_far_episodes_per_hour']}</strong></div>
        <div><span>held-out</span><strong>{_badge("UNCONFIRMED")}</strong></div>
        <div><span>직접 T2 Agentic 결과</span><strong>아님</strong></div>
      </div>
      <div class="two-column"><div><h3>공격 반응 민감도</h3><dl class="architecture-contract">
        <div><dt>attack event</dt><dd>{d1['pilot_events']}개 중 {d1['attack_events_detected']}개가 하나 이상의 D1 alarm episode와 겹침</dd></div>
        <div><dt>D0 / D1 겹침</dt><dd>둘 다 {d1['overlap']['both']}; D0만 {d1['overlap']['d0_only']}; D1만 {d1['overlap']['d1_only']}; 둘 다 아님 {d1['overlap']['neither']}</dd></div>
        <div><dt>D0 miss</dt><dd>현재 예비 실험에서 D0가 놓친 3개 event 모두에 D1 response가 있었음</dd></div>
      </dl></div><div><h3>정상 false-alarm 부담</h3><dl class="architecture-contract">
        <div><dt>rule record</dt><dd>{d1['anomalous_rule_records']}</dd></div>
        <div><dt>alarm second</dt><dd>{d1['unique_alarm_seconds']}</dd></div>
        <div><dt>전체 episode</dt><dd>{d1['total_alarm_episodes']}</dd></div>
        <div><dt>정상 false episode</dt><dd>{d1['normal_exposure_seconds']} normal seconds에서 {d1['normal_false_episodes']}개</dd></div>
      </dl></div></div>
      <aside class="principle">예비 Recall이 높다고 운영 유용성이 우수하다고 결론 내릴 수 없습니다.</aside>
      <aside class="principle">D1은 COMMON-42 검증된 관계 규칙 단독 방식이며, T2 Agentic Rule-only가 아닙니다.</aside>
      <p><a href="../architecture/08_d1_rule_only/ARCH_008_REPORT.md">D1 평가 심층 점검 열기</a> · <a href="../architecture/08_d1_rule_only/ARCH_008_OUTPUT_LEVELS.md">출력 단위</a> · <a href="../architecture/08_d1_rule_only/ARCH_008_COMPLEMENTARITY_BOUNDARY.md">상보성 경계</a> · <a href="../architecture/08_d1_rule_only/ARCH_008_CLAIM_MATRIX.csv">주장 matrix</a></p>
      <p><strong>다음 심층 점검:</strong> {_escape(_ko_text(d1['next_deep_review']))}</p>
    </section>

    <section id="d2-fusion" class="section panel-feature">
      <div class="section-heading"><p class="eyebrow">D2</p><h2>탐지기·규칙 결합 예비 실험</h2></div>
      <p class="architecture-flow">고정 D0 + 고정 D1 evidence → 결정론적 V1 / V2 → durable combined prediction → label 접근 → 예비 metric</p>
      <div class="summary-grid">
        <article class="summary-card"><p class="eyebrow">D0</p><h3>기준 탐지기</h3><dl>
          <div><dt>정책 (Policy)</dt><dd>Frozen PCA-SPE</dd></div><div><dt>공격 사건 단위 재현율 (Attack-event Recall)</dt><dd>11/14</dd></div>
          <div><dt>시간당 정상 오경보율 (Normal FAR/hour)</dt><dd>{d0['normal_far_episodes_per_hour']}</dd></div><div><dt>D0 누락 회복 (D0-miss Recovery)</dt><dd>해당 없음 (N/A)</dd></div>
          <div><dt>상태</dt><dd>예비 기준선</dd></div><div><dt>독립 검증</dt><dd>아니오</dd></div>
        </dl></article>
        <article class="summary-card"><p class="eyebrow">D2 V1</p><h3>동일 index 근거 결합</h3><dl>
          <div><dt>정책 (Policy)</dt><dd>같은 <code>decision_physical_row_index</code>에서 canonical D1 source가 2개 이상일 때 추가 alarm</dd></div><div><dt>공격 사건 단위 재현율 (Attack-event Recall)</dt><dd>{_escape(d2['v1']['attack_event_response'])}</dd></div>
          <div><dt>시간당 정상 오경보율 (Normal FAR/hour)</dt><dd>{d2['v1']['normal_far_episodes_per_hour']}</dd></div><div><dt>D0 누락 회복 (D0-miss Recovery)</dt><dd>{_escape(d2['v1']['d0_miss_recovery'])}</dd></div>
          <div><dt>상태</dt><dd>{_escape(d2['v1']['development_status'])}</dd></div><div><dt>독립 검증</dt><dd>아니오</dd></div>
        </dl></article>
        <article class="summary-card"><p class="eyebrow">D2 V2</p><h3>native horizon 근거 결합</h3><dl>
          <div><dt>정책 (Policy)</dt><dd>각 relation의 native-horizon token 안에서 active D1 source가 2개 이상일 때 추가 alarm</dd></div><div><dt>공격 사건 단위 재현율 (Attack-event Recall)</dt><dd>{_escape(d2['v2']['attack_event_response'])}</dd></div>
          <div><dt>시간당 정상 오경보율 (Normal FAR/hour)</dt><dd>{d2['v2']['normal_far_episodes_per_hour']}</dd></div><div><dt>D0 누락 회복 (D0-miss Recovery)</dt><dd>{_escape(d2['v2']['d0_miss_recovery'])}</dd></div>
          <div><dt>상태</dt><dd>{_escape(d2['v2']['development_status'])}</dd></div><div><dt>독립 검증</dt><dd>아니오</dd></div>
        </dl></article>
      </div>
      <aside class="principle">D1의 다른 event response는 관찰됐지만, 현재 V1/V2 policy는 이를 attack-event Recall 증가로 바꾸지 못했습니다.</aside>
      <aside class="principle">V2는 test1-informed development이며 독립 확인이 아닙니다.</aside>
      <p><a href="../architecture/09_d2_fusion/ARCH_009_REPORT.md">D2 심층 점검 열기</a> · <a href="../architecture/09_d2_fusion/ARCH_009_POLICY_COMPARISON.csv">policy 비교</a> · <a href="../architecture/09_d2_fusion/ARCH_009_MISS_RECOVERY.md">miss 회복</a> · <a href="../architecture/09_d2_fusion/ARCH_009_CLAIM_MATRIX.csv">주장 matrix</a></p>
      <p><strong>다음 심층 점검:</strong> {_escape(_ko_text(d2['next_deep_review']))}</p>
    </section>

    <section id="metrics-results" class="section panel-history">
      <div class="section-heading"><p class="eyebrow">METRICS</p><h2>성능 지표와 결과 무결성</h2></div>
      <p class="architecture-flow">방법별 원시 출력 → alarm second → episode → attack-event unit / 정상 노출 시간 → Recall / FAR</p>
      <div class="status-snapshot">
        <div><span>연속 공격 구간 단위</span><strong>{metrics['event_unit_count']}개 contiguous units</strong></div>
        <div><span>통계적 독립성</span><strong>{_escape(_ko_text(metrics['event_independence']))}</strong></div>
        <div><span>정상 노출 시간</span><strong>{metrics['normal_exposure_seconds']}초</strong></div>
        <div><span>방법 간 비교 가능성</span><strong>{_escape(_ko_text(metrics['comparability']))}</strong></div>
        <div><span>비교 공정성</span><strong>{_escape(_ko_text(metrics['fairness']))}</strong></div>
        <div><span>추론 통계</span><strong>고정된 검정 없음</strong></div>
      </div>
      <div class="summary-grid">
        <article class="summary-card"><p class="eyebrow">D0</p><h3>기준 detector</h3><dl><div><dt>공격 사건 단위 재현율 (Recall)</dt><dd>11/14</dd></div><div><dt>시간당 정상 오경보율 (FAR/hour)</dt><dd>0.4939336325682589</dd></div><div><dt>상태</dt><dd>예비 실험 수준</dd></div><div><dt>독립 검증</dt><dd>아니오</dd></div></dl></article>
        <article class="summary-card"><p class="eyebrow">D1</p><h3>검증된 관계 규칙</h3><dl><div><dt>공격 사건 단위 재현율 (Recall)</dt><dd>13/14</dd></div><div><dt>시간당 정상 오경보율 (FAR/hour)</dt><dd>40.50255787059723</dd></div><div><dt>상태</dt><dd>예비 실험 수준</dd></div><div><dt>독립 검증</dt><dd>아니오</dd></div></dl></article>
        <article class="summary-card"><p class="eyebrow">D2 V1</p><h3>고정 fusion 예비 실험</h3><dl><div><dt>공격 사건 단위 재현율 (Recall)</dt><dd>11/14</dd></div><div><dt>시간당 정상 오경보율 (FAR/hour)</dt><dd>0.7056194750975128</dd></div><div><dt>상태</dt><dd>예비 policy</dd></div><div><dt>독립 검증</dt><dd>아니오</dd></div></dl></article>
        <article class="summary-card"><p class="eyebrow">D2 V2</p><h3>개발용 fusion</h3><dl><div><dt>공격 사건 단위 재현율 (Recall)</dt><dd>11/14</dd></div><div><dt>시간당 정상 오경보율 (FAR/hour)</dt><dd>6.915070855955625</dd></div><div><dt>상태</dt><dd>test1-informed</dd></div><div><dt>독립 검증</dt><dd>아니오</dd></div></dl></article>
      </div>
      <div class="two-column"><div><h3>지표 계약</h3><dl class="architecture-contract"><div><dt>사건 검출 (Event Hit)</dt><dd>half-open alarm episode가 attack unit과 하나라도 겹치면 hit; PA·grace·dilation·최소 지속시간 없음</dd></div><div><dt>알람 구간 (Episode)</dt><dd>physical row를 set으로 중복 제거하고 정렬한 뒤 정확히 +1 row로 이어지는 경우만 합침; 허용 gap 0</dd></div><div><dt>시간당 오경보율 (FAR)</dt><dd>정상 false episode 수 / (정상 노출 초 / 3600)</dd></div><div><dt>D1 정규화</dt><dd>non-opportunity·non-alarm·abstain은 Boolean metric interface에 alarm timestamp를 추가하지 않음; 고정 abstain 수는 0</dd></div></dl></div><div><h3>결과 무결성 경계</h3><dl class="architecture-contract"><div><dt>보장하는 것</dt><dd>고정 artifact identity·label identity·ordering·arithmetic·mutation/replay·report binding</dd></div><div><dt>보장하지 않는 것</dt><dd>독립성·표본 충분성·일반화·우수성·유용성·과학적 타당성을 확립하지 않음</dd></div><div><dt>보고서 계보</dt><dd>부분적: 고정 comparison artifact는 있지만 aggregation source는 현재 scientific tree에서 찾을 수 없음</dd></div></dl></div></div>
      <aside class="principle">14개의 연속 공격 구간 단위(contiguous attack-event units)이며, 통계적 독립성은 확립되지 않았습니다.</aside>
      <aside class="principle">결과 무결성 확인은 과학적 검증과 다릅니다.</aside>
      <p><a href="../architecture/10_metrics_integrity/ARCH_010_REPORT.md">지표 심층 점검 열기</a> · <a href="../architecture/10_metrics_integrity/ARCH_010_FROZEN_PILOT_RESULTS.csv">고정 예비 결과 표</a> · <a href="../architecture/10_metrics_integrity/ARCH_010_RESULT_INTEGRITY.md">무결성 경계</a></p>
      <p><strong>다음 심층 점검:</strong> {_escape(_ko_text(metrics['next_deep_review']))}</p>
    </section>

    <section id="outer-reproducibility" class="section panel-feature">
      <div class="section-heading"><p class="eyebrow">ARCH-011</p><h2>OUTER·재현성·이식성</h2></div>
      <p class="architecture-flow">근거 추적 → 같은 환경 replay → 새 환경 synthetic 재현 → 새 환경 scientific 재현 → 외부 독립 재현</p>
      <div class="status-snapshot">
        <div><span>근거 추적 (Traceability)</span><strong>{_escape(_ko_text(outer['reproduction_levels']['traceability']))}</strong></div>
        <div><span>같은 환경 replay</span><strong>{_escape(_ko_text(outer['reproduction_levels']['same_machine_replay']))}</strong></div>
        <div><span>새 환경 synthetic 재현</span><strong>{_escape(_ko_text(outer['reproduction_levels']['fresh_machine_synthetic']))}</strong></div>
        <div><span>새 환경 scientific 재현</span><strong>{_escape(_ko_text(outer['reproduction_levels']['fresh_machine_scientific']))}</strong></div>
        <div><span>외부 독립 재현</span><strong>{_escape(_ko_text(outer['reproduction_levels']['independent_external']))}</strong></div>
      </div>
      <div class="two-column"><div><h3>기존 OUTER</h3><dl class="architecture-contract">
        <div><dt>결과</dt><dd>{_escape(_ko_text(outer['old_outer']['result']))}</dd></div>
        <div><dt>중단 지점</dt><dd><code>OUTER_TEST2_FEATURE_CUSTODY_REJECTED</code> — file open/read 전</dd></div>
        <div><dt>과학 내용 접근</dt><dd>byte {outer['old_outer']['feature_byte_reads']}; semantic parse {outer['old_outer']['semantic_parses']}; label {outer['old_outer']['label_accesses']}</dd></div>
        <div><dt>재시도 가능성</dt><dd>{_escape(_ko_text(outer['old_outer']['retryability']))}</dd></div>
        <div><dt>같은 test2 재사용</dt><dd>{_escape(_ko_text(outer['old_outer']['same_physical_test2_reuse']))}</dd></div>
      </dl></div><div><h3>향후 VALIDATION V2</h3><dl class="architecture-contract">
        <div><dt>PILOT V1</dt><dd>{_escape(_ko_text(outer['pilot_v1']))}</dd></div>
        <div><dt>VALIDATION V2</dt><dd>{_escape(_ko_text(outer['validation_v2']))}</dd></div>
        <div><dt>VALIDATION V2 authority</dt><dd>DEC-020과 GAP-FIX-001에 따라 별도 Formal V4를 채택했다. canonical RuleV1·VerifierV1 authority를 상속하지 않으며 실제 scientific frame materialization과 custody는 후속 gate다.</dd></div>
        <div><dt>환경</dt><dd>project 전체 lock이 없고 NumPy·test tooling·schema package closure가 불완전하다. exact GDN은 Windows·wheel·root에 결속되고 scientific replay에는 private custody asset이 필요하다.</dd></div>
        <div><dt>재현 rehearsal</dt><dd>{_escape(_ko_text(outer['fresh_machine_timing']))}</dd></div>
      </dl></div></div>
      <aside class="principle">기존 연구: 결과 없음. 새 held-out: 새로운 사전 등록(preregistration)이 필요합니다.</aside>
      <aside class="principle">근거 추적은 새 환경 독립 재현(Fresh-machine Reproduction)이 아닙니다. OUTER 결과 없음은 성능 실패를 뜻하지 않습니다.</aside>
      <p><a href="../architecture/11_outer_reproducibility/ARCH_011_REPORT.md">OUTER·재현성 심층 점검 열기</a> · <a href="../architecture/11_outer_reproducibility/ARCH_011_REPRODUCTION_LEVELS.md">재현 수준</a> · <a href="../architecture/11_outer_reproducibility/ARCH_011_AUTHORITY_OPTIONS.csv">authority 선택지</a> · <a href="../architecture/11_outer_reproducibility/ARCH_011_FRESH_MACHINE_PROTOCOL.md">새 환경 재현 protocol</a></p>
    </section>

    <section id="data-governance" class="section panel-history">
      <div class="section-heading"><p class="eyebrow">DATA</p><h2>데이터·split 통제</h2></div>
      <div class="status-snapshot">
        <div><span>데이터셋</span><strong>{_escape(governance['dataset'])}</strong></div>
        <div><span>공정 범위</span><strong>{_escape(governance['process'])}</strong></div>
        <div><span>feature·역할 범위</span><strong>{_escape(_ko_text(governance['source_scope']))}</strong></div>
        <div><span>정보 누출 상태</span><strong>{_escape(_ko_text(governance['leakage_status']))}</strong></div>
        <div><span>Test1</span><strong>{_escape(_ko_text(governance['test1_status']))}</strong></div>
        <div><span>Test2</span><strong>{_escape(_ko_text(governance['test2_status']))}</strong></div>
      </div>
      <div class="summary-grid">{split_markup}</div>
      <aside class="principle">{_escape(_ko_text(governance['label_access']))}</aside>
      <p><a href="../architecture/01_data_and_splits/ARCH_001_REPORT.md">데이터·split 심층 점검 열기</a> · <a href="../architecture/01_data_and_splits/ARCH_001_LABEL_ACCESS_TIMELINE.md">label 접근 순서</a> · <a href="../architecture/01_data_and_splits/ARCH_001_MISMATCHES.md">불일치 기록</a></p>
      <p><strong>다음 심층 점검:</strong> {_escape(_ko_text(governance['next_deep_review']))}</p>
    </section>

    <section id="candidate-discovery" class="section panel-feature">
      <div class="section-heading"><p class="eyebrow">DISCOVERY</p><h2>관계 후보 탐색</h2></div>
      <div class="status-snapshot">
        <div><span>후보 전체 범위</span><strong>{_escape(_ko_text(discovery['candidate_universe']))}</strong></div>
        <div><span>후보 합집합</span><strong>{_escape(_ko_text(discovery['union']))}</strong></div>
        <div><span>학습 graph 사용</span><strong>예</strong></div>
        <div><span>Attention을 최종 근거로 사용</span><strong>아니오</strong></div>
        <div><span>사후 설명(XAI)</span><strong>아니오</strong></div>
        <div><span>GDN 고유 기여</span><strong>미검증</strong></div>
      </div>
      <div class="summary-grid">{discovery_markup}</div>
      <aside class="principle">{_escape(_ko_text(discovery['warning']))}</aside>
      <p><a href="../architecture/02_candidate_discovery/ARCH_002_REPORT.md">후보 탐색 심층 점검 열기</a> · <a href="../architecture/02_candidate_discovery/ARCH_002_GDN_PROFESSOR_ANSWER.md">GDN 교수 설명</a> · <a href="../architecture/02_candidate_discovery/ARCH_002_MISMATCHES.md">탐색 불일치 기록</a></p>
      <p><strong>다음 심층 점검:</strong> {_escape(_ko_text(discovery['next_deep_review']))}</p>
    </section>

    <section id="my-tasks" class="section">
      <div class="section-heading"><p class="eyebrow">02</p><h2>내가 해야 할 일</h2></div>
      <p class="section-intro">current-state registry에 기록된 연구 책임자의 우선 검토 항목입니다.</p>
      {_bullet_list((_ko_text(item) for item in state['top_user_todo']), empty="현재 사용자 할 일이 없습니다.")}
    </section>

    <section id="decisions" class="section">
      <div class="section-heading"><p class="eyebrow">03</p><h2>결정이 필요한 사항</h2></div>
      {decision_content}
    </section>

    <section id="architecture" class="section panel-dark">
      <div class="section-heading"><p class="eyebrow">04</p><h2>전체 아키텍처</h2></div>
      <p class="architecture-flow">HAI provenance·P1 범위 → 고정 role universe → META / STAT / GDN → 재점수화 없는 후보 합집합 → 정상 관계 profiling → 구성 evidence → T0 / T1 / T1-B / T2 → task deterministic verifier → COMMON-42·private runtime numeric authority → D1; detector authority → D0; D0 + D1 → D2 policy → event / episode metric → 결과 무결성 governance</p>
      <p class="section-intro">ARCH-000은 실제 source·실행·artifact 계보를 점검했습니다. 각 영역을 열면 상위 계약을 볼 수 있으며, 미확인 연결은 상세 map에 그대로 남깁니다.</p>
      <div class="architecture-detail-grid">{architecture_markup}</div>
      <p><a href="../architecture/00_overview/ARCH_000_REPORT.md">전체 아키텍처 점검 열기</a> · <a href="../architecture/00_overview/ARCH_000_MISMATCHES.md">불일치 기록 검토</a> · <a href="../architecture/00_overview/DEEP_REVIEW_INDEX.md">심층 점검 색인</a></p>
    </section>

    <section class="section explorer" aria-label="Registry 검색">
      <div><label for="registry-search">Registry 검색</label><input id="registry-search" type="search" placeholder="이름·근거·위험·다음 조치 검색…"></div>
      <div><label for="status-filter">상태 필터</label><select id="status-filter"><option value="">전체 상태</option>{status_options}</select></div>
      <p id="filter-count" aria-live="polite"></p>
    </section>

    <section id="components" class="section">
      <div class="section-heading"><p class="eyebrow">05</p><h2>구현 현황</h2></div>
      <p class="section-intro">기존 component token은 화면에서만 한글로 표시합니다. 근거 점검 완료(Evidence-reviewed)는 source·evidence 검토이며 성능 검증이 아닙니다. 결과 무결성 확인에는 결과별 명시적 artifact가 필요합니다.</p>
      <div class="card-grid">{component_cards}</div>
    </section>

    <section id="experiments" class="section">
      <div class="section-heading"><p class="eyebrow">06</p><h2>실험 현황</h2></div>
      <p class="section-intro">근거 점검을 마친 예비 실험은 기록된 범위의 evidence와 artifact를 확인했다는 뜻이며, 자동으로 과학적 검증 결과가 되지 않습니다.</p>
      <div class="card-grid">{experiment_cards}</div>
    </section>

    <section id="claims" class="section">
      <div class="section-heading"><p class="eyebrow">07</p><h2>연구 주장과 근거</h2></div>
      <p class="section-intro"><code>claims.csv</code>가 과학적 주장 상태의 공식 기준입니다. component 호환 field는 과학적 주장 상태를 결정하지 않습니다.</p>
      <div class="card-grid">{claim_cards}</div>
    </section>

    <section id="risks" class="section">
      <div class="section-heading"><p class="eyebrow">08</p><h2>위험 및 점검사항</h2></div><div class="card-grid">{risk_cards}</div>
    </section>

    <section id="history" class="section panel-history">
      <div class="section-heading"><p class="eyebrow">09</p><h2>연구 진행 이력</h2></div>
      <p class="section-intro">방향 전환과 결정의 핵심 이력이며 전체 commit log는 아닙니다. USER_CONTEXT 항목은 불확실성을 보존하고 현재 <code>claims.csv</code>를 덮어쓰지 않습니다.</p>
      <div class="timeline history-timeline">{history_markup}</div>
      <h3>현재 유효하거나 조건부인 핵심 결정</h3>
      <ul class="decision-list">{key_decisions_markup}</ul>
      <p><a href="../history/PROJECT_TIMELINE.md">전체 연구 진행 이력 열기</a> · <a href="../history/PROFESSOR_FEEDBACK_LINEAGE.md">교수 피드백 계보</a> · <a href="../history/SUPERSEDED_DIRECTIONS.md">중단·대체된 방향</a></p>
    </section>

    <section id="source-authority" class="section authority-detail">
      <div class="section-heading"><p class="eyebrow">10</p><h2>공식 기준 코드·근거</h2></div>
      <dl>
        <div><dt>과학 source</dt><dd>{_escape(authority['ref'])}<br><code>{_escape(authority['commit'])}</code></dd></div>
        <div><dt>변경 불가 pin</dt><dd>{_escape(state['immutable_scientific_pin']['tag'])}<br><code>{_escape(state['immutable_scientific_pin']['commit'])}</code></dd></div>
        <div><dt>문서 overlay</dt><dd>{_escape(state['documentation_overlay']['ref'])}<br><code>{_escape(state['documentation_overlay']['commit'])}</code><br>{_escape(state['documentation_overlay']['role'])}</dd></div>
      </dl>
      <p>과학 코드와 결과 주장은 scientific authority에서만 파생됩니다. overlay의 설명 문맥은 이를 덮어쓸 수 없습니다.</p>
    </section>

    <section id="recent-change" class="section">
      <div class="section-heading"><p class="eyebrow">11</p><h2>최근 변경사항</h2></div>
      <div class="timeline">{recent_markup}</div>
      <div class="next-task"><span>정확한 다음 작업</span><strong>{_escape(state['exact_next_task'])}</strong></div>
    </section>
  </main>

  <footer>RCC registry snapshot {_escape(state['generated_at'])}에서 자동 생성 · Authority <code>{_escape(authority['commit'])}</code></footer>
  <script src="assets/rcc.js"></script>
</body>
</html>
"""


def render_dashboard(
    data: Mapping[str, Any], digest: str, rcc_root: Path | None = None
) -> str:
    """Render the application-style Dashboard V2 from registry state."""

    from dashboard_v2 import render_dashboard_v2

    return render_dashboard_v2(data, digest, rcc_root or default_rcc_root())


def _markdown_marker(state: Mapping[str, Any], digest: str) -> str:
    return f"<!-- {_source_marker(state, digest)} -->"


def _md_bullets(values: Iterable[object]) -> str:
    items = list(values)
    return "\n".join(f"- {item}" for item in items) if items else "- None recorded."


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def render_gpt_brief(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    authority = state["scientific_authority"]
    experiments = "\n".join(
        f"- **{row['experiment_id']} · {row['name']}** — "
        f"`{GPT_EXPERIMENT_STATUS_LABELS.get(row['status'], row['status'])}`."
        for row in data["experiments"]
    )
    claims = "\n".join(
        f"- **{row['claim_id']} · {row['status']}** — {row['allowed_wording']}"
        for row in data["claims"]
    )
    risks = "\n".join(
        f"- **{row['severity']} / {row['status']}** — {row['description']}"
        for row in data["risks"] if row["severity"] in {"CRITICAL", "HIGH"}
    )
    return f"""{_markdown_marker(state, digest)}
# GPT Brief — Research Control Center

{front_markdown(data['front_results'])}

Scientific authority: `{authority['ref']}` @ `{authority['commit']}`.

> Chat memory must not override the scientific authority or RCC registry.

## Research objective

{state['research_objective']}

## Current phase

**{state['current_phase']}** — {state['current_phase_statement']}

## How to read RCC status

`audited=true`는 Evidence-reviewed이며 scientific validation이 아니다.
A Result-integrity audit checks custody and arithmetic, not generalization.
이 상태들은 not a single completion percentage다. claim은 claims.csv가 관리한다.

    ## Architecture in one line

{state['architecture_flow']}

## Data and split boundary

HAI 23.05 P1 is selected. train1/train2 fit normal evidence; train3 confirms relations and
calibrates D0; train4 is a guard. test1 is development evidence. OUTER produced no result.
PILOT V1 D1 lacks durable pre-label persistence; PILOT V1 D2 V2 is test1-informed.
VALIDATION V2 completed durable five-method prediction replay before its one-shot label access.

## Evaluation expansion boundary

The frozen 14-scenario test1 result remains DEVELOPMENT_ONLY and will not be reopened.
The prospective panels are HAI 23.05 test2 as PRIMARY_HELDOUT and HAI 22.04 plus
HAI 21.03 as version-separated external replications. Their 146 nominal scenarios are
not IID and one pooled Recall is prohibited as the primary result. DG-05 is mandatory
before any new attack payload or label access. Current next gate: {state['exact_next_task']}.

## Candidate-discovery boundary

    PILOT V1은 47-pair union을 보존한다. V2 EXP-01은 META_PLUS_STAT을 선택했고,
    EXP-01B는 GDN-XAI arm을 동일 예산으로 비교한 뒤 `GDN_ABLATION_ONLY`로 끝났다.
    META provenance는 `{state['candidate_discovery']['meta_lineage']['source']}`이고,
    researcher intervention은 `{state['candidate_discovery']['meta_lineage']['user_intervention']}`이다.
    exact replay에는 private reviewed semantic declaration이 필요하므로 공개 재현 상태는
    `{state['candidate_discovery']['meta_lineage']['exact_public_reproducibility']}`이다.

## Relation and numeric-authority boundary

The lineage is 47 pairs → 94 directions → 25/45 fit-supported → 23/42 confirmed. Confirmation
cannot search or retune. Construction and runtime numeric identities remain separate. Repeated
normal response is not causal proof.

## Rule-construction boundary

E3 exposes a fixed relation, horizon, and normal-only references to a closed proposal schema.
`accepted_proposal` grants neither runtime authority nor detection performance. T2 feedback was zero.

## Frozen pilot runtime boundary

D1 is COMMON-42 Verified Relational Rule-only, not T2 Agentic Rule-only. D0 is the frozen
37-feature PCA-SPE baseline. D2 V1/V2 preserved D0 pointwise and recovered 0/3 misses;
their development-only FAR increased. PILOT V1 lacks the later V2 durable custody gate.

## How we got here

    History cannot override current state. ARGOS remains partial support.

## Established boundary

Frozen discovery, construction, runtime, and integrity artifacts establish execution and custody,
not causality, physical truth, general GDN utility, agentic-feedback advantage, or generalization.
T2 feedback actions were zero.

## Frozen INNER pilot observations

The INNER evaluation contains 14 contiguous attack-event units; statistical independence is
not established. D0 PCA-SPE responded to
11/14 with Normal FAR 0.4939336325682589 episodes/hour. D1 verified Rule-only responded
to 13/14 with Normal FAR 40.50255787059723 episodes/hour. Their event overlap was both
10, D0-only 1, D1-only 3, neither 0. D2 V1 and D2 V2 each responded to 11/14 and each
recovered 0/3 D0-missed events; their Normal FAR values were 0.7056194750975128 and
6.915070855955625 episodes/hour respectively. These are exact public frozen pilot
observations, not new calculations.

> These 14 units are pilot evidence only, not validated performance.

## Unresolved scientific questions

{_md_bullets(state['not_established'])}

    Graph-Guided and Agentic remain provisional contribution labels. EXP-01 and EXP-01B do not
    support GDN under their original protocols. Later EXP-01C provides LEARNED_GRAPH_SUPPORTING
    evidence only; it does not replace the META+STAT discovery policy. DG-04 controls final wording. T2
    feedback advantage also remains unsupported.

## Claim boundaries

{claims}

## Current execution gates

EXP-03 V1: {state.get('exp03_execution', {}).get('status', 'PREPARED_PROVIDER_GATED')} — constrained Rule materialization, not evidence-to-rule induction.
EXP-03B: {state.get('exp03b_preparation', {}).get('status', 'NOT_PREPARED')}. DG-03B 별도 승인 전 provider 0회. DG-04는 EXP-03B 이후로 연기합니다. All new attack panels await DG-05;
professor submission awaits DG-06. Cross-version P1 compatibility remains unresolved.

## Top user TODO

{_md_bullets(state['top_user_todo'])}

## Exact next task

Management: **{state['recommended_next_management_task']}**

Following architecture review: **{state['recommended_next_architecture_task']}**
"""


def render_current_status(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    authority = state["scientific_authority"]
    components = data["components"]
    component_summary = {
        "구현 완료": sum(row["status"].startswith("IMPLEMENTED") for row in components),
        "실제 실행 완료": sum(row["executed"] == "true" for row in components),
        "근거 점검 완료 (Evidence-reviewed)": sum(row["audited"] == "true" for row in components),
        "독립 재현 완료": sum(row["reproduced"] == "true" for row in components),
    }
    component_summary_rows = "\n".join(f"- **{label}:** {value}" for label, value in component_summary.items())
    component_rows = "\n".join(
        f"| {row['component_id']} | {COMPONENT_STATUS_LABELS.get(row['status'], row['status'])} | {COMPONENT_CARD_COPY.get(row['component_id'], (row['name'], row['next_action']))[1]} |"
        for row in components
    )
    experiment_rows = "\n".join(
        f"| {row['experiment_id']} | {EXPERIMENT_STATUS_LABELS.get(row['status'], row['status'])} | {EXPERIMENT_CARD_COPY.get(row['experiment_id'], (row['name'], row['result_scope']))[1]} |"
        for row in data["experiments"]
    )
    claim_rows = "\n".join(
        f"| {row['claim_id']} | {STATUS_DISPLAY_LABELS.get(row['status'], row['status'])} | {CLAIM_CARD_COPY.get(row['claim_id'], (row['claim_text'], row['allowed_wording']))[1]} |"
        for row in data["claims"]
    )
    return f"""{_markdown_marker(state, digest)}
# RCC 현재 연구 상태

{front_markdown(data['front_results'])}

과학 source authority: `{authority['ref']}` @ `{authority['commit']}`
Registry version: `{state['registry_version']}`
Registry snapshot: `{state['generated_at']}`

## 현재 단계

**{PHASE_DISPLAY_LABELS.get(state['current_phase'], state['current_phase'])}** (`{state['current_phase']}`)

{_ko_text(state['current_phase_statement'])}

## 상태를 읽는 방법

- **구현 완료 / 실제 실행 완료:** 엔지니어링 상태일 뿐이다.
- **근거 점검 완료 (Evidence-reviewed):** 호환용 component field `audited`가 pinned authority와
  source 또는 evidence 상태를 대조했다는 뜻이다. 성능 검증이 아니다.
- **결과 무결성 확인 (Result Integrity):** 명시된 결과 artifact의 custody·불변성·순서·산술을
  확인한 상태다. 과학적 검증이 아니다.
- **독립 재현 완료 (Reproduced):** 필요한 환경과 custody 아래에서 별도로 재현한 상태다.
- **과학적 검증:** 가설에 대한 충분한 독립 근거가 있는 상태이며 component 상태에서 추론하지
  않고 `claims.csv`가 관리한다.

구현 완료, 실행 완료, 결과 무결성 확인, 과학적 검증, 재현성, 일반화는 서로 다른 상태다.
따라서 아래 개수는 하나의 완료율이 아니며, 근거 점검 완료 수가 실제 실행 완료 수보다 많을 수 있다.

## 구성요소 요약

{component_summary_rows}

## 데이터·split 점검

- **데이터셋 / 공정:** {state['data_governance']['dataset']} / {state['data_governance']['process']}
- **Label 접근:** {_ko_text(state['data_governance']['label_access'])}
- **정보 누출:** {_ko_text(state['data_governance']['leakage_status'])}
- **Test1:** {_ko_text(state['data_governance']['test1_status'])}
- **Test2:** {_ko_text(state['data_governance']['test2_status'])}

## META provenance 점검

- **META SOURCE:** `{state['candidate_discovery']['meta_lineage']['source']}`
- **META USER INTERVENTION:** `{state['candidate_discovery']['meta_lineage']['user_intervention']}`
- **META EXACT PUBLIC REPRODUCIBILITY:** `{state['candidate_discovery']['meta_lineage']['exact_public_reproducibility']}`
- **경계:** 공식 P1 graph 자동 처리와 AI-assisted reviewed semantic declaration이 함께
  ranking에 기여했다. 최종 Top-20은 deterministic code가 선택했으며 researcher pair
  selection은 확인되지 않았다.

## 고정 D1 runtime·trace 점검

- **실행 authority:** task-specific V4 authority plane — CanonicalRuleDescriptorV4 42개, 고정 V4 evaluator bundle, normal-only Utility V4 numeric resolver, committed one-attempt INNER grant.
- **Prediction:** opportunity record 6,031개, anomalous rule record 788개, 고유 alarm decision second 630개, downstream metric episode 626개.
- **고정 경계:** D0/D2보다 약한 in-memory pre-label freeze; label 전 durable persistence = 아니오.
- **Trace:** canonical RuntimeTraceV1과 동등하지 않으며 terminal outcome semantics만 부분적으로 겹친다.
- **설명:** canonical RuntimeTraceV1 renderer는 있지만 고정 V4 D1이 호출하지 않았고 고정 D1 explanation artifact도 없다.

## 고정 D2 fusion 점검

- **역할:** D0 alarm을 보존하는 결정론적 fusion-policy 예비 실험
- **V1:** {state['pilot_observations']['d2_v1']}.
- **V2:** {state['pilot_observations']['d2_v2']}.
- **D0 보존:** pointwise 보존 — `D2(t)=D0(t) OR policy_admits_D1(t)`
- **고정 / label:** V1과 V2 모두 label 접근 전 durable prediction file gate를 사용한다.
- **경계:** {_ko_text(state['d2_fusion']['warning'])}

## 구현 구성요소

| 구성요소 | 엔지니어링·근거 표시 | 다음 조치 |
|---|---|---|
{component_rows}

호환용 field `claim_ready`는 이 요약에서 제외했다. 이는 component가 좁은 구현 또는 계약
주장을 하나 이상 지원한다는 뜻일 뿐이다.

## 실험

| 실험 | 상태 | 결과 범위 |
|---|---|---|
{experiment_rows}

## 공식 연구 주장

주장 상태는 `registry/claims.csv`에서만 가져온다.

| 주장 | 상태 | 허용되는 설명 |
|---|---|---|
{claim_rows}

## 연구 상태의 서로 다른 차원

- **엔지니어링:** {_ko_text(state['research_status_summary']['engineering'])}
- **결과 무결성:** {_ko_text(state['research_status_summary']['result_integrity'])}
- **과학적 검증:** {_ko_text(state['research_status_summary']['scientific_validation'])}
- **재현성:** {_ko_text(state['research_status_summary']['reproducibility'])}
- **일반화:** {_ko_text(state['research_status_summary']['generalization'])}
- **연구 주장:** {_ko_text(state['research_status_summary']['claims'])}

## 현재 보장되지 않는 것

아직 확립되지 않음:

{_md_bullets(_ko_text(item) for item in state['not_established'])}

## 정확한 다음 작업

**{state['exact_next_task']}**
"""


def render_arch001_user_summary(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    return f"""{_markdown_marker(state, digest)}
# 우리가 어떤 데이터를 쓰고 있는가

## 한 문장 답

우리는 공식 provenance가 고정된 HAI 23.05의 P1 Boiler 범위를 사용하며, 정상 학습
split과 INNER pilot, 아직 결과가 없는 held-out test2를 서로 다른 권한으로 다룬다.

## Split 한눈에 보기

| Split | 역할 | 무엇을 정하는 데 사용? | Label 사용? | 최종평가? |
|---|---|---|---|---|
| train1 | NORMAL FIT | 후보·관계·수치 authority·D0 fit | 아니오 | 아니오 |
| train2 | NORMAL FIT | train1과 독립적인 file-local fit 근거 | 아니오 | 아니오 |
| train3 | CONFIRMATION / CALIBRATION | 관계 확인과 D0 threshold 보정 | 아니오 | 아니오 |
| train4 | SANITY | normal guard와 D0 정상 sanity | 아니오 | 아니오 |
| test1 | PILOT EVALUATION | frozen 방법의 INNER 개발·예비 비교 | prediction 뒤에만 | 아니오 |
| test2 | HELD-OUT / UNAVAILABLE | 의도상 one-way 일반화 평가 | 실행되지 않음 | 결과 없음 |

## 왜 여러 train split이 있는가?

같은 normal data를 한 단계에서 만들고 같은 단계에서 확인하는 것을 피하려고 역할을
나눈다. train1/train2는 fit, train3는 독립 확인과 D0 threshold calibration, train4는
normal sanity에 사용된다. train3를 두 arm이 함께 쓰는 것은 확인된 leakage가 아니지만,
비교 독립성의 범위를 제한하므로 `ACCEPTABLE_WITH_SCOPE_LIMITATION`으로 기록했다.

## Rule을 만들 때 공격 답을 본 적이 있는가?

찾아본 현재 frozen 경로에서는 아니다. 후보 탐색, 관계 profiling, normal numeric
authority, evidence pack, T0/T1/T1-B/T2, verifier, COMMON-42는 normal-only evidence를
사용한다. test1 결과로 individual rule을 뒤에서 삭제하거나 COMMON-42를 다시 고른
경로도 확인되지 않았다.

## D0 threshold는 어디서 결정되는가?

D0는 train1과 train2로 표준화와 PCA를 fit하고, train3의 normal SPE 분포로 threshold를
calibrate한다. test1 label이나 test1 outcome은 model fit과 threshold 결정에 들어가지 않는다.

## Label은 언제 보이는가?

D0와 D2는 prediction file을 atomic하게 기록하고 다시 읽은 뒤 label을 연다. D1도
label-blind prediction object를 먼저 만들고 self-hash를 검증하지만, public prediction
file은 metric 뒤에 기록된다. 그래서 D1은 decision-before-label은 확인됐지만 durable
file-before-label 보장은 부족하다. 이것은 HIGH governance gap이며 leakage가 확인됐다는
뜻은 아니다.

## test1은 왜 final test가 아닌가?

현재 14개 사건은 작은 INNER pilot이다. 특히 D2 V2 policy는 앞선 INNER 결과를 알고
설계되었다고 명시되어 있다. 따라서 test1 수치는 개발·예비 관찰이며 독립 성능 검증이나
일반화 증거가 아니다.

## test2는 왜 결과가 없는가?

OUTER recovery는 test2 feature custody 확인에서 멈췄다. 파일 접근 시도는 한 번 있었지만
feature byte, hash, semantic parse는 0이고 label·prediction·metric도 0이다. 따라서
성능이 실패한 것이 아니라 **held-out result unavailable**이다.

## 현재 leakage 우려는 무엇인가?

**NO VERIFIED LEAKAGE FOUND.** 다만 D1 durable persistence gap, task별로 분산된 split
enforcement, train3 dual use, test1-informed D2 V2 때문에 “leakage impossible”이라고는
말할 수 없다.

## 다음 파트 전에 이해할 것

1. feature 파일과 label 파일은 별도 authority다.
2. 86 dataset points, 37 P1 features, 12×12 role universe는 같은 숫자가 아니다.
3. label-blind object와 durable prediction file은 서로 다른 보장이다.
4. test1은 pilot이고 test2는 결과가 없다.

다음 task는 **{state['exact_next_task']}**이다.
"""


def render_arch002_user_summary(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    return f"""{_markdown_marker(state, digest)}
# 관계 후보는 왜 세 방식으로 고르는가

## 한 문장 답

144개 가능한 source→target 쌍을 META·STAT·GDN이 서로 다른 근거로 20개씩 제안하고,
중복을 접은 47개만 다음 normal relation profiling이 검사한다.

| 방식 | 무엇을 보는가 | 무엇을 내놓는가 | 아직 말할 수 없는 것 |
|---|---|---|---|
| META | reviewed metadata와 physical graph | domain-prior 후보 Top-20 | 물리적 진실·인과 |
| STAT | normal train1/train2의 lagged 변화 상관 | association 후보 Top-20 | confirmed response·인과 |
| GDN | 정상 multivariate next-value prediction | learned-graph 후보 Top-20 | 고유 유용성·인과·attention 설명 |

## 왜 관계 후보를 먼저 줄이는가?

모든 가능한 쌍을 규칙으로 만들지 않고 서로 다른 약한 근거로 profiling 대상만 제한하기
위해서다. 이 단계는 관계를 확정하는 단계가 아니다.

## 144개는 어디서 나오는가?

P1의 ordered source 역할 12개와 target 역할 12개의 directed cross product다. 두 역할
집합은 현재 freeze에서 겹치지 않으므로 12×12=144다.

## META는 무엇을 보는가?

실제 센서 값을 읽지 않고 공식 HAI manual·directed physical graph와 AI-assisted reviewed
semantic declaration을 본다. 명시 연결, graph adjacency, subsystem support 순으로 분류하고
공식 reference category 수와 identity로 결정적으로 정렬한다. 학습 score와 researcher의
최종 Top-20 수동 선택은 없다. Exact public replay에는 private reviewed declaration이 필요하다.

## STAT은 무엇을 보는가?

train1과 train2 각각에서 source/target의 1초 변화량을 만들고 여러 lag에서 Pearson
association을 계산한다. 두 파일에서 부호가 안정적인지 확인하고 약한 쪽 strength로
정렬한다. 후속 delayed-response profiling과는 별개다.

## GDN은 무엇을 학습하는가?

37개 P1 node의 5초 history로 다음 1초 값을 예측한다. 학습된 node embedding의 cosine
similarity로 target별 neighbor graph를 만들고 세 seed에서 반복 선택된 edge를 우선한다.
현재 Top-5는 diagonal/self를 먼저 제거하지 않아 자기 node가 내부 슬롯을 차지할 수 있다.
후속 disjoint-role projection이 exported self-pair는 제거하지만 기능적 영향은 미검증이다.

## GDN attention을 쓰는 것인가?

모델 내부 message passing에는 attention을 쓴다. 그러나 attention coefficient를 후보
ranking이나 최종 관계 evidence로 쓰지 않는다. 후보 authority는 embedding-cosine
learned graph다. 별도 XAI나 SHAP도 쓰지 않는다.

## GDN edge는 어떤 의미인가?

target 예측에 선택된 neighbor/input dependency **후보**다. 원인, root cause, 확정된
시간 관계가 아니다.

## 20+20+20인데 왜 47개인가?

세 arm에서 겹친 pair를 exact directed identity로 한 번만 남기기 때문이다. META-only 8,
STAT-only 8, GDN-only 18, 두 arm 공통 13, 세 arm 공통 0으로 총 47이다. Arm score는
합치거나 비교하지 않으므로 47개 전체 순위도 없다.

## 다음 단계에서 무엇을 검증하는가?

47개 cohort를 normal delayed-response profiling에 넘겨 step event, response direction,
horizon과 안정성을 별도로 확인한다. 그 전에는 최종 relation이라고 부르면 안 된다.

다음 task는 **{state['exact_next_task']}**이다.
"""


def render_arch003_user_summary(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    return f"""{_markdown_marker(state, digest)}
# 47개 후보는 어떻게 42개 실행 관계가 되는가

## 한 문장 답

47개 pair를 정상 train1·train2의 반복 source step과 delayed target response로 검사하고,
선택된 relation만 train3에서 검색·재조정 없이 확인한 뒤, 별도 numeric authority를 붙여
실행 가능하게 만든다.

## 단계별 숫자

| 단계 | 수 | 의미 |
|---|---:|---|
| Candidate pairs | 47 | discovery가 제안한 source-target 조합 |
| Source-direction opportunities | 94 | pair마다 step_up·step_down을 별도로 검사 |
| Fit-supported | 25 contexts / 45 directions | train1·train2 gate 통과 |
| Confirmed | 23 contexts / 42 relations | 고정 identity가 train3 gate 통과 |

## 1. 47개 후보 중 무엇을 검사하는가?

source가 정상 구간에서 충분히 크고 지속적인 step을 만들었을 때 target이 일정 시간 뒤
같은 방향으로 반복 반응하는지 검사한다. 후보는 아직 관계가 아니고, source sign,
target sign, horizon이 정해져야 relation이 된다.

## 2. Source event와 target response

Source event는 직전 5행과 이후 5행 median 차이가 normal-derived threshold 이상이고 양쪽이
안정적일 때 생긴다. 같은 source의 가까운 event는 single-link 10행 cluster로 묶고, 다른
source event가 ±2행 안에 있으면 isolation에서 제외한다.

Target response는 event 전 5행 median을 baseline으로 하고, horizon 뒤 3행 median에서
baseline을 뺀 값이다. 파일 끝의 불완전 window는 버리며 보간하지 않는다.

## 3. Lag/horizon은 무엇이며 왜 여러 개를 보는가?

반응이 즉시 오지 않을 수 있어 1, 5, 10, 30, 60행 지연을 미리 고정해 비교한다. 각
source direction에서 consistency, effect, 짧은 horizon 순으로 하나만 고른다. 선택된
horizon은 이 유한 grid의 규칙상 winner이지 물리적 최적값이 아니다.

## 4. Consistency와 effect

Consistency는 usable event 중 target response가 선택 방향의 normal noise scale을 넘은
비율이다. Effect는 target response median의 절댓값을 target noise scale로 나눈 비율이다.
Support, consistency, effect, 두 fit file의 방향 우세를 모두 통과해야 한다.

## 5. 왜 train3에서 다시 확인하는가?

train1·train2에서 골랐던 relation이 다른 normal file에서도 유지되는지 보기 위해서다.
train3는 source/target/sign/horizon/parameter를 바꾸지 않고 같은 항목만 검사한다. 실패하면
conflict로 남고 다른 horizon이나 방향을 찾지 않는다.

## 6. 23 pair contexts와 42 relations의 차이

한 source-target pair에서 `step_up`과 `step_down`이 각각 별도 relation이 될 수 있다.
그래서 23개의 pair context 안에 42개의 directional relation이 존재한다.

## 7. Numeric authority는 무엇인가?

실행 숫자가 어느 normal split, relation, 계산 함수, artifact, hash에서 왔는지를 함께
고정한 권한이다. LLM은 authoritative number를 정하지 않는다.

Construction 시점에는 relation마다 11개 reference, 총 462개가 있었다. Frozen D1 runtime은
새 version의 normal-only authority에서 relation마다 10개 private role, 총 420개를 사용하고,
horizon은 canonical descriptor에서 사용한다. Focused audit는 공유 420개 value가 E1과 정확히
일치함을 확인했지만, 두 authority identity 자체가 같다는 뜻은 아니다.

## 8. 왜 causal relation이라고 부르면 안 되는가?

정상 데이터에서 반복되는 순서와 방향을 operationalize했을 뿐, intervention이나 물리 법칙,
root-cause를 검증하지 않았다. Held-out 일반화도 아직 확인되지 않았다.

## 다음 파트 전에 이해할 것

1. candidate, fit-supported, confirmed, runtime-bound는 서로 다른 단계다.
2. train3는 재탐색이 아니라 고정 relation의 확인이다.
3. value equality와 authority identity equality는 다르다.
4. relation numeric authority와 D0 PCA-SPE threshold는 별개다.

다음 task는 **{state['exact_next_task']}**이다.
"""


def render_arch004_user_summary(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    construction = state["rule_construction_authority"]
    return f"""{_markdown_marker(state, digest)}
# Rule은 어떻게 만들어지는가

## Evidence Pack

정상 데이터에서 확인한 relation을 제한된 construction view로 만든다. E1의 11개 role 중
horizon은 fixed relation field로, 나머지 10개는 값과 reference로 보인다. raw HAI, label,
attack, test/utility outcome, D0/D1 result와 runtime authority는 포함되지 않는다.

## LLM과 DSL 경계

LLM은 값을 볼 수 있지만 output에는 승인 reference만 반환한다. strict proposal schema에는
arbitrary numeric literal, Python, file/network access, 새 operator, free-form runtime logic가 없다.
새 variable이나 relation/horizon mismatch는 뒤의 deterministic validity가 거부한다.

## 네 construction arm

| Arm | LLM | Call policy | Frozen relation outcome |
|---|---|---|---|
| T0 | no | local deterministic template | 42/42 accepted proposal |
| T1 | yes | one call | 42/42 accepted proposal |
| T1-B | yes | three stateless calls, earliest admissible | 42/42 selected proposal |
| T2 | yes | maximum three, bounded feedback | 39/42 accepted; 3 no_rule |

T1-B는 126 calls를 모두 썼고, T2는 42 calls 모두 call 1에서 종료했다. 따라서 maximum
opportunity budget은 비교 가능하지만 realized cost가 같다고 말할 수 없다.

## Feedback은 실제 사용됐는가?

{construction['agentic_claim']}

T2의 세 no_rule은 unsupported-variable non-repairable validity issue였다. revise 0, retrieve 0,
follow-up 0이다. 따라서 “feedback improved quality”라고 말할 수 없다.

주의: task-specific orchestrator는 response/schema failure, verifier rejection, budget exhaustion도
`no_rule`로 합칠 수 있다. 이는 generic/frozen protocol의 explicit-failure 분리와 맞지 않는 HIGH
contract gap이며, frozen 세 건의 구체 원인을 바꾸지는 않는다.

## 42/42의 정확한 뜻

relation-level `accepted_proposal` 수다. canonical Rule v1 materialization, COMMON-42 membership,
runtime authorization 또는 detection performance 수가 아니다. `no_rule`은 construction의
fail-closed outcome이며 runtime `abstain`과 다르다.

## 재현성

T0는 frozen input에서 deterministic하다. LLM arms는 model/config, prompt, evidence, request,
response와 ledger hash가 추적되지만 temperature 0.7, seed 없음이므로 bitwise deterministic하지 않다.

다음 task는 **{state['exact_next_task']}**이다.
"""


def render_arch005_user_summary(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    verifier = state["verifier_common42_authority"]
    return f"""{_markdown_marker(state, digest)}
# Proposal부터 COMMON-42와 D1까지

Proposal은 frozen relation에 묶인 construction 후보이고, canonical `DelayedResponseRuleV1`은
graph/evidence/parameter/output까지 포함하는 다른 계약이다. 두 validity layer는
`PARTIALLY_OVERLAPPING`이며 frozen path에서 lossless bridge는 발견되지 않았다.

Canonical `VerifierV1`은 20단계로 contract와 binding을 검사하지만 scientific truth, causality,
utility, optimality 또는 generalization을 증명하지 않는다. Accepted도 runtime authorization이 아니다.

COMMON-42는 T0/T1/T1-B가 공통으로 가진 42개 executable projection을 하나의 V4 descriptor
portfolio로 중복 제거한 것이다. T2는 39 accepted와 3 no_rule이며 D1 utility authority에서
제외됐다. 따라서 D1 권장 명칭은 **{verifier['preferred_d1_term']}**이다.

Frozen D1은 canonical RuntimeAuthorizationBundleV1이 아니라 V4 authority, evaluator bundle,
private numeric custody와 committed one-attempt INNER grant를 사용했다. 420 shared values는 exact
match였지만 runtime authority/reference identity는 별도로 rebound됐다.

세 frozen T2 no_rule은 unsupported-variable non-repairable validity outcome으로 확인됐다. 그러나
일반 orchestration은 response/parse/rejection/budget failure도 no_rule로 합칠 수 있어 code-fix risk가 남는다.

기억할 한 문장: **Verifier acceptance는 scientific validation도 runtime authorization도 아니다.**

다음 task는 **{state['exact_next_task']}**이다.
"""


def render_arch006_user_summary(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    runtime = state["runtime_trace_explanation"]
    return f"""{_markdown_marker(state, digest)}
# Rule은 실제 시계열에서 어떻게 판단하는가

## 1. Rule은 언제 발동하는가?

Frozen D1은 매 초 모든 Rule을 판정하는 방식이 아니다. 5개 행의 source 전·후 median이
수치 권한의 magnitude·stability 조건과 방향을 만족하면 하나의 **opportunity**가 생긴다.
같은 source의 10초 single-link cluster에서는 절대 step amplitude가 가장 큰 후보를 남기며,
정확히 동률이면 가장 이른 index를 남긴다. 다른 source event와 ±2초로 겹치는 후보도 제외한다.

## 2. 발동하지 않으면 정상인가, abstain인가?

둘 다 아니다. source event가 없으면 opportunity 자체가 없고 terminal outcome도 없다.
`abstain`은 이미 형성된 opportunity를 미래 window 부족 등으로 평가할 수 없을 때만 나온다.

## 3. Rule이 깨졌다는 것은 무엇인가?

고정 horizon 뒤 target의 3개 행 median이 정상 데이터에서 결속된 expected direction과
noise 조건을 만족하지 못했다는 실행 계약상의 뜻이다. 물리적 원인이나 causal root cause를
증명하는 뜻이 아니다.

## 4. PASS와 FAIL은 무엇인가?

- PASS shorthand는 실제 코드의 `evaluated_expected_response`이며 alarm이 아니다.
- FAIL shorthand는 `evaluated_anomaly`이며 그 decision index에 alarm을 만든다.
- ABSTAIN은 평가 불가능 상태이고 alarm이 아니다.
- 권한·custody·replay 오류는 hard system error이며 abstain이 아니다.

## 5. 42개 결과를 어떻게 D1 alarm으로 만드는가?

어느 Rule이든 `evaluated_anomaly`이면 해당 decision second가 D1 alarm이 된다. Frozen artifact는
6,031 opportunity record와 788 anomalous rule record를 담지만, 같은 시점 중복을 제거하면
630 unique alarm seconds다. 이어진 seconds를 묶은 626 episodes는 metric 단계의 별도 산출물이다.

## 6. Trace에는 무엇이 들어가는가?

Frozen D1 trace는 opportunity, source-event hash, relation hash, terminal state, alarm,
decision index, numeric reference IDs, computation identity를 묶은 task-specific terminal hash다.
단계별 `RuntimeTraceV1` 객체는 저장하지 않았다.

## 7. D1 prediction은 label보다 먼저 정해지는가?

그렇다. 전체 label-blind prediction object를 만든 뒤 검증하고 shallow-frozen 상태로 custody를
확인한 후에 label-test1을 연다. 그래서 현재 분류는 **{runtime['freeze_classification']}**이다.

## 8. 왜 durable file freeze가 더 강한가?

현재 object는 top-level frozen dataclass이지만 내부 record dict는 mutable이고, public prediction
file은 metric 계산 뒤에 저장된다. Label 전에 bytes를 atomic하게 저장·재개방하고 label 뒤 동일
bytes를 다시 확인하면 process boundary가 생겨 더 강한 증거가 된다. Frozen pilot은 수정하지 않는다.

## 9. Runtime은 정말 LLM-free인가?

Frozen fixed-rule R0/D1 runtime에서는 LLM, provider, network call이 0이다. 이 문장을 미래 R1이나
전체 가능한 runtime 설계까지 일반화하면 안 된다.

## 10. 설명은 trace를 얼마나 그대로 반영하는가?

Canonical `RuntimeTraceV1`용 deterministic template renderer는 variable·lag·provenance binding을
재검증한다. 그러나 frozen V4 D1은 `RuntimeTraceV1`을 만들지도 renderer를 호출하지도 않았으며,
frozen D1 explanation artifact도 없다.

## 11. 설명이 root cause를 말할 수 있는가?

아니다. Canonical renderer는 causal/root-cause flag를 금지한다. 현재 보장 가능한 것은 canonical
synthetic path의 구조적 binding뿐이며 사람에게 유용한지는 **UNVALIDATED**다.

## 12. 현재 가장 중요한 runtime 위험은 무엇인가?

V4 frozen path와 canonical Rule/Trace 설명을 혼동하는 것, label 전 durable persistence가 없는 것,
그리고 설명 구현이 frozen D1에 실제 연결된 것처럼 표현하는 것이 가장 중요한 위험이다.

다음 task는 **{state['exact_next_task']}**이다.
"""


def render_arch007_user_summary(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    d0 = state["d0_detector"]
    return f"""{_markdown_marker(state, digest)}
# D0 PCA-SPE를 쉽게 이해하기

## 1. PCA는 왜 쓰는가?

37개 P1 변수가 정상일 때 함께 움직이는 큰 패턴을 작은 수의 축으로 요약하기 위해 쓴다.
D0는 이 정상 패턴에서 벗어난 정도를 보는 단순한 비교 기준선이다.

## 2. 정상 패턴을 어떻게 학습하는가?

Normal train1과 train2만 사용한다. 각 변수의 평균과 population 표준편차로 표준화하고,
custom NumPy PCA에서 누적 설명분산 0.95 이상이 되는 최소 축 수를 고른다. Frozen fit은
10개 축을 선택했고 27개 residual dimension을 남겼다.

## 3. SPE는 무엇인가?

한 시점의 37개 값을 PCA 정상 공간으로 복원한 뒤, 원래 표준화 값과 복원값 차이의 제곱을
합한 값이다. SPE가 크다는 것은 정상 PCA 공간으로 잘 설명되지 않는다는 뜻이다. Probability나
causal score는 아니다.

## 4. Threshold는 누가 정하는가?

이미 고정된 model로 normal train3의 SPE를 만들고 q=.999의 exact order statistic을 사용한다.
Interpolation은 없고, 정확한 판정은 `score > threshold`다. 같은 값은 alarm이 아니다.

## 5. Attack label을 보고 threshold를 정했는가?

아니다. Fit은 train1+train2 normal, calibration은 train3 normal이고 artifact에는
`labels_used=false`, `test_used=false`가 결속돼 있다. Test1 label은 durable prediction 파일을
쓰고 다시 검증한 뒤에만 열린다.

## 6. test1에서는 무엇을 하는가?

54,000개 test1 feature row에 frozen scaler/PCA/threshold를 적용해 label-blind Boolean prediction을
만든다. 공개 prediction은 raw score나 private threshold가 아니라 row index, alarm 여부와 hash를 담는다.

## 7. 11/14와 FAR/hour는 무엇인가?

| Level | Frozen pilot meaning |
|---|---|
| Point alarm | 876개 row가 threshold를 넘음 |
| Alarm episode | 연속 alarm point를 묶은 46개 구간 |
| Attack-event response | 통계적 독립성이 미확인된 14개 연속 사건 단위 중 11개가 alarm episode와 겹침 |
| Normal false episode | 46개 중 attack timestamp와 겹치지 않은 7개 |
| 시간당 정상 오경보율 (Normal FAR/hour) | 7개 normal false episode를 normal exposure hour로 나눈 `{d0['normal_far_episodes_per_hour']}` |

FAR/hour는 point false-positive rate가 아니다. 11/14도 point recall이 아니라 attack-event recall이다.

## 8. 왜 D0를 SOTA detector라고 하면 안 되는가?

D0는 선형 PCA residual을 쓰는 단순하고 추적 가능한 reference detector다. 현재 비교는 강한 최신
multivariate TSAD 전체를 대표하지 않는다. D0는 thesis contribution이 아니며 frozen 결과는 14-event
INNER pilot일 뿐이다.

## 9. D0와 Rule-only를 비교하는 목적은 무엇인가?

서로 다른 원리의 reference detector와 verified relational Rule-only가 어떤 사건에 반응하고 어떤
false-alarm trade-off를 보이는지 분리해서 관찰하는 것이다. 현재 결과로 어느 쪽의 일반적 우수성을
결론내리면 안 된다.

## 10. 앞으로 stronger detector가 왜 필요한가?

Rule-only 기여를 설득력 있게 평가하려면 새 독립 사전등록에서 더 많은 사건과 적어도 하나의 더
강한 multivariate detector baseline이 필요하다. ARCH-007은 그 detector를 선택하거나 구현하지 않았다.

기억할 한 문장: **D0는 normal-only로 고정된 단순 reference detector이고, 점수·point·episode·event를
구분해야 하며, 14-event 수치는 pilot evidence다.**

다음 task는 **{state['exact_next_task']}**이다.
"""


def render_arch008_user_summary(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    d1 = state["d1_evaluation"]
    return f"""{_markdown_marker(state, digest)}
# D1 검증된 관계 규칙 단독 평가를 쉽게 이해하기

## 1. D1은 정확히 무엇인가?

D1은 COMMON-42의 42개 verified relational descriptor를 V4 고정 runtime으로 실행한
Rule-only 방식이다. 직접 T2 Agentic arm이나 특정 LLM arm의 runtime 결과가 아니다.

## 2. 788, 630, 626은 왜 다른가?

| 숫자 | 뜻 |
|---:|---|
| 6,031 | Rule을 실제로 평가할 수 있었던 relation opportunity |
| 788 | anomaly로 끝난 rule-opportunity record |
| 630 | 여러 Rule의 같은 시점 경보를 합친 unique alarm second |
| 626 | 연속 alarm second를 묶은 total alarm episode |
| 574 | 626 episode 중 attack timestamp와 겹치지 않은 normal false episode |

## 3. 13/14는 무슨 뜻인가?

Test1의 14개 연속 label-one attack event 중 13개가 적어도 하나의 D1 alarm episode와
직접 겹쳤다는 attack-event Recall이다. Point recall이나 precision이 아니다.

## 4. 40.5 FAR/hour는 무슨 뜻인가?

51,019 normal labeled second에서 나온 574 normal false episode를 normal exposure hour로
나눈 값이 `{d1['normal_far_episodes_per_hour']}`이다. Point false-positive rate가 아니다.

## 5. 공격은 많이 잡으면서 오경보도 많은 이유는?

현재 증거가 보장하는 것은 **그 두 현상이 동시에 관찰되었다**는 사실뿐이다. Frozen report에는
high FAR의 일반적 원인 분석이 없으므로 trigger, tolerance, duplication 중 하나를 원인으로 단정하면
안 된다. 상태는 `CAUSE_NOT_YET_ANALYZED`다.

## 6. D1은 D0보다 좋은가?

그렇게 결론내릴 수 없다. D1은 event response가 13/14로 D0의 11/14보다 높았지만, normal FAR은
40.50255787059723으로 D0의 0.4939336325682589보다 훨씬 높았다. 민감도와 false-alarm burden은
별도 축이다.

## 7. D1은 D0와 다른 정보를 보는가?

현재 pilot response는 다르다. 둘 다 10개, D0만 1개, D1만 3개, 둘 다 놓친 사건 0개였다.
이는 response diversity를 보여주지만 원인이나 일반화는 증명하지 않는다.

## 8. D1이 D0가 놓친 3개 사건에 반응했다는 의미는?

현재 14-event INNER pilot에서만 확인된 중요한 signal이다. Allowed wording은 “D1이 D0 miss 3개
모두에 반응했다”이다. “Rule이 일반적으로 detector miss를 복구한다”는 아직 금지된 표현이다.

## 9. Complementarity가 입증됐는가?

아니다. Pilot complementarity signal은 있지만 statistical/general complementarity와 operational
utility는 **UNVALIDATED**다. D2 fusion policy와 결과 lineage는 ARCH-009에서 별도로 감사됐다.

## 10. D1은 LLM Rule-only 또는 Agentic Rule-only인가?

직접 LLM-arm runtime은 `NOT_DIRECTLY_TESTED`다. T2는 COMMON-42에서 제외되므로 Agentic Rule-only는
`MISLEADING_NOT_APPLICABLE`이다. 현재 이름은 **{d1['preferred_name']}**이다.

## 11. Prediction은 label보다 먼저 정해졌는가?

완전한 label-blind prediction object가 label open 전에 검증되었다. 그러나 그 시점에 atomic file로
durably persisted되지는 않았다. 현재 pilot에서 verified leakage는 없지만 future validation에는 더 강한
durable gate가 필요하다.

## 12. 앞으로 무엇을 검증해야 하는가?

더 큰 독립 사건 집합, validation/final-test 분리, durable pre-label persistence, stronger detector,
사전 고정된 comparison/fusion policy가 필요하다.

기억할 한 문장: **D1은 D0와 다른 pilot event response를 보였지만 normal false-alarm 부담이 매우 높아,
Rule-only utility와 complementarity는 아직 검증되지 않았다.**

다음 task는 **{state['exact_next_task']}**이다.
"""


def render_arch009_user_summary(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    d2 = state["d2_fusion"]
    return f"""{_markdown_marker(state, digest)}
# D2에서 Detector와 Rule을 어떻게 합쳤는가

## 1. 왜 D0와 D1을 합치려고 했는가?

D0가 놓친 3개 attack-event unit에 D1은 모두 반응했다. 그래서 D0 alarm은 지키면서 신뢰할 만한
D1 evidence만 추가하면 detector miss를 줄일 수 있는지 시험했다. D2는 이 질문을 위한
deterministic fusion-policy pilot이다.

## 2. D2 V1은 무엇인가?

같은 `decision_physical_row_index`, 즉 같은 1초 decision row에서 alarm을 낸 D1 source를 센다.
같은 source의 여러 rule은 한 번만 세고, 서로 다른 source가 2개 이상이면 D1 alarm을 추가한다.
D0가 이미 alarm이면 항상 유지한다.

## 3. 왜 distinct sources >= 2를 쓰는가?

한 source의 여러 relation record가 우연히 중복되어도 여러 독립 source evidence처럼 세지 않기 위한
frozen corroboration contract다. 이 threshold가 과학적으로 최적이라는 뜻은 아니다.

## 4. “same-second”는 정확히 무엇인가?

D1 record의 `decision_physical_row_index`가 정확히 같은 경우다. Source trigger 시점이나 attack
episode 전체가 아니다. Rolling window나 tolerance도 없다.

## 5. D2 V2는 V1과 무엇이 다른가?

V2는 D1 alarm을 한 row에서만 보지 않고 relation의 frozen native horizon 끝까지 active token으로
유지한다. 그 시간에 동시에 active한 서로 다른 source가 2개 이상이면 추가한다. D0 preservation과
source threshold 2는 그대로다.

## 6. native horizon/persistence는 실제 무엇인가?

Alarm decision index가 `i`, frozen relation horizon이 `h`라면 token은 `i <= t <= i+h`에서 active다.
별도의 연속 alarm 횟수 threshold나 learned persistence model은 없다.

## 7. D1은 3개를 잡았는데 왜 D2는 못 잡았는가?

V1에서는 두 unit의 여러 source alarm이 같은 row에 맞지 않았고 한 unit은 source가 하나뿐이었다.
V2는 temporal activity를 늘렸지만 frozen result상 세 unit 어디에도 추가 alarm을 admit하지 못했다.
Single-source unit은 정책상 제외되며, 나머지 두 unit의 V2 상세 원인은 public frozen trace만으로는
확정할 수 없다. 핵심은 **D1 response와 D2 admission은 다른 조건**이라는 점이다.

## 8. D2 V1 결과는 D0보다 좋은가?

현재 pilot metric으로는 아니다. D0와 같은 11/14였고 Normal FAR은
{d2['v1']['normal_far_episodes_per_hour']}로 D0의 0.4939336325682589보다 높았다. Recovery는
{d2['v1']['d0_miss_recovery']}였다.

## 9. D2 V2 결과는 D0보다 좋은가?

아니다. V2도 11/14, recovery {d2['v2']['d0_miss_recovery']}였고 Normal FAR은
{d2['v2']['normal_far_episodes_per_hour']}로 더 높았다. 이는 현재 test1 descriptive result이며
새로운 통계 비교를 한 것이 아니다.

## 10. 왜 V2는 독립 검증이 아닌가?

V1 negative result와 test1 diagnostic이 V2 문제 설정을 informed했고 동일 test1에서 평가됐다.
V2 결과 자체는 freeze 전에 보지 않았지만 validation/final-test가 분리되지 않았으므로
`TEST1_INFORMED_DEVELOPMENT`이다.

## 11. 현재 Detector+Rule에 대해 무엇을 말할 수 있는가?

D0/D1 response diversity는 pilot에서 관찰됐다. 하지만 현재 V1/V2는 그 diversity를 incremental
attack-event recall로 바꾸지 못했고 normal FAR을 늘렸다. 이것은 현재 두 policy의 negative pilot
result이지 Detector+Rule 전체가 쓸모없다는 증거가 아니다.

## 12. 앞으로 무엇을 검증해야 하는가?

더 큰 evaluation scope, event-unit definition freeze, validation/final-test 분리, final test 전에 고정된
fusion policy, stronger detector, durable upstream prediction, preregistered incremental Recall/FAR와
D0-miss recovery가 필요하다.

기억할 한 문장: **D1의 다른 response가 관찰됐지만, 현재 V1/V2 gate는 이를 recall 증가로 바꾸지
못했고 V2는 독립 검증이 아니다.**

다음 task는 **{state['exact_next_task']}**이다.
"""


def render_arch010_user_summary(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    return f"""{_markdown_marker(state, digest)}
# 성능 숫자를 어떻게 읽어야 하는가

## 1. alarm point와 episode는 무엇이 다른가?

Point는 한 physical row의 alarm이다. Episode는 중복을 없앤 alarm row 가운데 정확히 1행씩
이어지는 최대 구간이다. D0의 876 points가 46 episodes가 되는 이유다.

## 2. D1 rule record와 alarm second는 무엇이 다른가?

같은 second에 여러 rule이 깨질 수 있다. Frozen D1의 788 anomalous records는 row 중복을 없애면
630 alarm seconds이고, 이를 연속 구간으로 묶으면 626 episodes다.

## 3. attack-event unit은 무엇인가?

Strict label `1`이 연속되는 최대 구간이다. test1에는 14 contiguous units가 있다.

## 4. 왜 14개를 독립 사건이라고 하면 안 되는가?

연속 label grouping은 operational unit만 만든다. unit 사이의 통계적 독립성 분석은 없었다.

## 5. 11/14와 13/14는 어떻게 계산되는가?

Alarm episode가 attack unit과 한 row라도 겹치면 그 unit은 detected다. D0는 11개, D1은 13개를
detected했다. Point recall이나 precision이 아니다. Grace window나 point adjustment도 없다.

## 6. FAR/hour는 무엇인가?

Attack unit과 전혀 겹치지 않는 normal false episodes를 51,019 normal seconds의 시간으로 나눈
episodes/hour다. D0 0.4939336325682589, D1 40.50255787059723, V1 0.7056194750975128,
V2 6.915070855955625다.

## 7. 왜 point FPR과 다른가?

분자는 false point 수가 아니라 grouped episode 수다. 분모도 normal point 비율이 아니라 exposure hours다.

## 8. D0/D1/D2를 같은 metric으로 비교할 수 있는가?

같은 test1, event units, exposure, overlap, episode grouping, Recall/FAR 공식을 사용하므로 common
interface 비교는 가능하다. 다만 D0/D2는 모든 row를 평가하고 D1은 opportunity-driven이므로
`FAIR_WITH_LIMITATIONS`다.

## 9. D1 abstain/non-opportunity는 metric에서 어떻게 처리되는가?

Alarm timestamp를 만들지 않아 Boolean interface에서는 `NO_ALARM`처럼 작동한다. Runtime의
ABSTAIN/NO_OPPORTUNITY 의미 자체가 정상 판정으로 바뀌었다는 뜻은 아니다. Frozen abstain은 0이다.

## 10. result integrity audit은 무엇을 보장하는가?

Prediction/label identity, ordering, row closure, arithmetic, mutation/replay, report binding을 보장한다.
D0/D2는 durable pre-label file gate가 있고 D1은 더 약한 in-memory object gate다.

## 11. 왜 integrity PASS가 성능 검증 PASS가 아닌가?

Integrity는 sample size, event independence, development-set reuse, generalization, superiority, utility를
검사하지 않는다. V2도 여전히 test1-informed development다.

## 12. 현재 pilot 결과에서 무엇까지 믿어도 되는가?

고정 artifact에 기록된 현재 pilot의 descriptive Recall/FAR와 D0/D1 response diversity까지다. 일반
complementarity, held-out generalization, 통계적 우수성은 미확인이다.

기억할 한 문장: **결과 무결성은 숫자가 고정 artifact와 맞는지 보장하지만, 그 숫자가 일반 성능을
증명하는지는 보장하지 않는다.**

ARCH-011은 완료되었다. 다음 관리 task는 **{state['exact_next_task']}**이다.
"""


def render_gap000_user_summary(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    readiness = state["pre_validation_readiness"]
    return f"""{_markdown_marker(state, digest)}
# 본격 실험 전에 무엇을 고쳐야 하는가

## 지금까지 감사 결과 한 문장

ARCH-000~010의 120개 mismatch는 {readiness['root_issues']}개 root issue로 줄어들며, frozen pilot을
무효화하는 결함은 발견되지 않았지만 미래 final validation 전에 닫아야 할 authority, custody,
evaluation-design gate가 있다.

## 현재 연구를 무효로 만드는 문제가 발견됐는가

아니다. 무효화된 frozen artifact는 0개다. 현재 pilot은 V4 authority, D1의 더 약한 in-memory
pre-label gate, test1 development scope, 14 contiguous event units, held-out 부재라는 조건을 붙여
해석할 수 있다. 새 remediation은 PILOT V1을 고치지 않고 VALIDATION V2로 version을 나눈다.

## 반드시 고쳐야 하는 것

1. `P0_FIX_BEFORE_EXPANDED_VALIDATION`이었던 최종 scientific execution authority는 Formal V4로 결정·version 고정됐고,
   version과 test를 고정한다.
2. 새 D1 evaluation은 prediction을 label 전에 atomic persist, close, reopen/replay하고 label access를
   authorize해야 한다.

## 특정 실험 전에만 고치면 되는 것

아래는 primary disposition `P1_FIX_BEFORE_SPECIFIC_EXPERIMENT`이다. Urgency priority P1과 같은 축이 아니다.

- EXP-01 전: GDN Top-5 self-neighbor convention을 고치거나 명시적으로 ablation한다.
- EXP-03 전: `no_rule`과 provider/parse/verifier/budget failure를 분리한다.
- EXP-05 전: 실제 evaluated trace와 deterministic explanation renderer를 연결한다.

## 코드 문제가 아니라 실험 설계 문제인 것

- validation과 final test 역할, fusion policy selection 시점을 미리 고정한다.
- 14개를 독립 사건이라고 가정하지 말고 event-unit 정책과 분석 방법을 사전등록한다.
- EXP-04 final claim에는 PCA-SPE 외 stronger multivariate detector가 필요하다.
- GDN contribution은 seed/split stability, unique confirmed yield, masking, Top-20 sensitivity로 검증한다.
- Agentic contribution은 budget-matched 반복 실험에서 feedback이 실제 작동하고 이득을 보이는지 본다.

## 그냥 limitation으로 남겨도 되는 것

- train3가 normal-only relation confirmation과 D0 calibration에 함께 쓰였다는 점.
- 현재 D1 high FAR의 일반 원인이 아직 분석되지 않았다는 점.
- explanation의 인간 유용성이 아직 평가되지 않았다는 점.

## 지금 하지 않아도 되는 것

Runtime LLM, causal discovery, 복잡한 hierarchy/tree relation, multi-agent runtime, production fusion,
대규모 human study는 현재 석사 논문의 최소 경로에 필요하지 않다.

## 가장 안전한 다음 진행 순서

1. 완료된 GAP-000과 read-only ARCH-011의 사실을 검토한다.
2. final authority를 결정한다.
3. 승인된 authority remediation만 좁게 구현한다.
4. 필요한 실험별 P1만 닫고 protocol을 결과 전에 freeze한다.
5. development/validation 실험 뒤 fresh-machine rehearsal을 완료한다.
6. 마지막에 새 preregistered held-out study를 한 번 실행한다.

## 내가 결정해야 하는 것

1. Final authority는 Formal V4로 결정됐다. 다음 결정 전 작업은 durable custody와 protocol freeze다.
2. Graph-Guided와 Agentic의 conditional 유지 정책은 이미 승인되었다. 최종 포함 여부는 EXP-01/EXP-03
   결과가 결정한다.

기억할 한 문장: **pilot은 보존하고, final validation에 꼭 필요한 authority와 custody만 먼저 고친다.**

다음 task는 **{state['exact_next_task']}**이다. ARCH-011은 이 remediation이나 test2 access를
자동으로 허가하지 않는다.
"""


def render_arch011_user_summary(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    outer = state["outer_reproducibility"]
    return f"""{_markdown_marker(state, digest)}
# OUTER와 재현성을 쉽게 이해하기

## 1. OUTER가 정확히 무엇인가?

개발에 쓰지 않은 held-out test2에서 frozen D0/D1/D2 V1을 한 번 확인하려던 confirmatory study다.

## 2. 왜 결과가 없는가?

유일한 시도가 시작된 뒤 첫 feature custody 검사에서 파일을 열기 전에 중단되었다. Prediction과 metric이 없으므로 성능 결과도 없다.

## 3. test2 내용은 본 적이 있는가?

Custody check는 1회였지만 feature bytes/hash/parse와 labels는 모두 0이다. 즉 과학 내용은 보지 않았다.

## 4. 그냥 다시 실행하면 왜 안 되는가?

One-shot attempt가 소비되었고 retry 권한이 0이기 때문이다. 구 protocol은 `NOT_RETRYABLE_BY_PROTOCOL`이며 새 study와 preregistration이 필요하다.

## 5. 새 held-out은 어떻게 해야 하는가?

Data, method, authority, event unit, metrics, fusion policy, environment, prediction-before-label 순서를 결과 전에 고정해야 한다. 같은 test2 reuse 여부도 새 연구가 명시적으로 결정해야 한다.

## 6. traceability와 reproducibility는 뭐가 다른가?

Traceability는 source/artifact lineage를 찾는 능력이다. Reproducibility는 다른 환경에서 같은 절차와 출력을 다시 만드는 능력이다.

## 7. same-machine과 fresh-machine은 뭐가 다른가?

같은 PC에는 local asset과 environment가 남아 있다. Fresh machine은 dependency, schema, Git authority, private restoration을 처음부터 재구성해야 한다.

## 8. 현재 프로젝트는 어디까지 재현 가능한가?

Traceability는 `{outer['reproduction_levels']['traceability']}`이고 same-machine은 `{outer['reproduction_levels']['same_machine_replay']}`다. Fresh-machine synthetic/scientific reproduction은 아직 입증되지 않았다.

## 9. PILOT V1과 VALIDATION V2를 왜 나누는가?

과거 결과를 새 code와 protocol로 소급 변경하지 않기 위해서다. V1은 그대로 보존하고 remediation 결과는 V2로만 평가한다.

## 10. 어떤 authority option이 가장 현실적인가?

DEC-020은 lossless equivalence를 강제하지 않고 Formal V4를 별도 VALIDATION V2 authority로 선택했다. canonical RuleV1·VerifierV1 authority는 주장하지 않는다.

## 11. fresh-machine rehearsal은 언제 해야 하는가?

Authority/dependency/entrypoint remediation 뒤, held-out 접근 전이다. 첫 rehearsal은 synthetic/public 단계에서 멈춘다.

## 12. 논문 공개본에는 무엇을 포함해야 하는가?

Source, tests, schemas, synthetic fixture, public configs, RCC docs, lock과 guide를 포함한다. Raw/private data, test2, credentials, private numeric/model payload는 제외한다.

기억할 한 문장: **현재 연구는 잘 추적되지만, 새 컴퓨터에서 과학 결과를 다시 만드는 상태는 아직 아니다.**

다음 task는 **{state['exact_next_task']}**이다. ARCH-011은 이 remediation을 실행하지 않았다.
"""


def render_change_summary(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    authority = state["scientific_authority"]
    events = sorted(data["timeline"], key=lambda row: (row["date"], row["event_id"]), reverse=True)
    rows = "\n".join(
        f"- **{row['date']} — {row['title']}** (`{row['status']}`): {row['summary']}"
        for row in events
    )
    return f"""{_markdown_marker(state, digest)}
# RCC Change Summary

Scientific authority: `{authority['ref']}` @ `{authority['commit']}`
Registry version: `{state['registry_version']}`

## Recorded timeline

{rows}

## Next

**{state['exact_next_task']}**
"""


def render_current_context(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    authority = state["scientific_authority"]
    pilot = state["pilot_observations"]
    return f"""{_markdown_marker(state, digest)}
# Current Research Context

Last updated: {state['last_updated']}
Scientific authority: `{authority['ref']}` @ `{authority['commit']}`
Documentation overlay: `{state['documentation_overlay']['ref']}` @ `{state['documentation_overlay']['commit']}`
RCC version: `{state['rcc_version']}`

## Current Phase

ARCHITECTURE_COMPLETE → **EVALUATION_SCOPE_EXPANSION (CURRENT)** → HYPOTHESIS_VALIDATION

Architecture implementation and pilot operation are complete. Scientific validation is partial,
held-out generalization is unconfirmed, and fresh-machine reproduction is incomplete.

## HOW TO READ STATUS

- Implemented and Executed describe engineering state.
- Evidence-reviewed is the backward-compatible component `audited` field: source or evidence
  status was reviewed. It does not mean performance validation.
- Result-integrity audited applies only to an explicit result-specific integrity artifact and
  checks custody and arithmetic. It does not mean scientific validation.
- Independently reproduced is a separate state and is currently zero at component level.
- `claims.csv` alone controls authoritative scientific claim status. Component `claim_ready`
  supports narrow implementation or contract wording only.

These states are not a single completion percentage. Evidence-reviewed can exceed Executed
because governance and documentation evidence can be reviewed without scientific execution.

## WHAT EXISTS

The pinned repository contains the end-to-end HAI 23.05 P1 INNER path: provenance and
split governance, a 144-pair role universe, META/STAT/GDN candidate discovery, a 47-pair
union, normal temporal profiling, normal-only numeric authority, typed evidence, bounded
T0/T1/T1-B/T2 construction, deterministic verification, COMMON-42, LLM-free fixed-rule
runtime, D0/D1/D2 evaluation, event/episode metrics, and integrity audits.

## DATA / SPLIT FOUNDATION

- **Dataset / process:** {state['data_governance']['dataset']} / {state['data_governance']['process']}.
- **Roles:** train1/train2 normal fit; train3 relation confirmation plus D0 calibration;
  train4 normal sanity; test1 INNER pilot; test2 held-out result unavailable.
- **Label ordering:** {state['data_governance']['label_access']}
- **Leakage finding:** {state['data_governance']['leakage_status']}

## EVALUATION EXPANSION (PLAN ONLY)

- **Development:** HAI 23.05 test1 — existing 14-scenario DEVELOPMENT_ONLY result; immutable and not reopened.
- **Primary held-out:** HAI 23.05 test2 — 38 nominal scenarios; DG-05 required before any access.
- **External replication 1:** HAI 22.04 — 58 nominal scenarios; compatibility and normal-only re-instantiation first.
- **External replication 2:** HAI 21.03 — 50 nominal scenarios; compatibility and deterministic normal split first.
- **Interpretation:** the 146 non-development scenarios are not IID. Primary results are version-specific;
  P1 eligibility is frozen outcome-blind before denominators, and pooled Recall is descriptive only with an explicit warning.
- **Metrics:** P1-eligible Scenario Recall and normal false episodes/hour are primary; eTaPR,
  coverage, delay, overlap, and uncertainty are secondary under a pinned pre-label contract.

## CANDIDATE DISCOVERY FOUNDATION

- **Universe:** {state['candidate_discovery']['candidate_universe']}.
- **META:** reviewed metadata domain-prior candidate ranking.
- **STAT:** normal train1/train2 directional lagged-association candidate ranking.
    - **GDN / PILOT V1:** embedding-cosine learned-graph candidate ranking; attention and post-hoc XAI were not final Pilot evidence.
    - **PILOT V1 union:** {state['candidate_discovery']['union']}.
    - **VALIDATION V2A:** META+STAT 29-pair union, 39 confirmed directional relations, and 39-rule Formal V4 portfolio are frozen.
    - **EXP-01B:** nine CUDA runs compared Embedding, Attention, EdgeMask, and Source Occlusion; the frozen disposition is `GDN_ABLATION_ONLY`.
- **Boundary:** {state['candidate_discovery']['warning']}

## RULE CONSTRUCTION FOUNDATION

- **Evidence view:** {state['rule_construction_authority']['evidence_view']}.
- **Withheld:** {state['rule_construction_authority']['withheld']}.
- **Lifecycle:** {state['rule_construction_authority']['lifecycle']}.
- **Agentic boundary:** {state['rule_construction_authority']['agentic_claim']}

## FROZEN D1 RUNTIME / TRACE FOUNDATION

- **Authority:** {state['runtime_trace_explanation']['authority']}
- **Evaluation:** {state['runtime_trace_explanation']['evaluator']}
- **Prediction:** {state['runtime_trace_explanation']['prediction']}
- **Freeze / labels:** {state['runtime_trace_explanation']['label_access']}
- **Trace:** {state['runtime_trace_explanation']['canonical_trace_relationship']}
- **Explanation:** {state['runtime_trace_explanation']['explanation']}

## WHAT WAS EXECUTED

- All three discovery arms produced evidence-reviewed top-20 rankings.
- Profiling produced 23 pair contexts and 42 frozen directed relations.
- T0, T1, T1-B, and T2 executed; their accepted counts were 42, 42, 42, and 39.
    - Frozen integrity-audited INNER results exist for D0, D1, D2 V1, and D2 V2.
    - Normal-only VALIDATION V2 EXP-01, EXP-01B, and EXP-02 completed without test or label access.
- The OUTER bridge produced a blocker record only; it produced no scientific outcome.

## WHAT WAS OBSERVED

- D0: {pilot['d0']}
- D1: {pilot['d1']}
- Event overlap: {pilot['overlap']}.
- D2 V1: {pilot['d2_v1']}.
- D2 V2: {pilot['d2_v2']}.
- T2 feedback actions: zero; the current cohort did not exercise feedback recovery.

These are frozen observations from 14 contiguous INNER attack-event units. Statistical
independence is not established; they are pilot evidence only and are not validated performance conclusions.

## WHAT IS VALIDATED

The narrow implementation statements are supported: deterministic authority controls exist;
normal-data evidence can be transformed into bounded executable rules; the verifier checks
structural, evidence, parameter, split, and operational contracts; and the current fixed-rule
runtime is LLM-free and deterministic given frozen authorities. Integrity audits validate
artifact custody and arithmetic, not generalization, superiority, causality, or human usefulness.

## WHAT REMAINS UNKNOWN

{_md_bullets(state['current_unvalidated'])}

## Current highest-priority work

{_md_bullets(state['top_priorities'])}

Exact next management task: **{state['recommended_next_management_task']}**
Following architecture task: **{state['recommended_next_architecture_task']}**
"""


def render_my_todo(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    grouped: dict[str, list[Mapping[str, str]]] = {}
    for item in state["user_todo_items"]:
        grouped.setdefault(item["category"], []).append(item)
    heading_labels = {
        "DECISION NEEDED": "결정 필요",
        "UNDERSTANDING NEEDED": "이해 필요",
        "REVIEW NEEDED": "검토 필요",
        "WAITING ON CODEX": "Codex 작업 대기",
        "APPROVED POLICY": "승인된 정책",
        "PRESERVATION": "보존 원칙",
        "DECISION LATER": "추후 결정",
        "MANDATORY FUTURE GATE": "필수 향후 Gate",
        "REVIEW REQUIRED": "검토 필요",
    }
    sections: list[str] = []
    for heading, display_heading in heading_labels.items():
        items = grouped.get(heading, [])
        body = "\n\n".join(
            f"- **ID:** {item['id']}\n  **우선순위:** {({'HIGH': '높음 (HIGH)', 'MEDIUM': '중간 (MEDIUM)', 'LOW': '낮음 (LOW)'}).get(item['priority'], item['priority'])}\n  **할 일:** {item['task']}\n  **사용자 확인이 필요한 이유:** {item['why']}\n  **연결 문서:** {item['linked']}\n  **상태:** {STATUS_DISPLAY_LABELS.get(item['status'], item['status'])}"
            for item in items
        ) or "현재 항목이 없습니다."
        sections.append(f"## {display_heading}\n\n{body}")
    return f"""{_markdown_marker(state, digest)}
# 내가 해야 할 연구 검토

{front_markdown(data['front_results'])}

이 문서는 낮은 수준의 개발 작업이 아니라 연구 책임자가 확인하거나 결정할 항목을 모은다.

{chr(10).join(sections)}

과학 source authority: `{state['scientific_authority']['commit']}`
"""


def render_decision_inbox(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    unresolved = [row for row in data["decisions"] if row["status"] == "OPEN"]
    body = "\n\n".join(
        f"## {row['decision_id']} — {DECISION_CARD_COPY.get(row['decision_id'], (row['title'], row['reason']))[0]}\n\n**필요한 이유:** {DECISION_CARD_COPY.get(row['decision_id'], (row['decision'], row['reason']))[1]}\n\n**registry 원문 결정:** {row['decision']}\n\n**registry 원문 이유:** {row['reason']}"
        for row in unresolved
    ) or "현재 미결정 사용자 항목은 없다. RCC-000의 결정 001·002는 `registry/decisions.csv`에서 승인 상태를 유지한다."
    if state.get('exp03b_preparation'):
        body='## DG-03B — EXP-03B provider 실행 승인 필요\n\n상태 USER_DECISION_REQUIRED. 최대609회 / 81,621,225 tokens / USD65.90. 승인 snapshot gpt-5.4-mini-2026-03-17. 현재 provider0이며 기존 DG-03 승인은 상속하지 않습니다.\n\n[정확한 예산·privacy brief](validation_v2/exp03b/DG03B_PROVIDER_DECISION_BRIEF_V1.md)\n\nDEC-024 SCI-01~04 과학 결정은 승인 완료이지만 이 별도 provider 예산은 미승인입니다. DG-04는 EXP03B 이후로 연기합니다.'
    return f"""{_markdown_marker(state, digest)}
# 결정이 필요한 사항

{front_markdown(data['front_results'])}

{body}

과학 source authority: `{state['scientific_authority']['commit']}`
"""


def render_user_summary(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    pilot = state["pilot_observations"]
    top_risks = [row["description"] for row in data["risks"] if row["severity"] in {"CRITICAL", "HIGH"}][:5]
    return f"""{_markdown_marker(state, digest)}
# 지금 연구는 어디까지 왔나

## 한 문장 상태

HAI 23.05 P1을 대상으로 한 전체 INNER 연구 경로는 구현되고 예비 실행 및 무결성
감사까지 끝났지만, 과학적 가설 검증·홀드아웃 일반화·새 컴퓨터 재현은 아직 끝나지 않았다.

## 상태 라벨 읽는 법

- **구현됨 / 실행됨**은 엔지니어링 상태다. 성능 검증을 뜻하지 않는다.
- **Evidence-reviewed**는 소스나 공개 증거 상태를 고정 권한과 대조했다는 뜻이다.
  과학적 성능을 감사하거나 검증했다는 뜻이 아니다.
- **Result-integrity audited**는 명시된 고정 결과의 보관·불변성·순서·산술을 확인했다는
  뜻이다. 우수성이나 일반화를 입증하지 않는다.
- **Independently reproduced**는 필요한 환경과 custody에서 독립 재현했다는 별도 상태다.
- 과학적 주장의 허용 범위는 오직 `claims.csv`가 결정한다. 구성요소의 호환용
  `claim_ready` 필드는 좁은 구현·계약 문구만 지원하며 과학적 성능 검증을 뜻하지 않는다.

이 숫자들은 하나의 연구 완료율이 아니다.

## 이미 만들어진 것

데이터 출처와 분할 통제에서 시작해 META·STAT·GDN 후보 탐색, 관계 프로파일링,
normal-only 수치 권한, 규칙 생성, 결정론적 검증기, COMMON-42 고정 규칙, LLM 없는
고정 규칙 런타임, D0/D1/D2 평가와 결과 무결성 감사까지 이어지는 구조가 있다.

## 실제 실행된 것

- 144개 가능한 관계에서 META·STAT·GDN이 각각 top-20을 만들었고 합집합은 47개였다.
- 23개 pair context에서 42개 방향성 시간 관계가 확인되어 COMMON-42로 고정되었다.
- T0/T1/T1-B/T2 규칙 생성 경로가 모두 실행되었고 승인 수는 42/42/42/39였다.
- D0, D1, D2 V1, D2 V2의 INNER 결과가 고정되고 독립 무결성 감사를 받았다.
- OUTER는 실행 결과가 아니라 차단 기록만 있다.

## 현재 관찰된 결과

- D0: {pilot['d0']}.
- D1: {pilot['d1']}.
- 두 신호의 사건 겹침: {pilot['overlap']}.
- D2 V1: {pilot['d2_v1']}.
- D2 V2: {pilot['d2_v2']}.

이 수치는 통계적 독립성이 입증되지 않은 14개 연속 attack-event unit의 INNER 예비 관찰이다.
검증된 일반 성능으로 표현하면 안 된다.

## 아직 증명되지 않은 것

{_md_bullets(state['current_unvalidated'])}

특히 GDN의 고유 기여와 Agentic 피드백의 이점은 아직 가설이다. 현재 T2에서는 피드백
행동이 0회였으므로 Agentic 장점이 실험된 것으로 볼 수 없다. D1은 D0와 다른 사건에
반응했지만 정상 FAR가 높아 실용성을 주장할 수 없다. 현재 D2 정책도 개선 주장을 지지하지 않는다.

## 가장 큰 위험 5개

{_md_bullets(top_risks)}

## 다음에 해야 할 것

{_md_bullets(state['top_priorities'])}

관리 작업의 다음 단계는 **{state['recommended_next_management_task']}** 이고, 이후 전체
구조 검토는 **{state['recommended_next_architecture_task']}** 이다. 둘 다 사용자 승인 전에
자동으로 시작하지 않는다.

## 내가 직접 확인할 것

{_md_bullets(state['top_user_todo'])}

Scientific authority: `{state['scientific_authority']['commit']}`
"""


def render_project_timeline(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    phase_sections = []
    for index, phase in enumerate(data["history"]["phases"], start=1):
        phase_sections.append(
            f"""## {index}. {phase['title']}

**Period:** {phase['period']} (`{phase['date_precision']}`)

**Source class:** `{phase['source_class']}`

**Status:** `{phase['status']}` · **Confidence:** `{phase['confidence']}`

### Goal at the time

{phase['goal']}

### What was implemented / investigated

{phase['investigated']}

### What problem was found

{phase['problem']}

### Decision

{phase['decision']}

### What survived into the current method

{phase['survived']}

### What was abandoned or deferred

{phase['abandoned_or_deferred']}

### Evidence

{phase['evidence']}
"""
        )
    return f"""{_markdown_marker(state, digest)}
# Research Evolution

Scientific authority: `{state['scientific_authority']['commit']}`

This narrative explains why the architecture changed. It is not a replacement for
`registry/current_state.yaml` or `registry/claims.csv`. Early user-context stages keep
their approximate dates and confidence labels; later Git milestones use exact evidence.

{chr(10).join(phase_sections)}

## Current State

The architecture is substantially implemented and the INNER path has frozen pilot
observations. Scientific validation remains partial, held-out generalization remains
unconfirmed, and fresh-machine reproduction remains incomplete. The exact next task is
**{state['exact_next_task']}**.
"""


def render_professor_feedback_lineage(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    rows = "\n".join(
        f"| {item['date']} ({item['date_precision']}) | {item['feedback']} | {item['interpretation']} | {item['decision_ref']} | {item['effect']} | {item['classification']} / {item['confidence']} |"
        for item in data["history"]["professor_feedback_lineage"]
    )
    return f"""{_markdown_marker(state, digest)}
# Professor Feedback Lineage

Scientific authority: `{state['scientific_authority']['commit']}`

This is a decision lineage, not an email archive. Dates describe the evidence basis shown
in the final column. Retrospective response matrices do not create contemporaneous proof.

| Date | Professor feedback or record | Research interpretation | Decision | Implementation / experiment effect | Evidence class |
|---|---|---|---|---|---|
{rows}

## Temporal safeguards

- The pairwise continuous-step protocol was frozen on **2026-08-03**. The user-context
  2026-08-04 feedback may have reinforced or clarified pairwise-first scope; it did not
  originate the already-frozen protocol.
- **2026-08-18** is an internal progress update, not professor feedback.
- **2026-08-24** is the Git-supported professor-package preparation milestone, not proof
  of professor approval.
- **2026-08-26** is integrated report preparation in user context, not automatically new
  professor feedback.
"""


def render_superseded_directions(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    rows = "\n".join(
        f"| {item['direction']} | {item['period']} | {item['why_explored']} | {item['why_reduced']} | {item['survived']} | {item['replacement']} | {item['status']} | {'Yes' if not item['current_claim'] else 'No'} |"
        for item in data["history"]["superseded_directions"]
    )
    return f"""{_markdown_marker(state, digest)}
# Superseded and Conditional Directions

Scientific authority: `{state['scientific_authority']['commit']}`

Old documents may use these framings. Preserve them historically; do not reuse them as
current claims without current evidence.

| Direction | Period | Why explored | Why reduced or abandoned | What survived | Replacement | Status | Do not use as current claim? |
|---|---|---|---|---|---|---|---|
{rows}
"""


def render_terminology_guide(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    rows = "\n".join(
        f"| {item['term']} | {item['historical']} | {item['current']} | {item['deprecated']} |"
        for item in data["history"]["terminology"]
    )
    return f"""{_markdown_marker(state, digest)}
# Historical Terminology Guide

Scientific authority: `{state['scientific_authority']['commit']}`

| Term | Historical meaning | Current preferred meaning | Deprecated or guarded wording |
|---|---|---|---|
{rows}

Historical documents remain untouched. This guide controls current-facing interpretation.
"""


def render_history_confirmation(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    questions = []
    for item in data["history"]["confirmation_questions"]:
        questions.append(
            f"""## {item['id']}

**Question:** {item['question']}

**Why it matters:** {item['why']}

**Evidence found:** {item['evidence']}

**Suggested interpretation:** {item['suggested']}

**Confidence:** `{item['confidence']}`
"""
        )
    return f"""{_markdown_marker(state, digest)}
# History Confirmation Needed

Only high-value uncertainties are listed. Until confirmed, the conservative interpretation
in each item remains the RCC history boundary.

{chr(10).join(questions).rstrip()}
"""


def render_decision_record(row: Mapping[str, str], state: Mapping[str, Any], digest: str) -> str:
    return f"""{_markdown_marker(state, digest)}
# {row['decision_id']} — {row['title']}

## Date

{row['date']} (`{row['date_precision']}`)

## Status

`{row['status']}`

## Context

{row['context']}

## Alternatives Considered

{_md_bullets(row['alternatives_considered'].split(';'))}

## Decision

{row['decision']}

## Why

{row['reason']}

## Consequence

{row['consequence']}

## Current Relevance

{row['current_relevance']}

## Supersedes

{row['supersedes']}

## Superseded By

{row['superseded_by']}

## Evidence

Source class: `{row['source']}`

Reference: {row['source_ref']}

Source commit: `{row['source_commit']}`

## Confidence

`{row['confidence']}`
"""


def render_rcc003_history_summary(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    inheritance = data["history"]["current_method_inheritance"]
    return f"""{_markdown_marker(state, digest)}
# 우리 연구가 어떻게 여기까지 왔나

## 처음 무엇을 하려 했는가

사용자 기록에 따르면 2025년 말부터 DHAG 확장과 PoC를 검토했고, 2026년 봄에는
ARGOS·LLMAD 같은 관련 연구와 설명 충실도 검증 중심의 방향을 탐색했다. 이 초기
시기는 Git에 동시대 기록이 충분하지 않으므로 정확한 실패 원인이나 날짜를 확정하지
않는다.

## 왜 방향이 바뀌었는가

자유로운 LLM 규칙이나 설명을 과학적 권한으로 쓰면 변수·숫자·검증·실행의 책임이
불명확해진다. 7월의 저장소 기록은 ARGOS를 그대로 복제하기보다 유용한 요소만 남기고,
규칙 구조·수치 근거·검증·런타임을 분리하는 CPS 관계 규칙 방향을 보여 준다. HAI에서
기존 이산 제어원 가정이 실패했을 때도 기준을 완화하지 않고 연속 step-response 계열을
새로 사전등록했으며, 그 결과 P1만 선택되었다.

## 지금 방법에 남은 핵심 아이디어

- DHAG 시기: {inheritance['from_dhag']}
- ARGOS 탐색: {inheritance['from_argos']}
- Verifier 시기: {inheritance['from_verifier']}
- 교수님 피드백 재정리: {inheritance['from_professor_reframing']}
- 현재 조합: {inheritance['current_combination']}

## 버린 것 / 보류한 것

현재 핵심에서 제외된 것은 DHAG를 전면 방법으로 삼는 주장, Faithfulness Verifier가
과학적 진실을 증명한다는 주장, ARGOS의 직접 복제, HAI 이산 제어원 경로, 그리고
ARTIST식 학습 기반 segment 선택이다. 복잡한 관계와 runtime LLM은 틀렸다고 판정한
것이 아니라 별도 설계가 필요한 조건부 과제로 남아 있다.

## 교수님 피드백이 실제로 바꾼 것

2026-08-04 피드백은 사용자 기록으로 보존한다. pairwise-first 프로토콜은 이미
8월 3일 고정되어 있었으므로 이 피드백은 그 기원을 만든 사건이라기보다 범위와 표현을
강화한 것으로 기록한다. Rule-only를 fusion 안에 숨기지 않고 별도로 보며, verifier와
GDN과 agent라는 단어를 좁게 쓰고, 실행과 검증을 구분하는 방향이 이후 구현에 남았다.
8월 18일은 내부 진행 업데이트이고, 8월 26일은 통합 보고서 준비이지 새 교수님 피드백이 아니다.

## 현재 위치

HAI 23.05 P1에서 후보 탐색, normal-only 관계·수치 근거, COMMON-42, 고정 규칙 런타임,
D0/D1/D2 INNER 예비 평가와 결과 무결성 감사까지 구현되었다. 그러나 14개 사건 수치는
pilot evidence일 뿐이다. Rule-only 실용성, D2 개선, GDN 고유 기여, Agentic 이점,
사람 대상 설명 유용성, 홀드아웃 일반화는 아직 검증되지 않았다.

## 앞으로는 무엇을 검증해야 하는가

새 독립 사전등록 아래 더 많은 사건과 더 강한 다변량 탐지기 기준선으로 Rule-only와
detector 비교를 확장해야 한다. GDN 안정성과 고유 기여, 실제 피드백이 발생하는 T2 비교,
fresh-machine 재현도 별도로 검증해야 한다. 다음 관리 작업은 **{state['exact_next_task']}**이다.
"""


def generate_history_documents(rcc_root: Path, data: Mapping[str, Any], digest: str) -> list[Path]:
    history_dir = rcc_root / "history"
    decisions_dir = history_dir / "decisions"
    history_dir.mkdir(parents=True, exist_ok=True)
    decisions_dir.mkdir(parents=True, exist_ok=True)
    payloads = {
        history_dir / "PROJECT_TIMELINE.md": render_project_timeline(data, digest),
        history_dir / "PROFESSOR_FEEDBACK_LINEAGE.md": render_professor_feedback_lineage(data, digest),
        history_dir / "SUPERSEDED_DIRECTIONS.md": render_superseded_directions(data, digest),
        history_dir / "TERMINOLOGY_GUIDE.md": render_terminology_guide(data, digest),
        history_dir / "HISTORY_CONFIRMATION_NEEDED.md": render_history_confirmation(data, digest),
    }
    for row in data["decisions"]:
        name = f"{row['decision_id']}-{_slug(row['title'])}.md"
        payloads[decisions_dir / name] = render_decision_record(row, data["state"], digest)
    for path, payload in payloads.items():
        path.write_text(payload, encoding="utf-8", newline="\n")
    return list(payloads)


def build_dashboard(rcc_root: Path) -> Path:
    data = load_registry(rcc_root)
    digest = registry_digest(rcc_root)
    output = rcc_root / "dashboard" / "index.html"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_dashboard(data, digest, rcc_root), encoding="utf-8", newline="\n")
    return output


def generate_summaries(rcc_root: Path) -> list[Path]:
    data = load_registry(rcc_root)
    digest = registry_digest(rcc_root)
    generated = rcc_root / "generated"
    generated.mkdir(parents=True, exist_ok=True)
    outputs = {
        "GPT_BRIEF.md": render_gpt_brief(data, digest),
        "CURRENT_STATUS.md": render_current_status(data, digest),
        "CHANGE_SUMMARY.md": render_change_summary(data, digest),
        "RCC_002_USER_SUMMARY.md": render_user_summary(data, digest),
        "RCC_003_HISTORY_SUMMARY.md": render_rcc003_history_summary(data, digest),
        "ARCH_001_USER_SUMMARY.md": render_arch001_user_summary(data, digest),
        "ARCH_002_USER_SUMMARY.md": render_arch002_user_summary(data, digest),
        "ARCH_003_USER_SUMMARY.md": render_arch003_user_summary(data, digest),
        "ARCH_004_USER_SUMMARY.md": render_arch004_user_summary(data, digest),
        "ARCH_005_USER_SUMMARY.md": render_arch005_user_summary(data, digest),
        "ARCH_006_USER_SUMMARY.md": render_arch006_user_summary(data, digest),
        "ARCH_007_USER_SUMMARY.md": render_arch007_user_summary(data, digest),
        "ARCH_008_USER_SUMMARY.md": render_arch008_user_summary(data, digest),
        "ARCH_009_USER_SUMMARY.md": render_arch009_user_summary(data, digest),
        "ARCH_010_USER_SUMMARY.md": render_arch010_user_summary(data, digest),
        "GAP_000_USER_SUMMARY.md": render_gap000_user_summary(data, digest),
        "ARCH_011_USER_SUMMARY.md": render_arch011_user_summary(data, digest),
    }
    paths: list[Path] = []
    for name, payload in outputs.items():
        if name in {"ARCH_009_USER_SUMMARY.md", "ARCH_010_USER_SUMMARY.md", "ARCH_011_USER_SUMMARY.md"} and data['state'].get('exp03b_preparation'):
            payload += '\n## 현재 provider Gate\n\nEXP-03B PREPARED_DG03B_PENDING. DG-03B 별도 승인 전 provider 호출 0. EXP-03 V1은 constrained materialization 결과로 보존하며 DG-04는 EXP-03B 이후로 연기합니다. DG-05/06 미승인.\n'
        elif name in {"ARCH_009_USER_SUMMARY.md", "ARCH_010_USER_SUMMARY.md", "ARCH_011_USER_SUMMARY.md"} and data["state"].get("exp03_execution"):
            payload += "\n## 현재 provider Gate\n\nDG-03은 고정 snapshot으로 승인·실행되었으며 EXP-03 독립 QA가 완료되었습니다. 현재는 DG-04 제목·기여 결정 대기입니다. DG-05 공격 접근과 DG-06 제출은 승인되지 않았습니다.\n"
        path = generated / name
        path.write_text(payload, encoding="utf-8", newline="\n")
        paths.append(path)
    navigation_outputs = {
        "CURRENT_CONTEXT.md": render_current_context(data, digest),
        "MY_TODO.md": render_my_todo(data, digest),
        "DECISION_INBOX.md": render_decision_inbox(data, digest),
    }
    for name, payload in navigation_outputs.items():
        path = rcc_root / name
        path.write_text(payload, encoding="utf-8", newline="\n")
        paths.append(path)
    paths.extend(generate_history_documents(rcc_root, data, digest))
    return paths


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rcc-root", type=Path, default=default_rcc_root())
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dashboard-only", action="store_true")
    mode.add_argument("--summaries-only", action="store_true")
    args = parser.parse_args(argv)
    root = args.rcc_root.resolve()

    written: list[Path] = []
    if not args.summaries_only:
        written.append(build_dashboard(root))
    if not args.dashboard_only:
        written.extend(generate_summaries(root))
    for path in written:
        print(path.relative_to(root).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
