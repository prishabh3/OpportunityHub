import { apiClient } from "@/lib/api-client";

export type OpportunityType =
  | "hackathon"
  | "internship"
  | "full_time_job"
  | "research_program"
  | "competition";
export type RemoteType = "remote" | "hybrid" | "onsite" | "unspecified";
export type DifficultyLevel = "beginner" | "intermediate" | "advanced" | "unspecified";

export interface OpportunitySummary {
  id: string;
  type: OpportunityType;
  status: string;
  title: string;
  organizer: string;
  location: string | null;
  country: string | null;
  remote_type: RemoteType;
  difficulty: DifficultyLevel;
  deadline_at: string | null;
  starts_at: string | null;
  apply_url: string;
  banner_url: string | null;
  tags: string[];
}

export interface OpportunityDetail extends OpportunitySummary {
  description: string | null;
  source_url: string | null;
  posted_at: string | null;
  ends_at: string | null;
  details: Record<string, unknown>;
  source: { key: string; display_name: string };
}

export interface Page<T> {
  data: T[];
  page: { next_cursor: string | null; has_more: boolean; limit: number };
}

export interface OpportunityFilters {
  type?: OpportunityType;
  remote_type?: RemoteType;
  country?: string;
  q?: string;
}

export function getOpportunities(
  filters: OpportunityFilters,
  cursor?: string,
  limit = 12,
) {
  const params: Record<string, string | number | undefined> = {
    ...filters,
    limit,
    cursor,
  };
  return apiClient.get<Page<OpportunitySummary>>("/api/v1/opportunities", { params });
}

export const getOpportunity = (id: string) =>
  apiClient.get<OpportunityDetail>(`/api/v1/opportunities/${id}`);

export const TYPE_LABELS: Record<OpportunityType, string> = {
  hackathon: "Hackathon",
  internship: "Internship",
  full_time_job: "Full-time",
  research_program: "Research",
  competition: "Competition",
};

export const REMOTE_LABELS: Record<RemoteType, string> = {
  remote: "Remote",
  hybrid: "Hybrid",
  onsite: "Onsite",
  unspecified: "—",
};
