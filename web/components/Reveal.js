'use client';

/**
 * Shared scroll-driven primitives:
 *   - <Reveal>   : opacity + y fade-in on viewport entry
 *   - <Counter>  : tabular-nums number that counts up on entry
 *   - <Stagger>  : container that staggers child Reveal animations
 *
 * Counter is NOT a ticker — it animates exactly once when the element
 * first scrolls into view. It rounds to int by default so we don't
 * see "10.271" mid-animation. The format function is stable across
 * renders so a parent re-render never restarts the animation
 * (the original bug surfaced as visibly fluctuating stat numbers).
 */

import { useRef, useEffect, useState, useCallback } from 'react';
import { motion, useInView, useReducedMotion } from 'framer-motion';

export function Reveal({
  children,
  className = '',
  delay = 0,
  y = 28,
  duration = 0.7,
  margin = '0px 0px -10% 0px',
  as = 'div',
}) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin });
  const reduced = useReducedMotion();
  const Comp = motion[as] || motion.div;
  // Reduced-motion branch (July 2026): this is the most-used animation
  // primitive on the site, so it must not translate/fade for motion-
  // sensitive users — render static, fully visible.
  if (reduced) {
    const Tag = as || 'div';
    return <Tag className={className}>{children}</Tag>;
  }
  return (
    <Comp
      ref={ref}
      initial={{ opacity: 0, y }}
      animate={inView ? { opacity: 1, y: 0 } : { opacity: 0, y }}
      transition={{ duration, ease: [0.16, 1, 0.3, 1], delay }}
      className={className}
    >
      {children}
    </Comp>
  );
}

export function Stagger({ children, className = '', stagger = 0.08 }) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: '0px 0px -10% 0px' });
  const reduced = useReducedMotion();
  if (reduced) {
    return <div className={className}>{children}</div>;
  }
  return (
    <motion.div
      ref={ref}
      initial="hidden"
      animate={inView ? 'visible' : 'hidden'}
      variants={{
        hidden:  { opacity: 1 },
        visible: { opacity: 1, transition: { staggerChildren: stagger } },
      }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

export const StaggerItem = (props) => (
  <motion.div
    variants={{
      hidden:  { opacity: 0, y: 24 },
      visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1] } },
    }}
    {...props}
  />
);

// Stable default formatter — defined OUTSIDE the component so its
// reference identity never changes across renders.
const defaultFormat = (n) => Math.round(n).toLocaleString();

export function Counter({
  value,
  duration = 1400,
  format,
  suffix = '',
  className = '',
}) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: '0px 0px -10% 0px' });
  const fmt = format || defaultFormat;
  const [display, setDisplay] = useState(() => fmt(0));
  const startedRef = useRef(false);

  // Stabilise the format function reference across re-renders so the
  // useEffect dep-list doesn't retrigger and restart the animation.
  const stableFmt = useCallback(fmt, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!inView || startedRef.current) return;
    startedRef.current = true;
    let raf;
    const t0 = performance.now();
    const step = (t) => {
      const u = Math.min(1, (t - t0) / duration);
      const eased = 1 - Math.pow(1 - u, 3);
      setDisplay(stableFmt(value * eased));
      if (u < 1) raf = requestAnimationFrame(step);
      else setDisplay(stableFmt(value));
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [inView, value, duration, stableFmt]);

  return (
    <span ref={ref} className={['tabular-nums', className].join(' ')}>
      {display}{suffix}
    </span>
  );
}
