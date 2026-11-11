import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import CodeComment from '../../../components/CodeComment';
import StructuredData, { articleSchema, OG_IMAGE } from '../../StructuredData';

const REPO = 'https://github.com/toto171/MotoQuant.in';
const SLUG = 'motoquant-2-0-is-open-source';

export const metadata = {
  title: { absolute: 'MotoQuant 2.0 is open source, including where it is wrong' },
  description:
    'MotoQuant 2.0 is free and open source under Apache-2.0, with no accounts and no paid plans. What it gets right, where it is still wrong, and how a timeslip from you makes it better.',
  keywords: [
    'motoquant open source',
    'open source motorcycle simulator',
    'motorcycle quarter mile simulator free',
    'motoquant 2.0',
  ],
  alternates: { canonical: `https://motoquant.in/blog/${SLUG}` },
  openGraph: {
    title: 'MotoQuant 2.0 is open source, including where it is wrong',
    description: 'Free, Apache-2.0, no accounts. What it gets right, where it is wrong, and how to help.',
    url: `https://motoquant.in/blog/${SLUG}`,
    type: 'article',
    publishedTime: '2026-11-10T00:00:00Z',
    images: [OG_IMAGE],
  },
};

const CONTENT = [
  {
    type: 'lead',
    text: 'MotoQuant 2.0 is out, and the whole thing is now free and open source under the Apache License 2.0: the physics engine, the catalog of 534 bikes, the website and the test suite. There are no accounts and no paid plans. Before you trust a number from it, you should know where it is wrong, so most of this post is about that.',
  },
  { type: 'h2', text: 'Where it is good' },
  {
    type: 'p',
    text: 'We check every catalog bike against 250 published quarter-mile tests from Cycle World, Sport Rider, MCN, MotoStatz and others, which gives 263 bike-to-test matches. Weighted by how trustworthy each source is, the simulated time is off by 0.25 s on average, and it is not systematically quick or slow (the average bias is +0.02 s).',
  },
  {
    type: 'p',
    text: 'Litre and 600 cc sport bikes do best, because most of their benchmarks come from instrumented magazine tests. The 600–1000 cc fours and triples are off by 0.15 s on average over 76 matches, and the ten closest matches against measured tests are, on average, 0.006 s from the published time.',
  },
  { type: 'h2', text: 'Where it is wrong' },
  {
    type: 'p',
    text: 'Small bikes, singles and two-strokes are the weak spot. Entry 200–300 cc bikes come out about 0.27 s slow on average, 300–500 cc singles about 0.27 s quick, and two-strokes about 0.26 s slow. Part of that is the benchmarks: few instrumented timeslips exist for these bikes, so their numbers lean on estimates with a declared uncertainty of ±0.7 s. Part of it is the model.',
  },
  {
    type: 'p',
    text: 'The clearest model problem is gearing. Many small bikes fall back to a primary gear ratio meant for a litre bike, which gears them too tall. In November we sourced the real gearing for 53 bikes and applied it. The weighted error got worse, from 0.2495 s to 0.2525 s, because the current tuning had been compensating for the wrong gearing. So we did not ship it. The sourced data and the full write-up are in the repository, and fixing it properly means re-tuning the small-bike launch at the same time.',
  },
  {
    type: 'p',
    text: 'Even the reference bikes are not perfect matches. The Suzuki GSX-R1000 K5 simulates at 10.04 s against 9.97 s in Cycle World, the Yamaha YZF-R1 at 10.11 s against 10.30 s in Sport Rider, and the Hayabusa at 10.11 s against 10.40 s in Cycle World. Those three are pinned in the test suite so that no change can move them by accident; they are a fixed point for the code, not a claim that the model is exact.',
  },
  {
    type: 'callout',
    text: 'Every result on the site states the conditions it was computed for: the place, its altitude, the air and the track surface. If you compare a simulated time with a timeslip, compare like with like.',
  },
  { type: 'h2', text: 'What changed in 2.0' },
  {
    type: 'p',
    text: 'MotoQuant was once planned as a paid product. No payment was ever taken, and that plan is gone: there is no pricing page, no sign-in and no licence key. Runs you save stay in your own browser, and a timeslip link lets you share one. The link re-runs the physics when it opens, so it always shows the engine’s current answer for that setup and those conditions.',
  },
  {
    type: 'p',
    text: 'Underneath, the physics now has a Rust core that gives the same answer as the Python reference to the last digit and runs about 40 times faster. The accuracy pass in this release times each run from the 1-ft rollout beam, the way a drag strip does. It also treats the rider and bike as one centre of mass when the front wheel lifts.',
  },
  { type: 'h2', text: 'How you can make it better' },
  {
    type: 'p',
    text: 'The most useful thing you can send is a real run. If you have a Dragy, a VBOX or a timeslip from a drag strip, especially for a bike under 400 cc, send it with the "Submit a timeslip" form on GitHub. A maintainer checks each one before it joins the benchmark set, and every accepted run tightens the numbers for everyone who rides that kind of bike.',
  },
  {
    type: 'p',
    text: 'If your bike is missing, suggest it from the bike list. If you have a dyno sheet or an ECU log, there is a form for that too. And if you write code, the repository has issues labelled for first-time contributors, a short guide to the rules, and a test suite that tells you within minutes whether a change broke the physics.',
  },
];

