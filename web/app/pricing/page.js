"use client";

/**
 * MotoQuant Pro — Pricing Page
 * ==============================
 * Three-tier feature matrix: Free / Pro (₹499/mo) / Studio (₹1,999/mo).
 * Monthly / Yearly toggle (yearly = ~17% off).
 *
 * Freemium open beta (June 2026): /api/payments/config drives the CTAs.
 * While billing enforcement is off, every Pro/Studio feature is unlocked
 * for free accounts and the CTAs route to account creation. Once the
 * operator flips MOTOQUANT_BILLING_ENFORCE, the same buttons hit
 * POST /api/payments/checkout (Razorpay for India incl. UPI, Stripe for
 * international cards) and redirect to the hosted checkout.
 *
 * IGNITION v5 (July 2026): PageHero + three `.card` columns (Pro column
 * border-accent with a `.chip-volt` "Most popular" tag, Studio carries the
 * mint tier chip via TierBadge), prices big mono, feature rows with
 * signal-colored check marks, FAQ as native <details>. Beta-mode reshaping,
 * checkout flow, EXP-002 + EXP-005 hooks all unchanged.
 */

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useAuth } from "../../components/AuthProvider";
import { track } from "../../lib/telemetry";
import TierBadge from "../../components/TierBadge";
import SiteNav from "../../components/SiteNav";
import SiteFooter from "../../components/SiteFooter";
import { Reveal } from "../../components/Reveal";
import PageHero from "../../components/PageHero";
import ActionButton from "../../components/ActionButton";
import { Skeleton } from "../../components/Skeleton";
import useAsyncTask from "../../lib/useAsyncTask";

import { API_URL_DIRECT as API_BASE } from "../../lib/api";

const PRICES = {
  pro:    { monthly: 499,  yearly: 4999 },
  studio: { monthly: 1999, yearly: 19990 },
};

const FEATURES = [
  ["Simulations per day",                "10", "Unlimited", "Unlimited"],
  ["Parts in a build",                   "3",  "Unlimited", "Unlimited"],
  ["Bike catalog (541 bikes)",           "✓",  "✓",         "✓"],
  ["Tire library (254 tires)",           "✓",  "✓",         "✓"],
  ["Venue conditions (20 venues)",       "✓",  "✓",         "✓"],
  ["ROI & Sobol analysis",               "—",  "✓",         "✓"],
  ["Build optimiser (BoTorch)",          "—",  "✓",         "✓"],
  ["Smart recommendations engine",       "—",  "✓",         "✓"],
  ["PDF report export",                  "—",  "✓",         "✓"],
  ["Live parts pricing",                 "—",  "✓",         "✓"],
  ["Leaderboard saves",                  "—",  "✓",         "✓"],
  ["Dragy GPS import & overlay",         "—",  "—",         "✓"],
  ["Dyno CSV import & calibration",      "—",  "—",         "✓"],
  ["ECU log import (Woolich / PC-Link)", "—",  "—",         "✓"],
  ["A vs B comparison",                  "—",  "—",         "✓"],
  ["Priority email support",             "—",  "—",         "✓"],
];

const FAQ = [
  { q: "Is the open beta really free?", a: "Yes. While MotoQuant is in open beta, every Pro and Studio feature is unlocked for all accounts at ₹0 — unlimited sims, the build optimiser, ECU autotune, Dragy/dyno imports, all of it. When we flip to paid plans at commercial launch you'll get advance notice by email, and the Free tier stays free forever." },
  { q: "Can I switch tiers?", a: "Yes — you can upgrade or downgrade at any time from your account page. Upgrades take effect immediately; downgrades apply at the end of your current billing period." },
  { q: "What happens if I cancel?", a: "Your access continues until the end of the paid period. After that, your account moves to the Free tier automatically. No data is deleted — your build history and sim runs are retained." },
  { q: "Do I need an internet connection?", a: "Yes — MotoQuant is a hosted web app, so simulations run on our servers and need a connection. Quick sims are ~50 ms round-trip, so even patchy strip-side data is usually enough." },
  { q: "Is GST included in the price?", a: "Prices shown are exclusive of GST. 18% GST is applied at checkout where applicable, as per Indian tax regulations. Your tax invoice is issued by our payment provider (Razorpay or Stripe)." },
  { q: "What payment methods are accepted?", a: "In India: UPI, credit/debit cards, net banking, and wallets via Razorpay. International riders: credit/debit cards via Stripe. PayPal support is planned." },
  { q: "Is there a refund policy?", a: "Yes. If you are not satisfied within 7 days of your first payment, contact motoquant@gmail.com for a full refund — no questions asked." },
];

