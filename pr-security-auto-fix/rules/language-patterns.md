# Language And Framework Patterns

## JavaScript / TypeScript / Next.js

- API routes, route handlers, server actions, and middleware/proxy files are security-sensitive.
- Do not report ordinary React interpolation as XSS.
- Report `dangerouslySetInnerHTML`, `innerHTML`, `eval`, `new Function`, command execution, unsafe redirects, public server-side fetches, and server-side auth bypasses when attacker-controlled input reaches them.
- For MongoDB, report direct use of untrusted objects in query operators when the code does not normalize to expected scalar fields.

## Python

- Report unsafe `subprocess` with `shell=True`, `pickle`, unsafe YAML loading, path traversal, SQL string interpolation, SSRF, and auth bypasses.
- Do not report command injection in scripts unless they process untrusted runtime input.

## GitHub Actions

- Prefer environment variables over direct expression interpolation inside shell scripts.
- Report `pull_request_target` only when combined with checking out or executing untrusted PR code with write/secrets permissions.
- Report script execution from PR-controlled strings only when the path is concrete.

## Infrastructure

- Report public debug/admin surfaces, permissive CORS with credentials, disabled TLS/certificate validation, and secret material committed into config.
- Do not report broad best-practice hardening without an exploit path.
