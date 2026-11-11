/**
 * MotoQuant — Terms of Service
 * Last updated: 10 November 2026 — accounts removed; saved runs live in the
 * visitor's browser. §6 now says chat goes to Anthropic (Claude) and covers a
 * visitor's own Anthropic key. (9 November 2026: rewritten for the open-source
 * Apache-2.0 release: no plans, payments, refunds or license keys.)
 */

import SiteNav from "../../components/SiteNav";
import SiteFooter from "../../components/SiteFooter";
import PageHero from "../../components/PageHero";

const REPO_URL = "https://github.com/toto171/MotoQuant.in";

export const metadata = {
  title: "Terms of Service",
  alternates: { canonical: "https://motoquant.in/terms" },
};

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-asphalt-0 text-white">
      <SiteNav />

      <PageHero
        title="Terms of Service"
        sub="Plain terms for a free, hosted instance of open-source software."
        className="pb-8 md:pb-10"
      >
        <p className="label-mono">Last updated &middot; 10 November 2026</p>
      </PageHero>

      <main id="main" className="pt-10 pb-20 px-4 sm:px-6">
        <div className="mx-auto max-w-3xl">
        <p className="text-white/75 text-base leading-relaxed">
          MotoQuant is free, open-source software for
          simulating motorcycle drag-racing quarter-mile times. The site at motoquant.in is a
          free, public instance of that project, run from Pune, India. By using it you agree
          to these terms.
        </p>

        <Section title="1. Open source and free">
          <p>
            The MotoQuant software is released under the{" "}
            <a href={`${REPO_URL}/blob/main/LICENSE`} target="_blank" rel="noopener noreferrer" className="text-accent hover:text-accent-bright transition-colors">Apache License 2.0</a>.
            The source code is at{" "}
            <a href={REPO_URL} target="_blank" rel="noopener noreferrer" className="text-accent hover:text-accent-bright transition-colors">github.com/toto171/MotoQuant.in</a>.
            Your rights to the code are whatever that license grants. Using this hosted
            instance is free: there are no paid plans, no subscriptions and no license keys.
          </p>
        </Section>

        <Section title="2. Simulations are estimates, not advice">
          <p>
            Predicted elapsed times, trap speeds and parts-ROI figures are estimates from
            physical models and publicly available specifications. They are for
            informational and analytical purposes only and are not safety, engineering or
            tuning advice. Real-world performance also depends on things the model does not
            capture.
          </p>
          <p>
            Do not make safety-critical decisions from a prediction. Race only at sanctioned
            venues, with appropriate safety gear and supervision, and follow the law where you
            ride.
          </p>
        </Section>

        <Section title="3. No warranty">
          <p>
            The service and the software are provided &ldquo;as is&rdquo;, without warranty
            of any kind, express or implied, including accuracy, fitness for a particular
            purpose and availability. The hosted instance may be slow, change, or go offline
            at any time. To the maximum extent permitted by law, the maintainers are not liable
            for any damages arising from use of, or inability to use, the service or software.
          </p>
        </Section>

        <Section title="4. No accounts">
          <p>
            There is nothing to sign up for. Runs you save are kept in your own browser, not on
            our servers, so we cannot recover them if you clear your browser data.
          </p>
        </Section>

        <Section title="5. Acceptable use">
          <p>Please do not:</p>
          <ul className="text-white/65 list-disc pl-5 space-y-1">
            <li>Abuse or scrape the hosted service in a way that degrades it for others, or try to get around its rate limits</li>
            <li>Probe for or exploit security vulnerabilities (report them on GitHub instead)</li>
            <li>Use the service for any unlawful purpose under Indian law or the law of your jurisdiction</li>
          </ul>
          <p>
            If you need heavy or automated use, run your own copy under the
            Apache License 2.0. We may rate-limit or block usage that harms the service.
          </p>
        </Section>

        <Section title="6. What you send us">
          <p>
            Simulation requests, chat questions and files you upload (Dragy GPS logs, dyno
            sheets) are used only to produce your result. Chat questions are answered by
            Anthropic&rsquo;s Claude, so they are sent to Anthropic. If you use your own
            Anthropic API key, it is used only to answer your questions, you are responsible
            for its use and cost, and Anthropic&rsquo;s terms for your account apply. A timeslip
            link shows its setup to anyone who has the link. The{" "}
            <a href="/privacy" className="text-accent hover:text-accent-bright transition-colors">privacy page</a>{" "}
            lists what is kept and who else sees it.
          </p>
        </Section>

        <Section title="7. Third-party data">
          <p>
            Manufacturer specifications and published test results used in the bike catalog
            and validation set are publicly available data and remain the property of their
            respective owners. Brand and model names identify the products they belong to.
            MotoQuant is not affiliated with any motorcycle, parts or tyre manufacturer.
          </p>
        </Section>

        <Section title="8. Governing law">
          <p>
            These terms are governed by the laws of India. Any disputes are subject to the
            exclusive jurisdiction of the courts in Pune, Maharashtra, India.
          </p>
        </Section>

        <Section title="9. Changes">
          <p>
            We may update these terms; the date at the top shows the latest revision.
            Continued use after a change means you accept the updated terms.
          </p>
        </Section>

        <div className="card mt-8 p-5 md:p-6 text-sm text-white/60">
          <p>MotoQuant &middot; Pune, Maharashtra, India</p>
          <p>Contact: <a href="mailto:motoquant@gmail.com" className="font-mono text-white/80 hover:text-white transition-colors">motoquant@gmail.com</a></p>
          <div className="mt-4 flex flex-wrap gap-4">
            <a href="/privacy" className="text-accent hover:text-accent-bright transition-colors">Privacy</a>
            <a href="/contact" className="text-accent hover:text-accent-bright transition-colors">Contact</a>
            <a href={REPO_URL} target="_blank" rel="noopener noreferrer" className="text-accent hover:text-accent-bright transition-colors">GitHub</a>
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
      <h2 className="font-display font-semibold text-lg md:text-xl text-white mb-3 border-l-2 border-white/15 pl-3">{title}</h2>
      <div className="space-y-3 text-white/75 text-base leading-relaxed">{children}</div>
    </section>
  );
}
