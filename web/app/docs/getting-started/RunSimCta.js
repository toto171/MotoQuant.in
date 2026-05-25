"use client";

/**
 * EXP-014 — /docs/getting-started bottom CTA presence test.
 *
 * Variant A (control, default): no CTA — "Next" nav cards drop directly into
 * the article footer (pre-EXP-014 behaviour). A hidden sentinel span carries
 * data-exp/data-variant so analytics can attribute control arm views.
 *
 * Variant B (?variant=B): a glass CTA card is injected above the "Next" nav
 * cards, copy "You've read the steps. Now run a sim." linking to /simulator.
 * Presence-only test — copy + href fixed so only the presence of the CTA varies.
 *
 * Implementation follows the App-Router static-prerender rule from CLAUDE.md:
 * useSearchParams() lives inside RunSimCtaInner, wrapped at the call site in a
 * <Suspense fallback={null}> so the SSR/SSG output is byte-identical to the
 * pre-EXP-014 page on both arms.
 */

import { useSearchParams } from "next/navigation";
import Link from "next/link";

function RunSimCtaInner() {
  const params = useSearchParams();
  const variant = params.get("variant") === "B" ? "B" : "A";

  if (variant === "A") {
    // Control — no visible CTA, sentinel only
    return (
      <span
        aria-hidden="true"
        hidden
        data-exp="EXP-014"
        data-variant="A"
        data-cta="getting-started-bottom"
      />
    );
  }

  // Variant B — glass CTA card above the Next nav cards
  return (
    <div
      className="mb-10 rounded-xl border border-brand-orange/30 bg-brand-orange/5 p-6"
      data-exp="EXP-014"
      data-variant="B"
      data-cta="getting-started-bottom"
    >
      <p className="font-display font-bold text-lg text-white mb-1">
        You&apos;ve read the steps. Now run a sim.
      </p>
      <p className="text-sm text-white/60 mb-4">
        Pick your bike, set your conditions, and see your quarter-mile ET — same
        engine you just read about. No account required.
      </p>
      <Link
        href="/simulator"
        className="inline-block px-5 py-2.5 rounded-lg bg-brand-orange text-black font-mono text-sm font-bold hover:bg-brand-orange/85 transition-colors"
        data-exp="EXP-014"
        data-variant="B"
        data-cta-link="getting-started-bottom"
      >
        Run a sim →
      </Link>
    </div>
  );
}

export default RunSimCtaInner;
