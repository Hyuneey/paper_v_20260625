#!/usr/bin/env python3
"""Registry-driven presentation model and renderer for RCC Dashboard V2.

This module reads only public RCC registries, audit tables, and display-only
configuration.  It never imports scientific code or recomputes scientific
results.
"""

from __future__ import annotations

import csv
import hashlib
import html
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


CONFIG_FILES = (
    "architecture_nodes.csv",
    "architecture_edges.csv",
    "architecture_groups.json",
    "dashboard_layout.json",
    "display_labels_ko.json",
    "visual_tokens.json",
)

EXPECTED_RESULTS = {
    "D0": (11, 14, 0.4939336325682589),
    "D1": (13, 14, 40.50255787059723),
    "D2 V1": (11, 14, 0.7056194750975128),
    "D2 V2": (11, 14, 6.915070855955625),
}
EXPECTED_OVERLAP = {"both": 10, "d0_only": 1, "d1_only": 3, "neither": 0}


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _split(value: str) -> list[str]:
    return [item.strip() for item in value.split(";") if item.strip()]


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_dashboard_config(rcc_root: Path) -> dict[str, Any]:
    directory = rcc_root / "dashboard_config"
    if not directory.is_dir():
        directory = Path(__file__).resolve().parents[1] / "dashboard_config"
    config = {
        "nodes": _read_csv(directory / "architecture_nodes.csv"),
        "edges": _read_csv(directory / "architecture_edges.csv"),
        "groups": _load_json(directory / "architecture_groups.json"),
        "layout": _load_json(directory / "dashboard_layout.json"),
        "labels": _load_json(directory / "display_labels_ko.json"),
        "tokens": _load_json(directory / "visual_tokens.json"),
    }
    digest = hashlib.sha256()
    for name in CONFIG_FILES:
        payload = (directory / name).read_bytes()
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(payload)
    config["digest"] = digest.hexdigest()
    return config


def _component_state(component: Mapping[str, str]) -> dict[str, bool]:
    return {
        "code": bool(component.get("representative_path") and component.get("representative_symbol")),
        "execution": component.get("executed") == "true",
        "evidence": component.get("audited") == "true",
        "reproduction": component.get("reproduced") == "true",
    }


def _node_integrity(node_id: str) -> bool:
    return node_id in {"NODE_D0", "NODE_D1", "NODE_D2", "NODE_METRICS_INTEGRITY"}


def _node_result(node_id: str, state: Mapping[str, Any]) -> str:
    mapping = {
        "NODE_HAI_P1": "HAI 23.05 P1 source provenance 고정",
        "NODE_SPLIT_ROLES": "12 source × 12 target = 144 directed pairs",
        "NODE_CANDIDATE_DISCOVERY": "META·STAT·GDN 각각 Top-20",
        "NODE_CANDIDATE_UNION": "47 unique candidate pairs",
        "NODE_RELATION_PROFILING": "23 pair contexts · 42 confirmed relations",
        "NODE_NUMERIC_AUTHORITY": "420 shared runtime values exact-match; authority identity는 분리",
        "NODE_RULE_CONSTRUCTION": "T0/T1/T1-B 42/42 · T2 39/42 · feedback action 0",
        "NODE_VERIFIER": "Canonical VerifierV1 20단계; V4 frozen D1 직접 authority는 아님",
        "NODE_COMMON42": "42 CanonicalRuleDescriptorV4",
        "NODE_D0": f"11/14 · FAR {state['d0_detector']['normal_far_episodes_per_hour']}",
        "NODE_D1": f"13/14 · FAR {state['d1_evaluation']['normal_far_episodes_per_hour']}",
        "NODE_D2": "V1/V2 모두 11/14 · D0 miss recovery 0/3",
        "NODE_METRICS_INTEGRITY": "공통 Recall/FAR contract · 결과 무결성 점검 완료",
        "NODE_OUTER_REPRO": "기존 OUTER 결과 없음 · held-out 일반화 미확인",
    }
    return mapping.get(node_id, "미확인 (UNKNOWN)")


def _node_unvalidated(node_id: str) -> str:
    mapping = {
        "NODE_CANDIDATE_DISCOVERY": "GDN 고유 기여와 seed/split 안정성",
        "NODE_RELATION_PROFILING": "인과성·최적 horizon·held-out 일반화",
        "NODE_NUMERIC_AUTHORITY": "수치 기준의 과학적 최적성",
        "NODE_RULE_CONSTRUCTION": "Agentic feedback 이점",
        "NODE_VERIFIER": "과학적 진실·탐지 유용성; canonical→V4 equivalence",
        "NODE_D0": "SOTA 우수성·fresh-machine 재현",
        "NODE_D1": "운영 유용성·held-out 일반화",
        "NODE_D2": "fusion 개선과 일반 complementarity",
        "NODE_METRICS_INTEGRITY": "통계적 독립성·일반화·우수성",
        "NODE_OUTER_REPRO": "held-out 결과·새 환경 과학 재현",
    }
    return mapping.get(node_id, "독립 재현과 과학적 검증")


