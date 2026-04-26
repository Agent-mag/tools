# Security Review Rules

Review only vulnerabilities introduced or materially changed by the pull request.

## Reportable Findings

1. Injection into SQL, NoSQL, shell commands, templates, XML parsers, deserializers, file paths, or GraphQL resolvers.
2. Server-side authorization bypass, tenant isolation bypass, privilege escalation, or trusting client-controlled role/user identifiers.
3. Authentication bypass, unsafe session/token validation, missing signature checks, or predictable security tokens.
4. Sensitive data exposure to client responses, logs, public artifacts, error messages, or analytics payloads.
5. XSS only when an unsafe rendering sink exists, such as `dangerouslySetInnerHTML`, `innerHTML`, template bypass APIs, or direct HTML construction.
6. SSRF only when attacker input can control the host, protocol, or internal network target.
7. Weak crypto only when it protects security-sensitive data or auth state.
8. Insecure configuration that exposes admin/debug functionality or secrets.
9. GitHub Actions risks only when untrusted PR/user data can reach script execution, secret access, or privileged writes.
10. AI-agent risks only when untrusted model/user output can reach privileged tools, filesystem writes, network requests, shell commands, or secrets.

## Required Evidence

Each finding must include:

- A changed file path and line number when available.
- A specific source of attacker-controlled input.
- A specific sink or privileged operation.
- A realistic exploit scenario.
- A concrete fix recommendation.

Do not report issues without a clear source-to-sink path.
