"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { createClient } from "@/lib/supabase/client";

type Mode = "sign-in" | "sign-up";

const schema = z.object({
  email: z.string().email("Enter a valid email address").max(254, "Email too long"),
  // 72-char cap: bcrypt silently truncates beyond 72 bytes; validate before sending.
  password: z.string().min(8, "Password must be at least 8 characters").max(72, "Password too long"),
});

type FormValues = z.infer<typeof schema>;

const COPY: Record<Mode, { submit: string; loading: string }> = {
  "sign-in": { submit: "Sign in", loading: "Signing in…" },
  "sign-up": { submit: "Create account", loading: "Creating account…" },
};

export function AuthForm({ mode, redirectTo }: { mode: Mode; redirectTo: string }) {
  const router = useRouter();
  const supabase = createClient();
  const [oauthLoading, setOauthLoading] = useState<"google" | "github" | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const callbackUrl = () => {
    const url = new URL("/auth/callback", window.location.origin);
    url.searchParams.set("next", redirectTo);
    return url.toString();
  };

  async function onSubmit(values: FormValues) {
    if (mode === "sign-in") {
      const { error } = await supabase.auth.signInWithPassword(values);
      if (error) {
        toast.error(error.message);
        return;
      }
      router.push(redirectTo);
      router.refresh();
      return;
    }

    const { error } = await supabase.auth.signUp({
      email: values.email,
      password: values.password,
      options: { emailRedirectTo: callbackUrl() },
    });
    if (error) {
      toast.error(error.message);
      return;
    }
    toast.success("Check your email to confirm your account.");
  }

  async function signInWithProvider(provider: "google" | "github") {
    setOauthLoading(provider);
    const { error } = await supabase.auth.signInWithOAuth({
      provider,
      options: { redirectTo: callbackUrl() },
    });
    if (error) {
      toast.error(error.message);
      setOauthLoading(null);
    }
    // On success the browser is redirected to the provider, so no further work.
  }

  const busy = isSubmitting || oauthLoading !== null;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-3">
        <Button
          type="button"
          variant="outline"
          size="lg"
          disabled={busy}
          onClick={() => signInWithProvider("google")}
        >
          {oauthLoading === "google" ? "Redirecting…" : "Continue with Google"}
        </Button>
        <Button
          type="button"
          variant="outline"
          size="lg"
          disabled={busy}
          onClick={() => signInWithProvider("github")}
        >
          {oauthLoading === "github" ? "Redirecting…" : "Continue with GitHub"}
        </Button>
      </div>

      <div className="flex items-center gap-3 text-xs text-muted-foreground">
        <span className="h-px flex-1 bg-border" />
        or
        <span className="h-px flex-1 bg-border" />
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4" noValidate>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            autoComplete="email"
            placeholder="you@example.com"
            aria-invalid={!!errors.email}
            {...register("email")}
          />
          {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="password">Password</Label>
          <Input
            id="password"
            type="password"
            autoComplete={mode === "sign-in" ? "current-password" : "new-password"}
            placeholder="••••••••"
            aria-invalid={!!errors.password}
            {...register("password")}
          />
          {errors.password && (
            <p className="text-xs text-destructive">{errors.password.message}</p>
          )}
        </div>

        <Button type="submit" size="lg" disabled={busy}>
          {isSubmitting ? COPY[mode].loading : COPY[mode].submit}
        </Button>
      </form>
    </div>
  );
}
