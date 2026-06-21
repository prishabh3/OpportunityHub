"use client";

import { useEffect, useState } from "react";
import type { Factor } from "@supabase/supabase-js";
import { MfaEnrollDialog } from "@/features/auth/components/mfa-enroll-dialog";
import { createClient } from "@/lib/supabase/client";

export function MfaSection() {
  const supabase = createClient();
  const [enrolledFactor, setEnrolledFactor] = useState<Factor | null>(null);
  const [loading, setLoading] = useState(true);

  async function loadFactors() {
    setLoading(true);
    const { data } = await supabase.auth.mfa.listFactors();
    // Only show verified TOTP factors (status === 'verified' means enrollment was completed).
    const verified = data?.totp?.find((f) => f.status === "verified") ?? null;
    setEnrolledFactor(verified);
    setLoading(false);
  }

  useEffect(() => {
    loadFactors();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (loading) return null;

  return (
    <section className="mt-8 flex flex-col gap-3">
      <div>
        <h2 className="text-base font-semibold">Security</h2>
        <p className="text-sm text-muted-foreground">
          Two-factor authentication adds an extra layer of security to your account.
        </p>
      </div>
      <MfaEnrollDialog enrolledFactor={enrolledFactor} onChanged={loadFactors} />
    </section>
  );
}
