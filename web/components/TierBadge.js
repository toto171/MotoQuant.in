'use client';

/**
 * MotoQuant Pro — Tier Badge Component
 * =====================================
 * A small pill/badge that displays the user's subscription tier.
 * Cockpit identity: dark-surface tokens, mono tracking labels.
 * (Rebuilt June 2026 — the original used light-mode Tailwind classes
 * that rendered near-invisible on the site's black background.)
 *
 * Usage
 * -----
 *   <TierBadge tier="pro" />
 *   <TierBadge tier={user.tier} size="sm" />
 */

const TIER_CONFIG = {
  free: {
    label: 'Free',
    bg: 'bg-white/5',
    text: 'text-white/60',
    border: 'border-white/15',
  },
  pro: {
    label: 'Pro',
    bg: 'bg-brand-orange/15',
    text: 'text-brand-orange',
    border: 'border-brand-orange/40',
  },
  studio: {
    label: 'Studio',
    bg: 'bg-brand-accent/10',
    text: 'text-brand-accent',
    border: 'border-brand-accent/30',
  },
};

const SIZE_CLASSES = {
  xs: 'text-[9px] px-1.5 py-0.5',
  sm: 'text-[10px] px-2 py-0.5',
  md: 'text-[11px] px-2.5 py-1',
  lg: 'text-xs px-3 py-1.5',
};

export default function TierBadge({ tier = 'free', size = 'sm', className = '' }) {
  const config = TIER_CONFIG[tier] ?? TIER_CONFIG.free;
  const sizeClass = SIZE_CLASSES[size] ?? SIZE_CLASSES.sm;

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full font-mono uppercase tracking-[0.18em] border
                  ${config.bg} ${config.text} ${config.border} ${sizeClass} ${className}`}
    >
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
export function UpgradeCTA({
  requiredTier = 'pro',
  featureName = 'this feature',
  className = '',
}) {
  const config = TIER_CONFIG[requiredTier] ?? TIER_CONFIG.pro;
  const prices = { pro: '₹499/mo', studio: '₹1,999/mo' };

  return (
    <div
      className={`rounded-xl border border-dashed p-6 text-center
                  ${config.border} bg-ink-1/70 ${className}`}
    >
      <div className="mb-2">
        <TierBadge tier={requiredTier} size="md" />
      </div>
      <p className="mt-2 text-sm text-white/70">
        <span className="font-semibold text-white/90">{featureName}</span> is a{' '}
        <span className={`font-semibold ${config.text}`}>{config.label}</span> feature.
      </p>
      <p className="mt-1 text-xs text-white/40 font-mono">
        From {prices[requiredTier]} · Cancel anytime
      </p>
      <a href="/pricing" className="btn-primary btn-sm mt-4">
        Upgrade to {config.label}
        <span aria-hidden="true">→</span>
      </a>
    </div>
  );
}
