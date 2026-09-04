# DEC-025 — 최종 방법과 한정된 Agentic 기여 고정

사용자 결정: `APPROVED_WITH_SCOPED_AGENTIC_CLAIM`. 이는 새 과학 결과가 아니라 동결된 EXP-03B 결과에 대한 기여 표현 결정입니다. 역사적 DG-04 brief와 EXP-03B 결과는 변경하지 않습니다.

## 고정 제목

Verifier-Guided Agentic Relational Rule Induction with GDN-Based Learned-Graph Evidence for Explainable Multivariate Time-Series Anomaly Detection

## 주장과 필수 한계

동결된 정상-only EXP-03B에서 verifier feedback은 동일 **최대** 호출 예산의 독립 생성 T1-B보다 의미적 관계 Rule 유도를 개선했습니다. 실제 호출 수는 early-stop 때문에 다릅니다. T2는 주요 의미적 유도 지표에서 결정론적 T0보다 우수하지 않았습니다. LLM 필수성, 공격 탐지 개선, held-out 일반화, 인과 복원, production 우월성을 주장하지 않습니다. 추가 Agentic rescue는 없습니다.

META(HYBRID_REVIEWED_METADATA)+STAT는 후보 pair 권한입니다. GDN은 핵심 아키텍처 근거 모듈이지만 그 과학적 이력은 LEARNED_GRAPH_SUPPORTING이며 후보 admission·탐지기·인과 그래프·수치 권한이 아닙니다. T0는 동일 정보의 강한 결정론적 baseline, T2는 bounded verifier-guided 의미 유도입니다. SCI-02B는 사후 결정론적 수치 결속, Formal V4는 실행 Rule 권한, train4는 one-way 정상 guard입니다. Fusion은 재설계 없는 사전등록 비교이지 기여가 아닙니다. 설명의 구조 fidelity와 사람에게 유용함은 별개이며 후자는 미검증입니다.

## C1–C4

1. 도메인·통계 후보 근거와 GDN learned-graph evidence를 결합한 다중 출처 관계 근거.
2. 제한된 feedback와 숨겨진 정상 검증에 의한 Agentic 의미 Rule 유도.
3. 결정론적 수치 결속, Formal V4 변환, 정상 운영 guard.
4. 실행 가능한 관계 이상 분석과 runtime trace 기반 구조 설명.

## RQ1–RQ4

1. 도메인·통계·GDN 근거를 경험적으로 확인된 관계 Rule 후보로 전환할 수 있는가?
2. Bounded verifier feedback이 one-shot 및 matched-budget 독립 생성보다 LLM 의미 유도를 개선하는가? T0 우월성 질문이 아닙니다.
3. 결정론적 Rule-only, Agentic Rule-only, Detector-only, Detector+Rule의 공격 반응과 false burden은 어떻게 다른가?
4. 설명은 실제 Formal V4 runtime trace에 구조적으로 충실한가?

## 다음 단계와 접근 경계

T0 단일 출력과 T2 Repeat 1의 이미 동결된 admission→train3→SCI02B→Formal V4→train4 retained 경로만 held-out **후보**로 물질화합니다. V2A는 별도 evidence-rich reference입니다. 후보 고정은 공격 실행·production 승인이 아닙니다.

외부 HAI22/21은 정상-only 준비이며 기존 수치 정책 n7-q0.90-s2-f0.05를 재선택하지 않습니다. Provider는 DG-03C, 공격은 DG-05, 제출은 DG-06에서 별도 승인합니다. Test1 재개봉 금지. 이 task의 모든 수정은 task branch에만 두며 전체 PASS 전 integration에 병합하지 않습니다.
