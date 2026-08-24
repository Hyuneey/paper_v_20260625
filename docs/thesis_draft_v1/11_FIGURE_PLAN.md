# 논문 그림 계획

모든 그림은 aggregate public evidence만 사용한다. raw row, private numeric
parameter, attack coordinate는 시각화하지 않는다.

## Figure 1. 전체 제안 방법

- 목적: data contract에서 rule construction, verifier, D0/D1/D2와 metric까지
  한 장에 보여준다.
- 입력: architecture audit, v6 canonical architecture, method configs.
- encoding: 단계별 box; normal-only, INNER-label, held-out 경계를 색으로 구분;
  LLM 단계에는 점선, deterministic 단계에는 실선.
- caption 초안: “그래프 유도 후보와 정상 시간 증거를 제한된 규칙 구성,
  결정론적 검증, LLM-free runtime에 연결한 전체 아키텍처.”
- source: `docs/post_push_checkpoint_v1/02_END_TO_END_ARCHITECTURE_AUDIT.md`,
  `docs/professor_first_results_v1/04_METHOD_AND_CODE_ARCHITECTURE.md`.

## Figure 2. 후보 144 → 47 → 관계 42

- 목적: discovery와 confirmation이 서로 다른 selection 단계임을 설명한다.
- 입력: C0 universe, META/STAT/GDN top-20 membership, 47-pair cohort,
  confirmed 23 pairs/42 directions.
- encoding: three-arm set union → 47 pair funnel → direction split/confirmation
  → 42 relation nodes. score 크기를 공통척도처럼 그리지 않는다.
- caption 초안: “서로 다른 후보 근거의 unscored union과 정상 데이터
  confirmation을 통한 COMMON-42 형성.”
- source: `TASK-039C_*`, `TASK-039D*`,
  `TASK-039E0_CONFIRMED_RELATION_COHORT.json`.

## Figure 3. LLM proposal과 deterministic authority 분리

- 목적: 본 연구의 핵심 contribution boundary를 시각화한다.
- 입력: T0/T1/T1-B/T2 contract, numeric authority, verifier/runtime policy.
- encoding: LLM이 접근 가능한 structured fields와 접근 불가능한 numeric,
  approval, runtime 영역을 두 열로 분리; verifier rejection/no_rule 경로 표시.
- caption 초안: “LLM은 bounded structure를 제안하지만 수치, 유효성,
  실행 판단은 결정론적 authority가 소유한다.”
- source: rule-construction protocol, normal-only authority reports,
  `src/paperworks/contracts/verifier_v1.py`.

## Figure 4. 시간 규칙과 satisfaction trace

- 목적: time-variable-relation localization의 실제 정보 단위를 설명한다.
- 입력: sanitized representative descriptor A–C, runtime trace schema.
- encoding: source step, expected horizon band, target response arrow, operator
  trace timeline. threshold와 attack coordinate는 생략.
- caption 초안: “source transition 이후 frozen horizon에서 expected target
  response를 검사하고 결과를 trace로 남기는 실행 규칙.”
- source: public COMMON-42 descriptor,
  `src/paperworks/contracts/runtime_v1.py`, professor first-results report.

## Figure 5. D0/D1 attack-event overlap

- 목적: complementarity를 가장 단순하게 보여준다.
- 입력: BOTH 10, D0_ONLY 1, D1_ONLY 3, NEITHER 0.
- encoding: 면적 과장을 피한 2×2 count matrix 또는 정확한 count bar;
  Venn area는 count 비례가 보장될 때만 사용.
- caption 초안: “INNER 14개 attack event에서 D1은 D0 miss 3개를 모두
  포함했지만 rule-only FAR는 높았다.”
- source: D0/D1/D2 comparison arm metrics and complementarity artifacts.

## Figure 6. D0/D1/D2 Recall–FAR 비교

- 목적: recall과 false-alarm trade-off를 동시에 제시한다.
- 입력: 네 arm의 exact Recall/FAR.
- encoding: x=Normal FAR/hour(log scale 권장), y=Attack-event Recall; 점마다
  exact value label과 INNER-only 표기. 14 event uncertainty를 caption에 명시.
- caption 초안: “D1은 높은 event recall과 매우 높은 FAR를 보였고 D2
  V1/V2는 D0 recall을 넘지 못했다.”
- source: frozen metric artifacts and result-integrity completion.

## Figure 7. V1/V2 fusion과 실패 구조

- 목적: point-level gate가 event complementarity를 놓친 이유를 설명한다.
- 입력: one single-source event, two asynchronous multi-source events;
  V1 exact same-second; V2 native-horizon token policy; recovery 0/3.
- encoding: 실제 attack 좌표가 아닌 schematic timelines. V1은 non-overlap,
  V2는 widened tokens와 normal false-alarm expansion을 표시.
- caption 초안: “V1은 비동기 evidence를 잃었고 V2는 evidence persistence를
  늘렸지만 useful recovery 없이 정상 경보를 확대했다.”
- source: D2 recovery diagnostic, V2 design and disposition artifacts.
