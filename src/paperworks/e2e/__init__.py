"""End-to-end deterministic feasibility workflows."""

from paperworks.e2e.staging_dry_run import (
    StagingPipelineConfig,
    StagingPipelineDryRunError,
    StagingPipelineDryRunReport,
    StagingProfileAttempt,
    load_staging_pipeline_config,
    run_task017_staging_pipeline_dry_run,
    run_task017_staging_pipeline_dry_run_from_env,
)
from paperworks.e2e.rule_evidence_audit import (
    RuleEvidenceAuditError,
    RuleEvidenceAuditReport,
    RuleEvidenceCard,
    render_rule_evidence_audit_markdown,
    run_task019_rule_evidence_audit,
    run_task019_rule_evidence_audit_from_env,
)
from paperworks.e2e.support_aware_staging import (
    PairSupportSummary,
    SliceSupportSummary,
    SupportAwareStagingConfig,
    SupportAwareStagingError,
    SupportScanReport,
    SupportSliceSelectionPolicy,
    load_support_aware_staging_config,
    run_task018_support_aware_staging,
    run_task018_support_aware_staging_from_env,
    scan_support_aware_slice,
)
from paperworks.e2e.template_feasibility import (
    Task011AttemptOutcome,
    Task011FeasibilityReport,
    run_task011_template_feasibility,
)

__all__ = [
    "PairSupportSummary",
    "RuleEvidenceAuditError",
    "RuleEvidenceAuditReport",
    "RuleEvidenceCard",
    "SliceSupportSummary",
    "StagingPipelineConfig",
    "StagingPipelineDryRunError",
    "StagingPipelineDryRunReport",
    "StagingProfileAttempt",
    "SupportAwareStagingConfig",
    "SupportAwareStagingError",
    "SupportScanReport",
    "SupportSliceSelectionPolicy",
    "Task011AttemptOutcome",
    "Task011FeasibilityReport",
    "load_support_aware_staging_config",
    "load_staging_pipeline_config",
    "render_rule_evidence_audit_markdown",
    "run_task017_staging_pipeline_dry_run",
    "run_task017_staging_pipeline_dry_run_from_env",
    "run_task018_support_aware_staging",
    "run_task018_support_aware_staging_from_env",
    "run_task019_rule_evidence_audit",
    "run_task019_rule_evidence_audit_from_env",
    "run_task011_template_feasibility",
    "scan_support_aware_slice",
]
