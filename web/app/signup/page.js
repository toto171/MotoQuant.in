"use client";

/**
 * MotoQuant Pro — Signup Page
 * ============================
 * Signup = login (magic-link, no password).
 * Redirect to login with a "welcome" flag so the CTA copy differs.
 */

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function SignupPage() {
  const router = useRouter();

  // Signup is the same flow as login — redirect immediately
  useEffect(() => {
    router.replace("/login?signup=1");
  }, [router]);

  return (
    <main className="flex min-h-screen items-center justify-center bg-black">
      <p className="font-mono text-[11px] uppercase tracking-[0.25em] text-white/45 select-none">
        <span className="text-brand-orange/70">//&nbsp;</span>
        redirecting to /login…
        <span className="cc-cursor text-brand-orange/70">_</span>
      </p>
    </main>
  );
}
