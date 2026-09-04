<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=0679baf23b38ac292c9ec0334debce0277b7bbb1b7d17558ff90374c40286fe3 authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
# 우리 연구가 어떻게 여기까지 왔나

## 처음 무엇을 하려 했는가

사용자 기록에 따르면 2025년 말부터 DHAG 확장과 PoC를 검토했고, 2026년 봄에는
ARGOS·LLMAD 같은 관련 연구와 설명 충실도 검증 중심의 방향을 탐색했다. 이 초기
시기는 Git에 동시대 기록이 충분하지 않으므로 정확한 실패 원인이나 날짜를 확정하지
않는다.

## 왜 방향이 바뀌었는가

자유로운 LLM 규칙이나 설명을 과학적 권한으로 쓰면 변수·숫자·검증·실행의 책임이
불명확해진다. 7월의 저장소 기록은 ARGOS를 그대로 복제하기보다 유용한 요소만 남기고,
규칙 구조·수치 근거·검증·런타임을 분리하는 CPS 관계 규칙 방향을 보여 준다. HAI에서
기존 이산 제어원 가정이 실패했을 때도 기준을 완화하지 않고 연속 step-response 계열을
새로 사전등록했으며, 그 결과 P1만 선택되었다.

## 지금 방법에 남은 핵심 아이디어

- DHAG 시기: 구조적 한계를 명시적인 계약으로 다뤄야 한다는 교훈일 가능성만 남았으며, 정확한 계승 관계는 아직 확인되지 않았다.
- ARGOS 탐색: 실행 가능한 규칙, 학습 단계의 제한된 제안·수정, 탐지기 보완, 명시적 no-op, 저비용 결정론적 런타임이라는 아이디어가 남았다.
- Verifier 시기: 결정론적 승인과 근거 결합 원칙은 남았지만, 독립적인 충실도 입증 주장은 남지 않았다.
- 교수님 피드백 재정리: pairwise-first 범위, 독립적인 Rule-only 비교, 좁은 용어 사용, 보수적인 검증 경계가 강화되었다.
- 현재 조합: 여러 후보 근거의 분리·통합, 정상 데이터 전용 시간 관계 프로파일링과 수치 권한, 제한된 규칙 구성, 결정론적 검증, COMMON-42, LLM 없는 런타임, 분리 관리되는 D0·D1·D2 근거가 결합되었다.

## 버린 것 / 보류한 것

현재 핵심에서 제외된 것은 DHAG를 전면 방법으로 삼는 주장, Faithfulness Verifier가
과학적 진실을 증명한다는 주장, ARGOS의 직접 복제, HAI 이산 제어원 경로, 그리고
ARTIST식 학습 기반 segment 선택이다. 복잡한 관계와 runtime LLM은 틀렸다고 판정한
것이 아니라 별도 설계가 필요한 조건부 과제로 남아 있다.

## 교수님 피드백이 실제로 바꾼 것

2026-08-04 피드백은 사용자 기록으로 보존한다. pairwise-first 프로토콜은 이미
8월 3일 고정되어 있었으므로 이 피드백은 그 기원을 만든 사건이라기보다 범위와 표현을
강화한 것으로 기록한다. Rule-only를 fusion 안에 숨기지 않고 별도로 보며, verifier와
GDN과 agent라는 단어를 좁게 쓰고, 실행과 검증을 구분하는 방향이 이후 구현에 남았다.
8월 18일은 내부 진행 업데이트이고, 8월 26일은 통합 보고서 준비이지 새 교수님 피드백이 아니다.

## 현재 위치

HAI 23.05 P1에서 후보 탐색, normal-only 관계·수치 근거, COMMON-42, 고정 규칙 런타임,
D0/D1/D2 INNER 예비 평가와 결과 무결성 감사까지 구현되었다. 그러나 14개 사건 수치는
pilot evidence일 뿐이다. Rule-only 실용성, D2 개선, GDN 고유 기여, Agentic 이점,
사람 대상 설명 유용성, 홀드아웃 일반화는 아직 검증되지 않았다.

## 앞으로는 무엇을 검증해야 하는가

새 독립 사전등록 아래 더 많은 사건과 더 강한 다변량 탐지기 기준선으로 Rule-only와
detector 비교를 확장해야 한다. GDN 안정성과 고유 기여, 실제 피드백이 발생하는 T2 비교,
fresh-machine 재현도 별도로 검증해야 한다. 다음 관리 작업은 **DG-XVER-PROVIDER**이다.

## 현재 DG-04 / 외부 준비 Gate

HAI-XVER-NORMAL-PREP-001: 정상-only 실행 완료, 독립 최종 QA PASS. DG-XVER-PROVIDER에서 정지합니다.
HAI22/HAI21 GDN은 각각6회, 총12회입니다. GLOBAL5는 train1 provider / train2 retrieval, EVENT10은 보조 분석 전용이며 융합·후보·verifier·T0·숫자·guard 사용을 금지합니다.
HAI22 T0: 13 Rules/12 pairs. HAI21 T0: 7 Rules/5 pairs. 모두 HELDOUT_CANDIDATE, 공격 검증·production 결과가 아닙니다.
T2 provider/retrieval packs와 정확 예산은 버전별 고정됐습니다. 합계 최대 174 calls, 3622912 tokens, 표준 공개가격 상한 USD 4.06이며 실제 지출이 아닙니다.
DG-XVER-PROVIDER는 USER_DECISION_REQUIRED; provider/credential/공격 접근0. DG05 NOT_APPROVED; 교수 package NOT_SUBMITTED; DG06 필수.
DEC025 제목·claim·HAI23 V2A/T0/T2·EXP03B·EXP02·EXP04/05·PILOT 결과 불변. T2>T1-B는 정상 의미 유도에 한정하며 T0보다 우수하지 않습니다.
후보 권한 META+STAT, GDN은 비인과적 learned-graph evidence, SCI02B 고정 숫자 결합, FormalV4 실행권한, guard 단방향. 37정책 재선택·META 재구성·best seed 없음.
eTaPR109 합성/가상 동등성 PASS. 다중파일/empty/secondary P1 해석은 DG05 전 결정 항목으로 유지하며 실제 eligibility는 생성하지 않았습니다. 백업 SINGLE_COPY_LOCAL_ONLY.
