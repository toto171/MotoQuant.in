/**
 * Same-origin redirect guard for `?next=` style parameters.
 *
 * Returns a path (`pathname + search + hash`) that is guaranteed to stay on
 * `origin`, or `fallback`. Validation is by parsing, not by string prefixes:
 * browsers strip tabs/newlines and treat "\" as "/" inside URLs, so a string
 * that merely starts with "/" can still resolve to another host.
 */
const MAX_LEN = 2048;

export function safeNextPath(raw, origin, fallback = '/account') {
  if (typeof raw !== 'string' || !raw || raw.length > MAX_LEN) return fallback;
  // Any ASCII control character (tab, CR, LF, NUL, DEL…) or backslash: reject.
  if (/[\u0000-\u001f\u007f\\]/.test(raw)) return fallback;
  // Exactly one leading "/", not followed by another "/".
  if (!/^\/(?![/\\])/.test(raw)) return fallback;
  let u;
  try {
    u = new URL(raw, origin);
  } catch {
    return fallback;
  }
  if (u.origin !== new URL(origin).origin) return fallback;
  return u.pathname + u.search + u.hash;
}
