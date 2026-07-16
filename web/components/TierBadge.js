'use client';

/**
 * MotoQuant Pro — Tier Badge Component (IGNITION v5)
 * ==================================================
 * A small chip that displays the user's subscription tier, on the shared
 * .chip system: Free = neutral .chip, Pro = .chip-volt (legacy-named class,
 * renders the signal-orange accent tint), Studio = .chip-mint
 * (mint is reserved for tier chips — see DESIGN.md §2.1).
 *
 * Usage
 * -----
 *   <TierBadge tier="pro" />
 *   <TierBadge tier={user.tier} size="sm" />
 */

const TIER_CONFIG = {
  free: {
    label: 'Free',
    chip: 'chip',
    text: 'text-white/65',
  },
  pro: {
    label: 'Pro',
    chip: 'chip chip-volt',
    text: 'text-accent',
  },
  studio: {
    label: 'Studio',
    chip: 'chip chip-mint',
    text: 'text-mint',
  },
};

// Size overrides on top of the .chip base (h-6 px-2 text-[10px]).
const SIZE_CLASSES = {
  xs: 'h-5 px-1.5 text-[9px]',
  sm: '',
  md: 'h-7 px-2.5 text-[11px]',
  lg: 'h-8 px-3 text-xs',
};

export default function TierBadge({ tier = 'free', size = 'sm', className = '' }) {
  const config = TIER_CONFIG[tier] ?? TIER_CONFIG.free;
  const sizeClass = SIZE_CLASSES[size] ?? SIZE_CLASSES.sm;

  return (
    <span className={`${config.chip} ${sizeClass} ${className}`}>{config.label}</span>
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
    <div className={`card p-6 text-center ${className}`}>
      <div className="mb-2">
        <TierBadge tier={requiredTier} size="md" />
      </div>
      <p className="mt-2 text-sm text-white/65">
        <span className="font-semibold text-white/90">{featureName}</span> is a{' '}
        <span className={`font-semibold ${config.text}`}>{config.label}</span> feature.
      </p>
      <p className="mt-1 text-xs text-white/40 font-mono tabular-nums">
        From {prices[requiredTier]} · Cancel anytime
      </p>
      <a href="/pricing" className="btn-primary btn-sm mt-4">
        Upgrade to {config.label}
        <span aria-hidden="true">→</span>
      </a>
    </div>
  );
}
