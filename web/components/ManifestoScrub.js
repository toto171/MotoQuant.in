'use client';

/**
 * ManifestoScrub — BITKRAFT-style scroll-scrubbed text reveal.
 *
 * The manifesto sits sticky in the viewport while a tall section
 * scrolls past; each word brightens from 13% → 100% opacity mapped to
 * section progress (their signature long-form pattern, via framer's
 * useScroll — no Lenis, native scrolling untouched).
 *
 * Perf: opacity-only transforms on ~55 spans, one shared scroll
 * progress MotionValue. prefers-reduced-motion renders fully lit,
 * non-sticky. Section height trimmed on mobile.
 */

import { useRef } from 'react';
import { motion, useScroll, useTransform, useReducedMotion } from 'framer-motion';
import CodeComment from './CodeComment';

const TEXT =
  "We don't guess. We integrate. Six state variables through RK4 at one " +
  'millisecond — tire temperature, clutch slip, weight transfer, air ' +
  'density. The quarter-mile is a physics problem. We treat it like one. ' +
  "Where the data is good, we land inside two tenths. Where it isn't, " +
  'we say so.';

const WORDS = TEXT.split(' ');

function Word({ children, progress, index, total }) {
  // Each word owns a slice of the scrub; slight overlap keeps the
  // sweep reading as a wave rather than a typewriter. The wave now
  // finishes at 82% of the window (was 100%+): field report said the
  // text "gets brighter late" — the closing words were still dim when
  // the reader's eye reached them.
  const start = (index / total) * 0.7;
  const end = start + 0.12;
  const opacity = useTransform(progress, [start, end], [0.13, 1]);
  return (
    <motion.span style={{ opacity }} className="inline">
      {children}{' '}
    </motion.span>
  );
}

export default function ManifestoScrub() {
  const ref = useRef(null);
  const reduced = useReducedMotion();
  const { scrollYProgress } = useScroll({
    target: ref,
    // Start brightening the moment the text is comfortably readable
    // (section top at 80% viewport) and finish while it is still centred
    // (section end at 60%) — paired with the shorter section below, this
    // also removes the dead black runway that used to sit between the
    // manifesto and the stats strip.
    offset: ['start 0.8', 'end 0.6'],
  });

  return (
    <section
      ref={ref}
      id="manifesto"
      className="relative h-[100svh] sm:h-[115vh] border-t border-brand-orange/10 bg-ink-1/30"
    >
      <div className="sticky top-0 min-h-[80svh] sm:min-h-screen flex items-center">
        <div className="max-w-4xl mx-auto px-6 py-24">
          <CodeComment className="mb-6">belief system · honest physics</CodeComment>
          {reduced ? (
            <p className="font-display font-bold text-[1.4rem] sm:text-4xl lg:text-[2.75rem] leading-snug tracking-tight text-white">
              {TEXT}
            </p>
          ) : (
            <p className="font-display font-bold text-[1.4rem] sm:text-4xl lg:text-[2.75rem] leading-snug tracking-tight text-white">
              {WORDS.map((w, i) => (
                <Word key={i} progress={scrollYProgress} index={i} total={WORDS.length}>
                  {w}
                </Word>
              ))}
            </p>
          )}
          <div className="mt-8 flex items-center gap-3 font-mono text-[10px] tracking-[0.25em] uppercase text-white/40">
            <span className="h-px w-10 bg-brand-orange/50" />
            Validation methodology in&nbsp;
            <a href="/docs/validation" className="text-brand-accent hover:text-white transition-colors pointer-events-auto">
              /docs/validation
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
