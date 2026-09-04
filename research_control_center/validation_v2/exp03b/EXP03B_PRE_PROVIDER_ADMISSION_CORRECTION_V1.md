# Provider 이전 admission 결속 보강

정상 evidence 계산과 provider 결과 계산은 별도입니다. 원래 pre-I/O SCI binding 및 evidence bytes는 보존합니다.
독립 QA에서 train2 source별 preferred tuple을 계산하지만 target tuple 비교가 빠져 있음을 확인했습니다. 사용자 SCI-01의 source별 exact preferred tuple을 admission에 강제하는 exp03b_admission_verifier.py를 추가했습니다. 임계값·정렬·numeric grid·data/evidence 계산은 바꾸지 않았습니다.
낮은 우선순위의 다른 target direction tuple은 RULE_NOT_JUSTIFIED로 repairable 처리하며 정답은 공개하지 않습니다. 동일 target 내부 horizon stability 검사도 유지합니다.
provider 호출/결과는 아직 0입니다. 최종 실행 계약은 EXP03B_FINAL_PREPARATION_FREEZE_V2.json이며 V1 freeze는 이 보강 전의 역사적 packaging snapshot입니다. 새 과학 실험·rescue 또는 결과 기반 tuning이 아닙니다.
