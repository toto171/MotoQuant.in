'use client';

/**
 * Route error boundary (STAGED v4). Catches render/runtime errors below
 * the root layout and offers an honest retry instead of a white screen.
 * Client component by Next.js convention (receives error + reset).
 */

import StageDots from '../components/StageDots';

export default function Error({ error, reset }) {
  return (
    <div className="min-h-screen bg-asphalt-0 text-white antialiased flex items-center justify-center px-6">
      <div className="max-w-lg w-full text-center py-24">
        <div className="flex items-center justify-center gap-3">
          <StageDots foul size={8} />
          <span className="label-mono">engine fault — run interrupted</span>
        </div>
        <h1 className="mt-6 font-display font-bold uppercase leading-[0.95] tracking-[-0.01em] text-3xl md:text-4xl">
          Something broke mid-run.
        </h1>
        <p className="mt-4 text-white/65 leading-relaxed">
          The page hit an unexpected error. Your data is fine — restart the run
          or head back to the pits.
        </p>
        {process.env.NODE_ENV !== 'production' && error?.message && (
          <p className="mt-4 rounded-xl border border-signal-foul/30 bg-signal-foul/10 px-4 py-3 text-left font-mono text-xs text-signal-foul/90 break-words">
            {String(error.message).slice(0, 300)}
          </p>
        )}
        <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
          <button type="button" onClick={() => reset()} className="btn-primary">
            Restart the run
          </button>
          <a href="/" className="btn-ghost">
            Back to the pits
          </a>
        </div>
      </div>
    </div>
  );
}
