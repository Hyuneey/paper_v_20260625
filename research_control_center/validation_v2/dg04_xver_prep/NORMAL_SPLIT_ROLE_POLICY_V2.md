# 정상 split 역할 V2 — 전향적 계획

V1의 external EXP-02 재선택 계획을 prospectively supersede합니다. V1은 삭제하지 않습니다.
HAI23 기존 authority는 변경하지 않습니다.

| 버전 | train1 | train2 | train3 | train4 | train5 | train6 |
|---|---|---|---|---|---|---|
| HAI22 | provider/T0 구조·STAT·GDN | hidden verifier/retrieval | hidden confirmation·detector calibration | numeric evaluation·one-way guard | normal robustness | stability/reproduction |
| HAI21 | provider/T0 구조·STAT·GDN | hidden verifier/retrieval | A confirmation/calibration; purge; B one-way guard | 해당 없음 | 해당 없음 | 해당 없음 |

Detector fit과 candidate STAT는 별도 고정 authority로 train1+train2를 사용할 수 있습니다.
Provider STAT/GDN은 train1-only, retrieval은 train2-only입니다. Train3/guard는 돌아오지 않습니다.
수치 정책은 n7-q0.90-s2-f0.05 고정. 37-option 재선택을 하지 않으며 각 버전 train1/train2 통계로
SCI-02B 값을 산출하고 보수적 max pooling합니다. HAI23 수치값을 이전하지 않습니다.

HAI21 row arithmetic: n 행, m=floor(n/2), purge p의 좌측 floor(p/2), 우측 ceil(p/2).
A=[0,m-floor(p/2)), B=[m+ceil(p/2),n). 기존 partition_hai21_train3_v1을 재사용합니다.
정확한 p는 전체 외부 모델 feature/context authority를 완성한 뒤 history/baseline/response/horizon
의 합성 최대 raw context 이상으로 사전 동결해야 합니다. 현재 n/p 값은 미적용이며 값 기반 분석 0입니다.
이 문서는 역할 고정이며 아직 실행 가능한 분할 receipt가 아닙니다.
