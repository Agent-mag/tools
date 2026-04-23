"""
False-positive filter for findings.

Stage 1: regex rules — strip findings that match known-noise patterns.
Stage 2: (optional) re-score via LLM — lowers false-positive rate further.
         Currently implemented via the review model's own system prompt
         instructions about known FPs; no second call needed.
"""

import re
from typing import Any


# Patterns to strip. If a finding's (rule + issue) contains any of these
# regex patterns, drop it.
FP_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"phosphor.?icons?.*alt", re.IGNORECASE),
    re.compile(r"inline svg.*alt text", re.IGNORECASE),
    re.compile(r"decorative.*alt", re.IGNORECASE),
    re.compile(r"middleware\.ts", re.IGNORECASE),  # we use proxy.ts
    re.compile(r"use client.*metadata", re.IGNORECASE),  # layout.tsx pattern covers this
    re.compile(r"json-ld.*dangerouslySetInnerHTML", re.IGNORECASE),
    # Pages that are intentionally noindex
    re.compile(r"signin|signup|login|access-denied|bookmarks|notifications|/account|/settings|/billing", re.IGNORECASE),
    # Dev / api routes
    re.compile(r"^/dev/|^/api/", re.IGNORECASE),
]


# Paths to exclude entirely — never generate findings for these
EXCLUDE_PATH_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^node_modules/"),
    re.compile(r"^\.next/"),
    re.compile(r"^dist/"),
    re.compile(r"^\.git/"),
    re.compile(r"package-lock\.json$"),
    re.compile(r"pnpm-lock\.yaml$"),
    re.compile(r"\.lock$"),
    # src/data/ is now patchable for SEO fields (schema/meta in authors, skills, etc.)
    re.compile(r"^src/types/"),  # types, not pages
    re.compile(r"^src/components/ui/"),  # shadcn primitives
    re.compile(r"^\.github/"),  # the action itself
    re.compile(r"^public/fonts/"),
    re.compile(r"^content/articles/.*\.mdx$", re.IGNORECASE),  # allowed, but we want content-seo rules only
]


def is_excluded_path(path: str) -> bool:
    # Allow MDX to pass through for content-seo checks
    if path.startswith("content/articles/") and path.endswith(".mdx"):
        return False
    for pat in EXCLUDE_PATH_PATTERNS:
        if pat.search(path):
            return True
    return False


def matches_fp(finding: dict[str, Any]) -> bool:
    text = f"{finding.get('rule', '')} {finding.get('issue', '')} {finding.get('file', '')}"
    for pat in FP_PATTERNS:
        if pat.search(text):
            return True
    return False


def filter_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Apply regex FP filtering."""
    kept: list[dict[str, Any]] = []
    for f in findings:
        if matches_fp(f):
            continue
        file = f.get("file", "")
        if file and is_excluded_path(file):
            continue
        kept.append(f)
    return kept


def recount_summary(findings: list[dict[str, Any]]) -> dict[str, int]:
    """Regenerate summary counts from filtered findings."""
    summary = {"high": 0, "medium": 0, "low": 0}
    for f in findings:
        sev = str(f.get("severity", "")).upper()
        if sev == "HIGH":
            summary["high"] += 1
        elif sev == "MEDIUM":
            summary["medium"] += 1
        elif sev == "LOW":
            summary["low"] += 1
    return summary


def compute_verdict(summary: dict[str, int]) -> str:
    if summary["high"] >= 1:
        return "REQUEST_CHANGES"
    if summary["medium"] > 3:
        return "COMMENT"
    return "APPROVE"
