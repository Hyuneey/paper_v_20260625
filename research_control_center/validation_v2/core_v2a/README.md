# VALIDATION V2A — META+STAT core path

이 namespace는 기존 EXP-01의 `COMPLETE_QA_PASS` 결과를 그대로 소비한다.
GDN의 기존 demotion을 바꾸지 않으며, 기본 후보 탐색은 `META_PLUS_STAT`이다.

실행 순서는 다음과 같이 고정한다.

1. 공개 META/STAT authority로 29개 후보 union을 구성한다.
2. 기존 arm-blind train3 확인 authority의 불변 subset으로 별도 방향성 cohort를 만든다.
3. 세 EXP-02 과학 binding을 데이터 접근 전에 고정한다.
4. train1/train2에서만 수치 summary를 만들고, train4 정상 데이터에서 37개 정책을 선택한다.
5. test1, label, test2, held-out은 이 namespace에서 허용하지 않는다.

개인 수치 authority는 Git에서 제외된 `artifacts/validation_v2/core_v2a/private/`에만 저장한다.
