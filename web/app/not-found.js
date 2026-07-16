import Link from 'next/link';
import SiteNav from '../components/SiteNav';
import SiteFooter from '../components/SiteFooter';
import StageDots from '../components/StageDots';

export const metadata = {
  title: '404 — Off the racing line | MotoQuant Pro',
  robots: { index: false },
};

/**
 * Branded 404 (IGNITION v5). A red-light foul, not a dead end: the page
 * routes lost visitors straight back into the product. Server component —
 * StageDots is the only client leaf beyond the shared chrome.
 */
export default function NotFound() {
  return (
    <div className="min-h-screen bg-asphalt-0 text-white antialiased flex flex-col">
      <SiteNav />
      <main className="flex-1 flex items-center justify-center px-6 pt-16">
        <div className="max-w-xl w-full text-center py-24">
          <div className="flex items-center justify-center gap-3">
            <StageDots foul size={8} />
            <span className="label-mono">red light — foul</span>
          </div>
          <h1 className="mt-6 font-display font-bold tracking-tight text-white">
            <span className="block font-mono font-bold text-7xl md:text-8xl tabular-nums">404</span>
            <span className="mt-3 block text-2xl md:text-3xl">Red light — this page fouled.</span>
          </h1>
          <p className="mt-4 text-white/65 leading-relaxed">
            The URL you staged doesn&apos;t exist on this strip. Back the bike up
            and pick a lane.
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Link href="/simulator" className="btn-primary">
              Run the simulator
            </Link>
            <Link href="/bikes" className="btn-ghost">
              Browse 541 bikes
            </Link>
            <Link href="/" className="btn-ghost">
              Home
            </Link>
          </div>
          <p className="label-mono mt-10">
            tip: press Ctrl+K anywhere to jump to any page or bike
          </p>
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
