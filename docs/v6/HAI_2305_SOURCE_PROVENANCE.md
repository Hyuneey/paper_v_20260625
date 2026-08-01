# HAI 23.05 Source Provenance

TASK-039A pins the official repository at
`2a814cebc9a66b06c9e5cd545e2d72e65d383737` and permits only the official
GitHub remote and its Git-LFS endpoints. The checkout and raw files remain
outside the paper repository.

The implementation freeze completed at `3f272b7ba7a313b31bde4b589b65cb3094f72aec`.
The sanitized failure-capable execution revision is
`8ad80118c5272a7d62e20fa5f69cf366720bccbf`.

The official Git remote, pinned snapshot, and introduction commit were
reachable. The restricted HAI 23.05 Git-LFS request was blocked because the
official repository's LFS budget was exhausted. The exact LFS objects were not
available, no fallback source was used, and provenance status remains
`blocked_lfs_object_unavailable`.

No moving ref, mirror, Kaggle copy, archive fallback, or HAIEnd file is an
authorized source.
