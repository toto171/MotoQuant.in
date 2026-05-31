'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';
import { Sliders, Zap } from 'lucide-react';
import SiteNav from '../../components/SiteNav';
import SiteFooter from '../../components/SiteFooter';
import EcuAutotune from '../../components/EcuAutotune';

export default function AutotunePage() {
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
              <Sliders size={12} /> ECU Autotune
            </span>
            <h1 className="font-display font-bold text-3xl sm:text-5xl tracking-tight mb-4">
              A setup sheet for <span className="text-gradient-orange">today&apos;s conditions</span>
            </h1>
            <p className="text-white/60 text-base sm:text-lg max-w-2xl mx-auto">
              Pick your bike and where you&apos;re running. MotoQuant works out the density altitude
              and returns gearing, launch RPM, tyre pressure, and fuel/timing — each with the
              predicted quarter-mile ET change so you know what actually moves the clock.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Tool */}
      <section className="px-4 sm:px-6 pb-16">
        <div className="max-w-2xl mx-auto">
          <EcuAutotune />

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
