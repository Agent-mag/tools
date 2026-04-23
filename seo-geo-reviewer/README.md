<div align="center">

<a href="https://theagentmag.com"><img src="https://theagentmag.com/brand/agentmag-banner-github.png" alt="Agent Mag" width="540" /></a>

<br /><br />

# SEO/GEO Auto-Fix Reviewer

**AI-powered GitHub Action that reviews PRs for SEO issues — and fixes them automatically.**

[![License: MIT](https://img.shields.io/badge/License-MIT-000?style=for-the-badge)](../LICENSE)
[![Agent Mag](https://img.shields.io/badge/by-Agent_Mag-000?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0id2hpdGUiPjxwYXRoIGQ9Ik0xMiAyTDIgMjJoMjBMMTIgMnoiLz48L3N2Zz4=)](https://theagentmag.com)

</div>

---

## What It Does

This GitHub Action runs on every PR and:

1. **Scans** changed files for SEO and GEO (Generative Engine Optimization) issues
2. **Produces patches** — exact search-and-replace fixes for every HIGH and MEDIUM finding
3. **Commits the fixes** directly to the PR branch via the GitHub Git Data API
4. **Posts a branded comment** summarizing what was found and what was auto-fixed

You merge. That's it. No manual SEO work.

## Quick Start

```yaml
# .github/workflows/seo-review.yml
name: SEO/GEO Auto-Fix Review

on:
  pull_request:
    types: [opened, synchronize, reopened]
    branches: [main]

permissions:
  contents: write
  pull-requests: write
  issues: write

concurrency:
  group: seo-review-${{ github.event.pull_request.number }}
  cancel-in-progress: true

jobs:
  review:
    if: github.event.pull_request.draft == false
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - name: Skip auto-fix commits
        id: skip-check
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          MSG=$(gh api repos/${{ github.repository }}/commits/${{ github.event.pull_request.head.sha }} --jq '.commit.message' 2>/dev/null || echo "")
          if echo "$MSG" | grep -q "^fix(seo): auto-fix SEO issues"; then
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

      - name: SEO/GEO Review
        if: steps.skip-check.outputs.skip != 'true'
        uses: Agent-mag/tools/seo-geo-reviewer@main
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          pr-number: ${{ github.event.pull_request.number }}
          base-sha: ${{ github.event.pull_request.base.sha }}
          head-sha: ${{ github.event.pull_request.head.sha }}
          anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
```

## Model Support

| Provider | Model | Config |
|----------|-------|--------|
| **Azure OpenAI** (primary) | GPT-5.4 | `azure-openai-endpoint`, `azure-openai-deployment`, `azure-openai-api-key` |
| **Anthropic** (fallback) | Claude Opus 4.6 | `anthropic-api-key` |

If Azure fails, it automatically falls back to Claude. You can use either or both.

## What Gets Reviewed

The reviewer checks 5 rule categories with 90+ rules:

| Category | What It Checks |
|----------|---------------|
| **Base SEO** | Metadata, titles, descriptions, canonicals, headings, image alt text, anchor text |
| **Technical SEO** | JSON-LD schemas, sitemaps, robots.txt, Core Web Vitals, crawl infrastructure |
| **Content SEO** | Article frontmatter, keyword usage, internal linking, word count, heading hierarchy |
| **GEO / Citation** | AI-citability, definitional openers, FAQ schemas, TL;DR blocks, entity consistency |
| **False Positives** | Known-good patterns that should never be flagged (Next.js idioms, decorative icons, etc.) |

## What Gets Auto-Fixed

The model produces **search-and-replace patches** for SEO-layer code only:

- Metadata exports (`title`, `description`, `canonical`, OpenGraph, Twitter)
- JSON-LD schema objects
- MDX frontmatter fields
- Internal link anchor text
- Heading hierarchy
- Component injection (`<RelatedContent>`, `<PageSchema>`)

It will **never** touch business logic, API routes, styling, or auth.

## PR Comment

Every review posts a branded comment on your PR:

![PR Comment Example](https://theagentmag.com/brand/agentmag-banner-github.png)

- **Verdict**: PASS / INFO / BLOCKING
- **Auto-fixed**: files patched with commit SHA
- **Remaining findings**: table of issues that couldn't be auto-fixed
- **What's working well**: positive SEO signals in your PR

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
| `comment-pr` | No | `true` | Post review comment on PR |
| `auto-fix` | No | `true` | Apply auto-fix patches |

## Outputs

| Output | Description |
|--------|-------------|
| `findings-count` | Remaining findings after auto-fix |
| `summary` | Human-readable summary (e.g. "0 high / 1 medium / 2 low") |

## Customizing Rules

The `rules/` directory contains markdown rulesets. Fork this repo and edit them to match your site's SEO strategy:

- `rules/base-seo.md` — on-page fundamentals
- `rules/technical-seo.md` — schemas, sitemaps, performance
- `rules/content-seo.md` — article/content quality
- `rules/geo-citation.md` — AI engine citability
- `rules/false-positives.md` — patterns to ignore

## How It Works

```
PR opened
  → Fetch changed files + full contents via GitHub API
  → Build prompt with file contents + diff + rulebook
  → Call GPT-5.4 (or Claude fallback)
  → Model returns JSON: findings[] + patches[]
  → Validate patches (exact string match, patchable file)
  → Apply via Git Data API (blob → tree → commit → ref update)
  → Post branded PR comment
  → Upload findings JSON as artifact
```

No cloning. No pushing. The entire fix happens through the GitHub API.

## License

MIT — see [LICENSE](../LICENSE).

---

<div align="center">

**Built by [Agent Mag](https://theagentmag.com)** — the magazine for AI agent builders.

</div>
