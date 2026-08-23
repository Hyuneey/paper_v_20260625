"""R2-custody recovery bridge for the sole sealed OUTER execution.

The scientific controller is the frozen implementation from Commit
``63b33ee3b9976177d3b00d8aa4ac0ec9ed83f5a7``.  This module delegates that
controller without copying or changing its D0, D1, D2-V1, ordering, event,
episode, or metric logic.  It adds only the frozen R2 eight-field local-binding
adapter, receipt replay, path-free errors, recovery commit custody, and new
public result filenames.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import sys
from typing import Any, Mapping, NoReturn, Sequence

from paperworks.v6 import task039e3_r2r_outer_d0_d1_d2v1_execution_v1 as original


ROOT = Path(__file__).resolve().parents[3]
REPORT_ROOT = ROOT / "docs" / "task_reports"
TASK_ID = "TASK-039E3-R2R-UTILITY-OUTER-D0-D1-D2V1-EXECUTION-RECOVERY-V1"
PASS_STATUS = "passed_task039e3_r2r_utility_outer_d0_d1_d2v1_execution_recovery_v1"
BLOCK_STATUS = "blocked_task039e3_r2r_utility_outer_d0_d1_d2v1_execution_recovery_v1"
BRANCH = "task-039e3-r2r-utility-outer-d0-d1-d2v1-execution-recovery-v1"
BASE = "37f2ec05617e51a87a5144823b3782057820767f"
ORIGINAL_IMPLEMENTATION_COMMIT = "63b33ee3b9976177d3b00d8aa4ac0ec9ed83f5a7"
NEXT_TASK = "TASK-039E3-R2R-UTILITY-OUTER-D0-D1-D2V1-RESULT-INTEGRITY-AUDIT-V1"
FAILURE_NEXT_TASK = "TASK-039E3-R2R-UTILITY-OUTER-EXECUTION-FAILURE-DISPOSITION-V1"
RECOVERY_IMPLEMENTATION_VERSION = "TASK039E3_R2R_OUTER_D0_D1_D2V1_EXECUTION_RECOVERY_V1"

ORIGINAL_SCIENTIFIC_EXECUTION_SEMANTICS_CHANGED = False
ALLOWED_IMPLEMENTATION_CHANGES = (
    "INFRASTRUCTURE_LOCAL_BINDING_ADAPTER",
    "PRIVATE_PATH_REDACTION_ADAPTER",
    "PRE_REAL_CUSTODY_READINESS_RECEIPT_CONSUMPTION",
)
FORBIDDEN_SCIENTIFIC_CHANGES = (
    "D0_INFERENCE_MATH", "D1_EVALUATOR_SEMANTICS", "D1_RULE_PORTFOLIO",
    "D2_FUSION_LOGIC", "METRICS", "EVENT_POLICY", "EPISODE_POLICY", "TEST2_ORDER",
)

R2_SCHEMA_SHA256 = "533627b18c29be21435f9641b6ec8583f88586af1cd766bd41fab67ea0cecbd1"
R2_SCHEMA_ARTIFACT_SHA256 = "f8bf60d9a3a69628f13361372820fb9dd1cf0c367085360bdf20a4a84c9f773f"
R2_COMPATIBILITY_SHA256 = "536a156a085968234db86c6650bff3c65dc3c210ce9914432c35b3f17d4872b0"
R2_READINESS_SHA256 = "05aa268559a4c1830896e07f42fb6661b007c0c398ea6439fadbb98cddd82e59"
R2_PATH_REDACTION_SHA256 = "6df121d976f5512c8d7999f35e4140abb04ac919b9d3df07428156e8f3f9080b"
R2_NAMESPACE_SHA256 = "dedc2c7829122e5fc6bf8d623c2d0df68ed35c31e516a41e5942ec36b1d48279"
R2_SENTINEL_SHA256 = "84ce4999af15b3e052bece2577c3e9811859149bcfd491273631fb5aa65681fa"
R2_D0_MODEL_BINDING_SHA256 = "b97d4899f0869a20c1aacc147acdcfe537b84d6b8f72f5dd2b29aa159229bed5"
R2_D0_THRESHOLD_BINDING_SHA256 = "34e8eaffd80b4f9688a1d50835f6aa7d31767f8ac1201af949da6738757d1b2c"

R2_REPORTS = {
    "schema": ("TASK-039E3_R2R_UTILITY_OUTER_PRE_EXECUTION_CUSTODY_R2_LOCAL_BINDING_SCHEMA.json", R2_SCHEMA_ARTIFACT_SHA256),
    "compatibility": ("TASK-039E3_R2R_UTILITY_OUTER_PRE_EXECUTION_CUSTODY_R2_COMPATIBILITY_RECEIPT.json", R2_COMPATIBILITY_SHA256),
    "readiness": ("TASK-039E3_R2R_UTILITY_OUTER_PRE_EXECUTION_CUSTODY_R2_READINESS.json", R2_READINESS_SHA256),
    "path_redaction": ("TASK-039E3_R2R_UTILITY_OUTER_PRE_EXECUTION_CUSTODY_R2_PATH_REDACTION_AUDIT.json", R2_PATH_REDACTION_SHA256),
    "namespaces": ("TASK-039E3_R2R_UTILITY_OUTER_PRE_EXECUTION_CUSTODY_R2_PRIVATE_NAMESPACE_AUDIT.json", R2_NAMESPACE_SHA256),
    "sentinel": ("TASK-039E3_R2R_UTILITY_OUTER_PRE_EXECUTION_CUSTODY_R2_SENTINEL_AUDIT.json", R2_SENTINEL_SHA256),
    "model": ("TASK-039E3_R2R_UTILITY_OUTER_PRE_EXECUTION_CUSTODY_R2_D0_MODEL_BINDING.json", R2_D0_MODEL_BINDING_SHA256),
    "threshold": ("TASK-039E3_R2R_UTILITY_OUTER_PRE_EXECUTION_CUSTODY_R2_D0_THRESHOLD_BINDING.json", R2_D0_THRESHOLD_BINDING_SHA256),
}

HAI_ROOT = "HAI_DATA_ROOT"
MAIN_REGISTRY = "TASK039E3_UTILITY_NORMAL_ONLY_AUTHORITY_V1"
MAIN_LOCATOR = "TASK039E3_UTILITY_NORMAL_ONLY_AUTHORITY_V1_LOCATOR"
SUPPLEMENT_REGISTRY = "TASK039E3_UTILITY_SOURCE_CENSUS_SUPPLEMENT_V1"
SUPPLEMENT_LOCATOR = "TASK039E3_UTILITY_SOURCE_CENSUS_SUPPLEMENT_V1_LOCATOR"
PREPROCESSING = "TASK039E3_D0_PCA_SPE_PREPROCESSING_V1"
MODEL = "TASK039E3_D0_PCA_SPE_MODEL_V1"
THRESHOLD = "TASK039E3_D0_PCA_SPE_THRESHOLD_V1"
CANONICAL_BINDING_FIELDS = frozenset({
    HAI_ROOT, MAIN_REGISTRY, MAIN_LOCATOR, SUPPLEMENT_REGISTRY,
    SUPPLEMENT_LOCATOR, PREPROCESSING, MODEL, THRESHOLD,
})
OBSOLETE_R1_BINDING_FIELDS = frozenset({
    "TASK039E3_UTILITY_NORMAL_ONLY_PRIVATE_REGISTRY_V1",
    "TASK039E3_UTILITY_NORMAL_ONLY_PRIVATE_LOCATOR_V1",
    "TASK039E3_UTILITY_SOURCE_CENSUS_SUPPLEMENT_PRIVATE_REGISTRY_V1",
    "TASK039E3_UTILITY_SOURCE_CENSUS_SUPPLEMENT_PRIVATE_LOCATOR_V1",
})
_BINDING_LINE = re.compile(r"^([A-Z0-9_]+)='((?:[^']|'\"'\"')*)'$")

PREDICTION_PATHS = {
    "d0": REPORT_ROOT / "TASK-039E3_R2R_UTILITY_OUTER_RECOVERY_D0_PREDICTION_V1.json",
    "d1": REPORT_ROOT / "TASK-039E3_R2R_UTILITY_OUTER_RECOVERY_D1_PREDICTION_V1.json",
    "d2": REPORT_ROOT / "TASK-039E3_R2R_UTILITY_OUTER_RECOVERY_D2V1_PREDICTION_V1.json",
}
PREFIX = "TASK-039E3_R2R_UTILITY_OUTER_D0_D1_D2V1_EXECUTION_RECOVERY_V1_"
REPORT_PATHS = {
    "implementation_audit": REPORT_ROOT / f"{PREFIX}IMPLEMENTATION_AUDIT.json",
    "accounting": REPORT_ROOT / f"{PREFIX}ACCOUNTING.json",
    "metrics": REPORT_ROOT / f"{PREFIX}METRICS.json",
    "readiness": REPORT_ROOT / f"{PREFIX}READINESS.json",
    "bundle": REPORT_ROOT / f"{PREFIX}BUNDLE.json",
    "receipt": REPORT_ROOT / f"{PREFIX}RECEIPT.json",
    "report": REPORT_ROOT / f"{PREFIX}REPORT.md",
}

STATIC_TESTS = 54
INDEPENDENT_ATTACKS = 44
HISTORICAL_PRE_SCIENTIFIC_OUTER_ABORTS = 2

# Exact frozen scientific helpers are re-exported for synthetic/audit tests.
OuterExecutionError = original.OuterExecutionError
OuterExecutionState = original.OuterExecutionState
OuterExecutionStateMachineV1 = original.OuterExecutionStateMachineV1
OuterTest2FeatureSnapshotV1 = original.OuterTest2FeatureSnapshotV1
CommittedOuterThreeArmExecutionGrantV1 = original.CommittedOuterThreeArmExecutionGrantV1
OuterExecutionOutcomeV1 = original.OuterExecutionOutcomeV1
ROW_COUNT = original.ROW_COUNT
D1_RELATION_COUNT = original.D1_RELATION_COUNT
D1_EVALUATOR_IDENTITY = original.D1_EVALUATOR_IDENTITY
REQUIRED_DISTINCT_SOURCES = original.REQUIRED_DISTINCT_SOURCES
TRIGGER_CLASSES = original.TRIGGER_CLASSES
AUTHORIZATION_SHA256 = original.AUTHORIZATION_SHA256
PREREGISTRATION_SHA256 = original.PREREGISTRATION_SHA256
D0_MODEL_SHA256 = original.D0_MODEL_SHA256
D0_THRESHOLD_SHA256 = original.D0_THRESHOLD_SHA256
D2_DESIGN_SHA256 = original.D2_DESIGN_SHA256
SOURCE_MAP_SHA256 = original.SOURCE_MAP_SHA256
compact_prediction = original.compact_prediction
expand_compact_prediction = original.expand_compact_prediction
fuse_point_v1 = original.fuse_point_v1
derive_intervals = original.derive_intervals
metric_values = original.metric_values
complementarity = original.complementarity
reject_prohibited_operation_v1 = original.reject_prohibited_operation_v1
outer_auth = original.outer_auth


def fail(code: str) -> NoReturn:
    raise OuterExecutionError(code) from None


def parse_canonical_local_bindings_v1(raw: bytes) -> dict[str, str]:
    """Parse the R2 canonical binding document without exposing its values."""
    try:
        text = raw.decode("utf-8")
        result: dict[str, str] = {}
        for line in text.splitlines():
            if not line:
                continue
            match = _BINDING_LINE.fullmatch(line)
            if match is None:
                fail("OUTER_RECOVERY_LOCAL_BINDING_REJECTED")
            key = match.group(1)
            if key not in CANONICAL_BINDING_FIELDS or key in result or key in OBSOLETE_R1_BINDING_FIELDS:
                fail("OUTER_RECOVERY_LOCAL_BINDING_REJECTED")
            result[key] = match.group(2).replace("'\"'\"'", "'")
        if set(result) != set(CANONICAL_BINDING_FIELDS):
            fail("OUTER_RECOVERY_LOCAL_BINDING_REJECTED")
        return result
    except OuterExecutionError:
        raise
    except BaseException:
        fail("OUTER_RECOVERY_LOCAL_BINDING_REJECTED")


def reject_absolute_path_comparison_v1() -> NoReturn:
    fail("OUTER_RECOVERY_ABSOLUTE_PATH_COMPARISON_REJECTED")


def assert_path_free_surfaces_v1(surfaces: Sequence[str], private_tokens: Sequence[str]) -> None:
    if any(token and token in surface for token in private_tokens for surface in surfaces):
        fail("OUTER_RECOVERY_PATH_EXPOSURE_REJECTED")


def validate_r2_infrastructure_authority_v1() -> Mapping[str, str]:
    observed: dict[str, str] = {}
    for role, (filename, expected) in R2_REPORTS.items():
        try:
            document = original.strict_json((REPORT_ROOT / filename).read_bytes())
            observed[role] = original.validate_sealed(document, expected)
        except OuterExecutionError:
            raise
        except BaseException:
            fail("OUTER_RECOVERY_R2_AUTHORITY_REJECTED")
    compatibility = original.strict_json((REPORT_ROOT / R2_REPORTS["compatibility"][0]).read_bytes())
    schema = original.strict_json((REPORT_ROOT / R2_REPORTS["schema"][0]).read_bytes())
    readiness = original.strict_json((REPORT_ROOT / R2_REPORTS["readiness"][0]).read_bytes())
    path_audit = original.strict_json((REPORT_ROOT / R2_REPORTS["path_redaction"][0]).read_bytes())
    if (
        schema.get("schema_identity") != R2_SCHEMA_SHA256
        or compatibility.get("canonical_local_binding_schema_identity") != R2_SCHEMA_SHA256
        or compatibility.get("scientific_attempts_consumed") != 0
        or compatibility.get("scientific_attempts_remaining") != 1
        or compatibility.get("test2_access_count") != 0
        or compatibility.get("path_redaction_result") != "PASS"
        or readiness.get("outer_scientific_attempts_consumed") != 0
        or readiness.get("outer_scientific_attempts_remaining") != 1
        or readiness.get("test2_feature_accesses") != 0
        or readiness.get("test2_label_accesses") != 0
        or path_audit.get("result") != "PASS"
        or any(path_audit.get(key) != 0 for key in (
            "new_continuity_occurrences", "new_exception_occurrences",
            "new_public_json_occurrences", "new_public_markdown_occurrences",
            "new_stderr_occurrences", "new_stdout_occurrences",
            "new_scientific_private_value_leaks",
        ))
    ):
        fail("OUTER_RECOVERY_R2_AUTHORITY_REJECTED")
    return observed


def issue_committed_outer_execution_grant_v1() -> CommittedOuterThreeArmExecutionGrantV1:
    validate_r2_infrastructure_authority_v1()
    return original.issue_committed_outer_execution_grant_v1()


def validate_grant(value: CommittedOuterThreeArmExecutionGrantV1) -> str:
    return original.validate_grant(value)


@dataclass
class RecoveryAttemptBoundaryV1:
    scientific_attempts: int = 0
    attempts_remaining: int = 1
    retries: int = 0

    def begin_immediately_before_feature_access(self) -> None:
        if self.scientific_attempts != 0 or self.attempts_remaining != 1 or self.retries != 0:
            fail("OUTER_SECOND_ATTEMPT_REJECTED")
        self.scientific_attempts = 1
        self.attempts_remaining = 0

    def reject_retry(self) -> NoReturn:
        fail("OUTER_PROHIBITED_OPERATION_REJECTED")


def _load_combined_private_scientific_authorities_v1() -> tuple[Any, Any, Any, Any, Path]:
    """Resolve the exact original authorities through the R2 canonical schema."""
    try:
        binding_path = ROOT / ".env.custody.local"
        if binding_path.is_symlink() or not binding_path.is_file():
            fail("OUTER_RECOVERY_LOCAL_BINDING_REJECTED")
        bindings = parse_canonical_local_bindings_v1(binding_path.read_bytes())
        preprocessing = original.d0_inner._load_private_json_once_v1(
            bindings[PREPROCESSING], original.d0_inner.PREPROCESSING_HASH)
        model = original.d0_inner._load_private_json_once_v1(bindings[MODEL], D0_MODEL_SHA256)
        threshold = original.d0_inner._load_private_json_once_v1(bindings[THRESHOLD], D0_THRESHOLD_SHA256)
        decoded = original.d0_inner._validate_and_decode_private_documents_v1(
            preprocessing, model, threshold)
        _, bundle = original.d1_inner._load_public_authorities_v1()
        main_document = original.d1_inner._strict_private_json_v1(Path(bindings[MAIN_REGISTRY]))
        supplement_document = original.d1_inner._strict_private_json_v1(Path(bindings[SUPPLEMENT_REGISTRY]))
        resolver = original.d1_inner.build_real_private_numeric_resolver_v1(
            bundle, main_document=main_document, supplement_document=supplement_document)
        root = original.d0_inner._private_hai_root_v1(bindings[HAI_ROOT])
        return decoded, bundle, resolver, bindings, root
    except OuterExecutionError:
        raise
    except BaseException:
        fail("OUTER_RECOVERY_PRIVATE_AUTHORITY_REPLAY_REJECTED")


def _validate_recovery_commit_boundary_v1() -> tuple[str, str, str]:
    if original._git("branch", "--show-current") != BRANCH or original._git("status", "--porcelain"):
        fail("OUTER_PRE_REAL_GIT_STATE_REJECTED")
    if original._git("merge-base", "--is-ancestor", BASE, "HEAD") != "":
        fail("OUTER_BASE_ANCESTRY_REJECTED")
    source_rel = "src/paperworks/v6/task039e3_r2r_outer_d0_d1_d2v1_execution_recovery_v1.py"
    basic_rel = "tests/test_task039e3_r2r_outer_d0_d1_d2v1_execution_recovery_v1.py"
    independent_rel = "tests/test_task039e3_r2r_outer_d0_d1_d2v1_execution_recovery_v1_independent.py"
    task_rel = "TASKS/TASK-039E3-R2R-UTILITY-OUTER-D0-D1-D2V1-EXECUTION-RECOVERY-V1.md"
    commit_a = original._git("log", "-1", "--format=%H", "--", source_rel)
    commit_b = original._git("log", "-1", "--format=%H", "--", independent_rel)
    changed_a = set(original._git("diff-tree", "--no-commit-id", "--name-only", "-r", commit_a).splitlines())
    changed_b = set(original._git("diff-tree", "--no-commit-id", "--name-only", "-r", commit_b).splitlines())
    if changed_a != {task_rel, source_rel, basic_rel} or changed_b != {independent_rel}:
        fail("OUTER_COMMIT_BOUNDARY_REJECTED")
    if original._git("merge-base", "--is-ancestor", commit_a, commit_b) != "" or original._git(
        "merge-base", "--is-ancestor", commit_b, "HEAD"
    ) != "":
        fail("OUTER_COMMIT_BOUNDARY_REJECTED")
    return commit_a, commit_b, original.sha256((ROOT / source_rel).read_bytes()).hexdigest()


_ORIGINAL_SEAL = original.seal


def _recovery_seal_adapter_v1(value: Mapping[str, Any]) -> dict[str, Any]:
    adapted = dict(value)
    artifact_type = adapted.get("artifact_type")
    if artifact_type == "OuterThreeArmImplementationAuditV1":
        adapted.update({
            "recovery_implementation_version": RECOVERY_IMPLEMENTATION_VERSION,
            "original_implementation_commit": ORIGINAL_IMPLEMENTATION_COMMIT,
            "original_scientific_execution_semantics_changed": False,
            "allowed_infrastructure_changes": list(ALLOWED_IMPLEMENTATION_CHANGES),
            "forbidden_scientific_changes_applied": 0,
            "r2_compatibility_receipt_sha256": R2_COMPATIBILITY_SHA256,
            "r2_path_redaction_readiness_pass": True,
        })
    elif artifact_type == "OuterThreeArmExecutionAccountingV1":
        adapted.update({
            "historical_pre_scientific_outer_aborts": HISTORICAL_PRE_SCIENTIFIC_OUTER_ABORTS,
            "outer_scientific_attempts_remaining": 0,
            "new_private_path_exposures": 0,
        })
    elif artifact_type == "OuterThreeArmExecutionReadinessV1":
        adapted.update({
            "recovery_implementation_version": RECOVERY_IMPLEMENTATION_VERSION,
            "r2_compatibility_receipt_sha256": R2_COMPATIBILITY_SHA256,
        })
    return _ORIGINAL_SEAL(adapted)


_RECOVERY_INVOKED = False


def _configure_original_controller_v1() -> None:
    original.BRANCH = BRANCH
    original.BASE = BASE
    original.PASS_STATUS = PASS_STATUS
    original.BLOCK_STATUS = BLOCK_STATUS
    original.NEXT_TASK = NEXT_TASK
    original.FAILURE_NEXT_TASK = FAILURE_NEXT_TASK
    original.PREDICTION_PATHS = PREDICTION_PATHS
    original.REPORT_PATHS = REPORT_PATHS
    original.STATIC_TESTS = STATIC_TESTS
    original.INDEPENDENT_ATTACKS = INDEPENDENT_ATTACKS
    original._validate_commit_boundary = _validate_recovery_commit_boundary_v1
    original._load_private_scientific_authorities = _load_combined_private_scientific_authorities_v1
    original.seal = _recovery_seal_adapter_v1


def execute_authorized_outer_recovery_v1() -> OuterExecutionOutcomeV1:
    """Execute the original sole scientific controller through frozen R2 custody."""
    global _RECOVERY_INVOKED
    if _RECOVERY_INVOKED:
        fail("OUTER_SECOND_ATTEMPT_REJECTED")
    validate_r2_infrastructure_authority_v1()
    _configure_original_controller_v1()
    _RECOVERY_INVOKED = True
    return original.execute_authorized_outer_v1()


def _main(argv: Sequence[str]) -> int:
    if tuple(argv) != ("--execute-once",):
        fail("OUTER_UNAUTHORIZED_ENTRY_POINT")
    outcome = execute_authorized_outer_recovery_v1()
    print(json.dumps({
        "status": PASS_STATUS,
        "scientific_state": original.SCIENTIFIC_STATE,
        "execution_run_hash": outcome.execution_run_hash,
        "d0_prediction_hash": outcome.d0_prediction_hash,
        "d1_prediction_hash": outcome.d1_prediction_hash,
        "d2_prediction_hash": outcome.d2_prediction_hash,
        "d1_relation_evidence_hash": outcome.d1_relation_evidence_hash,
        "d2_fusion_evidence_hash": outcome.d2_fusion_evidence_hash,
        "private_metric_evidence_hash": outcome.private_metric_evidence_hash,
        "implementation_audit_hash": outcome.implementation_audit_hash,
        "accounting_hash": outcome.accounting_hash,
        "metrics_hash": outcome.metrics_hash,
        "readiness_hash": outcome.readiness_hash,
        "bundle_hash": outcome.bundle_hash,
        "receipt_hash": outcome.receipt_hash,
        "report_self_hash": outcome.report_self_hash,
        "commit_a": outcome.commit_a,
        "commit_b": outcome.commit_b,
    }, sort_keys=True))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    try:
        return _main(tuple(sys.argv[1:] if argv is None else argv))
    except OuterExecutionError as error:
        print(error.code, file=sys.stderr)
        return 2
    except BaseException:
        print("OUTER_RECOVERY_UNEXPECTED", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
