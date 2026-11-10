import Link from 'next/link';
import { ChevronRight } from 'lucide-react';
import SiteNav from '../../components/SiteNav';
import SiteFooter from '../../components/SiteFooter';
import PageHeader from '../../components/PageHeader';

function FounderCard({ initial, name, role, email, children }) {
  return (
    <div className="card h-full p-6 md:p-8">
      <div className="flex items-start gap-5 mb-5">
        <div className="w-14 h-14 rounded-full bg-asphalt-3 border border-white/10 flex items-center justify-center shrink-0">
          <span className="text-white font-display font-bold text-xl">{initial}</span>
        </div>
        <div>
          <div className="font-display font-semibold text-lg md:text-xl text-white mb-0.5">{name}</div>
          <div className="text-sm text-white/60">{role}</div>
        </div>
      </div>
      <div className="space-y-3 text-white/75 text-base leading-relaxed">{children}</div>
      <a
        href={`mailto:${email}`}
        className="inline-flex items-center gap-1.5 mt-5 text-sm text-white/70 font-mono hover:text-white transition-colors"
      >
        {email} <ChevronRight size={14} aria-hidden="true" />
      </a>
    </div>
  );
}

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-asphalt-0 text-white">
      <SiteNav />

      <PageHeader
        maxWidth="max-w-4xl"
        title="About MotoQuant"
        lede="A free, open-source quarter-mile simulator for motorcycles, built in Pune for the Indian drag strip."
      />

      <main id="main" className="px-4 pb-20 sm:px-6">
        <div className="mx-auto max-w-4xl">
          <section className="mb-14 max-w-2xl space-y-4 text-base leading-relaxed text-white/75">
            <h2 className="font-display text-xl font-semibold text-white md:text-2xl">Why we built it</h2>
            <p>
              It started with a question at a drag strip outside Pune: &ldquo;How do I know which part will actually make my
              bike quicker?&rdquo; The usual answers were guesswork, comments under YouTube videos, or an expensive test day.
            </p>
            <p>
              Indian drag racing is growing fast, at Aamby Valley, MMRT, BIC, Kari and Hyderabad, but the tools were built for
              other bikes and other weather. A calculator tuned for Santa Pod at 5 °C says very little about Aamby Valley at
              35 °C. So we built one for here: 534 bikes, 546 parts with prices in rupees, and 20 venues with real seasonal
              weather.
            </p>
            <h2 className="pt-4 font-display text-xl font-semibold text-white md:text-2xl">How it works, in one paragraph</h2>
            <p>
              We did not fit a curve to old results. MotoQuant simulates the physics of the run: engine power, gearing, tyre
              grip, drag and weight transfer. When it is wrong we can find out why and fix the cause, and when you add a part
              its effect flows through the whole bike. We check it against 250 published timeslips, and the{' '}
              <Link href="/validation" className="text-accent underline-offset-2 hover:underline">accuracy page</Link> shows every
              result, including where it is weakest.
            </p>
          </section>

          <section className="mb-14 rounded-2xl border border-accent/25 bg-accent/5 p-6 md:p-8">
            <h2 className="mb-2 font-display text-xl font-semibold text-white md:text-2xl">Open source and community-driven</h2>
            <p className="mb-4 max-w-2xl text-base leading-relaxed text-white/80">
              MotoQuant is free and Apache-2.0 licensed, and the public site has no limits. Add a bike that is missing, correct a
              spec, send us a timeslip or improve the physics.
            </p>
            <div className="flex flex-wrap gap-3">
              <a href="https://github.com/toto171/MotoQuant.in" target="_blank" rel="noopener noreferrer" className="btn-primary">
                View on GitHub
              </a>
              <Link href="/contact" className="btn-ghost">Contact us</Link>
            </div>
          </section>

          <section className="mb-14">
            <h2 className="mb-2 font-display text-xl font-semibold text-white md:text-2xl">The team</h2>
            <p className="mb-8 text-base text-white/70">Engineers first, racers second. We are building a tool we would use ourselves.</p>
<div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
                          <FounderCard initial="A" name="Arya Desai" role="Co-founder & Lead Engineer · Pune, India" email="motoquant@gmail.com">
                <p>
                  Arya started MotoQuant and leads it. He has an M.Tech from NIT Warangal and a B.Tech from Manipal (Automotive System Design). He owns the physics: the vehicle-dynamics model, its calibration against real Dragy traces, and where the engine goes next.
                </p>
                <p>
                  At NIT-W he used CFD to study engine combustion, researched magnetorheological suspension and filed a design patent. At Power Solutions Pune he tuned 25+ performance cars by hand (Mercedes-AMG, BMW, Audi, Jaguar Land Rover). He is certified in ECU tuning.
                </p>
              </FounderCard>
            
                          <FounderCard initial="R" name="Ritwik Singh" role="Co-founder & Advisor · Bengaluru, India" email="motoquant@gmail.com">
                <p>
                  Ritwik is an automobile and AI engineer. He shaped MotoQuant&apos;s early software and machine learning, from the simulation scaffolding to the first surrogate models and the ROI ranker. He is now a co-founder and advisor and stays close to the technical direction.
                </p>
                <p>
                  Day to day he&apos;s building Dhisetu, an AI-assisted indie game studio in Bengaluru. He&apos;s a hardcore indie gamer, and his bet is that the next studios will be solo creators with AI co-pilots rather than big teams.
                </p>
              </FounderCard>
            
                          <FounderCard initial="S" name="Sahil Shetye" role="Co-founder & CMO · Manipal, India" email="motoquant@gmail.com">
                <p>
                  Sahil is an electrical engineer finishing his B.Tech in EEE at Manipal, and our pitchman. He runs growth and marketing for MotoQuant and the electronics half of the hardware roadmap: PCB design, EV powertrain and battery tech, low-level C.
                </p>
                <p>
                  He brings communication skills and real market experience. His job is to turn a physics engine into something racers and tuning shops hear about and want to use.
                </p>
                <p className="border-l-2 border-white/15 pl-4 italic text-white/70">
                  &ldquo;In my third year, a major bike accident paused my degree. While recovering, I refused to sit idle: I built a social-media audience and finished multiple industry-standard certifications. I don&apos;t just study engineering; I build, optimize, and execute under pressure.&rdquo;
                </p>
              </FounderCard>
                      </div>
          </section>

          <section className="text-base text-white/75">
            <h2 className="mb-2 font-display text-xl font-semibold text-white md:text-2xl">Get in touch</h2>
            <p>
              Questions, bug reports, or a bike we should add? See the{' '}
              <Link href="/contact" className="text-accent underline-offset-2 hover:underline">contact page</Link>.
            </p>
          </section>
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}
