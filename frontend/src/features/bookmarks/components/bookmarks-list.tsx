"use client";

import { useInfiniteQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Bookmark } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError } from "@/lib/api-client";
import { getBookmarks } from "@/features/bookmarks/api";
import { OpportunityCard } from "@/features/opportunities/components/opportunity-card";

export function BookmarksList() {
  const { data, isLoading, isError, error, fetchNextPage, hasNextPage, isFetchingNextPage } =
    useInfiniteQuery({
      queryKey: ["bookmarks"],
      queryFn: ({ pageParam }) => getBookmarks(pageParam),
      initialPageParam: undefined as string | undefined,
      getNextPageParam: (last) => last.page.next_cursor ?? undefined,
    });

  const items = data?.pages.flatMap((p) => p.data) ?? [];

  if (isError) {
    return (
      <p className="py-12 text-center text-sm text-destructive">
        {error instanceof ApiError ? error.message : "Couldn't load your bookmarks."}
      </p>
    );
  }

  if (isLoading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <Card key={i} className="p-5">
            <Skeleton className="h-40 w-full" />
          </Card>
        ))}
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center py-16 text-center">
        <div className="mb-4 flex size-12 items-center justify-center rounded-xl border bg-muted/50">
          <Bookmark className="size-6 text-muted-foreground" />
        </div>
        <p className="font-medium">No bookmarks yet</p>
        <p className="mt-1 text-sm text-muted-foreground">
          Save opportunities you&apos;re interested in and they&apos;ll show up here.
        </p>
        <Button className="mt-6" nativeButton={false} render={<Link href="/opportunities" />}>
          Browse opportunities
        </Button>
      </div>
    );
  }

  return (
    <>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((bookmark) => (
          <OpportunityCard key={bookmark.id} opportunity={bookmark.opportunity} isAuthenticated />
        ))}
      </div>
      {hasNextPage && (
        <div className="mt-6 flex justify-center">
          <Button variant="outline" onClick={() => fetchNextPage()} disabled={isFetchingNextPage}>
            {isFetchingNextPage ? "Loading…" : "Load more"}
          </Button>
        </div>
      )}
    </>
  );
}
