# Security

## Reporting a vulnerability

Please report suspected vulnerabilities by opening a private security
advisory on this repository's GitHub Security tab rather than a public
issue. Include enough detail to reproduce the problem; a fix or mitigation
suggestion is welcome but not required.

## Sandbox execution threat model

Bug Hunt lets users run commands against a real codebase as part of an
investigation. The design assumes that input is not trusted, and the
execution path is built accordingly:

- **No host execution.** `sandbox/e2b_backend.py`, the only production
  `ExecutionBackend`, runs every command inside an isolated
  [E2B](https://e2b.dev) Firecracker microVM. Nothing a user runs during an
  investigation executes on the API server's host.
- **Command allowlist, enforced twice.** Only `pytest`, `python`, `git`,
  `ls`, `cat`, `grep`, `find`, `diff` are permitted
  (`sandbox/base.py: ALLOWED_COMMANDS`). This is checked once at the API
  router (`api/app/routers/exec.py`), before a request reaches the sandbox
  at all, and again inside the sandbox backend itself, so a caller that
  bypasses the router still can't run an arbitrary command.
- **Argv only, never a shell string.** Commands are passed as argv lists
  throughout the codebase; there is no `shell=True` and no string
  interpolation into a shell command anywhere. Where the underlying E2B SDK
  only accepts a single shell-parsed command string, the backend builds
  that string with `shlex.join()` on the argv list, which quotes each
  token individually so no argument can inject additional shell syntax.
- **No host filesystem or secrets access.** Each investigation gets a fresh
  microVM seeded only with the scenario's fixture repository contents — it
  has no access to the API server's filesystem, environment, or other
  investigations' workspaces.
- **Fails loudly, never falls back.** If `E2B_API_KEY` isn't set,
  `E2BExecutionBackend` raises at construction time rather than silently
  running code unsandboxed on the host. There is a separate in-memory
  `FakeExecutionBackend`, but it exists only under `sandbox/tests/` for unit
  testing the API layer without real sandbox credentials, and it is never
  wired into production configuration (`api/app/deps.py` only ever
  constructs the real E2B backend outside of test dependency overrides).

This project has not yet been run end to end against a live E2B account
outside development — see the README's Current scope and status section.
The threat model above describes what's implemented in the code, not a
claim of independent security review.

Out of scope for this document: authentication (there is none yet — see the
README), and anything about the frontend build pipeline or third-party
dependencies, which should be reported the same way as any other
vulnerability above.
