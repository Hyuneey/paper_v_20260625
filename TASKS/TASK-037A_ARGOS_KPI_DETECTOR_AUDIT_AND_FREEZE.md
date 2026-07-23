# TASK-037A: ARGOS KPI Base-Detector Audit and Freeze

Status: `unresolved_variant_ambiguity_with_dual_arm_freeze`

## Completed

- Audited the ARGOS paper, pinned/historical ARGOS source, and official
  EasyTSAD sources.
- Pinned ignored EasyTSAD `0.2.0.2` commit `55eff2c...` and hashed required
  detector/config/schema/evaluation files.
- Preserved the unresolved alpha/beta identity as two non-selected co-primary
  arms.
- Froze split, threshold, artifact, error-segment, diagnostic-fusion, and
  paper-faithful-fusion contracts.
- Built a dedicated rootless Podman image and passed isolation plus synthetic
  deterministic smoke for both variants.

## Not performed

No real KPI detector fit, score, threshold, validation, test, detector-rule
fusion, provider/agent action, or generated-rule execution occurred. TASK-037B
through TASK-037E remain unauthorized.
