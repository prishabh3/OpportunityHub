"use client";

import { useTrafficPing } from "@/hooks/use-traffic-ping";

export function TrafficProvider({ children }: { children: React.ReactNode }) {
  useTrafficPing();
  return <>{children}</>;
}
