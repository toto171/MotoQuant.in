'use client';

/**
 * PageHero — unified inner-page hero (STAGED v4 skin, same API).
 *
 * One drop-in block giving every inner page the v4 voice: StageDots +
 * label kicker, condensed uppercase display title, quiet Inter subcopy,
 * mono stat row, centerline underneath.
 *
 * Usage (unchanged since June 2026)
 * ---------------------------------
 *   <PageHero
 *     kicker="Motorcycle database"
 *     badge="541 bikes"
 *     title={<>Every bike. <span className="text-gradient-volt">Real physics.</span></>}
 *     sub="541 bikes with full physics data — individual aero, dyno curves, gear cassettes."
 *     stats={[{ value: 541, label: 'BIKES' }, { value: 254, label: 'TIRES' }]}
 *   />
 *
 * Opacity/transform-only (Reveal) and reduced-motion-safe by construction —
 * do not add position:fixed children here.
 */

import CodeComment from './CodeComment';
import { Reveal } from './Reveal';
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
  const alignCls = align === 'center' ? 'text-center items-center' : 'text-left items-start';

  return (
    <section className={`relative pt-28 md:pt-32 pb-10 md:pb-14 px-6 ${className}`}>
      <div className={`relative max-w-6xl mx-auto flex flex-col gap-4 ${alignCls}`}>
        {kicker && (
          <Reveal y={12} duration={0.5}>
            <CodeComment center={align === 'center'}>{kicker}</CodeComment>
          </Reveal>
        )}
        {badge && (
          <Reveal y={14} duration={0.55} delay={0.05}>
            <span className="chip chip-volt">{badge}</span>
          </Reveal>
        )}
        <Reveal y={20} duration={0.65} delay={0.1}>
          <h1 className="font-display font-bold uppercase text-5xl md:text-6xl leading-[0.95] tracking-[-0.01em] text-white max-w-3xl">
            {title}
          </h1>
        </Reveal>
        {sub && (
          <Reveal y={16} duration={0.6} delay={0.16}>
            <p className="text-white/65 text-lg leading-relaxed max-w-2xl">{sub}</p>
          </Reveal>
        )}
        {stats && stats.length > 0 && (
          <Reveal y={14} duration={0.6} delay={0.22}>
            <div className="mt-2 flex flex-wrap gap-x-10 gap-y-4">
              {stats.map((s) => (
                <div key={s.label} className="flex flex-col gap-1.5">
                  <ScoreboardCounter value={s.value} h={s.h ?? 24} />
                  <span className="label-mono">{s.label}</span>
                </div>
              ))}
            </div>
          </Reveal>
        )}
        {children}
        <div className="centerline mt-6 w-full" aria-hidden="true" />
      </div>
    </section>
  );
}
