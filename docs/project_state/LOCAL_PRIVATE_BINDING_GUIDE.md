# Local private binding guide

Machine-specific custody paths cannot live in Git, chat, reports, or the
public project-state layer. The repository therefore uses a second,
local-only continuity layer named `.env.custody.local`. Git ignores this file;
its contents must never be displayed, pasted into chat, or committed.

On a new execution machine, run:

```text
python scripts/local/bootstrap_custody_bindings_v1.py
```

If the HAI binding is not already present in the process environment, the
helper requests it through a hidden terminal prompt. `HAI_DATA_ROOT` means the
parent directory of `hai-23.05/`. The helper validates the frozen raw-byte
custody hashes of the authorized test1 feature and label assets. It does not
parse them, inspect test2, discover directories, or issue scientific
authorization.

Optional MAIN and supplement custody bindings are copied only when they are
already present in the current process environment. The later authorization
recovery task loads the local file without printing it and performs any
separately authorized path-silent locator recovery.

Deleting `.env.custody.local` removes the local binding state. The public
`docs/project_state/` layer records only configured/not-configured booleans,
never binding values.

## Approved HAI binding routes

There are two approved ways to establish `HAI_DATA_ROOT`:

1. Use an existing local dataset through the hidden prompt in
   `scripts/local/bootstrap_custody_bindings_v1.py`.
2. Reconstruct only the authorized INNER test1 feature and label payload from
   the pinned official source with
   `scripts/local/materialize_hai_inner_payload_v1.py`.

The code-materialized route is non-interactive. It freezes the official source
and commit, limits payload acquisition to the two authorized files, validates
their exact hashes and sizes, and stores the resulting disposable cache binding
only in the ignored local layer. The cache location is never public authority.
