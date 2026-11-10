"use client";

/**
 * MotoQuant — Signup Page
 * ============================
 * Signup = login (register tab opens via ?signup=1).
 * Redirect stub only.
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
    <main id="main" className="flex min-h-screen items-center justify-center bg-asphalt-0">
      <p className="text-base text-white/70">Taking you to the sign-up form…</p>
    </main>
  );
}