function CheckIcon() {
  return (
    <svg className="h-4 w-4 shrink-0 text-signal-go" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414L8.414 15l-4.121-4.121a1 1 0 011.414-1.414L8.414 12.172l6.879-6.879a1 1 0 011.414 0z" clipRule="evenodd" />
    </svg>
  );
}
function CrossIcon() { return <span className="font-mono text-sm text-signal-foul/40" aria-hidden="true">—</span>; }

function FaqItem({ q, a }) {
  return (
    <details className="group border-b border-white/10 last:border-0">
      <summary className="flex w-full cursor-pointer list-none items-center justify-between py-5 text-left text-sm font-medium text-white/85 hover:text-white [&::-webkit-details-marker]:hidden">
        {q}
        <span className="ml-4 font-mono text-lg leading-none text-white/40 group-open:hidden" aria-hidden="true">+</span>
        <span className="ml-4 hidden font-mono text-lg leading-none text-white/40 group-open:inline" aria-hidden="true">−</span>
      </summary>
      <p className="pb-5 text-sm leading-relaxed text-white/60">{a}</p>
    </details>
  );
}

function PricingPageInner() {
  const [cycle, setCycle] = useState("monthly");
  const { isAuthenticated, accessToken } = useAuth();

  // ── Freemium beta switch — served by the backend so flipping
  // MOTOQUANT_BILLING_ENFORCE on Render reshapes this page with no deploy.
  // Defaults to beta=true until /config answers (safe: checkout isn't
  // configured before launch anyway). While the fetch is in flight the CTA
  // labels show a skeleton instead of flashing the beta default; a failed
  // fetch settles onto the beta default (cfgLoading goes false either way).
  const [payCfg, setPayCfg] = useState(null);
  const [cfgLoading, setCfgLoading] = useState(true);
  useEffect(() => {
    let cancelled = false;
    fetch(`${API_BASE}/api/payments/config`)
      .then((r) => (r.ok ? r.json() : null))
      .then((cfg) => { if (!cancelled && cfg) setPayCfg(cfg); })
      .catch(() => {})
      .finally(() => { if (!cancelled) setCfgLoading(false); });
    return () => { cancelled = true; };
  }, []);
  const beta = payCfg ? !!payCfg.beta : true;

  // ── EXP-002: Pro-CTA copy A/B test (live 2026-05-08) ────────────────
  // Hypothesis: "Subscribe to Pro" is high-commitment language; framing
  // the same action as "Start Pro · 7-day refund" embeds the risk-reversal
  // directly on the button so the visitor's eye doesn't have to drift to
  // the smaller "7-day money-back guarantee" caption below it. SEO-safe:
  // SSR always renders Variant A (default); ?variant=B switches client-side.
  const searchParams = useSearchParams();
  const proCtaVariant = searchParams?.get("variant") === "B" ? "B" : "A";
  const proCtaCopy = (loadingText) => {
    if (loadingText) return loadingText;
    return proCtaVariant === "B" ? "Start Pro · 7-day refund" : "Subscribe to Pro";
  };

  // ── EXP-005: Pro tier tag-line copy A/B test (live 2026-05-22) ──────
  // Hypothesis: the current Pro tag line "Everything you need to go faster"
  // is generic enough to describe any racing product. Visitors who just ran
  // a free sim and clicked through to pricing already know they want more —
  // what they're evaluating is "will Pro actually tell me something I can
  // act on?" Variant B names the specific analytical outputs (ROI per part,
  // build optimizer, unlimited sims) so the tag line answers "what changes
  // when I upgrade?" rather than restating the aspirational positioning.
  // Single-variable: only the 14-word tag line under the Pro price changes.
  // EXP-002 controls the button; EXP-005 controls the descriptor — no overlap.
  // Flag: ?exp5=B  (separate param so EXP-002 and EXP-005 can be toggled
  // independently without arm contamination).
  const exp5Variant = searchParams?.get("exp5") === "B" ? "B" : "A";
  const proTagLine = exp5Variant === "B"
    ? "Unlimited sims, ROI per part, build optimizer — know what each mod does before you buy it."
    : "Everything you need to go faster.";

  async function subscribe(tier, signal) {
    // Funnel event fires on intent (the click), not checkout completion —
    // completion lands server-side via the payment webhooks.
    track("upgrade_clicked", { tier, cycle, beta });
    if (beta) {
      // Open beta: no checkout — route to account creation, everything is free.
      window.location.href = isAuthenticated ? "/simulator" : "/login?signup=1";
      return;
    }
    if (!isAuthenticated) {
      window.location.href = `/login?next=/pricing&intent=${tier}_${cycle}`;
      return;
    }
    const res = await fetch(`${API_BASE}/api/payments/checkout`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ tier, billing_cycle: cycle }),
      signal,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Checkout failed.");
    window.location.href = data.checkout_url;
    return data;
  }

  // One task per tier button so a running Pro checkout doesn't flip the
  // Studio button into its running state (and vice versa).
  const proTask = useAsyncTask((signal) => subscribe("pro", signal));
  const studioTask = useAsyncTask((signal) => subscribe("studio", signal));
  const checkoutError = proTask.error || studioTask.error;

  const yearlyDiscount = (tier) => {
    const m = PRICES[tier].monthly * 12;
    const y = PRICES[tier].yearly;
    return Math.round(((m - y) / m) * 100);
  };

  const displayPrice = (tier) => {
    if (cycle === "monthly") return `₹${PRICES[tier].monthly.toLocaleString("en-IN")}`;
    return `₹${Math.round(PRICES[tier].yearly / 12).toLocaleString("en-IN")}`;
  };

  const h2Class =
    "font-display font-bold text-3xl md:text-4xl tracking-tight text-white";

  return (
    <div className="min-h-screen bg-asphalt-0 text-white">
      <SiteNav />
      <PageHero
        align="center"
        kicker={beta ? "pricing matrix · open beta · ₹0" : "pricing matrix · plans live"}
        title={<>Simple, <span className="text-gradient-orange">honest pricing</span>.</>}
        sub="Built in Pune. Serving the Indian drag-racing community. INR pricing, GST-compliant, Razorpay + Stripe secured."
      >
        {beta && (
          <div className="mx-auto mt-2 max-w-2xl rounded-xl border border-accent/40 bg-accent/[0.08] px-5 py-4">
          <p className="text-sm font-medium text-accent">
            🏁 Open beta — every Pro &amp; Studio feature is unlocked
            free for everyone. Create an account and go racing; paid
            plans only start at commercial launch (with advance notice).
          </p>
          </div>
        )}
        <div className="mx-auto mt-4 inline-flex items-center gap-1 rounded-full border border-white/10 bg-asphalt-2 p-1">
          <button
            onClick={() => setCycle("monthly")}
            className={`rounded-full px-5 py-1.5 font-mono text-sm transition-colors ${cycle === "monthly" ? "bg-accent font-bold text-asphalt-0" : "text-white/55 hover:text-white"}`}
          >
            Monthly
          </button>
          <button
            onClick={() => setCycle("yearly")}
            className={`flex items-center gap-2 rounded-full px-5 py-1.5 font-mono text-sm transition-colors ${cycle === "yearly" ? "bg-accent font-bold text-asphalt-0" : "text-white/55 hover:text-white"}`}
          >
            Yearly
            <span className="rounded bg-signal-go px-2 py-0.5 text-[10px] font-bold text-asphalt-0 tabular-nums">Save ~17%</span>
          </button>
        </div>
      </PageHero>

      <main id="main" className="pb-20 px-4 sm:px-6">
        <div className="mx-auto max-w-6xl">
          {checkoutError && (
            <div className="card mb-8 border-signal-foul/40 bg-signal-foul/10 px-5 py-4 text-center text-sm text-signal-foul">
              {checkoutError}
            </div>
          )}

          <div className="grid gap-4 md:grid-cols-3 md:gap-6">
            <Reveal delay={0.05}>
              <div className="card flex h-full flex-col p-5 md:p-6">
                <TierBadge tier="free" size="sm" />
                <div className="mt-5">
                  <span className="font-mono font-bold text-5xl text-white tabular-nums">₹0</span>
                  <span className="ml-1.5 font-mono text-sm text-white/45">/mo</span>
                </div>
                <p className="mt-3 text-sm text-white/65">Try the simulator, explore the catalog.</p>
                <div className="mt-7 flex-1 space-y-3">
                  {FEATURES.map(([label, free]) => (
                    <div key={label} className="flex items-start gap-2.5 text-sm text-white/75">
                      {free === "✓" || free === "1" ? <CheckIcon /> : <CrossIcon />}
                      <span className={free === "—" ? "text-white/35" : ""}>
                        {free === "✓" ? label : free !== "—" ? `${label}: ${free}` : label}
                      </span>
                    </div>
                  ))}
                </div>
                <Link href="/login?signup=1" className="btn-ghost mt-8 w-full">
                  Start free
                </Link>
              </div>
            </Reveal>

            <Reveal delay={0.12}>
              <div className="card relative flex h-full flex-col border-accent/40 p-5 md:p-6">
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <span className="chip chip-volt bg-asphalt-1">Most popular</span>
                </div>
                <TierBadge tier="pro" size="sm" />
                <div className="mt-5">
                  <span className="font-mono font-bold text-5xl text-white tabular-nums">{displayPrice("pro")}</span>
                  <span className="ml-1.5 font-mono text-sm text-white/45">/mo</span>
                </div>
                {cycle === "yearly" && (
                  <p className="mt-1 font-mono text-xs text-signal-go tabular-nums">
                    ₹{PRICES.pro.yearly.toLocaleString("en-IN")}/yr · save {yearlyDiscount("pro")}%
                  </p>
                )}
                <p
                  className="mt-3 text-sm text-white/75"
                  data-exp="EXP-005"
                  data-variant={exp5Variant}
                >
                  {proTagLine}
                </p>
                <div className="mt-7 flex-1 space-y-3">
                  {FEATURES.map(([label, , pro]) => (
                    <div key={label} className="flex items-start gap-2.5 text-sm text-white/85">
                      {pro === "✓" || pro?.includes("seat") ? <CheckIcon /> : <CrossIcon />}
                      <span className={pro === "—" ? "text-white/35" : ""}>
                        {pro === "✓" ? label : pro !== "—" ? `${label}: ${pro}` : label}
                      </span>
                    </div>
                  ))}
                </div>
                {cfgLoading ? (
                  <div className="mt-8" aria-hidden="true">
                    <Skeleton className="h-11 w-full rounded-lg" />
                    <Skeleton className="mx-auto mt-3 h-3 w-44" />
                  </div>
                ) : (
                  <>
                    <div className="mt-8" data-exp="EXP-002" data-variant={proCtaVariant}>
                      <ActionButton
                        task={proTask}
                        onRun={() => proTask.run()}
                        disabled={studioTask.active}
                        stoppable={false}
                        label={beta ? "Free during beta — create account" : proCtaCopy()}
                        runningLabel="Redirecting to checkout"
                        className="w-full"
                      />
                    </div>
                    <p className="mt-3 text-center font-mono text-xs text-white/40">
                      {beta ? "₹0 until commercial launch" : "7-day money-back guarantee"}
                    </p>
                  </>
                )}
              </div>
            </Reveal>

            <Reveal delay={0.19}>
              <div className="card flex h-full flex-col p-5 md:p-6">
                <TierBadge tier="studio" size="sm" />
                <div className="mt-5">
                  <span className="font-mono font-bold text-5xl text-white tabular-nums">{displayPrice("studio")}</span>
                  <span className="ml-1.5 font-mono text-sm text-white/45">/mo</span>
                </div>
                {cycle === "yearly" && (
                  <p className="mt-1 font-mono text-xs text-signal-go tabular-nums">
                    ₹{PRICES.studio.yearly.toLocaleString("en-IN")}/yr · save {yearlyDiscount("studio")}%
                  </p>
                )}
                <p className="mt-3 text-sm text-white/65">For tuning shops and professional teams.</p>
                <div className="mt-7 flex-1 space-y-3">
                  {FEATURES.map(([label, , , studio]) => (
                    <div key={label} className="flex items-start gap-2.5 text-sm text-white/75">
                      {studio === "✓" || studio?.includes("seat") ? <CheckIcon /> : <CrossIcon />}
                      <span className={studio === "—" ? "text-white/35" : ""}>
                        {studio === "✓" ? label : studio !== "—" ? `${label}: ${studio}` : label}
                      </span>
                    </div>
                  ))}
                </div>
                {cfgLoading ? (
                  <div className="mt-8" aria-hidden="true">
                    <Skeleton className="h-11 w-full rounded-lg" />
                    <Skeleton className="mx-auto mt-3 h-3 w-44" />
                  </div>
                ) : (
                  <>
                    <ActionButton
                      task={studioTask}
                      onRun={() => studioTask.run()}
                      disabled={proTask.active}
                      stoppable={false}
                      variant="ghost"
                      label={beta ? "Free during beta — create account" : "Subscribe to Studio"}
                      runningLabel="Redirecting to checkout"
                      className="mt-8 w-full"
                    />
                    <p className="mt-3 text-center font-mono text-xs text-white/40">
                      {beta ? "₹0 until commercial launch" : "7-day money-back guarantee"}
                    </p>
                  </>
                )}
              </div>
            </Reveal>
          </div>

          <Reveal>
            <div className="mt-14 space-y-3 text-center">
              <p className="text-sm text-white/50">
                India: <span className="font-medium text-white/80">Razorpay</span> · UPI · Cards · Net Banking · Wallets
                <span className="mx-2 text-white/25">|</span>
                International: <span className="font-medium text-white/80">Stripe</span> · Cards
              </p>
              <p className="font-mono text-xs text-white/35">
                All prices in INR + 18% GST at checkout where applicable · Cancel anytime · 7-day refund guarantee
              </p>
              <div className="mt-6 flex flex-wrap justify-center gap-x-6 gap-y-2 font-mono text-[11px] text-white/45">
                <span>Aamby Valley</span>
                <span className="text-white/15">·</span>
                <span>MMRT Chennai</span>
                <span className="text-white/15">·</span>
                <span>BIC Buddh International</span>
                <span className="text-white/15">·</span>
                <span>Kari Motor Speedway</span>
              </div>
            </div>
          </Reveal>

          <Reveal>
            <div className="mt-20">
              <div className="centerline mb-16" aria-hidden="true" />
              <h2 className={h2Class}>
                Full feature <span className="text-accent">comparison</span>
              </h2>
              <p className="mb-8 mt-2 max-w-2xl text-sm text-white/65">Everything in every tier, side-by-side.</p>
              <div className="card overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-white/10 bg-white/[0.02]">
                        <th className="px-5 py-4 text-left label-mono">Feature</th>
                        <th className="px-5 py-4 text-center label-mono">Free</th>
                        <th className="px-5 py-4 text-center label-mono text-accent">Pro</th>
                        <th className="px-5 py-4 text-center label-mono text-mint">Studio</th>
                      </tr>
                    </thead>
                    <tbody>
                      {FEATURES.map(([label, free, pro, studio]) => (
                        <tr key={label} className="border-b border-white/5 last:border-0 hover:bg-white/[0.02]">
                          <td className="px-5 py-3 text-white/80">{label}</td>
                          <td className="px-5 py-3 text-center">
                            {free === "✓" ? <CheckIcon /> : free === "—" ? <CrossIcon /> : <span className="font-mono text-white/65">{free}</span>}
                          </td>
                          <td className="px-5 py-3 text-center">
                            {pro === "✓" ? <CheckIcon /> : pro === "—" ? <CrossIcon /> : <span className="font-mono text-white/85">{pro}</span>}
                          </td>
                          <td className="px-5 py-3 text-center">
                            {studio === "✓" ? <CheckIcon /> : studio === "—" ? <CrossIcon /> : <span className="font-mono text-white/70">{studio}</span>}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </Reveal>

          <Reveal>
            <div className="mx-auto mt-20 max-w-2xl">
              <div className="centerline mb-16" aria-hidden="true" />
              <h2 className={`${h2Class} text-center`}>
                Frequently asked <span className="text-accent">questions</span>
              </h2>
              <p className="mb-6 mt-2 text-center text-sm text-white/65">
                Anything else?{" "}
                <a
                  href="mailto:motoquant@gmail.com"
                  className="text-white/80 underline decoration-white/25 underline-offset-2 hover:text-white transition-colors"
                >
                  motoquant@gmail.com
                </a>
              </p>
              <div className="card px-6">
                {FAQ.map((item) => <FaqItem key={item.q} {...item} />)}
              </div>
            </div>
          </Reveal>
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}


// ──────────────────────────────────────────────────────────────────────
// Default export wraps PricingPageInner in <Suspense> so the static
// prerender of /pricing doesn't bail out on the EXP-002 useSearchParams()
// call. Mirrors the HomePage Suspense fix (66e769d).
export default function PricingPage() {
  return (
    <Suspense fallback={null}>
      <PricingPageInner />
    </Suspense>
  );
}
