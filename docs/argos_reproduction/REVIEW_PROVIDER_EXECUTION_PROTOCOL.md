# Review Provider Execution Protocol

DEC-074 authorizes at most one independent Review request for each triggered
`A2` or `A3` branch. The exact eligible manifest is committed before provider
access.

The provider configuration is OpenAI Responses API with model
`gpt-5.6-luna`, 6,000 maximum output tokens, omitted temperature and provider
seed, and no automatic retry, manual retry or replacement generation. A
receipt is written before every request and permanently consumes its branch
slot.

`A2` and `A3` use separate call identities and provider calls even when their
parent, metrics and prompt payload are identical. The branch request hash binds
the branch ID; a shared prompt payload hash is permitted. Responses are not
reused between branches.

Every visible response is extracted and statically audited. Static-valid
revisions execute twice on generation target, twice on generation contrast and
twice on full inner values in fresh rootless Podman containers. Generated code
never executes on the host. Invalid, nondeterministic or harmful revisions are
retained as branch outcomes and are never replaced by their parent.
