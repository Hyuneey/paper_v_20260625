# Permanent safety boundaries

- Raw HAI data never enters Git.
- Label rows and attack intervals never enter public reports.
- Private numeric values never enter Git or prompts.
- Private locator and registry paths never enter tool output or reports.
- Test2 remains sealed until separate OUTER authorization.
- Provider or LLM calls require separate explicit authority.
- Runtime LLM is prohibited.
- Detector execution requires separate authority.
- Results cannot drive threshold, rule, or policy modification.
- Broad filesystem discovery for private custody is prohibited.
- Shell history and old logs cannot recover private paths.

## Path-safe command prohibitions

Sensitive custody handling must not display environment values; enable shell
tracing; display resolved paths or symlink targets; list, search, or traverse
private custody areas; display locator documents; print exceptions containing
paths; or permit uncaught tracebacks. In particular, environment-dump commands,
path-resolution output, directory-tree discovery, locator-content display, and
path-bearing command arguments are prohibited.

Sensitive work runs in one path-silent process. It outputs only fixed status
codes and explicitly allowed hashes, booleans, and counters. Any private path
or numeric-value disclosure is a terminal blocker for that task.

## Local private continuity

- `.env.custody.local` is private, local-only, and must remain Git-ignored.
- Its contents may never appear in chat, tool output, reports, or tracked
  project-state files.
- Never display, echo, stage, or commit the local binding file.
- Never use shell history, prior logs, or broad discovery to recover it.
- `scripts/local/bootstrap_custody_bindings_v1.py` is the only approved
  interactive HAI root setup route.
- Sensitive user input must use the helper's hidden prompt.
- Test2 remains sealed during binding setup and authorization recovery.
