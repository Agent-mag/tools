#!/usr/bin/env python3
"""
Agent Mag PR Security Auto-Fix.

Pipeline:
1. Fetch PR metadata and changed files via GitHub API.
2. Filter to security-relevant files.
3. Chunk changed file contents + diffs for model limits.
4. Call Azure OpenAI GPT-5.4, with Anthropic fallback.
5. Parse structured JSON findings and safe patches.
6. Apply false-positive filtering and patch validation.
7. Optionally apply patches locally and run a validation command.
8. Commit validated patches to the PR branch via GitHub Git Data API.
9. Post/update a branded PR comment and upload JSON results.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from github import Github
from github.PullRequest import PullRequest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from filters import compute_verdict, filter_findings, recount_summary, is_excluded_path
from fixer import Patch, apply_patches, apply_to_contents
from prompts import SYSTEM_PROMPT, build_user_prompt, load_rulebook, read_optional_instruction

RESULTS_FILE = "pr-security-auto-fix-findings.json"
COMMENT_MARKER = "<!-- agent-mag-pr-security-auto-fix -->"

REVIEWABLE_EXTENSIONS = (
    ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
    ".py", ".rb", ".php", ".go", ".rs", ".java", ".kt", ".kts",
    ".cs", ".scala", ".swift", ".c", ".cc", ".cpp", ".h", ".hpp",
    ".sql", ".graphql", ".gql", ".json", ".yaml", ".yml", ".toml",
    ".tf", ".tfvars", ".sh", ".bash", ".zsh", ".ps1",
)

REVIEWABLE_FILENAMES = {
    "Dockerfile",
    "Containerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "next.config.js",
    "next.config.mjs",
    "next.config.ts",
    "vite.config.js",
    "vite.config.ts",
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "go.mod",
    "Cargo.toml",
}

NEVER_PATCH_PREFIXES = (
    ".github/",
    "docs/",
    "public/",
    "assets/",
)

DEFAULT_EXCLUDE_DIRECTORIES = (
    "node_modules/",
    "vendor/",
    ".next/",
    "dist/",
    "build/",
    "coverage/",
)

MIN_PATCH_CONFIDENCE = 0.85


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except ValueError:
        return default


def _confidence(value: Any) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return 0.0
    return score / 10 if score > 1 else score


def _normalize_exclude_dirs(raw: str) -> list[str]:
    dirs = list(DEFAULT_EXCLUDE_DIRECTORIES)
    for part in raw.split(","):
        cleaned = part.strip().lstrip("./")
        if not cleaned:
            continue
        dirs.append(cleaned if cleaned.endswith("/") else f"{cleaned}/")
    return dirs


def _is_reviewable_path(path: str, exclude_dirs: list[str]) -> bool:
    normalized = path.lstrip("./")
    if any(normalized.startswith(prefix) for prefix in exclude_dirs):
        return False
    if is_excluded_path(normalized):
        return False
    name = Path(normalized).name
    if name in REVIEWABLE_FILENAMES:
        return True
    return normalized.endswith(REVIEWABLE_EXTENSIONS)


def _is_patchable_path(path: str, changed_paths: set[str]) -> bool:
    normalized = path.lstrip("./")
    if normalized not in changed_paths:
        return False
    if any(normalized.startswith(prefix) for prefix in NEVER_PATCH_PREFIXES):
        return False
    if is_excluded_path(normalized):
        return False
    name = Path(normalized).name
    return name in REVIEWABLE_FILENAMES or normalized.endswith(REVIEWABLE_EXTENSIONS)


def filter_changed_files(files: list[dict[str, Any]], exclude_dirs: list[str]) -> list[dict[str, Any]]:
    kept: list[dict[str, Any]] = []
    for file in files:
        filename = str(file.get("filename", ""))
        if not filename:
            continue
        if file.get("status") == "removed":
            continue
        if _is_reviewable_path(filename, exclude_dirs):
            kept.append(file)
    return kept


def fetch_file_contents(repo, ref: str, filepaths: list[str], max_file_chars: int = 28_000) -> dict[str, str]:
    contents: dict[str, str] = {}
    for filepath in filepaths:
        try:
            content_file = repo.get_contents(filepath, ref=ref)
            if isinstance(content_file, list):
                continue
            if content_file.encoding == "base64":
                import base64

                text = base64.b64decode(content_file.content).decode("utf-8", errors="replace")
            else:
                text = content_file.decoded_content.decode("utf-8", errors="replace")
            if len(text) > max_file_chars:
                text = text[:max_file_chars] + "\n\n/* ... truncated by PR Security Auto-Fix ... */\n"
            contents[filepath] = text
        except Exception as exc:
            print(f"Unable to fetch {filepath}: {exc}")
            continue
    return contents


def build_diff_text(files: list[dict[str, Any]], max_chars: int = 24_000) -> str:
    chunks: list[str] = []
    total = 0
    for file in files:
        filename = str(file.get("filename", ""))
        patch = file.get("patch", "") or ""
        if not patch:
            continue
        block = f"diff --git a/{filename} b/{filename}\n{patch}\n"
        if total + len(block) > max_chars:
            chunks.append(f"\n... truncated at {max_chars} chars ...\n")
            break
        chunks.append(block)
        total += len(block)
    return "".join(chunks)


def chunk_files(files: list[dict[str, Any]], file_contents: dict[str, str], max_chars: int) -> list[list[dict[str, Any]]]:
    chunks: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    current_size = 0

    for file in files:
        filename = str(file.get("filename", ""))
        size = len(file_contents.get(filename, "")) + len(file.get("patch", "") or "") + 600
        if current and current_size + size > max_chars:
            chunks.append(current)
            current = []
            current_size = 0
        current.append(file)
        current_size += size

    if current:
        chunks.append(current)
    return chunks


def call_azure_openai(system: str, user: str) -> str:
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

    last_error: Exception | None = None
    for attempt in range(3):
        try:
            resp = client.chat.completions.create(
                model=deployment,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_completion_tokens=6000,
            )
            return resp.choices[0].message.content or "{}"
        except Exception as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(8 * (attempt + 1))
    raise RuntimeError(f"Azure OpenAI failed: {last_error}")


def call_anthropic_fallback(system: str, user: str) -> str:
    from anthropic import Anthropic

    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    client = Anthropic(api_key=key)
    resp = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=6000,
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
        "overall_verdict": "APPROVE",
        **({"error": error} if error else {}),
    }


def _merge_chunk_result(
    aggregate: dict[str, Any],
    chunk_result: dict[str, Any],
    next_id: int,
) -> int:
    id_map: dict[str, str] = {}

    for finding in chunk_result.get("findings", []):
        old_id = str(finding.get("id") or f"finding-{next_id}")
        new_id = f"SEC-{next_id:03d}"
        next_id += 1
        id_map[old_id] = new_id
        finding["id"] = new_id
        finding["confidence"] = _confidence(finding.get("confidence"))
        aggregate["findings"].append(finding)

    for patch in chunk_result.get("patches", []):
        old_finding_id = str(patch.get("finding_id", ""))
        if old_finding_id in id_map:
            patch["finding_id"] = id_map[old_finding_id]
            aggregate["patches"].append(patch)

    for positive in chunk_result.get("positives", []):
        if positive not in aggregate["positives"]:
            aggregate["positives"].append(positive)

    return next_id


def validate_patches(
    patches_raw: list[dict[str, Any]],
    file_contents: dict[str, str],
    changed_paths: set[str],
    findings: list[dict[str, Any]],
    max_patches: int,
) -> list[Patch]:
    findings_by_id = {str(f.get("id")): f for f in findings}
    valid: list[Patch] = []

    for i, patch_raw in enumerate(patches_raw):
        if len(valid) >= max_patches:
            print(f"  Patch {i}: SKIP - max patch count reached")
            break

        finding_id = str(patch_raw.get("finding_id", ""))
        finding = findings_by_id.get(finding_id)
        filepath = str(patch_raw.get("file", "")).lstrip("./")
        search = str(patch_raw.get("search", ""))
        replace = str(patch_raw.get("replace", ""))
        reason = str(patch_raw.get("reason", ""))

        if not finding:
            print(f"  Patch {i}: SKIP - no surviving finding for {finding_id}")
            continue
        if str(finding.get("severity", "")).upper() not in {"HIGH", "MEDIUM"}:
            print(f"  Patch {i}: SKIP - severity is not HIGH/MEDIUM")
            continue
        if _confidence(finding.get("confidence")) < MIN_PATCH_CONFIDENCE:
            print(f"  Patch {i}: SKIP - confidence below {MIN_PATCH_CONFIDENCE}")
            continue
        if not filepath or not search or not replace:
            print(f"  Patch {i}: SKIP - missing file/search/replace")
            continue
        if not _is_patchable_path(filepath, changed_paths):
            print(f"  Patch {i}: SKIP - {filepath} is not patchable")
            continue
        if filepath not in file_contents:
            print(f"  Patch {i}: SKIP - {filepath} not fetched")
            continue
        count = file_contents[filepath].count(search)
        if count == 0:
            print(f"  Patch {i}: SKIP - search string not found in {filepath}")
            continue
        if count > 1:
            print(f"  Patch {i}: SKIP - search string ambiguous in {filepath}")
            continue
        if search == replace:
            print(f"  Patch {i}: SKIP - no-op patch")
            continue
        if len(replace) > max(12_000, len(search) * 8):
            print(f"  Patch {i}: SKIP - replacement too large for safe auto-fix")
            continue

        print(f"  Patch {i}: VALID - {filepath} ({reason})")
        valid.append(Patch(file=filepath, search=search, replace=replace, finding_id=finding_id, reason=reason))

    return valid


def write_patches_to_workspace(file_contents: dict[str, str], patches: list[Patch]) -> None:
    modified = apply_to_contents(file_contents, patches)
    root = Path.cwd().resolve()
    for filepath, content in modified.items():
        target = (root / filepath).resolve()
        if root not in target.parents and target != root:
            raise ValueError(f"Refusing to write outside workspace: {filepath}")
        target.write_text(content)


def run_validation(command: str) -> tuple[bool, str]:
    if not command.strip():
        return True, ""
    proc = subprocess.run(
        command,
        shell=True,
        cwd=Path.cwd(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=300,
    )
    output = proc.stdout[-4000:] if proc.stdout else ""
    return proc.returncode == 0, output


def format_comment(result: dict[str, Any], patches_applied: list[Patch], commit_sha: str | None) -> str:
    summary = result["summary"]
    findings = result["findings"]
    positives = result.get("positives", [])
    verdict = result.get("overall_verdict", "COMMENT")
    verdict_label = {"APPROVE": "PASS", "COMMENT": "INFO", "REQUEST_CHANGES": "BLOCKING"}.get(verdict, "INFO")

    lines: list[str] = [
        "[![Agent Mag](https://theagentmag.com/brand/agentmag-banner-github.png)](https://theagentmag.com)",
        "",
        "## PR Security Auto-Fix Review",
        "",
        f"**Verdict**: `{verdict_label}` - {verdict}",
        f"**Findings**: {summary.get('high', 0)} high · {summary.get('medium', 0)} medium · {summary.get('low', 0)} low",
    ]

    if result.get("model_used"):
        lines.append(f"**Model**: {result['model_used']}")

    if patches_applied:
        lines.append(f"**Auto-fixed**: {len(patches_applied)} patch{'es' if len(patches_applied) != 1 else ''} applied")
        if commit_sha:
            lines.append(f"**Fix commit**: `{commit_sha[:7]}`")
    lines.append("")

    if result.get("skipped_reason"):
        lines.append(f":warning: {result['skipped_reason']}")
        lines.append("")

    if patches_applied:
        lines.append("### Auto-applied fixes")
        lines.append("")
        for patch in patches_applied:
            label = f"{patch.finding_id}: " if patch.finding_id else ""
            lines.append(f"- `{patch.file}` - {label}{patch.reason or 'security patch'}")
        lines.append("")
        lines.append("> Review the fix commit. If anything looks wrong, revert that commit.")
        lines.append("")

    if positives:
        lines.append("### Secure patterns in this PR")
        for positive in positives[:5]:
            lines.append(f"- {positive}")
        lines.append("")

    if findings:
        lines.append("### Remaining findings")
        lines.append("")
        lines.append("| Sev | Conf | Category | Rule | File |")
        lines.append("|---|---:|---|---|---|")
        for finding in findings[:25]:
            sev = finding.get("severity", "")
            confidence = _confidence(finding.get("confidence"))
            category = finding.get("category", "")
            rule = finding.get("rule", "")
            file_path = finding.get("file", "")
            line = finding.get("line")
            loc = f"`{file_path}`{f':{line}' if line else ''}"
            lines.append(f"| {sev} | {confidence:.2f} | {category} | `{rule}` | {loc} |")
        if len(findings) > 25:
            lines.append("")
            lines.append(f"_... and {len(findings) - 25} more in the JSON artifact._")
        lines.append("")

        lines.append("<details><summary>Finding details</summary>")
        lines.append("")
        for finding in findings:
            lines.append(f"#### `{finding.get('severity', '')}` - {finding.get('id', '')}: {finding.get('rule', '')}")
            lines.append(f"**File**: `{finding.get('file', '')}`" + (f" (line {finding.get('line')})" if finding.get("line") else ""))
            lines.append("")
            lines.append(f"**Issue**: {finding.get('issue', '')}")
            lines.append("")
            lines.append(f"**Exploit scenario**: {finding.get('exploit_scenario', '')}")
            lines.append("")
            lines.append(f"**Recommendation**: {finding.get('recommendation', '')}")
            lines.append("")
        lines.append("</details>")
        lines.append("")

    if not findings and not patches_applied and not result.get("skipped_reason"):
        lines.append("No high-confidence security findings in the changed files.")

    if result.get("patch_error"):
        lines.append("")
        lines.append(f":warning: Auto-fix skipped: `{result['patch_error']}`")

    lines.extend([
        "",
        "---",
        "",
        "<sub>Powered by [Agent Mag](https://theagentmag.com) PR Security Auto-Fix · GPT-5.4 specialist · [Get this tool](https://theagentmag.com/tools/pr-security-auto-fix)</sub>",
    ])
    return "\n".join(lines)


def post_comment(pr: PullRequest, body: str) -> None:
    for comment in pr.get_issue_comments():
        if comment.body and COMMENT_MARKER in comment.body:
            comment.edit(COMMENT_MARKER + "\n" + body)
            return
    pr.create_issue_comment(COMMENT_MARKER + "\n" + body)


def _write_outputs(count: int, summary: dict[str, int], verdict: str) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return
    with open(output_path, "a") as handle:
        handle.write(f"findings_count={count}\n")
        handle.write(f"summary={summary['high']} high / {summary['medium']} medium / {summary['low']} low\n")
        handle.write(f"verdict={verdict}\n")


def _write_result(result: dict[str, Any]) -> None:
    Path(RESULTS_FILE).write_text(json.dumps(result, indent=2))


def main() -> int:
    token = os.environ["GITHUB_TOKEN"]
    repo_full = os.environ["GITHUB_REPOSITORY"]
    pr_number = int(os.environ["PR_NUMBER"])
    should_comment = _env_bool("COMMENT_PR", True)
    auto_fix = _env_bool("AUTO_FIX", True)
    trusted_only = _env_bool("TRUSTED_ONLY", True)
    max_patches = max(0, _env_int("MAX_PATCHES", 5))
    validation_command = os.environ.get("VALIDATION_COMMAND", "").strip()
    exclude_dirs = _normalize_exclude_dirs(os.environ.get("EXCLUDE_DIRECTORIES", ""))
    chunk_max_chars = _env_int("SECURITY_CHUNK_MAX_CHARS", 32_000)
    action_path = os.environ.get("ACTION_PATH", os.path.dirname(os.path.abspath(__file__)))

    gh = Github(token)
    repo = gh.get_repo(repo_full)
    pr = repo.get_pull(pr_number)
    head_ref = pr.head.ref
    head_sha = pr.head.sha
    head_repo = pr.head.repo.full_name if pr.head.repo else repo_full
    is_trusted = head_repo == repo_full

    if not is_trusted and trusted_only:
        result = _empty_result("Skipped untrusted PR")
        result["skipped_reason"] = "Review skipped because this PR comes from a fork and `trusted-only` is enabled."
        result["overall_verdict"] = "COMMENT"
        _write_result(result)
        if should_comment:
            post_comment(pr, format_comment(result, [], None))
        _write_outputs(0, result["summary"], result["overall_verdict"])
        return 0

    if not is_trusted:
        print("Untrusted/fork PR detected. Disabling auto-fix.")
        auto_fix = False

    raw_files = list(pr.get_files())
    files_as_dicts = [
        {
            "filename": file.filename,
            "patch": file.patch,
            "status": file.status,
            "additions": file.additions,
            "deletions": file.deletions,
        }
        for file in raw_files
    ]
    relevant_files = filter_changed_files(files_as_dicts, exclude_dirs)

    if not relevant_files:
        result = _empty_result()
        result["skipped_reason"] = "No security-relevant changed files were found."
        result["overall_verdict"] = "APPROVE"
        _write_result(result)
        if should_comment:
            post_comment(pr, format_comment(result, [], None))
        _write_outputs(0, result["summary"], result["overall_verdict"])
        return 0

    changed_paths = [str(file["filename"]) for file in relevant_files]
    changed_path_set = set(changed_paths)
    print(f"Fetching full contents for {len(changed_paths)} changed files...")
    file_contents = fetch_file_contents(repo, head_sha, changed_paths)
    relevant_files = [file for file in relevant_files if file["filename"] in file_contents]

    rulebook = load_rulebook(action_path)
    custom_scan = read_optional_instruction(action_path, os.environ.get("CUSTOM_SECURITY_SCAN_INSTRUCTIONS", ""))
    false_positive_scan = read_optional_instruction(action_path, os.environ.get("FALSE_POSITIVE_FILTERING_INSTRUCTIONS", ""))

    aggregate = _empty_result()
    aggregate["overall_verdict"] = "COMMENT"
    aggregate["chunks"] = []
    next_id = 1
    model_used = "none"

    chunks = chunk_files(relevant_files, file_contents, chunk_max_chars)
    print(f"Reviewing {len(relevant_files)} files in {len(chunks)} chunk(s).")

    for index, chunk in enumerate(chunks, start=1):
        chunk_paths = [str(file["filename"]) for file in chunk]
        chunk_contents = {path: file_contents[path] for path in chunk_paths if path in file_contents}
        diff_text = build_diff_text(chunk)
        user_prompt = build_user_prompt(
            repo_full_name=repo_full,
            pr_title=pr.title or "",
            pr_body=pr.body or "",
            pr_number=pr_number,
            diff_text=diff_text,
            changed_files=chunk_paths,
            file_contents=chunk_contents,
            rulebook=rulebook,
            custom_scan_instructions=custom_scan,
            false_positive_instructions=false_positive_scan,
        )

        raw = ""
        try:
            raw = call_azure_openai(SYSTEM_PROMPT, user_prompt)
            model_used = "azure-gpt-5.4"
        except Exception as azure_error:
            print(f"Azure OpenAI failed on chunk {index}: {azure_error}. Trying Anthropic fallback...")
            try:
                raw = call_anthropic_fallback(SYSTEM_PROMPT, user_prompt)
                model_used = "anthropic-claude-opus-4.6"
            except Exception as anthropic_error:
                print(f"Anthropic fallback failed on chunk {index}: {anthropic_error}")
                aggregate.setdefault("model_errors", []).append(
                    {
                        "chunk": index,
                        "azure_error": str(azure_error),
                        "anthropic_error": str(anthropic_error),
                    }
                )
                continue

        chunk_result = parse_response(raw)
        if chunk_result.get("error"):
            aggregate.setdefault("model_errors", []).append(
                {"chunk": index, "parse_error": chunk_result.get("error")}
            )
        next_id = _merge_chunk_result(aggregate, chunk_result, next_id)
        aggregate["chunks"].append({"index": index, "files": chunk_paths})

    aggregate["model_used"] = model_used
    if not aggregate["chunks"] and aggregate.get("model_errors"):
        aggregate["skipped_reason"] = "Review skipped because all model calls failed or returned invalid JSON."
        aggregate["overall_verdict"] = "COMMENT"
        _write_result(aggregate)
        if should_comment:
            post_comment(pr, format_comment(aggregate, [], None))
        _write_outputs(0, aggregate["summary"], aggregate["overall_verdict"])
        return 0

    aggregate["findings"] = filter_findings(aggregate.get("findings", []))
    aggregate["summary"] = recount_summary(aggregate["findings"])
    aggregate["overall_verdict"] = compute_verdict(aggregate["summary"])

    raw_patches = aggregate.get("patches", [])
    patches_applied: list[Patch] = []
    commit_sha: str | None = None
    print(f"Model returned {len(aggregate['findings'])} findings and {len(raw_patches)} candidate patches.")

    if auto_fix and raw_patches and max_patches > 0:
        valid_patches = validate_patches(
            raw_patches,
            file_contents,
            changed_path_set,
            aggregate["findings"],
            max_patches,
        )
        print(f"{len(valid_patches)} patches passed validation.")
        if valid_patches:
            try:
                if validation_command:
                    print(f"Applying patches locally and running validation: {validation_command}")
                    write_patches_to_workspace(file_contents, valid_patches)
                    ok, output = run_validation(validation_command)
                    aggregate["validation_command"] = validation_command
                    aggregate["validation_output"] = output
                    if not ok:
                        raise RuntimeError("validation command failed")

                commit_sha = apply_patches(
                    repo=repo,
                    branch=head_ref,
                    base_sha=head_sha,
                    patches=valid_patches,
                    file_contents=file_contents,
                    commit_message=(
                        "fix(security): auto-fix PR security issues\n\n"
                        "Applied by Agent Mag PR Security Auto-Fix.\n"
                        "Patched files: " + ", ".join(sorted({patch.file for patch in valid_patches}))
                    ),
                )
                patches_applied = valid_patches
                print(f"Committed fixes: {commit_sha}")
            except Exception as exc:
                print(f"Failed to apply patches: {exc}")
                aggregate["patch_error"] = str(exc)

    if patches_applied:
        patched_finding_ids = {patch.finding_id for patch in patches_applied if patch.finding_id}
        aggregate["findings"] = [
            finding for finding in aggregate["findings"]
            if str(finding.get("id", "")) not in patched_finding_ids
        ]
        aggregate["summary"] = recount_summary(aggregate["findings"])
        aggregate["overall_verdict"] = compute_verdict(aggregate["summary"])

    aggregate["patches_applied"] = [
        {"finding_id": patch.finding_id, "file": patch.file, "reason": patch.reason}
        for patch in patches_applied
    ]
    aggregate["fix_commit"] = commit_sha
    _write_result(aggregate)

    if should_comment:
        post_comment(pr, format_comment(aggregate, patches_applied, commit_sha))

    _write_outputs(len(aggregate["findings"]), aggregate["summary"], aggregate["overall_verdict"])
    print(
        "PR Security Auto-Fix complete. "
        f"Findings: {len(aggregate['findings'])}. "
        f"Patches: {len(patches_applied)}. Model: {model_used}."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
