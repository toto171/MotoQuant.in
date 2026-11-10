import Link from 'next/link';
import { Zap } from 'lucide-react';
import SiteNav from '../../components/SiteNav';
import SiteFooter from '../../components/SiteFooter';
import PageHeader from '../../components/PageHeader';
import EcuAutotune from '../../components/EcuAutotune';

// Server component: composes the page chrome around the client-side tool.
// Metadata lives in ./layout.js.
export default function AutotunePage() {
  return (
    <div className="min-h-screen overflow-x-hidden bg-asphalt-0 text-white">
      <SiteNav />

      <PageHeader
        title="Race-day setup"
        lede="Pick your bike and where you're racing. Get the gearing, launch RPM and tyre pressure that suit today's air — with how much time each one is worth."
      />

      <main id="main" className="px-4 pb-16 sm:px-6 md:pb-24">
        <div className="mx-auto max-w-6xl">
          <EcuAutotune />

          <div className="mt-10 text-center">
            <Link href="/simulator" className="btn-ghost">
              <Zap size={16} aria-hidden="true" /> Open the simulator
            </Link>
          </div>
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}
