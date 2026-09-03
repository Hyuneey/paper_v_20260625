# 후보와 근거의 역할

| 모듈 | 허용된 역할 | 허용되지 않은 해석 |
|---|---|---|
| META | 공식 Process Graph + AI-assisted reviewed semantic metadata에 의한 도메인/의미 후보 사전정보 | 완전 자동 탐색, expert ground truth, 연구자의 최종 Top-20 선택 |
| STAT | 정상 데이터의 통계적 후보 근거 | 인과성 또는 공격 성능 근거 |
| EXP-01C GDN | HAI-adapted learned-graph functional supporting evidence | 핵심 후보 권한, 탐지기, 물리적 진실 |
| Temporal Profiling | 정상 데이터 기반 경험적 관계 채택 | 인과적 관계 증명 |
| EXP-02 | 정상 전용 관계별 수치 권한 | test1에 맞춘 수치 선택 |
| Formal V4 | 고정 규칙의 실행 권한 | Canonical VerifierV1의 직접 실행 결속이 증명됨 |

META의 출처 분류는 HYBRID_REVIEWED_METADATA이다.
Process Graph, reviewed semantic metadata, learned graph는 서로 다른 근거 출처다.
GDN의 COMBINED seed 안정성과 split 간 안정성은 구분하며, 후자는 별도 수치가 지지하는 범위만 기술한다.
