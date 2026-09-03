# V2 GDN 보조 근거 연결 및 EXP04 실행

이 namespace는 기존 V2A META+STAT 39-rule portfolio를 변경하지 않는 실행·보존·보고 계층이다. GDN은 frozen EXP-01C의 predictive supporting evidence이고 새로운 discovery 실험을 실행하지 않는다.

실행 순서: scope와 sidecar → 필수 private 보존 → 합성 성능/QA → Commit A → freeze receipt/Commit B → 정상 fit → label-blind test1 predictions 5개 → 전부 durable freeze → label capability → development metrics와 모든 실제 EXP05 traces → 독립 QA/Commit C.

현재 이 README의 최초 작성 상태는 PRE_FEATURE다. 실제 실행 여부는 contracts/ 및 results/ receipt와 최종 report를 확인한다. test1은 DEVELOPMENT_ONLY, held-out 일반화와 human usefulness는 미검증이다. DG-03 provider, DG-04 최종 제목, DG-05 heldout, DG-06 제출은 별도 결정이다.
