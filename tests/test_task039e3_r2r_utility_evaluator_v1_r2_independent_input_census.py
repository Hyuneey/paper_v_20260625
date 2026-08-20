"""Independent R2 input, source-census, isolation, and opportunity audit.

The constants and small oracle functions below are frozen from the committed
lower Protocol V2/V3/V4 and source-census-supplement authorities.  They do not
call evaluator event/census helpers to calculate expected answers.  Production
APIs are used only after the independent expectations have been derived.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
import json
import math
from pathlib import Path
import statistics
import unittest

import paperworks.v6.task039e3_r2r_utility_evaluator_authority_v1 as evaluator
import paperworks.v6.task039e3_r2r_utility_evaluator_census_v1 as census_module
import paperworks.v6.task039e3_r2r_utility_evaluator_input_v1 as input_module
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
    FullCensusResultV1,
    SyntheticFeatureFrameV1,
    SyntheticFeatureRowV1,
    UtilityEvaluatorV1Error,
    stable_hash_v1,
)
from paperworks.v6 import task039e3_r2r_utility_protocol_v4 as v4
import paperworks.v6.task039e3_r2r_utility_source_census_supplement_v1 as supplement


# Independent lower-authority oracle.  Keep these literals separate from the
# evaluator constants so an evaluator-side substitution cannot redefine the
# expected audit answer.
ORACLE_SOURCE_PRE_WINDOW = 5
ORACLE_SOURCE_POST_WINDOW = 5
ORACLE_MINIMUM_STABILITY_FRACTION = 0.8
ORACLE_SOURCE_REFRACTORY_SECONDS = 10
ORACLE_CROSS_SOURCE_ISOLATION_RADIUS_SECONDS = 2
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

INPUT_SCHEMA_SEMANTIC_CLASSES = (
    "outer rows exact tuple",
    "row values exact tuple",
    "feature pair exact tuple",
    "feature pair tuple subclass",
    "feature pair list subclass",
    "feature pair generator",
    "feature pair cardinality",
    "feature name exact string",
    "feature value exact float",
    "boolean value rejection",
    "integer value rejection",
    "string-number rejection",
    "NaN rejection",
    "positive infinity rejection",
    "negative infinity rejection",
    "feature missing",
    "feature insertion",
    "feature duplication",
    "feature reorder",
    "row duplication",
    "row removal",
    "row reorder",
    "physical coordinate mutation",
    "timestamp mutation",
    "dataset mutation",
    "split mutation",
    "file mutation",
    "schema authority mutation",
    "row identity replay",
    "frame identity replay",
)

SOURCE_CENSUS_ISOLATION_SEMANTIC_CLASSES = (
    "exact nine MAIN sources",
    "exact three supplement sources",
    "exact twelve-source union",
    "pre-window boundary",
    "post-window boundary",
    "exact threshold inclusion",
    "below-threshold exclusion",
    "minimum stability qualification",
    "unstable-window exclusion",
    "single-link refractory clustering",
    "inside-refractory merge",
    "outside-refractory split",
    "chained cluster",
    "largest absolute amplitude retention",
    "exact amplitude tie earliest index",
    "inclusive left isolation radius",
    "inclusive right isolation radius",
    "outside left isolation radius",
    "outside right isolation radius",
    "symmetric cross-source isolation",
    "own-source exclusion",
    "local-to-physical coordinate mapping",
    "P1_FCV02Z isolation participation",
    "P1_PCV02Z isolation participation",
    "P1_PP04 isolation participation",
    "supplement-only relation exclusion",
    "source-census resolver closure",
)

OPPORTUNITY_SEMANTIC_CLASSES = (
    "COMMON-42 only",
    "T2-39 prohibited",
    "source subset prohibited",
    "relation subset prohibited",
    "caller rule library prohibited",
    "caller numeric registry prohibited",
    "caller opportunity list prohibited",
    "caller sample size prohibited",
    "caller max opportunities prohibited",
    "caller denominator prohibited",
    "generator relation input prohibited",
    "lazy opportunity input prohibited",
    "container subclass authority prohibited",
    "precomputed opportunity injection prohibited",
    "self-rehashed fake census prohibited",
    "duplicate opportunity prohibited",
    "missing opportunity prohibited",
    "foreign relation opportunity prohibited",
    "source-event and opportunity counts distinct",
    "one source event expands to all applicable COMMON relations",
)

INDEPENDENT_INPUT_SCHEMA_ATTACKS = len(INPUT_SCHEMA_SEMANTIC_CLASSES)
INDEPENDENT_SOURCE_CENSUS_ISOLATION_ATTACKS = len(
    SOURCE_CENSUS_ISOLATION_SEMANTIC_CLASSES
)
INDEPENDENT_OPPORTUNITY_ATTACKS = len(OPPORTUNITY_SEMANTIC_CLASSES)
INDEPENDENT_UNIQUE_SEMANTIC_CLASSES = (
    INDEPENDENT_INPUT_SCHEMA_ATTACKS
    + INDEPENDENT_SOURCE_CENSUS_ISOLATION_ATTACKS
    + INDEPENDENT_OPPORTUNITY_ATTACKS
)
INDEPENDENT_RAW_ADVERSARIAL_CASES = 100
EXPECTED_ACCEPTED_INVALID_CASES = 0

ROOT = Path(__file__).resolve().parents[1]


def _load(relative: str) -> dict[str, object]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def _build_lower_v4_authority() -> v4.UtilityProtocolV4CanonicalAuthority:
    """Reconstruct current V4 from committed lower, public authority inputs."""

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
    """Reconstruct threshold and stability candidates without production code."""

    result: list[tuple[int, float]] = []
    for index in range(
        ORACLE_SOURCE_PRE_WINDOW,
        len(series) - ORACLE_SOURCE_POST_WINDOW + 1,
    ):
        pre = series[index - ORACLE_SOURCE_PRE_WINDOW : index]
        post = series[index : index + ORACLE_SOURCE_POST_WINDOW]
        pre_level = float(statistics.median(pre))
        post_level = float(statistics.median(post))
        amplitude = post_level - pre_level
        pre_stable = (
            sum(abs(value - pre_level) <= tolerance for value in pre)
            / ORACLE_SOURCE_PRE_WINDOW
        )
        post_stable = (
            sum(abs(value - post_level) <= tolerance for value in post)
            / ORACLE_SOURCE_POST_WINDOW
        )
        if (
            amplitude != 0.0
            and abs(amplitude) >= threshold
            and pre_stable >= ORACLE_MINIMUM_STABILITY_FRACTION
            and post_stable >= ORACLE_MINIMUM_STABILITY_FRACTION
        ):
            result.append((index, amplitude))
    return tuple(result)


def _oracle_cluster(
    candidates: tuple[tuple[int, float], ...]
) -> tuple[tuple[int, float], ...]:
    """Single-link cluster; keep largest magnitude then earliest index."""

    if not candidates:
        return ()
    ordered = tuple(sorted(candidates))
    clusters: list[list[tuple[int, float]]] = [[ordered[0]]]
    for candidate in ordered[1:]:
        if candidate[0] - clusters[-1][-1][0] <= ORACLE_SOURCE_REFRACTORY_SECONDS:
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
    """All-twelve, symmetric, inclusive-radius isolation replay."""

    if tuple(retained) != ORACLE_SOURCE_UNIVERSE:
        raise AssertionError("audit oracle requires canonical source ordering")
    return not any(
        abs(index - other) <= ORACLE_CROSS_SOURCE_ISOLATION_RADIUS_SECONDS
        for other_source, indices in retained.items()
        if other_source != source
        for other in indices
    )


def _step_series(
    *, length: int, index: int, before: float = 0.0, after: float = 1.0
) -> tuple[float, ...]:
    return tuple(before if offset < index else after for offset in range(length))


def _piecewise_series(
    length: int, transitions: tuple[tuple[int, float], ...]
) -> tuple[float, ...]:
    values = [0.0] * length
    for index, level in transitions:
        for offset in range(index, length):
            values[offset] = float(level)
    return tuple(values)


# Expected event and cardinality values are always supplied by the independent
# oracle above.  The fixture factory merely materializes those cases through
# the public synthetic evaluator boundary.


class UtilityEvaluatorV1R2IndependentInputCensusAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.authority = _build_lower_v4_authority()
        cls.bundle = evaluator.build_evaluator_authority_bundle_v1(cls.authority)
        cls.features = cls.authority.feature_schema.union_features

        grouped: dict[tuple[str, str], list[object]] = {}
        for rule in cls.authority.rule_descriptors:
            if rule.source in ORACLE_MAIN_SOURCES:
                grouped.setdefault((rule.source, rule.source_direction), []).append(rule)
        cls.event_source, cls.event_direction = max(
            grouped, key=lambda key: len(grouped[key])
        )
        cls.rules_by_source_direction = {
            key: tuple(value) for key, value in grouped.items()
        }

        main_records = []
        fixed_values: dict[str, int | float] = {
            "source_step_threshold": 1.0,
            "source_stability_tolerance": 0.0,
            "target_noise_scale": 1.0,
            "source_pre_window_seconds": ORACLE_SOURCE_PRE_WINDOW,
            "source_post_window_seconds": ORACLE_SOURCE_POST_WINDOW,
            "minimum_source_stability_fraction": ORACLE_MINIMUM_STABILITY_FRACTION,
            "source_refractory_seconds": ORACLE_SOURCE_REFRACTORY_SECONDS,
            "cross_source_isolation_radius_seconds": (
                ORACLE_CROSS_SOURCE_ISOLATION_RADIUS_SECONDS
            ),
            "target_baseline_window_seconds": 5,
            "target_response_window_seconds": 3,
        }
        for rule in cls.authority.rule_descriptors:
            for role, reference in rule.numeric_reference_bindings:
                main_records.append(
                    evaluator.SyntheticNumericRecordV1(
                        "SYNTHETIC_MAIN_420",
                        rule.source,
                        rule.relation_binding_hash,
                        role,
                        reference,
                        fixed_values[role],
                    )
                )
        cls.main_records = tuple(main_records)
        cls.supplement_records = tuple(
            evaluator.SyntheticNumericRecordV1(
                evaluator.SUPPLEMENT_PURPOSE,
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
        return evaluator.build_synthetic_numeric_resolver_v1(
            self.bundle, self.main_records, self.supplement_records
        )

    def matrix(
        self,
        series_by_feature: dict[str, tuple[float, ...]] | None = None,
        *,
        row_count: int = 40,
    ) -> tuple[tuple[float, ...], ...]:
        series_by_feature = series_by_feature or {}
        if any(len(series) != row_count for series in series_by_feature.values()):
            raise AssertionError("audit series length differs")
        return tuple(
            tuple(
                series_by_feature.get(feature, (0.0,) * row_count)[row]
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

    def census(
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

    def assert_frame_rejects(self, frame: object) -> None:
        with self.assertRaises(UtilityEvaluatorV1Error):
            validate_synthetic_feature_frame_v1(frame, self.bundle)  # type: ignore[arg-type]

    def test_lower_authority_source_schema_and_policy_exact(self) -> None:
        self.assertEqual(tuple(self.bundle.main_sources), ORACLE_MAIN_SOURCES)
        self.assertEqual(tuple(self.bundle.supplement_sources), ORACLE_SUPPLEMENT_SOURCES)
        self.assertEqual(tuple(self.authority.feature_schema.source_features), ORACLE_SOURCE_UNIVERSE)
        self.assertEqual(tuple(self.bundle.evaluator_source_census), ORACLE_SOURCE_UNIVERSE)
        self.assertEqual(len(set(ORACLE_SOURCE_UNIVERSE)), 12)
        self.assertEqual(len(self.authority.feature_schema.target_features), 10)
        self.assertEqual(len(self.authority.feature_schema.union_features), 22)
        self.assertEqual(len(self.authority.feature_schema.common_source_footprint), 9)
        self.assertEqual(len(self.authority.feature_schema.common_feature_footprint), 19)
        self.assertEqual(len(self.authority.rule_descriptors), 42)
        self.assertEqual(self.bundle.common_portfolio, "COMMON-42")
        self.assertIs(self.bundle.t2_utility_authorized, False)

    def test_input_builder_strict_scalar_container_attacks(self) -> None:
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
            {"source_file_identity": "hai-train1.csv"},
            {"start_physical_row_index": True},
            {"start_physical_row_index": -1},
            {"start_physical_row_index": 53_995},
        )
        for override in cases:
            kwargs = {
                "source_file_identity": "hai-test1.csv",
                "start_physical_row_index": 100,
                "rows": canonical,
                **override,
            }
            with self.subTest(override=override), self.assertRaises(UtilityEvaluatorV1Error):
                build_synthetic_feature_frame_v1(self.bundle, **kwargs)

    def test_inner_feature_pair_exact_type_and_value_attacks(self) -> None:
        class TuplePair(tuple):
            pass

        class ListPair(list):
            pass

        canonical = self.frame(row_count=12)
        row = canonical.rows[0]
        first = row.feature_values[0]
        pair_cases: tuple[object, ...] = (
            [first[0], first[1]],
            TuplePair(first),
            ListPair(first),
            (item for item in first),
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
        for pair in pair_cases:
            widened = replace(
                row,
                feature_values=(pair,) + row.feature_values[1:],  # type: ignore[arg-type]
            )
            candidate = replace(canonical, rows=(widened,) + canonical.rows[1:])
            with self.subTest(pair_type=type(pair).__name__):
                self.assert_frame_rejects(candidate)

        widened_values = list(row.feature_values)
        widened_values[0] = [first[0], first[1]]  # type: ignore[list-item]
        widened_row = replace(row, feature_values=tuple(widened_values))
        preserved = replace(canonical, rows=(widened_row,) + canonical.rows[1:])
        recomputed = replace(
            preserved,
            frame_hash=stable_hash_v1(input_module._frame_payload_v1(preserved)),
        )
        self.assertEqual(widened_row.row_identity, row.row_identity)
        self.assert_frame_rejects(preserved)
        self.assert_frame_rejects(recomputed)

    def test_frame_schema_row_and_provenance_mutations(self) -> None:
        canonical = self.frame(row_count=12)
        row0, row1 = canonical.rows[:2]
        feature_values = row0.feature_values
        row_mutations = (
            replace(row0, feature_values=feature_values[1:]),
            replace(row0, feature_values=feature_values + (feature_values[-1],)),
            replace(row0, feature_values=(feature_values[0],) + feature_values),
            replace(row0, feature_values=tuple(reversed(feature_values))),
            replace(row0, physical_row_index=row0.physical_row_index + 1),
            replace(row0, timestamp_second=row0.timestamp_second + 1),
            replace(row0, row_identity="b" * 64),
        )
        frame_cases: list[object] = [
            replace(canonical, ordered_features=canonical.ordered_features[:-1]),
            replace(canonical, ordered_features=canonical.ordered_features + ("UNKNOWN",)),
            replace(
                canonical,
                ordered_features=(canonical.ordered_features[0],)
                + canonical.ordered_features,
            ),
            replace(canonical, ordered_features=tuple(reversed(canonical.ordered_features))),
            replace(canonical, rows=(row0, row0) + canonical.rows[2:]),
            replace(canonical, rows=canonical.rows[1:]),
            replace(canonical, rows=(row1, row0) + canonical.rows[2:]),
            replace(canonical, rows=list(canonical.rows)),  # type: ignore[arg-type]
            replace(canonical, dataset_manifest_identity="wrong"),
            replace(canonical, split_identity="wrong"),
            replace(canonical, source_file_identity="hai-test2.csv"),
            replace(canonical, feature_schema_authority_hash="b" * 64),
            replace(canonical, frame_hash="b" * 64),
        ]
        frame_cases.extend(
            replace(canonical, rows=(mutation,) + canonical.rows[1:])
            for mutation in row_mutations
        )
        for candidate in frame_cases:
            with self.subTest(candidate_type=type(candidate).__name__):
                self.assert_frame_rejects(candidate)

    def test_valid_frame_replays_exact_values_coordinates_and_hash(self) -> None:
        series = _step_series(length=20, index=10, after=2.0)
        frame = self.frame({self.event_source: series}, row_count=20, start=700)
        self.assertEqual(
            validate_synthetic_feature_frame_v1(frame, self.bundle), frame.frame_hash
        )
        self.assertEqual(feature_series_v1(frame, self.bundle, self.event_source), series)
        self.assertEqual(
            feature_value_v1(
                frame,
                self.bundle,
                physical_row_index=719,
                feature=self.event_source,
            ),
            series[-1],
        )
        self.assertEqual(
            tuple(row.physical_row_index for row in frame.rows), tuple(range(700, 720))
        )
        self.assertEqual(
            tuple(row.timestamp_second for row in frame.rows), tuple(range(700, 720))
        )

    def test_independent_dynamic_source_event_oracle_cases(self) -> None:
        sign = 1.0 if self.event_direction == "step_up" else -1.0
        cases = {
            "clean": _step_series(length=40, index=10, after=2.0 * sign),
            "exact_threshold": _step_series(length=40, index=10, after=sign),
            "below_threshold": _step_series(length=40, index=10, after=0.5 * sign),
            "unstable": tuple(2.0 * sign if index % 2 else 0.0 for index in range(40)),
            "inside_refractory": _piecewise_series(
                40, ((10, 2.0 * sign), (18, 4.0 * sign))
            ),
            "outside_refractory": _piecewise_series(
                50, ((10, 2.0 * sign), (30, 4.0 * sign))
            ),
            "chained_cluster": _piecewise_series(
                50, ((10, 1.0 * sign), (20, 3.0 * sign), (30, 6.0 * sign))
            ),
            "amplitude_winner": _piecewise_series(
                40, ((10, 1.0 * sign), (18, 4.0 * sign))
            ),
            "amplitude_tie_earliest": _piecewise_series(
                40, ((10, 2.0 * sign), (18, 0.0))
            ),
            "start_boundary": _step_series(length=40, index=4, after=2.0 * sign),
            "end_boundary": _step_series(length=40, index=36, after=2.0 * sign),
        }
        for name, series in cases.items():
            expected_candidates = _oracle_candidates(series, 1.0, 0.0)
            expected_retained = _oracle_cluster(expected_candidates)
            result = self.census(
                {self.event_source: series}, row_count=len(series), start=1000
            )
            expected_rows: list[int] = []
            for index, amplitude in expected_retained:
                direction = "step_up" if amplitude > 0.0 else "step_down"
                expected_rows.extend(
                    [1000 + index]
                    * len(self.rules_by_source_direction.get((self.event_source, direction), ()))
                )
            observed_rows = [
                envelope.canonical_opportunity.physical_row_index
                for envelope in result.relation_opportunities
            ]
            with self.subTest(case=name):
                self.assertEqual(result.raw_source_event_count, len(expected_candidates))
                self.assertEqual(result.retained_source_event_count, len(expected_retained))
                self.assertEqual(result.isolated_source_event_count, len(expected_retained))
                self.assertEqual(Counter(observed_rows), Counter(expected_rows))

    def test_all_three_supplement_sources_participate_in_isolation(self) -> None:
        sign = 1.0 if self.event_direction == "step_up" else -1.0
        main_series = _step_series(length=40, index=12, after=2.0 * sign)
        main_retained = _oracle_cluster(_oracle_candidates(main_series, 1.0, 0.0))
        self.assertEqual(len(main_retained), 1)
        for supplement_source in ORACLE_SUPPLEMENT_SOURCES:
            supplement_series = _step_series(length=40, index=12, after=2.0)
            retained_map = {
                source: (
                    (main_retained[0][0],)
                    if source == self.event_source
                    else (12,)
                    if source == supplement_source
                    else ()
                )
                for source in ORACLE_SOURCE_UNIVERSE
            }
            self.assertFalse(
                _oracle_isolated(self.event_source, main_retained[0][0], retained_map)
            )
            result = self.census(
                {
                    self.event_source: main_series,
                    supplement_source: supplement_series,
                },
                row_count=40,
                start=2000,
            )
            with self.subTest(supplement_source=supplement_source):
                self.assertEqual(result.retained_source_event_count, 2)
                self.assertEqual(result.isolated_source_event_count, 0)
                self.assertEqual(result.relation_opportunities, ())

    def test_isolation_radius_inclusive_symmetric_and_physical_coordinates(self) -> None:
        sign = 1.0 if self.event_direction == "step_up" else -1.0
        main_index = 15
        cases = (
            ("left_inclusive", main_index - 2, False),
            ("right_inclusive", main_index + 2, False),
            ("left_outside", main_index - 3, True),
            ("right_outside", main_index + 3, True),
        )
        for name, supplement_index, expected_isolated in cases:
            retained = {
                source: (
                    (main_index,)
                    if source == self.event_source
                    else (supplement_index,)
                    if source == "P1_PP04"
                    else ()
                )
                for source in ORACLE_SOURCE_UNIVERSE
            }
            self.assertEqual(
                _oracle_isolated(self.event_source, main_index, retained), expected_isolated
            )
            result = self.census(
                {
                    self.event_source: _step_series(
                        length=45, index=main_index, after=2.0 * sign
                    ),
                    "P1_PP04": _step_series(
                        length=45, index=supplement_index, after=2.0
                    ),
                },
                row_count=45,
                start=4000,
            )
            with self.subTest(case=name):
                self.assertEqual(
                    result.isolated_source_event_count,
                    2 if expected_isolated else 0,
                )
                if not expected_isolated:
                    self.assertEqual(result.relation_opportunities, ())

    def test_supplement_events_never_expand_common_relations(self) -> None:
        for source in ORACLE_SUPPLEMENT_SOURCES:
            series = _step_series(length=40, index=12, after=2.0)
            expected = _oracle_cluster(_oracle_candidates(series, 1.0, 0.0))
            result = self.census({source: series}, row_count=40)
            with self.subTest(source=source):
                self.assertEqual(result.retained_source_event_count, len(expected))
                self.assertEqual(result.isolated_source_event_count, len(expected))
                self.assertEqual(result.relation_opportunities, ())

    def test_source_event_and_relation_opportunity_cardinality_are_distinct(self) -> None:
        sign = 1.0 if self.event_direction == "step_up" else -1.0
        series = _step_series(length=40, index=12, after=2.0 * sign)
        expected_retained = _oracle_cluster(_oracle_candidates(series, 1.0, 0.0))
        expected_relations = len(
            self.rules_by_source_direction[(self.event_source, self.event_direction)]
        )
        self.assertGreater(expected_relations, 1)
        result = self.census({self.event_source: series}, row_count=40)
        self.assertEqual(len(expected_retained), 1)
        self.assertEqual(result.retained_source_event_count, 1)
        self.assertEqual(result.isolated_source_event_count, 1)
        self.assertEqual(len(result.relation_opportunities), expected_relations)
        self.assertNotEqual(
            result.isolated_source_event_count, len(result.relation_opportunities)
        )
        self.assertEqual(
            len({item.canonical_opportunity.relation_binding_hash for item in result.relation_opportunities}),
            expected_relations,
        )

    def test_caller_has_no_census_or_denominator_controls(self) -> None:
        frame = self.frame(row_count=12)

        class TupleSubclass(tuple):
            pass

        class LazyIterable:
            def __iter__(self):
                return iter(())

        cases = (
            ("source_subset", ORACLE_SOURCE_UNIVERSE[:9]),
            ("relation_subset", self.authority.rule_descriptors[:39]),
            ("rule_library", self.authority.rule_descriptors),
            ("numeric_registry", {}),
            ("opportunity_list", ()),
            ("sample_n", 1),
            ("max_opportunities", 1),
            ("denominator", 1),
            ("portfolio", "T2"),
            ("relation_subset", (item for item in self.authority.rule_descriptors)),
            ("opportunity_list", LazyIterable()),
            ("source_subset", TupleSubclass(ORACLE_SOURCE_UNIVERSE)),
        )
        for key, value in cases:
            with self.subTest(control=key, value_type=type(value).__name__):
                with self.assertRaises(TypeError):
                    enumerate_full_census_v1(
                        frame, self.bundle, self.resolver(), **{key: value}
                    )

    def test_full_census_replay_rejects_precomputed_and_self_hashed_forgery(self) -> None:
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
        forged_envelope = replace(first, envelope_hash="b" * 64)
        cases = (
            replace(canonical, relation_opportunities=canonical.relation_opportunities[:-1]),
            replace(
                canonical,
                relation_opportunities=canonical.relation_opportunities + (first,),
            ),
            replace(canonical, relation_opportunities=(forged_envelope,)),
            replace(canonical, relation_opportunities=list(canonical.relation_opportunities)),  # type: ignore[arg-type]
            replace(canonical, denominator_policy="CALLER_DENOMINATOR"),
            replace(canonical, isolated_source_event_count=len(canonical.relation_opportunities)),
            replace(canonical, census_hash="c" * 64),
        )
        for candidate in cases:
            with self.subTest(mutated=True), self.assertRaises(UtilityEvaluatorV1Error):
                validate_full_census_result_v1(candidate, frame, self.bundle, resolver)

        mutated = replace(
            canonical,
            relation_opportunities=canonical.relation_opportunities[:-1],
            census_hash="",
        )
        rehashed = replace(
            mutated, census_hash=stable_hash_v1(census_module._census_payload(mutated))
        )
        with self.assertRaises(UtilityEvaluatorV1Error):
            validate_full_census_result_v1(rehashed, frame, self.bundle, resolver)

    def test_opportunity_membership_relation_and_envelope_injection_reject(self) -> None:
        sign = 1.0 if self.event_direction == "step_up" else -1.0
        frame = self.frame(
            {self.event_source: _step_series(length=40, index=12, after=2.0 * sign)},
            row_count=40,
        )
        resolver = self.resolver()
        canonical = enumerate_full_census_v1(frame, self.bundle, resolver)
        first = canonical.relation_opportunities[0]
        self.assertEqual(
            validate_opportunity_envelope_v1(
                first, canonical, frame, self.bundle, resolver
            ),
            first.envelope_hash,
        )
        foreign_rule = next(
            rule
            for rule in self.authority.rule_descriptors
            if rule.relation_binding_hash
            != first.canonical_opportunity.relation_binding_hash
        )
        foreign_opportunity = replace(
            first.canonical_opportunity,
            relation_binding_hash=foreign_rule.relation_binding_hash,
        )
        attacks = (
            replace(first, isolated_source_event_identity="b" * 64),
            replace(first, canonical_opportunity=foreign_opportunity),
            replace(first, envelope_hash="c" * 64),
        )
        for attack in attacks:
            with self.subTest(attack=True), self.assertRaises(UtilityEvaluatorV1Error):
                validate_opportunity_envelope_v1(
                    attack, canonical, frame, self.bundle, resolver
                )

    def test_census_resolver_source_closure_rejects_omission_insertion_and_roles(self) -> None:
        frame = self.frame(row_count=12)
        mutations = (
            ("omit_main", ORACLE_MAIN_SOURCES[0], "source_step_threshold", None),
            ("omit_supplement", ORACLE_SUPPLEMENT_SOURCES[0], "source_step_threshold", None),
            ("insert_unknown", "UNKNOWN", "source_step_threshold", 1.0),
            ("wrong_role", ORACLE_SUPPLEMENT_SOURCES[0], "target_noise_scale", 1.0),
            ("threshold_int", ORACLE_MAIN_SOURCES[0], "source_step_threshold", 1),
            ("tolerance_negative", ORACLE_MAIN_SOURCES[0], "source_stability_tolerance", -1.0),
        )
        for name, source, role, value in mutations:
            resolver = self.resolver()
            key = (source, role)
            if value is None:
                del resolver._source_values[key]
            else:
                resolver._source_values[key] = value
            with self.subTest(case=name), self.assertRaises(UtilityEvaluatorV1Error):
                enumerate_full_census_v1(frame, self.bundle, resolver)

    def test_audit_coverage_floor_is_explicit(self) -> None:
        self.assertGreaterEqual(INDEPENDENT_INPUT_SCHEMA_ATTACKS, 15)
        self.assertGreaterEqual(INDEPENDENT_SOURCE_CENSUS_ISOLATION_ATTACKS, 20)
        self.assertGreaterEqual(INDEPENDENT_OPPORTUNITY_ATTACKS, 12)
        self.assertEqual(INDEPENDENT_UNIQUE_SEMANTIC_CLASSES, 77)
        self.assertEqual(INDEPENDENT_RAW_ADVERSARIAL_CASES, 100)
        self.assertEqual(EXPECTED_ACCEPTED_INVALID_CASES, 0)


if __name__ == "__main__":
    unittest.main()
