"""Independent R3 input, census, isolation, and opportunity completion audit.

The oracle literals and pure calculations in this file are derived from the
committed Protocol V2/V3/V4 and source-census supplement authorities.  No
production evaluator helper is used to calculate an expected source event,
cluster, isolation decision, or opportunity cardinality.

This file also corrects the historical audit-harness error around
``CanonicalOpportunityV4``: the factory-only lower object is never passed to
``dataclasses.replace`` or directly reconstructed.  Opportunity attacks enter
through caller-control arguments, evaluator-owned envelope/census dataclasses,
or canonical membership replay.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
import json
import math
from pathlib import Path
import statistics
import unittest
from unittest.mock import patch

import paperworks.v6.task039e3_r2r_utility_evaluator_authority_v1 as authority_module
import paperworks.v6.task039e3_r2r_utility_evaluator_census_v1 as census_module
from paperworks.v6.task039e3_r2r_utility_evaluator_census_v1 import (
    enumerate_full_census_v1,
    validate_full_census_result_v1,
    validate_opportunity_envelope_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_input_v1 import (
    build_synthetic_feature_frame_v1,
    feature_series_v1,
    feature_value_v1,
    validate_synthetic_feature_frame_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_types_v1 import (
    CanonicalOpportunityEnvelopeV1,
    FullCensusResultV1,
    SyntheticFeatureFrameV1,
    SyntheticFeatureRowV1,
    UtilityEvaluatorV1Error,
    stable_hash_v1,
)
from paperworks.v6 import task039e3_r2r_utility_protocol_v4 as v4
from paperworks.v6.task039e3_r2r_utility_protocol_v3 import RetainedSourceEventV3
import paperworks.v6.task039e3_r2r_utility_source_census_supplement_v1 as supplement


# Frozen lower-authority oracle literals.  These are intentionally not aliases
# of evaluator constants: an evaluator-side substitution must not redefine the
# audit answer.
ORACLE_PRE = 5
ORACLE_POST = 5
ORACLE_STABILITY = 0.8
ORACLE_REFRACTORY = 10
ORACLE_ISOLATION_RADIUS = 2
ORACLE_DENOMINATOR_POLICY = (
    "ALL_AUTOMATICALLY_ENUMERATED_APPLICABLE_CANONICAL_OPPORTUNITIES"
)
ORACLE_MAIN_SOURCES = (
    "P1_FCV01D",
    "P1_FCV01Z",
    "P1_FCV02D",
    "P1_FCV03D",
    "P1_FCV03Z",
    "P1_LCV01D",
    "P1_LCV01Z",
    "P1_PCV01D",
    "P1_PCV01Z",
)
ORACLE_SUPPLEMENT_SOURCES = ("P1_FCV02Z", "P1_PCV02Z", "P1_PP04")
ORACLE_SOURCE_UNIVERSE = (
    "P1_FCV01D",
    "P1_FCV01Z",
    "P1_FCV02D",
    "P1_FCV02Z",
    "P1_FCV03D",
    "P1_FCV03Z",
    "P1_LCV01D",
    "P1_LCV01Z",
    "P1_PCV01D",
    "P1_PCV01Z",
    "P1_PCV02Z",
    "P1_PP04",
)
ORACLE_COMBINED_CENSUS = (
    "cb53d0e4533ebadb61edbdc72b549fe47b46c8dcc4621841aac93a007660ced9"
)
ORACLE_EVENT_POLICY = (
    "3fb20068feff44632be3e4e6917183d52fea5616feec68ede5e9b62f95ecb390"
)
ORACLE_ISOLATION_POLICY = (
    "f62075523632a7573d28e95ca7f0402d87e62977f4a2f14f4eaf2b9a58f0e280"
)


INPUT_SEMANTIC_CLASSES = (
    "outer rows exact tuple",
    "row values exact tuple",
    "feature pair exact tuple",
    "feature pair tuple subclass",
    "feature pair list widening",
    "feature pair generator",
    "feature pair length",
    "feature name exact string",
    "feature value exact float",
    "boolean value rejected",
    "integer value rejected",
    "numeric string rejected",
    "NaN rejected",
    "positive infinity rejected",
    "negative infinity rejected",
    "missing feature rejected",
    "extra feature rejected",
    "duplicate feature rejected",
    "reordered feature rejected",
    "duplicate row rejected",
    "omitted row rejected",
    "reordered row rejected",
    "physical coordinate immutable",
    "timestamp equals physical coordinate",
    "dataset binding immutable",
    "split binding immutable",
    "file binding immutable",
    "schema authority immutable",
    "row identity replay",
    "frame identity replay",
    "unknown feature lookup rejected",
    "outside-row lookup rejected",
)

SOURCE_CENSUS_SEMANTIC_CLASSES = (
    "exact MAIN nine",
    "exact supplement three",
    "exact combined twelve",
    "source universe unique",
    "five-second pre-window",
    "five-second post-window",
    "exact 0.8 stability boundary",
    "exact threshold included",
    "below threshold excluded",
    "unstable window excluded",
    "inside refractory single-link merge",
    "outside refractory split",
    "chained single-link cluster",
    "largest absolute amplitude wins",
    "exact amplitude tie earliest row",
    "local to physical row mapping",
    "inclusive isolation left one",
    "inclusive isolation left two",
    "inclusive isolation right one",
    "inclusive isolation right two",
    "outside isolation left three",
    "outside isolation right three",
    "symmetric isolation",
    "own source excluded from conflicts",
    "same-source duplicate excluded from conflicts",
    "P1_FCV02Z isolation participation",
    "P1_PCV02Z isolation participation",
    "P1_PP04 isolation participation",
    "missing supplement source rejected",
    "caller isolation subset rejected",
    "supplement relation expansion prohibited",
    "source numeric closure exact",
    "raw retained isolated cardinalities distinct",
)

OPPORTUNITY_SEMANTIC_CLASSES = (
    "COMMON-42 exact",
    "T2 authority false",
    "T2 portfolio caller rejected",
    "source subset caller rejected",
    "relation subset caller rejected",
    "caller rule library rejected",
    "caller numeric registry rejected",
    "caller opportunity list rejected",
    "caller sample_n rejected",
    "caller maximum rejected",
    "caller denominator rejected",
    "generator input rejected",
    "lazy iterable rejected",
    "tuple subclass rejected",
    "list subclass rejected",
    "precomputed census injection rejected",
    "fake self-rehashed census rejected",
    "missing opportunity rejected",
    "duplicate opportunity rejected",
    "reordered opportunity rejected",
    "foreign envelope pairing rejected",
    "source-event count not relation count",
    "one event expands to all applicable relations",
    "factory-only opportunity not reconstructed",
    "canonical envelope membership required",
)

INDEPENDENT_UNIQUE_SEMANTIC_CLASSES = (
    len(INPUT_SEMANTIC_CLASSES)
    + len(SOURCE_CENSUS_SEMANTIC_CLASSES)
    + len(OPPORTUNITY_SEMANTIC_CLASSES)
)
RAW_CASE_COUNTS = {
    "builder_boundary": 15,
    "inner_pairs": 15,
    "frame_replay": 21,
    "lookup": 3,
    "source_event_oracle": 11,
    "supplement_offsets": 18,
    "isolation_structure": 4,
    "supplement_no_expansion": 3,
    "cardinality_distinction": 1,
    "caller_controls": 18,
    "census_forgery": 12,
    "envelope_membership": 5,
    "resolver_closure": 10,
}
INDEPENDENT_RAW_ADVERSARIAL_CASES = sum(RAW_CASE_COUNTS.values())
EXPECTED_ACCEPTED_INVALID_CASES = 0

ROOT = Path(__file__).resolve().parents[1]


def _load(relative: str) -> dict[str, object]:
    """Read only committed public authority material, never private registries."""

    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def _build_lower_v4_authority() -> v4.UtilityProtocolV4CanonicalAuthority:
    return v4.build_utility_protocol_v4_canonical_authority(
        executable_equivalence=_load(
            "docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_EXECUTABLE_EQUIVALENCE.json"
        ),
        evidence_manifest=_load(
            "docs/task_reports/TASK-039E1_CONSTRUCTION_EVIDENCE_MANIFEST.json"
        ),
        dataset_manifest=_load("docs/task_reports/TASK-039A_DATASET_MANIFEST_V2.json"),
        csv_structure_report=_load(
            "docs/task_reports/TASK-039A_CSV_STRUCTURE_REPORT.json"
        ),
        c0_config=_load("configs/v6/task039c0_candidate_discovery_protocol.json"),
        br2_config=_load(
            "configs/v6/task039br2_hai_continuous_step_feasibility.json"
        ),
        materialized_audit_receipt=_load(
            "docs/task_reports/"
            "TASK-039E3_R2R_UTILITY_NORMAL_ONLY_AUTHORITY_V1_MATERIALIZED_RECEIPT.json"
        ),
    )


def _oracle_candidates(
    series: tuple[float, ...], threshold: float, tolerance: float
) -> tuple[tuple[int, float], ...]:
    """Pure lower-policy candidate scan, independent of production census code."""

    candidates: list[tuple[int, float]] = []
    for index in range(ORACLE_PRE, len(series) - ORACLE_POST + 1):
        pre = series[index - ORACLE_PRE : index]
        post = series[index : index + ORACLE_POST]
        pre_level = float(statistics.median(pre))
        post_level = float(statistics.median(post))
        amplitude = post_level - pre_level
        pre_fraction = sum(
            abs(value - pre_level) <= tolerance for value in pre
        ) / ORACLE_PRE
        post_fraction = sum(
            abs(value - post_level) <= tolerance for value in post
        ) / ORACLE_POST
        if (
            amplitude != 0.0
            and abs(amplitude) >= threshold
            and pre_fraction >= ORACLE_STABILITY
            and post_fraction >= ORACLE_STABILITY
        ):
            candidates.append((index, amplitude))
    return tuple(candidates)


def _oracle_cluster(
    candidates: tuple[tuple[int, float], ...]
) -> tuple[tuple[int, float], ...]:
    """Single-link within ten seconds; retain magnitude then earliest row."""

    if not candidates:
        return ()
    ordered = tuple(sorted(candidates, key=lambda item: item[0]))
    clusters: list[list[tuple[int, float]]] = [[ordered[0]]]
    for candidate in ordered[1:]:
        if candidate[0] - clusters[-1][-1][0] <= ORACLE_REFRACTORY:
            clusters[-1].append(candidate)
        else:
            clusters.append([candidate])
    return tuple(
        min(cluster, key=lambda item: (-abs(item[1]), item[0]))
        for cluster in clusters
    )


def _oracle_isolated(
    source: str,
    index: int,
    retained: dict[str, tuple[int, ...]],
) -> bool:
    """Exact-twelve, symmetric, inclusive-radius cross-source replay."""

    if tuple(retained) != ORACLE_SOURCE_UNIVERSE:
        raise AssertionError("oracle source universe is not exact and ordered")
    return not any(
        abs(index - other) <= ORACLE_ISOLATION_RADIUS
        for other_source, indices in retained.items()
        if other_source != source
        for other in indices
    )


def _step_series(
    *, length: int, index: int, before: float = 0.0, after: float = 1.0
) -> tuple[float, ...]:
    return tuple(before if row < index else after for row in range(length))


def _piecewise_series(
    length: int, transitions: tuple[tuple[int, float], ...]
) -> tuple[float, ...]:
    result = [0.0] * length
    for index, level in transitions:
        for row in range(index, length):
            result[row] = float(level)
    return tuple(result)


def _row_payload(
    frame: SyntheticFeatureFrameV1,
    row: SyntheticFeatureRowV1,
) -> dict[str, object]:
    return {
        "artifact_type": "task039e3_r2r_utility_evaluator_v1_synthetic_feature_row",
        "dataset_manifest_identity": frame.dataset_manifest_identity,
        "execution_mode": frame.execution_mode,
        "feature_values": [
            {"feature": pair[0], "value": pair[1]} for pair in row.feature_values
        ],
        "physical_row_index": row.physical_row_index,
        "source_file_identity": frame.source_file_identity,
        "split_identity": frame.split_identity,
        "synthetic_authority_identity": frame.synthetic_authority_identity,
        "timestamp_second": row.timestamp_second,
    }


def _frame_payload(frame: SyntheticFeatureFrameV1) -> dict[str, object]:
    return {
        "artifact_type": "task039e3_r2r_utility_evaluator_v1_synthetic_feature_frame",
        "dataset_manifest_identity": frame.dataset_manifest_identity,
        "execution_mode": frame.execution_mode,
        "feature_schema_authority_hash": frame.feature_schema_authority_hash,
        "ordered_features": list(frame.ordered_features),
        "rows": [
            {
                "physical_row_index": row.physical_row_index,
                "timestamp_second": row.timestamp_second,
                "feature_values": [list(pair) for pair in row.feature_values],
                "row_identity": row.row_identity,
            }
            for row in frame.rows
        ],
        "source_file_identity": frame.source_file_identity,
        "split_identity": frame.split_identity,
        "synthetic_authority_identity": frame.synthetic_authority_identity,
    }


def _envelope_payload(envelope: CanonicalOpportunityEnvelopeV1) -> dict[str, object]:
    return {
        "artifact_type": "task039e3_r2r_utility_evaluator_v1_canonical_opportunity_envelope",
        "execution_mode": "SYNTHETIC_CONTRACT_ONLY",
        "isolated_source_event_identity": envelope.isolated_source_event_identity,
        "opportunity_id": getattr(envelope.canonical_opportunity, "opportunity_id", None),
    }


def _census_payload(result: FullCensusResultV1) -> dict[str, object]:
    return {
        "artifact_type": "task039e3_r2r_utility_evaluator_v1_synthetic_full_census",
        "denominator_policy": result.denominator_policy,
        "execution_mode": result.execution_mode,
        "isolated_source_event_count": result.isolated_source_event_count,
        "opportunity_envelope_hashes": [
            item.envelope_hash for item in result.relation_opportunities
        ],
        "raw_source_event_count": result.raw_source_event_count,
        "relation_opportunity_count": len(result.relation_opportunities),
        "retained_source_event_count": result.retained_source_event_count,
        "source_census_identity": result.source_census_identity,
    }


class TupleSubclass(tuple):
    pass


class ListSubclass(list):
    pass


class LazyIterable:
    def __iter__(self):
        return iter(())


class UtilityEvaluatorV1R3IndependentInputCensusAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.v4_authority = _build_lower_v4_authority()
        cls.bundle = authority_module.build_evaluator_authority_bundle_v1(
            cls.v4_authority
        )
        cls.features = cls.v4_authority.feature_schema.union_features

        grouped: dict[tuple[str, str], list[object]] = {}
        for rule in cls.v4_authority.rule_descriptors:
            if rule.source in ORACLE_MAIN_SOURCES:
                grouped.setdefault((rule.source, rule.source_direction), []).append(rule)
        cls.event_source, cls.event_direction = max(
            grouped,
            key=lambda key: (len(grouped[key]), key),
        )
        cls.rules_by_source_direction = {
            key: tuple(value) for key, value in grouped.items()
        }

        frozen_values: dict[str, int | float] = {
            "source_step_threshold": 1.0,
            "source_stability_tolerance": 0.0,
            "target_noise_scale": 1.0,
            "source_pre_window_seconds": ORACLE_PRE,
            "source_post_window_seconds": ORACLE_POST,
            "minimum_source_stability_fraction": ORACLE_STABILITY,
            "source_refractory_seconds": ORACLE_REFRACTORY,
            "cross_source_isolation_radius_seconds": ORACLE_ISOLATION_RADIUS,
            "target_baseline_window_seconds": 5,
            "target_response_window_seconds": 3,
        }
        cls.main_records = tuple(
            authority_module.SyntheticNumericRecordV1(
                "SYNTHETIC_MAIN_420",
                rule.source,
                rule.relation_binding_hash,
                role,
                reference,
                frozen_values[role],
            )
            for rule in cls.v4_authority.rule_descriptors
            for role, reference in rule.numeric_reference_bindings
        )
        cls.supplement_records = tuple(
            authority_module.SyntheticNumericRecordV1(
                authority_module.SUPPLEMENT_PURPOSE,
                source,
                None,
                role,
                supplement.supplement_reference_identity_v1(source, role),
                1.0 if role == "source_step_threshold" else 0.0,
            )
            for source in ORACLE_SUPPLEMENT_SOURCES
            for role in ("source_step_threshold", "source_stability_tolerance")
        )

    def resolver(self):
        return authority_module.build_synthetic_numeric_resolver_v1(
            self.bundle,
            self.main_records,
            self.supplement_records,
        )

    def matrix(
        self,
        series_by_feature: dict[str, tuple[float, ...]] | None = None,
        *,
        row_count: int = 40,
    ) -> tuple[tuple[float, ...], ...]:
        supplied = series_by_feature or {}
        if any(len(series) != row_count for series in supplied.values()):
            raise AssertionError("independent fixture series length differs")
        return tuple(
            tuple(
                supplied.get(feature, (0.0,) * row_count)[row]
                for feature in self.features
            )
            for row in range(row_count)
        )

    def frame(
        self,
        series_by_feature: dict[str, tuple[float, ...]] | None = None,
        *,
        row_count: int = 40,
        start: int = 100,
    ) -> SyntheticFeatureFrameV1:
        return build_synthetic_feature_frame_v1(
            self.bundle,
            source_file_identity="hai-test1.csv",
            start_physical_row_index=start,
            rows=self.matrix(series_by_feature, row_count=row_count),
        )

    def full_census(
        self,
        series_by_feature: dict[str, tuple[float, ...]],
        *,
        row_count: int,
        start: int = 100,
    ) -> FullCensusResultV1:
        return enumerate_full_census_v1(
            self.frame(series_by_feature, row_count=row_count, start=start),
            self.bundle,
            self.resolver(),
        )

    def assert_frame_rejects(self, candidate: object) -> None:
        with self.assertRaises(UtilityEvaluatorV1Error):
            validate_synthetic_feature_frame_v1(
                candidate, self.bundle  # type: ignore[arg-type]
            )

    def test_lower_authorities_fix_exact_schema_source_and_portfolio_scope(self) -> None:
        self.assertEqual(tuple(self.bundle.main_sources), ORACLE_MAIN_SOURCES)
        self.assertEqual(
            tuple(self.bundle.supplement_sources), ORACLE_SUPPLEMENT_SOURCES
        )
        self.assertEqual(
            tuple(self.bundle.evaluator_source_census), ORACLE_SOURCE_UNIVERSE
        )
        self.assertEqual(
            tuple(self.v4_authority.feature_schema.source_features),
            ORACLE_SOURCE_UNIVERSE,
        )
        self.assertEqual(len(set(ORACLE_SOURCE_UNIVERSE)), 12)
        self.assertEqual(len(self.v4_authority.feature_schema.target_features), 10)
        self.assertEqual(len(self.features), 22)
        self.assertEqual(
            len(self.v4_authority.feature_schema.common_source_footprint), 9
        )
        self.assertEqual(
            len(self.v4_authority.feature_schema.common_feature_footprint), 19
        )
        self.assertEqual(len(self.v4_authority.rule_descriptors), 42)
        self.assertEqual(self.bundle.common_portfolio, "COMMON-42")
        self.assertIs(self.bundle.t2_utility_authorized, False)
        self.assertEqual(
            self.bundle.combined_source_census_contract_hash,
            ORACLE_COMBINED_CENSUS,
        )
        self.assertEqual(
            self.bundle.source_census_event_policy_hash, ORACLE_EVENT_POLICY
        )
        self.assertEqual(
            self.bundle.cross_source_isolation_policy_hash, ORACLE_ISOLATION_POLICY
        )

    def test_builder_rejects_noncanonical_outer_rows_values_and_coordinates(self) -> None:
        canonical = self.matrix(row_count=12)
        cases = (
            {"rows": list(canonical)},
            {"rows": (list(canonical[0]),) + canonical[1:]},
            {"rows": ((True,) + canonical[0][1:],) + canonical[1:]},
            {"rows": ((1,) + canonical[0][1:],) + canonical[1:]},
            {"rows": (("1.0",) + canonical[0][1:],) + canonical[1:]},
            {"rows": ((math.nan,) + canonical[0][1:],) + canonical[1:]},
            {"rows": ((math.inf,) + canonical[0][1:],) + canonical[1:]},
            {"rows": ((-math.inf,) + canonical[0][1:],) + canonical[1:]},
            {"rows": tuple(row[:-1] for row in canonical)},
            {"rows": tuple(row + (0.0,) for row in canonical)},
            {"source_file_identity": "UNKNOWN.csv"},
            {"start_physical_row_index": True},
            {"start_physical_row_index": -1},
            {"start_physical_row_index": 53_995},
            {"rows": ()},
        )
        self.assertEqual(len(cases), RAW_CASE_COUNTS["builder_boundary"])
        for override in cases:
            arguments = {
                "source_file_identity": "hai-test1.csv",
                "start_physical_row_index": 100,
                "rows": canonical,
                **override,
            }
            with self.subTest(override=override), self.assertRaises(
                UtilityEvaluatorV1Error
            ):
                build_synthetic_feature_frame_v1(self.bundle, **arguments)

    def test_inner_pair_container_scalar_and_hash_replay_attacks(self) -> None:
        canonical = self.frame(row_count=12)
        row = canonical.rows[0]
        first = row.feature_values[0]
        pairs: tuple[object, ...] = (
            [first[0], first[1]],
            TupleSubclass(first),
            ListSubclass(first),
            (value for value in first),
            (first[0],),
            (first[0], first[1], 2.0),
            (7, first[1]),
            (first[0], True),
            (first[0], 1),
            (first[0], "1.0"),
            (first[0], math.nan),
            (first[0], math.inf),
            (first[0], -math.inf),
        )
        for candidate_pair in pairs:
            mutated_row = replace(
                row,
                feature_values=(candidate_pair,) + row.feature_values[1:],  # type: ignore[arg-type]
            )
            candidate = replace(
                canonical, rows=(mutated_row,) + canonical.rows[1:]
            )
            with self.subTest(pair_type=type(candidate_pair).__name__):
                self.assert_frame_rejects(candidate)

        widened_row = replace(
            row,
            feature_values=([first[0], first[1]],) + row.feature_values[1:],  # type: ignore[arg-type]
        )
        preserved = replace(canonical, rows=(widened_row,) + canonical.rows[1:])
        self.assert_frame_rejects(preserved)
        self_rehashed = replace(
            preserved,
            frame_hash=stable_hash_v1(_frame_payload(preserved)),
        )
        self.assert_frame_rejects(self_rehashed)
        self.assertEqual(len(pairs) + 2, RAW_CASE_COUNTS["inner_pairs"])

    def test_frame_schema_row_provenance_and_self_hash_attacks(self) -> None:
        canonical = self.frame(row_count=12)
        row0, row1 = canonical.rows[:2]
        values = row0.feature_values
        row_mutations = (
            replace(row0, feature_values=values[1:]),
            replace(row0, feature_values=values + (values[-1],)),
            replace(row0, feature_values=(values[0],) + values),
            replace(row0, feature_values=tuple(reversed(values))),
            replace(row0, physical_row_index=row0.physical_row_index + 1),
            replace(row0, timestamp_second=row0.timestamp_second + 1),
            replace(row0, row_identity="b" * 64),
        )
        frame_mutations: list[object] = [
            replace(canonical, ordered_features=canonical.ordered_features[:-1]),
            replace(canonical, ordered_features=canonical.ordered_features + ("EXTRA",)),
            replace(
                canonical,
                ordered_features=(canonical.ordered_features[0],)
                + canonical.ordered_features,
            ),
            replace(
                canonical, ordered_features=tuple(reversed(canonical.ordered_features))
            ),
            replace(canonical, rows=(row0, row0) + canonical.rows[2:]),
            replace(canonical, rows=canonical.rows[1:]),
            replace(canonical, rows=(row1, row0) + canonical.rows[2:]),
            replace(canonical, rows=list(canonical.rows)),  # type: ignore[arg-type]
            replace(canonical, dataset_manifest_identity="wrong-dataset"),
            replace(canonical, split_identity="wrong-split"),
            replace(canonical, source_file_identity="UNKNOWN.csv"),
            replace(canonical, feature_schema_authority_hash="b" * 64),
            replace(canonical, frame_hash="b" * 64),
        ]
        frame_mutations.extend(
            replace(canonical, rows=(row,) + canonical.rows[1:])
            for row in row_mutations
        )
        self.assertEqual(len(frame_mutations) + 1, RAW_CASE_COUNTS["frame_replay"])
        for candidate in frame_mutations:
            with self.subTest(candidate=repr(candidate)[:80]):
                self.assert_frame_rejects(candidate)

        # An independently recomputed row and frame hash cannot authorize a
        # semantic coordinate mutation.
        moved = replace(
            row0,
            physical_row_index=row0.physical_row_index + 2,
            timestamp_second=row0.timestamp_second + 2,
            row_identity="",
        )
        moved = replace(moved, row_identity=stable_hash_v1(_row_payload(canonical, moved)))
        moved_frame = replace(canonical, rows=(moved,) + canonical.rows[1:])
        moved_frame = replace(
            moved_frame, frame_hash=stable_hash_v1(_frame_payload(moved_frame))
        )
        self.assert_frame_rejects(moved_frame)

    def test_feature_access_rejects_unknown_feature_and_outside_coordinate(self) -> None:
        frame = self.frame(row_count=12)
        cases = (
            lambda: feature_series_v1(frame, self.bundle, "UNKNOWN"),
            lambda: feature_value_v1(
                frame,
                self.bundle,
                physical_row_index=99,
                feature=self.features[0],
            ),
            lambda: feature_value_v1(
                frame,
                self.bundle,
                physical_row_index=100,
                feature="UNKNOWN",
            ),
        )
        self.assertEqual(len(cases), RAW_CASE_COUNTS["lookup"])
        for case in cases:
            with self.subTest(case=case), self.assertRaises(UtilityEvaluatorV1Error):
                case()

    def test_independent_eleven_case_source_event_oracle_matches_production(self) -> None:
        sign = 1.0 if self.event_direction == "step_up" else -1.0
        cases = {
            "clean": _step_series(length=40, index=10, after=2.0 * sign),
            "exact_threshold_and_stability": (
                0.0,
                0.0,
                0.0,
                0.0,
                0.5 * sign,
                sign,
                sign,
                sign,
                sign,
                1.5 * sign,
            ),
            "below_threshold": _step_series(length=40, index=10, after=0.5 * sign),
            "unstable": tuple(2.0 * sign if row % 2 else 0.0 for row in range(40)),
            "within_refractory": _piecewise_series(
                40, ((10, 2.0 * sign), (18, 4.0 * sign))
            ),
            "outside_refractory": _piecewise_series(
                50, ((10, 2.0 * sign), (30, 4.0 * sign))
            ),
            "chained_cluster": _piecewise_series(
                50, ((10, sign), (20, 3.0 * sign), (30, 6.0 * sign))
            ),
            "amplitude_winner": _piecewise_series(
                40, ((10, sign), (18, 5.0 * sign))
            ),
            "amplitude_tie": _piecewise_series(
                40, ((10, 2.0 * sign), (18, 0.0))
            ),
            "left_boundary": _step_series(length=40, index=ORACLE_PRE, after=2.0 * sign),
            "right_boundary": _step_series(
                length=40, index=40 - ORACLE_POST, after=2.0 * sign
            ),
        }
        self.assertEqual(len(cases), RAW_CASE_COUNTS["source_event_oracle"])
        for name, series in cases.items():
            expected_candidates = _oracle_candidates(series, 1.0, 0.0)
            expected_retained = _oracle_cluster(expected_candidates)
            observed = self.full_census(
                {self.event_source: series},
                row_count=len(series),
                start=1000,
            )
            expected_rows: list[int] = []
            for local_index, amplitude in expected_retained:
                direction = "step_up" if amplitude > 0.0 else "step_down"
                relation_count = len(
                    self.rules_by_source_direction.get(
                        (self.event_source, direction), ()
                    )
                )
                expected_rows.extend([1000 + local_index] * relation_count)
            observed_rows = [
                item.canonical_opportunity.physical_row_index
                for item in observed.relation_opportunities
            ]
            with self.subTest(case=name):
                self.assertEqual(observed.raw_source_event_count, len(expected_candidates))
                self.assertEqual(
                    observed.retained_source_event_count, len(expected_retained)
                )
                self.assertEqual(
                    observed.isolated_source_event_count, len(expected_retained)
                )
                self.assertEqual(Counter(observed_rows), Counter(expected_rows))

    def test_all_supplement_sources_and_radius_boundaries_drive_isolation(self) -> None:
        sign = 1.0 if self.event_direction == "step_up" else -1.0
        main_index = 20
        offsets = (-3, -2, -1, 1, 2, 3)
        case_count = 0
        for supplement_source in ORACLE_SUPPLEMENT_SOURCES:
            for offset in offsets:
                supplement_index = main_index + offset
                retained = {
                    source: (
                        (main_index,)
                        if source == self.event_source
                        else (supplement_index,)
                        if source == supplement_source
                        else ()
                    )
                    for source in ORACLE_SOURCE_UNIVERSE
                }
                expected_main_isolated = abs(offset) > ORACLE_ISOLATION_RADIUS
                self.assertEqual(
                    _oracle_isolated(self.event_source, main_index, retained),
                    expected_main_isolated,
                )
                result = self.full_census(
                    {
                        self.event_source: _step_series(
                            length=50, index=main_index, after=2.0 * sign
                        ),
                        supplement_source: _step_series(
                            length=50, index=supplement_index, after=2.0
                        ),
                    },
                    row_count=50,
                    start=3000,
                )
                with self.subTest(source=supplement_source, offset=offset):
                    self.assertEqual(result.retained_source_event_count, 2)
                    self.assertEqual(
                        result.isolated_source_event_count,
                        2 if expected_main_isolated else 0,
                    )
                    if not expected_main_isolated:
                        self.assertEqual(result.relation_opportunities, ())
                    else:
                        self.assertGreater(len(result.relation_opportunities), 0)
                case_count += 1
        self.assertEqual(case_count, RAW_CASE_COUNTS["supplement_offsets"])

    def test_isolation_excludes_self_source_and_rejects_noncanonical_universes(self) -> None:
        # Oracle-level duplicate/self-source evidence: neither creates a
        # cross-source conflict.
        retained = {
            source: ((12, 12, 13) if source == self.event_source else ())
            for source in ORACLE_SOURCE_UNIVERSE
        }
        self.assertTrue(_oracle_isolated(self.event_source, 12, retained))

        # Exercise the production isolation loop with two same-source retained
        # events.  This patches only the lower pure derivation output and keeps
        # frame/bundle/resolver/census behavior under audit.
        frame = self.frame(row_count=40, start=5000)
        resolver = self.resolver()
        derived = {
            source: (
                (
                    RetainedSourceEventV3(source, 12, self.event_direction, 2.0 * (1.0 if self.event_direction == "step_up" else -1.0)),
                    RetainedSourceEventV3(source, 13, self.event_direction, 3.0 * (1.0 if self.event_direction == "step_up" else -1.0)),
                )
                if source == self.event_source
                else ()
            )
            for source in ORACLE_SOURCE_UNIVERSE
        }
        with patch.object(
            census_module,
            "derive_retained_source_events_v3",
            return_value=derived,
        ):
            result = enumerate_full_census_v1(frame, self.bundle, resolver)
        self.assertEqual(result.retained_source_event_count, 2)
        self.assertEqual(result.isolated_source_event_count, 2)

        missing = dict(retained)
        missing.pop(ORACLE_SUPPLEMENT_SOURCES[0])
        with self.assertRaises(AssertionError):
            _oracle_isolated(self.event_source, 12, missing)

        with self.assertRaises(TypeError):
            enumerate_full_census_v1(
                frame,
                self.bundle,
                resolver,
                isolation_sources=ORACLE_MAIN_SOURCES,
            )
        self.assertEqual(4, RAW_CASE_COUNTS["isolation_structure"])

    def test_supplement_events_never_expand_the_common_relation_portfolio(self) -> None:
        case_count = 0
        for source in ORACLE_SUPPLEMENT_SOURCES:
            series = _step_series(length=40, index=12, after=2.0)
            retained = _oracle_cluster(_oracle_candidates(series, 1.0, 0.0))
            result = self.full_census({source: series}, row_count=40)
            with self.subTest(source=source):
                self.assertEqual(result.retained_source_event_count, len(retained))
                self.assertEqual(result.isolated_source_event_count, len(retained))
                self.assertEqual(result.relation_opportunities, ())
            case_count += 1
        self.assertEqual(case_count, RAW_CASE_COUNTS["supplement_no_expansion"])

    def test_source_event_and_relation_opportunity_cardinality_remain_distinct(self) -> None:
        sign = 1.0 if self.event_direction == "step_up" else -1.0
        series = _step_series(length=40, index=12, after=2.0 * sign)
        expected_retained = _oracle_cluster(_oracle_candidates(series, 1.0, 0.0))
        expected_relations = len(
            self.rules_by_source_direction[(self.event_source, self.event_direction)]
        )
        self.assertEqual(len(expected_retained), 1)
        self.assertGreater(expected_relations, 1)
        observed = self.full_census({self.event_source: series}, row_count=40)
        self.assertEqual(observed.retained_source_event_count, 1)
        self.assertEqual(observed.isolated_source_event_count, 1)
        self.assertEqual(len(observed.relation_opportunities), expected_relations)
        self.assertNotEqual(
            observed.isolated_source_event_count,
            len(observed.relation_opportunities),
        )
        self.assertEqual(
            len(
                {
                    item.canonical_opportunity.relation_binding_hash
                    for item in observed.relation_opportunities
                }
            ),
            expected_relations,
        )
        self.assertEqual(1, RAW_CASE_COUNTS["cardinality_distinction"])

    def test_public_enumerator_exposes_zero_caller_census_or_denominator_controls(self) -> None:
        frame = self.frame(row_count=12)
        resolver = self.resolver()
        controls = (
            ("source_subset", ORACLE_MAIN_SOURCES),
            ("relation_subset", self.v4_authority.rule_descriptors[:39]),
            ("rule_library", self.v4_authority.rule_descriptors),
            ("numeric_registry", {}),
            ("opportunity_list", ()),
            ("sample_n", 1),
            ("max_opportunities", 1),
            ("denominator", 1),
            ("portfolio", "T2"),
            ("relation_subset", (item for item in self.v4_authority.rule_descriptors)),
            ("opportunity_list", LazyIterable()),
            ("source_subset", TupleSubclass(ORACLE_SOURCE_UNIVERSE)),
            ("source_subset", ListSubclass(ORACLE_SOURCE_UNIVERSE)),
            ("precomputed_census", object()),
            ("retained_events", {}),
            ("isolation_sources", ORACLE_SOURCE_UNIVERSE),
            ("caller_denominator_policy", ORACLE_DENOMINATOR_POLICY),
            ("relations", reversed(self.v4_authority.rule_descriptors)),
        )
        self.assertEqual(len(controls), RAW_CASE_COUNTS["caller_controls"])
        for name, value in controls:
            with self.subTest(control=name, value_type=type(value).__name__):
                with self.assertRaises(TypeError):
                    enumerate_full_census_v1(
                        frame,
                        self.bundle,
                        resolver,
                        **{name: value},
                    )

    def test_full_census_replay_rejects_forgery_reorder_and_count_conflation(self) -> None:
        sign = 1.0 if self.event_direction == "step_up" else -1.0
        frame = self.frame(
            {self.event_source: _step_series(length=40, index=12, after=2.0 * sign)},
            row_count=40,
        )
        resolver = self.resolver()
        canonical = enumerate_full_census_v1(frame, self.bundle, resolver)
        self.assertEqual(canonical.denominator_policy, ORACLE_DENOMINATOR_POLICY)
        self.assertEqual(
            validate_full_census_result_v1(canonical, frame, self.bundle, resolver),
            canonical.census_hash,
        )
        first = canonical.relation_opportunities[0]
        attacks: tuple[object, ...] = (
            replace(
                canonical,
                relation_opportunities=canonical.relation_opportunities[:-1],
            ),
            replace(
                canonical,
                relation_opportunities=canonical.relation_opportunities + (first,),
            ),
            replace(
                canonical,
                relation_opportunities=tuple(reversed(canonical.relation_opportunities)),
            ),
            replace(canonical, relation_opportunities=list(canonical.relation_opportunities)),  # type: ignore[arg-type]
            replace(canonical, denominator_policy="CALLER_DENOMINATOR"),
            replace(
                canonical,
                isolated_source_event_count=len(canonical.relation_opportunities),
            ),
            replace(
                canonical,
                retained_source_event_count=len(canonical.relation_opportunities),
            ),
            replace(
                canonical,
                raw_source_event_count=len(canonical.relation_opportunities),
            ),
            replace(canonical, source_census_identity="b" * 64),
            replace(canonical, execution_mode="SCIENTIFIC"),
            replace(canonical, census_hash="c" * 64),
        )
        self.assertEqual(len(attacks) + 1, RAW_CASE_COUNTS["census_forgery"])
        for candidate in attacks:
            with self.subTest(candidate=repr(candidate)[:90]), self.assertRaises(
                UtilityEvaluatorV1Error
            ):
                validate_full_census_result_v1(
                    candidate, frame, self.bundle, resolver  # type: ignore[arg-type]
                )

        forged = replace(
            canonical,
            relation_opportunities=canonical.relation_opportunities[:-1],
            census_hash="",
        )
        forged = replace(forged, census_hash=stable_hash_v1(_census_payload(forged)))
        with self.assertRaises(UtilityEvaluatorV1Error):
            validate_full_census_result_v1(forged, frame, self.bundle, resolver)

    def test_opportunity_attacks_use_corrected_envelope_boundary_not_v4_replace(self) -> None:
        sign = 1.0 if self.event_direction == "step_up" else -1.0
        frame = self.frame(
            {
                self.event_source: _piecewise_series(
                    50, ((10, 2.0 * sign), (30, 4.0 * sign))
                )
            },
            row_count=50,
        )
        resolver = self.resolver()
        canonical = enumerate_full_census_v1(frame, self.bundle, resolver)
        first = canonical.relation_opportunities[0]
        second = next(
            item
            for item in canonical.relation_opportunities
            if item.isolated_source_event_identity
            != first.isolated_source_event_identity
        )
        self.assertEqual(
            validate_opportunity_envelope_v1(
                first, canonical, frame, self.bundle, resolver
            ),
            first.envelope_hash,
        )

        # V4 CanonicalOpportunityV4 remains untouched and factory-issued.  The
        # attack pairs canonical opportunity content with a foreign evaluator
        # isolation envelope, then optionally self-hashes the envelope.
        paired = CanonicalOpportunityEnvelopeV1(
            first.isolated_source_event_identity,
            second.canonical_opportunity,
            "",
        )
        paired = replace(paired, envelope_hash=stable_hash_v1(_envelope_payload(paired)))
        attacks = (
            replace(first, isolated_source_event_identity="b" * 64),
            replace(first, envelope_hash="c" * 64),
            paired,
            CanonicalOpportunityEnvelopeV1(
                second.isolated_source_event_identity,
                first.canonical_opportunity,
                first.envelope_hash,
            ),
            object(),
        )
        self.assertEqual(len(attacks), RAW_CASE_COUNTS["envelope_membership"])
        for candidate in attacks:
            with self.subTest(candidate_type=type(candidate).__name__), self.assertRaises(
                UtilityEvaluatorV1Error
            ):
                validate_opportunity_envelope_v1(
                    candidate,  # type: ignore[arg-type]
                    canonical,
                    frame,
                    self.bundle,
                    resolver,
                )

    def test_resolver_exact_twelve_source_closure_and_types_fail_closed(self) -> None:
        frame = self.frame(row_count=12)
        mutations = (
            ("omit_main_threshold", ORACLE_MAIN_SOURCES[0], "source_step_threshold", None),
            ("omit_main_tolerance", ORACLE_MAIN_SOURCES[0], "source_stability_tolerance", None),
            ("omit_supplement_threshold", ORACLE_SUPPLEMENT_SOURCES[0], "source_step_threshold", None),
            ("omit_supplement_tolerance", ORACLE_SUPPLEMENT_SOURCES[0], "source_stability_tolerance", None),
            ("insert_unknown", "UNKNOWN", "source_step_threshold", 1.0),
            ("wrong_role", ORACLE_SUPPLEMENT_SOURCES[0], "target_noise_scale", 1.0),
            ("threshold_int", ORACLE_MAIN_SOURCES[0], "source_step_threshold", 1),
            ("threshold_bool", ORACLE_MAIN_SOURCES[0], "source_step_threshold", True),
            ("tolerance_negative", ORACLE_MAIN_SOURCES[0], "source_stability_tolerance", -1.0),
            ("tolerance_nan", ORACLE_SUPPLEMENT_SOURCES[0], "source_stability_tolerance", math.nan),
        )
        self.assertEqual(len(mutations), RAW_CASE_COUNTS["resolver_closure"])
        for name, source, role, value in mutations:
            resolver = self.resolver()
            key = (source, role)
            if value is None:
                del resolver._source_values[key]
            else:
                resolver._source_values[key] = value
            with self.subTest(case=name), self.assertRaises(UtilityEvaluatorV1Error):
                enumerate_full_census_v1(frame, self.bundle, resolver)

    def test_lane_coverage_floor_and_zero_acceptance_contract(self) -> None:
        self.assertGreaterEqual(len(INPUT_SEMANTIC_CLASSES), 15)
        self.assertGreaterEqual(len(SOURCE_CENSUS_SEMANTIC_CLASSES), 20)
        self.assertGreaterEqual(len(OPPORTUNITY_SEMANTIC_CLASSES), 12)
        self.assertGreaterEqual(INDEPENDENT_UNIQUE_SEMANTIC_CLASSES, 75)
        self.assertEqual(INDEPENDENT_UNIQUE_SEMANTIC_CLASSES, 90)
        self.assertGreaterEqual(INDEPENDENT_RAW_ADVERSARIAL_CASES, 115)
        self.assertEqual(INDEPENDENT_RAW_ADVERSARIAL_CASES, 136)
        self.assertEqual(EXPECTED_ACCEPTED_INVALID_CASES, 0)


if __name__ == "__main__":
    unittest.main()
