"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ArrowRight } from "lucide-react";

export function Hero({ isAuthenticated }: { isAuthenticated: boolean }) {
  return (
    <section className="relative overflow-hidden px-6 pt-24 pb-20 text-center">
      <div
        className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[480px] bg-[radial-gradient(ellipse_at_top,_var(--color-primary)_0%,_transparent_60%)] opacity-[0.07]"
        aria-hidden
      />

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        className="mx-auto flex max-w-3xl flex-col items-center"
      >
        <span className="mb-6 inline-flex items-center rounded-full border border-border bg-card px-3 py-1 text-xs text-muted-foreground">
          Now tracking 30+ sources, updated hourly
        </span>

        <h1 className="text-4xl font-semibold tracking-tight sm:text-6xl">
          Every opportunity that matters.
          <br />
          <span className="text-muted-foreground">In one place, automatically.</span>
        </h1>

        <p className="mt-6 max-w-xl text-balance text-base text-muted-foreground sm:text-lg">
          OpportunityHub continuously aggregates hackathons, internships, jobs, research
          programs, and competitions from Google, Microsoft, Devpost, MLH, and dozens more —
          then matches them to your profile and notifies you before deadlines slip by.
        </p>

        <div className="mt-10 flex flex-col items-center gap-3 sm:flex-row">
          {isAuthenticated ? (
            <Button size="lg" nativeButton={false} render={<Link href="/dashboard" />}>
              Go to dashboard <ArrowRight className="ml-1 size-4" />
            </Button>
          ) : (
            <Button size="lg" nativeButton={false} render={<Link href="/sign-up" />}>
              Get started for free <ArrowRight className="ml-1 size-4" />
            </Button>
          )}
          <Button
            size="lg"
            variant="outline"
            nativeButton={false}
            render={<Link href="/opportunities" />}
          >
            Browse opportunities
          </Button>
        </div>
      </motion.div>
    </section>
  );
}
