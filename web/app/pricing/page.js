"use client";

/**
 * MotoQuant Pro — Pricing Page
 * ==============================
 * Three-tier feature matrix: Free / Pro (₹499/mo) / Studio (₹2,999/mo).
 * Monthly / Yearly toggle (yearly = ~17% off).
 * CTAs hit POST /api/subscriptions/checkout and redirect to Razorpay.
 */

import { useState } from "react";
import { useAuth } from "../../components/AuthProvider";
import TierBadge from "../../components/TierBadge";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "https://web-production-de6eb.up.railway.app";

const PRICES = {
  pro: { monthly: 499, yearly: 4999 },
  studio: { monthly: 2999, yearly: 29999 },
};

const FEATURES = [
  // [label, free, pro, studio]
  ["Simulations per day",                "10", "Unlimited", "Unlimited"],
  ["Parts in a build",                   "3",  "Unlimited", "Unlimited"],
  ["Bike catalog (270+ bikes)",          "✓",  "✓",         "✓"],
  ["Tire library (159 tires)",           "✓",  "✓",         "✓"],
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
  {
    q: "Can I switch tiers?",
    a: "Yes — you can upgrade or downgrade at any time from your account page. Upgrades take effect immediately; downgrades apply at the end of your current billing period.",
  },
  {
    q: "What happens if I cancel?",
    a: "Your access continues until the end of the paid period. After that, your account moves to the Free tier automatically. No data is deleted — your build history and sim runs are retained.",
  },
  {
    q: "Do I need an internet connection?",
    a: "The web app always needs a connection. The MotoQuant desktop app (Pro/Studio) works offline for up to 7 days on a cached license validation — useful at the drag strip where signal can be patchy.",
  },
  {
    q: "Is GST included in the price?",
    a: "Prices shown are exclusive of GST. 18% GST will be added at checkout as per Indian tax regulations. You will receive a GST invoice.",
  },
  {
    q: "What payment methods are accepted?",
    a: "We accept UPI, credit/debit cards, net banking, and wallets via Razorpay — the same gateway trusted by thousands of Indian businesses.",
  },
  {
    q: "Is there a refund policy?",
    a: "Yes. If you're not satisfied within 7 days of your first payment, contact hello@motoquant.in for a full refund — no questions asked.",
  },
];

function CheckIcon() {
  return (
    <svg className="h-4 w-4 text-green-400 shrink-0" viewBox="0 0 20 20" fill="currentColor">
      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414L8.414 15l-4.121-4.121a1 1 0 011.414-1.414L8.414 12.172l6.879-6.879a1 1 0 011.414 0z" clipRule="evenodd" />
    </svg>
  );
}

function CrossIcon() {
  return <span className="text-gray-600 text-sm">—</span>;
}

function FaqItem({ q, a }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border-b border-gray-800">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between py-4 text-left text-sm font-medium text-gray-200 hover:text-white"
      >
        {q}
        <span className="ml-4 text-gray-500">{open ? "−" : "+"}</span>
      </button>
      {open && <p className="pb-4 text-sm text-gray-400">{a}</p>}
    </div>
  );
}

