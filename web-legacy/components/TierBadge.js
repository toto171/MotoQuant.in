"use client";

/**
 * MotoQuant Pro — Tier Badge Component
 * =====================================
 * A small pill/badge that displays the user's subscription tier.
 *
 * Usage
 * -----
 *   <TierBadge tier="pro" />
 *   <TierBadge tier={user.tier} size="sm" />
 */

const TIER_CONFIG = {
  free: {
    label: "Free",
    bg: "bg-gray-100",
    text: "text-gray-600",
    border: "border-gray-200",
    icon: null,
  },
  pro: {
    label: "Pro",
    bg: "bg-orange-100",
    text: "text-orange-700",
    border: "border-orange-200",
    icon: "⚡",
  },
  studio: {
    label: "Studio",
    bg: "bg-purple-100",
    text: "text-purple-700",
    border: "border-purple-200",
    icon: "🏁",
  },
};

const SIZE_CLASSES = {
  xs: "text-xs px-1.5 py-0.5",
  sm: "text-xs px-2 py-0.5",
  md: "text-sm px-2.5 py-1",
  lg: "text-base px-3 py-1.5",
};

export default function TierBadge({ tier = "free", size = "sm", className = "" }) {
  const config = TIER_CONFIG[tier] ?? TIER_CONFIG.free;
  const sizeClass = SIZE_CLASSES[size] ?? SIZE_CLASSES.sm;

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full font-medium border
                  ${config.bg} ${config.text} ${config.border} ${sizeClass} ${className}`}
    >
      {config.icon && <span aria-hidden="true">{config.icon}</span>}
      {config.label}
    </span>
  );
}

/**
 * UpgradeCTA — shown when a feature requires a higher tier.
 *
 * Usage
 * -----
 *   <UpgradeCTA requiredTier="pro" featureName="Save runs" />
 */
export function UpgradeCTA({ requiredTier = "pro", featureName = "this feature", className = "" }) {
  const config = TIER_CONFIG[requiredTier] ?? TIER_CONFIG.pro;
  const prices = { pro: "₹499/mo", studio: "₹2,999/mo" };

  return (
    <div
      className={`rounded-xl border border-dashed p-6 text-center
                  ${config.border} bg-gradient-to-br from-white to-gray-50 ${className}`}
    >
      <div className="mb-2">
        <TierBadge tier={requiredTier} size="md" />
      </div>
      <p className="mt-2 text-sm text-gray-600">
        <span className="font-semibold">{featureName}</span> is a{" "}
        <span className={`font-semibold ${config.text}`}>{config.label}</span> feature.
      </p>
      <p className="mt-1 text-xs text-gray-400">
        From {prices[requiredTier]} · Cancel anytime
      </p>
      <a
        href="/pricing"
        className="mt-4 inline-flex items-center gap-1 rounded-lg bg-orange-500 px-4 py-2
                   text-sm font-semibold text-white shadow-sm hover:bg-orange-600
                   transition-colors"
      >
        Upgrade to {config.label}
        <span aria-hidden="true">→</span>
      </a>
    </div>
  );
}
