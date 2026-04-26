# False Positive Rules

Exclude these from findings unless there is an unusually direct and high-impact exploit path.

1. Denial of service, rate limiting, memory exhaustion, CPU exhaustion, regex DoS, and resource leaks.
2. Missing audit logs or monitoring.
3. Documentation-only concerns.
4. Test-only or fixture-only code.
5. Generic lack of validation without security impact.
6. Open redirects, tabnabbing, XS-Leaks, log spoofing, and clickjacking.
7. Outdated dependencies or known CVEs.
8. React, Angular, or Vue rendering of normal escaped text.
9. Client-side authorization checks unless server-side code also trusts them.
10. Attacks requiring control of trusted environment variables, deployment config, or repository secrets.
11. Prompt injection claims where no privileged tool, secret, or sensitive data can be reached.
12. Shell script injection unless untrusted runtime input reaches the script in CI or production.

Only include MEDIUM findings when the exploit is concrete and actionable.
