import type { Metadata } from "next";

import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";
import { OpportunityDetail } from "@/features/opportunities/components/opportunity-detail";

export const metadata: Metadata = { title: "Opportunity — OpportunityHub" };

export default async function OpportunityDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-3xl px-4 py-10">
        <OpportunityDetail id={id} />
      </main>
      <Footer />
    </>
  );
}
