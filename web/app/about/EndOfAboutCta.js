'use client';

// GROWTH_EXP_012 — /about end-of-page simulator CTA
//
// A (control)  = no terminal CTA — visitors who finish reading /about (story,
//                founders, roadmap, contact form) drop into the SiteFooter
//                with zero outbound action toward /simulator. /about has zero
//                <Link> usages today; the only outbound clicks are mailto:
//                anchors. This is the only credibility-heavy page on the site
//                without a next-step CTA.
// B (variant)  = a single end-of-page glass CTA card pinned BELOW the contact
//                form and ABOVE the SiteFooter. Copy ties the about-page
//                narrative ("first-principles, ±0.007 s top-10 error") to the
//                concrete next action ("run your own bike, 15 s, free").
//
// Hypothesis: visitors land on /about (often via the SiteNav after reading
// the landing-page hero, or from blog-post author bios) to vet the project's
// credibility — founders, location, methodology, roadmap. They absorb the
// pitch but the page has zero terminal CTA, so the cohort that finishes
// reading exits through the footer. Adding a single grounded CTA after the
// contact form (the natural end-of-content breakpoint, before the boilerplate
// footer) should lift simulator_runs/about_visitor without touching any
// SEO-anchored copy (h1, meta, founder bios, roadmap, contact form all
// byte-identical across arms).
//
// Single-variable test: presence of the end-of-page CTA. Copy + href fixed
// on variant B; control renders a hidden span placeholder so DOM is
// pre-experiment-equivalent. No conflict with other live experiments
// (EXP-001 landing, EXP-002+005 /pricing, EXP-003 /simulator, EXP-004
// /blog/the-physics-of-a-perfect-launch post body, EXP-006 /blog index,
// EXP-007 /login, EXP-008 /features bottom, EXP-009 /bikes catalog,
// EXP-010 /blog/pulsar-ns200-vs-apache-rtr-200... post body, EXP-011
// /bikes/[id] top CTA). /about had zero live experiments prior to this.
//
// Default = A. Flag = ?variant=B. Same canonical URL, same h1, same meta
// — SEO-safe. data-exp/data-variant on wrapper + Link for click
// attribution. Wrapped in <Suspense fallback={null}> at the call site per
// the Vercel App-Router static-prerender / CSR-bailout rule in CLAUDE.md.

import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { Zap } from 'lucide-react';

export default function EndOfAboutCta() {
  const searchParams = useSearchParams();
  const variant = searchParams?.get('variant') === 'B' ? 'B' : 'A';

  // Variant A: render a hidden marker. DOM stays additive-only on B so the
  // pre-EXP-012 contact-form-to-footer transition is byte-equivalent on
  // control.
  if (variant !== 'B') {
    return <span data-exp="EXP-012" data-variant="A" hidden />;
  }

  return (
    <section
      data-exp="EXP-012"
      data-variant="B"
      className="py-20 px-6 border-b border-white/5"
    >
      <div className="max-w-4xl mx-auto">
        <div className="card border-accent/30 p-8 md:p-10 flex flex-col md:flex-row items-start md:items-center gap-6">
          <div className="flex-1">
            <div className="label-mono mb-3">
              Next step
            </div>
            <div className="font-display font-bold tracking-tight text-white text-2xl md:text-3xl mb-3">
              You&apos;ve read the pitch. Now run the numbers.
            </div>
            <div className="text-white/65 text-sm md:text-base leading-relaxed">
              Same first-principles engine. Same ±0.007 s top-10 error. 15 seconds,
              no signup — pick your bike and see its quarter-mile ET.
            </div>
          </div>
          <Link
            href="/simulator"
            data-exp="EXP-012"
            data-variant="B"
            data-cta="about-end-of-page"
            className="btn-primary shrink-0"
          >
            <Zap size={18} /> Run a sim
          </Link>
        </div>
      </div>
    </section>
  );
}
