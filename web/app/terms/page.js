/**
 * MotoQuant Pro — Terms of Service
 * Last updated: July 2, 2026 (§2 corrected: password + magic-link sign-in;
 * Cockpit v3 PageHero + card surfaces)
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
    <div className="min-h-screen bg-black text-white">
      <SiteNav />

      <PageHero
        kicker="legal · terms of service · pune jurisdiction"
        badge="Legal"
        title="Terms of Service"
        sub="The agreement governing your access to and use of MotoQuant Pro."
        className="border-b border-brand-orange/10 pb-8 md:pb-10"
      >
        <p className="label-mono">Last updated · 2 July 2026</p>
      </PageHero>

      <main id="main" className="pt-10 pb-20 px-4 sm:px-6">
        <div className="mx-auto max-w-3xl">
        <p className="text-white/80 text-sm leading-relaxed">
          These Terms of Service ("Terms") govern your access to and use of MotoQuant Pro
          ("MotoQuant", "we", "us"), a motorcycle drag-racing physics simulation platform
          operated from Pune, India. By creating an account or using the service, you agree
          to these Terms.
        </p>

        <Section title="1. Description of Service">
          <p>
            MotoQuant Pro provides first-principles physics simulations for motorcycle
            quarter-mile drag racing, parts ROI analysis, and associated tools. The service
            is available via a web application at motoquant.in, a REST API, and an optional
            desktop application ("Desktop App") licensed under paid subscription plans.
          </p>
          <p>
            <strong>Disclaimer: </strong>Simulations are for informational and analytical
            purposes only. Predicted quarter-mile elapsed times and trap speeds are estimates
            based on physical models and publicly available specifications. Do not rely on
            predicted ET for race strategy in any life-safety context. Real-world performance
            is affected by many factors outside the simulation model.
          </p>
        </Section>

        <Section title="2. Accounts and Authentication">
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

        <Section title="3. Subscription Plans and Billing">
          <p>
            MotoQuant Pro offers three tiers: Free, Pro (₹499/mo or ₹4,999/yr), and
            Studio (₹1,999/mo or ₹19,990/yr). Prices are exclusive of GST (18% applicable
            under Indian GST law), which is applied at checkout where applicable. A tax
            invoice is issued by our payment provider.
          </p>
          <p>
            <strong>Open beta: </strong>while MotoQuant Pro is in open beta, all Pro and
            Studio features are provided free of charge to all registered accounts. We
            will give registered users advance notice by email before paid billing
            begins. Beta access does not create an entitlement to free access after
            commercial launch.
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
            Refunds are not available after the 7-day window or for renewals.
          </p>
        </Section>

        <Section title="4. Desktop Application and License Keys">
          <p>
            Pro subscribers may generate 1 desktop license key; Studio subscribers may
            generate up to 5 keys. License keys are personal and non-transferable.
            The Desktop App may operate offline for up to 7 days between license
            validation checks.
          </p>
          <p>
            On subscription cancellation or expiry, license keys are invalidated within
            24 hours of the next validation check. Access to paid features in the Desktop
            App will be revoked.
          </p>
        </Section>

        <Section title="5. Acceptable Use">
          <p>You may not:</p>
          <ul className="text-white/80 list-disc pl-5 space-y-1">
            <li>Reverse-engineer, decompile, or extract the physics model code</li>
            <li>Use the API at volumes exceeding fair-use limits (contact us for high-volume B2B arrangements)</li>
            <li>Share subscription credentials or license keys with third parties</li>
            <li>Use the service for any unlawful purpose under Indian law or the law of your jurisdiction</li>
            <li>Attempt to circumvent tier gating or rate-limit mechanisms</li>
          </ul>
        </Section>

        <Section title="6. Data You Submit">
          <p>
            We collect your email address, simulation runs, build configurations, and any
            files you voluntarily upload (Dragy GPS, dyno CSVs, ECU logs). This data is
            used to provide and improve the service. See our Privacy Policy for details.
          </p>
          <p>
            <strong>Right to delete: </strong>You may request account deletion at any time
            by emailing motoquant@gmail.com. We will soft-delete your account within 7
            business days and permanently purge all personal data within 30 days.
          </p>
        </Section>

        <Section title="7. Intellectual Property">
          <p>
            All physics models, software code, and data compilations in MotoQuant Pro are
            the intellectual property of MotoQuant Pro and are protected under applicable
            copyright and trade-secret law. Manufacturer specifications used in the bike
            catalog are publicly available data and remain the property of their respective
            manufacturers.
          </p>
        </Section>

        <Section title="8. Limitation of Liability">
          <p>
            To the maximum extent permitted by applicable law, MotoQuant Pro shall not be
            liable for any indirect, incidental, special, consequential, or exemplary
            damages arising from use of or inability to use the service. Our total aggregate
            liability to you shall not exceed the amount paid by you in the 12 months
            preceding the claim.
          </p>
        </Section>

        <Section title="9. Governing Law">
          <p>
            These Terms are governed by the laws of India. Any disputes shall be subject
            to the exclusive jurisdiction of the courts in Pune, Maharashtra, India.
          </p>
        </Section>

        <Section title="10. Changes to Terms">
          <p>
            We may update these Terms with 14 days' notice via email to registered users.
            Continued use after the notice period constitutes acceptance of the updated Terms.
          </p>
        </Section>

        <div className="card mt-8 p-5 md:p-6 text-sm text-white/45">
          <p>MotoQuant Pro · Pune, Maharashtra, India</p>
          <p>Contact: <a href="mailto:motoquant@gmail.com" className="text-brand-accent hover:text-white transition-colors">motoquant@gmail.com</a></p>
          <div className="mt-4 flex gap-4">
            <a href="/privacy" className="text-brand-orange hover:text-brand-orangeLight transition-colors">Privacy Policy</a>
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
      <div className="space-y-3 text-white/80 text-sm leading-relaxed">{children}</div>
    </section>
  );
}
