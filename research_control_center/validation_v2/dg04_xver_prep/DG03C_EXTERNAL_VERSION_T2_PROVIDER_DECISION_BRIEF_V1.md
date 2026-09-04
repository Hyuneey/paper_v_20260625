# DG-03C — 아직 승인 가능한 예산이 아님

상태: NOT_READY_BLOCKED_NORMAL_DATA_CUSTODY. 현재 USER_DECISION_REQUIRED provider package로 표시하지 않습니다.
선호 snapshot gpt-5.4-mini-2026-03-17 / Responses API; 이동 alias·자동 fallback 금지.
HAI22와 HAI21 모두 candidate N, GDN evidence, T0, 정확한 payload/token/cost가 아직 미동결입니다.
따라서 calls/tokens/cost ceiling은 UNKNOWN이며 0원/0-token ceiling으로 오표시하지 않습니다.

고정 외부 계획: T2만 pair당 한 portfolio-producing 실행, 최대3회, ACCEPTED 즉시 종료. R=3/T1/T1-B 재실행 없음.
최대 호출 공식은 버전당 3×N입니다. N과 exact prompt가 확보되기 전에 budget을 추정 승인하지 않습니다.
Provider projection은 버전별 train1 구조·STAT·GDN, bounded train2 repair만 허용합니다.
수치정책/역할값·최종답·META tier/선언·train3/4·공격·다른 arm·private path·credential은 금지합니다.
No credential read / capability probe / provider call. 이전 DG03B 승인은 외부 버전에 승계하지 않습니다.

정확한 다음: 정상 컨테이너의 label 열을 schema로만 식별하고 값은 배제하는 projection 범위 확인 →
normal custody → mapping/candidates/GDN/T0 → evidence/prompt freeze → exact DG03C budget.
