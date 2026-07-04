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
 */

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useAuth } from "../../components/AuthProvider";
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
  ["Bike catalog (535 bikes)",           "✓",  "✓",         "✓"],
  ["Tire library (232 tires)",           "✓",  "✓",         "✓"],
  ["Venue conditions (20 venues)",       "✓",  "✓",         "✓"],
  ["ROI & Sobol analysis",               "—",  "✓",         "✓"],
  ["Build optimiser (BoTorch)",          "—",  "✓",         "✓"],
  ["Smart recommendations engine",       "—",  "✓",         "✓"],
  ["PDF report export",                  "—",  "✓",         "✓"],
  ["Live parts pricing",                 "—",  "✓",         "✓"],
  ["Leaderboard saves",                  "—",  "✓",         "✓"],
  ["Desktop app license",                "—",  "1 seat",    "5 seats"],
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
  { q: "Do I need an internet connection?", a: "The web app always needs a connection. The MotoQuant desktop app (Pro/Studio) works offline for up to 7 days on a cached license validation — useful at the drag strip where signal can be patchy." },
  { q: "Is GST included in the price?", a: "Prices shown are exclusive of GST. 18% GST is applied at checkout where applicable, as per Indian tax regulations. Your tax invoice is issued by our payment provider (Razorpay or Stripe)." },
  { q: "What payment methods are accepted?", a: "In India: UPI, credit/debit cards, net banking, and wallets via Razorpay. International riders: credit/debit cards via Stripe. PayPal support is planned." },
  { q: "Is there a refund policy?", a: "Yes. If you are not satisfied within 7 days of your first payment, contact motoquant@gmail.com for a full refund — no questions asked." },
];

function CheckIcon() {
  return (
    <svg className="h-4 w-4 text-brand-accent shrink-0" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414L8.414 15l-4.121-4.121a1 1 0 011.414-1.414L8.414 12.172l6.879-6.879a1 1 0 011.414 0z" clipRule="evenodd" />
    </svg>
  );
}
function CrossIcon() { return <span className="text-white/25 text-sm" aria-hidden="true">—</span>; }

