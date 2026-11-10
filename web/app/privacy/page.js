/**
 * MotoQuant — Privacy Policy
 * Last updated: November 9, 2026 — open-source release: payment, subscription and
 * license-key data removed (none is collected).
 */

import SiteNav from "../../components/SiteNav";
import SiteFooter from "../../components/SiteFooter";
import PageHero from "../../components/PageHero";

export const metadata = {
  title: "Privacy Policy — MotoQuant",
  alternates: { canonical: "https://motoquant.in/privacy" },
};

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-asphalt-0 text-white">
      <SiteNav />

      <PageHero
        title="Privacy Policy"
        sub="What we collect, how we use it, and the rights you keep."
        className="pb-8 md:pb-10"
      >
        <p className="label-mono">Last updated &middot; 9 November 2026</p>
      </PageHero>

      <main id="main" className="pt-10 pb-20 px-4 sm:px-6">
        <div className="mx-auto max-w-3xl">
        <p className="text-white/75 text-base leading-relaxed">
          MotoQuant ("we", "us") is free, open-source software, and motoquant.in is a free
          public instance of it. Accounts are optional, and we collect as little as we can.
          This policy describes what data we collect, how we use it, and your rights
          under applicable Indian data protection principles and the Information
          Technology Act, 2000.
        </p>

        <Section title="1. Data we collect">
          <Row label="Email address">Only if you create an optional account: used to deliver sign-in links. Stored in our database indefinitely until you request deletion.</Row>
          <Row label="Password (optional)">If you choose password sign-in, we store only a salted scrypt hash — we cannot read your password. Magic-link sign-in requires no password at all.</Row>
          <Row label="Simulation runs">ET, trap speed, venue, build configuration. Stored when you choose to save a run, to power the leaderboard, shared timeslip links and your garage. Not sold to third parties.</Row>
          <Row label="Build configurations">Parts combinations and bike selections you save. Used to provide the service.</Row>
          <Row label="Dragy / dyno uploads">Dragy GPS logs and dyno CSV files you upload for calibration. Stored temporarily during processing and then deleted within 24 hours unless you explicitly save them.</Row>
          <Row label="Usage metadata">Request timestamps, endpoints called, error logs, and your IP address (used for per-IP rate limiting and abuse prevention). Used for debugging and service improvement. Not sold.</Row>
          <Row label="Anonymous telemetry">A small set of anonymous events (for example &ldquo;simulation run&rdquo; or a JavaScript error) with the page path, browser user-agent, viewport size and a random per-page-load session id. It carries no email, account id or free-text input, and is used to catch bugs and see which features get used.</Row>
        </Section>

        <Section title="2. Data residency">
          <p className="text-white/75 text-base leading-relaxed">
            Data is currently stored on servers in <strong>Singapore</strong> via
            Render (backend) and Vercel (frontend). We are evaluating migration to India-based
            hosting in line with anticipated data-localisation requirements. We will notify users
            via email before any material change in data residency.
          </p>
        </Section>

        <Section title="3. Cookies and tracking">
          <p className="text-white/75 text-base leading-relaxed">
            If you sign in, a session token is kept in your browser&rsquo;s sessionStorage (not
            localStorage or a cookie) to maintain your login state. We do <strong>not</strong>{" "}
            set analytics cookies, advertising cookies, or any third-party tracking cookies.
          </p>
        </Section>

        <Section title="4. How we use your data">
          <ul className="list-disc pl-5 space-y-1 text-white/75 text-base">
            <li>Authenticate you and maintain your session</li>
            <li>Save and show your runs in your garage, and render shared timeslip links</li>
            <li>Send transactional emails (sign-in links)</li>
            <li>Improve the physics model and catalog accuracy using anonymised run data</li>
            <li>Debug errors and maintain service reliability</li>
          </ul>
          <p className="text-white/75 text-base leading-relaxed mt-3">
            We do <strong>not</strong> sell, rent, or broker your personal data to third parties.
          </p>
        </Section>

        <Section title="5. Data sharing">
          <p className="text-white/75 text-base leading-relaxed">
            We share data only with:
          </p>
          <ul className="list-disc pl-5 space-y-1 text-white/75 text-base mt-2">
            <li><strong>Render / Vercel</strong> — infrastructure providers hosting our servers. Data is subject to their data-processing terms.</li>
          </ul>
        </Section>

        <Section title="6. Your rights">
          <ul className="list-disc pl-5 space-y-2 text-white/75 text-base">
            <li><strong>Access:</strong> Request a copy of the personal data we hold about you.</li>
            <li><strong>Correction:</strong> Request correction of inaccurate data.</li>
            <li><strong>Deletion:</strong> Request full account and data deletion. We will soft-delete within 7 business days and permanently purge within 30 days. Anonymised, aggregated sim data may be retained for model improvement.</li>
            <li><strong>Portability:</strong> Request your sim runs and build history in JSON format.</li>
          </ul>
          <p className="text-white/75 text-base leading-relaxed mt-3">
            To exercise any right, email <a href="mailto:motoquant@gmail.com" className="font-mono text-white/65 hover:text-white transition-colors">motoquant@gmail.com</a>.
            We respond within 14 business days.
          </p>
        </Section>

        <Section title="7. Data retention">
          <p className="text-white/75 text-base leading-relaxed">
            Active accounts and their data are retained for the lifetime of the account.
            Inactive accounts with no activity for 24 months may be soft-deleted
            after 60 days' notice.
          </p>
        </Section>

        <Section title="8. Security">
          <p className="text-white/75 text-base leading-relaxed">
            We use industry-standard practices: HTTPS everywhere, JWT tokens with short
            (15-minute) access lifetimes, rotating refresh tokens, and database access restricted to
            server-side code. Passwords are never stored in plaintext — only salted
            scrypt hashes.
          </p>
        </Section>

        <Section title="9. Changes to this policy">
          <p className="text-white/75 text-base leading-relaxed">
            We will notify registered users by email at least 14 days before making material
            changes to this policy. Continued use of the service after that period constitutes
            acceptance of the updated policy.
          </p>
        </Section>

        <div className="card mt-8 p-5 md:p-6 text-sm text-white/65">
          <p>MotoQuant · Pune, Maharashtra, India</p>
          <p>Contact: <a href="mailto:motoquant@gmail.com" className="font-mono text-white/65 hover:text-white transition-colors">motoquant@gmail.com</a></p>
          <div className="mt-4 flex gap-4">
            <a href="/terms" className="text-accent hover:text-accent-bright transition-colors">Terms of Service</a>
            <a href="/contact" className="text-accent hover:text-accent-bright transition-colors">Contact</a>
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
    <div className="flex gap-3 text-sm">
      <span className="w-44 shrink-0 font-medium text-white/65">{label}</span>
      <span className="text-white/60 leading-relaxed">{children}</span>
    </div>
  );
}
