'use client';

import Link from 'next/link';
import { Zap } from 'lucide-react';
import SiteNav from '../../components/SiteNav';
import SiteFooter from '../../components/SiteFooter';
import PageHero from '../../components/PageHero';
import BuildOptimizer from '../../components/BuildOptimizer';

export default function OptimizePage() {
  return (
    <div className="min-h-screen bg-asphalt-0 text-white overflow-x-hidden">
      <SiteNav />

      <PageHero
        kicker="Build optimizer"
        title={<>The <span className="text-accent">fastest</span> build for the budget</>}
        sub="Set a bike and a ₹ budget. MotoQuant runs a physics-based knapsack across every compatible upgrade and returns the combination that drops your quarter-mile ET the most — with cost-per-tenth, synergies, and the best next part to buy."
        stats={[
          { value: 593, label: 'PARTS' },
          { value: 541, label: 'BIKES' },
        ]}
      />

      {/* Tool — two-column workbench (inputs left, results right; stacks below lg) */}
      <section className="px-4 sm:px-6 pb-16 md:pb-24">
        <div className="max-w-6xl mx-auto">
          <BuildOptimizer />

          <div className="mt-10 text-center">
            <Link href="/simulator" className="btn-ghost">
              <Zap size={15} aria-hidden="true" /> Open the full simulator
            </Link>
          </div>
        </div>
      </section>

      <SiteFooter />
    </div>
  );
}
