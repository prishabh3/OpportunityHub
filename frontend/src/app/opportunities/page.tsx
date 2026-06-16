import type { Metadata } from "next";

import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";
import { OpportunityList } from "@/features/opportunities/components/opportunity-list";
import type { OpportunityCategory } from "@/features/opportunities/api";
import { createClient } from "@/lib/supabase/server";

export const metadata: Metadata = { title: "Opportunities — OpportunityHub" };

const CATEGORY_COPY: Record<OpportunityCategory, { title: string; subtitle: string }> = {
  hackathons: {
    title: "Hackathons",
    subtitle: "Hackathons and competitions to build, ship, and win.",
  },
  jobs: {
    title: "Jobs",
    subtitle: "Internships, full-time roles, and research programs.",
  },
};

export default async function OpportunitiesPage({
  searchParams,
}: {
  searchParams: Promise<{ category?: string }>;
}) {
  const { category: raw } = await searchParams;
  const category: OpportunityCategory | undefined =
    raw === "hackathons" || raw === "jobs" ? raw : undefined;

  const copy = category
    ? CATEGORY_COPY[category]
    : {
        title: "Opportunities",
        subtitle: "Hackathons, internships, jobs, research programs, and competitions.",
      };

  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-6xl px-4 py-10">
        <div className="mb-8">
          <h1 className="text-3xl font-semibold tracking-tight">{copy.title}</h1>
          <p className="mt-1 text-muted-foreground">{copy.subtitle}</p>
        </div>
        {/* key re-mounts the list when the category changes (nav between sections) */}
        <OpportunityList key={category ?? "all"} isAuthenticated={!!user} category={category} />
      </main>
      <Footer />
    </>
  );
}
