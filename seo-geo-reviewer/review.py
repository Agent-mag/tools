#!/usr/bin/env python3
"""
Agent Mag SEO/GEO Auto-Fix Reviewer.

Pipeline:
1. Fetch PR metadata + changed files via GitHub API.
2. Filter to SEO-relevant files.
3. Fetch full file contents (not just diff) for context.
4. Call Azure OpenAI GPT-5.4 (or Claude fallback) with SEO templates.
5. Model returns structured JSON: findings + concrete file patches.
6. Apply regex false-positive filter to findings.
7. Apply patches to PR branch via GitHub Git Data API (blob → tree → commit → ref).
8. Post summary comment with what was reviewed AND what was auto-fixed.
9. Write results to seo-geo-findings.json for artifact upload.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from github import Github
from github.PullRequest import PullRequest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from prompts import SYSTEM_PROMPT, load_rulebook, build_user_prompt
from filters import filter_findings, recount_summary, compute_verdict
from fixer import apply_patches, Patch

RELEVANT_EXTENSIONS = (
    ".tsx", ".ts", ".mdx", ".md", ".yml", ".yaml", ".json",
)

ALWAYS_RELEVANT = {
    "src/app/layout.tsx",
    "src/app/page.tsx",
    "src/app/sitemap.ts",
    "src/app/robots.ts",
    "src/app/llms.txt/route.ts",
    "src/app/llms-full.txt/route.ts",
    "src/app/ai-sitemap.xml/route.ts",
    "src/app/api/crawl-manifest/route.ts",
    "next.config.ts",
}

# Files the model is allowed to patch — SEO-relevant code only
PATCHABLE_PATTERNS = (
    "src/app/",           # page/layout/route files (metadata, schemas, links)
    "content/",           # MDX frontmatter
    "src/lib/seo/",       # SEO utilities
    "src/components/",    # components (footer links, anchor text, heading hierarchy)
    "src/data/",          # data files (authors, skills, jobs — schema/meta fields)
    "src/lib/articles.ts",  # article helpers
)


def filter_changed_files(files: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep only files relevant for SEO/GEO review."""
    kept: list[dict[str, Any]] = []
    for f in files:
        filename = f.get("filename", "")
        if not filename:
            continue
        if filename in ALWAYS_RELEVANT:
            kept.append(f)
            continue
        if any(filename.startswith(p) for p in ("node_modules/", ".next/", "dist/")):
            continue
        if filename.endswith((".lock", ".svg", ".png", ".jpg", ".webp", ".otf", ".ttf", ".ico")):
            continue
        if filename.startswith("src/types/"):
            continue
        if filename.endswith(RELEVANT_EXTENSIONS):
            kept.append(f)
    return kept


def is_patchable(filepath: str) -> bool:
    """Only allow patches to SEO-layer files."""
    return any(filepath.startswith(p) for p in PATCHABLE_PATTERNS)


def fetch_file_contents(repo, ref: str, filepaths: list[str], max_chars: int = 120_000) -> dict[str, str]:
    """Fetch full file contents from the repo at a given ref."""
    contents: dict[str, str] = {}
    total = 0
    for fp in filepaths:
        try:
            content_file = repo.get_contents(fp, ref=ref)
            if content_file.encoding == "base64":
                import base64
                text = base64.b64decode(content_file.content).decode("utf-8", errors="replace")
            else:
                text = content_file.decoded_content.decode("utf-8", errors="replace")
            if total + len(text) > max_chars:
                break
            contents[fp] = text
            total += len(text)
        except Exception:
            continue
    return contents


def build_diff_text(files: list[dict[str, Any]], max_chars: int = 30_000) -> str:
    """Concatenate per-file patches into a diff string."""
    chunks: list[str] = []
    total = 0
    for f in files:
        filename = f.get("filename", "")
        patch = f.get("patch", "") or ""
        if not patch:
            continue
        header = f"diff --git a/{filename} b/{filename}\n"
        block = header + patch + "\n"
        if total + len(block) > max_chars:
            chunks.append(f"\n... (truncated — diff exceeded {max_chars} chars) ...\n")
            break
        chunks.append(block)
        total += len(block)
    return "".join(chunks)


