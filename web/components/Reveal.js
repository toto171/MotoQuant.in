'use client';

/**
 * Shared scroll-driven primitives:
 *   - <Reveal>   : opacity + y fade-in on viewport entry
 *   - <Counter>  : tabular-nums number that counts up on entry
 *   - <Stagger>  : container that staggers child Reveal animations
 *
 * Built on framer-motion. All "once" by default — animations only
 * play the first time the element scrolls into view, so re-entering
 * doesn't replay them.
 */

import { useRef, useEffect, useState } from 'react';
import { motion, useInView } from 'framer-motion';

export function Reveal({
  children,
  className = '',
  delay = 0,
  y = 28,
  duration = 0.7,
  margin = '-80px',
  as = 'div',
}) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin });
  const Comp = motion[as] || motion.div;
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
  const inView = useInView(ref, { once: true, margin: '-80px' });
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

export function Counter({
  value,
  duration = 1400,
  format = (n) => n.toLocaleString(),
  suffix = '',
  className = '',
}) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: '-60px' });
  const [display, setDisplay] = useState(format(0));

  useEffect(() => {
    if (!inView) return;
    let raf;
    const t0 = performance.now();
    const step = (t) => {
      const u = Math.min(1, (t - t0) / duration);
      const eased = 1 - Math.pow(1 - u, 3);
      setDisplay(format(value * eased));
      if (u < 1) raf = requestAnimationFrame(step);
      else setDisplay(format(value));
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [inView, value, duration, format]);

  return (
    <span ref={ref} className={['tabular-nums', className].join(' ')}>
      {display}{suffix}
    </span>
  );
}
