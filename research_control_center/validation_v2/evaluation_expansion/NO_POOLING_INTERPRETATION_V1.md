# No-pooling Interpretation V1

## 금지되는 주 결과

- HAI 23.05/22.04/21.03의 하나로 합친 primary Recall
- 146 nominal scenario를 IID 표본으로 간주한 confidence interval 또는 significance claim
- HAI와 HAIEnd를 별도 attack event처럼 중복 합산
- official scenario를 interval/intervention으로 잘라 독립 attack 수로 계산
- synthetic violation을 real attack denominator에 추가

## 허용되는 cross-version summary

- 버전별 exact numerator/denominator와 Wilson 95% interval
- version-macro mean과 version-level range
- 같은 방향을 보인 버전 수
- 버전별 paired discordant counts
- attack morphology·feature compatibility의 heterogeneity narrative
- explicit non-IID 경고가 붙은 pooled descriptive count

LEVEL 1 official scenario가 primary statistical unit이다. LEVEL 2 contiguous interval과 LEVEL 3
intervention/response episode는 secondary description이며 새로운 독립 표본을 만들지 않는다.
