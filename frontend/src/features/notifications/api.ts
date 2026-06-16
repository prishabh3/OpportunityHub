import { apiClient } from "@/lib/api-client";
import type { Page } from "@/features/opportunities/api";

export interface AppNotification {
  id: string;
  event: string;
  title: string;
  body: string;
  opportunity_id: string | null;
  read_at: string | null;
  created_at: string;
}

export const getNotifications = (cursor?: string, limit = 20) =>
  apiClient.get<Page<AppNotification>>("/api/v1/notifications", { params: { limit, cursor } });

export const getUnreadCount = () =>
  apiClient.get<{ count: number }>("/api/v1/notifications/unread-count");

export const markAllRead = () =>
  apiClient.post<void>("/api/v1/notifications/read-all");

export const markRead = (id: string) =>
  apiClient.post<void>(`/api/v1/notifications/${id}/read`);
