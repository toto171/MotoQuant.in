'use client';

import { Suspense } from 'react';
import { Mail, ChevronRight } from 'lucide-react';
import SiteNav from '../../components/SiteNav';
import SiteFooter from '../../components/SiteFooter';
import PageHero from '../../components/PageHero';
import CodeComment from '../../components/CodeComment';
import { Reveal } from '../../components/Reveal';
import EndOfAboutCta from './EndOfAboutCta';

const ROADMAP = [
  {
    phase: 'Phase 1–2',
    status: 'complete',
    label: 'Physics engine + database',
    desc: '15 sub-models, 541 bikes, 593 parts, 20 venues, 4,393 tests. Full validation suite.',
  },
  {
    phase: 'Phase 3',
    status: 'complete',
    label: 'Web launch + calibration pipeline',
    desc: 'FastAPI backend, Next.js frontend live at motoquant.in. Dragy/dyno/ECU import + auto-calibrator.',
  },
  {
    phase: 'Phase 4',
    status: 'in-progress',
    label: 'AI & optimisation',
    desc: 'Parts ROI knapsack, Bayesian build optimiser, XGBoost & DNN surrogates, Smart Recommendations.',
  },
  // Phase 5 (native desktop app) was DISCONTINUED July 2026 — the hosted web
  // app is the product. Removed from the public roadmap; the phase numbering
  // below is unchanged so historical references stay meaningful.
  {
    phase: 'Phase 6',
    status: 'in-progress',
    label: 'Commercial launch + AI layer',
    desc: 'Accounts + freemium tiers live (free during open beta). Razorpay + Stripe payment rails wired. Conversational AI tuning shipped. PPO launch control next.',
  },
];

/* ── status voice: signal-go = shipped · signal-stage = in progress ·
      hollow white/30 = future. Signal colors carry state only; no
      infinite pulse (motion doctrine). ── */
const STATUS_DOT = {
  complete: 'bg-signal-go border-signal-go',
  'in-progress': 'bg-signal-stage border-signal-stage',
  planned: 'bg-transparent border-white/30',
};
const STATUS_PILL = {
  complete: 'chip chip-go',
  'in-progress': 'chip chip-stage',
  planned: 'chip',
};

