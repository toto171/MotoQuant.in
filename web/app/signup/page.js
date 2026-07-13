"use client";

/**
 * MotoQuant Pro — Signup Page
 * ============================
 * Signup = login (register tab opens via ?signup=1).
 * Redirect stub only — the interim frame renders the STAGED v4 label
 * voice via the shared CodeComment primitive (StageDots + mono label).
 */

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import CodeComment from "../../components/CodeComment";

export default function SignupPage() {
  const router = useRouter();

  // Signup is the same flow as login — redirect immediately
  useEffect(() => {
    router.replace("/login?signup=1");
  }, [router]);

  return (
    <main id="main" className="flex min-h-screen items-center justify-center bg-asphalt-0">
      <CodeComment center>redirecting to /login…</CodeComment>
    </main>
  );
}
