# Contributing to MotoQuant Pro web/

Quick guide to the gotchas that have bitten us repeatedly. Read this before opening a PR that touches `web/**`.

## Run `next build` before you push

Vercel reproduces the same `next build` we run locally. If the local build fails, the Vercel deploy will fail too — and a broken deploy means a broken landing page until the next push lands. Always:

```bash
cd web
npm install            # only first time, or after a package.json change
npm run build          # this is what Vercel runs
```

There is a pre-push hook at `scripts/git-hooks/pre-push` that will do this automatically when your push includes `web/**` changes. Enable it once per clone:

```bash
git config core.hooksPath scripts/git-hooks
```

In a real emergency you can bypass it with `SKIP_WEB_BUILD=1 git push`, but the GitHub Actions workflow `.github/workflows/web-verify.yml` still runs the same build on the server, so the failure surfaces there within a minute regardless.

## Static-export gotchas (App Router, Next.js 14)

### `useSearchParams()` MUST be inside a `<Suspense>` boundary

Any client component that reads URL search params via `useSearchParams()` opts every parent that renders it into client-side rendering. If the parent is statically pre-rendered (the default for everything in `app/`), `next build` errors with:

```
useSearchParams() should be wrapped in a suspense boundary at page "/..."
Read more: https://nextjs.org/docs/messages/missing-suspense-with-csr-bailout
```

Fix: wrap the component (or just the part that uses the hook) in `<Suspense>` from `react`:

```jsx
"use client";
import { Suspense } from "react";
import { useSearchParams } from "next/navigation";

function PageInner() {
  const params = useSearchParams();
  // ...
}

export default function Page() {
  return (
    <Suspense fallback={<div>Loading…</div>}>
      <PageInner />
    </Suspense>
  );
}
```

The Suspense boundary must be in a parent of the component that calls the hook, and the parent itself must not also call the hook outside the boundary.

### Don't read `window` / `navigator` / `document` at render time

These don't exist during SSR. Read them inside `useEffect` (which only runs in the browser) or behind a `typeof window !== 'undefined'` guard.

### `next/font/google` requires network access at build time

The build fetches font CSS from `fonts.googleapis.com`. If you're building offline or behind a strict firewall, the build fails. CI always has internet so this only hits local builds — work around it with `next dev` (which fetches lazily) for local iteration.

## File-write hygiene

The Cowork sandbox occasionally truncates files mid-write at ~5–6 KB. After any large edit, run `node scripts/verify-web.mjs` (also wired as `npm run verify`). It catches null bytes, mid-token truncation, and brace imbalance in <1 second. The same script runs as `prebuild`, so a truncated file fails the build before webpack even starts.

## See also

- Repository root `CLAUDE.md` — full project context, hygiene rules, and standing notes.
- `scripts/verify-web.mjs` — what the prebuild integrity check is doing.
- `next.config.js` — same-origin `/api/*` rewrite to the Railway backend.
