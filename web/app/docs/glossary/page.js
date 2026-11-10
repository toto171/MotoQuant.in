import Link from 'next/link';
import { GLOSSARY_LIST } from '../../../lib/glossary';

export const metadata = {
  title: 'Drag-racing terms in plain English',
  description:
    'A plain-English glossary of drag-racing and motorcycle terms used in MotoQuant: quarter-mile time, finish-line speed, launch RPM, gearing, density altitude, traction, cost per tenth of a second and more.',
  alternates: { canonical: 'https://motoquant.in/docs/glossary' },
};

export default function GlossaryPage() {
  return (
    <article>
      <header className="mb-10">
        <p className="eyebrow mb-2">Glossary</p>
        <h1 className="mb-3 font-display text-3xl font-bold tracking-tight text-white md:text-4xl">
          Drag-racing terms in plain English
        </h1>
        <p className="text-base leading-relaxed text-white/70">
          You do not need to be an engineer to use MotoQuant. This page explains
          every term the simulator uses. Anywhere on the site, a word with a
          dotted underline opens a short version of its definition here.
        </p>
      </header>

      <nav aria-label="Jump to a term" className="mb-10 flex flex-wrap gap-2">
        {GLOSSARY_LIST.map((e) => (
          <a
            key={e.key}
            href={`#${e.key}`}
            className="inline-flex min-h-[36px] items-center rounded-lg border border-white/10 px-3 text-sm text-white/75 transition-colors hover:border-accent/50 hover:text-white"
          >
            {e.label}
          </a>
        ))}
      </nav>

      <dl className="space-y-4">
        {GLOSSARY_LIST.map((e) => (
          <div key={e.key} id={e.key} className="card card-pad scroll-mt-24">
            <dt className="font-display text-lg font-semibold text-white">{e.label}</dt>
            <dd className="mt-2 text-base leading-relaxed text-white/80">{e.short}</dd>
            <dd className="mt-2 text-sm leading-relaxed text-white/65">{e.long}</dd>
          </div>
        ))}
      </dl>

      <p className="mt-10 text-sm text-white/65">
        Missing a term? <a className="text-accent underline-offset-2 hover:underline" href="https://github.com/toto171/MotoQuant.in/issues" target="_blank" rel="noopener noreferrer">Tell us on GitHub</a>, or head back to the{' '}
        <Link className="text-accent underline-offset-2 hover:underline" href="/simulator">simulator</Link>.
      </p>
    </article>
  );
}
