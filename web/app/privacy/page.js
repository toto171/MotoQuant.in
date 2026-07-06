/**
 * MotoQuant Pro — Privacy Policy
 * Last updated: April 24, 2026
 */

import SiteNav from "../../components/SiteNav";
import SiteFooter from "../../components/SiteFooter";
import PageHero from "../../components/PageHero";

export const metadata = {
  title: "Privacy Policy — MotoQuant Pro",
  alternates: { canonical: "https://motoquant.in/privacy" },
};

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-black text-white">
      <SiteNav />

      <PageHero
        kicker="legal · privacy · dpdp act"
        badge="Legal"
        title="Privacy Policy"
        sub="What we collect, how we use it, and the rights you keep."
        className="border-b border-brand-orange/10 pb-8 md:pb-10"
      >
        <p className="label-mono">Last updated · 24 April 2026</p>
      </PageHero>

      <main id="main" className="pt-10 pb-20 px-4 sm:px-6">
        <div className="mx-auto max-w-3xl">
        <p className="text-white/80 text-sm leading-relaxed">
          MotoQuant Pro ("we", "us") is committed to protecting your personal data.
          This policy describes what data we collect, how we use it, and your rights
          under applicable Indian data protection principles and the Information
          Technology Act, 2000.
        </p>

        <Section title="1. Data We Collect">
          <Row label="Email address">Required to create an account and deliver sign-in links. Stored in our database indefinitely until you request deletion.</Row>
          <Row label="Password (optional)">If you choose password sign-in, we store only a salted scrypt hash — we cannot read your password. Magic-link sign-in requires no password at all.</Row>
          <Row label="Payment details">Handled entirely by our payment processors — Razorpay (India) and Stripe (international). Card, UPI and bank details never touch MotoQuant servers; we store only your subscription id, plan, and billing status.</Row>
          <Row label="Simulation runs">ET, trap speed, venue, build configuration. Stored to power the leaderboard and your run history. Not sold to third parties.</Row>
          <Row label="Build configurations">Parts combinations and bike selections you save. Used to provide the service.</Row>
          <Row label="Dragy / Dyno / ECU uploads">(Studio tier only) Files you upload for calibration. Stored temporarily during processing and then deleted within 24 hours unless you explicitly save them.</Row>
          <Row label="Device ID">(License keys) An opaque device fingerprint used to bind a license key to a single device. Not shared externally.</Row>
          <Row label="Usage metadata">Request timestamps, endpoints called, error logs. Used for debugging and service improvement. Not sold.</Row>
        </Section>

        <Section title="2. Data Residency">
          <p className="text-white/80 text-sm leading-relaxed">
            Data is currently stored on servers in <strong>Singapore</strong> via
            Render (backend) and Vercel (frontend). We are evaluating migration to India-based
            hosting in line with anticipated data-localisation requirements. We will notify users
            via email before any material change in data residency.
          </p>
        </Section>

        <Section title="3. Cookies and Tracking">
          <p className="text-white/80 text-sm leading-relaxed">
            We use <strong>session cookies only</strong> — a single JWT-backed session identifier
            stored in sessionStorage (not localStorage or a cookie) to maintain your login state.
            We do <strong>not</strong> set analytics cookies, advertising cookies, or any
            third-party tracking cookies without your explicit consent.
          </p>
          <p className="text-white/80 text-sm leading-relaxed mt-2">
            If we add analytics in the future, we will prompt you for consent before setting any
            non-essential cookies in compliance with applicable privacy law.
          </p>
        </Section>

        <Section title="4. How We Use Your Data">
          <ul className="list-disc pl-5 space-y-1 text-white/80 text-sm">
            <li>Authenticate you and maintain your session</li>
            <li>Deliver subscription-gated features based on your tier</li>
            <li>Process payments via Razorpay (email shared with Razorpay for invoicing)</li>
            <li>Send transactional emails (sign-in links, subscription receipts)</li>
            <li>Improve the physics model and catalog accuracy using anonymised run data</li>
            <li>Debug errors and maintain service reliability</li>
          </ul>
          <p className="text-white/80 text-sm leading-relaxed mt-3">
            We do <strong>not</strong> sell, rent, or broker your personal data to third parties.
          </p>
        </Section>

        <Section title="5. Data Sharing">
          <p className="text-white/80 text-sm leading-relaxed">
            We share data only with:
          </p>
          <ul className="list-disc pl-5 space-y-1 text-white/80 text-sm mt-2">
            <li><strong>Razorpay</strong> — payment processor. Your email and billing information are shared to process subscriptions and issue GST invoices. Governed by Razorpay's privacy policy.</li>
            <li><strong>Render / Vercel</strong> — infrastructure providers hosting our servers. Data is subject to their data-processing terms.</li>
          </ul>
        </Section>

        <Section title="6. Your Rights">
          <ul className="list-disc pl-5 space-y-2 text-white/80 text-sm">
            <li><strong>Access:</strong> Request a copy of the personal data we hold about you.</li>
            <li><strong>Correction:</strong> Request correction of inaccurate data.</li>
            <li><strong>Deletion:</strong> Request full account and data deletion. We will soft-delete within 7 business days and permanently purge within 30 days. Anonymised, aggregated sim data may be retained for model improvement.</li>
            <li><strong>Portability:</strong> Request your sim runs and build history in JSON format.</li>
          </ul>
          <p className="text-white/80 text-sm leading-relaxed mt-3">
            To exercise any right, email <a href="mailto:motoquant@gmail.com" className="text-brand-accent">motoquant@gmail.com</a>.
            We respond within 14 business days.
          </p>
        </Section>

        <Section title="7. Data Retention">
          <p className="text-white/80 text-sm leading-relaxed">
            Active accounts and their data are retained for the lifetime of the account.
            Inactive free-tier accounts with no activity for 24 months may be soft-deleted
            after 60 days' notice. Paid-account data is retained for 2 years after subscription
            cancellation for billing record purposes.
          </p>
        </Section>

        <Section title="8. Security">
          <p className="text-white/80 text-sm leading-relaxed">
            We use industry-standard practices: HTTPS everywhere, JWT tokens with short
            (15-minute) access lifetimes, rotating refresh tokens, license keys stored
            as SHA-256 hashes (never in plaintext), and database access restricted to
            server-side code. No passwords are stored.
          </p>
        </Section>

        <Section title="9. Changes to This Policy">
          <p className="text-white/80 text-sm leading-relaxed">
            We will notify registered users by email at least 14 days before making material
            changes to this policy. Continued use of the service after that period constitutes
            acceptance of the updated policy.
          </p>
        </Section>

        <div className="card mt-8 p-5 md:p-6 text-sm text-white/55">
          <p>MotoQuant Pro · Pune, Maharashtra, India</p>
          <p>Contact: <a href="mailto:motoquant@gmail.com" className="text-brand-accent hover:text-white transition-colors">motoquant@gmail.com</a></p>
          <div className="mt-4 flex gap-4">
            <a href="/terms" className="text-brand-orange hover:text-brand-orangeLight transition-colors">Terms of Service</a>
            <a href="/pricing" className="text-brand-orange hover:text-brand-orangeLight transition-colors">Pricing</a>
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
      <h2 className="font-display font-bold text-xl text-white mb-3 border-l-2 border-brand-orange pl-3">{title}</h2>
      <div className="space-y-3">{children}</div>
    </section>
  );
}

function Row({ label, children }) {
  return (
    <div className="flex gap-3 text-sm">
      <span className="w-44 shrink-0 font-medium text-white/80">{label}</span>
      <span className="text-white/60 leading-relaxed">{children}</span>
    </div>
  );
}