def call_azure_openai(system: str, user: str) -> str:
    """Call Azure OpenAI GPT-5.4."""
    from openai import AzureOpenAI

    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "").rstrip("/")
    deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "")
    api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2025-04-01-preview")
    api_key = os.environ.get("AZURE_OPENAI_API_KEY", "")

    if not (endpoint and deployment and api_key):
        raise RuntimeError("Azure OpenAI env vars not configured")

    client = AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
    )

    resp = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_object"},
        temperature=0.15,
        max_completion_tokens=16000,
    )
    return resp.choices[0].message.content or "{}"


def call_anthropic_fallback(system: str, user: str) -> str:
    """Fallback — call Claude Opus."""
    from anthropic import Anthropic

    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    client = Anthropic(api_key=key)
    resp = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=16000,
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user}],
    )
    parts: list[str] = []
    for block in resp.content:
        if getattr(block, "type", None) == "text":
            parts.append(block.text)
    raw = "".join(parts).strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json\n"):
            raw = raw[5:]
    return raw


def parse_response(raw: str) -> dict[str, Any]:
    """Parse the model response into findings + patches."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            try:
                data = json.loads(raw[start : end + 1])
            except json.JSONDecodeError:
                return _empty_result("JSON parse failed")
        else:
            return _empty_result("No JSON found in response")

    data.setdefault("summary", {"high": 0, "medium": 0, "low": 0})
    data.setdefault("findings", [])
    data.setdefault("positives", [])
    data.setdefault("patches", [])
    data.setdefault("overall_verdict", "COMMENT")
    return data


def _empty_result(error: str = "") -> dict[str, Any]:
    return {
        "summary": {"high": 0, "medium": 0, "low": 0},
        "findings": [],
        "positives": [],
        "patches": [],
        "overall_verdict": "COMMENT",
        **({"parse_error": error} if error else {}),
    }


def validate_patches(patches_raw: list[dict[str, Any]], file_contents: dict[str, str]) -> list[Patch]:
    """Validate patches: file must exist, search string must be found, file must be patchable."""
    valid: list[Patch] = []
    for i, p in enumerate(patches_raw):
        filepath = p.get("file", "")
        search = p.get("search", "")
        replace = p.get("replace", "")
        reason = p.get("reason", "")

        if not filepath or not search:
            print(f"  Patch {i}: SKIP — missing file or search string")
            continue
        if not is_patchable(filepath):
            print(f"  Patch {i}: SKIP — {filepath} not in PATCHABLE_PATTERNS")
            continue
        if filepath not in file_contents:
            print(f"  Patch {i}: SKIP — {filepath} not in fetched file contents (not a changed file?)")
            continue
        if search not in file_contents[filepath]:
            print(f"  Patch {i}: SKIP — search string not found verbatim in {filepath}")
            print(f"    Search (first 120 chars): {search[:120]!r}")
            continue
        if search == replace:
            print(f"  Patch {i}: SKIP — search == replace (no-op)")
            continue

        print(f"  Patch {i}: VALID — {filepath} ({reason})")
        valid.append(Patch(file=filepath, search=search, replace=replace))
    return valid


def format_comment(result: dict[str, Any], patches_applied: list[Patch], commit_sha: str | None) -> str:
    """Format the PR comment with findings + auto-fix summary."""
    summary = result["summary"]
    findings = result["findings"]
    positives = result.get("positives", [])
    verdict = result.get("overall_verdict", "COMMENT")

    verdict_label = {"APPROVE": "PASS", "COMMENT": "INFO", "REQUEST_CHANGES": "BLOCKING"}.get(verdict, "INFO")

    lines: list[str] = []
    lines.append("[![Agent Mag](https://theagentmag.com/brand/agentmag-banner-github.png)](https://theagentmag.com)")
    lines.append("")
    lines.append("## SEO/GEO Auto-Fix Review")
    lines.append("")
    lines.append(f"**Verdict**: `{verdict_label}` — {verdict}")
    lines.append(f"**Findings**: {summary.get('high', 0)} high · {summary.get('medium', 0)} medium · {summary.get('low', 0)} low")

    if patches_applied:
        lines.append(f"**Auto-fixed**: {len(patches_applied)} file{'s' if len(patches_applied) != 1 else ''} patched")
        if commit_sha:
            lines.append(f"**Fix commit**: `{commit_sha[:7]}`")
    lines.append("")

    if patches_applied:
        lines.append("### Auto-applied fixes")
        lines.append("")
        lines.append("The following SEO improvements were applied directly to this branch:")
        lines.append("")
        for patch in patches_applied:
            lines.append(f"- `{patch.file}` — patched")
        lines.append("")
        lines.append("> Review the fix commit above. If anything looks wrong, revert it.")
        lines.append("")

    if positives:
        lines.append("### What's working well")
        for p in positives[:5]:
            lines.append(f"- {p}")
        lines.append("")

    if findings:
        lines.append("### Remaining findings (not auto-fixed)")
        lines.append("")
        lines.append("| Sev | Category | Rule | File |")
        lines.append("|---|---|---|---|")
        for f in findings[:25]:
            sev = f.get("severity", "")
            cat = f.get("category", "")
            rule = f.get("rule", "")
            file_path = f.get("file", "")
            line = f.get("line")
            loc = f"`{file_path}`{f':{line}' if line else ''}"
            lines.append(f"| {sev} | {cat} | `{rule}` | {loc} |")
        if len(findings) > 25:
            lines.append("")
            lines.append(f"_... and {len(findings) - 25} more in the JSON artifact._")
        lines.append("")

        lines.append("<details><summary>Full findings detail</summary>")
        lines.append("")
        for f in findings:
            lines.append(f"#### `{f.get('severity', '')}` — {f.get('rule', '')}")
            lines.append(f"**File**: `{f.get('file', '')}`" + (f" (line {f.get('line')})" if f.get("line") else ""))
            lines.append("")
            lines.append(f"**Issue**: {f.get('issue', '')}")
            lines.append("")
            lines.append(f"**Suggested fix**: {f.get('suggestion', '')}")
            if f.get("citation_impact"):
                lines.append("")
                lines.append(f"**AI citation impact**: {f['citation_impact']}")
            lines.append("")
        lines.append("</details>")
        lines.append("")

    if not findings and not patches_applied and not positives:
        lines.append("No findings. Clean PR from an SEO/GEO perspective.")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("<sub>Powered by [Agent Mag](https://theagentmag.com) SEO/GEO Reviewer · GPT-5.4 specialist · [Rules](.github/actions/seo-geo-review/rules/) · [Get this tool](https://theagentmag.com/tools/seo-geo-reviewer)</sub>")
    return "\n".join(lines)


def post_comment(pr: PullRequest, body: str, marker: str = "<!-- agent-mag-seo-geo-review -->") -> None:
    """Post or update the PR comment, keyed by marker."""
    for comment in pr.get_issue_comments():
        if comment.body and marker in comment.body:
            comment.edit(marker + "\n" + body)
            return
    pr.create_issue_comment(marker + "\n" + body)


def main() -> int:
    token = os.environ["GITHUB_TOKEN"]
    repo_full = os.environ["GITHUB_REPOSITORY"]
    pr_number = int(os.environ["PR_NUMBER"])
    should_comment = os.environ.get("COMMENT_PR", "true").lower() == "true"
    auto_fix = os.environ.get("AUTO_FIX", "true").lower() == "true"
    action_path = os.environ.get("ACTION_PATH", os.path.dirname(os.path.abspath(__file__)))

    gh = Github(token)
    repo = gh.get_repo(repo_full)
    pr = repo.get_pull(pr_number)
    head_ref = pr.head.ref
    head_sha = pr.head.sha

    # 1. Gather changed files
    raw_files = list(pr.get_files())
    files_as_dicts = [
        {
            "filename": f.filename,
            "patch": f.patch,
            "status": f.status,
            "additions": f.additions,
            "deletions": f.deletions,
        }
        for f in raw_files
    ]
    relevant_files = filter_changed_files(files_as_dicts)

    if not relevant_files:
        print("No relevant files for SEO/GEO review.")
        Path("seo-geo-findings.json").write_text(json.dumps(_empty_result(), indent=2))
        if should_comment:
            post_comment(pr, "## SEO/GEO Auto-Fix Review — Agent Mag\n\nNo SEO-relevant files changed. Nothing to review.\n")
        _write_outputs(0, {"high": 0, "medium": 0, "low": 0})
        return 0

    changed_paths = [f["filename"] for f in relevant_files]

    # 2. Fetch full file contents for the model to read + patch
    # Also fetch key SEO files even if they weren't changed — model needs them for context
    extra_context = [f for f in ALWAYS_RELEVANT if f not in changed_paths]
    all_paths = changed_paths + extra_context[:5]
    print(f"Fetching full contents for {len(changed_paths)} changed + {min(len(extra_context), 5)} context files...")
    file_contents = fetch_file_contents(repo, head_sha, all_paths)

    # 3. Also build the diff for context
    diff_text = build_diff_text(relevant_files)

    # 4. Build prompts
    rulebook = load_rulebook(action_path)
    user_prompt = build_user_prompt(
        pr_title=pr.title or "",
        pr_body=pr.body or "",
        pr_number=pr_number,
        diff_text=diff_text,
        changed_files=changed_paths,
        file_contents=file_contents,
        rulebook=rulebook,
    )

    # 5. Call model
    raw: str = ""
    model_used = "none"
    try:
        raw = call_azure_openai(SYSTEM_PROMPT, user_prompt)
        model_used = "azure-gpt-5.4"
    except Exception as e:
        print(f"Azure OpenAI failed: {e}. Trying Anthropic fallback...")
        try:
            raw = call_anthropic_fallback(SYSTEM_PROMPT, user_prompt)
            model_used = "anthropic-claude-opus-4.6"
        except Exception as e2:
            print(f"Anthropic fallback also failed: {e2}")
            Path("seo-geo-findings.json").write_text(
                json.dumps({"error": f"both models failed: {e}; {e2}"}, indent=2)
            )
            if should_comment:
                post_comment(
                    pr,
                    "## SEO/GEO Auto-Fix Review — Agent Mag\n\n:warning: Review skipped: both model providers failed.\n",
                )
            return 0

    # 6. Parse response
    result = parse_response(raw)

    # 7. Filter false positives from findings
    result["findings"] = filter_findings(result.get("findings", []))
    result["summary"] = recount_summary(result["findings"])
    result["overall_verdict"] = compute_verdict(result["summary"])
    result["model_used"] = model_used

    # 8. Validate and apply patches
    patches_applied: list[Patch] = []
    commit_sha: str | None = None

    raw_patches = result.get("patches", [])
    print(f"Model returned {len(result.get('findings', []))} findings and {len(raw_patches)} patches.")

    if auto_fix and raw_patches:
        print(f"Validating {len(raw_patches)} patches...")
        valid_patches = validate_patches(raw_patches, file_contents)
        print(f"{len(valid_patches)} patches passed validation (out of {len(raw_patches)}).")
        if valid_patches:
            print(f"Applying {len(valid_patches)} patches to branch '{head_ref}'...")
            try:
                commit_sha = apply_patches(
                    repo=repo,
                    branch=head_ref,
                    base_sha=head_sha,
                    patches=valid_patches,
                    file_contents=file_contents,
                    commit_message="fix(seo): auto-fix SEO issues from GPT-5.4 review\n\nApplied by Agent Mag SEO/GEO Auto-Fix Reviewer.\nPatched files: " + ", ".join(p.file for p in valid_patches),
                )
                patches_applied = valid_patches
                print(f"Committed fixes: {commit_sha}")
            except Exception as e:
                print(f"Failed to apply patches: {e}")
                result["patch_error"] = str(e)

    # Remove auto-fixed findings from the remaining findings list
    if patches_applied:
        patched_files = {p.file for p in patches_applied}
        result["findings"] = [
            f for f in result["findings"]
            if f.get("file", "") not in patched_files
        ]
        result["summary"] = recount_summary(result["findings"])
        result["overall_verdict"] = compute_verdict(result["summary"])

    # 9. Write artifact
    result["patches_applied"] = [{"file": p.file} for p in patches_applied]
    result["fix_commit"] = commit_sha
    Path("seo-geo-findings.json").write_text(json.dumps(result, indent=2))

    # 10. Post comment
    if should_comment:
        comment_body = format_comment(result, patches_applied, commit_sha)
        post_comment(pr, comment_body)

    # 11. Outputs
    _write_outputs(len(result["findings"]), result["summary"])

    print(f"SEO/GEO Review complete. Findings: {len(result['findings'])}. Patches: {len(patches_applied)}. Model: {model_used}.")
    return 0


def _write_outputs(count: int, summary: dict[str, int]) -> None:
    gho = os.environ.get("GITHUB_OUTPUT")
    if gho:
        with open(gho, "a") as fh:
            fh.write(f"findings_count={count}\n")
            fh.write(f"summary={summary['high']} high / {summary['medium']} medium / {summary['low']} low\n")


if __name__ == "__main__":
    sys.exit(main())
