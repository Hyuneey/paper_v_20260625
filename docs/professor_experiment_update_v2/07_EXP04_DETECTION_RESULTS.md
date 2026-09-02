# EXP-04 탐지 비교 결과

## 상태

**PREPARED / NOT EXECUTED — LABEL-BLIND PREDICTION FREEZE NEXT**

비교 arm은 D0 PCA-SPE, normal-only Isolation Forest, V2 Verified Relational Rule-only, frozen detector+rule policies입니다. 공통 metric은 Attack-event Recall, Normal FAR/hour, overlap, D0-miss recovery, incremental Recall/FAR, rule coverage와 구현된 abstain/conflict입니다.

EXP-01과 EXP-01B, EXP-02는 정상 데이터만으로 완료됐고 META+STAT 기반 39-rule Formal V4 V2A portfolio가 고정됐습니다. 아직 D0·Isolation Forest·Rule-only·Fusion의 V2 label-blind prediction과 durable freeze를 실행하지 않았으므로 V2 detection result는 없습니다. PILOT V1의 D0 11/14, D1 13/14, D2 V1/V2 11/14는 배경 개발 근거일 뿐 VALIDATION V2 결과로 재사용하지 않습니다.

test1은 앞으로도 development-only입니다. 결과를 본 뒤 새로운 fusion policy를 추가하지 않습니다.
