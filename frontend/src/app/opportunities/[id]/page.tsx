import type { Metadata } from "next";

import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";
import { OpportunityDetail } from "@/features/opportunities/components/opportunity-detail";
import { createClient } from "@/lib/supabase/server";

export const metadata: Metadata = { title: "Opportunity — OpportunityHub" };

export default async function OpportunityDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-3xl px-4 py-10">
        <OpportunityDetail id={id} isAuthenticated={!!user} />
      </main>
      <Footer />
    </>
  );
}
