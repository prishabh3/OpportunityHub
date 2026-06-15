"use client";

import { useInfiniteQuery } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { Search } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError } from "@/lib/api-client";
import { OpportunityCard } from "@/features/opportunities/components/opportunity-card";
import {
  getOpportunities,
  type OpportunityFilters,
  type OpportunityType,
  type RemoteType,
} from "@/features/opportunities/api";

const TYPE_OPTIONS: { value: OpportunityType | ""; label: string }[] = [
  { value: "", label: "All types" },
  { value: "hackathon", label: "Hackathons" },
  { value: "internship", label: "Internships" },
  { value: "full_time_job", label: "Full-time" },
  { value: "research_program", label: "Research" },
  { value: "competition", label: "Competitions" },
];

const REMOTE_OPTIONS: { value: RemoteType | ""; label: string }[] = [
  { value: "", label: "Anywhere" },
  { value: "remote", label: "Remote" },
  { value: "hybrid", label: "Hybrid" },
  { value: "onsite", label: "Onsite" },
];

const selectClass =
  "h-9 rounded-lg border border-input bg-transparent px-2.5 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 dark:bg-input/30";

export function OpportunityList() {
  const [type, setType] = useState<OpportunityType | "">("");
  const [remote, setRemote] = useState<RemoteType | "">("");
  const [searchInput, setSearchInput] = useState("");
  const [q, setQ] = useState("");

  // Debounce the search box into the query filter.
  useEffect(() => {
    const timer = setTimeout(() => setQ(searchInput.trim()), 350);
    return () => clearTimeout(timer);
  }, [searchInput]);

  const filters: OpportunityFilters = useMemo(
    () => ({
      type: type || undefined,
      remote_type: remote || undefined,
      q: q || undefined,
    }),
    [type, remote, q],
  );

  const { data, isLoading, isError, error, fetchNextPage, hasNextPage, isFetchingNextPage } =
    useInfiniteQuery({
      queryKey: ["opportunities", filters],
      queryFn: ({ pageParam }) => getOpportunities(filters, pageParam),
      initialPageParam: undefined as string | undefined,
      getNextPageParam: (last) => last.page.next_cursor ?? undefined,
    });

  const items = data?.pages.flatMap((p) => p.data) ?? [];

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search className="absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            className="h-9 pl-8"
            placeholder="Search opportunities…"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
          />
        </div>
        <select
          className={selectClass}
          value={type}
          onChange={(e) => setType(e.target.value as OpportunityType | "")}
        >
          {TYPE_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
        <select
          className={selectClass}
          value={remote}
          onChange={(e) => setRemote(e.target.value as RemoteType | "")}
        >
          {REMOTE_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      </div>

      {isError ? (
        <p className="py-12 text-center text-sm text-destructive">
          {error instanceof ApiError ? error.message : "Couldn't load opportunities."}
        </p>
      ) : isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Card key={i} className="p-5">
              <Skeleton className="h-40 w-full" />
            </Card>
          ))}
        </div>
      ) : items.length === 0 ? (
        <div className="py-16 text-center">
          <p className="font-medium">No opportunities match your filters</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Try clearing the search or choosing a different type.
          </p>
        </div>
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {items.map((opportunity) => (
              <OpportunityCard key={opportunity.id} opportunity={opportunity} />
            ))}
          </div>
          {hasNextPage && (
            <div className="flex justify-center">
              <Button
                variant="outline"
                onClick={() => fetchNextPage()}
                disabled={isFetchingNextPage}
              >
                {isFetchingNextPage ? "Loading…" : "Load more"}
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
