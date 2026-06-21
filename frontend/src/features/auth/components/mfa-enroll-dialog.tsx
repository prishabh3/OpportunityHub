"use client";

import { useState } from "react";
import Image from "next/image";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { ShieldCheck, ShieldOff } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { createClient } from "@/lib/supabase/client";

const codeSchema = z.object({
  code: z.string().length(6, "Enter the 6-digit code from your authenticator app"),
});
type CodeValues = z.infer<typeof codeSchema>;

interface Factor {
  id: string;
  friendly_name?: string;
}

interface Props {
  enrolledFactor: Factor | null;
  onChanged: () => void;
}

export function MfaEnrollDialog({ enrolledFactor, onChanged }: Props) {
  const supabase = createClient();
  const [open, setOpen] = useState(false);
  // Step 1: qrSvg is set once enroll() succeeds; step 2: waiting for verification code.
  const [qrSvg, setQrSvg] = useState<string | null>(null);
  const [factorId, setFactorId] = useState<string | null>(null);
  const [challengeId, setChallengeId] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<CodeValues>({ resolver: zodResolver(codeSchema) });

  async function startEnroll() {
    const { data, error } = await supabase.auth.mfa.enroll({
      factorType: "totp",
      friendlyName: "Authenticator App",
    });
    if (error || !data) {
      toast.error("Failed to start MFA setup. Please try again.");
      return;
    }
    setFactorId(data.id);
    setQrSvg(data.totp.qr_code);

    // Immediately challenge so we have a challengeId ready for the verify step.
    const { data: challengeData, error: challengeError } = await supabase.auth.mfa.challenge({
      factorId: data.id,
    });
    if (challengeError || !challengeData) {
      toast.error("Failed to start MFA challenge.");
      return;
    }
    setChallengeId(challengeData.id);
  }

  async function onVerify({ code }: CodeValues) {
    if (!factorId || !challengeId) return;
    const { error } = await supabase.auth.mfa.verify({ factorId, challengeId, code });
    if (error) {
      toast.error("Invalid code — please try again.");
      return;
    }
    toast.success("Two-factor authentication enabled.");
    setOpen(false);
    setQrSvg(null);
    reset();
    onChanged();
  }

  async function unenroll() {
    if (!enrolledFactor) return;
    const { error } = await supabase.auth.mfa.unenroll({ factorId: enrolledFactor.id });
    if (error) {
      toast.error("Failed to disable MFA.");
      return;
    }
    toast.success("Two-factor authentication disabled.");
    onChanged();
  }

  function handleOpenChange(next: boolean) {
    if (!next) {
      setQrSvg(null);
      setFactorId(null);
      setChallengeId(null);
      reset();
    }
    setOpen(next);
  }

  if (enrolledFactor) {
    return (
      <div className="flex items-center justify-between rounded-lg border p-4">
        <span className="flex items-center gap-2 text-sm font-medium">
          <ShieldCheck className="size-4 text-green-500" />
          Two-factor authentication is <strong>enabled</strong>
        </span>
        <Button variant="destructive" size="sm" onClick={unenroll}>
          <ShieldOff className="size-4" />
          Disable
        </Button>
      </div>
    );
  }

  return (
    <>
      <div className="flex items-center justify-between rounded-lg border p-4">
        <span className="flex items-center gap-2 text-sm text-muted-foreground">
          <ShieldOff className="size-4" />
          Two-factor authentication is <strong>disabled</strong>
        </span>
        <Button
          size="sm"
          onClick={() => {
            setOpen(true);
            startEnroll();
          }}
        >
          <ShieldCheck className="size-4" />
          Enable
        </Button>
      </div>

      <Dialog open={open} onOpenChange={handleOpenChange}>
        <DialogContent className="sm:max-w-sm">
          <div className="flex flex-col gap-4">
            <div>
              <h2 className="text-lg font-semibold">Set up authenticator app</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Scan the QR code with Google Authenticator, Authy, or any TOTP app, then
                enter the 6-digit code to confirm.
              </p>
            </div>

            {qrSvg ? (
              <>
                <div className="flex justify-center rounded-lg border bg-white p-3">
                  {/* The QR code is an SVG string from Supabase — safe to render as an image */}
                  <Image
                    src={`data:image/svg+xml;utf8,${encodeURIComponent(qrSvg)}`}
                    alt="MFA QR code"
                    width={180}
                    height={180}
                    unoptimized
                  />
                </div>

                <form onSubmit={handleSubmit(onVerify)} className="flex flex-col gap-3" noValidate>
                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="mfa-code">Verification code</Label>
                    <Input
                      id="mfa-code"
                      type="text"
                      inputMode="numeric"
                      autoComplete="one-time-code"
                      maxLength={6}
                      placeholder="123456"
                      {...register("code")}
                    />
                    {errors.code && (
                      <p className="text-xs text-destructive">{errors.code.message}</p>
                    )}
                  </div>
                  <Button type="submit" disabled={isSubmitting}>
                    {isSubmitting ? "Verifying…" : "Verify and enable"}
                  </Button>
                </form>
              </>
            ) : (
              <p className="text-sm text-muted-foreground">Generating QR code…</p>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
