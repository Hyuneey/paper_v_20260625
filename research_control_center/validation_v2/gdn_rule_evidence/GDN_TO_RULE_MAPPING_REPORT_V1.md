# GDN 보조 근거와 V2A 규칙의 연결

동결된 EXP-01C의 안정적 양성 pair 2개가 V2A 39-rule portfolio와 모두 pair 및 일부 horizon에서 겹친다. pair-only 0개, 겹침 없음 0개다. Mapping/sidecar JSON이 exact identity와 hash의 기준이다.

- P1_FCV01D → P1_FT02: horizon 1에서 동일 directional reference가 COMBINED 3개 seed 중 2개 이상 양성.
- P1_FCV01Z → P1_FT02: horizons 5/60에서 동일 조건.
- 과거 EXP-01C의 pair 판정은 directional score의 pair별 median을 사용했다. 본 horizon 주석은 동일 directional reference의 양성을 추가 확인한다.
- 두 pair가 모든 split view에서 안정적이라는 뜻은 아니다. 첫 pair의 TRAIN1_ONLY와 둘째 pair의 TRAIN2_ONLY는 각각 양성 0/3이다.
- 기능적 예측 의존성은 target response sign이나 물리 인과성을 증명하지 않는다.

39개 descriptor 전체에 설명 sidecar를 붙이되, runtime / validity / numeric policy / prediction / fusion에는 입력하지 않는다. 주석은 원래 explanation을 수정하지 않는 별도 envelope이며 descriptor, portfolio, direction, horizon 및 sidecar hash를 재검사한다.

문서상 title eligibility는 GDN_ASSISTED_TITLE_STRONG이다. 최종 제목 결정은 DG-04이며 GDN 자체가 primary candidate discovery라는 뜻이 아니다. META+STAT primary authority, reviewed metadata의 한계, 기존 GDN 음성 결과를 유지한다.
