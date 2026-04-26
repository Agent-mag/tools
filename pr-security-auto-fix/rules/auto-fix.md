# Auto-Fix Rules

Auto-fix only safe, local, low-risk issues.

## Allowed Patches

1. Parameterize or escape a query when the local database API pattern is clear.
2. Add or restore a missing server-side authorization check when nearby code shows the intended helper.
3. Remove, redact, or narrow sensitive logging.
4. Validate URL host/protocol before a server-side fetch.
5. Restrict permissive CORS or redirect allowlists.
6. Replace an unsafe rendering sink with escaped text or an existing sanitizer.
7. Add input validation immediately before a dangerous sink.
8. Fix unsafe GitHub Actions shell interpolation when the safe environment-variable pattern is obvious.

## Disallowed Patches

1. Do not add new dependencies.
2. Do not rewrite broad architecture.
3. Do not guess business authorization policy.
4. Do not edit tests, docs, lockfiles, generated files, public assets, or workflow files.
5. Do not disable security controls, lint rules, type checks, or tests.
6. Do not delete functionality just to remove a finding.
7. Do not produce a patch unless the exact `search` string appears once in the file.

If the issue is real but the safe fix is not obvious, report the finding without a patch.
