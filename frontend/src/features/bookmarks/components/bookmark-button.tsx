"use client";

import { useRouter } from "next/navigation";
import { Bookmark, BookmarkCheck } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useBookmarkIds, useToggleBookmark } from "@/features/bookmarks/use-bookmarks";

interface BookmarkButtonProps {
  opportunityId: string;
  isAuthenticated: boolean;
  withLabel?: boolean;
}

export function BookmarkButton({
  opportunityId,
  isAuthenticated,
  withLabel = false,
}: BookmarkButtonProps) {
  const router = useRouter();
  const ids = useBookmarkIds(isAuthenticated);
  const toggle = useToggleBookmark();
  const bookmarked = ids.has(opportunityId);

  function handleClick(e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    if (!isAuthenticated) {
      router.push(`/sign-in?redirect=/opportunities/${opportunityId}`);
      return;
    }
    toggle.mutate({ id: opportunityId, bookmarked });
  }

  const Icon = bookmarked ? BookmarkCheck : Bookmark;

  if (withLabel) {
    return (
      <Button variant={bookmarked ? "secondary" : "outline"} size="lg" onClick={handleClick}>
        <Icon className="size-4" />
        {bookmarked ? "Saved" : "Save"}
      </Button>
    );
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      aria-label={bookmarked ? "Remove bookmark" : "Add bookmark"}
      className={cn(
        "flex size-8 items-center justify-center rounded-md border border-border bg-background/70 text-muted-foreground backdrop-blur transition-colors hover:text-foreground",
        bookmarked && "border-primary/40 text-primary",
      )}
    >
      <Icon className="size-4" />
    </button>
  );
}
