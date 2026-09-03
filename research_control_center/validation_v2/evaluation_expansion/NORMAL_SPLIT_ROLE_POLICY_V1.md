# Normal Split Role Policy V1

## HAI 23.05

기존 Validation V2 normal authorities를 변경하지 않는다.

## HAI 22.04

- train1+train2: detector/STAT fit, relation profiling, numeric summaries, optional frozen GDN views
- train3: relation confirmation, detector calibration
- train4: EXP-02 numeric-policy selection
- train5: normal guard
- train6: stability/reproducibility check

## HAI 21.03

- train1+train2: detector/STAT fit, relation profiling, numeric summaries, optional frozen GDN views
- train3 Block A: relation confirmation와 detector calibration
- train3 Block B: EXP-02 numeric selection와 normal guard

train3의 exact row count를 official normal-only custody 이후 확인하고 값 접근 전에 다음 산술을
고정한다. midpoint=`floor(n/2)`. purge width는 history window, relation baseline/response window,
60-second horizon을 모두 포함하는 최대 context 이상이다. 홀수 purge의 나머지는 Block B 쪽에
둔다. A는 `[0, midpoint-floor(purge/2))`, B는
`[midpoint+ceil(purge/2), n)`이다. 파일 경계를 넘지 않고 A/B가 raw timestamp를 공유하지
않는지 custody가 검증한다. 성능에 따라 partition을 고르지 않는다.
