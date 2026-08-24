# 3. 문제 정의

## 3.1 다변량 시계열과 변수 역할

샘플 간격이 1초인 다변량 시계열을

\[
X = \{\mathbf{x}_t\}_{t=1}^{T}, \qquad \mathbf{x}_t \in \mathbb{R}^{d}
\]

로 둔다. 변수 집합은 source 후보 \(S\)와 target 후보 \(Y\)로 역할이
구분된다. source는 제어 command 또는 actuator feedback처럼 공정 변화를
유발하거나 나타내는 변수이고, target은 그 변화에 반응하는 연속 공정
센서다. 역할 구분은 후보 범위를 제한하지만 물리적 인과를 증명하지 않는다.

## 3.2 후보 방향 관계

후보 관계는 \(r=(s,y)\), \(s\in S\), \(y\in Y\)인 방향쌍이다. graph,
metadata, statistical ranking은 \(r\)을 조사할 우선순위를 제공한다. 후보
선정은 relation validity나 anomaly utility를 의미하지 않는다.

## 3.3 Source transition과 delayed response

source event \(e=(s,t_e,d)\)는 source \(s\)가 시간 \(t_e\)에서 방향
\(d\in\{\uparrow,\downarrow\}\)으로 안정된 step transition을 보인
사건이다. refractory와 cross-source isolation 규칙으로 중복·오염 사건을
제거한다. 후보 horizon \(h\in H=\{1,5,10,30,60\}\)에 대해 target 변화
\(\Delta y_{t_e,h}\)의 방향, 일관성, robust effect를 정상 파일별로
측정한다.

정상 시간 관계 증거는 source event support, target response direction,
선택 horizon, effect/consistency summary, split·parameter reference를 포함한
결정론적 기록이다. 이 증거는 관계가 정상 데이터에서 반복 관측됐음을
뜻하지만 보편적 법칙이나 원인은 아니다.

## 3.4 검증된 시간 규칙

검증 규칙 \(q\)는 다음 요소를 갖는다.

\[
q=(s,y,e_s,d_y,[h_{min},h_{max}],\theta,\pi)
\]

여기서 \(e_s\)는 source trigger, \(d_y\)는 expected target direction,
\(\theta\)는 직접 수치가 아니라 normal calibration artifact reference,
\(\pi\)는 abstention·output·claim policy다. verifier를 통과하고 명시적
runtime authority를 가진 규칙만 실행할 수 있다.

## 3.5 Runtime outcome과 trace

각 평가 기회에서 규칙은 expected response satisfied, anomaly/violation,
abstain 중 하나의 상태를 낸다. abstain은 필요한 입력 또는 window가
부족해 판단하지 못한 상태이며 실패나 정상으로 치환하지 않는다.
satisfaction trace는 regime, trigger, lag, window, relation, tolerance,
persistence, abstention, output 단계를 순서대로 기록한다.

## 3.6 Reference detector와 attack event

기준 탐지기의 점별 경보를 \(a_t^{D0}\in\{0,1\}\), 규칙 계층 경보를
\(a_t^{D1}\in\{0,1\}\)로 둔다. 연속한 1초 경보는 하나의 alarm episode로
병합한다. attack event는 label 값이 정확히 1인 maximal contiguous
file-local run이다. 예측은 label을 읽기 전에 고정된다.

Attack-event Recall은 하나 이상의 alarm episode와 겹친 attack event의
비율이다.

\[
Recall_{event}=\frac{|\{E_i:\exists A_j, E_i\cap A_j\neq\varnothing\}|}
{|\{E_i\}|}
\]

Normal FAR/hour는 attack timestamp와 겹치지 않는 alarm episode 수를
정상 label seconds의 시간 단위로 나눈 값이다.

## 3.7 이벤트 수준 보완성

D0가 놓쳤으나 D1이 탐지한 event가 존재할 때 D1은 D0에 event-level
complementary evidence를 제공한다. 이는 두 prediction set의 관계이며,
D1이 더 우수하거나 운용 가능하다는 뜻이 아니다. D0와 D1의 합집합
coverage도 실제 fusion output과 구별한다.

## 3.8 Rule validity와 rule utility의 분리

**Rule validity**는 규칙이 deterministic scientific/evidence contract를
만족하는지를 묻는다. 구조, 변수 역할, graph/evidence binding, parameter
provenance, split compliance, operational contract, claim boundary가 대상이다.
공격 label 성능은 validity 승인 근거가 아니다.

**Rule utility**는 유효한 규칙이 anomaly event를 탐지하고 detector miss를
보완하면서 감당 가능한 false alarm을 유지하는지를 묻는다. utility는
label-aware INNER 평가이며 validity를 소급 변경하지 않는다.

이 분리는 “실행 가능하고 근거가 있는 규칙”과 “탐지에 유용한 규칙”을
동일시하지 않기 위한 본 논문의 중심 원칙이다.
