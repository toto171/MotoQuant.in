'use client';

import { Suspense, useState } from 'react';
import { Send, ChevronRight } from 'lucide-react';
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
    label: 'Physics engine + Database',
    desc: '15 sub-models, 501 bikes, 563 parts, 20 venues, 976 tests. Full validation suite.',
  },
  {
    phase: 'Phase 3',
    status: 'complete',
    label: 'Web launch + Calibration pipeline',
    desc: 'FastAPI backend, Next.js frontend live at motoquant.in. Dragy/dyno/ECU import + auto-calibrator.',
  },
  {
    phase: 'Phase 4',
    status: 'in-progress',
    label: 'AI & Optimisation',
    desc: 'Parts ROI knapsack, Bayesian build optimiser, XGBoost & DNN surrogates, Smart Recommendations.',
  },
  {
    phase: 'Phase 5',
    status: 'in-progress',
    label: 'Native Desktop App',
    desc: 'Tauri 2 + React 19 shell. Offline physics sidecar. macOS, Windows, Linux. Closed beta.',
  },
  {
    phase: 'Phase 6',
    status: 'in-progress',
    label: 'Commercial launch + AI layer',
    desc: 'Accounts + freemium tiers live (free during open beta). Razorpay + Stripe payment rails wired. Conversational AI tuning shipped. PPO launch control next.',
  },
];

/* ── status-dot voice: brand-green = shipped · brand-amber pulse = in
      progress · hollow white/30 = future. One language, no ad-hoc hues. ── */
const STATUS_DOT = {
  complete: 'bg-brand-green border-brand-green',
  'in-progress': 'bg-brand-amber border-brand-amber animate-pulse',
  planned: 'bg-transparent border-white/30',
};
const STATUS_PILL = {
  complete: 'bg-brand-green/10 text-brand-green',
  'in-progress': 'bg-brand-amber/15 text-brand-amber',
  planned: 'bg-white/5 text-white/40',
};

function FounderCard({ initial, name, role, email, children }) {
  return (
    <div className="relative overflow-hidden rounded-2xl border border-brand-orange/20 bg-ink-1/60 p-8">
      <span
        aria-hidden="true"
        className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-brand-orange/60 to-transparent"
      />
      <div className="flex items-start gap-5 mb-5">
        <div className="w-14 h-14 rounded-full bg-brand-orange/20 border border-brand-orange/40 flex items-center justify-center shrink-0">
          <span className="text-brand-orange font-display font-bold text-xl">{initial}</span>
        </div>
        <div>
          <div className="font-display font-bold text-xl text-white mb-0.5">{name}</div>
          <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-white/45">{role}</div>
        </div>
      </div>
      <div className="space-y-3 text-white/70 text-sm leading-relaxed">{children}</div>
      <a
        href={`mailto:${email}`}
        className="inline-flex items-center gap-1.5 mt-5 text-sm text-brand-accent font-mono hover:text-brand-orange transition-colors"
      >
        {email} <ChevronRight size={14} />
      </a>
    </div>
  );
}

