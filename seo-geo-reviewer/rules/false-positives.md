# Known False Positives — Do NOT flag these

These are valid patterns in our codebase. Do not raise findings against them.

## Next.js 16 patterns

1. **`proxy.ts` not `middleware.ts`** — Next.js 16 renamed middleware. `src/proxy.ts` exporting `function proxy()` is correct.
2. **`"use client"` directive paired with a sibling `layout.tsx`** — this is our standard pattern for getting metadata on client-component pages. Do NOT flag a client page for "missing metadata" if a `layout.tsx` in the same folder exports `metadata`.
3. **`dangerouslySetInnerHTML` inside `<JsonLd>` component** — this is the correct way to inject structured data. Safe because the data is our own.

## Icons and decorative SVGs

4. **Phosphor icons imported from `@phosphor-icons/react`** — these are inline SVGs, no alt text needed.
5. **Inline `<path>` elements inside `SocialLink` component** in `site-footer.tsx` — decorative brand icons, `aria-label` on parent link is sufficient.

## Intentional noindex pages

6. **`/signin`, `/signup`, `/login`, `/access-denied`, `/bookmarks`, `/notifications`, `/account`, `/settings`, `/billing`** — these SHOULD remain in `disallow` of robots.ts.
7. **`/feedback`, `/subscribe`, `/search`** — informational, intentionally indexed, but metadata may be minimal.

## External link patterns

8. **External links that already have `target="_blank" rel="noopener noreferrer"`** — do not flag as missing noopener.
9. **`target="_top"` in embed pages** (`/embed/*`) — this is intentional, breaks out of iframes when users click.

## Dev / tooling routes

10. **`/dev/*` routes** — development preview routes, not user-facing. Do not apply SEO rules to them.
11. **`/api/*` routes** — API endpoints, explicitly `disallow`ed from crawling. Do not flag for missing metadata.

## Sitemap dynamics

12. **Routes with `export const dynamic = "force-dynamic"`** — still need to be in sitemap.ts as static entries; dynamic marker only affects rendering.

## Data files and types

13. **`src/data/*.ts` files** — these are data, not pages. No SEO rules apply.
14. **`src/types/*.ts`, `src/lib/*.ts`** — library code, no SEO rules apply.

## MDX pre-existing articles

15. **Existing articles without extended frontmatter** (`tldr`, `faqs`, `citations`, `focusKeyword`) are grandfathered. Only flag NEWLY added or MODIFIED articles for missing extended frontmatter. Changes unrelated to frontmatter in an existing article don't trigger frontmatter rules.

## Performance exemptions

16. **Authentication flows** (Auth.js v5 components) may have heavier client-side JS — don't flag.
17. **Chat UI** (`src/components/chat-*`) may have heavier client-side state — don't flag.

## Build-generated

18. **`.next/`, `dist/`, `node_modules/`** — never scanned; if they appear in diffs, flag as misconfiguration but not as SEO issue.
