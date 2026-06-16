import { apiClient } from "@/lib/api-client";
import type { OpportunitySummary } from "@/features/opportunities/api";

export const searchOpportunities = (q: string, limit = 30) =>
  apiClient.get<OpportunitySummary[]>("/api/v1/search", { params: { q, limit } });
