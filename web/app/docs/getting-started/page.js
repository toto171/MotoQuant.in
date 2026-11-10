import Link from 'next/link';
import Term from '../../../components/Term';

export const metadata = {
  title: 'Getting started — your first quarter-mile time in five minutes',
  description:
    'A five-minute walkthrough of MotoQuant: pick one of 541 bikes, read your quarter-mile time, change rider weight and location, add parts, find the best parts for your budget and get a race-day setup. Free and open source.',
  keywords: [
    'motoquant getting started',
    'how to use motorcycle drag simulator',
    'motorcycle quarter mile simulation guide',
    'how to predict motorcycle quarter mile time',
    'motorcycle 60 ft time guide',
    'aamby valley simulation setup',
  ],
  alternates: { canonical: 'https://motoquant.in/docs/getting-started' },
};

const REPO = 'https://github.com/toto171/MotoQuant.in';

function Step({ n, title, children }) {
  return (
    <section className="mb-10 flex gap-4">
      <span className="step-badge shrink-0" aria-hidden="true">{n}</span>
      <div className="min-w-0 flex-1">
        <h2 className="mb-2 font-display text-xl font-semibold text-white">{title}</h2>
        <div className="space-y-3 text-base leading-relaxed text-white/75">{children}</div>
      </div>
    </section>
  );
}

function A({ href, children, external }) {
  const cls = 'text-accent underline-offset-2 hover:underline';
  return external ? (
    <a href={href} target="_blank" rel="noopener noreferrer" className={cls}>{children}</a>
  ) : (
    <Link href={href} className={cls}>{children}</Link>
  );
}

function Code({ children }) {
  return (
    <pre className="my-3 overflow-x-auto rounded-lg border border-white/10 bg-asphalt-3 px-4 py-3 font-mono text-sm text-white/85">
      <code>{children}</code>
    </pre>
  );
}

