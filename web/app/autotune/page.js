'use client';

import Link from 'next/link';
import { Zap } from 'lucide-react';
import SiteNav from '../../components/SiteNav';
import SiteFooter from '../../components/SiteFooter';
import PageHero from '../../components/PageHero';
import EcuAutotune from '../../components/EcuAutotune';

export default function AutotunePage() {
  return (
    <div className="min-h-screen bg-black text-white overflow-x-hidden">
      <SiteNav />

      <PageHero
        align="center"
        kicker="density altitude read · gearing sweep armed"
        badge="ECU Autotune"
        title={
          <>
            A setup sheet for <span className="text-gradient-orange">today&apos;s conditions</span>
          </>
        }
        sub="Pick your bike and where you’re running. MotoQuant works out the density altitude and returns gearing, launch RPM, tyre pressure, and fuel/timing — each with the predicted quarter-mile ET change so you know what actually moves the clock."
        stats={[
          { value: 541, label: 'BIKES' },
          { value: 20, label: 'VENUES' },
        ]}
      />

      {/* Tool — two-column workbench (controls left, results right; stacks below lg) */}
      <section className="px-4 sm:px-6 py-20 md:py-28 border-t border-brand-orange/10">
        <div className="max-w-6xl mx-auto">
          <EcuAutotune />

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
