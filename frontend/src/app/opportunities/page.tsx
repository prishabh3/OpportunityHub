import type { Metadata } from "next";

import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";
import { OpportunityList } from "@/features/opportunities/components/opportunity-list";

export const metadata: Metadata = { title: "Opportunities — OpportunityHub" };

export default function OpportunitiesPage() {
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
        <OpportunityList />
      </main>
      <Footer />
    </>
  );
}
