# EXP-03 고정 snapshot 메타데이터 접근 사전 점검

DG-03 사용자 승인: `APPROVED_WITH_FIXED_SNAPSHOT`.
검토 범위는 `GET /v1/models/gpt-5.4-mini-2026-03-17` 1회뿐이다.
과학 generation, evidence 전송, 데이터셋 접근은 이 점검에서 금지한다.

독립 읽기 전용 검토자 `front_performance`: `PASS_METADATA_ONLY`.
`xb` 예약 → flush/fsync → close → byte replay가 credential 사용과 HTTP보다 먼저다.
기존 예약이 있으면 재전송하지 않는다. redirect/proxy/자동 retry가 없고,
non-200 오류 본문을 읽지 않는다. 공개 결과에 credential, 경로, 응답 원문을 기록하지 않는다.
200 응답도 exact snapshot ID를 확인하며 generation capability로 과장하지 않는다.

합성 테스트 5개 + 기존 EXP-03 계약 테스트 30개: 35/35 PASS.
Registry/generated privacy: PASS. PILOT V1: 3,021/3,021 PASS.
메타데이터 PASS는 전체 과학 호출 허가가 아니다. 전체 prompt/schema/sampling/ledger와
첫 generation gate는 별도로 동결하고 독립 QA해야 한다.

공식 근거:
- https://developers.openai.com/api/docs/models/gpt-5.4-mini
- https://developers.openai.com/api/reference/resources/models/methods/retrieve

모델 목록 공식 문서에 고정 snapshot이 존재함을 확인했다. 실제 계정 접근은 아직 미확인이다.
