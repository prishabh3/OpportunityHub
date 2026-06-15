import Link from "next/link";
import type { Metadata } from "next";
import { Compass } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";

export const metadata: Metadata = { title: "Opportunities — OpportunityHub" };

export default function OpportunitiesPage() {
  return (
    <>
      <Navbar />
      <main className="mx-auto flex min-h-[60svh] max-w-3xl flex-col items-center justify-center px-4 py-24 text-center">
        <div className="mb-6 flex size-12 items-center justify-center rounded-xl border bg-muted/50">
          <Compass className="size-6 text-primary" />
        </div>
        <h1 className="text-3xl font-semibold tracking-tight">Opportunities are coming</h1>
        <p className="mt-3 max-w-md text-muted-foreground">
          The opportunity feed — hackathons, internships, jobs, research programs, and
          competitions — is being built. It will land with browsing, filters, and search.
        </p>
        <div className="mt-8">
          <Button nativeButton={false} render={<Link href="/sign-up" />}>
            Get notified — create an account
          </Button>
        </div>
      </main>
      <Footer />
    </>
  );
}
