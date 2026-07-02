import Link from 'next/link';
import SiteNav from '../components/SiteNav';
import SiteFooter from '../components/SiteFooter';
import CodeComment from '../components/CodeComment';

export const metadata = {
  title: '404 — Off the racing line | MotoQuant Pro',
  robots: { index: false },
};

/**
 * Branded 404 (Cockpit v3). A red-light foul, not a dead end: the page
 * routes lost visitors straight back into the product. Server component —
 * zero client JS beyond the shared chrome.
 */
export default function NotFound() {
  return (
    <div className="min-h-screen bg-black text-white antialiased flex flex-col">
      <SiteNav />
      <main className="flex-1 flex items-center justify-center px-6 pt-16">
        <div className="max-w-xl w-full text-center py-24">
          <CodeComment center>run aborted · page not staged</CodeComment>
          <div className="mt-6 flex items-center justify-center gap-3" aria-hidden="true">
            {/* foul lights — two red staging lamps */}
            <span className="h-4 w-4 rounded-full bg-brand-red shadow-lamp-red" />
            <span className="h-4 w-4 rounded-full bg-brand-red shadow-lamp-red" />
          </div>
          <h1 className="mt-6 font-display font-bold tracking-tight text-white">
            <span className="block text-7xl md:text-8xl text-gradient-orange tabular-nums">404</span>
            <span className="mt-3 block text-2xl md:text-3xl">Red light — this page fouled.</span>
          </h1>
          <p className="mt-4 text-white/60 leading-relaxed">
            The URL you staged doesn&apos;t exist on this strip. Back the bike up
            and pick a lane.
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Link href="/simulator" className="btn-primary">
              Run the simulator
            </Link>
            <Link href="/bikes" className="btn-ghost">
              Browse 501 bikes
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
