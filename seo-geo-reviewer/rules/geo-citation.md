# Generative Engine Optimization (GEO) Rules

GEO is about getting cited by ChatGPT, Claude, Gemini, Perplexity — not just ranking on Google. These rules reflect current 2026 best practices for AI-engine citability.

## Citation-ready structure

1. **First sentence = definition.** For entity-focused pages (articles, skill pages, tool pages), the first sentence must be a declarative definition an LLM can quote verbatim. Anti-pattern: "Let's dive in!" / "In this piece we explore..." / rhetorical openings.

2. **Named entity consistency.** Use the same canonical name for entities throughout. "Agent Mag" (not "the mag", "our publication") every time. "Claude Opus 4.6" (not "Claude", "the latest Claude model") every time.

3. **Fact-per-sentence density.** Each sentence in the lede should carry a discrete, citable fact (a stat, a definition, a date, a relationship). Minimize filler transitions.

4. **Explicit publication date.** Articles should reference their publication date in-body when making "current state" claims. Example: "As of April 2026, ..." — AI engines cite articles with clearer temporal grounding more reliably.

## Structured content for AI parsing

5. **FAQs are the highest-leverage GEO artifact.** Every article with > 1000 words should have 3+ FAQs. Each Q must be a natural phrasing of something a user would ask an AI engine. Each A must be a complete, self-contained answer (2–4 sentences).

6. **TL;DR block at the top.** A one-sentence summary above the body — explicitly labeled "TL;DR" or "Summary". LLMs preferentially extract these.

7. **Schema.org NewsArticle over Article.** More structured fields, better parsed by AI engines.

8. **Author is a Person schema with expertise.** Not just a name string. The `authors.ts` registry makes this automatic — ensure every article's `author` matches a registered Author.

## Source & attribution signals

9. **Citations in article body.** At least 1 external link to a primary source (arXiv, vendor docs, official blog post). AI engines use citation graph to weight authority.

10. **Link to original sources, not aggregators.** E.g., link to OpenAI's blog, not to a TechCrunch summary of the OpenAI blog.

11. **Attribution note.** The `license` field in `articleSchema` should point to CC-BY-4.0 — explicitly permitting AI ingestion with credit.

## llms.txt and machine-readable feeds

12. **llms.txt must stay up-to-date.** Any new product surface (courses, videos, podcasts, tool categories) must appear in llms.txt "Main Sections" and "Key Products".

13. **llms-full.txt must include the full article corpus.** The implementation at `src/app/llms-full.txt/route.ts` uses `getAllArticles()` — verify this isn't broken by schema changes.

14. **ai-sitemap.xml must include per-article metadata.** Don't strip the `<ai:metadata>` fields.

15. **crawl-manifest.json must list all content types.** New content types (beyond articles/tools/skills/jobs/events/courses/resources) must be added.

## Entity-focused pages (tools, skills, models)

16. **Clear "What is X" section.** Every tool/skill/model page should explicitly answer "What is X?" in the first 50 words — not implicitly.

17. **Usage snippet.** Skills should show the install command; tools should show a usage example; models should show basic API shape. LLMs extract these to answer "how do I use X?" queries.

18. **"X vs Y" comparison content.** Where relevant, include comparisons to alternatives — AI engines often answer comparison queries and prefer citing pages that directly compare.

## Avoid GEO anti-patterns

19. **No "click to expand" content for critical info.** Accordion-hidden content is skipped by many AI crawlers.

20. **No JS-only content for citable facts.** If a fact is in a React state blob and not rendered server-side, LLMs miss it.

21. **No vague attribution.** "Some say", "many believe", "experts agree" without citation. LLMs demote these signals.

22. **No walls of affiliate links at the expense of substance.** Commercial content is fine; spam is penalized.

## Topical authority signals

23. **Tag clustering.** Every article should share tags with at least 2 existing articles — this builds topic-cluster authority, which both Google and AI engines reward.

24. **Topic hub coverage.** If an article introduces a new tag/topic, the tag should already exist in the topic hub system (`src/lib/seo/linking.ts`) and have at least 1 other piece of content on it — otherwise the topic hub page would be empty.

25. **Author expertise match.** Don't have an infrastructure writer suddenly authoring a prompt engineering piece — misalignment degrades E-E-A-T signal.
