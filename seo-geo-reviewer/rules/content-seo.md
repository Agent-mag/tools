# Content SEO Rules — Articles and Newsletters

When an MDX article (`content/articles/*.mdx`) or newsletter is added or edited, validate the following. This is where most ranking decisions are made.

## Frontmatter completeness

Every new/modified MDX article must have:

1. **`title`** — 50–60 characters, must include `focusKeyword`.
2. **`excerpt`** — 120–160 characters. This becomes the meta description; compelling + descriptive.
3. **`author`** — must match a name in `src/data/authors.ts` (so the author profile page resolves).
4. **`authorBio`** — short bio sentence (will appear in the byline).
5. **`date`** — ISO 8601 format (`YYYY-MM-DD`).
6. **`category`** — one of: Deep Dive, Engineering, Analysis, Resources, News, Research, Opinion, Reference.
7. **`tags`** — 3–6 tags. Must overlap with existing tags when relevant (to build tag-cluster authority). Use lowercase, hyphen-separated.
8. **`readTime`** — matches actual length (roughly 200 words per minute).
9. **`slug`** — URL-safe, hyphen-separated, matches filename.

## Extended SEO/GEO frontmatter — REQUIRED on all new articles

10. **`focusKeyword`** — the primary target keyword (e.g. "multi-agent systems"). Must appear in:
    - Title
    - First 100 words of body
    - At least one H2 subheading
11. **`secondaryKeywords`** — 3–5 supporting keywords. At least 2 should appear in H2/H3 subheadings.
12. **`tldr`** — ONE sentence (max 200 chars) summarizing the piece. Critical for featured snippets + AI citation.
13. **`faqs`** — MINIMUM 3 FAQs. Each `q` is a natural question; each `a` is a complete declarative answer (2–4 sentences). These become FAQPage schema.
14. **`coverImage`** + **`coverAlt`** — cover image path + descriptive alt text.
15. **`citations`** — AT LEAST 1 external credibility citation (url + title + source). Google E-E-A-T signal.

## Body quality

16. **Minimum word count**: 800 words. Flag anything below as thin content risk.
17. **Heading hierarchy**: H1 is the title (rendered by the page); body uses H2 and H3. No H1 inside the MDX body.
18. **Paragraph length**: keep paragraphs to 2–4 sentences for scannability. Flag paragraphs > 6 sentences.
19. **Internal links**: minimum 2 internal links in the body. Prefer links to `/articles/...`, `/tools/...`, `/skills/...`, or `/topics/...`.
20. **External links**: at most 10 external links; use `rel="noopener"` implicitly via markdown; flag spammy link patterns.
21. **Code blocks**: must have language tag (` ```python`, ` ```typescript`) — Google surfaces code snippets if correctly marked.

## Images in body

22. **All images must have alt text.**
23. **Images should be lazy-loaded below the fold.**
24. **Hotlinked images** (external domains not in `next.config.ts` remotePatterns) must be flagged.

## Keyword usage (don't overdo it)

25. **Focus keyword density**: 0.5–2.0% of body word count. Flag either end of the range.
26. **No keyword stuffing in alt text, headings, or link anchor text.**
27. **Don't cannibalize**: if the focus keyword matches another article's focus keyword too closely, flag potential cannibalization and suggest topic differentiation.

## GEO content signals

28. **Definitional first sentence**: the first paragraph should define the main entity with a complete declarative sentence an LLM can quote verbatim.
29. **Fact density**: concrete numbers, dates, names, benchmarks in the first 200 words — LLMs prefer factful openings.
30. **Entity disambiguation**: spell out acronyms on first use (e.g., "Model Context Protocol (MCP)").
31. **Author expertise signals**: the author's expertise should match the topic per `src/data/authors.ts`.
32. **Publication date clarity**: the body should not contradict the frontmatter `date` (e.g., referencing "last year" inconsistently).

## Newsletter-specific rules

33. **Newsletter archive issues** (if added) should live at `/newsletter/issue-<number>` with:
    - Individual metadata
    - NewsletterIssue CreativeWork schema
    - Cross-links to articles mentioned
    - Visible issue number + date + subscriber CTA
