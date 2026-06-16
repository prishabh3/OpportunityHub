"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  getAnalytics,
  getConnectorRuns,
  getSources,
  triggerIngest,
} from "@/features/admin/api";

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <Card className="p-4">
      <p className="text-xs uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="mt-1 text-2xl font-semibold">{value}</p>
    </Card>
  );
}

const STATUS_STYLES: Record<string, string> = {
  success: "bg-green-500/15 text-green-600 dark:text-green-400",
  partial: "bg-yellow-500/15 text-yellow-600 dark:text-yellow-400",
  failed: "bg-destructive/15 text-destructive",
  running: "bg-muted text-muted-foreground",
};

export function AdminDashboard() {
  const queryClient = useQueryClient();
  const analytics = useQuery({ queryKey: ["admin", "analytics"], queryFn: getAnalytics });
  const sources = useQuery({ queryKey: ["admin", "sources"], queryFn: getSources });
  const runs = useQuery({ queryKey: ["admin", "runs"], queryFn: getConnectorRuns });

  const ingest = useMutation({
    mutationFn: triggerIngest,
    onSuccess: () => {
      toast.success("Ingestion complete");
      queryClient.invalidateQueries({ queryKey: ["admin"] });
    },
    onError: () => toast.error("Ingestion failed"),
  });

  if (analytics.isLoading) {
    return <Skeleton className="h-64 w-full" />;
  }

  const a = analytics.data;

  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Overview</h2>
        <Button onClick={() => ingest.mutate()} disabled={ingest.isPending}>
          <RefreshCw className={ingest.isPending ? "size-4 animate-spin" : "size-4"} />
          {ingest.isPending ? "Running…" : "Run ingestion"}
        </Button>
      </div>

      {a && (
        <div className="grid gap-3 grid-cols-2 lg:grid-cols-4">
          <Stat label="Opportunities" value={a.opportunities_total} />
          <Stat label="Users" value={a.users_total} />
          <Stat label="Bookmarks" value={a.bookmarks_total} />
          <Stat label="Notifications" value={a.notifications_total} />
        </div>
      )}

      {a && (
        <section>
          <h3 className="mb-3 text-sm font-semibold text-muted-foreground">By type</h3>
          <div className="flex flex-wrap gap-2">
            {Object.entries(a.by_type).map(([type, count]) => (
              <Badge key={type} variant="secondary">
                {type.replace(/_/g, " ")}: {count}
              </Badge>
            ))}
          </div>
        </section>
      )}

      <section>
        <h3 className="mb-3 text-sm font-semibold text-muted-foreground">Sources</h3>
        <Card className="divide-y p-0">
          {sources.data?.map((s) => (
            <div key={s.key} className="flex items-center justify-between px-4 py-2.5 text-sm">
              <span className="font-medium">{s.display_name}</span>
              <span className="text-muted-foreground">{s.opportunity_count} opportunities</span>
            </div>
          ))}
        </Card>
      </section>

      <section>
        <h3 className="mb-3 text-sm font-semibold text-muted-foreground">Recent connector runs</h3>
        <Card className="divide-y p-0">
          {runs.data?.length === 0 && (
            <p className="px-4 py-3 text-sm text-muted-foreground">No runs yet.</p>
          )}
          {runs.data?.map((r) => (
            <div key={r.id} className="flex items-center justify-between gap-3 px-4 py-2.5 text-sm">
              <span className="flex items-center gap-2">
                <Badge className={STATUS_STYLES[r.status] ?? ""}>{r.status}</Badge>
                <span className="font-medium">{r.source_key}</span>
              </span>
              <span className="text-xs text-muted-foreground">
                +{r.items_created} new · {r.items_updated} updated · {r.items_failed} failed
                {" · "}
                {new Date(r.started_at).toLocaleString()}
              </span>
            </div>
          ))}
        </Card>
      </section>
    </div>
  );
}
