import type { Metadata } from "next";

import { Navbar } from "@/components/layout/navbar";
import { BookmarksList } from "@/features/bookmarks/components/bookmarks-list";

export const metadata: Metadata = { title: "Bookmarks — OpportunityHub" };

export default function BookmarksPage() {
  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-6xl px-4 py-10">
        <div className="mb-8">
          <h1 className="text-3xl font-semibold tracking-tight">Bookmarks</h1>
          <p className="mt-1 text-muted-foreground">Opportunities you&apos;ve saved.</p>
        </div>
        <BookmarksList />
      </main>
    </>
  );
}
