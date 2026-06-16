import { apiClient } from "@/lib/api-client";
import type { OpportunitySummary, Page } from "@/features/opportunities/api";

export interface Bookmark {
  id: string;
  opportunity_id: string;
  notes: string | null;
  tags: string[];
  created_at: string;
  opportunity: OpportunitySummary;
}

export const getBookmarks = (cursor?: string, limit = 12) =>
  apiClient.get<Page<Bookmark>>("/api/v1/bookmarks", { params: { limit, cursor } });

export const getBookmarkIds = () => apiClient.get<string[]>("/api/v1/bookmarks/ids");

export const addBookmark = (opportunityId: string) =>
  apiClient.post<Bookmark>("/api/v1/bookmarks", { opportunity_id: opportunityId });

export const removeBookmark = (opportunityId: string) =>
  apiClient.delete<void>(`/api/v1/bookmarks/${opportunityId}`);
