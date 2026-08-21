/**
 * MotoQuant Pro — Terms of Service
 * Last updated: July 2, 2026 (§2 corrected: password + magic-link sign-in;
 * IGNITION v5 typographic skin)
 */

import SiteNav from "../../components/SiteNav";
import SiteFooter from "../../components/SiteFooter";
import PageHero from "../../components/PageHero";

export const metadata = {
  title: "Terms of Service — MotoQuant Pro",
  alternates: { canonical: "https://motoquant.in/terms" },
};

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-asphalt-0 text-white">
      <SiteNav />

      <PageHero
        kicker="legal · terms of service · pune jurisdiction"
        badge="Legal"
        title="Terms of Service"
        sub="The agreement governing your access to and use of MotoQuant Pro."
        className="pb-8 md:pb-10"
      >
        <p className="label-mono">Last updated · 2 July 2026</p>
      </PageHero>

      <main id="main" className="pt-10 pb-20 px-4 sm:px-6">
        <div className="mx-auto max-w-3xl">
        <p className="text-white/65 text-sm leading-relaxed">
          These Terms of Service ("Terms") govern your access to and use of MotoQuant Pro
          ("MotoQuant", "we", "us"), a motorcycle drag-racing physics simulation platform
          operated from Pune, India. By creating an account or using the service, you agree
          to these Terms.
        </p>

        <Section title="1. Description of service">
          <p>
            MotoQuant Pro provides first-principles physics simulations for motorcycle
            quarter-mile drag racing, parts ROI analysis, and associated tools. The service
            is available via a web application at motoquant.in and a REST API.
          </p>
          <p>
            <strong>Disclaimer: </strong>Simulations are for informational and analytical
            purposes only. Predicted quarter-mile elapsed times and trap speeds are estimates
            based on physical models and publicly available specifications. Do not rely on
            predicted ET for race strategy in any life-safety context. Real-world performance
            is affected by many factors outside the simulation model.
          </p>
        </Section>

        <Section title="2. Accounts and authentication">
          <p>
            You must provide a valid email address to create an account. You can sign in
            with a password — which we store only as a salted scrypt hash, never in
            plaintext — or with a passwordless magic-link email. You are responsible for
            keeping your email account and any password you set secure, as they control
            access to MotoQuant Pro.
          </p>
          <p>
            You must be at least 18 years old to create a paid account. By subscribing
            you confirm that you are 18 or over.
          </p>
        </Section>

        <Section title="3. Subscription plans and billing">
          <p>
            MotoQuant Pro offers three tiers: Free, Pro (₹499/mo or ₹4,999/yr), and
            Studio (₹1,999/mo or ₹19,990/yr). MotoQuant Pro is operated by an
            unregistered sole proprietorship with turnover below the ₹20 lakh GST
            registration threshold for services, so <strong>no GST is charged</strong> —
            the listed price is the total amount payable. You receive a payment
            receipt from the payment processor. Should we become GST-registered in
            future, we will give notice before GST begins to apply, and it will apply
            only to payments made after that date.
          </p>
          <p>
            <strong>Free tier: </strong>the Free tier is provided at no charge and is
            subject to a daily simulation limit. We may change free-tier limits with
            notice. Free access does not create an entitlement to paid-tier features
            or to any particular free-tier limit.
          </p>
          <p>
            Payments are processed by Razorpay (India — UPI, cards, net banking,
            wallets) and Stripe (international cards). By subscribing you agree to the
            processor's payment terms in addition to these Terms. Subscriptions
            auto-renew unless cancelled before the end of the billing period.
          </p>
          <p>
            <strong>7-day refund policy: </strong>If you are not satisfied within 7 calendar
            days of your first payment, contact us at motoquant@gmail.com for a full refund.
            Refunds are not available after the 7-day window or for renewals. Full terms,
            including how cancellations and failed payments are handled, are set out in our{" "}
            <a href="/refunds" className="text-accent hover:text-accent-bright transition-colors">Refund &amp; Cancellation Policy</a>.
          </p>
        </Section>

        <Section title="4. License keys">
          <p>
            License keys are device-bound seats for MotoQuant tooling and API
            integrations. A Pro subscription includes 1 seat; Studio includes up to 5.
            Keys are personal and non-transferable, and each binds to a single device.
          </p>
          <p>
            On subscription cancellation or expiry, seats are invalidated within
            24 hours.
          </p>
        </Section>

        <Section title="5. Acceptable use">
          <p>You may not:</p>
          <ul className="text-white/65 list-disc pl-5 space-y-1">
            <li>Reverse-engineer, decompile, or extract the physics model code</li>
            <li>Use the API at volumes exceeding fair-use limits (contact us for high-volume B2B arrangements)</li>
            <li>Share subscription credentials or license keys with third parties</li>
            <li>Use the service for any unlawful purpose under Indian law or the law of your jurisdiction</li>
            <li>Attempt to circumvent tier gating or rate-limit mechanisms</li>
          </ul>
        </Section>

        <Section title="6. Data you submit">
          <p>
            We collect your email address, simulation runs, build configurations, and any
            files you voluntarily upload (Dragy GPS logs, dyno CSVs). This data is
            used to provide and improve the service. See our Privacy Policy for details.
          </p>
          <p>
            <strong>Right to delete: </strong>You may request account deletion at any time
            by emailing motoquant@gmail.com. We will soft-delete your account within 7
            business days and permanently purge all personal data within 30 days.
          </p>
        </Section>

        <Section title="7. Intellectual property">
          <p>
            All physics models, software code, and data compilations in MotoQuant Pro are
            the intellectual property of MotoQuant Pro and are protected under applicable
            copyright and trade-secret law. Manufacturer specifications used in the bike
            catalog are publicly available data and remain the property of their respective
            manufacturers.
          </p>
        </Section>

        <Section title="8. Limitation of liability">
          <p>
            To the maximum extent permitted by applicable law, MotoQuant Pro shall not be
            liable for any indirect, incidental, special, consequential, or exemplary
            damages arising from use of or inability to use the service. Our total aggregate
            liability to you shall not exceed the amount paid by you in the 12 months
            preceding the claim.
          </p>
        </Section>

        <Section title="9. Governing law">
          <p>
            These Terms are governed by the laws of India. Any disputes shall be subject
            to the exclusive jurisdiction of the courts in Pune, Maharashtra, India.
          </p>
        </Section>

        <Section title="10. Changes to terms">
          <p>
            We may update these Terms with 14 days' notice via email to registered users.
            Continued use after the notice period constitutes acceptance of the updated Terms.
          </p>
        </Section>

        <div className="card mt-8 p-5 md:p-6 text-sm text-white/45">
          <p>MotoQuant Pro · Pune, Maharashtra, India</p>
          <p>Contact: <a href="mailto:motoquant@gmail.com" className="font-mono text-white/80 hover:text-white transition-colors">motoquant@gmail.com</a></p>
          <div className="mt-4 flex flex-wrap gap-4">
            <a href="/privacy" className="text-accent hover:text-accent-bright transition-colors">Privacy Policy</a>
            <a href="/refunds" className="text-accent hover:text-accent-bright transition-colors">Refunds</a>
            <a href="/contact" className="text-accent hover:text-accent-bright transition-colors">Contact</a>
            <a href="/pricing" className="text-accent hover:text-accent-bright transition-colors">Pricing</a>
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
      <div className="space-y-3 text-white/65 text-sm leading-relaxed">{children}</div>
    </section>
  );
}
