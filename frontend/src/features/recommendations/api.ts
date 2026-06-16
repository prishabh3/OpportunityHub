import { apiClient } from "@/lib/api-client";
import type { OpportunitySummary } from "@/features/opportunities/api";

export interface RecommendedOpportunity extends OpportunitySummary {
  match_score: number;
  matched_skills: string[];
}

export const getRecommendations = (limit = 12) =>
  apiClient.get<RecommendedOpportunity[]>("/api/v1/recommendations", { params: { limit } });
