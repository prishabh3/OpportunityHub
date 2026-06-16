import type { Metadata } from "next";

import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";
import { SearchView } from "@/features/search/components/search-view";
import { createClient } from "@/lib/supabase/server";

export const metadata: Metadata = { title: "Search — OpportunityHub" };

export default async function SearchPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string }>;
}) {
  const { q } = await searchParams;
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-6xl px-4 py-10">
        <h1 className="mb-6 text-3xl font-semibold tracking-tight">Search</h1>
        <SearchView isAuthenticated={!!user} initialQuery={q ?? ""} />
      </main>
      <Footer />
    </>
  );
}
