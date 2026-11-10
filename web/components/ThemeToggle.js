'use client';

/**
 * ThemeToggle — sun/moon button, 44px, aria-pressed (CLARITY v6).
 * Pressed = light theme. Reads the theme the head script already applied,
 * writes localStorage['mq-theme'] via lib/theme.js. Renders a stable
 * (moon, not-pressed) placeholder on the server so hydration never warns;
 * the real state is read on mount.
 */

import { useEffect, useState } from 'react';
import { Moon, Sun } from 'lucide-react';
import { getTheme, setTheme } from '../lib/theme';

export default function ThemeToggle({ className = '' }) {
  const [theme, setLocal] = useState('dark');
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setLocal(getTheme());
    setReady(true);
  }, []);

  const light = ready && theme === 'light';
  return (
    <button
      type="button"
      aria-pressed={light}
      aria-label="Light theme"
      title={light ? 'Switch to dark theme' : 'Switch to light theme'}
      onClick={() => setLocal(setTheme(light ? 'dark' : 'light'))}
      className={[
        'inline-flex h-11 w-11 items-center justify-center rounded-xl border border-white/[0.12]',
        'text-white/70 transition-colors hover:border-white/30 hover:text-white',
        className,
      ].join(' ')}
    >
      {light ? <Sun size={18} aria-hidden="true" /> : <Moon size={18} aria-hidden="true" />}
    </button>
  );
}