def _derive_pilot_results(state: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = [
        {
            "method": "D0",
            "detected": int(str(state["d0_detector"]["attack_event_response"]).split("/")[0]),
            "total": int(str(state["d0_detector"]["attack_event_response"]).split("/")[1]),
            "far": state["d0_detector"]["normal_far_episodes_per_hour"],
            "status": "PILOT_ONLY",
        },
        {
            "method": "D1",
            "detected": state["d1_evaluation"]["attack_events_detected"],
            "total": state["d1_evaluation"]["pilot_events"],
            "far": state["d1_evaluation"]["normal_far_episodes_per_hour"],
            "status": "PILOT_ONLY",
        },
        {
            "method": "D2 V1",
            "detected": int(str(state["d2_fusion"]["v1"]["attack_event_response"]).split("/")[0]),
            "total": 14,
            "far": state["d2_fusion"]["v1"]["normal_far_episodes_per_hour"],
            "status": "PILOT_ONLY",
        },
        {
            "method": "D2 V2",
            "detected": int(str(state["d2_fusion"]["v2"]["attack_event_response"]).split("/")[0]),
            "total": 14,
            "far": state["d2_fusion"]["v2"]["normal_far_episodes_per_hour"],
            "status": "TEST1_INFORMED_DEVELOPMENT",
        },
    ]
    for row in rows:
        expected = EXPECTED_RESULTS[row["method"]]
        actual = (row["detected"], row["total"], row["far"])
        if actual != expected:
            raise ValueError(f"Frozen pilot result mismatch for {row['method']}: {actual!r}")
    return rows


def _read_gap_tables(rcc_root: Path) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    directory = rcc_root / "architecture" / "gap_000_pre_validation"
    if not directory.is_dir():
        directory = Path(__file__).resolve().parents[1] / "architecture" / "gap_000_pre_validation"
    return (
        _read_csv(directory / "GAP_000_ROOT_ISSUES.csv"),
        _read_csv(directory / "GAP_000_REMEDIATION_MATRIX.csv"),
        _read_csv(directory / "GAP_000_EXPERIMENT_GATES.csv"),
    )


def _read_evaluation_panels(rcc_root: Path) -> list[dict[str, str]]:
    """Load the public planning registry; it contains no attack payload or labels."""
    path = rcc_root / "validation_v2" / "evaluation_expansion" / "PANEL_REGISTRY_V1.csv"
    if not path.is_file():
        return []
    return _read_csv(path)


def build_dashboard_view_model(
    data: Mapping[str, Any], digest: str, rcc_root: Path
) -> dict[str, Any]:
    config = load_dashboard_config(rcc_root)
    components = {row["component_id"]: dict(row) for row in data["components"]}
    artifacts = {row["artifact_id"]: dict(row) for row in data["artifacts"]}
    root_issues, remediation, gates = _read_gap_tables(rcc_root)
    evaluation_panels = _read_evaluation_panels(rcc_root)
    remediations = {row["gap_id"]: row for row in remediation}

    nodes: list[dict[str, Any]] = []
    valid_node_ids: set[str] = set()
    covered_components: set[str] = set()
    for row in config["nodes"]:
        node_id = row["node_id"]
        if node_id in valid_node_ids:
            raise ValueError(f"Duplicate architecture node: {node_id}")
        valid_node_ids.add(node_id)
        component_ids = _split(row["component_ids"])
        missing = sorted(set(component_ids) - set(components))
        if missing:
            raise ValueError(f"Unknown component references for {node_id}: {missing}")
        covered_components.update(component_ids)
        entries = [components[item] for item in component_ids]
        status_rows = [_component_state(item) for item in entries]
        node = dict(row)
        node.update(
            {
                "component_ids": component_ids,
                "audit_reports": _split(row["audit_reports"]),
                "status": {
                    "code": all(item["code"] for item in status_rows),
                    "execution": all(item["execution"] for item in status_rows),
                    "evidence": all(item["evidence"] for item in status_rows),
                    "integrity": _node_integrity(node_id),
                    "reproduction": all(item["reproduction"] for item in status_rows),
                    "scientific": False,
                },
                "current_result": _node_result(node_id, data["state"]),
                "unvalidated": _node_unvalidated(node_id),
                "next_work": entries[0].get("next_action", "미확인 (UNKNOWN)"),
                "technical": {
                    "paths": sorted({item["representative_path"] for item in entries if item["representative_path"]}),
                    "symbols": sorted({item["representative_symbol"] for item in entries if item["representative_symbol"]}),
                    "artifacts": sorted({value for item in entries for value in _split(item.get("artifact_refs", ""))}),
                    "tests": sorted({value for item in entries for value in _split(item.get("test_refs", ""))}),
                    "source_ref": entries[0].get("scientific_source_ref", "UNKNOWN"),
                    "source_commit": entries[0].get("scientific_source_commit", "UNKNOWN"),
                },
            }
        )
        nodes.append(node)

    edges: list[dict[str, Any]] = []
    for row in config["edges"]:
        if row["source_node_id"] not in valid_node_ids or row["target_node_id"] not in valid_node_ids:
            raise ValueError(f"Invalid architecture edge endpoints: {row['edge_id']}")
        artifact_ids = _split(row["artifact_ids"])
        missing_artifacts = sorted(set(artifact_ids) - set(artifacts))
        if missing_artifacts:
            raise ValueError(f"Unknown edge artifacts for {row['edge_id']}: {missing_artifacts}")
        edge = dict(row)
        edge["artifact_ids"] = artifact_ids
        edge["audit_reports"] = _split(row["audit_reports"])
        edges.append(edge)

    groups = config["groups"]
    catalog_only = set(groups.get("catalog_only_component_ids", []))
    if covered_components | catalog_only != set(components):
        missing = sorted(set(components) - covered_components - catalog_only)
        extra = sorted(covered_components | catalog_only - set(components))
        raise ValueError(f"Component coverage mismatch: missing={missing}, extra={extra}")

    state = data["state"]
    experiment_by_id = {row["experiment_id"]: dict(row) for row in data["experiments"]}
    gate_by_id = {row["experiment_id"]: row for row in gates}
    current_gate_status = state["pre_validation_readiness"]["experiment_gates"]
    experiments: list[dict[str, Any]] = []
    for experiment_id in ["EXP-01", "EXP-01B", "EXP-02", "EXP-03", "EXP-04", "EXP-05", "EXP-06"]:
        experiment = experiment_by_id[experiment_id]
        gate = dict(gate_by_id.get(experiment_id, {}))
        if not gate:
            gate = {
                "experiment_id": experiment_id,
                "must_fix_before_start": "별도 사전등록과 정상 전용 실행을 완료함",
                "must_freeze_before_results": "완료된 public lineage와 disposition 유지",
                "design_requirements": "새 실험 identity와 동일 예산 비교",
                "does_not_block": "V2A META+STAT 경로",
                "reason": "EXP-01B는 GAP-000 이후 별도로 사전등록된 정상 전용 실험이다.",
            }
        if current_gate_status[experiment_id] == "COMPLETE":
            gate["must_fix_before_start"] = "해당 실행 완료; 동결 결과 유지"
        gate["ready_now"] = current_gate_status[experiment_id]
        experiment["gate"] = gate
        experiments.append(experiment)

    overlap = dict(data["state"]["metric_integrity"]["overlap"])
    if overlap != EXPECTED_OVERLAP:
        raise ValueError(f"Frozen overlap mismatch: {overlap!r}")

    node_lane: dict[str, str] = {node["node_id"]: node["lane_id"] for node in nodes}
    component_lane: dict[str, str] = {}
    for node in nodes:
        for component_id in node["component_ids"]:
            component_lane[component_id] = node["lane_id"]
    for component_id in catalog_only:
        component_lane[component_id] = "LANE_GOVERNANCE_CATALOG"

    risks_by_component: dict[str, list[str]] = {}
    for risk in data["risks"]:
        risks_by_component.setdefault(risk["affected_component"], []).append(risk["risk_id"])
    experiment_links: dict[str, list[str]] = {}
    for experiment in data["experiments"]:
        for component_id in _split(experiment["linked_component_ids"]):
            experiment_links.setdefault(component_id, []).append(experiment["experiment_id"])

    catalog = []
    for component in data["components"]:
        item = dict(component)
        state = _component_state(component)
        item.update(
            {
                "lane_id": component_lane.get(component["component_id"], "LANE_GOVERNANCE_CATALOG"),
                "experiments": experiment_links.get(component["component_id"], []),
                "risks": risks_by_component.get(component["component_id"], []),
                "state": {
                    **state,
                    "integrity": component["component_id"] in {"D0_PCA_SPE", "D1_RULE_ONLY", "D2_V1", "D2_V2", "RESULT_INTEGRITY"},
                    "scientific": False,
                },
            }
        )
        catalog.append(item)

    current_gap_status = data["state"]["pre_validation_readiness"].get("current_gap_status", {})

    def current_gap_row(row: Mapping[str, str]) -> dict[str, str]:
        merged = {**row, **remediations.get(row["gap_id"], {})}
        merged["historical_status"] = merged.get("status", "UNKNOWN")
        current = current_gap_status.get(row["gap_id"])
        if current:
            merged["status"] = current["status"]
            merged["current_resolution"] = current["summary"]
        return merged

    p0 = [
        current_gap_row(row)
        for row in root_issues
        if remediations.get(row["gap_id"], {}).get("priority") == "P0"
    ]
    current_events = sorted(
        (dict(row) for row in data["timeline"] if row["date_precision"] == "DAY"),
        key=lambda row: (row["date"], row["event_id"]),
        reverse=True,
    )
    unresolved = [dict(row) for row in data["decisions"] if row["status"] == "OPEN"]
    if data['state'].get('exp03b_execution'):
        unresolved.append({'decision_id':'DG-04','title':'EXP-03B 이후 최종 기여 결정','status':'OPEN','reason':'정상 semantic induction 실행 결과와 한계 검토','decision':'USER_DECISION_REQUIRED'})
    elif data['state'].get('exp03b_preparation'):
        p=data['state']['exp03b_preparation']
        unresolved.append({'decision_id':p['next_gate'],'title':'EXP-03B 의미적 추론 provider 별도 승인','status':'OPEN','reason':f"최대{p['maximum_calls']}회·USD{p['cost_ceiling_usd']};현재 provider0",'decision':'USER_DECISION_REQUIRED'})
    state = data["state"]
    vm = {
        "schema_version": "rcc_dashboard_v2_view_model_v1",
        "registry_version": state["registry_version"],
        "registry_digest": digest,
        "config_digest": config["digest"],
        "scientific_authority": state["scientific_authority"],
        "last_updated": state["last_updated"],
        "current_phase": state["current_phase"],
        "phase_statement": state["current_phase_statement"],
        "exact_next_task": state["exact_next_task"],
        "pilot_v1": state["outer_reproducibility"]["pilot_v1"],
        "validation_v2": state["outer_reproducibility"]["validation_v2"],
        "readiness": state["pre_validation_readiness"],
        "navigation": config["layout"]["primary_navigation"],
        "nodes": nodes,
        "edges": edges,
        "groups": groups,
        "lanes": groups["lanes"],
        "catalog": catalog,
        "pilot_results": _derive_pilot_results(state),
        "overlap": overlap,
        "candidate_path": {"universe": 144, "META": 20, "STAT": 20, "GDN": 20, "union": 47, "confirmed": 42},
        "front_results": data["front_results"],
        "v2_normal_only": state["validation_v2a_normal_only"],
        "exp01b": {
            "status": state["candidate_discovery"]["exp01b_status"],
            "equal_budget": state["candidate_discovery"]["exp01b_equal_budget"],
            "limitation": state["candidate_discovery"]["exp01b_limitation"],
        },
        "meta_lineage": dict(state["candidate_discovery"]["meta_lineage"]),
        "construction": {"T0": "42/42", "T1": "42/42", "T1-B": "42/42", "T2": "39/42", "feedback_actions": 0},
        "runtime_status_tokens": ["PASS", "FAIL", "ABSTAIN"],
        "experiments": experiments,
        "evaluation_panels": evaluation_panels,
        "exp03_execution": state.get("exp03_execution", {}),
        "exp03b_preparation": state.get("exp03b_preparation", {}),
        "exp03b_execution": state.get("exp03b_execution", {}),
        "p0": p0,
        "root_issues": [current_gap_row(row) for row in root_issues],
        "risks": [dict(row) for row in data["risks"]],
        "claims": [dict(row) for row in data["claims"]],
        "dg04_method_lock": state.get("dg04_method_lock"),
        "xver_preparation": state.get("xver_preparation"),
        "decisions": [dict(row) for row in data["decisions"]],
        "unresolved_decisions": unresolved,
        "recent_events": current_events[:3],
        "history_events": current_events[:12],
        "labels": config["labels"],
        "safety": {
            "scientific_executions": state["safety_counters"]["scientific_executions"],
            "test2_accesses": state["safety_counters"]["test2_feature_accesses"] + state["safety_counters"]["test2_label_accesses"],
            "private_exposures": state["safety_counters"]["new_private_exposures"],
        },
    }
    return vm


NODE_POSITIONS = {
    "NODE_HAI_P1": (70, 76),
    "NODE_SPLIT_ROLES": (340, 76),
    "NODE_CANDIDATE_DISCOVERY": (610, 76),
    "NODE_CANDIDATE_UNION": (880, 76),
    "NODE_RELATION_PROFILING": (70, 258),
    "NODE_NUMERIC_AUTHORITY": (295, 258),
    "NODE_RULE_CONSTRUCTION": (520, 258),
    "NODE_VERIFIER": (745, 258),
    "NODE_COMMON42": (970, 258),
    "NODE_D0": (210, 440),
    "NODE_D1": (520, 440),
    "NODE_D2": (830, 440),
    "NODE_METRICS_INTEGRITY": (445, 622),
    "NODE_OUTER_REPRO": (790, 622),
}


def _status_rail(status: Mapping[str, bool]) -> str:
    labels = (
        ("code", "코드"),
        ("execution", "실행"),
        ("evidence", "근거"),
        ("integrity", "무결성"),
        ("reproduction", "재현"),
        ("scientific", "과학 검증"),
    )
    return "".join(
        f'<span class="node-state {"is-on" if status[key] else "is-off"}" '
        f'aria-label="{label}: {"완료" if status[key] else "미완료 또는 미확인"}"><i></i>{label}</span>'
        for key, label in labels
    )


def _edge_path(source: tuple[int, int], target: tuple[int, int]) -> str:
    sx, sy = source
    tx, ty = target
    sx += 92
    sy += 33
    tx += 92
    ty += 33
    if abs(ty - sy) < 80:
        return f"M {sx} {sy} L {tx} {ty}"
    bend = (sy + ty) / 2
    return f"M {sx} {sy} C {sx} {bend}, {tx} {bend}, {tx} {ty}"


def _render_architecture_svg(vm: Mapping[str, Any], *, compact: bool = False) -> str:
    id_prefix = "overview-" if compact else "map-"
    arrow_frozen = f"{id_prefix}arrow-frozen"
    arrow_gap = f"{id_prefix}arrow-gap"
    node_map = {node["node_id"]: node for node in vm["nodes"]}
    edge_markup = []
    for edge in vm["edges"]:
        edge_markup.append(
            f'<path id="{id_prefix}{_esc(edge["edge_id"])}" class="arch-edge edge-{_esc(edge["edge_class"].lower())}" '
            f'data-source="{_esc(edge["source_node_id"])}" data-target="{_esc(edge["target_node_id"])}" '
            f'data-edge-class="{_esc(edge["edge_class"])}" style="marker-end:url(#{arrow_gap if edge["edge_class"] == "AUTHORITY_GAP" else arrow_frozen})" '
            f'd="{_edge_path(NODE_POSITIONS[edge["source_node_id"]], NODE_POSITIONS[edge["target_node_id"]])}">'
            f'<title>{_esc(edge["label_ko"])} · {_esc(edge["notes_ko"])}</title></path>'
        )
    node_markup = []
    for node_id, (x, y) in NODE_POSITIONS.items():
        node = node_map[node_id]
        rail = "" if compact else _status_rail(node["status"])
        node_markup.append(
            f'<g id="{id_prefix}svg-{_esc(node_id)}" class="arch-node" role="button" tabindex="0" '
            f'data-node-id="{_esc(node_id)}" data-lane="{_esc(node["lane_id"])}" '
            f'aria-label="{_esc(node["label_ko"])} 상세 열기" transform="translate({x} {y})">'
            '<rect width="184" height="66" rx="10"></rect>'
            f'<text class="node-title" x="14" y="24">{_esc(node["label_ko"])}</text>'
            f'<text class="node-subtitle" x="14" y="44">{_esc(node["subtitle_ko"])}</text>'
            f'<title>{_esc(node["label_ko"])} — {_esc(node["current_result"])}</title>'
            '</g>'
        )
        if not compact:
            node_markup.append(
                f'<foreignObject class="node-rail-object" x="{x}" y="{y + 68}" width="184" height="42">'
                f'<div xmlns="http://www.w3.org/1999/xhtml" class="node-rail">{rail}</div></foreignObject>'
            )
    lane_labels = "" if compact else "".join(
        f'<text class="lane-label" x="22" y="{index * 182 + 42}">{_esc(lane["label_ko"])}</text>'
        for index, lane in enumerate(vm["lanes"])
    )
    return (
        f'<svg class="architecture-svg {"is-compact" if compact else ""}" '
        'viewBox="0 0 1180 760" role="img" aria-label="연구 아키텍처 지도">'
        f'<defs><marker id="{arrow_frozen}" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z"></path></marker>'
        f'<marker id="{arrow_gap}" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z"></path></marker></defs>'
        f'{lane_labels}<g class="edge-layer">{"".join(edge_markup)}</g><g class="node-layer">{"".join(node_markup)}</g></svg>'
    )


def _render_result_bars(vm: Mapping[str, Any], *, overview: bool = False) -> str:
    rows = []
    for item in vm["pilot_results"]:
        percent = item["detected"] / item["total"] * 100
        rows.append(
            f'<div class="metric-row"><span>{_esc(item["method"])}</span>'
            f'<div class="metric-track" role="img" aria-label="{_esc(item["method"])} {item["detected"]}/{item["total"]}">'
            f'<i style="--metric-value:{percent:.4f}%"></i></div>'
            f'<strong>{item["detected"]}/{item["total"]}</strong></div>'
        )
    classes = "pilot-bars compact" if overview else "pilot-bars"
    return f'<div class="{classes}">{"".join(rows)}</div>'


def _render_far_panels(vm: Mapping[str, Any]) -> str:
    low = [row for row in vm["pilot_results"] if row["method"] != "D1"]
    d1 = next(row for row in vm["pilot_results"] if row["method"] == "D1")
    low_max = 7.0
    low_rows = "".join(
        f'<div class="far-row"><span>{_esc(row["method"])}</span><div class="far-track"><i style="--metric-value:{min(row["far"] / low_max * 100, 100):.4f}%"></i></div><strong>{row["far"]}</strong></div>'
        for row in low
    )
    return (
        '<div class="far-panels" aria-label="Normal FAR/hour 비교. 패널 축이 서로 다름">'
        f'<section><h4>낮은 범위 · 0–7</h4>{low_rows}</section>'
        f'<section class="far-high"><h4>D1 별도 범위 · 0–45</h4><div class="far-row"><span>D1</span><div class="far-track"><i style="--metric-value:{d1["far"] / 45 * 100:.4f}%"></i></div><strong>{d1["far"]}</strong></div></section>'
        '</div><p class="chart-note">두 패널은 축이 다릅니다. 막대 길이만 교차 비교하지 말고 exact value를 확인하세요.</p>'
    )


def _render_results_table(vm: Mapping[str, Any]) -> str:
    rows = "".join(
        f'<tr><th scope="row">{_esc(item["method"])}</th><td>{item["detected"]}/{item["total"]}</td><td>{item["far"]}</td><td>{_esc(item["status"])}</td></tr>'
        for item in vm["pilot_results"]
    )
    return (
        '<div class="table-wrap accessible-data"><table><caption>Pilot V1 exact values</caption>'
        '<thead><tr><th>방법</th><th>Attack-event Recall</th><th>Normal FAR/hour</th><th>범위</th></tr></thead>'
        f'<tbody>{rows}</tbody></table></div>'
    )


def _render_front_results(vm: Mapping[str, Any], *, compact: bool = False) -> str:
    front = vm["front_results"]
    rows = "".join(
        f'<tr><th scope="row">{_esc(row["display_name"])}</th>'
        f'<td>{row["recall"]["numerator"]}/{row["recall"]["denominator"]}</td>'
        f'<td title="{_esc(row["far_per_hour"]["value_decimal"])}">{_esc(row["far_per_hour"]["value_decimal"][:8] if compact else row["far_per_hour"]["value_decimal"])}</td>'
        f'<td>{row["normal_false_episodes"]}</td></tr>'
        for row in front["rows"]
    )
    return f'''<section class="panel roadmap v2-development-results" aria-label="VALIDATION V2 개발 결과">
      <div class="panel-heading"><div><p class="kicker">VALIDATION V2 · DEVELOPMENT_ONLY</p><h3>개발 결과 · 최종 검증 아님</h3></div>
      <a class="text-button" href="../validation_v2/gdn_front_exp04_001/reports/EXP04_DEVELOPMENT_REPORT_V1.md">결과와 한계</a></div>
      <div class="table-wrap"><table><caption>5개 방법 · 14개 연속 공격 구간 단위 · 결과 무결성 QA PASS</caption><thead><tr><th>방법</th><th>Recall</th><th>FAR/hour</th><th>정상 false episode</th></tr></thead><tbody>{rows}</tbody></table></div>
      <p>두 fusion: 추가 탐지 0개 · 정상 false episode 각각 2개 증가. Rule-only의 높은 FAR는 해결되지 않았습니다.</p>
      <p>EXP-05: {front['trace_count']:,}개 actual trace 전체 구조 점검 PASS. EXP-01C GDN은 <code>LEARNED_GRAPH_SUPPORTING</code>이며 2개 pair를 통해 {front['gdn_annotated_count']}개 설명에만 보조 문구를 추가했습니다. 예측·Rule 권한은 변경하지 않았습니다.</p>
      <p class="chart-note">통계적 독립성·사람에게 주는 유용성·held-out 일반화는 미확인. GDN의 이전 EXP-01·EXP-01B 음성 결과는 그대로 보존합니다.</p></section>'''


def _render_overview(vm: Mapping[str, Any]) -> str:
    p0_count = len(vm["readiness"]["p0_global_fixes"]) + len(vm["readiness"]["p0_design_gates"])
    open_count = len(vm["unresolved_decisions"])
    actions = [
        ("DG-03", "EXP-03 provider 예산·승인 검토", "natural cohort와 정확한 model/call/token 상한 확정 후 별도 승인"),
        ("DG-04", "기여·제목 표현 결정", "GDN은 설명용 보조 근거; Agentic 효용은 아직 미검증"),
        ("DG-06", "교수님 개발 결과 package 검토", "음성 결과를 포함한 보고서 확인; 실제 제출은 별도 승인"),
    ]
    if vm.get("exp03_execution"):
        actions = [
            ("DG-04", "최종 제목·Agentic 기여 결정", "EXP-03 실행·QA 완료; 자연 feedback 발생 0으로 이점은 관찰되지 않음"),
            ("DG-05", "다중 HAI 공격 접근 별도 승인", "버전별 P1 호환성·시나리오·custody 준비 전 공격 데이터 접근 금지"),
            ("DG-06", "교수님 package 제출 검토", "초안 작성 완료와 실제 제출을 구분; 자동 발송 금지"),
        ]
    if vm.get('exp03b_execution'):
        e=vm['exp03b_execution']
        actions=[('DG-04','최종 제목·Agentic 기여 결정',e['disposition']),('DG-05','공격 접근 별도 승인','현재 test1 재개봉·test2·외부공격 접근 금지'),('DG-06','교수님 제출 검토','초안만 갱신; 실제 제출하지 않음')]
    elif vm.get('exp03b_preparation'):
        p=vm['exp03b_preparation']
        actions=[(p['next_gate'],'EXP-03B 의미적 추론 provider 승인',f"{p['cohort_count']} pair;numeric provider0;최대{p['maximum_calls']}회·USD{p['cost_ceiling_usd']};현재 호출0"),('DG-04','EXP-03B 이후 기여 결정','DEFERRED_UNTIL_EXP03B; V1은 constrained materialization 결과로 보존'),('DG-05/06','공격 접근·교수님 제출 별도 승인','현재 test/held-out 접근 및 제출 금지')]
    if vm.get('dg04_method_lock'):
        actions=[('CUSTODY','외부 정상 schema 접근 범위 확인','label 열은 schema로만 식별하고 값은 배제하는 projection; 현재 자동심사 차단'),
                 ('DG-03C','외부 T2 provider 예산 준비','N·evidence·예산 미동결, provider 승인 가능한 단계 아님'),
                 ('DG-05/06','공격 접근·교수님 제출 별도 승인','공격 접근 0; 교수님 package는 미제출')]
    action_markup = "".join(
        f'<li><span>{_esc(gap)}</span><strong>{_esc(title)}</strong><small>{_esc(body)}</small></li>'
        for gap, title, body in actions
    )
    gate_markup = "".join(
        f'<li><span>{_esc(exp["experiment_id"])}</span><strong>{_esc(exp["name"])}</strong>'
        f'<em class="gate gate-{_esc(exp["gate"]["ready_now"].lower())}">{_esc(vm["labels"].get(exp["gate"]["ready_now"], exp["gate"]["ready_now"]))}</em></li>'
        for exp in vm["experiments"][:5]
    )
    top_risks = [risk for risk in vm["risks"] if risk["severity"] in {"CRITICAL", "HIGH"} and risk["status"] in {"OPEN", "MITIGATING"}][:5]
    risk_markup = "".join(
        f'<li><span class="risk-level">{_esc(risk["severity"])}</span><strong>{_esc(risk["risk_id"])}</strong><small>{_esc(risk["description"])}</small></li>'
        for risk in top_risks
    )
    recent_markup = "".join(
        f'<li><time>{_esc(event["date"])}</time><strong>{_esc(event["title"])}</strong></li>'
        for event in vm["recent_events"]
    )
    return f'''
    <section class="view-panel is-active" id="view-overview" data-view-panel="overview" aria-labelledby="nav-overview">
      <p class="status-separation">구현 완료, 실행 완료, 결과 무결성 확인, 과학적 검증, 재현성, 일반화는 서로 다른 상태입니다.</p>
      <div class="overview-header panel">
        <div><p class="kicker">현재 연구 단계</p><h2>V2 개발 평가 완료 · 결과 무결성 확인</h2><p>PILOT V1은 그대로 보존됩니다. VALIDATION V2에서는 EXP-01·EXP-01B·EXP-02를 정상 데이터로 완료했고, META+STAT 기반 39-rule Formal V4 portfolio를 test1 접근 전에 고정했습니다. 다섯 방법의 예측 동결 뒤 평가했고, 두 fusion의 추가 탐지는 없었습니다.</p>
        <div class="version-pills"><span>PILOT V1 · 보존</span><span>VALIDATION V2 · 개발 결과 QA PASS</span></div></div>
        <div class="next-task-callout"><span>정확한 다음 작업</span><strong>{_esc(vm["exact_next_task"])}</strong></div>
        <dl class="stage-facts"><div><dt>P0 문제</dt><dd>{p0_count}</dd></div><div><dt>미결정</dt><dd>{open_count}</dd></div><div><dt>갱신</dt><dd>{_esc(vm["last_updated"])}</dd></div><div><dt>과학 기준</dt><dd title="{_esc(vm["scientific_authority"]["commit"])}">{_esc(vm["scientific_authority"]["commit"][:10])}</dd></div></dl>
      </div>
      <ol class="research-rail panel" aria-label="연구 진행 단계"><li class="done">연구 방향</li><li class="done">아키텍처</li><li class="done">Pilot V1</li><li class="done">전체 감사</li><li class="done">공유 기반</li><li class="done">Fresh-machine synthetic</li><li class="done">V2 개발 평가</li><li>Held-out</li></ol>
      {_render_dg04(vm)}{_render_front_results(vm, compact=True)}
      <div class="overview-grid">
        <article class="panel overview-map"><div class="panel-heading"><div><p class="kicker">전체 지도</p><h3>근거에서 평가까지</h3></div><button class="text-button" data-go-view="architecture">크게 보기</button></div>{_render_architecture_svg(vm, compact=True)}</article>
        <aside class="panel action-panel"><div class="panel-heading"><div><p class="kicker">지금 할 일</p><h3>확대 검증 전 우선순위</h3></div></div><ol>{action_markup}</ol></aside>
        <article class="panel pilot-overview"><div class="panel-heading"><div><p class="kicker">Pilot 결과</p><h3>공격 반응과 정상 오경보를 분리해 보기</h3></div><button class="text-button" data-go-view="experiments">상세 결과</button></div>{_render_result_bars(vm, overview=True)}<div class="far-glance"><span>D0 <b>0.4939</b></span><span>D1 <b>40.5026</b></span><span>D2 V1 <b>0.7056</b></span><span>D2 V2 <b>6.9151</b></span></div><p class="pilot-warning">현재 결과는 test1의 14개 연속 공격 구간 단위를 이용한 예비 결과입니다. 통계적 독립성과 held-out 일반화는 확인되지 않았습니다.</p></article>
        <article class="panel compact-stack"><div class="compact-tabs" role="tablist"><button class="is-active" data-compact-tab="gates">실험 Gate</button><button data-compact-tab="risks">주요 위험</button><button data-compact-tab="recent">최근 변경</button></div><div data-compact-panel="gates"><ul class="compact-list">{gate_markup}</ul></div><div data-compact-panel="risks" hidden><ul class="compact-list">{risk_markup}</ul></div><div data-compact-panel="recent" hidden><ul class="compact-list timeline-mini">{recent_markup}</ul></div></article>
      </div>
    </section>'''


def _render_architecture_view(vm: Mapping[str, Any]) -> str:
    lane_options = "".join(f'<option value="{_esc(lane["lane_id"])}">{_esc(lane["label_ko"])}</option>' for lane in vm["lanes"])
    catalog_rows = "".join(
        f'<tr class="catalog-row" tabindex="0" data-component-id="{_esc(row["component_id"])}" data-lane="{_esc(row["lane_id"])}" data-risk="{_esc(row["risk_level"])}" data-search="{_esc((row["component_id"]+" "+row["name"]+" "+row["research_role"]).lower())}">'
        f'<th scope="row"><code>{_esc(row["component_id"])}</code><strong>{_esc(row["name"])}</strong></th><td>{_esc(row["research_role"])}</td><td>{_esc(row["input_summary"])}</td><td>{_esc(row["output_summary"])}</td>'
        f'<td>{"●" if row["state"]["code"] else "○"}</td><td>{"●" if row["state"]["execution"] else "○"}</td><td>{"●" if row["state"]["evidence"] else "○"}</td><td>{"●" if row["state"]["integrity"] else "○"}</td><td>{"●" if row["state"]["reproduction"] else "○"}</td><td>○</td><td>{_esc(row["risk_level"])}</td></tr>'
        for row in vm["catalog"]
    )
    return f'''
    <section class="view-panel" id="view-architecture" data-view-panel="architecture" aria-labelledby="nav-architecture" hidden>
      <header class="view-heading"><div><p class="kicker">Architecture Explorer</p><h2>전체 연구 시스템 지도</h2><p>node를 선택하면 Input → Process → Output과 실제 코드·artifact 근거를 확인할 수 있습니다.</p></div><div class="status-legend"><span>● 구현/실행/근거</span><span>● 결과 무결성</span><span>○ 재현/과학 검증</span></div></header>
      <div class="architecture-toolbar panel" role="group" aria-label="아키텍처 지도 도구"><label>node 검색<input id="node-search" type="search" placeholder="D1, Numeric, GDN…"></label><label>단계<select id="lane-filter"><option value="">전체 lane</option>{lane_options}</select></label><label class="check-control"><input id="risk-filter" type="checkbox"> 위험 node 강조</label><label class="check-control"><input id="frozen-only" type="checkbox"> 실제 frozen 경로만</label><label class="check-control"><input id="show-unknown" type="checkbox" checked> 미확인 연결 보기</label><div class="zoom-controls"><button id="zoom-out" aria-label="축소">−</button><button id="fit-view">맞춤</button><button id="zoom-in" aria-label="확대">＋</button><button id="reset-map">초기화</button></div></div>
      <div class="architecture-workspace panel"><div class="map-scroll"><div id="map-stage" class="map-stage">{_render_architecture_svg(vm)}</div></div><div id="subnode-strip" class="subnode-strip" aria-live="polite"><span>관계 후보 탐색 또는 Rule Construction을 선택하면 세부 node가 펼쳐집니다.</span></div></div>
      <div class="edge-legend" aria-label="연결선 의미"><span class="legend-frozen">굵은 실선 · frozen execution</span><span class="legend-verified">얇은 실선 · 코드·테스트 확인</span><span class="legend-conditional">점선 · 설계/조건부</span><span class="legend-gap">빨간 점선 · authority gap</span><span class="legend-legacy">회색선 · legacy/reference</span></div>
      <section class="panel roadmap" aria-labelledby="meta-lineage-heading"><div class="panel-heading"><div><p class="kicker">META provenance</p><h3 id="meta-lineage-heading">META 근거 출처와 개입 경계</h3></div><a class="text-button" href="../validation_v2/meta_lineage/META_LINEAGE_AUDIT_V1.md">감사 보고서</a></div><div class="readiness-summary"><article><h4>META SOURCE</h4><strong>{_esc(vm['meta_lineage']['source'])}</strong><p>공식 physical graph와 AI-assisted reviewed semantic declaration이 함께 기여합니다.</p></article><article><h4>META USER INTERVENTION</h4><strong>{_esc(vm['meta_lineage']['user_intervention'])}</strong><p>최종 Top-20은 code가 결정적으로 선택했습니다. 별도로 AI-authored declaration은 <code>{_esc(vm['meta_lineage']['declaration_intervention_surface'])}</code>입니다.</p></article><article><h4>META EXACT PUBLIC REPRODUCIBILITY</h4><strong>{_esc(vm['meta_lineage']['exact_public_reproducibility'])}</strong><p>Exact replay에는 self-hashed private reviewed input이 필요합니다.</p></article></div></section>
      <section class="panel roadmap gdn-evidence-flow" aria-labelledby="gdn-flow-heading"><div class="panel-heading"><div><p class="kicker">Learned-Graph evidence · 설명용 sidecar</p><h3 id="gdn-flow-heading">HAI-adapted GDN의 제한된 연결</h3></div><a class="text-button" href="../validation_v2/gdn_rule_evidence/GDN_TO_RULE_MAPPING_REPORT_V1.md">근거 map</a></div><svg viewBox="0 0 930 155" role="img" aria-label="HAI-adapted GDN에서 learned graph evidence와 temporal evidence 및 explanation annotation으로 이어지는 비권한 경로"><defs><marker id="gdn-arrow" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#64748b"/></marker></defs><g fill="#fff" stroke="#64748b"><rect x="20" y="30" width="210" height="75" rx="8"/><rect x="270" y="30" width="210" height="75" rx="8"/><rect x="520" y="30" width="180" height="75" rx="8"/><rect x="740" y="30" width="170" height="75" rx="8"/></g><g font-size="15" text-anchor="middle" fill="#172033"><text x="125" y="62">HAI-adapted GDN</text><text x="125" y="85">EXP-01C supporting</text><text x="375" y="62">Learned-Graph Evidence</text><text x="375" y="85">2 pair+horizon</text><text x="610" y="62">Temporal Evidence</text><text x="610" y="85">V2A Rule 유지</text><text x="825" y="62">설명 annotation</text><text x="825" y="85">130 / 6,418</text></g><g stroke="#64748b" stroke-width="2" stroke-dasharray="6 5" marker-end="url(#gdn-arrow)"><path d="M230 68H265"/><path d="M480 68H515"/><path d="M700 68H735"/></g><text x="465" y="140" text-anchor="middle" font-size="13" fill="#64748b">예측·Rule 포함·수치·방향·horizon을 바꾸지 않는 보조 근거 경로</text></svg><p class="chart-note"><code>GDN_ASSISTED_TITLE_STRONG</code>은 pair+horizon overlap에 따른 잠정 문서 eligibility입니다. 최종 제목은 DG-04이며 causal graph·detector·primary candidate authority가 아닙니다.</p></section>
      <details class="catalog-panel panel"><summary><span><b>구성요소 카탈로그</b> · Registry 32개</span><small>카드 wall 대신 검색 가능한 표로 제공합니다.</small></summary><div class="catalog-tools"><label>구성요소 검색<input id="catalog-search" type="search" placeholder="component ID, 역할, input…"></label><label>Lane<select id="catalog-lane"><option value="">전체</option>{lane_options}<option value="LANE_GOVERNANCE_CATALOG">Governance / catalog</option></select></label><label>위험<select id="catalog-risk"><option value="">전체</option><option>HIGH</option><option>MEDIUM</option><option>LOW</option></select></label><span id="catalog-count">32개</span></div><div class="table-wrap catalog-table"><table><thead><tr><th>구성요소</th><th>역할</th><th>Input</th><th>Output</th><th>코드</th><th>실행</th><th>근거</th><th>무결성</th><th>재현</th><th>과학 검증</th><th>위험</th></tr></thead><tbody>{catalog_rows}</tbody></table></div></details>
    </section>'''


def _render_experiments_view(vm: Mapping[str, Any]) -> str:
    overlap = vm["overlap"]
    exp_rows = "".join(
        f'<tr class="experiment-row" tabindex="0" data-experiment-id="{_esc(exp["experiment_id"])}"><th scope="row"><code>{_esc(exp["experiment_id"])}</code><strong>{_esc(exp["name"])}</strong></th><td>{_esc(exp["research_question"])}</td><td><span class="gate gate-{_esc(exp["gate"]["ready_now"].lower())}">{_esc(vm["labels"].get(exp["gate"]["ready_now"], exp["gate"]["ready_now"]))}</span></td><td>{_esc(exp["current_evidence"])}</td><td>{_esc(exp["gate"]["must_fix_before_start"])}</td><td>{_esc(exp["claim_impact"])}</td></tr>'
        for exp in vm["experiments"]
    )
    panel_role_labels = {
        "DEVELOPMENT_ONLY": "개발 평가",
        "PRIMARY_HELDOUT": "주 held-out",
        "EXTERNAL_VERSION_REPLICATION_1": "외부 버전 재현 1",
        "EXTERNAL_VERSION_REPLICATION_2": "외부 버전 재현 2",
    }
    panel_rows = "".join(
        '<tr>'
        f'<th scope="row"><code>{_esc(panel["panel_id"])}</code><strong>HAI {_esc(panel["dataset_version"])}</strong></th>'
        f'<td>{_esc(panel_role_labels.get(panel["role"], panel["role"]))}</td>'
        f'<td>{_esc(panel["nominal_attack_count"])}</td>'
        '<td>사전 P1 eligibility 확정 후 산출</td>'
        f'<td>{_esc(panel["attack_access_status"])}</td>'
        f'<td>{_esc(panel["method_policy"])}</td>'
        f'<td>{_esc(panel["metric_policy"])}</td>'
        f'<td>{_esc(panel["result_status"])}</td>'
        '</tr>'
        for panel in vm["evaluation_panels"]
    )
    panel_section = f'''
      <section class="panel roadmap evaluation-expansion" aria-labelledby="evaluation-expansion-heading">
        <div class="panel-heading"><div><p class="kicker">Evaluation Expansion · DG-05 이전 계획</p><h3 id="evaluation-expansion-heading">버전별 평가 panel</h3></div><a class="text-button" href="../validation_v2/evaluation_expansion/EVALUATION_MASTER_PLAN_V1.md">동결 계획</a></div>
        <div class="table-wrap"><table><thead><tr><th>Panel</th><th>역할</th><th>명목 scenario</th><th>실제 P1 분모</th><th>접근</th><th>방법</th><th>지표</th><th>결과</th></tr></thead><tbody>{panel_rows}</tbody></table></div>
        <p class="pilot-warning">버전별 공격 시나리오는 동일 분포의 독립 표본으로 간주하지 않으며, 주 결과는 버전별로 분리해 보고합니다.</p>
      </section>''' if panel_rows else ""
    return f'''
    <section class="view-panel" id="view-experiments" data-view-panel="experiments" aria-labelledby="nav-experiments" hidden>
      <header class="view-heading"><div><p class="kicker">PILOT V1 · VALIDATION V2 development evidence</p><h2>실험·결과</h2><p>정상 전용 근거, PILOT V1, VALIDATION V2 test1 개발 성능을 분리합니다. 결과 무결성 확인은 과학적 검증이 아닙니다.</p></div></header>
      <section class="panel roadmap"><div class="panel-heading"><div><p class="kicker">VALIDATION V2 · normal-only</p><h3>test1을 열기 전에 고정된 결과</h3></div></div><div class="readiness-summary"><article><h4>EXP-01</h4><strong>GDN ablation 유지</strong><p>동결 기준에 따라 V2A의 주 후보 정책은 META+STAT입니다.</p></article><article><h4>EXP-01B</h4><strong>GDN_ABLATION_ONLY</strong><p>{_esc(vm['exp01b']['equal_budget'])}</p></article><article><h4>EXP-02</h4><strong>{_esc(vm['v2_normal_only']['selected_numeric_policy'])}</strong><p>29개 후보 pair → 39개 directional relation → 39-rule Formal V4 portfolio</p></article></div><p class="chart-note">EXP-01B의 combined 증가는 split 안정성·양의 EdgeMask·고유 executable Rule 기준을 통과하지 못했습니다. 위 정상 전용 단계 당시 test1·label·test2·held-out 접근은 0이었습니다. 아래 후속 EXP-04는 승인된 test1 개발 평가입니다.</p></section>
      {('<p class="chart-note">현재 DG-04는 DEC-025로 승인되었습니다. 아래 완료된 EXP-03/03B의 다음 Gate 설명은 각 실행 종료 당시의 역사적 상태입니다. 현재 외부 정상 준비는 custody 차단이며 DG-03C 예산은 미정입니다.</p>' if vm.get('dg04_method_lock') else '')}
      {_render_exp03b(vm)}{_render_exp03_execution(vm)}{_render_front_results(vm)}{panel_section}
      <aside class="warning-banner">PILOT V1 결과는 test1의 14개 연속 공격 구간 단위(contiguous attack-event units)를 이용한 예비 결과입니다. 통계적 독립성과 held-out 일반화는 확인되지 않았습니다. D1은 T2 Agentic Rule-only가 아닙니다.</aside>
      <div class="results-grid"><article class="panel"><div class="panel-heading"><div><p class="kicker">Attack-event Recall</p><h3>14개 unit 중 반응한 unit</h3></div></div>{_render_result_bars(vm)}</article><article class="panel"><div class="panel-heading"><div><p class="kicker">Normal FAR/hour</p><h3>정상 구간 false episode 부담</h3></div></div>{_render_far_panels(vm)}</article><article class="panel overlap-panel"><div class="panel-heading"><div><p class="kicker">D0 / D1 overlap</p><h3>사건 단위 반응 2×2</h3></div></div><table class="overlap-matrix"><thead><tr><th></th><th>D1 탐지</th><th>D1 미탐</th></tr></thead><tbody><tr><th>D0 탐지</th><td>{overlap['both']}<small>둘 다</small></td><td>{overlap['d0_only']}<small>D0만</small></td></tr><tr><th>D0 미탐</th><td>{overlap['d1_only']}<small>D1만</small></td><td>{overlap['neither']}<small>둘 다 미탐</small></td></tr></tbody></table></article><article class="panel exact-table-panel"><div class="panel-heading"><div><p class="kicker">Accessible data table</p><h3>정확한 고정 값</h3></div></div>{_render_results_table(vm)}</article></div>
      <section class="panel roadmap"><div class="panel-heading"><div><p class="kicker">Experiment Roadmap</p><h3>실험 Gate와 claim 영향</h3></div></div><div class="table-wrap"><table><thead><tr><th>실험</th><th>확인할 가설</th><th>현재 상태</th><th>현재 근거</th><th>먼저 해결할 것</th><th>결과에 따른 결정</th></tr></thead><tbody>{exp_rows}</tbody></table></div></section>
    </section>'''


def _render_dg04(vm: Mapping[str, Any]) -> str:
    lock=vm.get('dg04_method_lock')
    if not lock:return ''
    rows=''.join(f"<tr><td>{arm}</td><td>{p['pair_count']}</td><td>{p['rule_count']}</td></tr>" for arm,p in lock['portfolios'].items())
    return f'''<section class="panel roadmap" aria-labelledby="dg04-xver-heading"><h3 id="dg04-xver-heading">DG-04 방법 고정 · 외부 정상 준비</h3>
    <p>DEC-025 · APPROVED_WITH_SCOPED_AGENTIC_CLAIM</p><p>{_esc(lock['title'])}</p>
    <p>EXP-03B 정상-only: T2는 matched-maximum-budget T1-B 대비 이점이 있으나 주요 의미 지표에서 T0보다 우수하지 않았습니다. GDN은 learned-graph evidence이며 후보·탐지·수치 권한이 아닙니다. Fusion은 사전등록 비교입니다.</p>
    <table><thead><tr><th>HELDOUT_CANDIDATE</th><th>pairs</th><th>guard-retained Rules</th></tr></thead><tbody>{rows}</tbody></table>
    <p>V2A 39 Rules는 별도 reference로 보존. T2는 Repeat 1만 사용. 공격 검증·production 권한 없음.</p>
    <p>Stage B: BLOCKED_NORMAL_DATA_CUSTODY. 공식 정상 train1 두 컨테이너는 identity 검증 후 헤더에서 중단했습니다. label 값 해석·검증·사용 0, 공격 payload 0. 추가 header 접근은 자동심사에서 차단되어 우회하지 않았습니다.</p>
    <p>Metadata: HAI22 24 / HAI21 22 P1 역할 feature 대응, portable META 20 / 19. 정상 schema·STAT·GDN·외부 T0/T2는 미완료. DG-03C exact budget 미정.</p>
    <p>eTaPR 공식/합성 109개 per-file 일치. 여러 파일 집계·secondary P1 range scope는 아직 미정입니다. 버전별 공격 시나리오는 동일 분포의 독립 표본으로 간주하지 않으며, 주 결과는 버전별로 분리해 보고합니다.</p>
    <a href="../validation_v2/dg04_xver_prep/P1_MAPPING_REPORT_V1.md">매핑 및 차단 기록</a></section>'''


def _render_exp03b(vm: Mapping[str, Any]) -> str:
    if vm.get('exp03b_execution'):
        e=vm['exp03b_execution']; p=vm['exp03b_preparation']
        def ratio(value):return f"{value['numerator']}/{value['denominator']}"
        rows=''.join(f"<tr><th>{_esc(arm)}</th><td>{ratio(r['strict']['F1'])}</td><td>{ratio(r['strict']['directional_F1'])}</td><td>{r['strict']['semantic_exact_match_count']}/29</td></tr>" for arm,r in e['reports'].items())
        return f'''<section class="panel roadmap" aria-labelledby="exp03b-heading"><h3 id="exp03b-heading">EXP-03B · 의미적 Rule induction 실행</h3><p>{_esc(e['status'])} · {_esc(e['disposition'])}</p><p>29 pair · 20 structural rows · numeric option rows 0. DG-03B_REVISED 승인 후 {e['calls']} calls · {e['total_tokens']:,} tokens · 표준 uncached 비용 상한 USD{_esc(e['cost_upper_bound_usd'])}.</p><table><thead><tr><th>arm</th><th>strict pair F1</th><th>directional F1</th><th>exact semantic set</th></tr></thead><tbody>{rows}</tbody></table><p>Feedback {e['feedback_actions']}회/{e['feedback_distinct_pairs']} pair · train3-confirmed exact repair {e['exact_repair_distinct_pairs']} pair. 정상 확인 reference 기반 결과이며, 인과·공격 탐지·일반화 검증이 아닙니다. 수치는 hidden train3 freeze 후 SCI02B로 결속했습니다.</p><p>원 승인 ceiling: {p['maximum_total_tokens']:,} tokens / USD{_esc(p['cost_ceiling_usd'])}. EXP-03 V1과 V2A·EXP04/05는 보존. 다음 DG-04; 추가 provider 호출·공격 접근·교수님 자동 제출 금지.</p><a href="../validation_v2/exp03b/execution_v2/EXP03B_RESULTS_REPORT_V1.md">실행 결과·독립 QA</a> · <a href="../validation_v2/exp03b/DG03B_PROVIDER_DECISION_BRIEF_V2.md">승인된 예산 계약</a></section>'''
    if not vm.get('exp03b_preparation'):return ''
    p=vm['exp03b_preparation']
    return f'''<section class="panel roadmap" aria-labelledby="exp03b-heading"><h3 id="exp03b-heading">EXP-03B · 의미적 Rule induction V2 준비</h3><p>{_esc(p['status'])} · {p['cohort_count']} pair · 20 structural rows · numeric option rows 0 · provider 호출 0</p><p>train1 근거 → 모든 outputs·train2 admission·train3 평가 동결 → SCI02B 결정론적 수치 결속 → Formal V4 → train4 guard. 준비 완료는 Agentic 결과가 아닙니다.</p><p>{_esc(p['next_gate'])} 별도 승인: 최대{p['maximum_calls']}회 · {p['maximum_total_tokens']:,} tokens · USD{_esc(p['cost_ceiling_usd'])}. DG-04는 EXP-03B 결과 이후입니다.</p><p>EXP-03 V1: CONSTRAINED_RULE_MATERIALIZATION_BENCHMARK · COMPLETE · AGENTIC FEEDBACK NOT EXERCISED. 기존 결과와 과거 EXP03B V1 계약은 보존합니다.</p><a href="../validation_v2/exp03b/DG03B_PROVIDER_DECISION_BRIEF_V2.md">수정된 DG-03B 결정 brief</a></section>'''


def _render_exp03_execution(vm: Mapping[str, Any]) -> str:
    result = vm.get("exp03_execution", {})
    if not result:
        return ""
    rows = "".join(f'<tr><th scope="row">{_esc(row["arm"])}</th><td>{row["accepted"]}/{row["scheduled"]}</td><td>{row["calls"]}</td><td>{row["feedback_activated"]}</td></tr>' for row in result["arm_metrics"])
    return f'''<section class="panel roadmap" aria-labelledby="exp03-live-heading"><div class="panel-heading"><div><p class="kicker">EXP-03 · 고정 snapshot 구성 비교</p><h3 id="exp03-live-heading">규칙 구성 결과와 feedback 관찰</h3></div><a class="text-button" href="../validation_v2/exp03/execution_v1/EXP03_RESULTS_REPORT_V1.md">결과·해석 경계</a></div><p>{_esc(result['model_snapshot'])} · {_esc(result['status'])} · {result['calls']}회 호출 · 표준요금 상한 USD {_esc(result['cost_upper_bound_usd'])}</p><div class="table-wrap"><table><thead><tr><th>arm</th><th>승인/예정</th><th>생성 호출</th><th>feedback 발생</th></tr></thead><tbody>{rows}</tbody></table></div><p class="chart-note">39개 고정 관계의 reference-bound construction 비교입니다. 새로운 관계 발견·탐지 성능 또는 Agentic 우월성을 뜻하지 않습니다. synthetic stress는 별도입니다. DG-04에서 제목·기여 표현을 결정합니다.</p></section>'''


def _render_readiness_view(vm: Mapping[str, Any]) -> str:
    gap_labels = vm["labels"].get("gap_labels_ko", {})
    callouts = "".join(
        f'<article class="p0-card"><span>{_esc(item["gap_id"])}</span><h3>{_esc(gap_labels.get(item["gap_id"], {}).get("title", item["title"]))}</h3><p>{_esc(item.get("current_resolution", gap_labels.get(item["gap_id"], {}).get("description", item["root_cause"])))}</p><dl><div><dt>현재 V2 상태</dt><dd>{_esc(item.get("status", "UNKNOWN"))}</dd></div><div><dt>GAP-000 주요 처분</dt><dd>{_esc(vm["labels"].get(item["disposition"], item["disposition"]))}</dd></div><div><dt>GAP-000 긴급도</dt><dd>{_esc(item["priority"])}</dd></div></dl></article>'
        for item in vm["p0"]
    )
    root_rows = "".join(
        f'<tr data-disposition="{_esc(item.get("disposition", "UNKNOWN"))}" data-priority="{_esc(item.get("priority", "UNKNOWN"))}"><th scope="row"><code>{_esc(item["gap_id"])}</code><strong>{_esc(gap_labels.get(item["gap_id"], {}).get("title", item["title"]))}</strong></th><td>{_esc(vm["labels"].get(item.get("disposition", "UNKNOWN"), item.get("disposition", "UNKNOWN")))}</td><td>{_esc(item.get("priority", "UNKNOWN"))}</td><td>{_esc(item["scientific_impact"])}</td><td>{_esc(item.get("current_resolution", item.get("recommended_action", "UNKNOWN")))}</td><td>{_esc(item.get("status", "UNKNOWN"))}</td></tr>'
        for item in vm["root_issues"]
    )
    disposition_items = "".join(
        f'<li><span>{_esc(vm["labels"].get(key, key))}</span><strong>{value}</strong></li>'
        for key, value in vm["readiness"]["disposition_counts"].items()
    )
    priority_items = "".join(f'<li><span>{_esc(key)}</span><strong>{value}</strong></li>' for key, value in vm["readiness"]["priority_counts"].items())
    return f'''
    <section class="view-panel" id="view-readiness" data-view-panel="readiness" aria-labelledby="nav-readiness" hidden>
      <header class="view-heading"><div><p class="kicker">GAP-000 원분류 · 현재 V2 해결 상태</p><h2>준비도·위험</h2><p>GAP-000의 주요 처분 (Primary disposition)·긴급도 (Urgency)와 이후 VALIDATION V2의 해결 상태를 분리해 표시합니다. 전체 완료율은 만들지 않습니다.</p></div></header>
      <div class="p0-grid">{callouts}</div>
      <div class="readiness-summary"><article class="panel"><h3>GAP-000 원분류</h3><ul>{disposition_items}</ul></article><article class="panel"><h3>GAP-000 원긴급도</h3><ul>{priority_items}</ul></article><article class="panel core-gate"><h3>핵심 검증 Gate</h3><ol><li>완료: Final scientific authority</li><li>완료: D1 durable pre-label custody</li><li>완료: Validation/final 역할과 event 의미 고정</li><li>완료: portable metric contract</li><li>현재: frozen EXP-04 label-blind prediction과 durable freeze</li></ol></article></div>
      <section class="panel readiness-table"><div class="panel-heading"><div><p class="kicker">19 root issues</p><h3>전체 remediation inventory</h3></div><div class="inline-filters"><label>Disposition<select id="gap-disposition"><option value="">전체</option>{''.join(f'<option value="{_esc(key)}">{_esc(vm["labels"].get(key,key))}</option>' for key in vm["readiness"]["disposition_counts"])}</select></label><label>Urgency<select id="gap-priority"><option value="">전체</option><option>P0</option><option>P1</option><option>P2</option><option>P3</option></select></label></div></div><div class="table-wrap"><table><thead><tr><th>Gap</th><th>Primary disposition</th><th>Urgency</th><th>과학 영향</th><th>권고 조치</th><th>상태</th></tr></thead><tbody id="gap-table-body">{root_rows}</tbody></table></div></section>
    </section>'''


def _render_evidence_view(vm: Mapping[str, Any]) -> str:
    timeline = "".join(
        f'<li><time>{_esc(event["date"])}</time><div><strong>{_esc(event["title"])}</strong><p>{_esc(event["summary"])}</p></div><span>{_esc(event["status"])}</span></li>'
        for event in reversed(vm["history_events"][:10])
    )
    decisions = "".join(
        f'<tr><th scope="row"><code>{_esc(row["decision_id"])}</code></th><td>{_esc(row["title"])}</td><td>{_esc(row["status"])}</td><td>{_esc(row["current_relevance"])}</td></tr>'
        for row in vm["decisions"][-10:]
    )
    claims = "".join(
        f'<tr><th scope="row"><code>{_esc(row["claim_id"])}</code></th><td>{_esc(row["claim_text"])}</td><td>{_esc(vm["labels"].get(row["status"], row["status"]))}</td><td>{_esc(row["allowed_wording"])}</td></tr>'
        for row in vm["claims"]
    )
    return f'''
    <section class="view-panel" id="view-history" data-view-panel="history" aria-labelledby="nav-history" hidden>
      <header class="view-heading"><div><p class="kicker">History · Decision · Evidence</p><h2>이력·근거</h2><p>현재 과학 상태는 Registry가 결정하며, history는 계보를 설명할 뿐 과거 claim을 승격하지 않습니다.</p></div></header>
      <div class="evidence-grid"><article class="panel timeline-panel"><div class="panel-heading"><div><p class="kicker">10 milestones</p><h3>연구 주요 단계</h3></div></div><ol class="history-line">{timeline}</ol></article><article class="panel authority-panel"><p class="kicker">Source Authority</p><h3>공식 기준 코드·근거</h3><dl><div><dt>Scientific ref</dt><dd><code>{_esc(vm["scientific_authority"]["ref"])}</code></dd></div><div><dt>Commit</dt><dd><code>{_esc(vm["scientific_authority"]["commit"])}</code></dd></div><div><dt>Registry digest</dt><dd><code>{_esc(vm["registry_digest"])}</code></dd></div><div><dt>View config digest</dt><dd><code>{_esc(vm["config_digest"])}</code></dd></div></dl><p>근거 출처 추적 (Provenance)은 강하지만 새 환경 독립 재현 (Fresh-machine Reproduction)은 아직 완료되지 않았습니다.</p></article></div>
      <details class="panel evidence-table"><summary><b>주요 Decision</b><small>기본 화면에서는 full hash와 raw Registry를 숨깁니다.</small></summary><div class="table-wrap"><table><thead><tr><th>ID</th><th>결정</th><th>상태</th><th>현재 의미</th></tr></thead><tbody>{decisions}</tbody></table></div></details>
      <details class="panel evidence-table"><summary><b>Claim & Evidence</b><small>과학적 주장 상태는 <code>claims.csv</code>가 유일한 기준입니다.</small></summary><div class="table-wrap"><table><thead><tr><th>Claim</th><th>내용</th><th>상태</th><th>허용 문구</th></tr></thead><tbody>{claims}</tbody></table></div></details>
      <div class="evidence-links panel"><a href="../history/PROFESSOR_FEEDBACK_LINEAGE.md">Professor feedback lineage</a><a href="../history/SUPERSEDED_DIRECTIONS.md">Superseded directions</a><a href="../architecture/00_overview/ARCH_000_REPORT.md">전체 architecture audit</a><a href="../architecture/11_outer_reproducibility/ARCH_011_REPORT.md">OUTER·재현성 audit</a></div>
    </section>'''


def render_dashboard_v2(data: Mapping[str, Any], digest: str, rcc_root: Path) -> str:
    vm = build_dashboard_view_model(data, digest, rcc_root)
    nav = "".join(
        f'<button id="nav-{_esc(item["view_id"])}" class="primary-nav-item {"is-active" if index == 0 else ""}" data-view="{_esc(item["view_id"])}" aria-current="{"page" if index == 0 else "false"}"><span>{index + 1:02d}</span>{_esc(item["label_ko"])}</button>'
        for index, item in enumerate(vm["navigation"])
    )
    payload = json.dumps(vm, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return f'''<!doctype html>
<html lang="ko">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="color-scheme" content="light"><meta name="rcc-registry-binding" content="registry_version={_esc(vm['registry_version'])} registry_digest={_esc(vm['registry_digest'])} authority={_esc(vm['scientific_authority']['commit'])}"><title>Research Control Center · Dashboard V2</title><link rel="stylesheet" href="assets/rcc.css"></head>
<body data-dashboard-version="2">
<a class="skip-link" href="#main-workspace">본문으로 건너뛰기</a>
<header class="app-header"><button id="mobile-nav-toggle" class="mobile-nav-toggle" aria-controls="primary-navigation" aria-expanded="false" aria-label="메뉴 열기">☰</button><a class="brand" href="#overview" aria-label="Research Control Center 개요"><span>RCC</span><strong>연구 아키텍처</strong></a><div class="header-context"><span>PILOT V1 보존</span><b>VALIDATION V2 개발 평가 QA PASS</b></div><div class="header-state"><span class="state-dot"></span>Registry 최신</div></header>
<div class="app-shell"><nav id="primary-navigation" class="primary-navigation" aria-label="주요 화면">{nav}<div class="nav-foot"><span>과학 기준</span><code title="{_esc(vm["scientific_authority"]["commit"])}">{_esc(vm["scientific_authority"]["commit"][:10])}</code><small>구현·실행·무결성·과학 검증·재현·일반화는 서로 다른 상태입니다.</small></div></nav>
<main id="main-workspace" class="workspace" tabindex="-1">{_render_overview(vm)}{_render_architecture_view(vm)}{_render_experiments_view(vm)}{_render_readiness_view(vm)}{_render_evidence_view(vm)}</main></div>
<aside id="detail-drawer" class="detail-drawer" aria-labelledby="drawer-title" aria-hidden="true"><div class="drawer-head"><div><p class="kicker" id="drawer-kicker">구성요소 상세</p><h2 id="drawer-title">선택된 항목</h2></div><button id="drawer-close" aria-label="상세 패널 닫기">×</button></div><div class="drawer-tabs" role="tablist"><button id="drawer-tab-easy" role="tab" aria-selected="true" data-drawer-mode="easy">쉽게 보기</button><button id="drawer-tab-technical" role="tab" aria-selected="false" data-drawer-mode="technical">기술 상세</button></div><div id="drawer-body" class="drawer-body"></div></aside><div id="drawer-backdrop" class="drawer-backdrop" hidden></div>
<script id="rcc-view-model" type="application/json">{payload}</script><script src="assets/rcc.js"></script>
</body></html>'''
