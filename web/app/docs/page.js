// /docs — a small server-rendered index of the docs pages (the URL used to
// 404). Rendered inside docs/layout.js, so it gets the nav and sidebar.
import Link from 'next/link';
import { OG_IMAGE } from '../StructuredData';

const DESCRIPTION =
  'How to use the MotoQuant quarter-mile simulator, the physics behind it, and how its times compare with published tests.';

export const metadata = {
  title: { absolute: 'MotoQuant docs' },
  description: DESCRIPTION,
  alternates: { canonical: 'https://motoquant.in/docs' },
  openGraph: {
    title: 'MotoQuant docs',
    description: DESCRIPTION,
    url: 'https://motoquant.in/docs',
    type: 'website',
    images: [OG_IMAGE],
  },
};

const PAGES = [
  {
    href: '/docs/getting-started',
    title: 'Getting started',
    text: 'Pick a bike, read its quarter-mile time, then change the rider, the strip and the parts.',
  },
  {
    href: '/docs/glossary',
    title: 'Glossary',
    text: 'Every term the simulator uses, in plain English.',
  },
  {
    href: '/docs/physics',
    title: 'How the physics works',
    text: 'The sub-models behind each simulated time: engine, gearing, tyres, air and weight transfer.',
  },
  {
    href: '/docs/validation',
    title: 'Accuracy data',
    text: 'Simulated times against published tests, and where the model still misses.',
  },
  {
    href: '/whitepaper',
    title: 'Whitepaper',
    text: 'The full technical write-up of the engine and how it is checked.',
  },
];

export default function DocsIndexPage() {
  return (
    <article>
      <header className="mb-10">
        <p className="eyebrow mb-2">Learn</p>
        <h1 className="mb-3 font-display text-3xl font-bold tracking-tight text-white md:text-4xl">
          MotoQuant docs
        </h1>
        <p className="text-base leading-relaxed text-white/70">{DESCRIPTION}</p>
      </header>
      <ul className="grid gap-3 sm:grid-cols-2">
        {PAGES.map((p) => (
          <li key={p.href}>
            <Link href={p.href} className="card card-hover block h-full p-5">
              <span className="block font-display text-lg font-semibold text-white">{p.title}</span>
              <span className="mt-1 block text-sm leading-relaxed text-white/70">{p.text}</span>
            </Link>
          </li>
        ))}
      </ul>
    </article>
  );
}
