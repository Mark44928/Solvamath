# Security

Solvamath is a local-only terminal game. It has no network code, no accounts
and no telemetry.

- Answers and Make 24 expressions are validated with a restricted AST. Code,
  names, power operators and oversized results are rejected.
- Persisted JSON is size/count bounded and sanitized on load.
- The game writes only to its own XDG data directory.
- No shell commands are built from user input.

Report vulnerabilities privately through GitHub Security Advisories on the
repository.
