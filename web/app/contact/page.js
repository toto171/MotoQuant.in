/**
 * MotoQuant Pro — Contact
 * Created: August 10, 2026 (commercial-launch readiness)
 *
 * Exists to satisfy the payment-provider website checklist (Razorpay
 * requires a reachable contact surface carrying the operating entity's
 * name, address and phone) AND to be the honest support page it looks
 * like. Email is the real channel — there is no ticket queue.
 *
 * ─────────────────────────────────────────────────────────────────────
 * OPERATOR: fill BUSINESS below with the EXACT values registered on the
 * Razorpay account. They must match — the activation review cross-checks
 * the website against the KYC record. Fields left as null simply do not
 * render (a missing address is recoverable; a wrong one fails review and
 * looks like fraud).
 * ─────────────────────────────────────────────────────────────────────
 */

import SiteNav from "../../components/SiteNav";
import SiteFooter from "../../components/SiteFooter";
import PageHero from "../../components/PageHero";

const BUSINESS = {
  // Legal name on the PAN the Razorpay account settles to.
  legalName: null, // e.g. "Arya Desai"
  tradeName: "MotoQuant Pro",
  // Registered/operating address, one array entry per line.
  addressLines: null, // e.g. ["Flat 4, Some Building", "Narhe", "Pune, Maharashtra 411041"]
  phone: null, // e.g. "+91 98765 43210"
  email: "motoquant@gmail.com",
  // Sole proprietorship, not GST-registered (turnover below the ₹20 lakh
  // services threshold). See /refunds and /terms §3.
  entityType: "Sole proprietorship (unregistered)",
};

export const metadata = {
  title: "Contact — MotoQuant Pro",
  alternates: { canonical: "https://motoquant.in/contact" },
};

export default function ContactPage() {
  const hasAddress = Array.isArray(BUSINESS.addressLines) && BUSINESS.addressLines.length > 0;

  return (
    <div className="min-h-screen bg-asphalt-0 text-white">
      <SiteNav />

      <PageHero
        kicker="support · billing · business details"
        badge="Contact"
        title="Contact us"
        sub="One inbox, answered by a founder. No contact form, no ticket queue."
        className="pb-8 md:pb-10"
      >
        <p className="label-mono">Typical reply · within 2 business days</p>
      </PageHero>

      <main id="main" className="pt-10 pb-20 px-4 sm:px-6">
        <div className="mx-auto max-w-3xl">
          <Section title="Email us">
            <p>
              Support, billing questions, refund requests, bug reports and B2B
              enquiries all go to the same address. It reaches a founder directly.
            </p>
            <p>
              <a
                href={`mailto:${BUSINESS.email}`}
                className="font-mono text-accent hover:text-accent-bright transition-colors"
              >
                {BUSINESS.email}
              </a>
            </p>
            <p className="text-white/45">
              For refund requests, please include the email address on your
              account and the approximate date of payment — see our{" "}
              <a href="/refunds" className="text-accent hover:text-accent-bright transition-colors">
                Refund &amp; Cancellation Policy
              </a>
              .
            </p>
          </Section>

          <Section title="Business details">
            <dl className="space-y-3">
              <Row label="Service">{BUSINESS.tradeName}</Row>
              {BUSINESS.legalName ? (
                <Row label="Operated by">{BUSINESS.legalName}</Row>
              ) : null}
              <Row label="Entity type">{BUSINESS.entityType}</Row>
              {hasAddress ? (
                <Row label="Address">
                  <span className="not-italic">
                    {BUSINESS.addressLines.map((line) => (
                      <span key={line} className="block">
                        {line}
                      </span>
                    ))}
                  </span>
                </Row>
              ) : null}
              {BUSINESS.phone ? (
                <Row label="Phone">
                  <a
                    href={`tel:${BUSINESS.phone.replace(/[^+\d]/g, "")}`}
                    className="font-mono text-white/80 hover:text-white transition-colors"
                  >
                    {BUSINESS.phone}
                  </a>
                </Row>
              ) : null}
              <Row label="Email">
                <a
                  href={`mailto:${BUSINESS.email}`}
                  className="font-mono text-white/80 hover:text-white transition-colors"
                >
                  {BUSINESS.email}
                </a>
              </Row>
              <Row label="Jurisdiction">Pune, Maharashtra, India</Row>
            </dl>
          </Section>

          <Section title="Grievance redressal">
            <p>
              If you are unhappy with how a support or billing issue was handled,
              write to{" "}
              <a
                href={`mailto:${BUSINESS.email}`}
                className="font-mono text-white/80 hover:text-white transition-colors"
              >
                {BUSINESS.email}
              </a>{" "}
              with &ldquo;Grievance&rdquo; in the subject line. We acknowledge within
              48 hours and aim to resolve within 15 days, consistent with Indian
              consumer-protection practice.
            </p>
            <p className="text-white/45">
              Payment disputes may also be raised directly with the payment
              processor that handled the transaction (Razorpay for Indian
              payments) through their own grievance channels.
            </p>
          </Section>

          <div className="card mt-8 p-5 md:p-6 text-sm text-white/45">
            <p>{BUSINESS.tradeName} · Pune, Maharashtra, India</p>
            <div className="mt-4 flex flex-wrap gap-4">
              <a href="/terms" className="text-accent hover:text-accent-bright transition-colors">
                Terms
              </a>
              <a href="/privacy" className="text-accent hover:text-accent-bright transition-colors">
                Privacy
              </a>
              <a href="/refunds" className="text-accent hover:text-accent-bright transition-colors">
                Refunds
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

function Row({ label, children }) {
  return (
    <div className="grid gap-1 sm:grid-cols-[10rem_1fr] sm:gap-4">
      <dt className="label-mono pt-0.5">{label}</dt>
      <dd className="text-white/70">{children}</dd>
    </div>
  );
}
