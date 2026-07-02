'use client';

/**
 * TronBackdrop — capability gate for the hero light-cycle backdrop.
 *
 * Renders the WebGL TronScene3D (three.js, code-split via a plain dynamic
 * import so three never enters the main bundle) only when the client can
 * carry it:
 *   - desktop viewport (≥1024px)
 *   - prefers-reduced-motion NOT set
 *   - WebGL actually available
 *   - Save-Data not requested
 * Everyone else — phones, tablets, reduced-motion users, software renderers,
 * SSR — gets the lightweight 2D canvas TronGrid. TronGrid also keeps
 * painting while the three chunk streams in, so the floor never blanks out;
 * the swap happens only once the module is fully loaded.
 *
 * Both engines share the same contract: `launchSignal` increments fire a
 * light-cycle burst wired to the christmas-tree launch.
 */

import { useEffect, useState } from 'react';
import TronGrid from './TronGrid';

let webglOk = null; // probe once per page lifetime

function canWebGL() {
  if (webglOk !== null) return webglOk;
  try {
    const c = document.createElement('canvas');
    webglOk = !!(c.getContext('webgl2') || c.getContext('webgl'));
  } catch {
    webglOk = false;
  }
  return webglOk;
}

export default function TronBackdrop({ launchSignal = 0, className = '' }) {
  const [Scene3D, setScene3D] = useState(null);

  useEffect(() => {
    let alive = true;
    const desktop = window.matchMedia('(min-width: 1024px)');
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
    const saveData = navigator.connection?.saveData === true;

    const gate = () => desktop.matches && !reduced.matches && !saveData && canWebGL();

    const evaluate = () => {
      if (!gate()) {
        setScene3D(null); // drop to 2D (e.g. reduced-motion toggled on live)
        return;
      }
      import('./TronScene3D')
        .then((m) => {
          // re-check — the gate may have flipped while the chunk loaded
          if (alive && gate()) setScene3D(() => m.default);
        })
        .catch(() => {}); // chunk load failure → stay on the 2D grid
    };
    evaluate();
    desktop.addEventListener('change', evaluate);
    reduced.addEventListener('change', evaluate);
    return () => {
      alive = false;
      desktop.removeEventListener('change', evaluate);
      reduced.removeEventListener('change', evaluate);
    };
  }, []);

  return Scene3D ? (
    <Scene3D launchSignal={launchSignal} className={className} />
  ) : (
    <TronGrid launchSignal={launchSignal} className={className} />
  );
}
