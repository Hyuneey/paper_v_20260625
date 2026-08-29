# GDN 기반으로 관계를 어떻게 도출하는가

Scientific authority: `origin/research-v6-thesis-checkpoint` @ `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`

## 1. 현재 실제 방식

현재 GDN arm은 P1의 정상 `train1`·`train2`에서 37개 node의 5초 history로 다음 1초 값을 예측하도록 학습된다. 학습 과정에서 각 node의 64차원 embedding을 얻고, embedding 간 cosine similarity로 target별 Top-5 neighbor를 만드는 `learned_graph`를 구성한다. 세 seed의 graph를 144개 허용 source→target 공간에 투영한 뒤, edge가 선택된 seed 수와 median cosine similarity로 정렬하여 GDN Top-20 후보를 만든다.

## 2. attention의 역할

Graph attention은 선택된 learned-graph edge 위에서 message passing을 수행하는 모델 내부 연산이다. attention coefficient를 내보내어 후보를 순위화하거나 최종 관계 근거로 사용하지 않는다. 따라서 “attention weight가 관계를 설명한다”는 표현은 현재 코드와 맞지 않는다.

## 3. XAI 사용 여부

별도 post-hoc XAI, SHAP 또는 attribution 방법은 현재 frozen discovery에서 사용하지 않는다.

## 4. learned graph edge가 의미하는 것

`i → j`는 보수적으로 **j의 예측 입력 dependency로 선택된 i neighbor 후보**를 뜻한다. 물리적 인과, root cause, 확정된 delayed response를 뜻하지 않는다.

## 5. 최종 temporal relation이 정해지는 단계

GDN edge는 후보 제안 단계의 결과다. 이후 별도 normal delayed-response profiling에서 방향, horizon, response evidence를 확인해야 관계 evidence가 된다.

## 6. 아직 검증해야 하는 GDN 기여

GDN이 META/STAT보다 고유하고 유용한 관계를 안정적으로 제공하는지는 미검증이다. 향후 EXP-01에서 seed 안정성, split 안정성, 고유 confirmed contribution, edge/source masking 효과를 독립적으로 평가해야 한다. GDN-Functional은 네 번째 discovery arm이 아니라 이 검증 절차다.
