import Link from 'next/link';
import { Zap } from 'lucide-react';
import SiteNav from '../../components/SiteNav';
import SiteFooter from '../../components/SiteFooter';
import PageHeader from '../../components/PageHeader';
import BuildOptimizer from '../../components/BuildOptimizer';

// Server component: composes the page chrome around the client-side tool.
// Metadata lives in ./layout.js.
export default function OptimizePage() {
  return (
    <div className="min-h-screen overflow-x-hidden bg-asphalt-0 text-white">
      <SiteNav />

      <PageHeader
        title="Best parts for your budget"
        lede="Tell us your bike and how much you want to spend. We test every compatible part and show the combination that makes it quickest."
      />

      <main id="main" className="px-4 pb-16 sm:px-6 md:pb-24">
        <div className="mx-auto max-w-6xl">
          <BuildOptimizer />

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
