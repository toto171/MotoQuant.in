'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence, useScroll, useTransform, useInView } from 'framer-motion';
import { useRef } from 'react';
import { Zap, TrendingUp, BarChart3, Github, ChevronDown, Cpu, Wind, Gauge, Menu, X } from 'lucide-react';
import SimulatorWidget from '../components/SimulatorWidget';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.1 } },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6 } },
};

const cardHover = {
  y: -4,
  transition: { duration: 0.2 },
};

function RevealSection({ children, className = '' }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });
  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 40 }}
      animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 40 }}
      transition={{ duration: 0.7, ease: 'easeOut' }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

function ScrollIndicator() {
  return (
    <motion.div
      className="absolute bottom-8 left-1/2 -translate-x-1/2"
      animate={{ y: [0, 12, 0] }}
      transition={{ duration: 2, repeat: Infinity }}
    >
      <ChevronDown className="w-6 h-6 text-brand-orange opacity-70" />
    </motion.div>
  );
}

function StatsStrip() {
  const stats = [
    { num: '135', label: 'BIKES' },
    { num: '69', label: 'TIRES' },
    { num: '70', label: 'PARTS' },
    { num: '12', label: 'VENUES' },
    { num: '583', label: 'TESTS' },
    { num: '15', label: 'SUB-MODELS' },
  ];

  return (
    <div className="bg-gradient-to-r from-ink-1 via-ink-0 to-ink-1 border-y border-brand-orange/20 py-8 overflow-hidden">
      <div className="max-w-6xl mx-auto px-6">
        <div className="flex justify-between items-center gap-4 md:gap-8 flex-wrap">
          {stats.map((stat, idx) => (
            <div key={idx} className="flex items-center gap-3">
              <div className="text-center">
                <div className="font-display font-bold text-2xl md:text-3xl text-brand-orange">
                  {stat.num}
                </div>
                <div className="font-mono text-xs text-white/60 tracking-widest">
                  {stat.label}
                </div>
              </div>
              {idx < stats.length - 1 && (
                <motion.div
                  className="w-0.5 h-8 bg-brand-orange/30"
                  animate={{ opacity: [0.3, 0.7, 0.3] }}
                  transition={{ duration: 2, delay: idx * 0.1, repeat: Infinity }}
                />
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function PhysicsCard({ icon: Icon, title, items }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-50px' });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 20 }}
      animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
      transition={{ duration: 0.6 }}
      whileHover={cardHover}
      className="glass rounded-xl p-8 border border-brand-orange/20 hover:border-brand-orange/50 transition-colors group cursor-default"
    >
      <h3 className="text-lg font-display font-bold mb-6 flex items-center gap-3 text-white">
        <Icon className="w-5 h-5 text-brand-orange group-hover:text-brand-orangeLight transition-colors" />
        {title}
      </h3>
      <ul className="space-y-3 font-mono text-sm text-white/60">
        {items.map((item, idx) => (
          <li key={idx} className="leading-relaxed">
            <span className="text-brand-orange">›</span> {item}
          </li>
        ))}
      </ul>
    </motion.div>
  );
}

function ValidationCard({ bike }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-50px' });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, scale: 0.95 }}
      animate={isInView ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.5 }}
      whileHover={cardHover}
      className="glass rounded-xl p-8 border border-brand-orange/20 hover:border-brand-orange/50 transition-all"
    >
      <h3 className="font-display font-bold text-white mb-2">{bike.name}</h3>
      <p className="text-white/60 text-sm mb-8 font-mono">{bike.cc}</p>

      <div className="space-y-6">
        <div className="pb-6 border-b border-ink-1">
          <p className="text-white/40 text-xs mb-2 font-mono uppercase tracking-widest">Target ET</p>
          <p className="text-3xl font-display font-bold text-brand-orange">{bike.target}</p>
        </div>

        <div className="pb-6 border-b border-ink-1">
          <p className="text-white/40 text-xs mb-2 font-mono uppercase tracking-widest">Simulated ET</p>
          <p className="text-3xl font-display font-bold text-white">{bike.sim}</p>
        </div>

        <div>
          <p className="text-xs font-mono uppercase tracking-widest mb-2 text-white/40">Accuracy</p>
          <p className="font-display font-bold text-brand-accent text-lg">{bike.accuracy}</p>
        </div>
      </div>
    </motion.div>
  );
}

export default function HomePage() {
  const { scrollYProgress } = useScroll();
  const heroOpacity = useTransform(scrollYProgress, [0, 0.3], [1, 0]);
  const navBackground = useTransform(scrollYProgress, [0, 0.1], ['rgba(0,0,0,0.5)', 'rgba(0,0,0,0.95)']);

  // Parallax transforms for the Hayabusa silhouette and road
  const motoX = useTransform(scrollYProgress, [0, 0.35], ['-18%', '130%']);
  const motoScale = useTransform(scrollYProgress, [0, 0.35], [1, 1.12]);
  const roadY = useTransform(scrollYProgress, [0, 0.3], ['0%', '-35%']);
  const streakX = useTransform(scrollYProgress, [0, 0.35], ['0%', '-60%']);

  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-ink-0 text-white overflow-x-hidden">
      <style jsx>{`
        @keyframes speedlines {
          0% { transform: translateX(-100%); opacity: 0; }
          10% { opacity: 0.6; }
          90% { opacity: 0.6; }
          100% { transform: translateX(100vw); opacity: 0; }
        }
        @keyframes drift {
          0%, 100% { transform: translate(0, 0); }
          50% { transform: translate(40px, 30px); }
        }
        .speedline {
          animation: speedlines 3s infinite;
        }
        .drift-slow {
          animation: drift 8s ease-in-out infinite;
        }
        .drift-medium {
          animation: drift 10s ease-in-out infinite 2s;
        }
      `}</style>

      {/* Nav */}
      <motion.nav
        style={{ backgroundColor: navBackground }}
        className="fixed top-0 left-0 right-0 h-16 backdrop-blur border-b border-brand-orange/10 z-50"
      >
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-full flex justify-between items-center">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6 }}
            className="flex items-center gap-2"
          >
            <div className="text-xl font-display font-bold tracking-tight">
              <span className="text-gradient-orange">Moto</span>
              <span>Quant</span>
            </div>
            <div className="ml-2 px-2 py-1 rounded text-xs font-mono font-semibold text-brand-accent border border-brand-accent/30 bg-brand-accent/5">
              Pro
            </div>
          </motion.div>

          <div className="hidden md:flex gap-8 items-center text-sm font-mono">
            <a href="/simulator" className="text-white/60 hover:text-white transition-colors duration-300">
              Simulator
            </a>
            <a href="#physics" className="text-white/60 hover:text-white transition-colors duration-300">
              Physics
            </a>
            <a href="#validation" className="text-white/60 hover:text-white transition-colors duration-300">
              Validation
            </a>
            <a href="#cta" className="text-white/60 hover:text-white transition-colors duration-300">
              Get Started
            </a>
          </div>

          <div className="flex items-center gap-2 sm:gap-3">
            <motion.a
              href="/simulator"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="px-3 sm:px-4 py-2 bg-brand-orange hover:bg-brand-orangeLight text-black font-semibold rounded-lg text-xs sm:text-sm font-display transition-colors whitespace-nowrap"
            >
              Launch <span className="hidden sm:inline">Simulator</span>
            </motion.a>

            {/* Mobile hamburger */}
            <button
              type="button"
              onClick={() => setMobileMenuOpen(v => !v)}
              aria-label={mobileMenuOpen ? 'Close menu' : 'Open menu'}
              aria-expanded={mobileMenuOpen}
              aria-controls="mobile-menu"
              className="md:hidden p-2 rounded-lg border border-white/10 text-white/80 hover:text-white hover:border-brand-orange/40 transition-colors"
            >
              {mobileMenuOpen ? <X size={18} /> : <Menu size={18} />}
            </button>
          </div>
        </div>

        {/* Mobile dropdown menu */}
        <AnimatePresence>
          {mobileMenuOpen && (
            <motion.div
              id="mobile-menu"
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
              className="md:hidden absolute top-16 left-0 right-0 bg-black/95 backdrop-blur-xl border-b border-brand-orange/20"
            >
              <div className="max-w-6xl mx-auto px-4 py-4 flex flex-col gap-1 font-mono text-sm">
                {[
                  { href: '/simulator', label: 'Simulator' },
                  { href: '#physics', label: 'Physics' },
                  { href: '#validation', label: 'Validation' },
                  { href: '#cta', label: 'Get Started' },
                ].map(link => (
                  <a
                    key={link.href}
                    href={link.href}
                    onClick={() => setMobileMenuOpen(false)}
                    className="px-4 py-3 rounded-lg text-white/70 hover:text-white hover:bg-white/5 transition-colors"
                  >
                    {link.label}
                  </a>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.nav>

      {/* Hero */}
      <motion.section
        style={{ opacity: heroOpacity }}
        className="relative min-h-screen flex flex-col items-center justify-center pt-16 px-6 overflow-hidden"
      >
        {/* Animated background scene */}
        <div className="absolute inset-0 overflow-hidden">
          {/* Optional video upgrade — drop /public/hero/reel.mp4 and it auto-fades in */}
          <video
            autoPlay
            muted
            loop
            playsInline
            preload="metadata"
            className="absolute inset-0 w-full h-full object-cover opacity-0 data-[loaded=true]:opacity-60 transition-opacity duration-1000"
            onLoadedData={(e) => { e.currentTarget.dataset.loaded = 'true'; }}
            onError={(e) => { e.currentTarget.style.display = 'none'; }}
            aria-hidden="true"
          >
            <source src="/hero/reel.mp4" type="video/mp4" />
          </video>

          {/* Darkening overlay over video */}
          <div className="absolute inset-0 bg-gradient-to-b from-black/40 via-transparent to-black" />

          {/* Radial gradient backdrop */}
          <div
            className="absolute inset-0"
            style={{ background: 'radial-gradient(ellipse at center, rgba(10,10,11,0.6) 0%, rgba(0,0,0,0.9) 70%)' }}
          />

          {/* Grid underlay */}
          <div className="absolute inset-0 bg-grid-fade opacity-20" />

          {/* Road perspective lines — slide upward on scroll */}
          <motion.div
            style={{ y: roadY }}
            className="absolute inset-x-0 bottom-0 h-2/3 pointer-events-none opacity-[0.18]"
            aria-hidden="true"
          >
            <svg viewBox="0 0 1600 600" className="w-full h-full" preserveAspectRatio="none">
              <defs>
                <linearGradient id="roadFade" x1="0" x2="0" y1="0" y2="1">
                  <stop offset="0" stopColor="#FF5E1F" stopOpacity="0" />
                  <stop offset="0.5" stopColor="#FF5E1F" stopOpacity="0.4" />
                  <stop offset="1" stopColor="#FF5E1F" stopOpacity="1" />
                </linearGradient>
              </defs>
              {[...Array(11)].map((_, i) => {
                const x = 800 + (i - 5) * 240;
                return (
                  <line
                    key={i}
                    x1={x}
                    y1="600"
                    x2="800"
                    y2="60"
                    stroke="url(#roadFade)"
                    strokeWidth="1.4"
                  />
                );
              })}
              {/* Horizontal distance marks */}
              {[0.55, 0.72, 0.85, 0.93, 0.97].map((t, i) => {
                const y = 60 + (600 - 60) * t;
                const w = 1600 * (0.1 + t * 0.9);
                return (
                  <line
                    key={`h-${i}`}
                    x1={800 - w / 2}
                    y1={y}
                    x2={800 + w / 2}
                    y2={y}
                    stroke="#FF5E1F"
                    strokeOpacity={0.15 + t * 0.35}
                    strokeWidth="0.8"
                  />
                );
              })}
            </svg>
          </motion.div>

          {/* Headlight focal point — pulsing orange core streaking across the hero */}
          <motion.div
            style={{ x: motoX, scale: motoScale }}
            className="absolute inset-y-0 left-0 w-full pointer-events-none flex items-center"
            aria-hidden="true"
          >
            <div className="relative w-[14%] aspect-square">
              {/* Hot core */}
              <div className="absolute inset-[38%] rounded-full bg-brand-orange blur-[1px] opacity-90" />
              {/* Mid glow */}
              <div className="absolute inset-[22%] rounded-full bg-brand-orange/60 blur-xl" />
              {/* Outer halo */}
              <div className="absolute inset-0 rounded-full bg-brand-orange/25 blur-3xl" />
              {/* Forward motion cone — trailing light */}
              <div
                className="absolute top-1/2 -translate-y-1/2 left-[55%] h-[3px] w-[420px] bg-gradient-to-r from-brand-orange via-brand-orange/60 to-transparent blur-[1px]"
              />
              <div
                className="absolute top-1/2 -translate-y-1/2 left-[55%] h-[1px] w-[520px] bg-gradient-to-r from-brand-accent/80 via-brand-orange/40 to-transparent"
              />
            </div>
          </motion.div>

          {/* Scroll-reactive neon speed streaks — varied widths & opacities for depth */}
          <motion.div style={{ x: streakX }} className="absolute inset-0 pointer-events-none" aria-hidden="true">
            {[
              { top: 14, width: 62, opacity: 0.55, duration: 2.2, delay: 0.0 },
              { top: 22, width: 78, opacity: 0.35, duration: 2.8, delay: 0.3 },
              { top: 34, width: 44, opacity: 0.7,  duration: 1.9, delay: 0.1 },
              { top: 46, width: 88, opacity: 0.4,  duration: 3.1, delay: 0.5 },
              { top: 58, width: 56, opacity: 0.6,  duration: 2.4, delay: 0.2 },
              { top: 68, width: 72, opacity: 0.45, duration: 2.7, delay: 0.4 },
              { top: 78, width: 50, opacity: 0.55, duration: 2.1, delay: 0.15 },
              { top: 88, width: 66, opacity: 0.35, duration: 2.9, delay: 0.35 },
            ].map((s, i) => (
              <div
                key={i}
                className="absolute h-px bg-gradient-to-r from-transparent via-brand-orange to-transparent speedline"
                style={{
                  top: `${s.top}%`,
                  left: `${Math.random() * 20}%`,
                  width: `${s.width}%`,
                  opacity: s.opacity,
                  animationDuration: `${s.duration}s`,
                  animationDelay: `${s.delay}s`,
                }}
              />
            ))}
          </motion.div>

          {/* Floating telemetry callouts — physics flavor that matches the tagline */}
          <div className="absolute inset-0 pointer-events-none hidden md:block" aria-hidden="true">
            <div className="absolute top-[18%] left-[8%] font-mono text-[10px] text-brand-orange/40 tracking-wider">
              <div>μ = 0.92</div>
              <div className="text-white/30">// peak grip</div>
            </div>
            <div className="absolute top-[72%] right-[10%] font-mono text-[10px] text-brand-orange/40 tracking-wider text-right">
              <div>Cd·A = 0.34</div>
              <div className="text-white/30">// tucked</div>
            </div>
            <div className="absolute top-[30%] right-[14%] font-mono text-[10px] text-brand-accent/60 tracking-wider">
              <div>ET → 9.97s</div>
            </div>
            <div className="absolute top-[60%] left-[12%] font-mono text-[10px] text-white/35 tracking-wider">
              <div>v_trap = 239.8 km/h</div>
            </div>
          </div>

          {/* Animated glow orbs */}
          <motion.div
            className="absolute -top-40 -right-40 w-80 h-80 rounded-full bg-brand-orange/20 blur-3xl drift-slow"
            aria-hidden="true"
          />
          <motion.div
            className="absolute -bottom-40 -left-40 w-80 h-80 rounded-full bg-brand-orangeDeep/10 blur-3xl drift-medium"
            aria-hidden="true"
          />
        </div>

        {/* Content */}
        <div className="relative z-10 max-w-4xl text-center">
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="mb-8 inline-block"
          >
            <div className="px-4 py-2 rounded-full border border-brand-orange/50 bg-brand-orange/10 backdrop-blur-sm">
              <p className="text-xs font-mono text-brand-orange uppercase tracking-widest">
                v1.0 · Open Source · Built in India
              </p>
            </div>
          </motion.div>

          {/* Main heading */}
          <motion.h1
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2, ease: 'easeOut' }}
            className="font-display font-bold text-5xl md:text-7xl lg:text-8xl mb-6 tracking-tighter leading-tight text-gradient-orange"
          >
            The Physics of Faster
          </motion.h1>

          {/* Subheading */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="text-lg md:text-xl text-white/80 mb-6 max-w-2xl mx-auto leading-relaxed"
          >
            A first-principles physics engine predicting quarter-mile ET within{' '}
            <span className="text-brand-accent font-semibold">±0.07s</span>. Validated on real Dragy GPS telemetry at
            Aamby Valley, MMRT, and beyond.
          </motion.p>

          {/* Secondary text */}
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.5 }}
            className="text-sm text-white/60 font-mono uppercase tracking-widest mb-12"
          >
            From Pune to the world
          </motion.p>

          {/* CTAs */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.6 }}
            className="flex flex-col sm:flex-row gap-4 justify-center"
          >
            <motion.a
              href="/simulator"
              whileHover={{ scale: 1.05, boxShadow: '0 0 30px rgba(255, 94, 31, 0.4)' }}
              whileTap={{ scale: 0.95 }}
              className="px-8 py-4 bg-brand-orange text-black font-display font-bold rounded-lg transition-all glow-orange"
            >
              Run a Simulation
            </motion.a>
            <motion.a
              href="https://github.com/da25mem5s02-debug/MotoQuant_v1"
              target="_blank"
              rel="noopener noreferrer"
              whileHover={{ scale: 1.05, borderColor: 'rgb(255, 94, 31)' }}
              whileTap={{ scale: 0.95 }}
              className="px-8 py-4 border-2 border-brand-orange/40 hover:border-brand-orange text-brand-orange font-display font-bold rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              <Github size={20} /> View on GitHub
            </motion.a>
          </motion.div>
        </div>

        {/* Scroll indicator */}
        <ScrollIndicator />
      </motion.section>

      {/* Stats strip */}
      <StatsStrip />

      {/* Simulator section */}
      <section
        id="simulator"
        className="relative py-24 md:py-32 px-6 border-t border-brand-orange/10"
      >
        <div className="max-w-6xl mx-auto">
          <RevealSection>
            <div className="text-center mb-16">
              <h2 className="font-display font-bold text-4xl md:text-5xl mb-4 text-white">
                Run It Yourself
              </h2>
              <p className="text-white/80 text-lg max-w-2xl mx-auto">
                Real physics, running live. Pick a bike, adjust your setup, get your ET in under a second.
              </p>
            </div>
          </RevealSection>

          {/* Ambient glow effect */}
          <div className="absolute -left-40 top-1/2 w-80 h-80 rounded-full bg-brand-orange/10 blur-3xl pointer-events-none" />
          <div className="absolute -right-40 top-1/2 w-80 h-80 rounded-full bg-brand-orangeDeep/10 blur-3xl pointer-events-none" />

          <div className="relative z-10">
            <SimulatorWidget />
          </div>
        </div>
      </section>

      {/* Physics section */}
      <section id="physics" className="py-24 md:py-32 px-6 border-t border-brand-orange/10 bg-ink-1/50">
        <div className="max-w-6xl mx-auto">
          <RevealSection>
            <div className="mb-16">
              <h2 className="font-display font-bold text-4xl md:text-5xl mb-4">
                15 Physics Sub-Models
              </h2>
              <p className="text-white/80 text-lg">
                Every coefficient is traceable to a real measurement. No curve-fitting against times — pure physics.
              </p>
            </div>
          </RevealSection>

          <motion.div
            className="grid md:grid-cols-2 gap-6"
            variants={containerVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-100px' }}
          >
            <PhysicsCard
              icon={Zap}
              title="Engine & Drivetrain"
              items={[
                '3D engine torque curves (Willans friction model)',
                'Forced induction — turbo, supercharger, nitrous',
                'Gear shifting and clutch engagement dynamics',
                'Chain drive losses and sprocket ratios',
              ]}
            />
            <PhysicsCard
              icon={Gauge}
              title="Grip & Aerodynamics"
              items={[
                'Pacejka tire model with thermal evolution',
                'Drag coefficient and frontal area per-bike',
                'Weight transfer and traction limits',
                'Rider CoG shift and wheelie physics',
              ]}
            />
            <PhysicsCard
              icon={Wind}
              title="Environment & Setup"
              items={[
                'Air density, altitude and temperature correction',
                'Rolling resistance and surface grip multipliers',
                'Staging, reaction time, two-step launch control',
                'Wind and live weather effects',
              ]}
            />
            <PhysicsCard
              icon={BarChart3}
              title="Numerics & Validation"
              items={[
                'RK4 fixed-step integrator at 1ms timestep',
                'Adaptive step-size solver with error bounds',
                '583+ regression tests (zero failures)',
                'Validated against real GPS and ECU telemetry',
              ]}
            />
          </motion.div>
        </div>
      </section>

      {/* Validation section */}
      <section id="validation" className="py-24 md:py-32 px-6 border-t border-brand-orange/10">
        <div className="max-w-6xl mx-auto">
          <RevealSection>
            <div className="mb-16">
              <h2 className="font-display font-bold text-4xl md:text-5xl mb-4">
                Validated on Real Telemetry
              </h2>
              <p className="text-white/80 text-lg">
                We don't just predict — we measure. Here's how the engine stacks up against real quarter-mile runs.
              </p>
            </div>
          </RevealSection>

          <div className="grid md:grid-cols-3 gap-6 mb-12">
            <ValidationCard
              bike={{
                name: 'Suzuki GSX-R 1000 K5',
                cc: '999cc Superbike',
                target: '9.97s',
                sim: '10.04s',
                accuracy: '±0.07s (0.7%)',
              }}
            />
            <ValidationCard
              bike={{
                name: 'Yamaha YZF-R1 4C8',
                cc: '998cc Superbike',
                target: '10.2–10.4s',
                sim: '~10.3s',
                accuracy: 'In-range ✓',
              }}
            />
            <ValidationCard
              bike={{
                name: 'Suzuki Hayabusa Gen1',
                cc: '1299cc Hyperbike',
                target: '10.1–10.7s',
                sim: '10.477s',
                accuracy: 'Validated ✓',
              }}
            />
          </div>

          <RevealSection className="text-center text-sm text-white/60 font-mono">
            <p>
              Plug in your own Dragy GPS logs to auto-calibrate for your bike, rider style, and venue.{' '}
              <span className="text-brand-accent">Zero guesswork.</span>
            </p>
          </RevealSection>
        </div>
      </section>

      {/* Who uses this */}
      <section className="py-24 md:py-32 px-6 border-t border-brand-orange/10 bg-ink-1/50">
        <div className="max-w-6xl mx-auto">
          <RevealSection>
            <h2 className="font-display font-bold text-4xl md:text-5xl mb-16 text-center">
              Built For Champions
            </h2>
          </RevealSection>

          <div className="grid md:grid-cols-2 gap-8">
            <RevealSection>
              <div className="glass rounded-xl p-6 sm:p-10 border border-brand-orange/20 h-full">
                <h3 className="font-display font-bold text-2xl mb-4 text-white">Racers</h3>
                <p className="text-white/80 mb-6 leading-relaxed">
                  ET prediction before you hit the strip. Simulate launch strategies, gear shifts, and setup changes.
                  Share your data with crew chiefs and track results in the leaderboard.
                </p>
                <ul className="space-y-2 text-sm font-mono text-white/60">
                  <li>
                    <span className="text-brand-orange">›</span> Pre-event ET prediction
                  </li>
                  <li>
                    <span className="text-brand-orange">›</span> Setup optimisation
                  </li>
                  <li>
                    <span className="text-brand-orange">›</span> Performance leaderboard
                  </li>
                </ul>
              </div>
            </RevealSection>

            <RevealSection>
              <div className="glass rounded-xl p-6 sm:p-10 border border-brand-orange/20 h-full">
                <h3 className="font-display font-bold text-2xl mb-4 text-white">Tuning Shops</h3>
                <p className="text-white/80 mb-6 leading-relaxed">
                  ROI analysis for every part you sell. Import dyno curves, calibrate against customer Dragy runs,
                  and build data-driven recommendations. Impress clients with physics-backed estimates.
                </p>
                <ul className="space-y-2 text-sm font-mono text-white/60">
                  <li>
                    <span className="text-brand-orange">›</span> Parts ROI calculator
                  </li>
                  <li>
                    <span className="text-brand-orange">›</span> Client calibration
                  </li>
                  <li>
                    <span className="text-brand-orange">›</span> Build recommendations
                  </li>
                </ul>
              </div>
            </RevealSection>
          </div>
        </div>
      </section>

      {/* CTA section */}
      <section id="cta" className="py-24 md:py-32 px-6 border-t border-brand-orange/10">
        <div className="max-w-4xl mx-auto">
          <RevealSection>
            <div className="glass rounded-2xl p-6 sm:p-10 md:p-12 border border-brand-orange/30 bg-gradient-to-br from-brand-orange/10 to-brand-orangeDeep/5">
              <h2 className="font-display font-bold text-3xl sm:text-4xl md:text-5xl mb-6 text-center">
                Start Predicting Your Quarter Mile
              </h2>
              <p className="text-white/80 text-lg text-center mb-12 max-w-2xl mx-auto">
                Choose your path: CLI for deep analysis, REST API for integration, or the web simulator for quick runs.
              </p>

              <div className="grid md:grid-cols-2 gap-6 mb-10">
                <div className="bg-ink-0/60 rounded-xl p-6 sm:p-8 border border-brand-orange/20">
                  <h3 className="font-display font-bold text-xl mb-3 text-white">CLI & Python API</h3>
                  <p className="text-white/60 text-sm mb-6">
                    Full simulation from your terminal. Import Dragy GPS, dyno curves, and Woolich ECU logs for
                    calibration. Analyze parts ROI, optimize builds, and generate detailed reports.
                  </p>
                  <code className="block text-xs text-brand-accent bg-ink-1 px-4 py-3 rounded font-mono border border-brand-orange/20">
                    pip install motoquant
                  </code>
                </div>

                <div className="bg-ink-0/60 rounded-xl p-6 sm:p-8 border border-brand-orange/20">
                  <h3 className="font-display font-bold text-xl mb-3 text-white">REST API</h3>
                  <p className="text-white/60 text-sm mb-6">
                    POST /api/simulate with a bike config and get full time-series v(t), RPM, gear, and ET. Perfect
                    for building your own UI or integrating into tuning shop systems.
                  </p>
                  <code className="block text-xs text-brand-accent bg-ink-1 px-4 py-3 rounded font-mono border border-brand-orange/20">
                    api.motoquant.in/docs
                  </code>
                </div>
              </div>

              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <motion.a
                  href="https://github.com/da25mem5s02-debug/MotoQuant_v1"
                  target="_blank"
                  rel="noopener noreferrer"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="inline-flex items-center justify-center gap-2 px-8 py-3 bg-brand-orange text-black font-display font-bold rounded-lg transition-all glow-orange"
                >
                  <Github size={20} /> View on GitHub
                </motion.a>
                <motion.a
                  href="https://github.com/da25mem5s02-debug/MotoQuant_v1#readme"
                  target="_blank"
                  rel="noopener noreferrer"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="inline-flex items-center justify-center gap-2 px-8 py-3 border-2 border-brand-orange text-brand-orange font-display font-bold rounded-lg transition-colors"
                >
                  Quick Start Docs
                </motion.a>
              </div>
            </div>
          </RevealSection>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-brand-orange/10 py-12 px-6 text-center text-white/60 text-sm font-mono">
        <div className="max-w-6xl mx-auto">
          <div className="mb-6">
            <p className="mb-2">
              Built in India for the Indian drag racing community. Validated physics, open source, made for the strip.
            </p>
            <p>
              motoquant.in{' '}
              <span className="text-brand-orange/50">·</span>{' '}
              <a href="https://github.com/da25mem5s02-debug/MotoQuant_v1" className="text-brand-orange hover:text-brand-orangeLight transition-colors">
                GitHub
              </a>{' '}
              <span className="text-brand-orange/50">·</span> Not affiliated with any manufacturer
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
