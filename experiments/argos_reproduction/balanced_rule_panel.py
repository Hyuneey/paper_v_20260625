"""Label-free balanced primary-panel selection for TASK-035B."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Mapping, Sequence


class BalancedPanelError(ValueError):
    pass


def select_balanced_panel(
    rules: Sequence[Mapping[str, Any]],
    anchor_order: Sequence[str],
    *,
    panel_size: int = 10,
) -> list[dict[str, Any]]:
    if panel_size <= 0:
        raise BalancedPanelError("TASK035B_PANEL_SIZE_INVALID")
    rank = {anchor_id: index for index, anchor_id in enumerate(anchor_order)}
    if len(rank) != len(anchor_order):
        raise BalancedPanelError("TASK035B_ANCHOR_ORDER_DUPLICATE")
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen_hashes: set[str] = set()
    for source in rules:
        item = dict(source)
        anchor_id = str(item["anchor_id"])
        rule_hash = str(item["rule_sha256"])
        if anchor_id not in rank:
            raise BalancedPanelError("TASK035B_RULE_ANCHOR_UNKNOWN")
        if rule_hash in seen_hashes:
            raise BalancedPanelError("TASK035B_RULE_HASH_DUPLICATE")
        seen_hashes.add(rule_hash)
        groups[anchor_id].append(item)
    if len(rules) < panel_size:
        raise BalancedPanelError("TASK035B_PANEL_INSUFFICIENT_RULES")
    for items in groups.values():
        items.sort(key=lambda item: item["rule_sha256"])
    ordered_anchors = sorted(groups, key=lambda anchor_id: rank[anchor_id])
    selected: list[dict[str, Any]] = []
    offset = 0
    while len(selected) < panel_size:
        added = False
        for anchor_id in ordered_anchors:
            if offset < len(groups[anchor_id]):
                selected.append(dict(groups[anchor_id][offset]))
                added = True
                if len(selected) == panel_size:
                    break
        if not added:
            raise BalancedPanelError("TASK035B_PANEL_ROUND_ROBIN_EXHAUSTED")
        offset += 1
    return selected
