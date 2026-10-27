/**
 * MotoQuant — Contact & community
 *
 * Rewritten October 2026 when MotoQuant became free and open source
 * (Apache-2.0). It used to be the payment-provider checklist page
 * (business/KYC block, billing + refund + grievance copy); nothing is sold
 * any more, so it is now the honest "how to reach the project" page:
 * GitHub issues for bugs and data corrections, discussions for questions
 * and ideas, a private channel for security reports, and email for
 * everything else. The route is kept (footer + sitemap + backlinks).
 */

import SiteNav from "../../components/SiteNav";
import SiteFooter from "../../components/SiteFooter";
import PageHero from "../../components/PageHero";
import {
  CONTACT_EMAIL,
  CONTRIBUTING_URL,
  DISCUSSIONS_URL,
  ISSUES_URL,
  LICENSE_NAME,
  LICENSE_URL,
  REPO_URL,
  SECURITY_URL,
} from "../../lib/site";

export const metadata = {
  title: "Contact & community",
  description:
    "Reach the MotoQuant project: GitHub issues for bugs and data corrections, discussions for questions and ideas, private security reports, and email.",
  alternates: { canonical: "https://motoquant.in/contact" },
};

const linkCls = "text-accent hover:text-accent-bright transition-colors";

function Ext({ href, children, className = linkCls }) {
  return (
    <a href={href} target="_blank" rel="noopener noreferrer" className={className}>
      {children}
    </a>
  );
}

export default function ContactPage() {
  return (
    <div className="min-h-screen bg-asphalt-0 text-white">
      <SiteNav />

      <PageHero
        kicker="issues · discussions · security · email"
        badge="Community"
        title="Contact & community"
        sub="MotoQuant is a free, open-source project. The fastest way to get something fixed is in the open, on GitHub."
        className="pb-8 md:pb-10"
      >
        <p className="label-mono">Maintained by volunteers · no ticket queue, no SLA</p>
      </PageHero>

      <main id="main" className="pt-10 pb-20 px-4 sm:px-6">
        <div className="mx-auto max-w-3xl">
          <Section title="Found a bug or a wrong number?">
            <p>
              Open an issue on GitHub. Simulator crashes, a page that won&rsquo;t
              load, a bike whose specs are wrong, a part that fits a bike it
              shouldn&rsquo;t, a sim result that looks physically off &mdash; all of it
              belongs in the issue tracker, where anyone can see it, reproduce
              it and fix it.
            </p>
            <p>
              <Ext href={ISSUES_URL}>Open an issue on GitHub &rarr;</Ext>
            </p>
            <p className="text-white/45">
              For a sim result, include the bike, venue, rider weight and any
              parts you selected (the simulator&rsquo;s Share link captures all of
              it). For a spec correction, include a source &mdash; a service manual,
              a magazine test, or an instrumented timeslip.
            </p>
          </Section>

          <Section title="Questions, ideas and timeslips">
            <p>
              Ask how something works, propose a feature, or share a real
              Dragy/RaceBox run so we can validate the physics against it in
              GitHub Discussions. Instrumented runs from Indian strips are the
              single most valuable thing you can contribute &mdash; every one makes
              the model more accurate for everyone.
            </p>
            <p>
              <Ext href={DISCUSSIONS_URL}>Join the discussion &rarr;</Ext>
            </p>
          </Section>

          <Section title="Contribute code or data">
            <p>
              The whole project &mdash; physics engine, bike catalog, website and
              API &mdash; is on GitHub under the{" "}
              <Ext href={LICENSE_URL}>{LICENSE_NAME}</Ext>. Fork it, run it
              yourself, send a pull request.
            </p>
            <ul className="space-y-1.5">
              <li>
                <Ext href={REPO_URL}>Source repository</Ext>
              </li>
              <li>
                <Ext href={CONTRIBUTING_URL}>Contributing guide</Ext>
              </li>
            </ul>
          </Section>

          <Section title="Security issues">
            <p>
              Please don&rsquo;t open a public issue for a vulnerability. Email{" "}
              <a href={`mailto:${CONTACT_EMAIL}?subject=Security`} className="font-mono text-white/80 hover:text-white transition-colors">
                {CONTACT_EMAIL}
              </a>{" "}
              with &ldquo;Security&rdquo; in the subject line, or use the
              repository&rsquo;s <Ext href={SECURITY_URL}>Security</Ext> tab to
              report it privately. We&rsquo;ll acknowledge it and coordinate a fix
              before anything is disclosed.
            </p>
          </Section>

          <Section title="Everything else">
            <p>
              Press, collaboration, data partnerships, or a question about your
              account and saved runs:
            </p>
            <p>
              <a
                href={`mailto:${CONTACT_EMAIL}`}
                className="font-mono text-accent hover:text-accent-bright transition-colors"
              >
                {CONTACT_EMAIL}
              </a>
            </p>
            <p className="text-white/45">
              To delete your account and saved runs, email from the address on
              the account and we&rsquo;ll remove them &mdash; see the{" "}
              <a href="/privacy" className={linkCls}>
                Privacy Policy
              </a>
              .
            </p>
          </Section>

          <div className="card mt-8 p-5 md:p-6 text-sm text-white/45">
            <p>MotoQuant · built in Pune, Maharashtra, India · free &amp; open source</p>
            <div className="mt-4 flex flex-wrap gap-4">
              <a href="/terms" className={linkCls}>
                Terms
              </a>
              <a href="/privacy" className={linkCls}>
                Privacy
              </a>
              <a href="/about" className={linkCls}>
                About
              </a>
              <Ext href={REPO_URL}>GitHub</Ext>
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
      <h2 className="font-display font-semibold text-lg md:text-xl text-white mb-3 border-l-2 border-white/15 pl-3">
        {title}
      </h2>
      <div className="space-y-3 text-white/65 text-sm leading-relaxed">{children}</div>
    </section>
  );
}