export default function AboutPage() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [sent, setSent] = useState(false);

  function handleSubmit(e) {
    e.preventDefault();
    // Wire to Formspree or a POST /api/contact endpoint when ready.
    // For now, fall through to mailto as a reliable baseline.
    const subject = encodeURIComponent(`MotoQuant — message from ${name}`);
    const body = encodeURIComponent(`Name: ${name}\nEmail: ${email}\n\n${message}`);
    window.location.href = `mailto:motoquant@gmail.com?subject=${subject}&body=${body}`;
    setSent(true);
  }

  const inputCls =
    'w-full bg-ink-0/70 border border-white/10 rounded-lg px-3 py-2.5 text-sm text-white placeholder-white/30 focus:outline-none focus:border-brand-orange/60 transition-colors';
  const labelCls =
    'block font-mono text-[10px] uppercase tracking-[0.25em] text-white/45 mb-1.5';

  return (
    <div className="min-h-screen bg-ink-0 text-white overflow-x-hidden">
      {/* Nav */}
      <SiteNav />

      {/* Hero — unified cockpit voice */}
      <PageHero
        kicker="founders · pune, india"
        badge="Our story"
        title={<>Built in Pune.<br />For <span className="text-gradient-orange">the strip.</span></>}
        sub={
          <>
            MotoQuant started as a single question at a drag strip outside Pune: <em>&ldquo;How do I know which part will actually move my ET?&rdquo;</em> Every tuner, racer, and weekend warrior we talked to had the same problem. The answers were guesswork, YouTube comments, or ₹50,000 test runs. There had to be a better way.
          </>
        }
        className="border-b border-brand-orange/10"
      />

      {/* Story */}
      <section className="py-20 md:py-28 px-6 border-b border-brand-orange/10 max-w-6xl mx-auto">
        <CodeComment className="mb-10">problem statement · loaded</CodeComment>
        <div className="grid md:grid-cols-2 gap-12 items-start">
          <Reveal>
            <h2 className="font-display font-bold text-3xl mb-6 text-white">The Problem We Solve</h2>
            <div className="space-y-4 text-white/70 text-sm leading-relaxed">
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
            <h2 className="font-display font-bold text-3xl mb-6 text-white">Why First Principles?</h2>
            <div className="space-y-4 text-white/70 text-sm leading-relaxed">
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
                Top-10 mean error after our April 2026 calibration pass: <strong className="text-brand-orange">±0.006s</strong>. Reference baselines within 0.001s of targets. That&apos;s what first principles buys you.
              </p>
            </div>
          </Reveal>
        </div>
      </section>

      {/* Founders */}
      <section className="py-20 md:py-28 px-6 border-b border-brand-orange/10 bg-ink-1/30">
        <div className="max-w-5xl mx-auto">
          <CodeComment className="mb-10">crew manifest · two entries</CodeComment>
          <h2 className="font-display font-bold text-3xl md:text-4xl mb-3 text-white">Founders</h2>
          <p className="font-mono text-[10px] uppercase tracking-[0.25em] text-white/45 mb-10">
            Engineers first. Racers second. Shipping a tool we&apos;d use ourselves.
          </p>

          <div className="grid md:grid-cols-2 gap-6">
            <Reveal>
              <FounderCard initial="A" name="Arya Desai" role="Co-founder · Pune, India" email="motoquant@gmail.com">
                <p>
                  Automobile engineer — M.Tech at NIT Warangal, B.Tech from Manipal Institute of Technology (Automotive System Design). The physics-and-shop-floor side of MotoQuant.
                </p>
                <p>
                  At NIT-W his research runs close to MotoQuant&apos;s core stack: a CFD validation study of split-injection strategy in a single-cylinder diesel engine (ANSYS Forte, 28-species n-heptane kinetics, 60° sector mesh, peak-pressure match within 1.6% on the optimal case); a semi-active MR suspension paper that uses six-seed Monte Carlo on ISO 8608 roads to show comfort-optimised skyhook controllers actually lose 18–23% in ride comfort once realistic bump-stops engage — with a full reproducibility artefact; and a design patent filed with NIT-W&apos;s IP Cell.
                </p>
                <p>
                  Hands-on side: diagnosed and performance-tuned 25+ luxury and performance vehicles at Power Solutions Pune — Mercedes AMG, BMW, Audi, Jaguar Land Rover, Lincoln — including a flagship Mercedes AMG SLS valvetronic exhaust install. ECU-tuning certified (Techmaghi / ReynLab). Undergrad research at MIT Manipal on PU-based magnetorheological elastomers delivered a 22% improvement in vibration damping.
                </p>
              </FounderCard>
            </Reveal>

            <Reveal delay={0.08}>
              <FounderCard initial="R" name="Ritwik Singh" role="Co-founder · Bengaluru, India" email="dhisetu@gmail.com">
                <p>
                  Automobile and AI engineer by experience — the physics, software, and machine-learning side of MotoQuant. Built the 15-sub-model drag simulation engine, the bike-and-parts catalog, and the calibration pipeline that fits sim output to real Dragy traces within ±0.05 s.
                </p>
                <p>
                  Wrote the load-bearing physics from the ground up: the RK4 integrator, the Pacejka tire model, the expansion-chamber two-stroke curve, and the clutch-slip thermal model — caring more about which terms actually survive the force balance than about a good-looking regression. The AI layer is his too — a DNN surrogate that predicts an ET in ~1 ms, an XGBoost-backed ROI ranker, a Bayesian build optimiser, and a natural-language tuning interface.
                </p>
                <p>
                  Outside MotoQuant he&apos;s building Dhisetu, an AI-assisted indie game studio, from Bengaluru — and a hardcore indie gamer, which is where the instinct comes from. His bet: the next wave of studios won&apos;t look like teams but solo creators with AI co-pilots, shipping as fast as ideas come. Same instinct here — one engineer, the right tools, a sim serious tuners keep open on a second monitor.
                </p>
              </FounderCard>
            </Reveal>
          </div>
        </div>
      </section>

      {/* Roadmap */}
      <section className="py-20 md:py-28 px-6 border-b border-brand-orange/10">
        <div className="max-w-4xl mx-auto">
          <CodeComment className="mb-10">mission plan · phase 6 in progress</CodeComment>
          <h2 className="font-display font-bold text-3xl md:text-4xl mb-3 text-white">Where We&apos;re Going</h2>
          <p className="font-mono text-[10px] uppercase tracking-[0.25em] text-white/45 mb-12">
            Roadmap — no specific dates, shipping when it&apos;s right
          </p>

          <div className="relative pl-6 border-l border-brand-orange/20 space-y-10">
            {ROADMAP.map((item, i) => (
              <Reveal key={i} y={14} duration={0.45} delay={i * 0.08} className="relative">
                {/* Dot */}
                <div
                  className={`absolute -left-[1.625rem] top-1.5 w-3 h-3 rounded-full border-2 ${STATUS_DOT[item.status] ?? STATUS_DOT.planned}`}
                />

                <div className="flex items-center gap-3 mb-1.5">
                  <span className="font-mono text-[10px] text-white/45 uppercase tracking-[0.25em]">{item.phase}</span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase tracking-wide ${STATUS_PILL[item.status] ?? STATUS_PILL.planned}`}>
                    {item.status === 'complete' ? 'Done' : item.status === 'in-progress' ? 'In progress' : 'Planned'}
                  </span>
                </div>
                <h3 className="font-display font-bold text-lg text-white mb-1">{item.label}</h3>
                <p className="text-white/60 text-sm leading-relaxed">{item.desc}</p>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* Contact */}
      <section className="py-20 md:py-28 px-6 border-b border-brand-orange/10 bg-ink-1/30">
        <div className="max-w-4xl mx-auto">
          <CodeComment className="mb-10">comms channel · open</CodeComment>
          <div className="grid md:grid-cols-2 gap-12">
            <div>
              <h2 className="font-display font-bold text-3xl mb-4 text-white">Get in Touch</h2>
              <p className="text-white/60 text-sm leading-relaxed mb-6">
                Whether you&apos;re a tuning shop interested in the Pro plan, a racer who found a bug, or just want to talk drag racing — reach out.
              </p>
              <div className="space-y-3">
                <div>
                  <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-white/45 mb-1">Email</div>
                  <a href="mailto:motoquant@gmail.com" className="font-mono text-brand-accent hover:text-brand-orange transition-colors text-sm">
                    motoquant@gmail.com
                  </a>
                </div>
                <div>
                  <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-white/45 mb-1">Location</div>
                  <span className="font-mono text-white/70 text-sm">Pune, Maharashtra, India</span>
                </div>
                <div>
                  <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-white/45 mb-1">Pro licensing</div>
                  <a href="mailto:motoquant@gmail.com?subject=MotoQuant%20Pro%20Licensing" className="font-mono text-brand-accent hover:text-brand-orange transition-colors text-sm">
                    Request a quote →
                  </a>
                </div>
              </div>
            </div>

            <div>
              {sent ? (
                <div className="relative overflow-hidden rounded-xl border border-brand-green/30 bg-ink-1/60 p-8 text-center">
                  <span
                    aria-hidden="true"
                    className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-brand-green/60 to-transparent"
                  />
                  <div className="text-brand-green text-3xl mb-3">✓</div>
                  <h3 className="font-display font-bold text-white mb-2">Message sent!</h3>
                  <p className="text-white/60 text-sm">Your mail client should have opened with a pre-filled message. If not, email motoquant@gmail.com directly.</p>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="relative overflow-hidden rounded-xl border border-brand-orange/20 bg-ink-1/60 p-6 space-y-4">
                  <span
                    aria-hidden="true"
                    className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-brand-orange/60 to-transparent"
                  />
                  <div>
                    <label className={labelCls}>Your name</label>
                    <input
                      type="text"
                      value={name}
                      onChange={e => setName(e.target.value)}
                      required
                      className={inputCls}
                      placeholder="Arjun Sharma"
                    />
                  </div>
                  <div>
                    <label className={labelCls}>Email</label>
                    <input
                      type="email"
                      value={email}
                      onChange={e => setEmail(e.target.value)}
                      required
                      className={inputCls}
                      placeholder="you@example.com"
                    />
                  </div>
                  <div>
                    <label className={labelCls}>Message</label>
                    <textarea
                      value={message}
                      onChange={e => setMessage(e.target.value)}
                      required
                      rows={5}
                      className={`${inputCls} resize-none`}
                      placeholder="Tell us what you want to know, build, or break."
                    />
                  </div>
                  <button
                    type="submit"
                    className="w-full inline-flex items-center justify-center gap-2 px-5 py-3 bg-brand-orange text-black font-display font-bold rounded-md hover:bg-brand-orangeLight transition-colors shadow-orange-soft"
                  >
                    <Send size={14} /> Send message
                  </button>
                </form>
              )}
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
