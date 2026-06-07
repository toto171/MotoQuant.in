/**
 * Route template — gentle opacity-only entrance on every navigation.
 * Opacity only (no transform): transforms on an ancestor would re-anchor
 * position:fixed children (HudFrame, boot overlay) to the wrapper.
 * Server component; animation defined in globals.css, reduced-motion-safe.
 */
export default function Template({ children }) {
  return <div className="route-fade">{children}</div>;
}
