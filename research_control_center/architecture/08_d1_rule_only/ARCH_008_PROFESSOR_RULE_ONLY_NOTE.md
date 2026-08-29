# 교수님께 설명할 Rule-only 용어

교수님이 요청하신 핵심 비교는 Detector only, Detector + Rule, Rule only입니다. 현재 구현은 이를 각각 D0, D2, D1로 다룹니다.

다만 현재 D1의 정확한 이름은 **COMMON-42 Verified Relational Rule-only**입니다. COMMON-42는 T0, T1, T1-B에서 실행 의미가 공통으로 확인된 42개 V4 descriptor portfolio이며 T2는 포함하지 않습니다. 따라서 D1을 “T2 Agentic Rule-only”라고 부르면 틀립니다. 직접적인 “LLM Rule-only” 성능 실험이라고 부르는 것도 부정확합니다.

그럼에도 “규칙 자체가 이상 사건에 반응하는가?”라는 교수님의 질문에는 D1이 직접 답합니다. 현재 14-event INNER pilot에서 D1은 13개 사건에 반응했고 D0가 놓친 3개 사건 모두에 반응했습니다. 동시에 정상 false episode는 574개, FAR은 40.50255787059723 episodes/hour였습니다.

따라서 지금의 결론은 “규칙 신호가 다른 사건에 반응하는 pilot signal이 있다”까지입니다. Agentic/LLM construction arm 고유의 Rule-only 탐지 성능을 말하려면 T1/T1-B/T2별 canonical runtime portfolio를 독립적으로 고정하고 같은 평가 계약으로 비교해야 합니다.
