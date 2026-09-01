# V2-SCI-001 과학 실행 전 중단 보고서

상태: `BLOCKED_UNDEFINED_EXP02_SCIENTIFIC_BINDINGS_AND_COHORT_AUTHORITY`

## 결론

정상 데이터 custody는 준비됐지만, EXP-02를 시작하기 전에 동결되어야 하는
과학적 생산 규칙 세 개와 별도 V2 확인 관계 cohort가 아직 없습니다. 따라서
이번 실행은 HAI payload를 열기 전에 fail-closed로 중단했습니다.

이 중단은 데이터 부재나 일반 구현 오류가 아닙니다. 기존 구현을 임의로 선택해
quantile, relation-local summary, opportunity census 의미를 채우면 결과를 보기 전
동결되지 않았던 새로운 과학적 선택이 됩니다. 이는 V2-SCI-001의 stop condition E와
동결된 run matrix를 위반합니다.

## 통과한 게이트

- branch / origin: `validation-v2 @ 946badfa3d73a5ae32229ea74c6d41f28e33b679`, parity PASS
- PILOT V1: 3,021 / 3,021 blobs 보존 PASS
- Formal V4: `DEC-020 APPROVED_FORMAL_V4`
- normal-only custody: `NORMAL_ONLY_CUSTODY_READY`
- dataset/splits: HAI 23.05 P1, train1~train4만 결속
- protocol hash: `2c3000a912caf2167bfe49929c55229e5159d52cc9ad09b7e48d79d9aecc562f`
- metric contract hash: `aec2dd11b8178071eb91160f1dff45f9cd0cc1be6c314aa3641ed0698df3dde4`
- V2 tests: 328 PASS, 7 expected skips
- RCC tests: 171 PASS
- Registry: PASS, private exposures 0

## 실행을 막는 사전 권위

1. `SEPARATE_SELF_HASHED_V2_CONFIRMED_COHORT`
   - META+STAT candidate policy는 동결됐지만 pair identity materialization은 pending입니다.
2. `EXP02-BIND-QUANTILE`
   - Q50/Q75/Q90의 정확한 계산·보간 규칙이 고유하게 결속되지 않았습니다.
3. `EXP02-BIND-RELATION-SUMMARY`
   - relation-local noise/quantile/target-noise의 생산 규칙이 고유하게 결속되지 않았습니다.
4. `EXP02-BIND-OPPORTUNITY-CENSUS`
   - relation-specific threshold로 opportunity와 cross-source isolation census를 만드는
     규칙이 고유하게 결속되지 않았습니다.

`scripts/run_validation_v2_exp02_v1.py`는 위 세 binding의 재생 검증만 수행하는
preflight CLI입니다. 실제 train1/train2/train4 과학 실행 entrypoint가 아닙니다.

## 후속 영향

EXP-02 numeric policy가 동결되지 않았으므로 다음 단계도 시작할 수 없습니다.

- Formal V4 V2 portfolio materialization
- Rule-only V2 runtime authorization
- EXP-04 label-blind prediction 생성 및 durable freeze
- test1 label authorization
- EXP-04 development metrics
- actual runtime trace 기반 EXP-05

EXP-04 하위 계층에도 native Rule-only prediction과 공통 dense evaluation artifact 사이의
명시적 변환·custody binding, 재시작 가능한 label authorization, scientific result
integrity runner가 추가로 필요합니다. 그러나 이 구현 작업은 EXP-02 사전 권위가
해결된 뒤에만 과학 실행 경로에서 의미가 있습니다.

## 안전 카운터

- scientific payload opens: 0
- scientific executions: 0
- test1 feature accesses: 0
- test1 label accesses: 0
- test2 / held-out accesses: 0
- provider calls: 0
- PILOT V1 changes: 0
- result-driven redesigns: 0

## 정확한 다음 결정

데이터를 열기 전에 별도 authority-freeze 작업으로 다음을 승인·동결해야 합니다.

1. V2 META+STAT pair를 어떤 기존 arm-blind train3 confirmation authority에 엄격히
   rebind할지, 아니면 별도 V2 cohort를 새로 materialize할지 결정
2. quantile 계산 규칙
3. relation summary 생산 규칙
4. opportunity/cross-source isolation census 규칙

이 네 항목이 versioned specification, implementation, config, source commit, self-hash로
동결된 뒤 동일한 `V2-SCI-001` 실행 순서를 재개할 수 있습니다.
