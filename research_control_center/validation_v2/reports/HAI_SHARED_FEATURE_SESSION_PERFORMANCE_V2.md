# HAI shared feature session 성능 개선

상태: `IMPLEMENTED_SYNTHETIC_CONFORMANCE_PASS_NOT_YET_SCIENTIFICALLY_EXECUTED`

## 문제

VALIDATION V2의 기존 `hai_feature_adapter_v1`은 한 호출 안에서는 HAI split을
정확히 한 번 열고 검증하지만, D0 PCA-SPE, Isolation Forest, D1 Formal V4 같은
서로 다른 소비자가 각자 adapter를 만들면 동일 CSV를 다시 parse할 가능성이 있다.
HAI CSV parse는 byte hash, timestamp 연속성 확인, 37개 P1 feature의 float 변환을
모두 수행하므로 동일 process 안에서 반복할 이유가 없다.

## 구현

새 `HAISharedFeatureSessionV1`은 다음 경계를 고정한다.

1. split을 사용할 모든 consumer ID와 `ProtocolOperationV1`을 먼저 등록한다.
2. operation 전체가 frozen protocol에서 허용되는지 payload open 전에 검증한다.
3. 중복 operation은 하나로 모으되 소비자 identity는 각각 보존한다.
4. `HAIFeatureAccessLedgerV1`을 통해 split을 정확히 한 번만 연다.
5. source file hash, size, header, P1 feature order, 1초 timestamp 연속성 검증은
   기존 adapter를 그대로 사용한다.
6. 동일 feature projection은 session 안에서 한 번만 materialize한다.
7. 각 소비자에는 같은 buffer를 참조하는 별도 read-only NumPy view를 반환한다.
8. session close 시 frame/projection 참조를 해제하고 디스크 cache는 만들지 않는다.

기존 단일-operation API는 새 multi-operation one-open entrypoint의 singleton
호출로 유지되므로 기존 호출자 의미는 바뀌지 않는다.

## 합성 검증

실제 HAI data를 열지 않은 5-row, 37-feature 합성 fixture에서 확인했다.

- D0 PCA + Isolation Forest + D1 relation fit: source parse 1회
- 세 consumer의 full projection: unique projection materialization 1회
- D0 PCA + Isolation Forest + D1 Formal V4 test1 development path:
  `DEVELOPMENT_PREDICTION` authorization 1회, source parse 1회
- 각 consumer view: 서로 다른 객체, 동일 buffer 공유, direct write 불가
- subset projection: materialization 1회, consumer view 공유
- 잘못된 train3 detector operation: payload open 전 거부
- test2/held-out alias: payload open 전 거부
- duplicate split/consumer: 거부
- 미등록 consumer: 거부
- session 직렬화와 close 후 사용: 거부
- public receipt의 private path/numeric payload: 0

이는 실행 경로의 synthetic conformance evidence이며 scientific data 처리 시간이나
검출 성능 결과가 아니다.

## 과학적 경계

- architecture/model/hyperparameter/seed/dtype: 변경 0
- data/split/protocol/preregistration: 변경 0
- threshold/comparator/metric: 변경 0
- source file identity 검증: 기존 contract 재사용
- persistent scientific cache: 생성 0
- scientific execution: 0
- test1/test2/held-out/label access: 0
- PILOT V1 변경: 0
- scientific result 변경: 0

## 검증

- focused shared-session/adapter tests: 11 PASS
- VALIDATION V2 suite: 310 tests OK, 6 expected skips 포함
- RCC suite: 165 tests PASS
- RCC registry/privacy: PASS, `private_exposures=0`
- changed-file privacy scan: findings 0
- PILOT V1 preservation: 3,021/3,021 blobs PASS

## 적용 시점

현재 EXP-04 scientific runner는 아직 존재하지 않으므로 실제 HAI 실행에는 연결하지
않았다. 향후 runner와 method/config authority가 동결된 뒤, 한 session이 D0,
Isolation Forest, D1의 공통 split open을 소유하도록 연결한다. 각 detector/rule
계산과 결과 custody는 그대로 분리한다.

## 남은 병목

다음 안전한 독립 후보는 EXP-04에서 D1 rule outcome의 중복 순회와 D2 fusion의
coordinate별 반복 정렬을 한 번의 grouped pass로 합치는 것이다. 과학적 fusion
policy나 test1 결과를 변경하지 않는 합성 contract로만 먼저 검증해야 한다.
