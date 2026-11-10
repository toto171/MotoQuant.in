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
              spec, send us a timeslip or improve the physics. Every bit makes it more accurate for everyone.
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
            <p className="mb-8 text-base text-white/70">Engineers first, racers second, building a tool we would use ourselves.</p>
<div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
                          <FounderCard initial="A" name="Arya Desai" role="Co-founder & Lead Engineer · Pune, India" email="motoquant@gmail.com">
                <p>
                  The engineer who started MotoQuant and leads it — M.Tech from NIT Warangal, B.Tech from Manipal (Automotive System Design). He owns the physics: the vehicle-dynamics model, the calibration against real Dragy traces, and where the engine goes next.
                </p>
                <p>
                  Depth from both sides of the workshop door — CFD engine-combustion and magnetorheological-suspension research at NIT-W (plus a filed design patent) on one side; 25+ performance cars tuned by hand at Power Solutions Pune — Mercedes-AMG, BMW, Audi, Jaguar Land Rover — on the other. ECU-tuning certified.
                </p>
              </FounderCard>
            
                          <FounderCard initial="R" name="Ritwik Singh" role="Co-founder & Advisor · Bengaluru, India" email="dhisetu@gmail.com">
                <p>
                  Automobile-and-AI engineer — the software and machine-learning instinct behind MotoQuant&apos;s early architecture, from the simulation scaffolding to the first surrogate models and ROI ranker. Now a co-founder and advisor, still close to the technical direction.
                </p>
                <p>
                  Day to day he&apos;s building Dhisetu, an AI-assisted indie game studio in Bengaluru — a hardcore indie gamer, which is where the instinct comes from. His bet: the next studios won&apos;t be big teams but solo creators with AI co-pilots. Same instinct here.
                </p>
              </FounderCard>
            
                          <FounderCard initial="S" name="Sahil Shetye" role="Co-founder & CMO · Manipal, India" email="motoquant@gmail.com">
                <p>
                  Electrical engineer and our pitchman — finishing his B.Tech in EEE at Manipal. The growth-and-market side of MotoQuant, and the electronics half of the hardware roadmap: PCB design, EV powertrain and battery tech, low-level C.
                </p>
                <p>
                  Communication and market knowledge are the levers he owns, plus real market experience — turning a physics engine into something racers and tuning shops actually hear about, and want to implement.
                </p>
                <p className="border-l-2 border-white/15 pl-4 italic text-white/70">
                  &ldquo;In my third year, a major bike accident paused my degree. While recovering, I refused to sit idle — I built a social-media audience and finished multiple industry-standard certifications. I don&apos;t just study engineering; I build, optimize, and execute under pressure.&rdquo;
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
