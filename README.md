<div align="center">

<img src="https://raw.githubusercontent.com/Agent-mag/.github/main/profile/agentmag-readme-banner.png" alt="Agent Mag" width="540" />

<br /><br />

# Open-Source Agent Tools

**Free, MIT-licensed tools for AI agent builders. Use them. Fork them. Make them better.**

[![Browse Tools](https://img.shields.io/badge/Browse_Tools-theagentmag.com/tools-000?style=for-the-badge&logo=google-chrome&logoColor=white)](https://theagentmag.com/tools)
[![License: MIT](https://img.shields.io/badge/License-MIT-000?style=for-the-badge)](LICENSE)

</div>

---

## What Is This Repo?

This is the home for **free, open-source tools** built by and for the AI agent builder community. Each tool lives in its own directory and solves a specific, real problem that builders face when developing, testing, or deploying agent systems.

### Skills vs. Tools

| | [Skills](https://github.com/Agent-mag/skills) | Tools (this repo) |
|---|---|---|
| **What** | Config bundles (prompts, tool schemas, manifests) | Executable code (CLIs, libraries, utilities) |
| **Install** | `npx agentmag add <skill>` | Per-tool instructions |
| **Runs code?** | No — config only | Yes |
| **Use case** | Teaching an agent a new capability | Helping builders develop, test, or deploy agents |

---

## Tool Categories

We're building and accepting tools across these areas:

| Category | What Belongs Here |
|----------|------------------|
| 🧪 **Agent Testing** | Evaluation harnesses, conversation replay, assertion libraries |
| ✏️ **Prompt Engineering** | Prompt linters, version control, A/B testing utilities |
| 📊 **Observability** | Trace viewers, cost trackers, latency profilers |
| 🔌 **MCP & Tool Use** | Model Context Protocol servers, tool schema validators |
| 🤝 **Multi-Agent** | Orchestration templates, message bus adapters |
| 🚀 **Deployment** | Dockerfiles, CI/CD templates, infra-as-code |

---

## Contributing a Tool

### Option A: Add to this repo

Best for smaller tools, utilities, and scripts.

1. Fork this repo
2. Create `tools/your-tool-name/` with source code, README, and tests
3. Open a PR

### Option B: Standalone repo

Best for larger tools that need their own CI, releases, and issues.

1. Build your tool in your own repo
2. Open an issue here with a link — we'll add it to the directory and feature it on [theagentmag.com/tools](https://theagentmag.com/tools)

### Tool Requirements

- **Solves a real problem.** Not a demo or proof-of-concept.
- **Has a README.** Install to working in under 5 minutes.
- **Has tests.** Doesn't need 100% coverage, but needs confidence.
- **MIT licensed.** Everything in this repo is MIT.
- **No vendor lock-in.** Tools should work with any LLM provider, not just one.

---

## Architecture

```
Community PR → This repo (public) → Automated checks → Merge → Webhook → theagentmag.com/tools
```

This repo is public. The Agent Mag platform (private) syncs tool metadata from here on every merge. Contributors only interact with this public repo.

---

## License

MIT — see [LICENSE](LICENSE) for details.
