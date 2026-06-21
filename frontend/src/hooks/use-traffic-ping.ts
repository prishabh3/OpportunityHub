"use client";

import { useEffect } from "react";
import { apiClient } from "@/lib/api-client";

function getVisitorId(): string {
  const KEY = "oh_vid";
  let id = localStorage.getItem(KEY);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(KEY, id);
  }
  return id;
}

export function useTrafficPing() {
  useEffect(() => {
    const vid = getVisitorId();
    apiClient
      .post(`/api/v1/traffic/ping?visitor_id=${encodeURIComponent(vid)}`)
      .catch(() => {/* best-effort */});
  }, []);
}
