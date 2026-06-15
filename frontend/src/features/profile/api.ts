import { apiClient } from "@/lib/api-client";

export type RemoteType = "remote" | "hybrid" | "onsite" | "unspecified";

export interface Profile {
  id: string;
  full_name: string | null;
  preferred_role: string | null;
  preferred_companies: string[];
  preferred_countries: string[];
  preferred_remote: RemoteType | null;
  expected_graduation: string | null; // ISO date (YYYY-MM-DD)
  weekly_digest_enabled: boolean;
  timezone: string;
  skills: string[];
}

export type ProfileUpdate = Partial<Omit<Profile, "id">>;

export const getProfile = () => apiClient.get<Profile>("/api/v1/me");

export const updateProfile = (data: ProfileUpdate) =>
  apiClient.patch<Profile>("/api/v1/me", data);
