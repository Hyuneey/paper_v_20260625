"""Separated prospective GDN evidence roles; no I/O or hidden-answer access."""
from dataclasses import dataclass
import math
import statistics
from .exp03b_contract_v1 import HORIZONS, SOURCES, require


APPROVAL = "APPROVED_WITH_SEPARATED_GDN_EVIDENCE_ROLES"


@dataclass(frozen=True)
class GlobalSeedEvidenceV1:
    version: str
    split: str
    seed: int
    source: str
    target: str
    rows: tuple

    def __post_init__(self):
        require(self.version in ('22.04', '21.03') and self.split in ('train1', 'train2'), 'GLOBAL_SPLIT')
        require(self.seed in (11, 23, 37), 'GLOBAL_SEED')
        require(type(self.rows) is tuple and len(self.rows) == 5 and all(type(r) is tuple and len(r) == 4 for r in self.rows), 'GLOBAL_FIVE_ROWS')
        require(tuple(r[0] for r in self.rows) == HORIZONS, 'GLOBAL_HORIZONS')
        for row in self.rows:
            require(len(row) == 4 and all(type(v) in (int, float) and math.isfinite(v) for v in row[1:3]), 'GLOBAL_ROW')
            require(row[3] is None or type(row[3]) in (int, float) and math.isfinite(row[3]), 'GLOBAL_SIGNED_EFFECT')


@dataclass(frozen=True)
class AuxiliaryEventEvidenceV1:
    version: str
    split: str
    seed: int
    source: str
    target: str
    rows: tuple
    role: str = 'AUXILIARY_CORROBORATION_ONLY'

    def __post_init__(self):
        require(self.role == 'AUXILIARY_CORROBORATION_ONLY', 'AUXILIARY_ROLE')
        require(self.version in ('22.04', '21.03') and self.split in ('train1', 'train2'), 'EVENT_SPLIT')
        require(self.seed in (11, 23, 37), 'EVENT_SEED')
        require(type(self.rows) is tuple and len(self.rows) == 10 and all(type(r) is tuple and len(r) == 5 for r in self.rows), 'EVENT_TEN_ROWS')
        require(tuple((r[0], r[1]) for r in self.rows) == tuple((s, h) for s in SOURCES for h in HORIZONS), 'EVENT_AXES')
        # (source direction, horizon, support, signed effect or None, state).
        for _, _, count, effect, state in self.rows:
            require(type(count) is int and count >= 0, 'EVENT_SUPPORT')
            require(state in ('AVAILABLE', 'NO_VALIDATION_EVENT', 'NOT_IN_LEARNED_GRAPH'), 'EVENT_STATE')
            require((state == 'AVAILABLE' and count > 0 and type(effect) in (int, float) and math.isfinite(effect))
                    or (state != 'AVAILABLE' and effect is None), 'EVENT_UNAVAILABLE_NOT_ZERO')


def aggregate_global(seeds: tuple[GlobalSeedEvidenceV1, ...], *, version: str, split: str) -> tuple:
    """Exact EXP03B median: all seeds for embedding/attention, available edges for delta."""
    require(type(seeds) is tuple and len(seeds) == 3 and all(type(s) is GlobalSeedEvidenceV1 for s in seeds), 'GLOBAL_ONLY_NO_EVENT_FUSION')
    require({s.seed for s in seeds} == {11, 23, 37}, 'ALL_THREE_SEEDS_REQUIRED')
    require(all(s.version == version and s.split == split for s in seeds), 'GLOBAL_SPLIT_PURITY')
    require(len({(s.source, s.target) for s in seeds}) == 1, 'GLOBAL_PAIR')
    result = []
    for i, horizon in enumerate(HORIZONS):
        effects = [s.rows[i][3] for s in seeds if s.rows[i][3] is not None]
        result.append((horizon, statistics.median(s.rows[i][1] for s in seeds),
                       statistics.median(s.rows[i][2] for s in seeds),
                       statistics.median(effects) if effects else None))
    return tuple(result)


def provider_global(seeds: tuple[GlobalSeedEvidenceV1, ...], *, version: str) -> tuple:
    return aggregate_global(seeds, version=version, split='train1')


def retrieval_global(seeds: tuple[GlobalSeedEvidenceV1, ...], *, version: str) -> tuple:
    return aggregate_global(seeds, version=version, split='train2')


def event_validation_starts(*, source_event_rows: tuple[int, ...], validation_indices: tuple,
                            history_rows: int = 5) -> tuple[int, ...]:
    """EXP01C stop anchor (start + history), file-local seed-validation intersection."""
    require(history_rows == 5 and all(type(x) is int and x >= 0 for x in source_event_rows), 'EVENT_COORDINATES')
    require(all(f == 0 and type(i) is int and i >= 0 for f, i in validation_indices), 'ONE_SPLIT_ONE_FILE')
    events = frozenset(source_event_rows)
    return tuple(i for _, i in validation_indices if i + history_rows in events)
