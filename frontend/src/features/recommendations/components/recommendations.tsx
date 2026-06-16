"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { getRecommendations } from "@/features/recommendations/api";
import { OpportunityCard } from "@/features/opportunities/components/opportunity-card";

export function Recommendations() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["recommendations"],
    queryFn: () => getRecommendations(),
  });

  if (isLoading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <Card key={i} className="p-5">
            <Skeleton className="h-40 w-full" />
          </Card>
        ))}
      </div>
    );
  }

  if (isError || !data || data.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No recommendations yet — browse{" "}
        <Link href="/opportunities" className="text-foreground underline-offset-4 hover:underline">
          opportunities
        </Link>{" "}
        to get started.
      </p>
    );
  }

  const hasMatches = data.some((d) => d.match_score > 0);

  return (
    <div className="flex flex-col gap-4">
      {!hasMatches && (
        <p className="rounded-lg border border-border/60 bg-card/50 px-4 py-3 text-sm text-muted-foreground">
          Add skills and preferences to your{" "}
          <Link href="/profile" className="text-foreground underline-offset-4 hover:underline">
            profile
          </Link>{" "}
          to get personalized matches. Showing recent opportunities for now.
        </p>
      )}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {data.map((rec) => (
          <OpportunityCard
            key={rec.id}
            opportunity={rec}
            isAuthenticated
            matchScore={rec.match_score}
          />
        ))}
      </div>
    </div>
  );
}
