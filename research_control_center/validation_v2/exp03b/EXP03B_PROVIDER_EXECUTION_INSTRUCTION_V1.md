# EXP-03B 승인 후 실행 절차

현재 실행 금지: DG-03B USER_DECISION_REQUIRED. exact implementation commit은 EXP03B_RELEASE_RECEIPT_V1.json에서 재생합니다. preparation commit은 이 receipt를 처음 추가한 Git commit(`git log --diff-filter=A --format=%H -- research_control_center/validation_v2/exp03b/EXP03B_RELEASE_RECEIPT_V1.json`)으로 확정합니다. 자기 commit hash를 파일에 순환 삽입하지 않습니다. source/hash closure는 EXP03B_FINAL_PREPARATION_FREEZE_V2.json입니다.
budget self hash: `9e7e9c5b7d95b7cca7be8c6311c1f7d8b8b4c35268058af188ac289e10229be7`. 모델 `gpt-5.4-mini-2026-03-17`, 최대 609회, input 80373993, output 1247232, 총 81621225, USD 65.90.
1. clean branch/origin, release receipt, 모든 implementation/evidence hash, private vault 복구를 점검합니다. Gate 승인 파일은 사용자의 새 승인을 받은 뒤에만 생성합니다: gate=DG-03B, status=APPROVED, budget_hash 및 execution_freeze_hash를 exact binding하고 self-hash를 부여합니다. 준비 코드가 승인 파일을 자동 생성하지 않습니다.
2. 기존 고정 CUDA/Python 환경을 변경하지 않습니다. PYTHONPATH=src;tests. `python scripts/execute_exp03b_provider.py --approval <private-approved-receipt> --probe-only`를 실행합니다. credential은 이 승인 검증과 reservation 이후 transport 안에서만 읽습니다. public 출력에 경로/key/response를 노출하지 않습니다.
3. ONE_CALL_CAPABILITY_RECEIPT PASS 후 같은 approval로 probe-only 없이 재개합니다. 첫 호출은 재사용합니다. unmatched request, hash mismatch, snapshot 변경, budget/privacy 오류는 자동 재시도하지 않습니다. 한 writer, 동시 호출 1, T2 ACCEPTED 즉시 종료, 최대 3회입니다.
4. 모든 arm output이 atomic/fsync/close/reopen/hash replay 후 ALL_ARM_OUTPUTS_FROZEN으로 잠긴 다음 `python scripts/evaluate_exp03b_frozen_outputs.py`를 실행합니다. train3 hidden reference → train4 one-way guard 순서이며 provider로 돌아가는 경로는 없습니다. T0는 단일 산출물을 반복 표에서 참조합니다.
5. 독립 read-only QA로 call/response/cost ledger, strict denominator, semantic repair, guard, frozen output 무변경을 검사하고 공개 안전 보고/RCC를 동기화합니다. DG-04에서 정지합니다. test1/2/외부 공격/held-out 접근과 production Agentic portfolio 생성은 금지합니다.
