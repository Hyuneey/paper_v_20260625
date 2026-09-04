# EXP03B-PROVIDER-EXEC-001 — release validation

상태: PASS. 과학 실행·독립 결과 QA 완료; 다음은 DG-04 사용자 결정입니다.

- Integration baseline: `d10c93fbe36be237e5ecfe623c29c67b58e9e30d`
- 승인/실행 source commit: `811d5817bed1484bb3d0c36704bd74f224f4c526`
- Focused tests: 95 PASS.
- Validation V2 tests: 458, PASS, 기존 optional dependency skip 14 유지.
- RCC/UI tests: 203 PASS (새 실행 보고 regression 6개 포함).
- Registry + generated links + privacy: PASS.
- Independent execution/result QA: PASS; 별도 self-hashed QA receipt에 결속.
- Independent publication spot-check: PASS; 과거 feedback0과 현재 EXP03B를 분리했고 T0 우수·T2 abstain 증가 한계를 반영.
- PILOT V1: 3,021/3,021 blobs 보존; 보호 V2 artifacts149와 이전 EXP03B public files63 불변.
- Frozen private input hash bindings364 replay; 실행 private files1,853 hash bundle replay.
- Private vault restore/read smoke PASS; SINGLE_COPY_LOCAL_ONLY, 추가 backup 주장 없음.
- Provider518회는 승인된 실제 과학 호출입니다. 테스트의 mock calls는 여기에 포함되지 않습니다. 첫 과학 호출이 probe였으며 재전송/추가 probe/retry0.
- Test1/test2/held-out/외부공격/공격 labels/GDN retraining/post-result tuning/private exposure0.
- Source/prompt/schema/numeric-policy/metric/disposition 구현 hash는 실행 전후 동일합니다. Report/Registry 표시 수정은 과학 결과를 수정하지 않았습니다.
- Production/held-out Agentic portfolio 생성·교수님 제출 없음.

결과 hash: `a187e89e345e9f1eb42ca993c3d53c6f317a8ff5f33ee9fa7c7e8955baa962c8`.
독립 QA hash: `f6bf6d42a0dc9cd240d4c3e1a3afec811461f92f2ac3c2bda8b8090c6aded447`.

구체적인 수치·해석은 [동결 결과](EXP03B_RESULTS_REPORT_V1.md), 사용자 결정은 [DG-04](DG04_EXP03B_DECISION_BRIEF_V1.md)를 사용합니다. Final integration/push SHA는 이 release 파일을 포함한 Git history로 확인하며 순환 self-reference를 만들지 않습니다.