function FounderCard({ initial, name, role, email, children }) {
  return (
    <div className="card h-full p-6 md:p-8">
      <div className="flex items-start gap-5 mb-5">
        <div className="w-14 h-14 rounded-full bg-asphalt-3 border border-white/10 flex items-center justify-center shrink-0">
          <span className="text-white font-display font-bold text-xl">{initial}</span>
        </div>
        <div>
          <div className="font-display font-semibold text-lg md:text-xl text-white mb-0.5">{name}</div>
          <div className="label-mono">{role}</div>
        </div>
      </div>
      <div className="space-y-3 text-white/65 text-sm leading-relaxed">{children}</div>
      <a
        href={`mailto:${email}`}
        className="inline-flex items-center gap-1.5 mt-5 text-sm text-white/60 font-mono hover:text-white transition-colors"
      >
        {email} <ChevronRight size={14} />
      </a>
    </div>
  );
}

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-asphalt-0 text-white overflow-x-hidden">
      {/* Nav */}
      <SiteNav />

      {/* Hero — IGNITION v5 voice */}
      <PageHero
        kicker="founders · india"
        badge="Our story"
        title={<>Built in Pune.<br />For <span className="text-gradient-orange">the strip.</span></>}
        sub={
          <>
            MotoQuant started as a single question at a drag strip outside Pune: <em>&ldquo;How do I know which part will actually move my ET?&rdquo;</em> Every tuner, racer, and weekend warrior we talked to had the same problem. The answers were guesswork, YouTube comments, or ₹50,000 test runs. There had to be a better way.
          </>
        }
      />

      {/* Story */}
      <section className="py-16 md:py-24 px-6 border-b border-white/5 max-w-6xl mx-auto">
        <CodeComment className="mb-10">problem statement · loaded</CodeComment>
        <div className="grid md:grid-cols-2 gap-12 items-start">
          <Reveal>
            <h2 className="font-display font-bold text-3xl tracking-tight mb-6 text-white">The <span className="text-accent">problem</span> we solve</h2>
            <div className="space-y-4 text-white/65 text-sm leading-relaxed">
              <p>
                Indian drag racing has exploded over the last decade. Aamby Valley, MMRT, BIC, Kari, Hyderabad — the strips are full. But the tooling hasn&apos;t kept up. Racers still tune by feel and magazine estimates. Tuning shops quote improvements from memory. Parts distributors can&apos;t tell you how much faster that exhaust will actually make you.
              </p>
              <p>
                Meanwhile, the global sim tools that do exist are built for international bikes and international conditions. A tool calibrated for Santa Pod at 5°C doesn&apos;t tell you anything useful about Aamby Valley at 35°C and 1100 m density altitude in November.
              </p>
              <p>
                MotoQuant is built specifically for the Indian drag scene — with Indian bikes (all 57 of the most common Indian-market machines), Indian parts prices in INR, Indian venues with real seasonal weather data, and Indian community benchmarks used for validation.
              </p>
            </div>
          </Reveal>
          <Reveal delay={0.08}>
            <h2 className="font-display font-bold text-3xl tracking-tight mb-6 text-white">Why <span className="text-accent">first principles</span>?</h2>
            <div className="space-y-4 text-white/65 text-sm leading-relaxed">
              <p>
                We could have built a regression. Train on a database of published ETs, predict new ones by interpolation. Fast to build, reasonable accuracy for common bikes.
              </p>
              <p>
                But regressions break silently. They can&apos;t tell you <em>why</em> your R15 V3 is a second slower than predicted. They can&apos;t model the interaction between a new clutch kit and a heavier flywheel. They can&apos;t simulate what happens when you run the same bike at 5°C versus 38°C.
              </p>
              <p>
                First-principles physics can. Every sub-model — Pacejka tire, Willans friction engine, RK4 integrator — produces physically interpretable outputs. When the model is wrong, we can find and fix the cause. When you add a part, the physics of that part propagates through the whole system.
              </p>
              <p>
                Top-10 mean error after our August 2026 calibration pass: <strong className="font-mono tabular-nums text-accent">±0.007s</strong>. Reference baselines pinned bit-identical across every commit. That&apos;s what first principles buys you.
              </p>
            </div>
          </Reveal>
        </div>
      </section>

      {/* Founders */}
      <section className="py-16 md:py-24 px-6 border-b border-white/5 bg-asphalt-1/30">
        <div className="max-w-6xl mx-auto">
          <CodeComment className="mb-10">crew manifest · three entries</CodeComment>
          <h2 className="font-display font-bold text-3xl md:text-4xl tracking-tight mb-3 text-white">Founders</h2>
          <p className="label-mono mb-10">
            Engineers first. Racers second. Shipping a tool we&apos;d use ourselves.
          </p>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
            <Reveal>
              <FounderCard initial="A" name="Arya Desai" role="Co-founder & Lead Engineer · Pune, India" email="motoquant@gmail.com">
                <p>
                  The engineer who started MotoQuant and leads it — M.Tech from NIT Warangal, B.Tech from Manipal (Automotive System Design). He owns the physics: the vehicle-dynamics model, the calibration against real Dragy traces, and where the engine goes next.
                </p>
                <p>
                  Depth from both sides of the workshop door — CFD engine-combustion and magnetorheological-suspension research at NIT-W (plus a filed design patent) on one side; 25+ performance cars tuned by hand at Power Solutions Pune — Mercedes-AMG, BMW, Audi, Jaguar Land Rover — on the other. ECU-tuning certified.
                </p>
              </FounderCard>
            </Reveal>

            <Reveal delay={0.08}>
              <FounderCard initial="R" name="Ritwik Singh" role="Co-founder & Advisor · Bengaluru, India" email="dhisetu@gmail.com">
                <p>
                  Automobile-and-AI engineer — the software and machine-learning instinct behind MotoQuant&apos;s early architecture, from the simulation scaffolding to the first surrogate models and ROI ranker. Now a co-founder and advisor, still close to the technical direction.
                </p>
                <p>
                  Day to day he&apos;s building Dhisetu, an AI-assisted indie game studio in Bengaluru — a hardcore indie gamer, which is where the instinct comes from. His bet: the next studios won&apos;t be big teams but solo creators with AI co-pilots. Same instinct here.
                </p>
              </FounderCard>
            </Reveal>

            <Reveal delay={0.16}>
              <FounderCard initial="S" name="Sahil Shetye" role="Co-founder & CMO · Manipal, India" email="motoquant@gmail.com">
                <p>
                  Electrical engineer and our pitchman — finishing his B.Tech in EEE at Manipal. The growth-and-market side of MotoQuant, and the electronics half of the hardware roadmap: PCB design, EV powertrain and battery tech, low-level C.
                </p>
                <p>
                  Communication and market knowledge are the levers he owns, plus real market experience — turning a physics engine into something racers and tuning shops actually hear about, and want to implement.
                </p>
                <p className="border-l-2 border-white/15 pl-4 italic text-white/60">
                  &ldquo;In my third year, a major bike accident paused my degree. While recovering, I refused to sit idle — I built a social-media audience and finished multiple industry-standard certifications. I don&apos;t just study engineering; I build, optimize, and execute under pressure.&rdquo;
                </p>
              </FounderCard>
            </Reveal>
          </div>
        </div>
      </section>

      {/* Roadmap */}
      <section className="py-16 md:py-24 px-6 border-b border-white/5">
        <div className="max-w-4xl mx-auto">
          <CodeComment className="mb-10">mission plan · phase 6 in progress</CodeComment>
          <h2 className="font-display font-bold text-3xl md:text-4xl tracking-tight mb-3 text-white">Where we&apos;re <span className="text-accent">going</span></h2>
          <p className="label-mono mb-12">
            Roadmap — no specific dates, shipping when it&apos;s right
          </p>

          <div className="relative pl-6 border-l border-white/10 space-y-10">
            {ROADMAP.map((item, i) => (
              <Reveal key={i} y={14} duration={0.45} delay={i * 0.08} className="relative">
                {/* Dot */}
                <div
                  className={`absolute -left-[1.625rem] top-1.5 w-3 h-3 rounded-full border-2 ${STATUS_DOT[item.status] ?? STATUS_DOT.planned}`}
                />

                <div className="flex items-center gap-3 mb-1.5">
                  <span className="label-mono">{item.phase}</span>
                  <span className={STATUS_PILL[item.status] ?? STATUS_PILL.planned}>
                    {item.status === 'complete' ? 'Done' : item.status === 'in-progress' ? 'In progress' : 'Planned'}
                  </span>
                </div>
                <h3 className="font-display font-semibold text-lg text-white mb-1">{item.label}</h3>
                <p className="text-white/65 text-sm leading-relaxed">{item.desc}</p>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* Contact */}
      <section className="py-16 md:py-24 px-6 border-b border-white/5 bg-asphalt-1/30">
        <div className="max-w-4xl mx-auto">
          <CodeComment className="mb-10">comms channel · open</CodeComment>
          <div className="grid md:grid-cols-2 gap-12">
            <div>
              <h2 className="font-display font-bold text-3xl tracking-tight mb-4 text-white">Get in touch</h2>
              <p className="text-white/65 text-sm leading-relaxed mb-6">
                Whether you&apos;re a tuning shop interested in the Pro plan, a racer who found a bug, or just want to talk drag racing — reach out.
              </p>
              <div className="space-y-3">
                <div>
                  <div className="label-mono mb-1">Email</div>
                  <a href="mailto:motoquant@gmail.com" className="font-mono text-white/80 hover:text-white transition-colors text-sm">
                    motoquant@gmail.com
                  </a>
                </div>
                <div>
                  <div className="label-mono mb-1">Location</div>
                  <span className="font-mono text-white/70 text-sm">Pune, Maharashtra, India</span>
                </div>
                <div>
                  <div className="label-mono mb-1">Pro licensing</div>
                  <a href="mailto:motoquant@gmail.com?subject=MotoQuant%20Pro%20Licensing" className="font-mono text-white/80 hover:text-white transition-colors text-sm">
                    Request a quote →
                  </a>
                </div>
              </div>
            </div>

            {/* Honest direct-contact card — no fake form, no fake "sent"
                state. One mailto action; email is the real channel. */}
            <div className="card p-6 md:p-8">
              <div className="label-mono mb-3">Direct line</div>
              <h3 className="font-display font-semibold text-lg md:text-xl text-white mb-3">
                Email us — a founder replies
              </h3>
              <p className="text-white/65 text-sm leading-relaxed mb-6">
                No contact form, no ticket queue. Mail lands straight in the
                founders&apos; inbox and we reply within 48 hours — usually much
                faster. Bug reports with a share link or a Dragy CSV attached
                get answered first.
              </p>
              <a
                href="mailto:motoquant@gmail.com?subject=MotoQuant%20—%20hello"
                className="btn-primary w-full"
              >
                <Mail size={14} /> Email motoquant@gmail.com
              </a>
              <p className="label-mono mt-4 text-center">
                replies within 48h · IST working hours
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* EXP-012: end-of-page simulator CTA (variant B only). */}
      <Suspense fallback={null}>
        <EndOfAboutCta />
      </Suspense>

      <SiteFooter />
    </div>
  );
}
