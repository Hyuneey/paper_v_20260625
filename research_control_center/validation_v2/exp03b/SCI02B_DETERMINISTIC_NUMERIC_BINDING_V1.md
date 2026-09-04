# SCI-02B — 의미적 추론 후 결정론적 수치 결속

사용자 승인 EXP03B-PAYLOAD-REDUCE-001. 기존 SCI-02 provider의 37-option 선택은 SUPERSEDED이며 V1 파일·숫자·hash는 보존합니다. provider는 RULE_SET/NO_RULE·source/target direction·horizon·evidence slice만 산출합니다.

모든 arm output의 durable hash closure → train2 admission freeze → train3 semantic evaluation freeze → SCI02B → Formal V4 → train4 guard 순서를 강제합니다. provider phase는 영구 폐쇄하고 binder 이후 새 호출/resume도 거부합니다.

실행 calibrator는 `RELATION_SPECIFIC_NORMAL_ONLY_V1:n7-q0.90-s2-f0.05` 고정입니다. private NUM-033 매핑은 frozen grid의 exact configuration에서 유도되며 provider object에는 존재하지 않습니다. source noise는 file-local median absolute first difference; source direction별 Q90. threshold=max(7×source noise,Q90); tolerance=max(2×source noise,0.05×threshold); target scale은 target noise. 나머지 frozen runtime windows는 유지합니다. train1/train2 각각 도출한 role을 max pooling합니다. 기존 준비에서 생성된 hash-bound split-local numeric cache를 재사용하며 수치나 policy를 재선택하지 않습니다.

provider 출력·admission·train3 의미적 점수는 calibration에 byte/hash 독립입니다. 불완전·nonfinite·잘못된 role/window는 NUMERIC_BINDING_FAIL_CLOSED이며 NO_RULE로 변환하지 않습니다. frozen custody/hash 실패는 전체 정지합니다. 실제 Formal V4 descriptor/numeric validity를 재사용하되 production/held-out 배포 권한은 생성하지 않습니다.

train4는 동일 semantic Rule의 fixed policy와 Common comparator를 평가합니다. SCI03 coverage·최소5 opportunities·lexicographic burden(초/시간,episode/시간,abstain,complexity)·부분 retention·file-local FAIL union을 그대로 유지합니다. 숫자가 같아도 Common의 낮은 complexity가 이기므로 기준을 완화하지 않습니다. train4 이후 provider feedback/retuning은 없습니다.
