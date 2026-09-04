# Privacy / custody

Provider·credential·capability probe=0인 준비 작업이다.
normal 데이터와 numeric roles, checkpoints, evidence packs는 ignored private namespace에 보관한다.
Public receipt에는 hash/count/status만 기록한다.
normal accessor는 기존 official materialization receipt와 private manifest self-hash로 정확한 root를 선택한다.
test1/test2/held-out mapping은 EXP03B wrapper에서 거부한다.
train3는 공개 frozen relation reference만 재생하고 feature 파일을 열지 않는다.
원본 EXP03 V1, V2A, EXP04/05와 PILOT V1은 byte identity로 보호한다.
별도 독립 storage가 검증되지 않으면 SINGLE_COPY_LOCAL_ONLY이며 backup으로 부르지 않는다.

