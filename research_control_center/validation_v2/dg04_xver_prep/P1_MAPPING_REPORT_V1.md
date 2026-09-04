# P1 외부 버전 매핑 — metadata-only

공식 pinned manual Table 1(PDF 13–14쪽)을 시각 검토하고 Git blob/SHA를 재확인했습니다.
HAI22: 12 source × 12 target, 24개 exact-name metadata 대응.
HAI21: P1_PP04와 P1_TIT03은 표의 21.03 column에 없습니다. 나머지 11×11, 22개 대응입니다.
이는 정상 CSV datatype·sampling 검증 완료나 실행 가능한 candidate authority를 의미하지 않습니다.
정상 헤더 projection 접근 차단으로 실제 schema/sample-rate는 UNRESOLVED입니다.

FT01/02/03(mmH2O)와 FT01Z/02Z/03Z(l/h)를 구별했습니다. suffix 유사성을 alias 근거로 쓰지 않았습니다.
고정 META Top-20 metadata portability: HAI22 20, HAI21 19.
새 META 선언·pair·padding·reranking 없음. STAT를 실행하지 않아 candidate union N은 미정입니다.
GDN의 전체 37-node 입력 schema는 이 24개 역할 매핑과 별개입니다. 특히 P1_PP04D의 공식 대응을
추가 검증해야 하며 24-node 모델로 조용히 대체하지 않습니다.

일부 공개 매뉴얼 scenario 설명이 초기 read-only agent 검색에 포함되었습니다. 공격 CSV/label file은
열지 않았고 eligibility나 scientific decisions에 사용하지 않았습니다. 이후 표 페이지만 제한했습니다.
