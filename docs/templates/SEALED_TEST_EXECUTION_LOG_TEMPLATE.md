# Sealed Test One-Way Execution Log

Status: template

Do not create a completed sealed-test log until DEC-007 is resolved and final
test access is explicitly approved.

## Preconditions

- DEC-007 resolution reference:
- Official SWaT provenance manifest ID:
- Terms acknowledgement reference:
- Frozen split protocol hash:
- Frozen metric protocol hash:
- Frozen config hash:
- Code commit:
- Operator:
- Approval timestamp:

## Access Control

- `SWAT_DATA_ROOT`:
- Final test file logical role:
- Final test file SHA-256:
- Final test access approved: false
- Final test first opened at:
- Raw rows copied to Git worktree: no
- Raw windows copied to Git worktree: no

## Command

```powershell
# Fill only after approval.
```

## Execution Record

- Start timestamp:
- End timestamp:
- Exit code:
- Runtime environment:
- Random seeds:
- Network access used: no
- Real LLM provider used: no
- Runtime LLM used: no

## Output Artifacts

| Artifact | Path | SHA-256 / ID | Git tracked? |
|---|---|---|---|
| evaluation report | pending | pending | yes |
| aggregate metrics | pending | pending | yes |
| private debug output | none | none | no |

## Post-Test Change Audit

- Thresholds changed after test access: no
- K changed after test access: no
- Prompts changed after test access: no
- Rules changed after test access: no
- Fusion weights changed after test access: no
- Any rerun after post-test changes: no

If any answer above becomes `yes`, the result must be labeled exploratory and
must not replace the primary frozen run.

## Notes

- Do not paste raw rows, raw windows, full time-series sequences, private
  download links, or personal request information into this log.
