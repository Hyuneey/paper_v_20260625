<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=5346d667107de191b6acec481450f36906193d1f4dfa3e8831e02653607ac0bf authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
# 우리가 어떤 데이터를 쓰고 있는가

## 한 문장 답

우리는 공식 provenance가 고정된 HAI 23.05의 P1 Boiler 범위를 사용하며, 정상 학습
split과 INNER pilot, 아직 결과가 없는 held-out test2를 서로 다른 권한으로 다룬다.

## Split 한눈에 보기

| Split | 역할 | 무엇을 정하는 데 사용? | Label 사용? | 최종평가? |
|---|---|---|---|---|
| train1 | NORMAL FIT | 후보·관계·수치 authority·D0 fit | 아니오 | 아니오 |
| train2 | NORMAL FIT | train1과 독립적인 file-local fit 근거 | 아니오 | 아니오 |
| train3 | CONFIRMATION / CALIBRATION | 관계 확인과 D0 threshold 보정 | 아니오 | 아니오 |
| train4 | SANITY | normal guard와 D0 정상 sanity | 아니오 | 아니오 |
| test1 | PILOT EVALUATION | frozen 방법의 INNER 개발·예비 비교 | prediction 뒤에만 | 아니오 |
| test2 | HELD-OUT / UNAVAILABLE | 의도상 one-way 일반화 평가 | 실행되지 않음 | 결과 없음 |

## 왜 여러 train split이 있는가?

같은 normal data를 한 단계에서 만들고 같은 단계에서 확인하는 것을 피하려고 역할을
나눈다. train1/train2는 fit, train3는 독립 확인과 D0 threshold calibration, train4는
normal sanity에 사용된다. train3를 두 arm이 함께 쓰는 것은 확인된 leakage가 아니지만,
비교 독립성의 범위를 제한하므로 `ACCEPTABLE_WITH_SCOPE_LIMITATION`으로 기록했다.

## Rule을 만들 때 공격 답을 본 적이 있는가?

찾아본 현재 frozen 경로에서는 아니다. 후보 탐색, 관계 profiling, normal numeric
authority, evidence pack, T0/T1/T1-B/T2, verifier, COMMON-42는 normal-only evidence를
사용한다. test1 결과로 individual rule을 뒤에서 삭제하거나 COMMON-42를 다시 고른
경로도 확인되지 않았다.

## D0 threshold는 어디서 결정되는가?

D0는 train1과 train2로 표준화와 PCA를 fit하고, train3의 normal SPE 분포로 threshold를
calibrate한다. test1 label이나 test1 outcome은 model fit과 threshold 결정에 들어가지 않는다.

## Label은 언제 보이는가?

D0와 D2는 prediction file을 atomic하게 기록하고 다시 읽은 뒤 label을 연다. D1도
label-blind prediction object를 먼저 만들고 self-hash를 검증하지만, public prediction
file은 metric 뒤에 기록된다. 그래서 D1은 decision-before-label은 확인됐지만 durable
file-before-label 보장은 부족하다. 이것은 HIGH governance gap이며 leakage가 확인됐다는
뜻은 아니다.

## test1은 왜 final test가 아닌가?

현재 14개 사건은 작은 INNER pilot이다. 특히 D2 V2 policy는 앞선 INNER 결과를 알고
설계되었다고 명시되어 있다. 따라서 test1 수치는 개발·예비 관찰이며 독립 성능 검증이나
일반화 증거가 아니다.

## test2는 왜 결과가 없는가?

OUTER recovery는 test2 feature custody 확인에서 멈췄다. 파일 접근 시도는 한 번 있었지만
feature byte, hash, semantic parse는 0이고 label·prediction·metric도 0이다. 따라서
성능이 실패한 것이 아니라 **held-out result unavailable**이다.

## 현재 leakage 우려는 무엇인가?

**NO VERIFIED LEAKAGE FOUND.** 다만 D1 durable persistence gap, task별로 분산된 split
enforcement, train3 dual use, test1-informed D2 V2 때문에 “leakage impossible”이라고는
말할 수 없다.

## 다음 파트 전에 이해할 것

1. feature 파일과 label 파일은 별도 authority다.
2. 86 dataset points, 37 P1 features, 12×12 role universe는 같은 숫자가 아니다.
3. label-blind object와 durable prediction file은 서로 다른 보장이다.
4. test1은 pilot이고 test2는 결과가 없다.

다음 task는 **V2-HAI-NORMAL-MATERIALIZATION-001 — CODE_BASED_MATERIALIZATION for train1~4**이다.
