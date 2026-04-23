# Base On-Page SEO Rules

Every PR touching user-facing pages must satisfy these rules. Flag any violation with line numbers and file paths.

## Metadata completeness

1. **Every new route must have metadata.** Either:
   - `export const metadata` / `generateMetadata` in a server component `page.tsx`, OR
   - A co-located `layout.tsx` that exports `metadata` / `generateMetadata` if the page is a client component (`"use client"`).
2. **Title**: 50–60 characters ideal (<=65 absolute max). Should include the focus keyword for that page. Flag if missing or generic ("Untitled", "Page").
3. **Description**: 120–160 characters ideal (<=170 absolute max). Must be a compelling, declarative sentence — not a keyword stuff. Flag if missing or < 80 chars.
4. **Canonical URL**: Every metadata block must set `alternates.canonical` to the full absolute URL. Prevents duplicate-content penalties.
5. **OpenGraph** completeness: `type`, `title`, `description`, `url`, `siteName`, `images[]` all required.
6. **Twitter card**: `card` (summary_large_image for most pages), `title`, `description` at minimum.

## Headings and structure

7. **Exactly one H1 per page.** Flag multiple H1s or pages without an H1.
8. **Heading hierarchy must not skip levels** (no H3 directly under H1). Flag H3 without a preceding H2.
9. **First H1 should contain the focus keyword** (or a close semantic match).

## URLs and routing

10. **URLs should be lowercase, hyphen-separated, no query params for canonical pages.**
11. **No UPPERCASE or camelCase in route folder names.** `src/app/MyPage/` is a violation.
12. **Do NOT use `robots: { index: false }` on user-facing pages** unless the page is explicitly private (signin, account settings). Flag misuse.

## Images

13. **All `<Image>` / `<img>` must have `alt` text.** Decorative images can use `alt=""` explicitly but must not omit the attribute.
14. **Dimensions**: `<Image>` components must have `width` and `height` props (prevents CLS — Core Web Vital).

## Links

15. **External links should have `rel="noopener noreferrer"` when `target="_blank"`.** Security + SEO.
16. **Internal links should use Next.js `<Link>`**, not raw `<a href="/...">`. Exception: anchor links within the same page.
17. **Anchor text should be descriptive** — not "click here", "read more", "this". Google uses anchor text as a ranking signal.

## Crawlability

18. **Any new route added to `src/app/` must also appear in `src/app/sitemap.ts`.** Flag missing sitemap entries.
19. **If a new product section is added** (e.g. `/videos`, `/podcasts`), it must also be referenced in `llms.txt` under "Main Sections".
20. **Do NOT add user-facing routes to the `disallow` list in `robots.ts`** without explicit justification.

## Internal linking (ranking signal)

21. **Detail pages should include contextual internal links** via `<RelatedContent>` from `@/components/seo/related-content`. Flag detail pages missing this section.
22. **Listing pages should inject `<PageSchema>`** from `@/components/seo/page-schema` with breadcrumbs + FAQs.
23. **Articles must contain at least 2 outbound internal links** in the body (links to other articles, tools, skills, or topic hubs).
