# Detector와 Rule을 합치면 실제로 좋아졌는가

## 1. D2의 목적

D2는 D0 detector alarm을 그대로 보존하면서, D1 관계 규칙의 alarm evidence가
충분히 corroborate될 때만 alarm을 추가하는 deterministic policy pilot이다. 학습형
fusion model이나 production-ready architecture가 아니다.

## 2. D0와 D1에서 무엇을 입력받는가

두 버전 모두 frozen D0 Boolean prediction과 frozen D1 alarm record만 읽는다. D1에서
사용하는 필드는 decision row, alarm Boolean, relation binding이며, 별도의 frozen map으로
relation을 source identity에 연결한다. Raw HAI feature, D0 score, label, D1 metric은 fusion에
들어가지 않고 D0/D1도 다시 실행하지 않는다.

## 3. D2 V1은 무엇을 하는가

V1은 동일한 `decision_physical_row_index`에서 alarm을 낸 D1 record를 모은다. 같은 source의
여러 rule은 한 번만 세며, 서로 다른 source가 2개 이상이면 D1 addition을 허용한다.

```text
D2_V1(t) = D0(t) OR (distinct D1 alarming sources at t >= 2)
```

여기서 “same-second”는 1초 grid의 동일 decision row이다. Source trigger time이나 event
episode 전체를 뜻하지 않는다.

## 4. D2 V2는 무엇을 하는가

V2는 D1 alarm record를 해당 relation의 frozen native horizon 동안 active token으로 유지한다.
Token은 `decision_index <= t <= decision_index + horizon`에서 활성이고, 각 row에서 활성 source
identity를 deduplicate한 뒤 2개 이상이면 추가 alarm을 허용한다. 별도 consecutive persistence
threshold나 학습된 temporal model은 없다.

## 5. D0 Alarm은 그대로 보존되는가

그렇다. 두 버전 모두 pointwise OR이므로 D0가 true인 row를 제거하거나 이동할 수 없다. Code는
D0 alarm이 D2에서 사라지는 경우 fail closed한다. Episode grouping은 label access 이후 metric
단계이므로 preservation 단위가 아니다.

## 6. D1 Alarm은 언제 D2에 추가되는가

V1은 같은 row의 서로 다른 source 2개, V2는 각 native-horizon active interval 안에서 동시에
활성인 서로 다른 source 2개를 요구한다. D1이 event에 한 번 반응했다는 사실만으로는 충분하지
않다.

## 7. D0가 놓친 3개 사건은 왜 회복되지 않았는가

D1은 세 unit 모두에 반응했지만 V1 gate는 어느 unit에서도 통과하지 않았다. Frozen diagnostic은
두 unit에서 event-wide source가 여러 개였으나 같은 row에 정렬되지 않았고, 한 unit은 source가
하나뿐이었다고 기록한다. 같은 source에서 여러 relation이 울려도 source count는 하나다.

V2도 recovery 0/3이었다. Single-source unit은 정책상 제외되지만, 두 asynchronous unit이 V2에서도
왜 최종 admission되지 않았는지에 대한 per-unit public trace는 없다. 따라서 “native horizon으로도
현재 gate가 세 response를 admit하지 못했다”까지만 말할 수 있다.

## 8. V1 결과

14개 contiguous attack-event unit 중 11개에 반응했고 Recall은 0.7857142857142857이다. Normal
false episode는 10개, FAR은 0.7056194750975128 episodes/hour이다. D0-miss recovery는 0/3이었다.
V1은 D0 대비 Recall이 같고 normal FAR이 더 높다. 추가된 3개 recovery episode는 모두 이 pilot의
normal false episode였다.

## 9. V2 결과

V2도 11/14, recovery 0/3이었다. Point alarm 2,148개, total alarm episode 143개, normal false
episode 98개이며 Normal FAR은 6.915070855955625 episodes/hour이다. Native-horizon activity는
늘었지만 incremental attack-event Recall은 0이었다.

## 10. V2가 독립 검증이 아닌 이유

V2 provenance는 V1 negative result와 test1-label diagnostic이 problem formulation을 informed했다고
명시한다. V2 자체 결과는 design freeze 전에 보지 않았지만, 동일 test1에서 다시 평가했으므로
`TEST1_INFORMED_DEVELOPMENT`이다. 독립 confirmation에는 validation에서 policy를 선택·freeze한 뒤
별도의 final test가 필요하다.

## 11. 왜 Recall은 같고 FAR은 증가했는가

관찰된 mechanics만 말하면, D0는 보존됐고 V1/V2가 D1 evidence로 normal 구간 alarm을 추가했지만
D0가 놓친 세 event unit에는 추가 alarm을 admit하지 못했다. 이것이 현재 Recall 유지와 FAR 증가를
설명한다. 왜 특정 normal point에서 relation evidence가 많이 생겼는지는 이 감사에서 새로 분석하지
않았다.

## 12. 이것이 Detector+Rule 전체의 실패를 뜻하는가

아니다. 현재 결과는 두 고정 policy가 하나의 INNER pilot에서 D1 response diversity를 useful
incremental detection으로 바꾸지 못했다는 뜻이다. 다른 fusion family의 일반적 가치나 held-out
generalization은 검증되지 않았다.

## 13. 현재 말할 수 있는 것

- V1/V2는 frozen upstream prediction만 사용하는 deterministic policy다.
- 두 결과 모두 label-blind combined artifact를 durably persist한 뒤 label을 열었다.
- D0 alarm은 pointwise 보존됐다.
- 현재 pilot에서 V1/V2 모두 11/14, recovery 0/3이며 D0보다 FAR이 높았다.
- No frozen D0-versus-D2 significance test exists.

## 14. 앞으로 fusion을 검증하려면 필요한 것

더 큰 evaluation scope, frozen event-unit definition, validation/final-test separation, final test 전에
고정된 policy, stronger detector, durable upstream predictions, preregistered incremental Recall/FAR 및
D0-miss recovery가 필요하다. 이 문서는 V3를 설계하거나 threshold를 제안하지 않는다.
