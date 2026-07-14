# Multi-Rule Runtime Gate

Every statically valid TASK-035A rule is executed exactly once in the selected
WSL-native rootless Podman runtime. The dedicated image is pinned to Python
3.11.9 and NumPy 1.26.4.

The container receives only a read-only quarantined rule, the corresponding
anchor values as an `N x 1` array, and a bounded writable private output
directory. Labels, inner/outer/test arrays, repository files, provider config,
credentials, and host home directories are not mounted.

Runs use network none, a read-only root filesystem, non-root UID, all
capabilities dropped, no new privileges, one CPU, 256 MB memory, 64 PIDs, and a
bounded timeout. The output check covers only length, one-dimensional shape,
finite values, and binary domain. No metric or anomaly-quality claim follows.
