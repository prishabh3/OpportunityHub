import type { Metadata } from "next";
import { redirect } from "next/navigation";

import { createClient } from "@/lib/supabase/server";
import { ResetPasswordForm } from "@/features/auth/components/reset-password-form";

export const metadata: Metadata = {
  title: "Set new password — OpportunityHub",
  robots: { index: false, follow: false },
};

/**
 * Accessed after the user clicks the password-reset email link.
 * The `/auth/callback` route exchanges the code for a temporary session;
 * this page then lets the user set a new password while that session is live.
 */
export default async function ResetPasswordPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  // If there's no session (link expired or already used), send to forgot-password.
  if (!user) redirect("/forgot-password");

  return (
    <div className="flex min-h-svh flex-col items-center justify-center px-4 py-12">
      <div className="w-full max-w-sm flex flex-col gap-6">
        <div className="flex flex-col gap-1 text-center">
          <h1 className="text-2xl font-semibold tracking-tight">Set a new password</h1>
          <p className="text-sm text-muted-foreground">
            Choose a strong password you haven&apos;t used before.
          </p>
        </div>
        <ResetPasswordForm />
      </div>
    </div>
  );
}
