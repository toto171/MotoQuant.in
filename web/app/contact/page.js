/**
 * MotoQuant — Contact
 *
 * MotoQuant is free and open source (MIT). Bugs and feature requests go to
 * GitHub issues; everything else goes to the project email. There is no
 * ticket queue and no contact form.
 */

import SiteNav from "../../components/SiteNav";
import SiteFooter from "../../components/SiteFooter";
import PageHero from "../../components/PageHero";

const EMAIL = "motoquant@gmail.com";
const REPO_URL = "https://github.com/toto171/MotoQuant.in";

export const metadata = {
  title: "Contact — MotoQuant",
  description:
    "Report a bug or request a feature on GitHub, or email the MotoQuant maintainers.",
  alternates: { canonical: "https://motoquant.in/contact" },
};

export default function ContactPage() {
  return (
    <div className="min-h-screen bg-asphalt-0 text-white">
      <SiteNav />

      <PageHero
        title="Contact us"
        sub="MotoQuant is free and open source. GitHub is the best place for bugs and ideas; email is there for everything else."
        className="pb-8 md:pb-10"
      />

      <main id="main" className="pt-10 pb-20 px-4 sm:px-6">
        <div className="mx-auto max-w-3xl">
          <Section title="Bugs and feature requests">
            <p>
              Open an issue on GitHub. Include the bike, venue and settings you
              used (a shared timeslip link from the simulator is perfect) so the
              result can be reproduced.
            </p>
            <p>
              <a
                href={`${REPO_URL}/issues`}
                target="_blank"
                rel="noopener noreferrer"
                className="font-mono text-accent hover:text-accent-bright transition-colors break-all"
              >
                github.com/toto171/MotoQuant.in/issues
              </a>
            </p>
          </Section>

          <Section title="Email">
            <p>
              For anything that does not fit an issue — questions, data
              corrections, collaboration — email the maintainers.
            </p>
            <p>
              <a
                href={`mailto:${EMAIL}`}
                className="font-mono text-accent hover:text-accent-bright transition-colors break-all"
              >
                {EMAIL}
              </a>
            </p>
            <p className="text-white/60">
              This is a volunteer project, so replies are best-effort.
            </p>
          </Section>

          <div className="card mt-8 p-5 md:p-6 text-sm text-white/60">
            <p>MotoQuant · Open source under the MIT License · Pune, India</p>
            <div className="mt-4 flex flex-wrap gap-4">
              <a href="/terms" className="text-accent hover:text-accent-bright transition-colors">
                Terms
              </a>
              <a href="/privacy" className="text-accent hover:text-accent-bright transition-colors">
                Privacy
              </a>
              <a
                href={REPO_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="text-accent hover:text-accent-bright transition-colors"
              >
                GitHub
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
      <div className="space-y-3 text-white/75 text-base leading-relaxed">{children}</div>
    </section>
  );
}
