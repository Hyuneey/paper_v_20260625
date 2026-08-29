# ARCH-002 Candidate Discovery Mismatches

Scientific authority: `origin/research-v6-thesis-checkpoint` @ `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`

현재 RCC의 핵심 설명은 source와 대체로 일치한다. 아래 항목은 frozen 결과를 고치는 문제가 아니라, 구현·정책 문구·역사적 경로 사이의 오독 위험과 미기록 근거를 분리한 것이다.

| ID | 문서/통상 표현 | 실제 구현 증거 | 유형 | 과학적 영향 | 심각도 | 권고 |
|---|---|---|---|---|---|---|
| ARCH002-M01 | GDN의 attention이 관계 후보 근거라는 오해 | 후보 순위는 embedding cosine learned graph와 seed aggregation을 사용하고 attention coefficient는 사용하지 않음 | STATUS_SEMANTIC | GDN 기여를 설명 가능성으로 과장할 수 있음 | MEDIUM | learned graph와 attention을 항상 분리해 설명 |
| ARCH002-M02 | GDN edge가 temporal direction 또는 cause라는 오해 | edge는 target-indexed neighbor/input dependency 후보이며 temporal confirmation은 후속 profiling에서 수행 | STATUS_SEMANTIC | 인과·물리 관계 과장 가능 | MEDIUM | `learned-graph candidate edge` 사용 |
| ARCH002-M03 | candidate/self mask가 GDN Top-5 전에 적용된다는 넓은 설명 | frozen backend는 diagonal을 제거하지 않은 37×37 cosine Top-5를 만든 뒤 144-pair universe로 투영; self identity가 내부 슬롯을 차지할 수 있으나 disjoint role projection이 exported self-pair는 제거 | CODE_EXECUTION | 내부 neighbor budget과 future masking 실험 해석에 영향; 현재 exported 144-pair closure 오류를 뜻하지 않음 | MEDIUM | diagonal removal 및 pre-Top-5 masking과 post-projection을 분리해 검증 |
| ARCH002-M04 | 모든 GDN 경로가 현재 권위라는 인상 | generic `paperworks.gdn.masked` smoke backend와 초기 blocked/failed 경로는 frozen passing GDNP authority가 아님 | LEGACY_CURRENT | 잘못된 model identity 인용 위험 | MEDIUM | passing upstream-aligned GDNP lineage만 current로 표시 |
| ARCH002-M05 | Top-20이 과학적으로 최적화되었다는 인상 | C0에서 test1 이전 공통 budget으로 사전등록됐지만 추가 과학적 rationale는 문서화되지 않음 | DOCUMENTATION | 민감도/선택 편향 해석 제한 | LOW | `RATIONALE_UNDOCUMENTED`; 향후 sensitivity 분석 |
| ARCH002-M06 | 47개 union이 세 arm score의 통합 순위라는 인상 | exact pair set union이며 cross-arm score normalization과 global rank가 없음 | STATUS_SEMANTIC | serialization order를 성능 순위로 오독 가능 | LOW | `unscored union`과 provenance-only를 명시 |
| ARCH002-M07 | STAT이 최종 delayed-response 확인이라는 오해 | STAT은 lagged first-difference association ranking이고 relation confirmation은 별도 후속 단계 | DOC_CODE | association을 confirmed relation으로 과장 가능 | LOW | candidate discovery와 profiling을 분리 |

Summary: `CRITICAL=0`, `HIGH=0`, `MEDIUM=4`, `LOW=3`.
