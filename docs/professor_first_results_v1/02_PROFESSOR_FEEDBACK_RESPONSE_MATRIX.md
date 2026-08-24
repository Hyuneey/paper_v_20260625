# 교수님 피드백 대응 매트릭스

| 주제 | 원래 피드백/질문 | 현재 구현 | 무엇이 바뀌었나 | 미구현/한계 | 현재 근거 | 교수님 결정 |
|---|---|---|---|---|---|---|
| LLM | LLM을 왜 쓰며 결과를 어떻게 통제하는가 | T1/T1-B/T2는 제한된 구조만 제안; 숫자·검증·런타임은 별도 권한 | 자유 Python 생성에서 typed contract와 deterministic verifier로 이동 | T2 verifier feedback이 실제 성능 최적화에 기여했다는 근거 없음 | T0/T1/T1-B COMMON-42 동등, T2 39/42 및 3 no_rule | agentic 비교를 핵심 기여로 유지할지 |
| TSFM | 시계열 foundation model을 활용할 수 있는가 | **미구현** | 현재는 검증 가능한 규칙 파이프라인을 먼저 닫음 | TSFM 효과, 비용, 비교 없음 | 주장 근거 없음 | 필수 비교로 요구할지 향후 과제로 둘지 |
| 이상탐지 모델 | 탐지기와 규칙을 왜 결합하는가 | PCA-SPE D0을 참조 기준선으로 구현 | 규칙 자체가 아니라 D0 미탐 보완 가능성을 직접 평가 | 강한 detector baseline 비교 부족 | D1이 D0 미탐 3/3 포착, D2는 0/3 회복 | PCA-SPE 충분 여부 |
| 설명/지역화 | 결과가 무엇을 설명하는가 | source, target, transition, lag, expected response, satisfaction trace | 자연어 설명보다 실행 근거 추적으로 이동 | 사람 유용성 평가 없음 | COMMON-42와 LLM-free runtime trace | 주 설명 인터페이스로 인정할지 |
| 세그먼트 선택/ARTIST | 중요한 시간 구간을 먼저 고를 수 있는가 | **ARTIST식 세그먼트 선택 미구현** | 변수 관계의 transition과 horizon으로 국소화 | 데이터 주도 segment proposal/selection 없음 | 관계 수준 시간 창만 제공 | ARTIST 구성요소 추가 여부 |
| agent 규칙 제어 | agent가 임의 규칙·임계값을 만들지 않는가 | 후보, relation, numeric reference, verifier로 경계 설정 | 직접 숫자/코드 생성을 금지 | agentic repair의 효용은 확인되지 않음 | 수치 authority 420 bindings, deterministic rejection | agentic arm을 본문/부록 어디에 둘지 |
| 시간/동적 관계 | 정적 상관이 아닌 동적 관계를 다루는가 | continuous-step delayed-response, 1/5/10/30/60초 horizon | pairwise static rule에서 사건-반응 규칙으로 확장 | 더 복잡한 multi-stage dynamics/feedback loop 미지원 | 정상 train 기반 profiling, train3 confirmation, COMMON-42 | 현재 rule family 범위 승인 여부 |
| detector + rule 논리 | 단순 OR가 왜 유용한가 | D0, D1, D2 V1 exact same-second multi-source, D2 V2 native-horizon multi-source 비교 | 보완성 자체와 결합 utility를 분리 | 현재 결합 향상 근거 없음 | D1 3/3 보완, D2 V1/V2 0/3 | 결합 향상 주장을 제거할지 |
| 도메인 지식 | 도메인 전문가 지식 의존도가 과도한가 | 변수 역할 metadata와 bounded candidate mask 사용 | 숫자 기준은 정상 데이터에서 결정 | 변수 역할 review와 P1 범위 선정은 여전히 인간 지식 필요 | 144-pair universe와 3개 discovery arm | 도메인 의존성을 한계로 수용할지 |
| 결정론적 설명 | 동일 입력에 동일 설명이 나오는가 | verifier-accepted immutable rule + trace-grounded explanation | LLM 런타임 설명을 금지 | 사용성/신뢰도 human study 없음 | runtime LLM 0, trace binding | 설명 평가를 후속 연구로 둘지 |

## 핵심 정리

현재 설명 가능성은 **실행 가능한 시간 규칙, 변수 관계, lag/horizon, satisfaction trace**에 기반한다. 이는 ARTIST식 “중요 구간 선택”과 같은 것은 아니며, TSFM도 구현되지 않았다. 또한 INNER에서 detector–rule 보완 신호는 확인됐지만 **결합 detector 성능 개선은 지원되지 않는다**.

