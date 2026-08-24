# Remote canonical state

- Audited remote ref: `origin/research-v6-thesis-checkpoint`
- Initial remote commit: `5aa7c61ee37fb232c9b487e448ddbd30e3628872`
- First-results tag: `thesis-v1-first-results` (peeled to the same commit)
- Pre-push path gate: PASS
- New unpublished host-path occurrences: `0`
- Grandfathered legacy locator occurrences: `155` in `29` exact blobs
- Raw/private research data, credentials, and private scientific-value leaks: `0`

The audit used the remote-tracking ref and its Git objects. It did not rerun a
scientific experiment or read test data. The remote snapshot contains the
professor submission, frozen public INNER results, source, tests, configuration,
and the exact-blob legacy path disposition.

The two path-bearing self-hashed reports outside `origin/main` were already
reachable on other origin refs. They remain byte-exact because changing them
would invalidate referenced hashes. The only prospective change was replacing
a machine-local interpreter locator in its generator with `<BUNDLED_PYTHON>`.
