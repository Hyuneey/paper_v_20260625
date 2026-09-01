# V2-SCI-001 multi-agent review

## 구성

- Agent A — EXP-02 frozen protocol read-only audit
- Agent B — normal custody / Formal V4 / split authority read-only audit
- Agent C — EXP-04 prediction freeze / metric / EXP-05 read-only audit
- Coordinator — 유일한 공용 파일 writer 및 과학 실행 소유자
- Independent QA — 실행 전 중단 판단과 변경분 재검토

세 read-only agent 모두 scientific payload, test1, test2, label, held-out을
열지 않았고 파일을 수정하지 않았습니다.

## 합의된 사실

1. `validation-v2`와 `origin/validation-v2`는 preflight 시점에
   `946badfa3d73a5ae32229ea74c6d41f28e33b679`로 일치했습니다.
2. PILOT V1 3,021 blobs 보존, Formal V4, normal-only train1~train4 custody,
   protocol/metric hashes는 모두 유효합니다.
3. EXP-02 선택 규칙과 deterministic tie-break는 동결되어 있습니다.
4. EXP-02의 실제 scientific summary/census producer와 별도 V2 confirmed
   cohort authority는 동결되지 않았습니다.
5. 따라서 기존 NumPy 또는 legacy relation 구현을 임의로 선택하는 것은
   일반 wiring이 아니라 새로운 과학적 의미 선택입니다.
6. EXP-04 component 수준의 D0, Isolation Forest, Formal V4, fusion, custody,
   metric, EXP-05 구현은 존재하지만 이를 한 번에 실행하는 authoritative
   scientific orchestration과 result-integrity 경로는 아직 없습니다.

## Agent A — EXP-02

- `scripts/run_validation_v2_exp02_v1.py`는 세 binding의 replay-only preflight입니다.
- 미결속: `EXP02-BIND-QUANTILE`, `EXP02-BIND-RELATION-SUMMARY`,
  `EXP02-BIND-OPPORTUNITY-CENSUS`.
- `SEPARATE_SELF_HASHED_V2_CONFIRMED_COHORT`가 없습니다.
- 사전등록 hash `62b5de353a55560855e55cdeac3233505975377f354cbec3b66f1ba193570721`
  재생은 일치했습니다.

## Agent B — custody / authority

- active normal binding self-hash:
  `05a95d576fefaae8894b6ec9ed9796a9ba0cf5eea02e9dc4781985e462b4f58d`
- historical `BLOCKED_NORMAL_DATA_NOT_FOUND` receipt는 현재 binding으로
  사용하면 안 됩니다.
- private locator는 ignored 상태이며 auditor가 열지 않았습니다.
- safe normal opener는 label/test interface가 없는 guarded feature adapter입니다.

## Agent C — EXP-04 / EXP-05

EXP-02와 portfolio를 해결한 뒤에도 다음 구현 gate가 남습니다.

- authoritative EXP-04 scientific orchestration runner
- D0/Isolation Forest array를 file-local dense artifact로 binding하는 경로
- native D1 artifact와 common dense evaluation artifact의 exact equivalence
- PCA+Rule / IF+Rule fusion decision의 durable artifact materialization
- process restart 후에도 재생 가능한 five-method bundle custody
- native D1 label capability와 common evaluation label capability의 결합
- protocol freeze commit과 truthful execution-code commit의 분리
- V2-specific one-shot test1 label adapter
- scientific metric/result artifact와 independent integrity runner
- actual Formal V4 trace와 EXP-05 Commit B semantic receipt replay

이 항목들은 이번 중단의 최초 원인은 아니지만 test1 label access 전에 모두
해결되어야 합니다.

## Coordinator verdict

`BLOCKED_UNDEFINED_EXP02_SCIENTIFIC_BINDINGS_AND_COHORT_AUTHORITY`

V2-SCI-001 stop condition E가 충족됐습니다. 과학 payload를 열거나 기존
preregistration을 해석으로 보충하지 않고 중단하는 것이 유일하게 허용된 처리입니다.
