# 정상 container schema-only projection 승인 — Stage B 재개

사용자 승인: NORMAL_DATA_CUSTODY_SCHEMA_ONLY_ALLOWLIST_PROJECTION.
재개 기준 task commit: 77f340f6257054007b4e934d70d3a4a9e76803ec.
Stage A/DEC-025/V2A/T0/T2는 그대로이며 integrity replay만 허용합니다.
과거 XVER_NORMAL_CUSTODY_BLOCKER_V1은 삭제하지 않습니다. 이번 승인으로
label-free container 요구만 supersede하며 공식 source/byte identity는 변경하지 않습니다.

공식 normal train 파일의 취득·hash·decompression·header 이름 관찰은 허용합니다.
Row-level scientific decoder는 frozen positive allowlist의 timestamp/feature만 받습니다.
Excluded field는 byte CSV framing만 따라가고 값 buffer/string/number를 만들지 않습니다.
모든 unknown column도 제외합니다. Normal 역할은 공식 train-file identity로 정하며
label 값이 0인지 확인하지 않습니다. 원본 hash와 projection hash는 별개입니다.

12개 synthetic tests: excluded invalid UTF8, numeric/string mutation, quoted delimiter/newline,
downstream invariance, reserved-field rejection, allowlist hash, unknown fields, EOF closure.
실제 데이터 I/O 전에 구현/설정/매핑 hash를 별도 계약으로 동결합니다.

외부 GDN은 이번 재개 범위에서 호환성/계획/합성 QA까지만 수행합니다.
실제 evidence 실행이 필요하면 HAI-XVER-NORMAL-PREP-001을 정확히 준비하고 중단합니다.
Provider/credential/test/attack/label value 접근 및 Stage A 재실행은 금지합니다.

docs/project_state의 오래된 V1 summary는 현재 V2 상태와 다르고 named active task 파일도
현재 checkout에 없습니다. 최신 사용자 재개 지시와 committed V2 authority가 우선합니다.
그 오래된 summary를 새 실행 권한으로 사용하거나 역사적 OUTER를 재시도하지 않습니다.
