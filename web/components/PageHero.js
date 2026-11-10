/**
 * PageHero — slim header for CONTENT pages (CLARITY v6). Tool routes use
 * PageHeader instead.
 *
 *   <PageHero
 *     kicker="Motorcycle database"          // small eyebrow (optional)
 *     badge="534 bikes"                     // small pill (optional)
 *     title={<>Every bike. <span className="text-accent">Real physics.</span></>}
 *     sub="One plain sentence."
 *     stats={[{ value: 541, label: 'Bikes' }]}   // optional, static (no count-up)
 *     align="left" | "center"
 *   />
 *
 * Same props as v5 so existing callers keep working. Everything is rendered
 * in server HTML — no counters, no animation, no decorative dots/rulers.
 */

import { ScoreboardCounter } from './ScoreboardDigits';

export default function PageHero({
  kicker,
  badge,
  title,
  sub,
  stats = null,
  align = 'left',
  children = null,
  className = '',
}) {
  const center = align === 'center';
  const alignCls = center ? 'text-center items-center' : 'text-left items-start';

  return (
    <section className={`relative px-4 pb-8 pt-24 sm:px-6 md:pb-10 md:pt-28 ${className}`}>
      <div className={`mx-auto flex max-w-6xl flex-col gap-3 ${alignCls}`}>
        {kicker && <p className="eyebrow">{kicker}</p>}
        {badge && <span className="chip chip-volt">{badge}</span>}
        <h1 className="max-w-3xl font-display text-3xl font-bold tracking-tight text-white md:text-5xl">
          {title}
        </h1>
        {sub && <p className="max-w-2xl text-base leading-relaxed text-white/70 md:text-lg">{sub}</p>}
        {stats && stats.length > 0 && (
          <div className={`mt-2 flex flex-wrap gap-x-10 gap-y-4 ${center ? 'justify-center' : ''}`}>
            {stats.map((s) => (
              <div key={s.label} className="flex flex-col gap-1">
                <ScoreboardCounter value={s.value} h={s.h ?? 24} />
                <span className="text-sm text-white/60">{s.label}</span>
              </div>
            ))}
          </div>
        )}
        {children}
      </div>
    </section>
  );
}
