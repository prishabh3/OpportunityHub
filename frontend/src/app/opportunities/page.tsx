import type { Metadata } from "next";

import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";
import { OpportunityList } from "@/features/opportunities/components/opportunity-list";
import type { OpportunityType } from "@/features/opportunities/api";
import { createClient } from "@/lib/supabase/server";

export const metadata: Metadata = { title: "Opportunities — OpportunityHub" };

const VALID_TYPES: OpportunityType[] = [
  "hackathon",
  "internship",
  "full_time_job",
  "research_program",
  "competition",
];

export default async function OpportunitiesPage({
  searchParams,
}: {
  searchParams: Promise<{ type?: string }>;
}) {
  const { type } = await searchParams;
  const initialType = VALID_TYPES.includes(type as OpportunityType)
    ? (type as OpportunityType)
    : "";

  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-6xl px-4 py-10">
        <div className="mb-8">
          <h1 className="text-3xl font-semibold tracking-tight">Opportunities</h1>
          <p className="mt-1 text-muted-foreground">
            Hackathons, internships, jobs, research programs, and competitions — in one place.
          </p>
        </div>
        {/* key re-mounts the list when the type query changes (e.g. nav links) */}
        <OpportunityList key={initialType} isAuthenticated={!!user} initialType={initialType} />
      </main>
      <Footer />
    </>
  );
}
