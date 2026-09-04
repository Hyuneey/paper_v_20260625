# 정상 split 역할 V3 — schema-only amendment 적용

V1/V2는 역사적으로 보존. 외부 numeric option search는 superseded.
HAI22: train1 provider/T0, train2 hidden verifier/retrieval, train3 hidden confirmation/calibration,
train4 numeric evaluation/one-way guard, train5 robustness, train6 reproducibility.
Candidate STAT와 별도 detector fit은 train1+train2; provider/retrieval STAT는 각각 split-pure.
HAI21: train1/provider/T0, train2/hidden/retrieval, train3 n=478801.
Frozen arithmetic p=60, A=[0,239370), purge=[239370,239430), B=[239430,478801).
이 산술은 projection 전에 contract로 고정했으며 현재 schema/count로 materialize했을 뿐 block scientific values는 미사용입니다.
No shared timestamp/context; windows/events를 각 block 내부에서만 생성합니다.
SCI02B n7-q0.90-s2-f0.05 deterministic normal train1/train2 max pooling; 37옵션 재선택0.
