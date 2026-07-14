# Docker Interactive Retry Protocol

DEC-032 permits exactly one clean Docker Desktop retry after bounded cleanup.
The retry uses the verified official installer in a visible interactive session.

## Frozen retry controls

- Runtime: Docker Desktop, per-user, WSL 2, Linux containers.
- Arguments supplied by this task: `install --user`.
- `--quiet` and `--accept-license` are prohibited.
- `--backend=wsl-2` is intentionally omitted from the retry; WSL 2 is selected
  through the official user interface if prompted.
- A private ignored receipt is written before launch. Launch consumes the only
  retry regardless of success, failure, timeout, cancellation, or reboot.
- Any license or subscription agreement must be reviewed and accepted by the
  researcher. The task does not automate that action.

## Success gate

After installation, the Docker client and server must both respond. Linux
container mode, the WSL 2 backend, and Docker's WSL distribution must be
verified. A harmless `hello-world` container must then pass with no research
mounts and the required isolation controls.

If the installer fails or times out, no second Docker retry is allowed and the
next research decision is whether to switch to Podman. Runtime readiness alone
does not approve captured-rule execution.
