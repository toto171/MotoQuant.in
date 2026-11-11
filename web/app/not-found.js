import Link from 'next/link';
import SiteNav from '../components/SiteNav';
import SiteFooter from '../components/SiteFooter';

export const metadata = {
  title: 'Page not found',
  robots: { index: false },
};

export default function NotFound() {
  return (
    <div className="min-h-screen bg-asphalt-0 text-white antialiased flex flex-col">
      <SiteNav />
      <main id="main" className="flex-1 flex items-center justify-center px-6 pt-16">
        <div className="max-w-xl w-full text-center py-24">
          <p className="font-display font-bold text-7xl md:text-8xl tabular-nums text-accent">404</p>
          <h1 className="mt-4 font-display text-2xl md:text-3xl font-bold tracking-tight text-white">
            We can&apos;t find that page
          </h1>
          <p className="mt-4 text-base text-white/75 leading-relaxed">
            The link may be old or mistyped. You can start from the simulator or pick a bike.
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Link href="/simulator" className="btn-primary">
              Open the simulator
            </Link>
            <Link href="/bikes" className="btn-ghost">
              Browse 534 bikes
            </Link>
            <Link href="/" className="btn-ghost">
              Home
            </Link>
          </div>
          <p className="mt-10 text-sm text-white/60">
            Tip: press Ctrl+K (or ⌘K) anywhere to search pages and bikes.
          </p>
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