export default function GettingStartedPage() {
  return (
    <article>
      <header className="mb-10">
        <p className="eyebrow mb-2">Getting started</p>
        <h1 className="mb-3 font-display text-3xl font-bold tracking-tight text-white md:text-4xl">
          Your first quarter-mile time in five minutes
        </h1>
        <p className="text-base leading-relaxed text-white/70">
          MotoQuant runs in your browser, is free, and does not need an account. You do not need to
          know any physics. Every term with a dotted underline explains itself when you tap it, and
          the full list is in the <A href="/docs/glossary">glossary</A>.
        </p>
      </header>

      <Step n="1" title="Pick a bike and read your time">
        <p>
          Open the <A href="/simulator">simulator</A>. It starts in <strong className="text-white">Simple</strong> mode.
          Under <strong className="text-white">Choose your bike</strong>, search for yours or tap one of the popular
          bikes. Your result appears straight away: a sentence in plain words, then the numbers.
        </p>
        <p>
          That first number is an <Term k="instant_estimate">instant estimate</Term>. Press{' '}
          <strong className="text-white">Run the full simulation</strong> any time you want the exact splits and charts.
          If your bike is missing, the <A href="/bikes">Bikes page</A> has a form to suggest it.
        </p>
      </Step>

      <Step n="2" title="Understand the numbers">
        <ul className="list-disc space-y-2 pl-5">
          <li>
            <Term k="et">Quarter-mile time</Term>: how long the bike takes to cover 402 m from a standing start.
            Smaller is quicker.
          </li>
          <li>
            <Term k="trap">Finish-line speed</Term>: how fast it is going as it crosses the line.
          </li>
          <li>
            <Term k="sixty">First 60 ft (launch)</Term>: how well it gets off the line. A good launch saves more time than
            extra power.
          </li>
          <li>
            <Term k="eighth">Halfway — ⅛ mile</Term>: the time at the halfway point, which many strips also time.
          </li>
        </ul>
      </Step>

      <Step n="3" title="Set your weight and where you are racing">
        <p>
          Change <strong className="text-white">Rider weight with gear</strong> to match you. Under{' '}
          <strong className="text-white">Where are you racing? (optional)</strong> pick a drag strip, or enter a place.
          Thin, hot air makes a bike slower, so the result adjusts for altitude and weather
          (<Term k="da">air and altitude</Term>).
        </p>
        <p className="rounded-xl border border-white/10 bg-asphalt-2 px-4 py-3 text-sm text-white/75">
          <strong className="text-white">If you do not choose a location</strong>, the simulation uses its default
          conditions: Aamby Valley, 679 m altitude, 22 °C, 40 % humidity. That is not sea level, so a time at
          the default can differ from one at your local strip. The result card always tells you which conditions it used.
        </p>
      </Step>

      <Step n="4" title="Switch to Advanced to add parts and compare">
        <p>
          The <strong className="text-white">Simple | Advanced</strong> switch is at the top of the simulator. Advanced is
          the full workbench. You can:
        </p>
        <ul className="list-disc space-y-1 pl-5">
          <li>add <strong className="text-white">Parts and mods</strong> from a catalog that only shows parts that fit your bike;</li>
          <li>change <Term k="power_boost">engine power</Term> and <Term k="mass_delta">weight added or removed</Term>;</li>
          <li>pick different tyres and set the <Term k="da">air and altitude</Term> by hand;</li>
          <li>see <Term k="top_speed">top speed</Term>, charts, <Term k="splits">splits</Term> and a <strong className="text-white">Compare</strong> tab for two bikes side by side;</li>
          <li>upload your own <Term k="dragy">Dragy</Term> or <Term k="dyno">dyno</Term> data under <strong className="text-white">My data</strong>.</li>
        </ul>
      </Step>

      <Step n="5" title="Find the best parts for your budget">
        <p>
          Not sure what to buy? Open <A href="/optimize">Best parts for your budget</A>, pick your bike, set how much you
          want to spend and what kind of build you want. MotoQuant tests every part that fits and shows the
          combination that makes the bike quickest, with the <Term k="cost_per_tenth">cost per tenth of a second</Term> for each part.
        </p>
      </Step>

      <Step n="6" title="Get a race-day setup">
        <p>
          <A href="/autotune">Race-day setup</A> suggests <Term k="gearing">gearing</Term>, <Term k="launch_rpm">launch RPM</Term>{' '}
          and tyre pressure for the air you will actually race in, and tells you how much time each change is worth.
        </p>
      </Step>

      <Step n="7" title="Save and share a run">
        <p>
          Press <strong className="text-white">Share</strong> to copy a link that opens the same bike, parts and conditions.
          If you create a free account you can also <strong className="text-white">Save</strong> a run, which gives it a public
          timeslip page and a place on the <A href="/leaderboard">leaderboard</A>. Only runs saved from the full simulation
          are listed, never instant estimates.
        </p>
      </Step>

      <Step n="8" title="For developers">
        <p>
          MotoQuant is open source (MIT). The same engine is a Python package, a command line tool, an HTTP API
          and an MCP server. Source and issues are on <A external href={REPO}>GitHub</A>.
        </p>
        <Code>{`git clone ${REPO}.git
cd MotoQuant.in
pip install -e .
python -m motoquant.run bikes --search hayabusa
python -m motoquant.run sim --bike-id 1 --venue-id 1`}</Code>
        <p>
          <code className="rounded bg-white/10 px-1.5 py-0.5 font-mono text-sm">make install</code> installs every dependency, and{' '}
          <code className="rounded bg-white/10 px-1.5 py-0.5 font-mono text-sm">make api</code> starts the HTTP API on
          port 8000 with interactive docs at <code className="rounded bg-white/10 px-1.5 py-0.5 font-mono text-sm">/docs</code>. The
          hosted API has the same docs at <A external href="https://motoquant-api.onrender.com/docs">motoquant-api.onrender.com/docs</A>.
        </p>
        <Code>{`curl -X POST https://motoquant-api.onrender.com/api/simulate/quick \\
  -H "Content-Type: application/json" \\
  -d '{"bike_id": 1, "rider_mass_kg": 70}'`}</Code>
        <p>To let an AI assistant such as Claude run simulations for you, add the MCP server:</p>
        <Code>{`claude mcp add motoquant -- python -m motoquant.mcp_server`}</Code>
        <p>
          More in the <A external href={`${REPO}/blob/main/docs/MCP.md`}>MCP guide</A> and the{' '}
          <A external href={`${REPO}#readme`}>README</A>.
        </p>
      </Step>

      <div className="mt-12 border-t border-white/10 pt-8">
        <p className="mb-4 text-sm font-semibold text-white">Keep reading</p>
        <div className="grid gap-4 sm:grid-cols-2">
          <Link href="/docs/glossary" className="card card-hover block p-4">
            <div className="mb-1 font-display font-semibold text-white">Glossary →</div>
            <div className="text-sm text-white/65">Every term in plain English.</div>
          </Link>
          <Link href="/docs/physics" className="card card-hover block p-4">
            <div className="mb-1 font-display font-semibold text-white">How the physics works →</div>
            <div className="text-sm text-white/65">The engineering behind every prediction.</div>
          </Link>
        </div>
        <div className="mt-8">
          <Link href="/simulator" className="btn-primary">Open the simulator</Link>
        </div>
      </div>
    </article>
  );
}
