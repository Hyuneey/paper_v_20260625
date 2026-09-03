# 로컬 artifact 보존 범위

초기 PUBLIC_PRIVATE_ARTIFACT_INDEX_V1은 V2A numeric authority 1개와 EXP-01C functional evidence 9개의 복원만 기록한다. 초기 missing_required_artifacts=[]는 이 좁은 범위에 한정하며 전체 scientific dependency가 준비됐다는 뜻이 아니다.

PUBLIC_PRIVATE_ARTIFACT_INDEX_PREFEATURE_V2는 artifact type, 생산 authority, 재현 중요도, byte replay 및 content-addressed private snapshot을 추가한다. 원본 ledger는 덮어쓰지 않는다. final 단계는 완료된 모델·예측·trace·metric namespace를 새 snapshot으로 보존한다. 원본 HAI 파일과 label은 이 도구로 탐색하거나 읽지 않는다.

외부 TASK_PRIVATE_VAULT는 Git 밖에 있으나 동일 로컬 저장장치이다. 따라서 SINGLE_COPY_LOCAL_ONLY이고 독립 백업이나 새 환경 과학 재현 완료가 아니다. 기존 exact file hashes 및 restored bytes는 일치한다. 불필요한 과거 checkpoint 또는 reviewed META private input 부재는 현재 execution의 blocker로 승격하지 않는다.

정상 입력 및 test1 payload는 기존 공식 code materializer/adapter가 각각의 실행 gate에서만 확인한다. test2/heldout은 어떤 단계에서도 열지 않는다. 초기 ledger는 historical snapshot으로 보존하고 현재 범위는 V2 phase receipt를 확인한다.

## 실행 후 최종 보존

PUBLIC_PRIVATE_ARTIFACT_INDEX_FINAL_V2.json은 122개 artifact(초기 복원 10 + 실행 산출물 112)를 기록한다.
필수 task namespace의 exact bytes와 content-addressed snapshot replay PASS.
최종 private snapshot hash: `ece326db668118e3be19d3e188c2043c201ae59fe3e75f4399677773abc438e2`.
이 범위 내 missing required artifact는 0이며 전체 호스트/과거 transcript를 전수 보존했다는 뜻은 아니다.
backup은 여전히 SINGLE_COPY_LOCAL_ONLY이다. independent storage나 fresh-machine scientific 복원 PASS가 아니다.
