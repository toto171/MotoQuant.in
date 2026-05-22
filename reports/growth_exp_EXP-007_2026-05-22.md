# Growth Experiment EXP-007 — Login submit button copy

**Started:** 2026-05-22
**Status:** live (variant default OFF; control unchanged)
**Page:** `/login`
**Element:** magic-link submit button copy

---

## Hypothesis

First-time visitors arriving at `/login` (especially via the `/signup` →
`/login?signup=1` redirect, plus inbound from `/pricing` plan CTAs and blog
end-of-post cards) hesitate at the form because the submit button currently
reads **"Send sign-in link"** — copy that describes the *email-delivery
mechanism* rather than the *outcome the visitor wants* (start using the
product, free, with no password commitment).

For a returning user the mechanism wording is fine; for first-time-signup
intent it raises perceived friction at the moment of click ("Do I need an
account first? Is this a sign-in for people who already registered
somewhere else?"). The full magic-link UX (passwordless, free trial,
zero-card) is described in tiny grey-text below the heading — but the eye
goes to the bright orange button, and the button says **send link**, not
**start free**.

**Variant B** replaces the button with **"Start free · email me the
link"** — names the outcome (start free), embeds the zero-friction promise
on the click target itself, and retains the mechanism noun ("link") so the
action remains unambiguous (no bait-and-switch).

If the value-forward CTA reduces the moment-of-click hesitation,
magic-link-request submits per `/login` visitor should rise.

---

## Variants

| Arm | Button copy |
|-----|-------------|
| **A** (control, default — `/login`) | `Send sign-in link` |
| **B** (`/login?variant=B`)         | `Start free · email me the link` |

**Single variable.** Only the submit button label changes. Everything else
is byte-identical across arms: form action, magic-link API call, heading
("Sign in"), subhead ("No password needed — we'll email you a sign-in
link."), email input, terms+privacy footer, AuthProvider integration, and
the `?token=...` verification flow.

---

## Implementation

Client-side `useSearchParams()` inside `LoginPageInner` in
`web/app/login/page.js`, which is already wrapped in `<Suspense>` per the
Vercel static-prerender CSR-bailout rule. The variant resolver:

```js
const ctaVariant = params?.get("variant") === "B" ? "B" : "A";
const sendButtonLabel =
  ctaVariant === "B" ? "Start free · email me the link" : "Send sign-in link";
```

`data-exp="EXP-007"` and `data-variant={ctaVariant}` attributes go on the
submit `<button>` for analytics attribution. Default-OFF: visitors who
land at `/login` with no query param see the control byte-for-byte.

Note: the `/signup` page does a `router.replace('/login?signup=1')`, so the
natural signup-intent funnel into this page already preserves the
`signup=1` query param. We considered defaulting first-time-signup
visitors to variant B (via
`params.get('variant')==='B' || params.get('signup')==='1'`), but that
turns this from a clean A/B into a segmented default — bundling two
changes. **Held for a separate follow-up experiment** if B wins.

---

## SEO + canonical safety

- Same canonical URL (`/login`)
- Same `<h1>` ("Sign in")
- Same meta tags (no layout-level changes)
- `?variant=B` is a query string — no impact on indexed URLs
- No layout shift, no new fonts, no a11y change
- Submit button retains the same accessible name pattern (visible text)

---

## Primary metric

`magic_link_requests / login_page_visitor`

Counted at the `POST /api/auth/magic-link` request boundary (the moment a
visitor commits to the form), not at email-verification completion —
button-copy effect is on *click commitment*, not downstream email open
behaviour. Verification rate is a secondary gate (below).

---

## Secondary metrics

- `login_button_click_through_rate` — direct CTR on the submit button
- `magic_link_verification_completion_rate` — gate against vanity uplift;
  if B inflates clicks but not verifications, B is recruiting low-quality
  intent and gets rolled back
- `login_page_bounce_rate` — guards against "this button reads spammy"
- `signup_redirect_to_submit_seconds` — time-to-action for the
  `?signup=1` traffic cohort (the funnel B is most aimed at)
- `returning_user_friction_signal` — qualitative gate via support tickets
  ("the sign-in button changed and now I'm confused"); if this rises on
  any arm, investigate before declaring a winner

---

## Expected lift

**Point estimate: +12–18 % on primary metric.**

Reasoning, in order of weight:

1. Button is the highest-attention element on the page (one bright orange
   block on a mostly-black canvas). Copy on it has more leverage than copy
   anywhere else.
2. The `/signup` → `/login?signup=1` redirect funnel is currently lossy —
   we redirect signup-intent traffic into a page header that says "Sign
   in" with a button that says "Send sign-in link", which is intent
   mismatch at two surfaces. Variant B closes the mismatch on the
   higher-leverage surface (the click target). Headline mismatch persists
   but is a separate variable, held for a follow-up.
3. Comparable button-copy A/Bs in adjacent SaaS funnels (per
   [GoodUI](https://goodui.org/) cohort data) typically show +10–20 % on
   first-click commit when the copy moves from mechanism-describing to
   outcome-naming with risk-reversal language ("free", "no password", "no
   card"). Variant B does outcome-naming + the zero-friction promise.
4. Returning-user cohort (existing accounts re-signing in) is unlikely to
   be affected meaningfully — they know the flow; the button copy is a
   syntax point, not a decision point.

**Conservative downside:** flat (no effect). Worst-case downside: −5 % if
returning users misread "Start free" as "this isn't for me, I already paid"
and bounce to look for a separate sign-in link. Mitigated by retaining
the "Sign in" heading and the "email me the link" mechanism phrase on the
button itself.

---

## Decision criteria

- **Ship variant B as new control if** `magic_link_requests / visitor`
  lifts **≥15 %** with **p<0.05** over **≥200 samples per arm** AND
  `magic_link_verification_completion_rate` does not drop **>5 %**.
- **Roll back if** `login_page_bounce_rate` rises **>10 %** OR
  `returning_user_friction_signal` increases (support tickets reporting
  confusion on the new copy).
- **No decision before 200 samples per arm.**
- **If B wins**, evaluate the segmented-default follow-up (auto-B for
  `?signup=1` traffic, control for direct `/login` traffic) as a
  separate experiment — do not bundle the two changes.

---

## Kill criteria (early)

- Vercel Speed Insights or CWV regressions on `/login` (none expected —
  pure copy swap, no layout shift, no new component) → roll back immediately
- Any 5xx rate increase on `/api/auth/magic-link` correlated with `variant=B`
  traffic in server logs → roll back immediately (would indicate a
  client-side bug introduced by the variant)
- Support ticket count on "login confusion" >2× baseline within 7 days → pause

---

## Page-conflict check

Live experiments at session start (per `data/growth_experiments.json`):

| Experiment | Page |
|------------|------|
| EXP-001 | `/` (landing-hero) |
| EXP-002 | `/pricing` (Pro button) |
| EXP-003 | `/simulator` (default bike) |
| EXP-004 | `/blog/the-physics-of-a-perfect-launch` (inline CTA) |
| EXP-005 | `/pricing` (Pro tag line — uses `?exp5=B`, not `?variant=B`) |
| EXP-006 | `/blog` (end-of-grid CTA) |
| **EXP-007** | **`/login` — new, no conflict** |

`/login` has no live experiment. Clean target.

---

## Files touched

- `/tmp/mq-session-1779431430-624/repo/web/app/login/page.js`
- `/tmp/mq-session-1779431430-624/repo/data/growth_experiments.json`
- `/tmp/mq-session-1779431430-624/repo/reports/growth_exp_EXP-007_2026-05-22.md` (this file)
