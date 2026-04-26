<div align="center">

<a href="https://theagentmag.com"><img src="https://theagentmag.com/brand/agentmag-banner-github.png" alt="Agent Mag" width="540" /></a>

<br /><br />

# PR Security Auto-Fix

**AI-powered GitHub Action that reviews pull requests for security issues and commits safe fixes automatically.**

[![License: MIT](https://img.shields.io/badge/License-MIT-000?style=for-the-badge)](../LICENSE)
[![Agent Mag](https://img.shields.io/badge/by-Agent_Mag-000?style=for-the-badge)](https://theagentmag.com)

</div>

---

## What It Does

PR Security Auto-Fix runs on pull requests and:

1. **Scans changed files** for high-confidence security vulnerabilities
2. **Filters noise** so it avoids generic hardening and theoretical findings
3. **Produces safe patches** for small, local fixes
4. **Commits fixes** directly to trusted PR branches
5. **Posts a branded PR comment** with verdict, exploit path, recommendations, and fix summary

It is intentionally conservative. The action reports concrete exploit paths and only auto-fixes changes it can validate with exact search-and-replace patches.

## Quick Start

### Option A: One command via Agent Mag

```bash
npx agentmag add tool pr-security-auto-fix
```

This scaffolds `.github/workflows/pr-security-auto-fix.yml`. Add the required model secret(s), then open a pull request.

### Option B: Manual setup

```yaml
name: PR Security Auto-Fix

on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]
    branches: [main]

permissions:
  contents: write
  pull-requests: write
  issues: write

concurrency:
  group: pr-security-auto-fix-${{ github.event.pull_request.number }}
  cancel-in-progress: true

jobs:
  security:
    if: github.event.pull_request.draft == false
    runs-on: ubuntu-latest
    timeout-minutes: 15

    steps:
      - name: Skip auto-fix commits
        id: skip-check
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          MSG=$(gh api repos/${{ github.repository }}/commits/${{ github.event.pull_request.head.sha }} --jq '.commit.message' 2>/dev/null || echo "")
          if echo "$MSG" | grep -q "^fix(security): auto-fix PR security issues"; then
            echo "skip=true" >> "$GITHUB_OUTPUT"
          else
            echo "skip=false" >> "$GITHUB_OUTPUT"
          fi

      - name: Checkout
        if: steps.skip-check.outputs.skip != 'true'
        uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.sha }}
          fetch-depth: 0

      - name: Setup Python
        if: steps.skip-check.outputs.skip != 'true'
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: PR Security Auto-Fix
        if: steps.skip-check.outputs.skip != 'true'
        uses: Agent-mag/tools/pr-security-auto-fix@main
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          pr-number: ${{ github.event.pull_request.number }}
          base-sha: ${{ github.event.pull_request.base.sha }}
          head-sha: ${{ github.event.pull_request.head.sha }}
          azure-openai-endpoint: ${{ secrets.AZURE_OPENAI_GPT54_ENDPOINT }}
          azure-openai-deployment: ${{ secrets.AZURE_OPENAI_GPT54_DEPLOYMENT }}
          azure-openai-api-version: ${{ secrets.AZURE_OPENAI_GPT54_API_VERSION }}
          azure-openai-api-key: ${{ secrets.AZURE_OPENAI_GPT54_KEY }}
          anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
          validation-command: "npm run lint"
```

## Model Support

| Provider | Model | Config |
|----------|-------|--------|
| **Azure OpenAI** (primary) | GPT-5.4 | `azure-openai-endpoint`, `azure-openai-deployment`, `azure-openai-api-key` |
| **Anthropic** (fallback) | Claude Opus 4.6 | `anthropic-api-key` |

Use either provider or both. Azure runs first when configured.

## What Gets Reviewed

PR Security Auto-Fix focuses on high-confidence vulnerabilities:

- SQL/NoSQL/command/template/path injection
- Authentication and authorization bypasses
- Tenant isolation failures
- Sensitive data exposure
- Unsafe HTML rendering and concrete XSS
- SSRF with attacker-controlled host/protocol
- Weak crypto in security-sensitive flows
- Dangerous GitHub Actions patterns
- AI-agent tool abuse paths

It deliberately skips noisy categories like DoS, generic rate limiting, missing audit logs, docs-only findings, test-only files, dependency CVEs, and theoretical hardening.

## What Gets Auto-Fixed

Auto-fixes are limited to small, local patches:

- Add obvious server-side auth checks using existing helpers
- Parameterize query or shell sinks
- Redact sensitive logging
- Validate SSRF/redirect targets
- Restrict unsafe CORS/allowlists
- Replace unsafe HTML sinks with escaped/sanitized output

Every patch must:

- Match an exact unique `search` string
- Map to a surviving HIGH or MEDIUM finding
- Have confidence of at least `0.85`
- Touch only changed source/config files
- Pass `validation-command` when configured

## Security Boundary

This action is designed for trusted PRs. By default, `trusted-only: true` skips forked PRs before model calls or writes. Do not run this with `pull_request_target` against untrusted code.

## Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `github-token` | Yes | — | Token with `contents:write` + `pull-requests:write` |
| `pr-number` | Yes | — | PR number |
| `base-sha` | Yes | — | PR base SHA |
| `head-sha` | Yes | — | PR head SHA |
| `azure-openai-endpoint` | No | — | Azure OpenAI endpoint URL |
| `azure-openai-deployment` | No | — | Azure OpenAI deployment name |
| `azure-openai-api-version` | No | `2025-04-01-preview` | Azure API version |
| `azure-openai-api-key` | No | — | Azure OpenAI API key |
| `anthropic-api-key` | No | — | Anthropic API key |
| `comment-pr` | No | `true` | Post/update PR comment |
| `auto-fix` | No | `true` | Commit safe fixes to trusted PR branch |
| `trusted-only` | No | `true` | Skip forked PRs |
| `max-patches` | No | `5` | Max auto-fixes per run |
| `validation-command` | No | — | Command to run before committing patches |
| `exclude-directories` | No | — | Comma-separated extra directories to skip |
| `custom-security-scan-instructions` | No | — | Extra scan prompt file |
| `false-positive-filtering-instructions` | No | — | Extra false-positive prompt file |

## Outputs

| Output | Description |
|--------|-------------|
| `findings-count` | Remaining findings after auto-fix |
| `summary` | Summary string |
| `verdict` | `APPROVE`, `COMMENT`, or `REQUEST_CHANGES` |
| `results-file` | `pr-security-auto-fix-findings.json` |

## Customizing Rules

Fork this repo and edit:

- `rules/security-review.md`
- `rules/auto-fix.md`
- `rules/false-positives.md`
- `rules/language-patterns.md`

## License

MIT — see [LICENSE](../LICENSE).

---

<div align="center">

**Built by [Agent Mag](https://theagentmag.com)** — the magazine for AI agent builders.

</div>
