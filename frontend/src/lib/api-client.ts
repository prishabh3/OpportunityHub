import { env } from "@/lib/env";
import { createClient } from "@/lib/supabase/client";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly type?: string,
    public readonly errors?: { field: string; message: string }[]
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type RequestOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
  params?: Record<string, string | number | boolean | undefined>;
};

/**
 * Typed fetch wrapper for the FastAPI backend. Attaches the current Supabase
 * session JWT (if any) and normalizes RFC 9457 problem-details error
 * responses into `ApiError`.
 */
async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { params, body, headers, ...rest } = options;

  const url = new URL(path, env.NEXT_PUBLIC_API_BASE_URL);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined) url.searchParams.set(key, String(value));
    }
  }

  const requestHeaders = new Headers(headers);
  requestHeaders.set("Content-Type", "application/json");

  if (typeof window !== "undefined") {
    const supabase = createClient();
    const { data } = await supabase.auth.getSession();
    if (data.session?.access_token) {
      requestHeaders.set("Authorization", `Bearer ${data.session.access_token}`);
    }
  }

  const response = await fetch(url.toString(), {
    ...rest,
    headers: requestHeaders,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    const problem = await response.json().catch(() => null);
    throw new ApiError(
      problem?.detail ?? response.statusText,
      response.status,
      problem?.type,
      problem?.errors
    );
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const apiClient = {
  get: <T>(path: string, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "GET" }),
  post: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "POST", body }),
  patch: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "PATCH", body }),
  delete: <T>(path: string, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "DELETE" }),
};
