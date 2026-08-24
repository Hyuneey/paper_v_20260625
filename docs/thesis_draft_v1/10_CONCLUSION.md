# 9. 결론

본 연구는 다변량 CPS 이상탐지에서 사람이 읽을 수 있는 시간 관계 규칙을
만들기 위해 graph-guided candidate discovery, normal-only relation evidence,
bounded LLM-assisted construction, deterministic numeric authority,
deterministic verifier, LLM-free runtime을 연결했다. HAI 23.05 P1 Boiler에서
144개 후보쌍을 47개 profiling cohort로 통합하고 23개쌍의 42개 방향 관계를
확인해 COMMON-42 규칙 portfolio를 구성했다.

INNER 결과에서 D1 rule layer는 14개 attack event 중 13개를 탐지했고 D0
PCA-SPE가 놓친 3개를 모두 포착했다. 이는 rule evidence가 reference detector와
event-level complementarity를 가진다는 근거다. 그러나 D1의 Normal FAR는
40.50255787059723으로 높았고, D2 V1/V2는 모두 D0 miss를 0/3만 회복했다.
V2의 temporal persistence는 Normal FAR를 6.915070855955625까지 늘렸지만
incremental recall을 만들지 못했다.

따라서 현재 결론은
`RULE_SIGNAL_PRESENT_BUT_CURRENT_FUSION_UTILITY_UNSUPPORTED`다. 규칙의
validity, 실행 가능성, 설명 trace, detector complementarity는 지지되지만,
rule-only deployability와 combined detector improvement는 지지되지 않는다.
event-level 보완성이 단순 point-level gate의 성공을 보장하지 않는다는
negative evidence도 중요한 결과다.

held-out 평가는 test2 bytes와 labels를 읽기 전에 중단돼 과학 결과가 없고,
일반화는 확인되지 않았다. causal root cause, TSFM/ARTIST 효과, human
explanation usefulness도 주장하지 않는다.

논문의 최종 제목·RQ·기여·평가 범위는 네 교수 결정에 달려 있다. 현재
권고는 graph-guided verified rule construction을 중심 기여로 두고 INNER
범위 초안을 먼저 발전시키며, 추가 OUTER나 stronger baseline은 요구될 때
새 연구로 설계하는 것이다.

`PROVISIONAL_PENDING_PROFESSOR_APPROVAL`
