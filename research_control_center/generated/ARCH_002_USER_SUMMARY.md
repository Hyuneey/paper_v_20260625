<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=ff5895a48395a92c97930f1c6b72d5583c95b0df7eb675bbe21b768d168a8b6a authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
# 관계 후보는 왜 세 방식으로 고르는가

## 한 문장 답

144개 가능한 source→target 쌍을 META·STAT·GDN이 서로 다른 근거로 20개씩 제안하고,
중복을 접은 47개만 다음 normal relation profiling이 검사한다.

| 방식 | 무엇을 보는가 | 무엇을 내놓는가 | 아직 말할 수 없는 것 |
|---|---|---|---|
| META | reviewed metadata와 physical graph | domain-prior 후보 Top-20 | 물리적 진실·인과 |
| STAT | normal train1/train2의 lagged 변화 상관 | association 후보 Top-20 | confirmed response·인과 |
| GDN | 정상 multivariate next-value prediction | learned-graph 후보 Top-20 | 고유 유용성·인과·attention 설명 |

## 왜 관계 후보를 먼저 줄이는가?

모든 가능한 쌍을 규칙으로 만들지 않고 서로 다른 약한 근거로 profiling 대상만 제한하기
위해서다. 이 단계는 관계를 확정하는 단계가 아니다.

## 144개는 어디서 나오는가?

P1의 ordered source 역할 12개와 target 역할 12개의 directed cross product다. 두 역할
집합은 현재 freeze에서 겹치지 않으므로 12×12=144다.

## META는 무엇을 보는가?

실제 센서 값을 읽지 않고 공식 HAI manual·directed physical graph와 AI-assisted reviewed
semantic declaration을 본다. 명시 연결, graph adjacency, subsystem support 순으로 분류하고
공식 reference category 수와 identity로 결정적으로 정렬한다. 학습 score와 researcher의
최종 Top-20 수동 선택은 없다. Exact public replay에는 private reviewed declaration이 필요하다.

## STAT은 무엇을 보는가?

train1과 train2 각각에서 source/target의 1초 변화량을 만들고 여러 lag에서 Pearson
association을 계산한다. 두 파일에서 부호가 안정적인지 확인하고 약한 쪽 strength로
정렬한다. 후속 delayed-response profiling과는 별개다.

## GDN은 무엇을 학습하는가?

37개 P1 node의 5초 history로 다음 1초 값을 예측한다. 학습된 node embedding의 cosine
similarity로 target별 neighbor graph를 만들고 세 seed에서 반복 선택된 edge를 우선한다.
현재 Top-5는 diagonal/self를 먼저 제거하지 않아 자기 node가 내부 슬롯을 차지할 수 있다.
후속 disjoint-role projection이 exported self-pair는 제거하지만 기능적 영향은 미검증이다.

## GDN attention을 쓰는 것인가?

모델 내부 message passing에는 attention을 쓴다. 그러나 attention coefficient를 후보
ranking이나 최종 관계 evidence로 쓰지 않는다. 후보 authority는 embedding-cosine
learned graph다. 별도 XAI나 SHAP도 쓰지 않는다.

## GDN edge는 어떤 의미인가?

target 예측에 선택된 neighbor/input dependency **후보**다. 원인, root cause, 확정된
시간 관계가 아니다.

## 20+20+20인데 왜 47개인가?

세 arm에서 겹친 pair를 exact directed identity로 한 번만 남기기 때문이다. META-only 8,
STAT-only 8, GDN-only 18, 두 arm 공통 13, 세 arm 공통 0으로 총 47이다. Arm score는
합치거나 비교하지 않으므로 47개 전체 순위도 없다.

## 다음 단계에서 무엇을 검증하는가?

47개 cohort를 normal delayed-response profiling에 넘겨 step event, response direction,
horizon과 안정성을 별도로 확인한다. 그 전에는 최종 relation이라고 부르면 안 된다.

다음 task는 **DG-04 후속 정상 준비 — BLOCKED_NORMAL_DATA_CUSTODY (schema-only projection 범위 확인)**이다.

## 현재 DG-04 / 외부 준비 Gate

DG-04 / DEC-025 승인 완료. DG-03B_REVISED 승인 후 동결한 EXP-03B에서 T2는 T1-B 대비 이점이 있으나 T0보다 우수하지 않았습니다. T0 22 Rules, T2 Repeat 1 21 Rules는 별도 HELDOUT_CANDIDATE이며 V2A39·기존 결과는 불변입니다.

Stage B는 BLOCKED_NORMAL_DATA_CUSTODY. 공식 정상 train1 두 컨테이너의 byte identity 검증 후 embedded label schema에서 중단했습니다. label 값 해석·과학 사용 0이며 정상 컨테이너 byte traversal은 있었습니다. 추가 header 접근 자동심사를 우회하지 않았습니다. Schema-only label 식별 및 feature-only projection 범위를 확인해야 합니다.

외부 STAT/GDN/T0 미실행, DG-03C N/token/cost 미정. eTaPR109 synthetic per-file 일치; 버전 내 집계는 미정. Provider·credential·공격 payload 0. 상세: validation_v2/dg04_xver_prep/CURRENT_PREPARATION_STATUS_V1.md. 전체 task PASS가 아니며 integration merge/push·교수 제출은 하지 않습니다.
