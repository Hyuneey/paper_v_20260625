# Windows Container Runtime Setup

TASK-028I prepares a Windows container runtime for a later TASK-028 resume. It
does not access or execute the captured ARGOS rule.

## Selected Runtime

- Runtime: Docker Desktop `4.82.0`
- Installation scope: per-user
- Intended backend: WSL 2
- Intended mode: Linux containers
- Fallback runtime: not selected and not installed

The host preflight found Windows Enterprise x64 build `26100.8737`, WSL
`2.6.3.0`, an active hypervisor, firmware virtualization enabled, no pending
restart, and approximately `31.12 GiB` physical memory. No existing Docker or
Podman CLI was present.

The processor CIM query reported the SLAT field as false despite the active
Hyper-V hypervisor and operational WSL 2 engine. Runtime installation, daemon
health, and the isolated security-control smoke therefore remained mandatory
gates rather than being inferred from the host query.

## Official Installer Verification

- Source: `https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe`
- Final source domain: `desktop.docker.com`
- File name: `Docker Desktop Installer.exe`
- Product version: `4.82.0.233772`
- Byte size: `638124464`
- SHA-256:
  `a5b5837542f2f57fadbb09db90a60c84f8efc0a65f8d6dcd2e5b9fca3a2b87e6`
- Authenticode status: valid
- Signer: Docker Inc.
- Issuer: DigiCert Trusted G4 Code Signing RSA4096 SHA384 2021 CA1

The installer was stored only under a system temporary directory. Its path is
not tracked. Docker's official Windows installation documentation was used to
confirm per-user mode and the WSL 2 backend.

## Installation Attempt

The verified installer was invoked once with these options:

```text
install --user --backend=wsl-2
```

`--accept-license` and `--quiet` were not used. No subscription agreement was
accepted automatically and no license screen was reached.

The installer failed to complete or update its log within the 900-second
limit. The two installer processes started by this attempt were then stopped;
no installer process remained. Partial per-user files were present, but there
was no uninstall registration, Start menu shortcut, Docker command, Docker WSL
distribution, or running Docker Desktop process.

## Result

```yaml
task_status: blocked_environment
runtime_installed: false
runtime_daemon_healthy: false
task028_resume_allowed: false
captured_rule_accessed: false
captured_rule_executed: false
```

The stop condition prevents Podman fallback, daemon startup, image pulls, or
container tests after the installer failure. A future retry must first resolve
the partial per-user Docker Desktop installation state through an explicit
environment-remediation task.
