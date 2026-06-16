"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { ArrowLeft, ArrowUpRight, CalendarClock, MapPin, Signal } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError } from "@/lib/api-client";
import { BookmarkButton } from "@/features/bookmarks/components/bookmark-button";
import { getOpportunity, REMOTE_LABELS, TYPE_LABELS } from "@/features/opportunities/api";

function formatDate(iso: string | null): string | null {
  if (!iso) return null;
  return new Date(iso).toLocaleDateString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function OpportunityDetail({
  id,
  isAuthenticated,
}: {
  id: string;
  isAuthenticated: boolean;
}) {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["opportunity", id],
    queryFn: () => getOpportunity(id),
  });

  if (isLoading) {
    return (
      <div className="flex flex-col gap-4">
        <Skeleton className="h-8 w-2/3" />
        <Skeleton className="h-5 w-1/3" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  if (isError || !data) {
    const notFound = error instanceof ApiError && error.status === 404;
    return (
      <div className="py-16 text-center">
        <p className="font-medium">{notFound ? "Opportunity not found" : "Something went wrong"}</p>
        <p className="mt-1 text-sm text-muted-foreground">
          {notFound
            ? "It may have been removed or the link is incorrect."
            : error instanceof ApiError
              ? error.message
              : "Please try again."}
        </p>
        <Button
          variant="outline"
          className="mt-6"
          nativeButton={false}
          render={<Link href="/opportunities" />}
        >
          Back to opportunities
        </Button>
      </div>
    );
  }

  const dates: { label: string; value: string | null }[] = [
    { label: "Deadline", value: formatDate(data.deadline_at) },
    { label: "Starts", value: formatDate(data.starts_at) },
    { label: "Ends", value: formatDate(data.ends_at) },
  ].filter((d) => d.value);

  return (
    <div className="flex flex-col gap-6">
      <Link
        href="/opportunities"
        className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="size-4" />
        All opportunities
      </Link>

      <div className="flex flex-col gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="secondary">{TYPE_LABELS[data.type]}</Badge>
          {data.remote_type !== "unspecified" && (
            <Badge variant="outline">{REMOTE_LABELS[data.remote_type]}</Badge>
          )}
          {data.difficulty !== "unspecified" && (
            <Badge variant="outline" className="capitalize">
              {data.difficulty}
            </Badge>
          )}
        </div>
        <h1 className="text-3xl font-semibold tracking-tight">{data.title}</h1>
        <p className="text-muted-foreground">{data.organizer}</p>
      </div>

      <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-muted-foreground">
        {data.location && (
          <span className="flex items-center gap-1.5">
            <MapPin className="size-4" />
            {data.location}
            {data.country ? `, ${data.country}` : ""}
          </span>
        )}
        {dates.map((d) => (
          <span key={d.label} className="flex items-center gap-1.5">
            <CalendarClock className="size-4" />
            {d.label}: {d.value}
          </span>
        ))}
        <span className="flex items-center gap-1.5">
          <Signal className="size-4" />
          via {data.source.display_name}
        </span>
      </div>

      <div className="flex flex-wrap gap-3">
        <Button
          size="lg"
          nativeButton={false}
          render={<a href={data.apply_url} target="_blank" rel="noopener noreferrer" />}
        >
          Apply now
          <ArrowUpRight className="size-4" />
        </Button>
        <BookmarkButton opportunityId={data.id} isAuthenticated={isAuthenticated} withLabel />
      </div>

      {data.description && (
        <>
          <Separator />
          <p className="whitespace-pre-line leading-relaxed text-foreground/90">
            {data.description}
          </p>
        </>
      )}

      {data.tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {data.tags.map((tag) => (
            <Badge key={tag} variant="outline" className="font-normal">
              {tag}
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
}
