'use client';

import { Suspense, useState } from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { Send, ChevronRight, Zap, Flag, Target, Cpu } from 'lucide-react';
import SiteNav from '../../components/SiteNav';
import SiteFooter from '../../components/SiteFooter';
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

  return (
    <div className="min-h-screen bg-ink-0 text-white overflow-x-hidden">
      {/* Nav */}
      <SiteNav />

      {/* Hero */}
      <section className="pt-32 pb-20 px-6 border-b border-brand-orange/10">
        <div className="max-w-3xl mx-auto">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}
            className="mb-4 inline-block px-4 py-1.5 rounded-full border border-brand-orange/40 bg-brand-orange/10 text-xs font-mono text-brand-orange uppercase tracking-widest"
          >
            Our story
          </motion.div>
          <motion.h1 initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1, duration: 0.6 }}
            className="font-display font-bold text-5xl md:text-6xl mb-6 tracking-tighter text-gradient-orange"
          >
            Built in Pune.<br/>For the strip.
          </motion.h1>
          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.25, duration: 0.6 }}
            className="text-white/70 text-lg leading-relaxed"
          >
            MotoQuant started as a single question at a drag strip outside Pune: <em>&ldquo;How do I know which part will actually move my ET?&rdquo;</em> Every tuner, racer, and weekend warrior we talked to had the same problem. The answers were guesswork, YouTube comments, or ₹50,000 test runs. There had to be a better way.
          </motion.p>
        </div>
      </section>

      {/* Story */}
      <section className="py-20 px-6 border-b border-brand-orange/10 max-w-6xl mx-auto">
        <div className="grid md:grid-cols-2 gap-12 items-start">
          <div>
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
          </div>
          <div>
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
                Top-10 mean error after our April 2026 calibration pass: <strong className="text-brand-orange">±0.032s</strong>. Reference baselines within 0.001s of targets. That&apos;s what first principles buys you.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Founders */}
      <section className="py-20 px-6 border-b border-brand-orange/10 bg-ink-1/30">
        <div className="max-w-5xl mx-auto">
          <h2 className="font-display font-bold text-3xl md:text-4xl mb-3 text-white">Founders</h2>
          <p className="text-white/60 text-sm font-mono mb-10 uppercase tracking-wide">Engineers first. Racers second. Shipping a tool we&apos;d use ourselves.</p>

          <div className="grid md:grid-cols-2 gap-6">
            {/* Founder 1 — Arya Desai */}
            <div className="glass rounded-2xl p-8 border border-brand-orange/20">
              <div className="flex items-start gap-5 mb-5">
                <div className="w-14 h-14 rounded-full bg-brand-orange/20 border border-brand-orange/40 flex items-center justify-center shrink-0">
                  <span className="text-brand-orange font-display font-bold text-xl">A</span>
                </div>
                <div>
                  <div className="font-display font-bold text-xl text-white mb-0.5">Arya Desai</div>
                  <div className="font-mono text-xs text-white/50">Co-founder · Pune, India</div>
                </div>
              </div>
              <div className="space-y-3 text-white/70 text-sm leading-relaxed">
                <p>
                  Automobile engineer — M.Tech at NIT Warangal, B.Tech from Manipal Institute of Technology (Automotive System Design). The physics-and-shop-floor side of MotoQuant.
                </p>
                <p>
                  At NIT-W his research runs close to MotoQuant&apos;s core stack: a CFD validation study of split-injection strategy in a single-cylinder diesel engine (ANSYS Forte, 28-species n-heptane kinetics, 60° sector mesh, peak-pressure match within 1.6% on the optimal case); a semi-active MR suspension paper that uses six-seed Monte Carlo on ISO 8608 roads to show comfort-optimised skyhook controllers actually lose 18–23% in ride comfort once realistic bump-stops engage — with a full reproducibility artefact; and a design patent filed with NIT-W&apos;s IP Cell.
                </p>
                <p>
                  Hands-on side: diagnosed and performance-tuned 25+ luxury and performance vehicles at Power Solutions Pune — Mercedes AMG, BMW, Audi, Jaguar Land Rover, Lincoln — including a flagship Mercedes AMG SLS valvetronic exhaust install. ECU-tuning certified (Techmaghi / ReynLab). Undergrad research at MIT Manipal on PU-based magnetorheological elastomers delivered a 22% improvement in vibration damping.
                </p>
              </div>
              <a
                href="mailto:motoquant@gmail.com"
                className="inline-flex items-center gap-1.5 mt-5 text-sm text-brand-accent font-mono hover:text-brand-orange transition-colors"
              >
                motoquant@gmail.com <ChevronRight size={14} />
              </a>
            </div>

            {/* Founder 2 — Hritwik Mudhai */}
            <div className="glass rounded-2xl p-8 border border-brand-orange/20">
              <div className="flex items-start gap-5 mb-5">
                <div className="w-14 h-14 rounded-full bg-brand-orange/20 border border-brand-orange/40 flex items-center justify-center shrink-0">
                  <span className="text-brand-orange font-display font-bold text-xl">H</span>
                </div>
                <div>
                  <div className="font-display font-bold text-xl text-white mb-0.5">Hritwik Mudhai</div>
                  <div className="font-mono text-xs text-white/50">Co-founder · Manipal, India</div>
                </div>
              </div>
              <div className="space-y-3 text-white/70 text-sm leading-relaxed">
                <p>
                  The physics + software side. Built the 15-sub-model drag simulation engine, the 334-bike catalog, the ROI knapsack, and the calibration pipeline that fits sim output to real Dragy traces within ±0.05 s.
                </p>
                <p>
                  AI engineer by trade — currently building a separate AI startup in parallel. That expertise is baked into MotoQuant&apos;s machine-learning layer: the DNN surrogate (1 ms per ET prediction), the XGBoost-backed ROI ranker, the Bayesian build optimiser, and the natural-language tuning interface.
                </p>
                <p>
                  Wrote the RK4 integrator, the Pacejka tire model, the expansion-chamber 2-stroke curve, and the clutch-slip thermal model from the ground up. Cares more about which terms actually survive the force balance than about chasing a good-looking regression. Wants MotoQuant to be the tool every serious tuner already has open on a second monitor.
                </p>
              </div>
              <a
                href="mailto:dhisetu@gmail.com"
                className="inline-flex items-center gap-1.5 mt-5 text-sm text-brand-accent font-mono hover:text-brand-orange transition-colors"
              >
                dhisetu@gmail.com <ChevronRight size={14} />
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Roadmap */}
      <section className="py-20 px-6 border-b border-brand-orange/10">
        <div className="max-w-4xl mx-auto">
          <h2 className="font-display font-bold text-3xl md:text-4xl mb-3 text-white">Where We&apos;re Going</h2>
          <p className="text-white/60 text-sm font-mono mb-12 uppercase tracking-wide">Roadmap — no specific dates, shipping when it&apos;s right</p>

          <div className="relative pl-6 border-l border-brand-orange/20 space-y-10">
            {ROADMAP.map((item, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -10 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.08 }}
                className="relative"
              >
                {/* Dot */}
                <div className={`absolute -left-[1.625rem] top-1.5 w-3 h-3 rounded-full border-2 ${
                  item.status === 'complete' ? 'bg-brand-accent border-brand-accent' :
                  item.status === 'in-progress' ? 'bg-brand-orange border-brand-orange animate-pulse' :
                  'bg-transparent border-white/30'
                }`} />

                <div className="flex items-center gap-3 mb-1.5">
                  <span className="font-mono text-[10px] text-white/40 uppercase tracking-widest">{item.phase}</span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase tracking-wide ${
                    item.status === 'complete' ? 'bg-brand-accent/10 text-brand-accent' :
                    item.status === 'in-progress' ? 'bg-brand-orange/15 text-brand-orange' :
                    'bg-white/5 text-white/40'
                  }`}>
                    {item.status === 'complete' ? 'Done' : item.status === 'in-progress' ? 'In progress' : 'Planned'}
                  </span>
                </div>
                <h3 className="font-display font-bold text-lg text-white mb-1">{item.label}</h3>
                <p className="text-white/60 text-sm leading-relaxed">{item.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Contact */}
      <section className="py-20 px-6 border-b border-brand-orange/10 bg-ink-1/30">
        <div className="max-w-4xl mx-auto">
          <div className="grid md:grid-cols-2 gap-12">
            <div>
              <h2 className="font-display font-bold text-3xl mb-4 text-white">Get in Touch</h2>
              <p className="text-white/60 text-sm leading-relaxed mb-6">
                Whether you&apos;re a tuning shop interested in the Pro plan, a racer who found a bug, or just want to talk drag racing — reach out.
              </p>
              <div className="space-y-3">
                <div>
                  <div className="text-xs font-mono text-white/40 uppercase tracking-widest mb-1">Email</div>
                  <a href="mailto:motoquant@gmail.com" className="font-mono text-brand-accent hover:text-brand-orange transition-colors text-sm">
                    motoquant@gmail.com
                  </a>
                </div>
                <div>
                  <div className="text-xs font-mono text-white/40 uppercase tracking-widest mb-1">Location</div>
                  <span className="font-mono text-white/70 text-sm">Pune, Maharashtra, India</span>
                </div>
                <div>
                  <div className="text-xs font-mono text-white/40 uppercase tracking-widest mb-1">Pro licensing</div>
                  <a href="mailto:motoquant@gmail.com?subject=MotoQuant%20Pro%20Licensing" className="font-mono text-brand-accent hover:text-brand-orange transition-colors text-sm">
                    Request a quote →
                  </a>
                </div>
              </div>
            </div>

            <div>
              {sent ? (
                <div className="glass rounded-xl p-8 border border-brand-accent/30 text-center">
                  <div className="text-brand-accent text-3xl mb-3">✓</div>
                  <h3 className="font-display font-bold text-white mb-2">Message sent!</h3>
                  <p className="text-white/60 text-sm">Your mail client should have opened with a pre-filled message. If not, email motoquant@gmail.com directly.</p>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="glass rounded-xl p-6 border border-brand-orange/20 space-y-4">
                  <div>
                    <label className="block text-xs font-mono text-white/50 uppercase tracking-wider mb-1.5">Your name</label>
                    <input
                      type="text"
                      value={name}
                      onChange={e => setName(e.target.value)}
                      required
                      className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2.5 text-sm text-white placeholder-white/30 focus:outline-none focus:border-brand-orange/60 transition-colors"
                      placeholder="Arjun Sharma"
                    />
                              </div>
                  <div>
                    <label className="block text-xs font-mono text-white/50 uppercase tracking-wider mb-1.5">Email</label>
                    <input
                      type="email"
                      value={email}
                      onChange={e => setEmail(e.target.value)}
                      required
                      className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2.5 text-sm text-white placeholder-white/30 focus:outline-none focus:border-brand-orange/60 transition-colors"
                      placeholder="you@example.com"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-mono text-white/50 uppercase tracking-wider mb-1.5">Message</label>
                    <textarea
                      value={message}
                      onChange={e => setMessage(e.target.value)}
                      required
                      rows={5}
                      className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2.5 text-sm text-white placeholder-white/30 focus:outline-none focus:border-brand-orange/60 transition-colors resize-none"
                      placeholder="Tell us what you want to know, build, or break."
                    />
                  </div>
                  <button
                    type="submit"
                    className="w-full inline-flex items-center justify-center gap-2 px-5 py-3 bg-brand-orange text-black font-display font-bold rounded-lg hover:bg-brand-orangeLight transition-colors"
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