function Prose({ content }) {
  return (
    <div className="max-w-2xl mx-auto">
      {content.map((block, i) => {
        if (block.type === 'h2') {
          return (
            <h2 key={i} className="font-display font-bold text-2xl md:text-3xl text-white mt-12 mb-4 tracking-tight">{block.text}</h2>
          );
        }
        if (block.type === 'lead') {
          return <p key={i} className="text-lg text-white/80 leading-relaxed mb-8 font-light">{block.text}</p>;
        }
        if (block.type === 'callout') {
          return (
            <div key={i} className="my-8 px-5 py-4 rounded-xl border-l-4 border-brand-orange bg-brand-orange/5">
              <p className="text-sm text-white/80 leading-relaxed">{block.text}</p>
            </div>
          );
        }
        return <p key={i} className="text-white/75 text-base leading-relaxed mb-5">{block.text}</p>;
      })}
    </div>
  );
}

const LINKS = [
  { href: `${REPO}/issues/new?template=submit-timeslip.yml`, label: 'Submit a timeslip' },
  { href: `${REPO}/issues/new?template=suggest-bike.yml`, label: 'Suggest a bike' },
  { href: `${REPO}/blob/main/reports/gearing_experiment_2026_11_10.md`, label: 'Read the gearing experiment' },
  { href: REPO, label: 'Read the code' },
];

export default function PostPage() {
  return (
    <div className="min-h-screen bg-black text-white">
      <StructuredData
        data={articleSchema({
          title: 'MotoQuant 2.0 is open source, including where it is wrong',
          description: 'MotoQuant 2.0 is free and open source under Apache-2.0, with no accounts and no paid plans. What it gets right, where it is still wrong, and how a timeslip from you makes it better.',
          slug: 'motoquant-2-0-is-open-source',
          datePublished: '2026-11-10',
        })}
      />
      <SiteNav />

      <article id="main" className="pt-32 pb-24 px-6">
        <div className="max-w-2xl mx-auto">
          <div className="flex flex-wrap gap-2 mb-6">
            {['release', 'open source', 'accuracy'].map((t) => (
              <span key={t} className="px-2.5 py-1 rounded-full bg-accent/10 border border-accent/25 text-xs font-medium text-accent">{t}</span>
            ))}
          </div>
          <CodeComment className="mb-4">release 2.0.0</CodeComment>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            MotoQuant 2.0 is open source, including where it is wrong
          </h1>
          <div className="text-sm text-white/60 mb-12">10 November 2026 · 5 min read · MotoQuant Blog</div>
        </div>

        <Prose content={CONTENT} />

        <div className="max-w-2xl mx-auto mt-12 grid gap-3 sm:grid-cols-2">
          {LINKS.map((l) => (
            <a
              key={l.href}
              href={l.href}
              target="_blank"
              rel="noopener noreferrer"
              className="card card-hover block p-4 font-display font-semibold text-white hover:text-accent transition-colors"
            >
              {l.label} →
            </a>
          ))}
        </div>

        <div className="max-w-2xl mx-auto mt-10 flex flex-col sm:flex-row items-center gap-4">
          <Link href="/validation" className="shrink-0 px-5 py-2.5 bg-brand-orange text-on-accent font-display font-bold rounded-lg text-sm hover:bg-brand-orangeLight transition-colors">
            See every benchmark →
          </Link>
          <Link href="/simulator" className="text-sm text-accent hover:text-accent-bright">
            Or open the simulator
          </Link>
        </div>
      </article>

      <SiteFooter />
    </div>
  );
}
