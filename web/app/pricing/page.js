"use client";

/**
 * MotoQuant Pro — Pricing Page
 * ==============================
 * Three-tier feature matrix: Free / Pro (₹499/mo) / Studio (₹2,999/mo).
 * Monthly / Yearly toggle (yearly = ~17% off).
 * CTAs hit POST /api/subscriptions/checkout and redirect to Razorpay.
 */

import { Suspense, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useAuth } from "../../components/AuthProvider";
import TierBadge from "../../components/TierBadge";
import SiteNav from "../../components/SiteNav";
import SiteFooter from "../../components/SiteFooter";
import { Reveal } from "../../components/Reveal";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "https://web-production-de6eb.up.railway.app";

const PRICES = {
  pro:    { monthly: 499,  yearly: 4999 },
  studio: { monthly: 2999, yearly: 29999 },
};

const FEATURES = [
  ["Simulations per day",                "10", "Unlimited", "Unlimited"],
  ["Parts in a build",                   "3",  "Unlimited", "Unlimited"],
  ["Bike catalog (527 bikes)",           "✓",  "✓",         "✓"],
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
  { q: "Can I switch tiers?", a: "Yes — you can upgrade or downgrade at any time from your account page. Upgrades take effect immediately; downgrades apply at the end of your current billing period." },
  { q: "What happens if I cancel?", a: "Your access continues until the end of the paid period. After that, your account moves to the Free tier automatically. No data is deleted — your build history and sim runs are retained." },
  { q: "Do I need an internet connection?", a: "The web app always needs a connection. The MotoQuant desktop app (Pro/Studio) works offline for up to 7 days on a cached license validation — useful at the drag strip where signal can be patchy." },
  { q: "Is GST included in the price?", a: "Prices shown are exclusive of GST. 18% GST will be added at checkout as per Indian tax regulations. You will receive a GST invoice." },
  { q: "What payment methods are accepted?", a: "We accept UPI, credit/debit cards, net banking, and wallets via Razorpay — the same gateway trusted by thousands of Indian businesses." },
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
  const [loading, setLoading] = useState(null);
  const [error, setError] = useState("");
  const { isAuthenticated, accessToken } = useAuth();

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

  async function subscribe(tier) {
    if (!isAuthenticated) {
      window.location.href = `/login?next=/pricing&intent=${tier}_${cycle}`;
      return;
    }
    setLoading(tier);
    setError("");
    try {
      const res = await fetch(`${API_BASE}/api/subscriptions/checkout`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${accessToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ tier, billing_cycle: cycle }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Checkout failed.");
      window.location.href = data.checkout_url;
    } catch (err) {
      setError(err.message);
      setLoading(null);
    }
  }

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
      <main className="pt-32 pb-20 px-4 sm:px-6">
        <div className="mx-auto max-w-6xl">
          <Reveal>
            <div className="text-center mb-14">
              <div className="inline-block px-4 py-1.5 rounded-full border border-brand-orange/40 bg-brand-orange/10 text-[10px] sm:text-xs font-mono text-brand-orange uppercase tracking-[0.25em]">
                Pricing
              </div>
              <h1 className="mt-6 font-display font-bold text-5xl md:text-6xl tracking-[-0.03em] text-white">
                Simple, honest pricing.
              </h1>
              <p className="mt-4 text-lg text-white/65 max-w-2xl mx-auto">
                Built in Pune. Serving the Indian drag-racing community.
                INR pricing, GST-compliant, Razorpay-secured.
              </p>
              <div className="mt-8 inline-flex items-center gap-1 rounded-full bg-ink-1 border border-white/10 p-1">
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
            </div>
          </Reveal>

          {error && (
            <div className="mb-8 rounded-xl bg-red-900/25 border border-red-500/40 px-5 py-4 text-sm text-red-200 text-center">
              {error}
            </div>
          )}

          <div className="grid gap-5 md:grid-cols-3">
            <Reveal delay={0.05}>
              <div className="rounded-2xl bg-ink-1/60 border border-white/10 p-8 flex flex-col h-full">
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
                <Link href="/login" className="mt-8 block w-full rounded-md border border-white/15 py-3 text-center text-sm font-display font-bold text-white/85 hover:border-white/40 hover:text-white transition-colors">
                  Start free
                </Link>
              </div>
            </Reveal>

            <Reveal delay={0.12}>
              <div className="rounded-2xl bg-gradient-to-b from-brand-orange/10 to-ink-1/40 border border-brand-orange/55 p-8 flex flex-col relative h-full shadow-orange-soft">
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <span className="rounded-full bg-brand-orange px-4 py-1 text-[10px] font-mono uppercase tracking-widest font-bold text-black shadow-lg">
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
                <p className="mt-3 text-sm text-white/75">Everything you need to go faster.</p>
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
                <button
                  onClick={() => subscribe("pro")}
                  disabled={!!loading}
                  data-exp="EXP-002"
                  data-variant={proCtaVariant}
                  className="mt-8 w-full rounded-md bg-brand-orange py-3 text-sm font-display font-bold text-black shadow-orange-soft hover:bg-brand-orangeLight disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {loading === "pro" ? "Redirecting…" : proCtaCopy()}
                </button>
                <p className="mt-3 text-center text-xs text-white/40 font-mono">7-day money-back guarantee</p>
              </div>
            </Reveal>

            <Reveal delay={0.19}>
              <div className="rounded-2xl bg-ink-1/60 border border-brand-accent/30 p-8 flex flex-col h-full">
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
                <button
                  onClick={() => subscribe("studio")}
                  disabled={!!loading}
                  className="mt-8 w-full rounded-md bg-brand-accent py-3 text-sm font-display font-bold text-black hover:bg-emerald-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {loading === "studio" ? "Redirecting…" : "Subscribe to Studio"}
                </button>
                <p className="mt-3 text-center text-xs text-white/40 font-mono">7-day money-back guarantee</p>
              </div>
            </Reveal>
          </div>

          <Reveal>
            <div className="mt-14 text-center space-y-3">
              <p className="text-sm text-white/50">
                Payments secured by <span className="text-white/80 font-medium">Razorpay</span> · UPI · Cards · Net Banking · Wallets
              </p>
              <p className="text-xs text-white/35 font-mono">
                All prices in INR + 18% GST at checkout · Cancel anytime · 7-day refund guarantee
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
            <div className="mt-20">
              <h2 className="font-display font-bold text-2xl md:text-3xl text-white mb-2">Full feature comparison</h2>
              <p className="text-sm text-white/55 mb-8 max-w-2xl">Everything in every tier, side-by-side.</p>
              <div className="rounded-xl border border-white/10 overflow-hidden bg-ink-1/40">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-white/10 bg-white/[0.02]">
                        <th className="py-4 px-5 text-left text-[10px] font-mono uppercase tracking-widest text-white/45">Feature</th>
                        <th className="py-4 px-5 text-center text-[10px] font-mono uppercase tracking-widest text-white/45">Free</th>
                        <th className="py-4 px-5 text-center text-[10px] font-mono uppercase tracking-widest text-brand-orange">Pro</th>
                        <th className="py-4 px-5 text-center text-[10px] font-mono uppercase tracking-widest text-brand-accent">Studio</th>
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
            <div className="mt-20 max-w-2xl mx-auto">
              <h2 className="font-display font-bold text-2xl md:text-3xl text-white mb-2 text-center">
                Frequently asked questions
              </h2>
              <p className="text-sm text-white/55 text-center mb-6">
                Anything else? <a href="mailto:motoquant@gmail.com" className="text-brand-accent hover:text-white transition-colors">motoquant@gmail.com</a>
              </p>
              <div className="rounded-xl border border-white/10 bg-ink-1/40 px-6">
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
