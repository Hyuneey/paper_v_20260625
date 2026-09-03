<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=7843bc595fd526de37fa6765d7982848c00d23c6391d954f25e1ba155557c3ea authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
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
| 시간당 정상 오경보율 (Normal FAR/hour) | 7개 normal false episode를 normal exposure hour로 나눈 `0.4939336325682589` |

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

다음 task는 **DG-03 — EXP-03 Provider Execution Decision**이다.
