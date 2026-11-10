'use client';

/**
 * Route error boundary. Catches render/runtime errors below the root layout
 * and offers a retry instead of a white screen.
 */

export default function Error({ error, reset }) {
  return (
    <div className="min-h-screen bg-asphalt-0 text-white antialiased flex items-center justify-center px-6">
      <div className="max-w-lg w-full text-center py-24">
        <h1 className="font-display font-bold text-3xl md:text-4xl tracking-tight">
          Something went wrong
        </h1>
        <p className="mt-4 text-base text-white/75 leading-relaxed">
          The page hit an unexpected error. Nothing you entered has been lost. Try again, or go
          back to the simulator.
        </p>
        {process.env.NODE_ENV !== 'production' && error?.message && (
          <p className="mt-4 rounded-xl border border-signal-foul/30 bg-signal-foul/10 px-4 py-3 text-left font-mono text-xs text-signal-foul break-words">
            {String(error.message).slice(0, 300)}
          </p>
        )}
        <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
          <button type="button" onClick={() => reset()} className="btn-primary">
            Try again
          </button>
          <a href="/simulator" className="btn-ghost">
            Open the simulator
          </a>
        </div>
      </div>
    </div>
  );
}
