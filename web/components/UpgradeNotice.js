'use client';

/**
 * UpgradeNotice — the one way to render a billing/auth API failure.
 *
 * Takes the raw thrown error (an ApiRequestError from lib/api — see
 * useAsyncTask's `errorObj`) and branches:
 *   402 upgrade_required / quota_exceeded → amber tile + "Upgrade to <Tier>"
 *     CTA linking to the pathname of error.upgradeUrl (fallback /pricing)
 *   401 → amber tile + "Sign in" CTA to /login?next=<current path>
 *   anything else → the standard foul error tile (+ Retry when onRetry given)
 *
 * Props: {error, onRetry} — error is required; onRetry optional.
 * Dependency-free beyond next/link + lucide (already sitewide).
 */

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { AlertCircle, Lock } from 'lucide-react';

// Only ever link within our own site: take the PATHNAME of the backend's
// absolute upgrade_url (the base arg also tolerates a relative path).
function upgradeHref(upgradeUrl) {
  if (upgradeUrl) {
    try {
      return new URL(upgradeUrl, 'https://motoquant.in').pathname || '/pricing';
    } catch {
      /* malformed URL → fall through to /pricing */
    }
  }
  return '/pricing';
}

export default function UpgradeNotice({ error, onRetry }) {
  const pathname = usePathname();
  const status = error?.status;
  const code = error?.code;
  const message = error?.message || 'Something went wrong — please try again';

  if (status === 402 && (code === 'upgrade_required' || code === 'quota_exceeded')) {
    const tier = error?.requiredTier
      ? error.requiredTier.charAt(0).toUpperCase() + error.requiredTier.slice(1)
      : 'Pro';
    return (
      <div className="card border-signal-stage/30 bg-signal-stage/10 p-4 text-sm">
        <p className="text-signal-stage flex items-start gap-2">
          <Lock size={16} className="shrink-0 mt-0.5" aria-hidden="true" />
          <span className="min-w-0">{message}</span>
        </p>
        <Link
          href={upgradeHref(error?.upgradeUrl)}
          className="btn-primary h-9 px-4 text-xs mt-3"
        >
          Upgrade to {tier}
        </Link>
      </div>
    );
  }

  if (status === 401) {
    return (
      <div className="card border-signal-stage/30 bg-signal-stage/10 p-4 text-sm">
        <p className="text-signal-stage flex items-start gap-2">
          <Lock size={16} className="shrink-0 mt-0.5" aria-hidden="true" />
          <span className="min-w-0">{message}</span>
        </p>
        <Link
          href={`/login?next=${encodeURIComponent(pathname || '/')}`}
          className="btn-ghost h-9 px-4 text-xs mt-3"
        >
          Sign in
        </Link>
      </div>
    );
  }

  return (
    <div className="card border-signal-foul/30 bg-signal-foul/10 p-3 text-signal-foul text-sm flex items-center gap-2">
      <AlertCircle size={16} className="shrink-0" aria-hidden="true" />
      <span className="min-w-0">{message}</span>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="chip h-8 px-3 ml-auto shrink-0 cursor-pointer hover:border-white/30 hover:text-white transition-colors"
        >
          Retry
        </button>
      )}
    </div>
  );
}
