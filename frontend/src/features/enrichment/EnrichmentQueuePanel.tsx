import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/api/client";
import { Badge, Button, Card, Spinner } from "@/components/ui";

function statusTone(status: string): string {
  return { completed: "green", running: "amber", pending: "slate", failed: "red" }[status] ?? "slate";
}

const ORDER = ["pending", "running", "completed", "failed"];

/** Live enrichment-queue status with a "Run pending" drain button. */
export function EnrichmentQueuePanel() {
  const qc = useQueryClient();
  const queue = useQuery({
    queryKey: ["enrichment-queue"],
    queryFn: api.enrichmentQueue,
    refetchInterval: 4000,
  });

  const run = useMutation({
    mutationFn: () => api.runEnrichment(25),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["enrichment-queue"] });
      qc.invalidateQueries({ queryKey: ["search"] });
    },
  });

  const counts = queue.data?.counts ?? {};
  const pending = counts.pending ?? 0;

  return (
    <Card>
      <div className="mb-3 flex items-center justify-between">
        <div>
          <h2 className="font-semibold">Enrichment queue</h2>
          <p className="text-xs text-slate-500">
            Bulk-enrich queued companies. Run here, or via the background worker.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {queue.isFetching && <span className="text-xs text-slate-400">refreshing…</span>}
          <Button onClick={() => run.mutate()} disabled={run.isPending || pending === 0}>
            {run.isPending ? "Running…" : `Run pending (${pending})`}
          </Button>
        </div>
      </div>

      <div className="mb-3 flex flex-wrap gap-2">
        {ORDER.map((s) => (
          <Badge key={s} tone={statusTone(s)}>
            {s}: {counts[s] ?? 0}
          </Badge>
        ))}
      </div>

      {queue.isLoading ? (
        <Spinner />
      ) : (queue.data?.recent ?? []).length === 0 ? (
        <p className="py-4 text-center text-sm text-slate-400">
          Queue is empty. Enqueue companies from Discover or a list.
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-xs uppercase text-slate-500">
              <tr>
                <th className="py-1">Job</th>
                <th>Company</th>
                <th>Status</th>
                <th>Attempts</th>
                <th>Error</th>
              </tr>
            </thead>
            <tbody>
              {(queue.data?.recent ?? []).map((j) => (
                <tr key={j.id} className="border-t border-slate-100 dark:border-slate-800/60">
                  <td className="py-1">{j.id}</td>
                  <td>#{j.company_id}</td>
                  <td>
                    <Badge tone={statusTone(j.status)}>{j.status}</Badge>
                  </td>
                  <td>{j.attempts}</td>
                  <td className="max-w-48 truncate text-xs text-red-500">{j.error ?? ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}
