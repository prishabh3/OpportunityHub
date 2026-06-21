import Link from "next/link";
import type { Metadata } from "next";

import { AuthForm } from "@/features/auth/components/auth-form";

export const metadata: Metadata = {
  title: "Sign in — OpportunityHub",
  robots: { index: false, follow: false },
};

export default async function SignInPage({
  searchParams,
}: {
  searchParams: Promise<{ redirect?: string; error?: string }>;
}) {
  const { redirect, error } = await searchParams;
  const redirectTo = redirect && redirect.startsWith("/") ? redirect : "/";

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1 text-center">
        <h1 className="text-2xl font-semibold tracking-tight">Welcome back</h1>
        <p className="text-sm text-muted-foreground">Sign in to your OpportunityHub account</p>
      </div>

      {error === "auth" && (
        <p className="rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-center text-sm text-destructive">
          Sign-in failed or link expired. Please try again.
        </p>
      )}

      <AuthForm mode="sign-in" redirectTo={redirectTo} />

      <div className="flex flex-col items-center gap-1 text-sm text-muted-foreground">
        <Link
          href="/forgot-password"
          className="underline-offset-4 hover:underline"
        >
          Forgot your password?
        </Link>
        <span>
          Don&apos;t have an account?{" "}
          <Link href="/sign-up" className="font-medium text-foreground underline-offset-4 hover:underline">
            Sign up
          </Link>
        </span>
      </div>
    </div>
  );
}
