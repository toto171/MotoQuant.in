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
          { value: 593, label: 'PARTS' },
          { value: 541, label: 'BIKES' },
        ]}
      />

      {/* Tool — two-column workbench (controls left, results right; stacks below lg) */}
      <section className="px-4 sm:px-6 py-20 md:py-28 border-t border-brand-orange/10">
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
