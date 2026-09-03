"""Public frozen-result presentation only; no scientific runtime imports."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

METHOD_LABELS = {
    "V2_D0_PCA_SPE_NORMAL_ONLY_V1": "D0 PCA-SPE",
    "V2_ISOLATION_FOREST_FIXED_NORMAL_ONLY_V1": "Isolation Forest",
    "V2_VERIFIED_RELATIONAL_RULE_ONLY_V1": "Rule-only V2A",
    "V2_D2_PCA_RULE_CONFIRM2_SAME_SECOND_V1": "PCA+Rule",
    "V2_D2_IF_RULE_CONFIRM2_SAME_SECOND_V1": "IF+Rule",
}


def load_front_results(repo_root: Path, state: Mapping[str, Any]) -> dict[str, Any]:
    """Replay public self-hashes; never open a private artifact or raw dataset."""
    front = dict(state["front_execution"])
    documents = {}
    for name, ref_key, hash_key in (
        ("result", "result_ref", "result_hash"),
        ("trace", "trace_ref", "trace_hash"),
    ):
        ref = front[ref_key]
        if not ref.startswith("research_control_center/validation_v2/gdn_front_exp04_001/results/") or ".." in ref or "\\" in ref:
            raise ValueError("Unsafe front result reference")
        path = repo_root / ref
        if not path.resolve().is_relative_to(repo_root.resolve()):
            raise ValueError("Result reference escapes repository")
        document = json.loads(path.read_text(encoding="utf-8"))
        payload = {key: value for key, value in document.items() if key != "self_hash"}
        actual = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()).hexdigest()
        if actual != document["self_hash"] or actual != front[hash_key]:
            raise ValueError("Frozen public result identity mismatch")
        documents[name] = document
    result, trace = documents["result"], documents["trace"]
    rows = {row["method_id"]: row for row in result["rows"]}
    if len(result["rows"]) != 5 or set(rows) != set(METHOD_LABELS):
        raise ValueError("Required five-method closure mismatch")
    if result["status"] != "DEVELOPMENT_ONLY" or result["post_result_tuning"] is not False:
        raise ValueError("Development/no-tuning boundary mismatch")
    if trace["unit_count"] != front["trace_count"] or trace["annotated_unit_count"] != front["gdn_annotated_count"]:
        raise ValueError("Trace summary mismatch")
    if trace["human_usefulness"] != "UNVALIDATED" or trace["runner_source_commit"] != front["execution_commit"]:
        raise ValueError("Trace claim/source boundary mismatch")
    return {**front, **documents, "rows": [{**rows[key], "display_name": label} for key, label in METHOD_LABELS.items()]}


def front_markdown(front: Mapping[str, Any]) -> str:
    rows = "\n".join(
        f"| {row['display_name']} | {row['recall']['numerator']}/{row['recall']['denominator']} | {row['far_per_hour']['value_decimal']} | {row['normal_false_episodes']} |"
        for row in front["rows"]
    )
    return f"""## VALIDATION V2 개발 결과 · 결과 무결성 QA PASS

모든 5개 prediction freeze와 replay 후에만 test1 label을 해석했습니다.
PILOT V1과 별도 결과이며 최종 과학적 검증은 아닙니다.

| 방법 | Attack-event Recall | Normal FAR/hour | 정상 false episode |
|---|---:|---:|---:|
{rows}

두 고정 fusion은 추가 탐지 0개, 정상 false episode 각각 2개 증가로 탐지 개선이 지지되지 않았습니다.
전체 {front['trace_count']:,}개 actual trace의 자동 구조 충실도 QA는 PASS입니다.
GDN은 LEARNED_GRAPH_SUPPORTING: 2개 pair의 보조 근거이며 {front['gdn_annotated_count']}개 설명에 선택적 문구를 붙였을 뿐 예측에는 영향을 주지 않습니다.
EXP-01·EXP-01B의 기존 음성 결과는 유지합니다. 전체 split에서 GDN 안정성을 입증한 것은 아닙니다.
14 contiguous attack-event units의 통계적 독립성, human usefulness, held-out 일반화는 미확인입니다.
평가 계획은 HAI23 test2 primary held-out와 HAI22/21 external replication으로 확대됐습니다.
146개 nominal scenario는 IID가 아니며 primary pooled Recall을 만들지 않습니다. 실제 P1 denominator는 아직 pending입니다.
다음: DG-03 provider 예산·승인 검토. DG-04 제목, DG-05 attack panel, DG-06 실제 제출은 별도 Gate입니다.
"""
