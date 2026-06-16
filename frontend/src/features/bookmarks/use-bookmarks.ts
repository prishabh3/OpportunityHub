"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { addBookmark, getBookmarkIds, removeBookmark } from "@/features/bookmarks/api";

const IDS_KEY = ["bookmark-ids"];

export function useBookmarkIds(enabled: boolean) {
  const { data } = useQuery({
    queryKey: IDS_KEY,
    queryFn: getBookmarkIds,
    enabled,
    staleTime: 60 * 1000,
  });
  return new Set(data ?? []);
}

export function useToggleBookmark() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, bookmarked }: { id: string; bookmarked: boolean }) => {
      if (bookmarked) await removeBookmark(id);
      else await addBookmark(id);
    },
    onMutate: async ({ id, bookmarked }) => {
      await queryClient.cancelQueries({ queryKey: IDS_KEY });
      const previous = queryClient.getQueryData<string[]>(IDS_KEY) ?? [];
      const next = bookmarked ? previous.filter((x) => x !== id) : [...previous, id];
      queryClient.setQueryData(IDS_KEY, next);
      return { previous };
    },
    onError: (_error, _vars, context) => {
      if (context) queryClient.setQueryData(IDS_KEY, context.previous);
      toast.error("Couldn't update bookmark");
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: IDS_KEY });
      queryClient.invalidateQueries({ queryKey: ["bookmarks"] });
    },
  });
}