export default function PricingPage() {
  const [cycle, setCycle] = useState("monthly"); // "monthly" | "yearly"
  const [loading, setLoading] = useState(null);  // tier being checked out
  const [error, setError] = useState("");
  const { isAuthenticated, accessToken } = useAuth();

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
    <main className="min-h-screen bg-gray-950 py-16 px-4">
      <div className="mx-auto max-w-5xl">

        {/* Hero */}
        <div className="text-center mb-12">
          <a href="/" className="text-2xl font-extrabold text-white">
            Moto<span className="text-orange-500">Quant</span>
          </a>
          <h1 className="mt-6 text-4xl font-extrabold text-white">
            Simple, honest pricing
          </h1>
          <p className="mt-3 text-lg text-gray-400">
            Built in Pune. Serving the Indian drag community.
          </p>

          {/* Billing toggle */}
          <div className="mt-8 inline-flex items-center gap-2 rounded-full bg-gray-900 border border-gray-700 p-1">
            <button
              onClick={() => setCycle("monthly")}
              className={`rounded-full px-5 py-1.5 text-sm font-medium transition-colors
                ${cycle === "monthly" ? "bg-orange-500 text-white" : "text-gray-400 hover:text-white"}`}
            >
              Monthly
            </button>
            <button
              onClick={() => setCycle("yearly")}
              className={`rounded-full px-5 py-1.5 text-sm font-medium transition-colors
                ${cycle === "yearly" ? "bg-orange-500 text-white" : "text-gray-400 hover:text-white"}`}
            >
              Yearly
              <span className="ml-1.5 rounded bg-green-600 px-1.5 py-0.5 text-xs text-white">
                Save ~17%
              </span>
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-8 rounded-xl bg-red-900/30 border border-red-700 px-5 py-4 text-sm text-red-300 text-center">
            {error}
          </div>
        )}

        {/* Tier cards */}
        <div className="grid gap-6 md:grid-cols-3">

          {/* FREE */}
          <div className="rounded-2xl bg-gray-900 border border-gray-800 p-8 flex flex-col">
            <TierBadge tier="free" size="sm" />
            <div className="mt-4">
              <span className="text-4xl font-extrabold text-white">₹0</span>
              <span className="text-gray-500 text-sm ml-1">/mo</span>
            </div>
            <p className="mt-2 text-sm text-gray-400">
              Try the simulator, explore the catalog.
            </p>
            <div className="mt-6 flex-1 space-y-3">
              {FEATURES.map(([label, free]) => (
                <div key={label} className="flex items-center gap-2 text-sm text-gray-300">
                  {free === "✓" || free === "1" ? <CheckIcon /> : <CrossIcon />}
                  <span>{free === "✓" ? label : free !== "—" ? `${label}: ${free}` : <span className="text-gray-600">{label}</span>}</span>
                </div>
              ))}
            </div>
            <a
              href="/login"
              className="mt-8 block w-full rounded-xl border border-gray-600 py-2.5 text-center
                         text-sm font-semibold text-gray-300 hover:border-gray-400 hover:text-white
                         transition-colors"
            >
              Start free
            </a>
          </div>

          {/* PRO — highlighted */}
          <div className="rounded-2xl bg-gradient-to-b from-orange-950/60 to-gray-900 border border-orange-500/50 p-8 flex flex-col relative">
            <div className="absolute -top-3 left-1/2 -translate-x-1/2">
              <span className="rounded-full bg-orange-500 px-4 py-0.5 text-xs font-bold text-white shadow">
                Most popular
              </span>
            </div>
            <TierBadge tier="pro" size="sm" />
            <div className="mt-4">
              <span className="text-4xl font-extrabold text-white">{displayPrice("pro")}</span>
              <span className="text-gray-400 text-sm ml-1">/mo</span>
            </div>
            {cycle === "yearly" && (
              <p className="mt-1 text-xs text-green-400">
                ₹{PRICES.pro.yearly.toLocaleString("en-IN")}/yr · save {yearlyDiscount("pro")}%
              </p>
            )}
            <p className="mt-2 text-sm text-gray-300">
              Everything you need to go faster.
            </p>
            <div className="mt-6 flex-1 space-y-3">
              {FEATURES.map(([label, , pro]) => (
                <div key={label} className="flex items-center gap-2 text-sm text-gray-200">
                  {pro === "✓" || pro?.includes("seat") ? <CheckIcon /> : <CrossIcon />}
                  <span>{pro === "✓" ? label : pro !== "—" ? `${label}: ${pro}` : <span className="text-gray-600">{label}</span>}</span>
                </div>
              ))}
            </div>
            <button
              onClick={() => subscribe("pro")}
              disabled={!!loading}
              className="mt-8 w-full rounded-xl bg-orange-500 py-2.5 text-sm font-bold
                         text-white shadow-lg hover:bg-orange-600 disabled:opacity-60
                         disabled:cursor-not-allowed transition-colors"
            >
              {loading === "pro" ? "Redirecting…" : "Subscribe to Pro"}
            </button>
            <p className="mt-2 text-center text-xs text-gray-500">7-day money-back guarantee</p>
          </div>

          {/* STUDIO */}
          <div className="rounded-2xl bg-gray-900 border border-gray-800 p-8 flex flex-col">
            <TierBadge tier="studio" size="sm" />
            <div className="mt-4">
              <span className="text-4xl font-extrabold text-white">{displayPrice("studio")}</span>
              <span className="text-gray-500 text-sm ml-1">/mo</span>
            </div>
            {cycle === "yearly" && (
              <p className="mt-1 text-xs text-green-400">
                ₹{PRICES.studio.yearly.toLocaleString("en-IN")}/yr · save {yearlyDiscount("studio")}%
              </p>
            )}
            <p className="mt-2 text-sm text-gray-400">
              For tuning shops and professional teams.
            </p>
            <div className="mt-6 flex-1 space-y-3">
              {FEATURES.map(([label, , , studio]) => (
                <div key={label} className="flex items-center gap-2 text-sm text-gray-300">
                  {studio === "✓" || studio?.includes("seat") ? <CheckIcon /> : <CrossIcon />}
                  <span>{studio === "✓" ? label : studio !== "—" ? `${label}: ${studio}` : <span className="text-gray-600">{label}</span>}</span>
                </div>
              ))}
            </div>
            <button
              onClick={() => subscribe("studio")}
              disabled={!!loading}
              className="mt-8 w-full rounded-xl bg-purple-600 py-2.5 text-sm font-bold
                         text-white shadow hover:bg-purple-700 disabled:opacity-60
                         disabled:cursor-not-allowed transition-colors"
            >
              {loading === "studio" ? "Redirecting…" : "Subscribe to Studio"}
            </button>
            <p className="mt-2 text-center text-xs text-gray-500">7-day money-back guarantee</p>
          </div>
        </div>

        {/* Trust bar */}
        <div className="mt-12 text-center space-y-2">
          <p className="text-sm text-gray-500">
            Payments secured by{" "}
            <span className="text-gray-300 font-medium">Razorpay</span> · UPI · Cards · Net Banking · Wallets
          </p>
          <p className="text-xs text-gray-600">
            All prices in INR + 18% GST at checkout · Cancel anytime · 7-day refund guarantee
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-6 text-xs text-gray-600">
            <span>🏁 Aamby Valley drag community</span>
            <span>🏁 MMRT Chennai</span>
            <span>🏁 BIC Buddh International</span>
            <span>🏁 Kari Motor Speedway</span>
            {/* Partner garage logos — placeholder until onboarded */}
          </div>
        </div>

        {/* Feature matrix (full breakdown) */}
        <div className="mt-16 overflow-x-auto">
          <h2 className="text-xl font-bold text-white mb-6">Full feature comparison</h2>
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="border-b border-gray-800">
                <th className="py-3 text-left text-gray-400 font-medium">Feature</th>
                <th className="py-3 text-center text-gray-400 font-medium">Free</th>
                <th className="py-3 text-center text-orange-400 font-semibold">Pro</th>
                <th className="py-3 text-center text-purple-400 font-semibold">Studio</th>
              </tr>
            </thead>
            <tbody>
              {FEATURES.map(([label, free, pro, studio]) => (
                <tr key={label} className="border-b border-gray-800/60 hover:bg-gray-900/40">
                  <td className="py-3 text-gray-300">{label}</td>
                  <td className="py-3 text-center">
                    {free === "✓" ? <CheckIcon /> : free === "—" ? <CrossIcon /> :
                      <span className="text-gray-400">{free}</span>}
                  </td>
                  <td className="py-3 text-center">
                    {pro === "✓" ? <CheckIcon /> : pro === "—" ? <CrossIcon /> :
                      <span className="text-orange-300">{pro}</span>}
                  </td>
                  <td className="py-3 text-center">
                    {studio === "✓" ? <CheckIcon /> : studio === "—" ? <CrossIcon /> :
                      <span className="text-purple-300">{studio}</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* FAQ */}
        <div className="mt-16 max-w-2xl mx-auto">
          <h2 className="text-xl font-bold text-white mb-2">Frequently asked questions</h2>
          <div className="mt-4">
            {FAQ.map((item) => (
              <FaqItem key={item.q} {...item} />
            ))}
          </div>
        </div>

        {/* Footer nav */}
        <div className="mt-16 flex flex-wrap justify-center gap-6 text-xs text-gray-600">
          <a href="/" className="hover:text-gray-400">← Back to home</a>
          <a href="/terms" className="hover:text-gray-400">Terms</a>
          <a href="/privacy" className="hover:text-gray-400">Privacy</a>
          <a href="mailto:hello@motoquant.in" className="hover:text-gray-400">Contact</a>
        </div>
      </div>
    </main>
  );
}
