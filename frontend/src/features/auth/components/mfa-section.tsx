"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import type { Factor } from "@supabase/supabase-js";

import { MfaEnrollDialog } from "@/features/auth/components/mfa-enroll-dialog";
import { createClient } from "@/lib/supabase/client";

export function MfaSection() {
  const supabase = createClient();
  const queryClient = useQueryClient();

  const { data: enrolledFactor = null, isLoading } = useQuery({
    queryKey: ["mfa", "factors"],
    queryFn: async () => {
      const { data } = await supabase.auth.mfa.listFactors();
      return (data?.totp?.find((f: Factor) => f.status === "verified") ?? null) as Factor | null;
    },
  });

  function onChanged() {
    queryClient.invalidateQueries({ queryKey: ["mfa", "factors"] });
  }

  if (isLoading) return null;

  return (
    <section className="mt-8 flex flex-col gap-3">
      <div>
        <h2 className="text-base font-semibold">Security</h2>
        <p className="text-sm text-muted-foreground">
          Two-factor authentication adds an extra layer of security to your account.
        </p>
      </div>
      <MfaEnrollDialog enrolledFactor={enrolledFactor} onChanged={onChanged} />
    </section>
  );
}
