# TASK-033 Container Runtime Re-entry

## Decision

TASK-033 uses one new experiment-phase runtime: rootless Podman 4.9.3 inside a
dedicated Ubuntu 24.04.4 WSL 2 distribution. Docker Desktop was not retried,
WSL-native Docker Engine was not installed, and TASK-028 remains deferred.

The Ubuntu distribution came from the official WSL catalog. Its downloaded
image hash was verified before registration. Podman, `crun`, `slirp4netns`,
`fuse-overlayfs`, and subordinate-ID support came from the Ubuntu 24.04 archive.

## Rootless boundary

Podman runs as the dedicated `task033` user with subordinate UID/GID mappings,
systemd cgroup v2, `crun`, and seccomp. No Podman socket is exposed. The host
wrapper enters WSL and delegates only the Podman command to this user.

Exactly one container runtime was selected. The alternate WSL-native Docker
Engine path was not installed after Podman satisfied the required controls.

## Harmless preflight

Before the captured rule was read, a public Python container was run with no
research mount. The probe observed:

- UID 65532 and GID 65532;
- loopback as the only network interface and blocked external connection;
- a blocked write to the root filesystem;
- enforced CPU, memory, and PID cgroup limits;
- bounded `noexec,nosuid` temporary storage;
- a two-second wait timeout followed by bounded cleanup.

Only after this gate passed was the frozen rule hash and static policy checked.

## Image

The runtime image uses Python 3.11.9 from a digest-pinned Linux base and NumPy
1.26.4 from a hash-pinned wheel. The image runs as UID/GID 65532. It contains
the fixed in-container entrypoint but neither ARGOS source nor the captured
rule. The rule is supplied only as a single read-only file during E1 execution.

The environment report records the resolved image digest, package versions,
lock hashes, and verified isolation controls without host-private paths.
