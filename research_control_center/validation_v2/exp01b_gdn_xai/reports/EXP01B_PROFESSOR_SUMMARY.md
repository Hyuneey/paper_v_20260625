# 교수님 피드백에 따른 GDN Prediction Model + XAI 추가 검증

기존 EXP-01의 음성 결과를 수정하지 않고, 별도 사전등록 실험 `EXP-01B-GDN-XAI-V1`을
수행했습니다. corrected self-excluded GDN을 3개 view와 3개 seed로 학습하고,
Embedding, Attention, EdgeMask, Source Occlusion을 같은 144-pair 정상 관계 참조에서
비교했습니다.

K=29에서 META+STAT+GDN 결합 순위는 META+STAT보다 confirmed pair yield가 20에서
21로, NDCG가 0.7428에서 0.7629로 소폭 높았습니다. 그러나 train1-only/train2-only
안정성 비열화 조건을 충족하지 못했고, GDN 고유 confirmed pair 3개 가운데 Formal V4
실행 규칙으로 전환된 pair는 0개였습니다. primary Top-K EdgeMask의 중앙값도 양수가
아니었습니다.

따라서 사전에 고정한 판정 규칙에 따라 결과는 `GDN_ABLATION_ONLY`입니다. V2의 주
후보 탐색 authority는 META+STAT을 유지합니다. 이 결과는 GDN이 일반적으로 무용하다는
주장이 아니며, attention이나 masking이 인과성을 증명한다는 주장도 아닙니다.

이번 실험은 normal train1~4만 사용했습니다. test1, 공격 label, test2, held-out,
외부 provider 접근은 모두 0입니다.
