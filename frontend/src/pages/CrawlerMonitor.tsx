import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/api/client";
import { ApiError } from "@/api/client";
import { Badge, Button, Card, Spinner } from "@/components/ui";
import type { CrawlJob } from "@/api/types";
import { EnrichmentQueuePanel } from "@/features/enrichment/EnrichmentQueuePanel";

function statusTone(status: string): string {
  return { completed: "green", running: "amber", pending: "slate", failed: "red" }[status] ?? "slate";
}

export function CrawlerMonitorPage() {
  const [hostname, setHostname] = useState("");
  const [error, setError] = useState<string | null>(null);
  const qc = useQueryClient();

  const jobs = useQuery({
    queryKey: ["jobs", "list"],
    queryFn: () => api.listCrawlJobs(1, 50),
    refetchInterval: 5000,
  });

  const crawl = useMutation({
    mutationFn: (host: string) => api.requestCrawl(host),
    onSuccess: () => {
      setHostname("");
      setError(null);
      qc.invalidateQueries({ queryKey: ["jobs"] });
    },
    onError: (e) => setError(e instanceof ApiError ? e.message : "Request failed"),
  });

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Crawler Monitor</h1>

      <EnrichmentQueuePanel />

      <Card>
        <form
          className="flex flex-wrap items-center gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            if (hostname.trim()) crawl.mutate(hostname.trim());
          }}
        >
          <input
            value={hostname}
            onChange={(e) => setHostname(e.target.value)}
            placeholder="hostname to crawl (must belong to a company), e.g. acme.com"
            className="min-w-64 flex-1 rounded-lg border border-slate-300 bg-transparent px-3 py-1.5 text-sm dark:border-slate-700"
          />
          <Button type="submit" disabled={crawl.isPending}>
            {crawl.isPending ? "Queuing…" : "Request crawl"}
          </Button>
        </form>
        {error && <p className="mt-2 text-sm text-red-500">{error}</p>}
      </Card>

      <Card>
        <div className="mb-2 flex items-center justify-between">
          <h2 className="font-semibold">Jobs</h2>
          {jobs.isFetching && <span className="text-xs text-slate-400">refreshing…</span>}
        </div>
        {jobs.isLoading ? (
          <Spinner />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs uppercase text-slate-500">
                <tr>
                  <th className="py-1">ID</th>
                  <th>Hostname</th>
                  <th>Status</th>
                  <th>Pages</th>
                  <th>Attempts</th>
                </tr>
              </thead>
              <tbody>
                {(jobs.data?.items ?? []).map((j: CrawlJob) => (
                  <tr key={j.id} className="border-t border-slate-100 dark:border-slate-800/60">
                    <td className="py-1">{j.id}</td>
                    <td>{j.hostname}</td>
                    <td>
                      <Badge tone={statusTone(j.status)}>{j.status}</Badge>
                    </td>
                    <td>{j.pages_crawled}</td>
                    <td>{j.attempts}</td>
                  </tr>
                ))}
                {(jobs.data?.items ?? []).length === 0 && (
                  <tr>
                    <td colSpan={5} className="py-6 text-center text-slate-400">
                      No crawl jobs yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
