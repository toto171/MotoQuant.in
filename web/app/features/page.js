import Link from 'next/link';
import {
  Gauge, Wrench, Flag, GitCompareArrows, CloudSun, Upload, MessageSquare,
  Share2, Code2, Github, ArrowRight,
} from 'lucide-react';
import SiteNav from '../../components/SiteNav';
import SiteFooter from '../../components/SiteFooter';
import PageHeader from '../../components/PageHeader';
import Term from '../../components/Term';

const REPO = 'https://github.com/toto171/MotoQuant.in';

const THINGS = [
  {
    icon: Gauge,
    q: 'How fast is my bike?',
    body: (
      <>
        Pick any of the 534 bikes and see its <Term k="et">quarter-mile time</Term>, its{' '}
        <Term k="trap">finish-line speed</Term> and how it launches. Set your weight and where you are racing and the
        answer changes with them.
      </>
    ),
    href: '/simulator',
    cta: 'Open the simulator',
  },
  {
    icon: Wrench,
    q: 'What should I buy first?',
    body: (
      <>
        Tell us your bike and your budget. We test every part that fits it, from a catalog of 546 parts, and show the
        combination that makes it quickest, with the <Term k="cost_per_tenth">cost per tenth of a second</Term> for each one.
      </>
    ),
    href: '/optimize',
    cta: 'Find the best parts',
  },
  {
    icon: Flag,
    q: 'How should I set up for race day?',
    body: (
      <>
        Get the <Term k="gearing">gearing</Term>, <Term k="launch_rpm">launch RPM</Term> and tyre pressure that suit
        the air on the day, and how much time each change is worth.
      </>
    ),
    href: '/autotune',
    cta: 'Get my setup',
  },
  {
    icon: GitCompareArrows,
    q: 'Which of two bikes is quicker?',
    body: 'Put two bikes side by side at the same strip and weight. See the time gap, the speed gap and where on the track one pulls ahead.',
    href: '/simulator',
    cta: 'Compare in the simulator',
  },
  {
    icon: CloudSun,
    q: 'What will the weather do to my time?',
    body: (
      <>
        Choose one of 20 venues, or any place, and the result adjusts for altitude, temperature and humidity (
        <Term k="da">air and altitude</Term>). Hot, thin air costs real tenths.
      </>
    ),
    href: '/simulator',
    cta: 'Try a location',
  },
  {
    icon: Upload,
    q: 'How do my real runs compare?',
    body: (
      <>
        Upload a <Term k="dragy">Dragy</Term> log or a <Term k="dyno">dyno</Term> sheet and see your real run lined up
        against the simulation, split by split.
      </>
    ),
    href: '/simulator',
    cta: 'Open the simulator',
  },
  {
    icon: MessageSquare,
    q: 'Can I just ask?',
    body: 'Yes. Type a question in plain English, such as “How fast is a Duke 390 at Aamby Valley?”, and the assistant runs the simulation for you.',
    href: '/simulator',
    cta: 'Ask a question',
  },
  {
    icon: Share2,
    q: 'Can I save and share a run?',
    body: 'Yes, without an account. Save keeps the run in your browser, and its timeslip link opens the same bike, upgrades and conditions for anyone you send it to. The slip re-runs the physics when it opens, so nobody can type a time in.',
    href: '/runs',
    cta: 'Your runs',
  },
  {
    icon: Code2,
    q: 'Can I use it from my own code?',
    body: 'The same engine is a Python package, a command-line tool, an HTTP API and an MCP server, so an AI assistant can run simulations too.',
    href: '/docs/getting-started',
    cta: 'Read the developer guide',
  },
];

export default function FeaturesPage() {
  return (
    <div className="min-h-screen bg-asphalt-0 text-white">
      <SiteNav />

      <PageHeader
        maxWidth="max-w-4xl"
        title="What you can do with MotoQuant"
        lede="Everything here is free, needs no account, and runs on the same physics engine."
      />

      <main id="main" className="px-4 pb-20 sm:px-6">
        <div className="mx-auto max-w-4xl">
          <ul className="grid gap-4 md:grid-cols-2">
            {THINGS.map(({ icon: Icon, q, body, href, cta }) => (
              <li key={q} className="card card-pad flex flex-col">
                <span className="mb-3 inline-flex h-10 w-10 items-center justify-center rounded-lg border border-white/10 bg-asphalt-3 text-accent">
                  <Icon size={20} aria-hidden="true" />
                </span>
                <h2 className="mb-2 font-display text-lg font-semibold text-white">{q}</h2>
                <p className="mb-4 flex-1 text-base leading-relaxed text-white/75">{body}</p>
                <Link href={href} className="inline-flex min-h-[44px] items-center gap-1.5 text-sm font-medium text-accent hover:text-accent-bright">
                  {cta} <ArrowRight size={14} aria-hidden="true" />
                </Link>
              </li>
            ))}
          </ul>

          <section className="mt-12 grid gap-4 md:grid-cols-2">
            <div className="card card-pad">
              <h2 className="mb-2 font-display text-lg font-semibold text-white">Can I trust the numbers?</h2>
              <p className="mb-4 text-base leading-relaxed text-white/75">
                We check the simulator against 250 published timeslips and show every result, including where it is
                weakest.
              </p>
              <Link href="/validation" className="inline-flex min-h-[44px] items-center gap-1.5 text-sm font-medium text-accent hover:text-accent-bright">
                See the accuracy <ArrowRight size={14} aria-hidden="true" />
              </Link>
            </div>
            <div className="card card-pad">
              <h2 className="mb-2 flex items-center gap-2 font-display text-lg font-semibold text-white">
                <Github size={18} aria-hidden="true" /> Open source, and yours to improve
              </h2>
              <p className="mb-4 text-base leading-relaxed text-white/75">
                MotoQuant is Apache-2.0 licensed and built in the open. You can add a bike, fix a spec, send us a timeslip or read
                the code.
              </p>
              <a href={REPO} target="_blank" rel="noopener noreferrer" className="inline-flex min-h-[44px] items-center gap-1.5 text-sm font-medium text-accent hover:text-accent-bright">
                Contribute on GitHub <ArrowRight size={14} aria-hidden="true" />
              </a>
            </div>
          </section>
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}
