'use client';

/**
 * Term — inline jargon with a plain-English popover (CLARITY v6).
 *
 *   <Term k="et">quarter-mile time</Term>   // custom wording
 *   <Term k="trap" />                       // renders the glossary label
 *
 * Props
 *  - k         : glossary key from lib/glossary.js (unknown key -> plain text)
 *  - children  : visible text; omitted -> the entry's `label`
 *  - className : extra classes for the trigger
 *
 * Behaviour: renders a dotted-underlined <button>. Hover, keyboard focus or a
 * tap opens a small popover with the short definition and a link to the full
 * glossary. Escape and outside click close it. The popover is portalled to
 * <body> and clamped inside the viewport (works on a 360px phone). The
 * trigger carries aria-describedby while open.
 */

import { useCallback, useEffect, useId, useLayoutEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import Link from 'next/link';
import { getTerm } from '../lib/glossary';

const MARGIN = 12;
const GAP = 8;

export default function Term({ k, children, className = '' }) {
  const entry = getTerm(k);
  const id = useId();
  const btnRef = useRef(null);
  const popRef = useRef(null);
  const closeTimer = useRef(null);
  const pinned = useRef(false); // opened by a click/tap: stays until dismissed
  const [open, setOpen] = useState(false);
  const [pos, setPos] = useState(null); // { left, top, width, above, arrowLeft }

  const clearTimer = () => {
    if (closeTimer.current) {
      clearTimeout(closeTimer.current);
      closeTimer.current = null;
    }
  };
  const show = useCallback(() => {
    clearTimer();
    setOpen(true);
  }, []);
  const hideSoon = useCallback(() => {
    clearTimer();
    if (pinned.current) return;
    closeTimer.current = setTimeout(() => setOpen(false), 120);
  }, []);
  const hideNow = useCallback(() => {
    clearTimer();
    pinned.current = false;
    setOpen(false);
  }, []);

  const place = useCallback(() => {
    const btn = btnRef.current;
    if (!btn) return;
    const r = btn.getBoundingClientRect();
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    const width = Math.min(304, vw - MARGIN * 2);
    const popH = popRef.current ? popRef.current.offsetHeight : 140;
    let left = r.left + r.width / 2 - width / 2;
    left = Math.max(MARGIN, Math.min(left, vw - width - MARGIN));
    const spaceBelow = vh - r.bottom;
    const above = spaceBelow < popH + GAP + MARGIN && r.top > spaceBelow;
    const top = above ? Math.max(MARGIN, r.top - popH - GAP) : r.bottom + GAP;
    const arrowLeft = Math.max(14, Math.min(r.left + r.width / 2 - left, width - 14));
    setPos({ left, top, width, above, arrowLeft });
  }, []);

  useLayoutEffect(() => {
    if (!open) {
      setPos(null);
      return undefined;
    }
    place();
    // second pass once the popover has real height
    const raf = requestAnimationFrame(place);
    return () => cancelAnimationFrame(raf);
  }, [open, place]);

  useEffect(() => {
    if (!open) return undefined;
    const onKey = (e) => {
      if (e.key === 'Escape') {
        hideNow();
        btnRef.current?.focus();
      }
    };
    const onDown = (e) => {
      if (btnRef.current?.contains(e.target) || popRef.current?.contains(e.target)) return;
      hideNow();
    };
    const onMove = () => place();
    document.addEventListener('keydown', onKey);
    document.addEventListener('pointerdown', onDown);
    window.addEventListener('resize', onMove);
    window.addEventListener('scroll', onMove, true);
    return () => {
      document.removeEventListener('keydown', onKey);
      document.removeEventListener('pointerdown', onDown);
      window.removeEventListener('resize', onMove);
      window.removeEventListener('scroll', onMove, true);
    };
  }, [open, hideNow, place]);

  useEffect(() => clearTimer, []);

  if (!entry) return <>{children ?? k}</>;

  const popId = `term-${id}`;
  return (
    <>
      <button
        ref={btnRef}
        type="button"
        aria-describedby={open ? popId : undefined}
        aria-expanded={open}
        onClick={() => {
          // Hover already opened it on desktop; a click pins it open, a second
          // click closes it. On touch the tap is the only trigger.
          if (pinned.current) hideNow();
          else {
            pinned.current = true;
            show();
          }
        }}
        onMouseEnter={show}
        onMouseLeave={hideSoon}
        onFocus={show}
        onBlur={(e) => {
          if (!popRef.current?.contains(e.relatedTarget)) hideSoon();
        }}
        className={[
          'inline cursor-help rounded-sm bg-transparent p-0 text-inherit',
          'font-[inherit] leading-[inherit] underline decoration-dotted decoration-1',
          'decoration-white/50 underline-offset-[5px] transition-colors',
          'hover:decoration-accent hover:text-white',
          'focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent',
          className,
        ].join(' ')}
      >
        {children ?? entry.label}
      </button>
      {open &&
        typeof document !== 'undefined' &&
        createPortal(
          <div
            ref={popRef}
            id={popId}
            role="dialog"
            aria-label={entry.label}
            onMouseEnter={show}
            onMouseLeave={hideSoon}
            style={{
              position: 'fixed',
              zIndex: 120,
              left: pos ? pos.left : 0,
              top: pos ? pos.top : 0,
              width: pos ? pos.width : 304,
              visibility: pos ? 'visible' : 'hidden',
            }}
            className="rounded-xl border border-white/15 bg-asphalt-1 p-3.5 text-left shadow-[var(--overlay-shadow)]"
          >
            <span
              aria-hidden="true"
              className="absolute h-2.5 w-2.5 rotate-45 border-white/15 bg-asphalt-1"
              style={{
                left: pos ? pos.arrowLeft - 5 : 0,
                ...(pos?.above
                  ? { bottom: -6, borderRightWidth: 1, borderBottomWidth: 1 }
                  : { top: -6, borderLeftWidth: 1, borderTopWidth: 1 }),
              }}
            />
            <p className="font-display text-sm font-semibold text-white">{entry.label}</p>
            <p className="mt-1 text-sm leading-relaxed text-white/80 normal-case tracking-normal font-normal">
              {entry.short}
            </p>
            <Link
              href={`/docs/glossary#${k}`}
              onClick={hideNow}
              className="mt-2 inline-flex min-h-[28px] items-center text-xs font-medium text-accent underline-offset-2 hover:underline"
            >
              Glossary &rarr;
            </Link>
          </div>,
          document.body
        )}
    </>
  );
}
