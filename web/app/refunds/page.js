/**
 * MotoQuant Pro — Refund & Cancellation Policy
 * Created: August 10, 2026 (commercial-launch readiness)
 *
 * Standalone + footer-linked because payment providers require the refund
 * terms to be findable without reading the full ToS. The substance mirrors
 * /terms §3 and §5 — if you change one, change both.
 */

import SiteNav from "../../components/SiteNav";
import SiteFooter from "../../components/SiteFooter";
import PageHero from "../../components/PageHero";

export const metadata = {
  title: "Refund & Cancellation Policy — MotoQuant Pro",
  alternates: { canonical: "https://motoquant.in/refunds" },
};

export default function RefundsPage() {
  return (
    <div className="min-h-screen bg-asphalt-0 text-white">
      <SiteNav />

      <PageHero
        kicker="legal · refunds · cancellations"
        badge="Legal"
        title="Refund &amp; Cancellation Policy"
        sub="What you get back, when, and how to ask for it."
        className="pb-8 md:pb-10"
      >
        <p className="label-mono">Last updated · 10 August 2026</p>
      </PageHero>

      <main id="main" className="pt-10 pb-20 px-4 sm:px-6">
        <div className="mx-auto max-w-3xl">
          <p className="text-white/65 text-sm leading-relaxed">
            MotoQuant Pro is a digital subscription service. This policy explains
            how to cancel a subscription and when a refund is available. It forms
            part of our{" "}
            <a href="/terms" className="text-accent hover:text-accent-bright transition-colors">
              Terms of Service
            </a>
            .
          </p>

          <Section title="1. Open beta">
            <p>
              While MotoQuant Pro is in open beta, all tiers are provided free of
              charge and no payments are collected. Nothing in this policy applies
              until paid billing begins. Registered users will receive advance
              notice by email before that happens.
            </p>
          </Section>

          <Section title="2. Cancelling a subscription">
            <p>
              You may cancel at any time from your{" "}
              <a href="/account" className="text-accent hover:text-accent-bright transition-colors">
                account page
              </a>
              , or by emailing{" "}
              <a
                href="mailto:motoquant@gmail.com"
                className="font-mono text-white/80 hover:text-white transition-colors"
              >
                motoquant@gmail.com
              </a>
              . Cancellation stops the next renewal.
            </p>
            <p>
              Your paid features remain active until the end of the billing period
              you have already paid for. We do not pro-rate or refund the unused
              remainder of a period, except under the 7-day guarantee below.
            </p>
            <p>
              On cancellation or expiry, the account reverts to the free tier.
              Saved runs and garage data are retained; any issued license keys are
              invalidated within 24 hours.
            </p>
          </Section>

          <Section title="3. 7-day refund guarantee">
            <p>
              <strong className="text-white/85">
                If you are not satisfied within 7 calendar days of your first
                payment, email us for a full refund — no questions asked.
              </strong>{" "}
              This applies once per account, to the first payment only.
            </p>
            <p>Refunds are not available:</p>
            <ul className="list-disc pl-5 space-y-1.5">
              <li>after the 7-day window has passed;</li>
              <li>on renewal payments (cancel before the renewal date instead);</li>
              <li>
                where the account has been suspended for a breach of the{" "}
                <a href="/terms" className="text-accent hover:text-accent-bright transition-colors">
                  Terms of Service
                </a>
                .
              </li>
            </ul>
            <p className="text-white/45">
              Outside these cases we will still read your email. If the service
              did not do what we said it does, tell us and we will make it right.
            </p>
          </Section>

          <Section title="4. How to request a refund">
            <p>
              Email{" "}
              <a
                href="mailto:motoquant@gmail.com"
                className="font-mono text-white/80 hover:text-white transition-colors"
              >
                motoquant@gmail.com
              </a>{" "}
              from the address on your account, including the approximate date of
              payment. No form, no justification required within the 7-day window.
            </p>
            <p>
              We acknowledge refund requests within 2 business days and approve or
              decline within 5 business days.
            </p>
          </Section>

          <Section title="5. How refunds are paid">
            <p>
              Approved refunds are returned to the original payment method through
              the processor that handled the transaction — we cannot pay out to a
              different card, UPI ID or bank account.
            </p>
            <p>
              Once we initiate the refund, the processor typically settles it in
              5&ndash;7 business days for cards and 3&ndash;5 business days for UPI
              and net banking. The exact timing is controlled by your bank, not by
              us.
            </p>
          </Section>

          <Section title="6. Failed payments">
            <p>
              If a renewal payment fails, we retain access for a short grace period
              and retry. If it continues to fail, the account reverts to the free
              tier. No cancellation fee is charged.
            </p>
          </Section>

          <Section title="7. Taxes">
            <p>
              MotoQuant Pro is operated by an unregistered sole proprietorship with
              annual turnover below the ₹20 lakh GST registration threshold for
              services. <strong className="text-white/85">No GST is charged</strong>{" "}
              — the price you see is the price you pay, and refunds return that
              same amount.
            </p>
            <p>
              If we become GST-registered in future, we will give notice before GST
              begins to apply, and it will apply only to payments made after that
              date.
            </p>
          </Section>

          <Section title="8. Changes to this policy">
            <p>
              We may update this policy with 14 days&apos; notice by email to
              registered users. Changes never apply retroactively to a payment
              already made.
            </p>
          </Section>

          <div className="card mt-8 p-5 md:p-6 text-sm text-white/45">
            <p>MotoQuant Pro · Pune, Maharashtra, India</p>
            <p>
              Contact:{" "}
              <a
                href="mailto:motoquant@gmail.com"
                className="font-mono text-white/80 hover:text-white transition-colors"
              >
                motoquant@gmail.com
              </a>
            </p>
            <div className="mt-4 flex flex-wrap gap-4">
              <a href="/terms" className="text-accent hover:text-accent-bright transition-colors">
                Terms
              </a>
              <a href="/privacy" className="text-accent hover:text-accent-bright transition-colors">
                Privacy
              </a>
              <a href="/contact" className="text-accent hover:text-accent-bright transition-colors">
                Contact
              </a>
              <a href="/pricing" className="text-accent hover:text-accent-bright transition-colors">
                Pricing
              </a>
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
