'use client';

/**
 * useAsyncTask — the one way to run a user-triggered async operation.
 *
 * Standardizes what every run button on the site needs and previously
 * re-implemented ad hoc (or skipped): AbortController wiring, progress
 * state for SimProgress/ActionButton, error capture, and quiet handling
 * of user-initiated aborts.
 *
 *   const task = useAsyncTask(async (signal, onProgress, ...args) => {
 *     return simulateJob(body, onProgress, signal);   // or any fetch
 *   });
 *
 *   task.run(...args)  → Promise<result|undefined>  (undefined on abort)
 *   task.stop()        → aborts; AbortError is swallowed (no error state)
 *   task.active        → boolean
 *   task.progress      → 0..1 float | null (null = indeterminate/staged)
 *   task.stage         → string ('' when none)
 *   task.error         → string | null
 *   task.errorObj      → the raw thrown error object | null (ApiRequestError
 *                        fields — status/code/upgradeUrl/… — when the API
 *                        threw; set/cleared in lockstep with task.error)
 *   task.result        → last successful result | null
 *   task.reset()       → clears error + result
 *
 * The `onProgress` handed to your function accepts either the runJob shape
 * ({status, progress, stage}) or a bare float — both update the bar.
 */

import { useCallback, useEffect, useRef, useState } from 'react';

export default function useAsyncTask(fn) {
  const [active, setActive] = useState(false);
  const [progress, setProgress] = useState(null);
  const [stage, setStage] = useState('');
  const [error, setError] = useState(null);
  const [errorObj, setErrorObj] = useState(null);
  const [result, setResult] = useState(null);

  const abortRef = useRef(null);
  const fnRef = useRef(fn);
  fnRef.current = fn;
  const mountedRef = useRef(true);
  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      abortRef.current?.abort();
    };
  }, []);

  const stop = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  const reset = useCallback(() => {
    setError(null);
    setErrorObj(null);
    setResult(null);
    setProgress(null);
    setStage('');
  }, []);

  const run = useCallback(async (...args) => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setActive(true);
    setError(null);
    setErrorObj(null);
    setProgress(null);
    setStage('');

    const onProgress = (p) => {
      if (!mountedRef.current || controller.signal.aborted) return;
      if (typeof p === 'number') {
        setProgress(p);
      } else if (p && typeof p === 'object') {
        setProgress(typeof p.progress === 'number' ? p.progress : null);
        setStage(p.stage || '');
      }
    };

    try {
      const res = await fnRef.current(controller.signal, onProgress, ...args);
      if (mountedRef.current && !controller.signal.aborted) {
        setResult(res);
      }
      return res;
    } catch (e) {
      if (e?.name === 'AbortError') return undefined; // user pressed Stop
      if (mountedRef.current) {
        setError(e?.message || 'Something went wrong — please try again');
        setErrorObj(e ?? null);
      }
      return undefined;
    } finally {
      if (mountedRef.current && abortRef.current === controller) {
        setActive(false);
        setProgress(null);
        setStage('');
      }
    }
  }, []);

  return { run, stop, reset, active, progress, stage, error, errorObj, result };
}
