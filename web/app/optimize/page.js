'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';
import { Wrench, Zap } from 'lucide-react';
import SiteNav from '../../components/SiteNav';
import SiteFooter from '../../components/SiteFooter';
import BuildOptimizer from '../../components/BuildOptimizer';

export default function OptimizePage() {
  return (
    <div className="min-h-screen bg-black text-white overflow-x-hidden">
      <SiteNav />

      {/* Hero */}
      <section className="pt-28 sm:pt-32 pb-6 px-4 sm:px-6">
        <div className="max-w-3xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-brand-orange/10 border border-brand-orange/30 text-[11px] font-mono text-brand-orange uppercase tracking-widest mb-4">
              <Wrench size={12} /> Build Optimizer
            </span>
            <h1 className="font-display font-bold text-3xl sm:text-5xl tracking-tight mb-4">
              The fastest build <span className="text-gradient-orange">for your budget</span>
            </h1>
            <p className="text-white/60 text-base sm:text-lg max-w-2xl mx-auto">
              Set a bike and a ₹ budget. MotoQuant runs a physics-based knapsack across every
              compatible upgrade and returns the combination that drops your quarter-mile ET the
              most — with cost-per-tenth, synergies, and the best next part to buy.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Tool */}
      <section className="px-4 sm:px-6 pb-16">
        <div className="max-w-2xl mx-auto">
          <BuildOptimizer />

          <div className="mt-8 text-center">
            <Link
              href="/simulator"
              className="inline-flex items-center justify-center gap-2 px-5 py-2.5 border border-white/15 text-white/70 hover:text-white hover:border-brand-orange/40 font-display font-semibold rounded-lg text-sm transition-colors"
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
