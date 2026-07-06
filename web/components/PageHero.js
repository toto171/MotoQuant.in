'use client';

/**
 * PageHero — unified cockpit hero for inner pages (June 2026 identity pass).
 *
 * Gives every inner page the landing page's voice in one drop-in block:
 * CodeComment kicker, mono badge pill, display heading, measured subcopy,
 * and an optional row of seven-segment stats.
 *
 * Usage
 * -----
 *   <PageHero
 *     kicker="catalog loaded [541/541] · search armed"
 *     badge="Motorcycle Database"
 *     title={<>Every bike. <span className="text-gradient-orange">Real physics.</span></>}
 *     sub="541 bikes with full physics data — individual aero, dyno curves, gear cassettes."
 *     stats={[{ value: 541, label: 'BIKES' }, { value: 254, label: 'TIRES' }]}
 *   />
 *
 * Stays opacity/transform-only (Reveal) and reduced-motion-safe by
 * construction — do not add position:fixed children here.
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
    <section className={`relative pt-28 md:pt-32 pb-12 md:pb-16 px-6 ${className}`}>
      {/* ambient glow — subtle, never animated */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-x-0 top-0 h-72 bg-[radial-gradient(ellipse_at_top,rgba(255,94,31,0.07),transparent_65%)]"
      />
      <div className={`relative max-w-6xl mx-auto flex flex-col gap-4 ${alignCls}`}>
        {kicker && (
          <Reveal y={12} duration={0.5}>
            <CodeComment>{kicker}</CodeComment>
          </Reveal>
        )}
        {badge && (
          <Reveal y={14} duration={0.55} delay={0.05}>
            <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-brand-orange/40 bg-brand-orange/10 text-[10px] font-mono uppercase tracking-[0.25em] text-brand-orange">
              {badge}
            </span>
          </Reveal>
        )}
        <Reveal y={20} duration={0.65} delay={0.1}>
          <h1 className="font-display font-bold text-4xl md:text-5xl text-white tracking-tight max-w-3xl">
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
                  <ScoreboardCounter value={s.value} h={s.h ?? 22} />
                  <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-white/45">
                    {s.label}
                  </span>
                </div>
              ))}
            </div>
          </Reveal>
        )}
        {children}
      </div>
    </section>
  );
}
