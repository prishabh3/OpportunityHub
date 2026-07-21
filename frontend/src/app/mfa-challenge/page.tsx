import type { Metadata } from "next";
import { redirect } from "next/navigation";

import { createClient } from "@/lib/supabase/server";
import { safeRedirectPath } from "@/lib/safe-redirect";
import { MfaChallengeForm } from "@/features/auth/components/mfa-challenge-form";

export const metadata: Metadata = {
  title: "Verify identity — OpportunityHub",
  robots: { index: false, follow: false },
};

export default async function MfaChallengePage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string }>;
}) {
  const { next } = await searchParams;
  const supabase = await createClient();

  const { data: aal } = await supabase.auth.mfa.getAuthenticatorAssuranceLevel();

  // Already at aal2 — nothing to verify.
  if (aal?.currentLevel === "aal2") {
    redirect(safeRedirectPath(next));
  }

  // Not authenticated at all — send to sign-in.
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) redirect("/sign-in");

  return (
    <div className="flex min-h-svh flex-col items-center justify-center px-4 py-12">
      <div className="w-full max-w-sm flex flex-col gap-6">
        <div className="flex flex-col gap-1 text-center">
          <h1 className="text-2xl font-semibold tracking-tight">Two-factor verification</h1>
          <p className="text-sm text-muted-foreground">
            Enter the 6-digit code from your authenticator app to continue.
          </p>
        </div>
        <MfaChallengeForm next={safeRedirectPath(next)} />
      </div>
    </div>
  );
}
