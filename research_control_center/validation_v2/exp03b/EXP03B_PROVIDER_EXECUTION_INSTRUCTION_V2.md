# EXP-03B V2 승인 후 실행 지침

현재 실행 금지: DG-03B_REVISED USER_DECISION_REQUIRED. 구현 commit `6b8463f5e420485fca0848d315db8cb7af112117`. 최종 통합 commit은 `git log -1 --format=%H -- research_control_center/validation_v2/exp03b/EXP03B_SEMANTIC_PREPARATION_FREEZE_V2.json`으로 freeze 추가 commit을 확인하고 branch/origin parity를 검증합니다.
Exact model `gpt-5.4-mini-2026-03-17`; calls≤609, input≤7216128, output≤1247232, total≤8463360, USD≤11.03.

1. 새 사용자 승인 뒤에만 private approval receipt를 생성합니다. `gate=DG-03B_REVISED`, `status=APPROVED`, `budget_hash=e6731a2fcfc1969287f74217b6cccb05f970673b5684a20493dec535b0ad28b6`, `execution_freeze_hash=bacfd22859bb7014f3604abf4ad81b63586e1a98f21ddb0206b4a8e892f8ab8c` 및 canonical self_hash. 이전 승인파일 재사용 금지. 현재 준비 코드가 승인을 만들지 않습니다.
2. source/public/private hashes·ignored custody·PILOT 보존·clean/origin parity를 점검합니다. PYTHONPATH=src;tests. `python scripts/execute_exp03b_provider_v2.py --approval <private-approved-receipt> --probe-only`. 이 작업에서는 실행하지 않았습니다. 승인·budget·source·phase gate 통과 후 transport 안에서만 credential을 읽습니다.
3. 첫 과학 호출은 추가 probe가 아닌 schedule 첫 호출입니다. response/cost/latency receipt atomic write/fsync/close/reopen/hash replay 및 model/schema/privacy/usage PASS 뒤 같은 명령에서 --probe-only를 제거해 재개합니다. 재개 시 기존 호출을 다시 보내지 않습니다. ledger gap/orphan/unmatched request·hash mismatch는 자동 retry하지 않고 정지합니다. concurrency1, T2 ACCEPTED 즉시 종료, 최대3.
4. ALL_ARM_OUTPUTS_FROZEN 이후 provider phase는 영구 폐쇄합니다. `python scripts/evaluate_exp03b_frozen_outputs_v2.py`가 call/raw/verifier/feedback replay → train2 admission freeze → train3 semantic evaluation freeze → deterministic SCI02B → Formal V4 → train4 one-way guard를 수행합니다. numeric binding은 semantic output을 수정하지 않습니다. T0 단일 결과는 반복표에서 참조만 합니다.
5. 독립 read-only QA로 exact call/output/cost/latency custody, failure denominator, semantic repair, numeric binding, guard 및 immutable 결과를 확인합니다. 공개 안전 보고와 RCC를 동기화한 뒤 DG-04에서 정지합니다. test1/2/held-out/외부공격 접근 및 production Agentic portfolio 생성은 금지합니다.
