# Technical SEO Rules

These rules govern JSON-LD schemas, sitemaps, crawl infrastructure, and performance signals.

## JSON-LD structured data

1. **Article detail pages** (`src/app/articles/[slug]/page.tsx`) must emit:
   - `articleSchema(...)` from `@/lib/seo/schemas` (NewsArticle type)
   - `breadcrumbSchema(...)` with Home → Articles → Category → Title
   - `faqSchema(...)` if the article has frontmatter `faqs`

2. **Job detail pages** must emit:
   - `jobPostingSchema(...)` — Google Rich Results for Jobs requires this
   - `breadcrumbSchema(...)`

3. **Event detail pages** must emit:
   - `eventSchema(...)` — eligible for Google Rich Results
   - `breadcrumbSchema(...)`

4. **Skill detail pages** must emit:
   - `softwareAppSchema({ ..., type: "skill" })`
   - `breadcrumbSchema(...)`

5. **Tool detail pages** must emit:
   - `softwareAppSchema({ ..., type: "tool" })`
   - `breadcrumbSchema(...)`

6. **Course detail pages** must emit:
   - `courseSchema(...)`
   - `breadcrumbSchema(...)`

7. **Listing pages** (`/tools`, `/skills`, `/jobs`, etc.) must inject `<PageSchema>` which emits CollectionPage + BreadcrumbList + optional FAQPage.

8. **Homepage** must emit Organization + WebSite schemas (currently in `src/app/layout.tsx`) + a CollectionPage + FAQPage via `<JsonLd>` in `src/app/page.tsx`.

## Schema accuracy

9. **Schema `@id` URLs must match the canonical URL.** No absolute/relative drift.
10. **`datePublished` and `dateModified` must be valid ISO 8601.**
11. **Author must resolve to a Person or Organization schema** — not a bare string.
12. **Citations in articleSchema should be actual CreativeWork references** with URL + name, not fake or placeholder entries.

## Sitemap and feeds

13. **Any new dynamic route must extend `src/app/sitemap.ts`** with the appropriate collection loader.
14. **New content types must be added to `/api/crawl-manifest`** contentTypes array.
15. **`/llms-full.txt`** must always include every article's full body — updated automatically via `getAllArticles()`.
16. **Do NOT cache-bust legitimate pages** by appending arbitrary query params.

## Robots.txt

17. **New AI crawler user-agents should be added to the allow list** in `src/app/robots.ts` as they emerge (e.g., new vendor bots from OpenAI/Anthropic/Google/Perplexity).
18. **Account/settings/signin routes should remain in the disallow list.**

## Performance (Core Web Vitals)

19. **No client-side data fetching for hero content.** Above-the-fold content must be SSR'd (use server components or `generateMetadata` with awaited data) — Google penalizes LCP regressions.
20. **Images larger than hero (>1200px width) should use `next/image`** with priority flag if above the fold.
21. **New third-party scripts must use `next/script` with a `strategy`** (afterInteractive, lazyOnload) — never `strategy="beforeInteractive"` on non-critical scripts.
22. **No unused CSS/JS bundles on critical routes.** Flag if a page imports a heavy library only used in one narrow branch.

## AI-specific infrastructure

23. **`/llms.txt`, `/llms-full.txt`, `/ai-sitemap.xml`, `/api/crawl-manifest`** are mandatory. Flag any PR that removes or breaks these.
24. **IndexNow key file** (`public/e5b5392aaf156bb8cf24ed78061c963c.txt`) must remain present and unchanged.
