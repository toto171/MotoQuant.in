import { Suspense } from 'react';
import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import CodeComment from '../../../components/CodeComment';
import ScoreboardDigits from '../../../components/ScoreboardDigits';

export const metadata = {
  title: 'The physics of a perfect launch | MotoQuant Blog',
  description: 'How clutch engagement RPM, tyre slip ratio and weight transfer interact in the first 0.4 seconds of a drag run, worked from first principles for Indian drag racers.',
  keywords: ['drag racing launch physics', 'motorcycle launch control', 'clutch engagement drag racing', 'tire slip ratio drag'],
  alternates: { canonical: 'https://motoquant.in/blog/the-physics-of-a-perfect-launch' },
  openGraph: {
    title: 'The physics of a perfect launch',
    description: 'How clutch, tyre, and weight transfer interact in the first 0.4 seconds.',
    url: 'https://motoquant.in/blog/the-physics-of-a-perfect-launch',
    type: 'article',
    publishedTime: '2026-04-24T00:00:00Z',
  },
};

const CONTENT = [
  {
    type: 'lead',
    text: 'Three things decide the first 0.4 seconds of a drag run: the RPM at which the clutch engages, how much the rear tyre slips, and how much weight moves onto the rear wheel. Get any one wrong and you lose tenths, sometimes much more. Below is the physics of each, how they affect each other, and what MotoQuant simulates when you press Run.',
  },
  {
    type: 'h2',
    text: 'Why the first 0.4 seconds matter',
  },
  {
    type: 'p',
    text: 'In a 10-second run, the first 60 feet usually take 1.7–2.1 seconds. Your 60-ft time, though, is almost entirely decided in the first half-second: from clutch release until the rear tyre stops spinning up and the bike settles into traction-limited acceleration. Miss the launch and you cannot catch up at the top end.',
  },
  {
    type: 'p',
    text: 'Taking 0.1 seconds off the 60-ft time takes roughly 0.07–0.09 seconds off the final ET, depending on the bike class. On a litre-class superbike, that margin decides most heads-up events. On a 155cc street bike, a good launch can make up for 3–4 hp less power.',
  },
  {
    type: 'h2',
    text: 'The clutch is your first control',
  },
  {
    type: 'p',
    text: 'The clutch does two jobs at launch. It limits the torque reaching the rear wheel, so the tyre does not light up and spin at once. It also lets the engine stay above idle, ideally at its peak-torque RPM, while the bike pulls away from rest.',
  },
  {
    type: 'p',
    text: 'Launch RPM is the engine speed you hold before you release the clutch. For most 4-stroke bikes the best launch RPM is 2,000–5,000 RPM below peak-power RPM. On a Yamaha R15 V3 (peak torque at ~7,500 RPM), a good launch RPM is around 4,000–5,000 RPM. On a Hayabusa (peak torque at ~7,000 RPM), it is 3,500–5,000 RPM.',
  },
  {
    type: 'p',
    text: 'MotoQuant models the clutch with two numbers: an engagement rate (Nm/s) and a slip RPM threshold. While the clutch is releasing, torque transfer scales with the engagement rate. Once rear-wheel RPM comes within the slip threshold of engine RPM, the clutch counts as locked. That gives realistic clutch heat and slip duration, and you can watch both in the simulation output.',
  },
  {
    type: 'callout',
    text: 'Rule of thumb: for most street-derived 4-stroke engines, launch at ≈70–80 % of peak-torque RPM. A two-stroke with a narrow power band needs 85–90 % of its tuned RPM, or the expansion chamber loses its boost before the bike has really moved.',
  },
  {
    type: 'h2',
    text: 'Tyre slip',
  },
  {
    type: 'p',
    text: 'Slip ratio is the normalized difference between the rear wheel\'s rotational speed and the bike\'s actual ground speed. At zero, the tyre rolls freely. At 1.0, the wheel spins in place.',
  },
  {
    type: 'p',
    text: 'Tyre models such as Pacejka\'s Magic Formula put peak longitudinal force at a slip ratio of roughly 0.07–0.15 for most road tyres. So a little wheel spin helps: the tyre makes more force than it would if it were locked to ground speed. Above 0.30 you are on the slope where traction falls off steeply.',
  },
  {
    type: 'p',
    text: 'Temperature matters too. A cold tyre has a lower μ_peak than a warm one. MotoQuant\'s thermal model tracks tyre temperature from conductance with the road surface and from the heat that slip generates. A sticky slick at race temperature (80–90°C) can reach a μ_peak of 1.6+. The same tyre cold, at 25°C, gives closer to 1.1.',
  },
  {
    type: 'h2',
    text: 'Weight transfer',
  },
  {
    type: 'p',
    text: 'When you accelerate, weight shifts from the front axle to the rear. More load on the rear tyre lets it make more friction force, up to a point. If the transfer is so large that the front wheel lifts, you have a wheelie, and the bike\'s angular momentum works against forward progress.',
  },
  {
    type: 'p',
    text: 'The share of weight that shifts is set by acceleration force × CoG height / wheelbase. A bike with a high CoG (adventure, cruiser) wheelies more readily than a low-slung sport bike, and a long wheelbase resists weight transfer.',
  },
  {
    type: 'p',
    text: 'MotoQuant tracks front and rear axle loads at every millisecond. If front load reaches zero, the simulation switches to a wheelie model that trades forward traction for rotational lift. Wheelie bars extend the effective wheelbase to delay that switch. They are a popular drag-prep mod, and their effect shows up clearly in MotoQuant\'s ET delta.',
  },
  {
    type: 'h2',
    text: 'How the three interact',
  },
  {
    type: 'p',
    text: 'The best launch is the mix of clutch engagement RPM, slip ratio and weight transfer that gives the highest average acceleration through the 60-ft zone. Each one moves the others. A higher launch RPM gives more torque and more slip. More slip means more heat and more traction, until you reach the μ_peak slope. More traction means more weight transfer and a higher wheelie risk.',
  },
  {
    type: 'p',
    text: 'In MotoQuant you can sweep the launch RPM and power boost sliders and watch the 60-ft time change in real time. The sweet spot usually shows as a shallow minimum: a slightly higher launch RPM gains nothing because the bike is already at the traction limit.',
  },
  {
    type: 'callout',
    text: 'To try this on your own bike, select it in the simulator, set Power boost to 0, then move the rider weight slider from 60 kg to 90 kg and watch the ET. A heavier rider puts more load on the rear, which helps traction slightly but adds inertia. For most sub-500cc bikes the crossover is around 72–75 kg.',
  },
  {
    type: 'h2',
    text: 'What to change on your bike',
  },
  {
    type: 'p',
    text: 'On a street bike at the drag strip, the most common launch mistake is holding too much RPM. The clutch heats up, engagement turns erratic, and the tyre spins past its peak-traction slip ratio. Drop launch RPM by 500–800 RPM and practise a smooth, fast clutch release. Most riders find this worth 0.2–0.5 seconds in 60-ft time alone.',
  },
  {
    type: 'p',
    text: 'On a built drag bike with a slipper clutch, MotoQuant\'s slipper model lets you tune the spring preload (Nm), which sets how hard the clutch bites. Lower preload gives softer engagement and less shock to the tyre, but slip can last longer. Higher preload gives a harder bite and a shorter engagement window, with more risk of wheelspin.',
  },
  {
    type: 'p',
    text: 'Run the numbers before you tune. MotoQuant is free, so you do not have to guess.',
  },
];

