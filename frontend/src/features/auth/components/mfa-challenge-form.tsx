"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { createClient } from "@/lib/supabase/client";

const schema = z.object({
  code: z.string().length(6, "Enter the 6-digit code from your authenticator app"),
});
type FormValues = z.infer<typeof schema>;

export function MfaChallengeForm({ next = "/" }: { next?: string }) {
  const supabase = createClient();
  const router = useRouter();
  const [factorId, setFactorId] = useState<string | null>(null);
  const [challengeId, setChallengeId] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  useEffect(() => {
    async function startChallenge() {
      const { data: factors } = await supabase.auth.mfa.listFactors();
      const factor = factors?.totp?.[0];
      if (!factor) return;
      setFactorId(factor.id);

      const { data, error } = await supabase.auth.mfa.challenge({ factorId: factor.id });
      if (error || !data) {
        toast.error("Could not start MFA challenge. Please sign in again.");
        return;
      }
      setChallengeId(data.id);
    }
    startChallenge();
  }, [supabase]);

  async function onSubmit({ code }: FormValues) {
    if (!factorId || !challengeId) {
      toast.error("Challenge not ready — please wait a moment.");
      return;
    }
    const { error } = await supabase.auth.mfa.verify({ factorId, challengeId, code });
    if (error) {
      toast.error("Invalid code — please try again.");
      return;
    }
    router.push(next.startsWith("/") ? next : "/");
    router.refresh();
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4" noValidate>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="mfa-code">Authenticator code</Label>
        <Input
          id="mfa-code"
          type="text"
          inputMode="numeric"
          autoComplete="one-time-code"
          maxLength={6}
          placeholder="123456"
          aria-invalid={!!errors.code}
          {...register("code")}
        />
        {errors.code && <p className="text-xs text-destructive">{errors.code.message}</p>}
      </div>
      <Button type="submit" size="lg" disabled={isSubmitting || !challengeId}>
        {isSubmitting ? "Verifying…" : "Verify"}
      </Button>
    </form>
  );
}
