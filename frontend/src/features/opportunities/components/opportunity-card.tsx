import Link from "next/link";
import { CalendarClock, MapPin } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { BookmarkButton } from "@/features/bookmarks/components/bookmark-button";
import {
  EXPERIENCE_LABELS,
  REMOTE_LABELS,
  TYPE_LABELS,
  type OpportunitySummary,
} from "@/features/opportunities/api";

function formatDeadline(iso: string | null): string | null {
  if (!iso) return null;
  const date = new Date(iso);
  const days = Math.ceil((date.getTime() - Date.now()) / (1000 * 60 * 60 * 24));
  const formatted = date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
  if (days < 0) return `Closed · ${formatted}`;
  if (days === 0) return "Due today";
  if (days <= 14) return `${days}d left · ${formatted}`;
  return formatted;
}

export function OpportunityCard({
  opportunity,
  isAuthenticated = false,
  matchScore,
}: {
  opportunity: OpportunitySummary;
  isAuthenticated?: boolean;
  matchScore?: number;
}) {
  const deadline = formatDeadline(opportunity.deadline_at);
  const place =
    opportunity.location ??
    (opportunity.remote_type !== "unspecified" ? REMOTE_LABELS[opportunity.remote_type] : null);

  return (
    <Link href={`/opportunities/${opportunity.id}`} className="group">
      <Card className="flex h-full flex-col gap-3 p-5 transition-colors group-hover:border-primary/50">
        <div className="flex items-center justify-between gap-2">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="secondary">{TYPE_LABELS[opportunity.type]}</Badge>
            {opportunity.experience_level !== "unspecified" && (
              <Badge variant="outline">{EXPERIENCE_LABELS[opportunity.experience_level]}</Badge>
            )}
            {matchScore !== undefined && matchScore > 0 && (
              <Badge className="bg-primary/15 text-primary">{Math.round(matchScore)}% match</Badge>
            )}
          </div>
          <BookmarkButton opportunityId={opportunity.id} isAuthenticated={isAuthenticated} />
        </div>

        <div className="flex-1">
          <h3 className="font-semibold leading-snug tracking-tight group-hover:text-primary">
            {opportunity.title}
          </h3>
          <p className="mt-0.5 text-sm text-muted-foreground">{opportunity.organizer}</p>
        </div>

        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
          {place && (
            <span className="flex items-center gap-1">
              <MapPin className="size-3.5" />
              {place}
            </span>
          )}
          {deadline && (
            <span className="flex items-center gap-1">
              <CalendarClock className="size-3.5" />
              {deadline}
            </span>
          )}
        </div>

        {opportunity.tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {opportunity.tags.slice(0, 3).map((tag) => (
              <Badge key={tag} variant="outline" className="text-xs font-normal">
                {tag}
              </Badge>
            ))}
          </div>
        )}
      </Card>
    </Link>
  );
}