function Prose({ content }) {

  return (
    <div className="max-w-2xl mx-auto">
      {content.map((block, i) => {
        const nodes = [];
        if (block.type === 'h2') {
          nodes.push(
            <h2 key={i} className="font-display font-bold text-2xl md:text-3xl text-white mt-12 mb-4 tracking-tight">{block.text}</h2>
          );
        } else if (block.type === 'lead') {
          nodes.push(
            <p key={i} className="text-lg text-white/80 leading-relaxed mb-8 font-light">{block.text}</p>
          );
        } else if (block.type === 'callout') {
          nodes.push(
            <div key={i} className="my-8 px-5 py-4 rounded-xl border-l-4 border-brand-orange bg-brand-orange/5">
              <p className="text-sm text-white/80 leading-relaxed italic">{block.text}</p>
            </div>
          );
        } else {
          nodes.push(
            <p key={i} className="text-white/75 text-base leading-relaxed mb-5">{block.text}</p>
          );
        }
        return nodes;
      })}
    </div>
  );
}

export default function PostPage() {
  return (
    <div className="min-h-screen bg-black text-white">
      <SiteNav />

      <article className="pt-32 pb-24 px-6">
        <div className="max-w-2xl mx-auto">
          {/* Meta */}
          <div className="flex flex-wrap gap-2 mb-6">
            {['physics', 'launch control', 'clutch'].map(t => (
              <span key={t} className="px-2.5 py-1 rounded-full bg-accent/10 border border-accent/25 text-xs font-medium text-accent">{t}</span>
            ))}
          </div>
          <CodeComment className="mb-4">staging lane · the first 0.4 s</CodeComment>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            The physics of a perfect launch
          </h1>
          <div className="text-sm text-white/60 mb-6">
            24 April 2026 · 8 min read · MotoQuant Blog
          </div>

          {/* 60-ft stat chip — timing-board voice */}
          <div className="relative overflow-hidden inline-flex flex-wrap items-end gap-x-5 gap-y-2 rounded-xl border border-brand-orange/20 bg-ink-1/60 px-5 py-4 mb-12">
            <span aria-hidden="true" className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-brand-orange/50 to-transparent" />
            <span className="flex items-end gap-1.5">
              <ScoreboardDigits value="1.7-2.1" h={26} label="1.7 to 2.1 seconds" />
              <span className="font-mono text-xs text-white/60 mb-0.5">s</span>
            </span>
            <span className="text-xs text-white/60 mb-0.5">
              typical 60-ft · decided in the first 0.4 s
            </span>
          </div>
        </div>

        <Prose content={CONTENT} />

        {/* CTA */}
        <div className="max-w-2xl mx-auto mt-16 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">Test your own launch physics</div>
            <div className="text-white/60 text-sm">Free simulator: pick your bike, adjust rider weight, and watch the 60-ft time change.</div>
          </div>
          <Link href="/simulator" className="shrink-0 px-5 py-2.5 bg-brand-orange text-on-accent font-display font-bold rounded-lg text-sm hover:bg-brand-orangeLight transition-colors">
            Open the simulator →
          </Link>
        </div>
      </article>

      <SiteFooter />
    </div>
  );
}
