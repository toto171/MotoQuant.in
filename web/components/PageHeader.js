/**
 * PageHeader — compact header for tool pages (CLARITY v6).
 *
 *   <PageHeader
 *     eyebrow="Upgrades"                        // optional, the one uppercase label
 *     title="Best parts for your budget"
 *     lede="Tell us your bike and how much you want to spend."
 *     right={<div className="seg-control">…</div>}   // optional right slot
 *   />
 *
 * Props: eyebrow, title (node), lede (node), right | actions (node),
 * maxWidth (default 'max-w-6xl'), className.
 *
 * Renders title + one plain sentence in server HTML — no counters, no
 * animation, no marketing hero. Sits below the fixed 64px nav (pt-24 clears
 * it with breathing room) and stays short so the tool starts in the first
 * viewport on a 390x844 phone. Server-component safe.
 */

export default function PageHeader({
  eyebrow,
  title,
  lede,
  right = null,
  actions = null,
  maxWidth = 'max-w-6xl',
  className = '',
}) {
  const slot = right ?? actions;
  return (
    <header className={`px-4 pb-5 pt-[88px] sm:px-6 md:pb-6 md:pt-24 ${className}`}>
      <div
        className={`mx-auto flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between ${maxWidth}`}
      >
        <div className="min-w-0 max-w-3xl">
          {eyebrow && <p className="eyebrow mb-2">{eyebrow}</p>}
          <h1 className="font-display text-3xl font-bold tracking-tight text-white md:text-4xl">
            {title}
          </h1>
          {lede && (
            <p className="mt-2 text-base leading-relaxed text-white/70">{lede}</p>
          )}
        </div>
        {slot && <div className="shrink-0">{slot}</div>}
      </div>
    </header>
  );
}
