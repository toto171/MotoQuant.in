/**
 * MotoQuant — Privacy Policy
 * Last updated: October 23, 2026 — rewritten when MotoQuant became free and
 * open source. Payment/subscription/license-key data no longer exists, so
 * those rows are gone; the policy now names every third-party processor the
 * hosted service really uses (hosting, email, AI chat providers, web search,
 * weather, error tracking, optional analytics). Keep it in sync with the
 * code: if a new external service starts receiving user data, add it here.
 */

import SiteNav from "../../components/SiteNav";
import SiteFooter from "../../components/SiteFooter";
import PageHero from "../../components/PageHero";
import { CONTACT_EMAIL, REPO_URL } from "../../lib/site";

export const metadata = {
  title: "Privacy Policy",
  alternates: { canonical: "https://motoquant.in/privacy" },
};

const linkCls = "text-accent hover:text-accent-bright transition-colors";

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-asphalt-0 text-white">
      <SiteNav />

      <PageHero
        kicker="legal · privacy · dpdp act"
        badge="Legal"
        title="Privacy Policy"
        sub="What the hosted MotoQuant service collects, who processes it, and the rights you keep."
        className="pb-8 md:pb-10"
      >
        <p className="label-mono">Last updated · 23 October 2026</p>
      </PageHero>

      <main id="main" className="pt-10 pb-20 px-4 sm:px-6">
        <div className="mx-auto max-w-3xl">
        <p className="text-white/65 text-sm leading-relaxed">
          This policy covers the hosted MotoQuant service at motoquant.in (&ldquo;we&rdquo;,
          &ldquo;us&rdquo;). MotoQuant is free and open source, so there is no payment data
          at all, and you can check exactly what the service does with your data by
          reading the{" "}
          <a href={REPO_URL} target="_blank" rel="noopener noreferrer" className={linkCls}>
            source code
          </a>
          . We handle personal data in line with India&rsquo;s Digital Personal Data
          Protection Act, 2023 and the Information Technology Act, 2000. If you run your
          own copy of MotoQuant, you are responsible for your own deployment&rsquo;s data.
        </p>

        <Section title="1. Data we collect">
          <Row label="Nothing, by default">You can run simulations, browse the catalog and use the tools without an account. We don&rsquo;t ask for your name, phone number or payment details &mdash; ever.</Row>
          <Row label="Email address">Only if you create an optional account or ask for a sign-in link. Used to sign you in and to send account emails. Kept until you delete your account.</Row>
          <Row label="Password (optional)">If you set one, we store only a salted scrypt hash &mdash; we cannot read your password. Magic-link sign-in needs no password.</Row>
          <Row label="Saved runs">When you press &ldquo;Save this run&rdquo;: bike, venue, conditions, build, ET, trap speed and any note you add. Saved runs get a public, shareable timeslip page and can appear on the leaderboard. If you are signed in, they are linked to your account&rsquo;s garage.</Row>
          <Row label="Dragy / dyno uploads">Files you upload for calibration are written to a temporary file, parsed, and deleted immediately. We keep only the computed result shown to you, and only for the request.</Row>
          <Row label="Chat messages">What you type into the chat assistant is sent to an AI model provider to generate the answer (see section 4). We don&rsquo;t store chat transcripts in our database. Please don&rsquo;t type personal information into the chat.</Row>
          <Row label="Location (optional)">If you tap &ldquo;Use my location&rdquo;, your browser asks permission first. Your coordinates are matched to the nearest venue in your browser; if none is near, they are sent to our server to look up current weather. They are not stored.</Row>
          <Row label="Suggestions &amp; corrections">If you suggest a bike for the catalog or a spec correction, we store it and, only if you provide one, a reply email address.</Row>
          <Row label="Usage &amp; error data">Anonymous product events (event names like &ldquo;sim run started&rdquo;, a random per-tab session id, page path, browser type, screen size) and error reports. No account id, no email. Our hosting providers&rsquo; standard request logs include IP addresses and are kept briefly for security and debugging. IP addresses are also held in memory, briefly, for per-visitor rate limiting.</Row>
        </Section>

        <Section title="2. Where data is stored">
          <p className="text-white/65 text-sm leading-relaxed">
            The backend and its database run on <strong>Render</strong> in
            <strong> Singapore</strong>. The website is served by <strong>Vercel</strong>&rsquo;s
            global edge network. We will notify registered users by email before any
            material change in where account data is stored.
          </p>
        </Section>

        <Section title="3. Cookies and browser storage">
          <p className="text-white/65 text-sm leading-relaxed">
            We set <strong>no cookies</strong> for analytics or advertising. If you sign in,
            your refresh token is kept in your browser&rsquo;s <strong>sessionStorage</strong>
            (cleared when you close the tab) and your access token only in memory.
            Nothing is kept in localStorage.
          </p>
        </Section>

        <Section title="4. Third parties that process data">
          <p className="text-white/65 text-sm leading-relaxed">
            We share data only with the services needed to run MotoQuant, and only the
            data each one needs:
          </p>
          <ul className="list-disc pl-5 space-y-2 text-white/65 text-sm mt-2">
            <li><strong>Render and Vercel</strong> &mdash; hosting for the backend/database and the website. All data passes through them under their data-processing terms.</li>
            <li><strong>Email delivery (Resend, or an SMTP mail provider)</strong> &mdash; receives your email address and the sign-in link when we send you one.</li>
            <li><strong>AI model providers for the chat assistant</strong> &mdash; your chat messages and the tool results the assistant uses are sent to the configured provider: Groq by default, or Google (Gemini), Anthropic (Claude), DeepSeek or OpenRouter if the operator configures one of those. They process it under their own terms.</li>
            <li><strong>Web search for the chat assistant</strong> &mdash; when the assistant looks something up, the search query (not your identity) is sent to Brave Search, Serper or DuckDuckGo.</li>
            <li><strong>OpenWeatherMap</strong> &mdash; receives coordinates or a place name when current weather is looked up for a location you chose.</li>
            <li><strong>Sentry</strong> &mdash; error tracking for the backend. Error reports contain technical details about the failing request; they are configured not to attach personal data.</li>
            <li><strong>PostHog (optional)</strong> &mdash; product analytics, used only if the operator has enabled it. When enabled, it receives the same anonymous usage events described above, forwarded by our server &mdash; never your email or account id. It is off by default.</li>
          </ul>
          <p className="text-white/65 text-sm leading-relaxed mt-3">
            We do <strong>not</strong> sell, rent or broker personal data, and we do not use
            it for advertising.
          </p>
        </Section>

        <Section title="5. How we use data">
          <ul className="list-disc pl-5 space-y-1 text-white/65 text-sm">
            <li>Run the simulations and tools you ask for</li>
            <li>Sign you in and keep your garage of saved runs</li>
            <li>Show saved runs on public timeslip pages and the leaderboard</li>
            <li>Improve the physics model and catalog using anonymised, aggregated run data</li>
            <li>Keep the service secure, rate-limit abuse and fix errors</li>
          </ul>
        </Section>

        <Section title="6. Your rights">
          <ul className="list-disc pl-5 space-y-2 text-white/65 text-sm">
            <li><strong>Access:</strong> ask for a copy of the personal data we hold about you.</li>
            <li><strong>Correction:</strong> ask us to correct inaccurate data.</li>
            <li><strong>Deletion:</strong> ask us to delete your account and saved runs. We remove account data within 30 days. Anonymised, aggregated statistics may be kept.</li>
            <li><strong>Portability:</strong> ask for your saved runs in JSON format.</li>
            <li><strong>Withdraw consent:</strong> stop using the service and ask for deletion at any time.</li>
          </ul>
          <p className="text-white/65 text-sm leading-relaxed mt-3">
            Email <a href={`mailto:${CONTACT_EMAIL}`} className="font-mono text-white/65 hover:text-white transition-colors">{CONTACT_EMAIL}</a> from
            the address on your account. We respond within 14 business days.
          </p>
        </Section>

        <Section title="7. Data retention">
          <p className="text-white/65 text-sm leading-relaxed">
            Account data and saved runs are kept for the life of the account. Accounts
            with no activity for 24 months may be deleted after 60 days&rsquo; notice by
            email. Saved runs made without an account have no owner to delete them on
            request by default &mdash; email us with the run link if you want one removed.
          </p>
        </Section>

        <Section title="8. Security">
          <p className="text-white/65 text-sm leading-relaxed">
            HTTPS everywhere, short-lived (15-minute) access tokens with rotating refresh
            tokens, passwords stored only as salted scrypt hashes, and database access
            restricted to server-side code. Because the code is public, anyone can review
            how this works. Found a vulnerability? See the{" "}
            <a href="/contact" className={linkCls}>contact page</a> for how to report it
            privately.
          </p>
        </Section>

        <Section title="9. Children">
          <p className="text-white/65 text-sm leading-relaxed">
            Accounts are for people aged 18 and over. We don&rsquo;t knowingly collect personal
            data from children; if you believe a child has created an account, email us
            and we will delete it.
          </p>
        </Section>

        <Section title="10. Changes to this policy">
          <p className="text-white/65 text-sm leading-relaxed">
            We will notify registered users by email at least 14 days before making
            material changes to this policy. Every version is also in the project&rsquo;s
            public git history.
          </p>
        </Section>

        <div className="card mt-8 p-5 md:p-6 text-sm text-white/55">
          <p>MotoQuant · Pune, Maharashtra, India · free &amp; open source</p>
          <p>Contact: <a href={`mailto:${CONTACT_EMAIL}`} className="font-mono text-white/65 hover:text-white transition-colors">{CONTACT_EMAIL}</a></p>
          <div className="mt-4 flex flex-wrap gap-4">
            <a href="/terms" className={linkCls}>Terms of Service</a>
            <a href="/contact" className={linkCls}>Contact &amp; community</a>
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
      <div className="space-y-3">{children}</div>
    </section>
  );
}

function Row({ label, children }) {
  return (
    <div className="flex flex-col gap-1 text-sm sm:flex-row sm:gap-3">
      <span className="w-44 shrink-0 font-medium text-white/65">{label}</span>
      <span className="text-white/60 leading-relaxed">{children}</span>
    </div>
  );
}
