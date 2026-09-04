# DG-04 — EXP-03B 이후 제목·Agentic 기여 결정

상태: **USER_DECISION_REQUIRED**. 아래는 결과에 근거한 결정안이며 최종 제목·기여를 자동 확정하지 않습니다. 추가 Agentic rescue 실험은 진행하지 않습니다.

## 동결 결과의 의미

EXP-03B의 preregistered 판정은 `AGENTIC_ADVANTAGE_SUPPORTED`입니다. 이는 29개 고정 후보 pair의 정상 evidence-to-rule semantic induction에서 **T2 대 T1-B** 기준을 만족했다는 뜻입니다. Attack detection, causal truth, held-out 일반화의 입증이 아닙니다.

- Feedback: 83회, 22개 distinct pair.
- Verifier repair: 26 observations / 13 distinct pairs.
- 독립 재계산한 train3-confirmed exact semantic repair: 20 observations / 10 distinct pairs.
- T2 대 T1-B: strict pair F1 0.7222 대 0.5714; directional F1 0.7385 대 0.5424; exact semantic set 17/29 대 10/29.
- Paired exact set: T2만 정답 8, T1-B만 정답 1, 둘 다 9, 둘 다 아님 11.
- Repeat 1 Formal V4 conversion: T2 27/30 대 T1-B 18/24; train4 retained Rules 21 대 17.
- Train4 false seconds/hour: 9.5818 대 10.9273. False episodes/hour: 9.5636 대 10.9273.

## 반드시 함께 보고할 한계

1. **T0가 T2보다 높습니다.** T0 strict pair F1 0.7692, directional F1 0.8116, exact set 18/29입니다. 이 결과는 Agentic 방법이 결정론적 heuristic보다 우월하다는 주장을 지지하지 않습니다.
2. T2의 train4 abstain rate는 0.1834로 T1-B의 0.0655보다 높습니다. 동결 판정은 false seconds/hour → episodes/hour → abstain의 lexicographic 비교였으므로 통과했지만, 모든 운영 지표가 개선된 것은 아닙니다.
3. Train3는 같은 정상 relation protocol의 frozen confirmation reference입니다. 독립적인 물리적/인과적 ground truth가 아닙니다.
4. 각 arm의 세 번 반복은 안정성 관찰이며 독립 과학 표본이 아닙니다. 사후 유의성 검정을 추가하지 않았습니다.
5. Numeric policy는 LLM 선택이 아닙니다. 모든 semantic output/admission/train3 freeze 뒤 deterministic SCI-02B가 수치를 결속했습니다.
6. Production/held-out Agentic portfolio는 생성·승인하지 않았습니다. V2A 39-rule portfolio와 EXP-04/05는 그대로 유지됩니다.

## 사용자 결정안

- Agentic contribution: **bounded verifier-feedback semantic rule induction**으로 제한해 유지할지 결정합니다. 권고는 “matched-budget independent generations 대비 구조 복구 이점; deterministic heuristic 대비 우월성은 미확인”이라는 명시적 경계입니다.
- GDN-Assisted 제목: GDN은 기존 learned-graph supporting evidence 역할을 유지합니다. 이번 EXP-03B만으로 GDN의 독립 효과나 primary discovery 권한을 새로 부여하지 않습니다.
- Final method set: frozen V2A·detector·fusion 세트를 유지합니다. Agentic V3를 향후 panel에 포함할지는 별도 명시적 결정이 필요하며 자동 교체하지 않습니다.
- Fusion: 기존 DEVELOPMENT_NOT_SUPPORTED 결과를 negative-result 비교로 보존합니다. 새 fusion을 만들지 않습니다.

Methods 권고 문장: “고정 후보 pair의 정상 evidence에서 의미적 관계 Rule Set을 유도하고, bounded hidden-verifier feedback으로 수정하며, 독립된 deterministic post-induction numeric binding과 Formal V4 admission을 적용했다. T2는 사전등록된 T1-B 비교 기준을 충족했지만 T0 대비 우월성은 관찰되지 않았다.”

DG-05의 test2/외부공격 접근과 DG-06의 실제 교수님 제출은 여전히 별도 승인입니다. Test1은 재개봉하지 않습니다. 교수님에게 제출하지 않았습니다.

근거: [동결 결과](EXP03B_RESULTS_REPORT_V1.md), [public result authority](EXP03B_REVISED_RESULTS_V1.json), [독립 QA](EXP03B_EXECUTION_INDEPENDENT_QA_V1.json).
