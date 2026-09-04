# EXP-03B Information Firewall V2

ProviderTrain1EvidencePackV2와 Train2SemanticEvidenceV2는 물리적으로 분리된 immutable 타입입니다. builder는 hidden authority/binder/evaluator를 import하지 않습니다. 기존 split-pure train1 structural 및 predictive authority를 재사용하되 mixed-split object는 만들지 않습니다.

초기 payload: candidate/source/target, 20 structural alternatives, train1 STAT, TRAIN1_ONLY 고정 GDN·purged validation 5-horizon rows. structural evidence의 aggregate 숫자는 허용하지만 raw role values·numeric option tables·NUM alias·최종 EXP02 identity·최종 direction/horizon·META tier/rank·train3/4·test/label·detector/Fusion·경로/credential은 금지합니다.

T2만 train2 semantic issue codes와 1 bounded structural retrieval을 받습니다. 모든 20 대안은 canonical order, best/pass marker 없음. STAT/GDN 추가 retrieval은 이 V2 구현에서 생략하며 기존 structural slice를 유지합니다. T1/T1-B는 feedback을 받지 않습니다. numeric feedback/retrieval schema가 없습니다.

Closed schema·taint 검사·exact request/config replay·candidate binding으로 추가 field/값 identity를 거부합니다. 모든 output 및 train2 admission이 먼저 동결되며 train3 평가도 동결된 뒤에만 SCI02B가 private numeric cache를 읽습니다. 이후 provider phase는 복귀 불가합니다. 이번 준비는 provider/credential/test/attack 접근 0입니다.
