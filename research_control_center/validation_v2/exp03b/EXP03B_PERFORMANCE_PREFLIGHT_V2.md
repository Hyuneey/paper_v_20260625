# EXP-03B payload 성능 preflight V2

기존 hash-bound split-pure evidence에서 선택지표 없이 구조·STAT·GDN만 투영했습니다. 정상 raw feature 재읽기·GDN 재학습·provider 실행 없음. train1/train2 별도 cache; T0 once/pair. provider/verifier는20 tuple 조회이며740 numeric rows를 계산/전송하지 않습니다. 후속 binder는 고정 policy만 읽고 old37-grid를 재탐색하지 않습니다.
초기 local token min/median/max=1562/1863/1942; schedule 최대형태 estimate=1,515,342. 실제 API latency/usage는 미측정. 29 payload마다 hash와 token profile 결속. hard cap은 별도 budgetV2입니다.
새 projection은 기존 train1 structural/STAT/GDN 값에 exact equality이며 scientific evidence 변형/반올림/요약 변경 없음. Binder formula·max pooling·FormalV4/guard는 기존 구현 재사용 및 synthetic equality 검사를 수행합니다.
