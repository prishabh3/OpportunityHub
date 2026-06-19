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
  type ExperienceLevel,
  type OpportunityCategory,
  type OpportunityFilters,
  type OpportunityType,
  type RemoteType,
} from "@/features/opportunities/api";

type TypeOption = { value: OpportunityType | ""; label: string };

const ALL_TYPE_OPTIONS: TypeOption[] = [
  { value: "", label: "All types" },
  { value: "hackathon", label: "Hackathons" },
  { value: "internship", label: "Internships" },
  { value: "full_time_job", label: "Full-time" },
  { value: "research_program", label: "Research" },
  { value: "competition", label: "Competitions" },
];

const TYPE_OPTIONS_BY_CATEGORY: Record<OpportunityCategory, TypeOption[]> = {
  hackathons: [
    { value: "", label: "All hackathons" },
    { value: "hackathon", label: "Hackathons" },
    { value: "competition", label: "Competitions" },
  ],
  jobs: [
    { value: "", label: "All jobs" },
    { value: "internship", label: "Internships" },
    { value: "full_time_job", label: "Full-time" },
    { value: "research_program", label: "Research" },
  ],
};

const REMOTE_OPTIONS: { value: RemoteType | ""; label: string }[] = [
  { value: "", label: "Anywhere" },
  { value: "remote", label: "Remote" },
  { value: "hybrid", label: "Hybrid" },
  { value: "onsite", label: "Onsite" },
];

const EXPERIENCE_OPTIONS: { value: ExperienceLevel | ""; label: string }[] = [
  { value: "", label: "Any experience" },
  { value: "intern", label: "Intern" },
  { value: "fresher", label: "Fresher (0 yrs)" },
  { value: "mid", label: "Mid-level" },
  { value: "senior", label: "Senior" },
];

const COUNTRY_OPTIONS: { value: string; label: string }[] = [
  { value: "", label: "Anywhere" },
  { value: "India", label: "India" },
  { value: "Global", label: "Remote / Global" },
];

const selectClass =
  "h-9 rounded-lg border border-input bg-transparent px-2.5 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 dark:bg-input/30";

export function OpportunityList({
  isAuthenticated = false,
  category,
}: {
  isAuthenticated?: boolean;
  category?: OpportunityCategory;
}) {
  const [type, setType] = useState<OpportunityType | "">("");
  const [remote, setRemote] = useState<RemoteType | "">("");
  const [experience, setExperience] = useState<ExperienceLevel | "">("");
  const [country, setCountry] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [q, setQ] = useState("");

  const typeOptions = category ? TYPE_OPTIONS_BY_CATEGORY[category] : ALL_TYPE_OPTIONS;
  const showExperience = category === "jobs" || category === undefined;

  // Debounce the search box into the query filter.
  useEffect(() => {
    const timer = setTimeout(() => setQ(searchInput.trim()), 350);
    return () => clearTimeout(timer);
  }, [searchInput]);

  const filters: OpportunityFilters = useMemo(
    () => ({
      category,
      type: type || undefined,
      remote_type: remote || undefined,
      experience_level: experience || undefined,
      country: country || undefined,
      q: q || undefined,
    }),
    [category, type, remote, experience, country, q],
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
          {typeOptions.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
        <select
          className={selectClass}
          value={country}
          onChange={(e) => setCountry(e.target.value)}
        >
          {COUNTRY_OPTIONS.map((o) => (
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
        {showExperience && (
          <select
            className={selectClass}
            value={experience}
            onChange={(e) => setExperience(e.target.value as ExperienceLevel | "")}
          >
            {EXPERIENCE_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        )}
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
              <OpportunityCard
                key={opportunity.id}
                opportunity={opportunity}
                isAuthenticated={isAuthenticated}
              />
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
