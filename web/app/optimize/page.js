'use client';

import Link from 'next/link';
import { Zap } from 'lucide-react';
import SiteNav from '../../components/SiteNav';
import SiteFooter from '../../components/SiteFooter';
import PageHero from '../../components/PageHero';
import BuildOptimizer from '../../components/BuildOptimizer';

export default function OptimizePage() {
  return (
    <div className="min-h-screen bg-black text-white overflow-x-hidden">
      <SiteNav />

      <PageHero
        align="center"
        kicker="knapsack solver · ₹100 buckets · exclusivity enforced"
        badge="Build Optimizer"
        title={
          <>
            The fastest build <span className="text-gradient-orange">for your budget</span>
          </>
        }
        sub="Set a bike and a ₹ budget. MotoQuant runs a physics-based knapsack across every compatible upgrade and returns the combination that drops your quarter-mile ET the most — with cost-per-tenth, synergies, and the best next part to buy."
        stats={[
          { value: 563, label: 'PARTS' },
          { value: 501, label: 'BIKES' },
        ]}
      />

      {/* Tool */}
      <section className="px-4 sm:px-6 py-20 md:py-28 border-t border-brand-orange/10">
        <div className="max-w-2xl mx-auto">
          <BuildOptimizer />

          <div className="mt-8 text-center">
            <Link
              href="/simulator"
              className="inline-flex items-center justify-center gap-2 px-5 py-2.5 border border-white/15 text-white/70 hover:text-white hover:border-brand-orange/40 font-display font-semibold rounded-md text-sm transition-colors"
            >
              <Zap size={15} /> Open the full simulator
            </Link>
          </div>
        </div>
      </section>

      <SiteFooter />
    </div>
  );
}