function FaqItem({ q, a }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border-b border-white/10">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between py-5 text-left text-sm font-medium text-white/85 hover:text-white"
        aria-expanded={open}
      >
        {q}
        <span className="ml-4 text-brand-orange font-mono text-lg leading-none">{open ? "−" : "+"}</span>
      </button>
      {open && <p className="pb-5 text-sm text-white/60 leading-relaxed">{a}</p>}
    </div>
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

  return (
    <div className="min-h-screen bg-black text-white">
      <SiteNav />
      <PageHero
        align="center"
        kicker={beta ? "pricing matrix \u00b7 open beta \u00b7 \u20b90" : "pricing matrix \u00b7 plans live"}
        badge="Pricing"
        title={<>Simple, <span className="text-gradient-orange">honest pricing</span>.</>}
        sub="Built in Pune. Serving the Indian drag-racing community. INR pricing, GST-compliant, Razorpay + Stripe secured."
      >
              {beta && (
                <div className="mt-2 mx-auto max-w-2xl rounded-xl border border-brand-accent/40 bg-brand-accent/10 px-5 py-4">
                  <p className="text-sm text-brand-accent font-medium">
                    🏁 Open beta — every Pro &amp; Studio feature is unlocked
                    free for everyone. Create an account and go racing; paid
                    plans only start at commercial launch (with advance notice).
                  </p>
                </div>
              )}
              <div className="mt-4 inline-flex items-center gap-1 rounded-full bg-ink-1 border border-white/10 p-1">
                <button
                  onClick={() => setCycle("monthly")}
                  className={`rounded-full px-5 py-1.5 text-sm font-mono transition-colors ${cycle === "monthly" ? "bg-brand-orange text-black font-bold" : "text-white/55 hover:text-white"}`}
                >
                  Monthly
                </button>
                <button
                  onClick={() => setCycle("yearly")}
                  className={`rounded-full px-5 py-1.5 text-sm font-mono transition-colors flex items-center gap-2 ${cycle === "yearly" ? "bg-brand-orange text-black font-bold" : "text-white/55 hover:text-white"}`}
                >
                  Yearly
                  <span className="rounded bg-brand-green px-2 py-0.5 text-[10px] text-black font-bold">Save ~17%</span>
                </button>
              </div>
      </PageHero>

      <main id="main" className="pb-20 px-4 sm:px-6">
        <div className="mx-auto max-w-6xl">
          {checkoutError && (
            <div className="mb-8 card border-brand-red/40 bg-brand-red/10 px-5 py-4 text-sm text-brand-red/90 text-center">
              {checkoutError}
            </div>
          )}

          <div className="grid gap-5 md:grid-cols-3">
            <Reveal delay={0.05}>
              <div className="relative card p-8 flex flex-col h-full">
                <TierBadge tier="free" size="sm" />
                <div className="mt-5">
                  <span className="font-display font-bold text-5xl text-white tabular-nums">₹0</span>
                  <span className="text-white/45 text-sm ml-1.5 font-mono">/mo</span>
                </div>
                <p className="mt-3 text-sm text-white/55">Try the simulator, explore the catalog.</p>
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
              <div className="relative card border-brand-orange/40 bg-gradient-to-b from-brand-orange/[0.07] to-white/[0.02] p-8 flex flex-col h-full">
                <div
                  aria-hidden="true"
                  className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-brand-orange/70 to-transparent"
                />
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <span className="rounded-full bg-brand-orange px-4 py-1 text-[10px] font-mono uppercase tracking-[0.25em] font-bold text-black shadow-orange-soft">
                    Most popular
                  </span>
                </div>
                <TierBadge tier="pro" size="sm" />
                <div className="mt-5">
                  <span className="font-display font-bold text-5xl text-white tabular-nums">{displayPrice("pro")}</span>
                  <span className="text-white/45 text-sm ml-1.5 font-mono">/mo</span>
                </div>
                {cycle === "yearly" && (
                  <p className="mt-1 text-xs text-brand-accent font-mono">
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
                    <Skeleton className="h-11 w-full rounded-xl" />
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
                    <p className="mt-3 text-center text-xs text-white/40 font-mono">
                      {beta ? "₹0 until commercial launch" : "7-day money-back guarantee"}
                    </p>
                  </>
                )}
              </div>
            </Reveal>

            <Reveal delay={0.19}>
              <div className="relative card border-brand-accent/30 p-8 flex flex-col h-full">
                <TierBadge tier="studio" size="sm" />
                <div className="mt-5">
                  <span className="font-display font-bold text-5xl text-white tabular-nums">{displayPrice("studio")}</span>
                  <span className="text-white/45 text-sm ml-1.5 font-mono">/mo</span>
                </div>
                {cycle === "yearly" && (
                  <p className="mt-1 text-xs text-brand-accent font-mono">
                    ₹{PRICES.studio.yearly.toLocaleString("en-IN")}/yr · save {yearlyDiscount("studio")}%
                  </p>
                )}
                <p className="mt-3 text-sm text-white/55">For tuning shops and professional teams.</p>
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
                    <Skeleton className="h-11 w-full rounded-xl" />
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
                      className="mt-8 w-full border-brand-accent/40 text-brand-accent"
                    />
                    <p className="mt-3 text-center text-xs text-white/40 font-mono">
                      {beta ? "₹0 until commercial launch" : "7-day money-back guarantee"}
                    </p>
                  </>
                )}
              </div>
            </Reveal>
          </div>

          <Reveal>
            <div className="mt-14 text-center space-y-3">
              <p className="text-sm text-white/50">
                India: <span className="text-white/80 font-medium">Razorpay</span> · UPI · Cards · Net Banking · Wallets
                <span className="text-white/25 mx-2">|</span>
                International: <span className="text-white/80 font-medium">Stripe</span> · Cards
              </p>
              <p className="text-xs text-white/35 font-mono">
                All prices in INR + 18% GST at checkout where applicable · Cancel anytime · 7-day refund guarantee
              </p>
              <div className="mt-6 flex flex-wrap justify-center gap-x-6 gap-y-2 text-[11px] font-mono text-white/45">
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
            <div className="mt-20 pt-16 border-t border-brand-orange/10">
              <h2 className="font-display font-bold text-2xl md:text-3xl text-white mb-2">Full feature comparison</h2>
              <p className="text-sm text-white/55 mb-8 max-w-2xl">Everything in every tier, side-by-side.</p>
              <div className="card overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-white/10 bg-white/[0.02]">
                        <th className="py-4 px-5 text-left label-mono">Feature</th>
                        <th className="py-4 px-5 text-center label-mono">Free</th>
                        <th className="py-4 px-5 text-center label-mono text-brand-orange">Pro</th>
                        <th className="py-4 px-5 text-center label-mono text-brand-accent">Studio</th>
                      </tr>
                    </thead>
                    <tbody>
                      {FEATURES.map(([label, free, pro, studio]) => (
                        <tr key={label} className="border-b border-white/5 last:border-0 hover:bg-white/[0.02]">
                          <td className="py-3 px-5 text-white/80">{label}</td>
                          <td className="py-3 px-5 text-center">
                            {free === "✓" ? <CheckIcon /> : free === "—" ? <CrossIcon /> : <span className="text-white/65 font-mono">{free}</span>}
                          </td>
                          <td className="py-3 px-5 text-center">
                            {pro === "✓" ? <CheckIcon /> : pro === "—" ? <CrossIcon /> : <span className="text-brand-orange font-mono">{pro}</span>}
                          </td>
                          <td className="py-3 px-5 text-center">
                            {studio === "✓" ? <CheckIcon /> : studio === "—" ? <CrossIcon /> : <span className="text-brand-accent font-mono">{studio}</span>}
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
            <div className="mt-20 pt-16 border-t border-brand-orange/10 max-w-2xl mx-auto">
              <h2 className="font-display font-bold text-2xl md:text-3xl text-white mb-2 text-center">
                Frequently asked questions
              </h2>
              <p className="text-sm text-white/55 text-center mb-6">
                Anything else? <a href="mailto:motoquant@gmail.com" className="text-brand-accent hover:text-white transition-colors">motoquant@gmail.com</a>
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
