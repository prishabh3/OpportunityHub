"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { Controller, useForm } from "react-hook-form";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { TagInput } from "@/components/ui/tag-input";
import { ApiError } from "@/lib/api-client";
import {
  getProfile,
  updateProfile,
  type Profile,
  type ProfileUpdate,
  type RemoteType,
} from "@/features/profile/api";
import { COUNTRY_SUGGESTIONS, SKILL_SUGGESTIONS } from "@/features/profile/constants";

interface FormValues {
  full_name: string;
  preferred_role: string;
  preferred_remote: RemoteType | "";
  expected_graduation: string;
  timezone: string;
  weekly_digest_enabled: boolean;
  countries: string[];
  skills: string[];
}

const emptyToNull = (value: string) => {
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
};

function toFormValues(profile: Profile): FormValues {
  return {
    full_name: profile.full_name ?? "",
    preferred_role: profile.preferred_role ?? "",
    preferred_remote: profile.preferred_remote ?? "",
    expected_graduation: profile.expected_graduation ?? "",
    timezone: profile.timezone ?? "UTC",
    weekly_digest_enabled: profile.weekly_digest_enabled ?? true,
    countries: profile.preferred_countries ?? [],
    skills: profile.skills ?? [],
  };
}

function toUpdate(values: FormValues): ProfileUpdate {
  return {
    full_name: emptyToNull(values.full_name),
    preferred_role: emptyToNull(values.preferred_role),
    preferred_remote: values.preferred_remote === "" ? null : values.preferred_remote,
    expected_graduation: emptyToNull(values.expected_graduation),
    timezone: values.timezone.trim() || "UTC",
    weekly_digest_enabled: values.weekly_digest_enabled,
    preferred_countries: values.countries,
    skills: values.skills,
  };
}

export function ProfileForm() {
  const queryClient = useQueryClient();
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["profile"],
    queryFn: getProfile,
  });

  const { register, handleSubmit, reset, control, formState } = useForm<FormValues>({
    defaultValues: {
      full_name: "",
      preferred_role: "",
      preferred_remote: "",
      expected_graduation: "",
      timezone: "UTC",
      weekly_digest_enabled: true,
      countries: [],
      skills: [],
    },
  });

  useEffect(() => {
    if (data) reset(toFormValues(data));
  }, [data, reset]);

  const mutation = useMutation({
    mutationFn: (values: FormValues) => updateProfile(toUpdate(values)),
    onSuccess: (updated) => {
      queryClient.setQueryData(["profile"], updated);
      reset(toFormValues(updated));
      toast.success("Profile saved");
    },
    onError: (err) => {
      toast.error(err instanceof ApiError ? err.message : "Failed to save profile");
    },
  });

  if (isLoading) {
    return (
      <div className="flex flex-col gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <p className="text-sm text-destructive">
        {error instanceof ApiError ? error.message : "Couldn't load your profile."}
      </p>
    );
  }

  return (
    <form
      onSubmit={handleSubmit((values) => mutation.mutate(values))}
      className="flex flex-col gap-6"
    >
      <Field label="Full name" htmlFor="full_name">
        <Input id="full_name" placeholder="Ada Lovelace" {...register("full_name")} />
      </Field>

      <Field label="Preferred role" htmlFor="preferred_role">
        <Input
          id="preferred_role"
          placeholder="Software Engineer, ML Engineer…"
          {...register("preferred_role")}
        />
      </Field>

      <Field label="Skills" htmlFor="skills" hint="Type to search or add your own, then Enter">
        <Controller
          control={control}
          name="skills"
          render={({ field }) => (
            <TagInput
              id="skills"
              value={field.value}
              onChange={field.onChange}
              suggestions={SKILL_SUGGESTIONS}
              placeholder="Python, React, SQL…"
            />
          )}
        />
      </Field>

      <Field label="Preferred countries" htmlFor="countries">
        <Controller
          control={control}
          name="countries"
          render={({ field }) => (
            <TagInput
              id="countries"
              value={field.value}
              onChange={field.onChange}
              suggestions={COUNTRY_SUGGESTIONS}
              placeholder="India, Germany, United States…"
            />
          )}
        />
      </Field>

      <Field label="Work preference" htmlFor="preferred_remote">
        <select
          id="preferred_remote"
          className="h-8 w-full rounded-lg border border-input bg-transparent px-2.5 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 dark:bg-input/30"
          {...register("preferred_remote")}
        >
          <option value="">No preference</option>
          <option value="remote">Remote</option>
          <option value="hybrid">Hybrid</option>
          <option value="onsite">Onsite</option>
          <option value="unspecified">Unspecified</option>
        </select>
      </Field>

      <Field label="Expected graduation" htmlFor="expected_graduation">
        <Input id="expected_graduation" type="date" {...register("expected_graduation")} />
      </Field>

      <Field label="Timezone" htmlFor="timezone">
        <Input id="timezone" placeholder="UTC, Asia/Kolkata…" {...register("timezone")} />
      </Field>

      <label className="flex items-center gap-2 text-sm">
        <input type="checkbox" className="size-4" {...register("weekly_digest_enabled")} />
        Send me a weekly digest of new opportunities
      </label>

      <div className="flex items-center gap-3">
        <Button type="submit" disabled={mutation.isPending || !formState.isDirty}>
          {mutation.isPending ? "Saving…" : "Save changes"}
        </Button>
        {formState.isDirty && !mutation.isPending && (
          <span className="text-xs text-muted-foreground">Unsaved changes</span>
        )}
      </div>
    </form>
  );
}

function Field({
  label,
  htmlFor,
  hint,
  children,
}: {
  label: string;
  htmlFor: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <Label htmlFor={htmlFor}>{label}</Label>
      {children}
      {hint && <p className="text-xs text-muted-foreground">{hint}</p>}
    </div>
  );
}
