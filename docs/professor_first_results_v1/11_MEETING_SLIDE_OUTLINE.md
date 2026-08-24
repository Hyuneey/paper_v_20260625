# 10–15분 미팅 슬라이드 구성

## 1. 문제와 교수님 피드백 (1분)

- LLM 통제, detector+rule 이유, 설명 범위, TSFM/ARTIST 질문
- 자유 생성보다 검증 가능한 구성으로 전환

## 2. 현재 연구 질문과 기여 (1분)

- graph-guided candidate curation
- normal-only numeric authority
- deterministic verifier + LLM-free runtime

## 3. 전체 아키텍처 (2분)

- 144 pairs → META/STAT/GDN → profiling → COMMON-42
- T0/T1/T1-B/T2 → verifier → D1, D0, D2

## 4. 구성 결과 (1분)

- 23 pairs / 42 directional relations
- T0/T1/T1-B 42/42, T2 39/42 + 3 no_rule

## 5. INNER 주 결과 (2분)

- D0 11/14, D1 13/14
- overlap: both 10, D0 only 1, D1 only 3, neither 0
- D1 FAR 40.50/hour

## 6. D2 negative result (2분)

- V1 0/3 recovery, FAR 0.706
- V2 0/3 recovery, FAR 6.915
- `RULE_SIGNAL_PRESENT_BUT_CURRENT_FUSION_UTILITY_UNSUPPORTED`

## 7. 설명 사례 (1분)

- source transition → frozen lag → expected target response → trace
- 관계 국소화이지 causal root cause/human usefulness 증명 아님

## 8. 구현·미구현 경계 (1분)

- complete: contracts/rules/verifier/runtime/INNER audit
- missing: TSFM, ARTIST, strong baseline, OUTER result, human study

## 9. OUTER 상태 (1분)

- custody reject before byte read
- prediction/metric 없음, generalization unconfirmed

## 10. 네 결정 (2분)

- contribution / explanation / OUTER / detector baseline
- 권고: `THESIS_FIRST_PENDING_PROFESSOR_FEEDBACK`

