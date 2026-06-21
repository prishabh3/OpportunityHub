"use client";

import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Search } from "lucide-react";

import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { OpportunityCard } from "@/features/opportunities/components/opportunity-card";
import { searchOpportunities } from "@/features/search/api";

export function SearchView({
  isAuthenticated,
  initialQuery = "",
}: {
  isAuthenticated: boolean;
  initialQuery?: string;
}) {
  const [input, setInput] = useState(initialQuery);
  const [q, setQ] = useState(initialQuery.trim());

  useEffect(() => {
    const timer = setTimeout(() => setQ(input.trim()), 300);
    return () => clearTimeout(timer);
  }, [input]);

  const { data, isLoading, isFetching } = useQuery({
    queryKey: ["search", q],
    queryFn: () => searchOpportunities(q),
    enabled: q.length > 0,
  });

  return (
    <div className="flex flex-col gap-6">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 size-5 -translate-y-1/2 text-muted-foreground" />
        <Input
          autoFocus
          className="h-12 pl-11 text-base"
          placeholder="Search opportunities — try 'AI', 'Google', 'open source'…"
          maxLength={200}
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
      </div>

      {q.length === 0 ? (
        <p className="py-12 text-center text-sm text-muted-foreground">
          Start typing to search across all opportunities.
        </p>
      ) : isLoading || isFetching ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Card key={i} className="p-5">
              <Skeleton className="h-40 w-full" />
            </Card>
          ))}
        </div>
      ) : !data || data.length === 0 ? (
        <p className="py-12 text-center text-sm text-muted-foreground">
          No results for &ldquo;{q}&rdquo;. Try different keywords.
        </p>
      ) : (
        <>
          <p className="text-sm text-muted-foreground">
            {data.length} result{data.length === 1 ? "" : "s"} for &ldquo;{q}&rdquo;
          </p>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {data.map((o) => (
              <OpportunityCard key={o.id} opportunity={o} isAuthenticated={isAuthenticated} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
