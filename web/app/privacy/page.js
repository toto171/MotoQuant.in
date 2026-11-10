/**
 * MotoQuant — Privacy
 * Last updated: 10 November 2026. Accounts and server-side saved runs were
 * removed; saved runs now live in the visitor's browser. The chat assistant
 * runs on Anthropic's Claude, and a visitor may bring their own Anthropic key.
 *
 * Every statement here is checked against the code. When the code changes
 * what leaves the browser or what the server keeps, change this page in the
 * same pull request.
 */

import SiteNav from '../../components/SiteNav';
import SiteFooter from '../../components/SiteFooter';
import PageHero from '../../components/PageHero';

export const metadata = {
  title: 'Privacy | MotoQuant',
  description:
    'MotoQuant has no accounts and sets no cookies. What leaves your browser, where it goes, and what we keep.',
  alternates: { canonical: 'https://motoquant.in/privacy' },
};

const CONTACT = 'motoquant@gmail.com';

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-asphalt-0 text-white">
      <SiteNav />

      <PageHero
        title="Privacy"
        sub="No accounts, no cookies, and nothing kept that identifies you. Here is exactly what leaves your browser and where it goes."
        className="pb-8 md:pb-10"
      >
        <p className="label-mono">Last updated &middot; 10 November 2026</p>
      </PageHero>

      <main id="main" className="px-4 pb-20 pt-10 sm:px-6">
        <div className="mx-auto max-w-3xl">
          <p className="text-base leading-relaxed text-white/75">
            MotoQuant is free, open-source software, and motoquant.in is a public copy of it
            run by its maintainers. You never give us a name, an email address or a password,
            because there is nothing to sign in to. The source code that handles everything
            below is public, so you can check each statement on this page.
          </p>

          <Section title="What stays in your browser">
            <Row label="Saved runs">
              When you press Save, the run is stored in your browser&rsquo;s local storage and
              listed on <a href="/runs" className="text-accent hover:underline">Your runs</a>. It
              is never uploaded. Delete runs there, or clear your browser data to remove them all.
            </Row>
            <Row label="Preferences">
              Light or dark theme, Simple or Advanced mode, which option panels you opened, and
              which assistant you picked in the chat.
            </Row>
            <Row label="Your Anthropic key">
              Only if you add one under &ldquo;Use your own key&rdquo; in the chat. By default it
              is kept in this tab&rsquo;s session storage and cleared when you close the tab. If
              you tick &ldquo;Remember on this device&rdquo;, it is kept in local storage until
              you press Remove key or clear your browser data.
            </Row>
          </Section>

          <Section title="What reaches our server">
            <Row label="Simulation requests">
              The bike, upgrades, tyres and conditions you choose. If you look up a place, its
              name or coordinates are sent too. The server returns a result and keeps nothing.
            </Row>
            <Row label="File uploads">
              A Dragy log or dyno sheet you upload is read into a temporary file, processed, and
              deleted as soon as the result is ready.
            </Row>
            <Row label="Chat questions">
              What you type into the assistant, and the conversation so far, so it can answer.
              Not stored by us, and neither is anything the assistant estimates for a bike that is
              missing from the catalog.
            </Row>
            <Row label="Your Anthropic key">
              If you added your own key, it is sent with each question in a request header. Our
              server passes it to Anthropic to answer that one question, then drops it. We never
              store it, never write it to our logs and never send it back to your browser. Like
              every request, it travels through Vercel and Render on the way.
            </Row>
            <Row label="Usage events">
              Short labels such as &ldquo;simulation run&rdquo; or &ldquo;page error&rdquo;, with
              the page path, your browser&rsquo;s user-agent string, window size and a random id that changes on every
              page load. No free text, and nothing that links one visit to the next. They are
              written to the server log.
            </Row>
            <Row label="IP address">
              Used in memory to limit how many requests one connection can make, which keeps the
              free service up for everyone. Our hosting providers also record it in their request
              logs.
            </Row>
          </Section>

          <Section title="Who else sees it">
            <ul className="list-disc space-y-2 pl-5 text-base text-white/75">
              <li>
                <strong>Render</strong> runs the simulation server in Singapore and{' '}
                <strong>Vercel</strong> serves the website. Both see requests in transit and keep
                request logs under their own terms.
              </li>
              <li>
                <strong>Anthropic</strong> receives chat questions and the conversation so far,
                because the assistant is Anthropic&rsquo;s Claude model. If you added your own key,
                the question is sent to Anthropic under your key and Anthropic&rsquo;s terms for your
                account apply.
              </li>
              <li>
                <strong>A web search provider</strong> (Brave, Serper or DuckDuckGo) receives the
                search terms when the assistant looks something up.
              </li>
              <li>
                <strong>OpenWeatherMap</strong> receives a place name or coordinates when you ask
                for live weather.
              </li>
              <li>
                <strong>Sentry</strong> receives error reports when error tracking is switched on,
                without IP addresses or other personal data. <strong>PostHog</strong> receives the
                usage events above when analytics forwarding is switched on.
              </li>
            </ul>
            <p className="mt-3 text-base leading-relaxed text-white/75">
              We do not sell or share data with anyone else, and we show no advertising.
            </p>
          </Section>

          <Section title="Cookies">
            <p className="text-base leading-relaxed text-white/75">
              MotoQuant sets no cookies: none for sign-in, analytics or advertising.
            </p>
          </Section>

          <Section title="Shared timeslips">
            <p className="text-base leading-relaxed text-white/75">
              A timeslip link contains the bike, the changes and the conditions of the run, and
              nothing else. Anyone you send it to can read that setup from the link.
            </p>
          </Section>

          <Section title="Your rights">
            <p className="text-base leading-relaxed text-white/75">
              We hold no personal data about you that we can look up, so there is nothing to send
              you or delete on our side. Your saved runs are in your browser and under your control.
              For any privacy question, email{' '}
              <a href={`mailto:${CONTACT}`} className="font-mono text-white/65 transition-colors hover:text-white">
                {CONTACT}
              </a>
              .
            </p>
          </Section>

          <Section title="Changes to this page">
            <p className="text-base leading-relaxed text-white/75">
              We change this page when the software changes what it collects, and update the date
              at the top. Every earlier version is in the public repository&rsquo;s history.
            </p>
          </Section>

          <div className="card mt-8 p-5 text-sm text-white/65 md:p-6">
            <p>MotoQuant · Pune, Maharashtra, India</p>
            <p>
              Contact:{' '}
              <a href={`mailto:${CONTACT}`} className="font-mono text-white/65 transition-colors hover:text-white">
                {CONTACT}
              </a>
            </p>
            <div className="mt-4 flex gap-4">
              <a href="/terms" className="text-accent transition-colors hover:text-accent-bright">Terms</a>
              <a href="/contact" className="text-accent transition-colors hover:text-accent-bright">Contact</a>
            </div>
          </div>
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}

function Section({ title, children }) {
  return (
    <section className="card mt-6 p-5 md:p-6">
      <h2 className="mb-3 border-l-2 border-white/15 pl-3 font-display text-lg font-semibold text-white md:text-xl">{title}</h2>
      <div className="space-y-3">{children}</div>
    </section>
  );
}

function Row({ label, children }) {
  return (
    <div className="flex flex-col gap-1 text-sm sm:flex-row sm:gap-3">
      <span className="shrink-0 font-medium text-white/65 sm:w-44">{label}</span>
      <span className="leading-relaxed text-white/60">{children}</span>
    </div>
  );
}
