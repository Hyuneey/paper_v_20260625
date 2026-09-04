# EXP-03B 사전 감사 — 미정 과학적 binding에서 정지

Task: `EXP03B-PREP-001`. Base: `4cbd13cec2e439f352adaf5b4e37163c6f18a485`.
상태: `BLOCKED_UNDEFINED_SCIENTIFIC_BINDINGS`; PREPARED/READY_TO_RUN/PASS가 아니다.
user가 승인한 보정 방향은 유지하지만, 아래 세부 과학 기준을 임의로 정하지 않는다.
실제 train1~4 값, credential, provider API, test/attack data는 읽지 않았다.

## 확인 완료

- local/origin 시작 SHA 일치와 clean worktree 확인.
- EXP-03 V1의585 request/response와390 terminal replay PASS, provider 재호출0.
- PILOT V1 3,021/3,021 blob 보존 PASS.
- 지정한 현재 공개 authority149개 blob의 Git byte identity PASS.
- candidate union29 pair, confirmed21 pair /39 directional relations를 재생으로 산출.
- 최대 호출은 `29 × 3 × (1+3+3) = 609`; 값은 cohort로부터 산출했다.

## 정보 분리상 기존 근거를 그대로 쓸 수 없는 이유

1. `exp01_relation_confirmation_v2.py:153–172`는 train1+train2로 source threshold와
   target scale을 만든다. `train1` 항목만 직렬화해도 이미 train2가 영향을 준 통계다.
   새 provider evidence는 train1-only derivation으로 만들어야 한다.
2. `run_exp01c_gdn_hai.py:635–636`, `exp01c_backend_v1.py:469–503`의 기능 평가는
   train4를 사용한다. TRAIN1_ONLY는 학습 view이지 기능 평가 split이 아니다.
   현 attention/EdgeMask 결과를 train1 근거로 보내면 안 된다. 새 train1-only 근거가
   없으면 해당 optional 항목은 unavailable로 표시해야 한다.
3. `exp02_bindings_v2a.py:99–148`의 summary는 final confirmed relation direction에
   결속되어 있다. provider builder는 이 객체를 import/read한 뒤 필드를 지우는 방식으로
   재사용하지 않는다. 모든 허용 방향·horizon의 pair-wide option에 별도 identity가 필요하다.
4. profiling normal scale과 EXP02 numeric noise는 서로 다르다.
   `relation_profiling_protocol_v1.py:467–509`의 MAD-based dx scale과
   `exp02_bindings_v2a.py:123–148`의 median absolute dx를 혼동하지 않는다.

## 사용자 결정 또는 명시적인 과학 명세가 필요한 항목

| ID | 미정 binding | 기존 계약으로 자동 결정할 수 없는 이유 |
|---|---|---|
| SCI-01 | train1 T0 / train2 verifier의 support, consistency, effect, opposite-margin, horizon-stability 판정식·임계값 | 기존 pooled fit는 usable20/per-file5/consistency.70와.60/effect2.0, train3 confirmation은5/.60/1.0이다. 서로 다른 역할의 규칙이며 단일 split에 그대로 대응하지 않는다. |
| SCI-02 | train1 numeric-option 선택 규칙, train2 option admissibility 및 firing/coverage guard | 37-grid와 per-split role derivation은 있지만 기존 선택은 train4에서 수행한다. 이를 train1 선택 또는 train2 admission으로 재명명할 수 없다. |
| SCI-03 | train4 Rule retention 기준과 arm 간 false-firing burden 집계 | report-only인지 제외 gate인지, pair별 합산인지 portfolio union인지, repeat별 비교인지가 결과와 disposition을 바꾼다. |
| SCI-04 | 3-repeat majority set 및 빈 denominator/failure 처리의 정확한 scoring 명세 | tuple별 투표는 실제 어떤 repeat에도 없던 Rule set을 만들 수 있다. exact-set majority와 NO_RULE/failure 구분을 명시해야 한다. |

SCI-01 근거: `src/paperworks/v6/relation_profiling_protocol_v1.py:577–609,695–707`.
SCI-02/03 근거: `src/paperworks/validation_v2/numeric_policy_v1.py:514–548,581,756–780,935–1003`.
새 threshold를 실제 데이터에 맞추어 선택하지 않는다. 이 선택들은 값/결과를 보기 전에 결정해야 한다.

권고하는 구현 방향(아직 동결된 과학 계약 아님): split-local adapter, 완전한 Rule-set majority,
parse/provider failure의 별도 상태, 양 arm의 같은 exposure 및 preassigned repeat 비교,
GDN train4 sidecar 제외. 숫자·admission 임계값은 이 문서에서 새로 발명하지 않는다.

## 이미 확정된 사용자 지시 — 변경 불가

train1 initial evidence; train2 hidden verifier와 제한된 T2 retrieval;
train3 frozen normal-confirmed development reference; train4 normal guard.
T2 feedback/retrieval은 initial train1-only 원칙의 명시적인 제한 예외이며 hidden answer는 아니다.
output RULE_SET/NO_RULE, source당 방향별 최대1개 총2개 Rule, horizon1/5/10/30/60.
Formal V4 direction token은 source `step_up/step_down`, target `increase/decrease`.
T1 one call; T1-B three stateless calls; T2 maximum3 with ACCEPTED early stop; repetitions3.
REPEAT_1만 prospective portfolio source. T0는 hidden authority를 보지 않는다.
사용자의 세 가지 Agentic disposition criteria는 변경하지 않는다.
train3 reference의 absence는 모든 alternative tuple의 과학적 오류를 증명하지 않는다.
단 하나의 bounded EXP03B 이후 추가 Agentic rescue는 새 사용자 결정 없이 하지 않는다.

## 아직 하지 않은 것

실제 evidence pack 생성/크기 측정, verifier/scientific runner 구현·동결, full synthetic suite,
train4 실행, provider budget 승인 요청, private vault 생성, Registry/Dashboard의 PREPARED 게시,
professor package 완성, task integration/push를 완료한 것으로 표시하지 않는다.
기존 frozen artifact와 DG-04 원문을 수정하지 않는다. 본 task branch의 감사 기록이 이후 재개 근거다.

정확한 다음 단계: SCI-01~04를 명시적으로 결속 → 나머지 EXP03B-PREP-001 완료 → DG-03B.
