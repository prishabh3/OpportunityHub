import { apiClient } from "@/lib/api-client";

export interface AdminAnalytics {
  opportunities_total: number;
  by_type: Record<string, number>;
  users_total: number;
  bookmarks_total: number;
  notifications_total: number;
}

export interface SourceStat {
  key: string;
  display_name: string;
  opportunity_count: number;
}

export interface ConnectorRun {
  id: string;
  source_key: string;
  status: string;
  started_at: string;
  finished_at: string | null;
  items_found: number;
  items_created: number;
  items_updated: number;
  items_failed: number;
  error_message: string | null;
}

export const getAnalytics = () => apiClient.get<AdminAnalytics>("/api/v1/admin/analytics");
export const getSources = () => apiClient.get<SourceStat[]>("/api/v1/admin/sources");
export const getConnectorRuns = () =>
  apiClient.get<ConnectorRun[]>("/api/v1/admin/connector-runs");
export const triggerIngest = () =>
  apiClient.post<{ results: unknown[] }>("/api/v1/admin/ingest/run");
