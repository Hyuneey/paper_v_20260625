# 7. 논의

## 7.1 LLM 규칙에서 결정론적 수치 권한이 필요한 이유

LLM은 관계 구조를 언어적·구조적으로 조합하는 데 유용하지만, 특정
threshold나 tolerance가 정상 공정을 대표한다는 근거를 스스로 만들 수
없다. 수치까지 LLM에 맡기면 같은 evidence에서 다른 값이 생성되고,
결과에 맞춰 parameter를 바꾸는 경로가 생긴다. 본 방법은 수치를 normal
calibration artifact에 연결해 규칙의 의미를 재현 가능하게 만든다.

이는 LLM을 제거하는 설계가 아니라 권한을 제한하는 설계다. proposal의
유연성은 남기되 scientific acceptance는 deterministic system이 담당한다.

## 7.2 Validity와 utility를 분리해야 하는 이유

구조가 맞고 정상 evidence에 근거한 규칙도 anomaly detection에는 유용하지
않을 수 있다. 반대로 attack label 성능이 좋아 보이는 규칙이 정상 관계나
parameter provenance를 위반한다면 valid rule이 아니다. 두 기준을 한 단계에
섞으면 label leakage와 사후 최적화가 발생한다.

본 결과는 이 분리의 필요성을 직접 보여준다. COMMON-42는 검증되고 실행
가능하지만 D1의 FAR는 높다. validity 성공은 utility 성공의 필요조건일 수
있어도 충분조건이 아니다.

## 7.3 높은 FAR에도 D1 complementarity가 중요한 이유

D1은 D0 miss 3/3을 모두 포함했다. 이는 normal temporal relation violation이
PCA residual score와 다른 event evidence를 가질 수 있음을 시사한다. 이
보완성은 규칙 구성 연구의 과학적 가치다. 하지만 FAR 40.50255787059723은
그 신호를 그대로 운영 경보로 사용할 수 없음을 동시에 보여준다.

따라서 “규칙이 미탐을 찾았다”와 “규칙 detector가 배포 가능하다”를
구분해야 한다. 본 연구는 첫 문장을 INNER evidence로 지지하지만 두 번째는
지지하지 않는다.

## 7.4 Event sensitivity가 deployability를 의미하지 않는 이유

event recall은 event 안에 한 번이라도 alarm episode가 겹치면 탐지로 센다.
규칙이 공정 변화에 민감하면 짧은 attack event를 포착할 수 있지만 정상
전이에서도 같은 relation check가 자주 발생할 수 있다. D1의 574 normal
episodes는 sensitivity와 specificity가 분리된다는 점을 보여준다.

## 7.5 Event-level complementarity가 D2 utility로 이어지지 않은 이유

event set은 시간 구간의 overlap을 요약한다. 반면 D2 gate는 매초 운영
가능한 label-blind decision을 만들어야 한다. V1은 two-source simultaneous
signal만 허용해 asynchronous evidence를 버렸다. V2는 이를 기억했지만
attack-specific evidence와 normal evidence를 구분하지 못했다.

결과적으로 event-level union은 이상적인 선택 규칙이 아니다. successful
fusion은 단순 presence가 아니라 evidence timing, source identity, normal
prevalence, detector state를 함께 고려하면서도 새 tuning leakage를 만들지
않아야 한다. 현재 연구는 이를 해결하지 않았으며 D2 V3를 자동 제안하지
않는다.

## 7.6 Negative fusion result가 주는 지식

V1의 실패는 exact same-second corroboration이 너무 보수적임을 보여줬다.
V2의 실패는 temporal memory만 추가하면 정상 false alarms가 함께 누적될
수 있음을 보여줬다. 따라서 필요한 것은 단순히 더 긴 window가 아니라
어떤 evidence가 normal context에서도 반복되는지에 대한 구별 가능성이다.

이 negative evidence는 규칙 신호가 없다는 뜻이 아니다. 신호가 존재하지만
현재 operational gate가 useful utility로 변환하지 못한다는 더 구체적인
결론을 제공한다.

## 7.7 자유 자연어 설명과의 차이

본 방법의 explanation은 자연어 생성 품질에 의존하지 않는다. 설명 단위는
검증된 source–target relation, frozen parameter reference, runtime operator,
observed outcome이다. 같은 rule과 window는 같은 trace를 낸다. 이 구조는
감사와 재실행에 유리하지만 사람이 실제로 더 빠르고 정확하게 사고를
이해하는지는 별도 human study가 필요하다.

## 7.8 교수 결정과 해석 범위

현재 근거가 가장 강한 framing은 graph-guided verified rule construction이다.
설명 interface, OUTER 우선순위, detector baseline 강화 여부는 교수님의
논문 범위 판단에 따라 바뀔 수 있다. 이 결정 전에는 새로운 결과를
추가하기보다 현재 근거와 한계를 명확히 서술하는 것이 합리적이다.
