<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=c0e0ce97206de8f04c9cd4ccd865cb3ea586816aea0bf8e6736264658eef9b89 authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
# 내가 해야 할 연구 검토

이 문서는 낮은 수준의 개발 작업이 아니라 연구 책임자가 확인하거나 결정할 항목을 모은다.

## 결정 필요

- **ID:** USER-ARCH011-002
  **우선순위:** 높음 (HIGH)
  **할 일:** 같은 물리 test2의 새 연구 사용 여부 결정
  **사용자 확인이 필요한 이유:** 내용은 봉인됐지만 재사용 권한이 자동으로 생기지는 않는다.
  **연결 문서:** ARCH_011_NEW_HELDOUT_REQUIREMENTS.md
  **상태:** 미결정

- **ID:** USER-ARCH011-005
  **우선순위:** 높음 (HIGH)
  **할 일:** 최종 scientific authority 승인
  **사용자 확인이 필요한 이유:** DEC-020은 확장 D1/D2와 held-out validation의 선행 결정이다.
  **연결 문서:** DEC-020
  **상태:** 미결정

- **ID:** USER-ARCH011-008
  **우선순위:** 높음 (HIGH)
  **할 일:** 첫 remediation task 승인
  **사용자 확인이 필요한 이유:** ARCH-011은 어떤 remediation도 실행하지 않았다.
  **연결 문서:** GAP-FIX-001
  **상태:** 미결정
## 이해 필요

- **ID:** USER-ARCH011-001
  **우선순위:** 높음 (HIGH)
  **할 일:** 기존 OUTER에 과학 결과가 없는 이유 이해
  **사용자 확인이 필요한 이유:** custody blocker는 test2 성능 실패가 아니다.
  **연결 문서:** ARCH_011_OUTER_CUSTODY_AUDIT.md
  **상태:** 미결정

- **ID:** USER-ARCH011-003
  **우선순위:** 높음 (HIGH)
  **할 일:** 5단계 재현성 수준 이해
  **사용자 확인이 필요한 이유:** 근거 추적(traceability)과 새 환경 재현을 구분해야 한다.
  **연결 문서:** ARCH_011_REPRODUCTION_LEVELS.md
  **상태:** 미결정
## 검토 필요

- **ID:** USER-ARCH011-004
  **우선순위:** 높음 (HIGH)
  **할 일:** canonical-to-V4 bridge 권고 검토
  **사용자 확인이 필요한 이유:** lossless mapping이 증명될 때 canonical validity와 V4 runtime 보존의 균형안이다.
  **연결 문서:** ARCH_011_AUTHORITY_OPTIONS.csv
  **상태:** 미결정

- **ID:** USER-ARCH011-007
  **우선순위:** 높음 (HIGH)
  **할 일:** remediation 순서 승인
  **사용자 확인이 필요한 이유:** authority와 custody를 portability rehearsal과 held-out보다 먼저 닫는다.
  **연결 문서:** ARCH_011_FRESH_MACHINE_PROTOCOL.md
  **상태:** 미결정
## Codex 작업 대기

현재 항목이 없습니다.
## 승인된 정책

- **ID:** USER-ARCH011-006
  **우선순위:** 높음 (HIGH)
  **할 일:** PILOT V1 보존·VALIDATION V2 분리 확인
  **사용자 확인이 필요한 이유:** 승인된 정책은 모든 변경을 미래 V2에만 적용한다.
  **연결 문서:** ARCH_011_VALIDATION_V2_VERSIONING.md
  **상태:** 미결정

과학 source authority: `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`
