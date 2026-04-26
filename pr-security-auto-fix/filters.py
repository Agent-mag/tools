"""
False-positive filtering and verdict helpers for PR Security Auto-Fix.

The model should already be conservative. These regex filters are a second
guardrail so the PR comment stays useful instead of turning into generic
"security best practices" noise.
"""

from __future__ import annotations

import re
from typing import Any


MIN_REPORT_CONFIDENCE = 0.8

FP_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bdenial of service\b|\bDoS\b|resource exhaustion|rate limit", re.IGNORECASE),
    re.compile(r"missing audit logs?|lack of logging|add audit", re.IGNORECASE),
    re.compile(r"open redirect", re.IGNORECASE),
    re.compile(r"tabnabbing|xs-leaks?|clickjacking", re.IGNORECASE),
    re.compile(r"prototype pollution", re.IGNORECASE),
    re.compile(r"regex injection|regular expression denial|ReDoS", re.IGNORECASE),
    re.compile(r"outdated dependency|vulnerable dependency|CVE", re.IGNORECASE),
    re.compile(r"documentation|readme|markdown", re.IGNORECASE),
    re.compile(r"client-side authorization|client side authorization", re.IGNORECASE),
    re.compile(r"React.*XSS|Angular.*XSS", re.IGNORECASE),
    re.compile(r"environment variables?.*attacker", re.IGNORECASE),
    re.compile(r"prompt injection.*not.*tool|AI prompt.*not.*secret", re.IGNORECASE),
    re.compile(r"log spoofing|logs? untrusted input", re.IGNORECASE),
]

EXCLUDE_PATH_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^node_modules/"),
    re.compile(r"^vendor/"),
    re.compile(r"^\.next/"),
    re.compile(r"^dist/"),
    re.compile(r"^build/"),
    re.compile(r"^coverage/"),
    re.compile(r"^\.git/"),
    re.compile(r"package-lock\.json$"),
    re.compile(r"pnpm-lock\.yaml$"),
    re.compile(r"yarn\.lock$"),
    re.compile(r"\.lock$"),
    re.compile(r"\.(md|mdx|txt|rst)$", re.IGNORECASE),
    re.compile(r"(^|/)(test|tests|__tests__|fixtures?|mocks?)/", re.IGNORECASE),
    re.compile(r"(\.test|\.spec)\.(js|jsx|ts|tsx|py|go|rs)$", re.IGNORECASE),
    re.compile(r"^public/"),
    re.compile(r"^assets?/"),
    re.compile(r"\.(png|jpe?g|gif|webp|svg|ico|pdf|woff2?|ttf|otf)$", re.IGNORECASE),
]


def is_excluded_path(path: str) -> bool:
    return any(pattern.search(path) for pattern in EXCLUDE_PATH_PATTERNS)


def _confidence(finding: dict[str, Any]) -> float:
    raw = finding.get("confidence", 0)
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return 0.0
    return value / 10 if value > 1 else value


def matches_fp(finding: dict[str, Any]) -> bool:
    text = " ".join(
        str(finding.get(key, ""))
        for key in ("rule", "issue", "description", "exploit_scenario", "recommendation", "file")
    )
    return any(pattern.search(text) for pattern in FP_PATTERNS)


def filter_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Drop low-confidence and known-noise findings."""
    kept: list[dict[str, Any]] = []
    for finding in findings:
        file_path = str(finding.get("file", ""))
        if file_path and is_excluded_path(file_path):
            continue
        if _confidence(finding) < MIN_REPORT_CONFIDENCE:
            continue
        if matches_fp(finding):
            continue
        kept.append(finding)
    return kept


def recount_summary(findings: list[dict[str, Any]]) -> dict[str, int]:
    summary = {"high": 0, "medium": 0, "low": 0}
    for finding in findings:
        sev = str(finding.get("severity", "")).upper()
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
    if summary["medium"] >= 1:
        return "COMMENT"
    return "APPROVE"
