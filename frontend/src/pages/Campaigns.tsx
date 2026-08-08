import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api, ApiError } from "@/api/client";
import type { Lead, LeadCampaign } from "@/api/types";
import { Badge, Button, Card, Spinner } from "@/components/ui";

/** Split a comma/newline separated input into a clean, de-duplicated list. */
function splitList(raw: string): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const part of raw.split(/[,\n]/)) {
    const trimmed = part.trim();
    if (trimmed && !seen.has(trimmed.toLowerCase())) {
      seen.add(trimmed.toLowerCase());
      out.push(trimmed);
    }
  }
  return out;
}

function relativeTime(iso: string | null): string {
  if (!iso) return "never";
  const then = new Date(iso).getTime();
  const mins = Math.round((Date.now() - then) / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.round(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.round(hours / 24)}d ago`;
}

export function CampaignsPage() {
  const qc = useQueryClient();
  const [filter, setFilter] = useState<number | "all">("all");

  const campaigns = useQuery({ queryKey: ["campaigns"], queryFn: api.listCampaigns });
  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["campaigns"] });
    qc.invalidateQueries({ queryKey: ["leads"] });
  };

  const runDue = useMutation({
    mutationFn: () => api.runDueCampaigns(),
    onSuccess: invalidate,
  });

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h1 className="text-2xl font-bold">Lead campaigns</h1>
          <p className="max-w-2xl text-sm text-slate-500">
            Describe who you sell to as business types × locations. The engine sweeps that grid on a
            rotation and brings back only businesses you haven't seen before — continuously, no paid
            APIs. Run <code className="text-xs">scripts/lead_engine.py</code> to keep it going
            hands-off, or trigger a cycle here.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {runDue.isSuccess && (
            <span className="text-xs text-green-600">+{runDue.data.new_leads} new</span>
          )}
          <Button onClick={() => runDue.mutate()} disabled={runDue.isPending}>
            {runDue.isPending ? "Running…" : "Run all due"}
          </Button>
        </div>
      </div>

      <CreateCampaignForm onCreated={invalidate} />

      {campaigns.isLoading ? (
        <Spinner />
      ) : (campaigns.data ?? []).length === 0 ? (
        <Card>
          <p className="p-6 text-center text-sm text-slate-400">
            No campaigns yet. Create one above to start a continuous flow of leads.
          </p>
        </Card>
      ) : (
        <div className="space-y-3">
          {(campaigns.data ?? []).map((c) => (
            <CampaignCard key={c.id} campaign={c} onChanged={invalidate} />
          ))}
        </div>
      )}

      <LeadInbox
        campaigns={campaigns.data ?? []}
        filter={filter}
        onFilter={setFilter}
      />
    </div>
  );
}

function CreateCampaignForm({ onCreated }: { onCreated: () => void }) {
  const [name, setName] = useState("");
  const [categories, setCategories] = useState("");
  const [locations, setLocations] = useState("");
  const [interval, setInterval] = useState(60);
  const [perRun, setPerRun] = useState(50);
  const [autoEnrich, setAutoEnrich] = useState(true);

  const create = useMutation({
    mutationFn: () =>
      api.createCampaign({
        name: name.trim(),
        categories: splitList(categories),
        locations: splitList(locations),
        interval_minutes: interval,
        per_run_limit: perRun,
        auto_enrich: autoEnrich,
      }),
    onSuccess: () => {
      setName("");
      setCategories("");
      setLocations("");
      onCreated();
    },
  });

  const cats = splitList(categories);
  const locs = splitList(locations);
  const gridSize = cats.length * locs.length;
  const valid = name.trim() !== "" && cats.length > 0 && locs.length > 0;

  const inputClass =
    "w-full rounded-lg border border-slate-300 bg-transparent px-3 py-1.5 text-sm dark:border-slate-700";

  return (
    <Card>
      <form
        className="space-y-3"
        onSubmit={(e) => {
          e.preventDefault();
          if (valid) create.mutate();
        }}
      >
        <div>
          <label className="mb-1 block text-sm font-medium">Campaign name</label>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Sydney dental clinics"
            className={inputClass}
          />
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-sm font-medium">Business types</label>
            <input
              value={categories}
              onChange={(e) => setCategories(e.target.value)}
              placeholder="dentist, orthodontist"
              className={inputClass}
            />
            <p className="mt-1 text-xs text-slate-500">Comma-separated.</p>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Locations</label>
            <input
              value={locations}
              onChange={(e) => setLocations(e.target.value)}
              placeholder="Sydney, Melbourne, Brisbane"
              className={inputClass}
            />
            <p className="mt-1 text-xs text-slate-500">Comma-separated.</p>
          </div>
        </div>
        <div className="grid gap-3 sm:grid-cols-3">
          <div>
            <label className="mb-1 block text-sm font-medium">Interval (minutes)</label>
            <input
              type="number"
              min={1}
              value={interval}
              onChange={(e) => setInterval(Math.max(1, Number(e.target.value)))}
              className={inputClass}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Per-run limit</label>
            <input
              type="number"
              min={1}
              max={200}
              value={perRun}
              onChange={(e) => setPerRun(Math.min(200, Math.max(1, Number(e.target.value))))}
              className={inputClass}
            />
          </div>
          <label className="flex items-end gap-2 pb-1 text-sm">
            <input
              type="checkbox"
              checked={autoEnrich}
              onChange={(e) => setAutoEnrich(e.target.checked)}
              className="h-4 w-4"
            />
            Auto-enrich new leads
          </label>
        </div>
        <div className="flex items-center justify-between gap-2">
          <span className="text-xs text-slate-500">
            {gridSize > 0
              ? `${gridSize} grid cell${gridSize === 1 ? "" : "s"} to sweep`
              : "Add at least one business type and location."}
          </span>
          <Button type="submit" disabled={create.isPending || !valid}>
            {create.isPending ? "Creating…" : "Create campaign"}
          </Button>
        </div>
        {create.isError && (
          <p className="text-sm text-red-500">
            {create.error instanceof ApiError ? create.error.message : "Could not create campaign."}
          </p>
        )}
      </form>
    </Card>
  );
}

function CampaignCard({
  campaign,
  onChanged,
}: {
  campaign: LeadCampaign;
  onChanged: () => void;
}) {
  const run = useMutation({
    mutationFn: () => api.runCampaign(campaign.id as number),
    onSuccess: onChanged,
  });
  const remove = useMutation({
    mutationFn: () => api.deleteCampaign(campaign.id as number),
    onSuccess: onChanged,
  });

  return (
    <Card>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-semibold">{campaign.name}</span>
            {campaign.auto_enrich && <Badge tone="brand">auto-enrich</Badge>}
          </div>
          <div className="mt-1 flex flex-wrap items-center gap-1.5 text-xs text-slate-500">
            {campaign.categories.map((cat) => (
              <Badge key={cat}>{cat}</Badge>
            ))}
            <span className="mx-1">×</span>
            {campaign.locations.map((loc) => (
              <Badge key={loc} tone="amber">
                {loc}
              </Badge>
            ))}
          </div>
          <div className="mt-2 text-xs text-slate-500">
            Next up: <span className="font-medium">{campaign.next_category}</span> in{" "}
            <span className="font-medium">{campaign.next_location}</span> · every{" "}
            {campaign.interval_minutes}m · last run {relativeTime(campaign.last_run_at)}
          </div>
        </div>
        <div className="flex flex-col items-end gap-2">
          <div className="text-right">
            <div className="text-2xl font-semibold">{campaign.lead_count}</div>
            <div className="text-xs text-slate-500">leads</div>
          </div>
          <div className="flex items-center gap-2">
            {run.isSuccess && (
              <span className="text-xs text-green-600">
                +{run.data.new_leads} from {run.data.category}
              </span>
            )}
            <Button onClick={() => run.mutate()} disabled={run.isPending}>
              {run.isPending ? "Running…" : "Run now"}
            </Button>
            <button
              className="text-xs text-red-500"
              onClick={() => remove.mutate()}
              disabled={remove.isPending}
            >
              Delete
            </button>
          </div>
        </div>
      </div>
    </Card>
  );
}

function toCsv(leads: Lead[]): string {
  const header = ["company", "website", "industry", "city", "country", "status", "discovered"];
  const rows = leads.map((lead) => {
    const c = lead.company;
    const website = c.domains.find((d) => d.is_primary)?.hostname ?? c.domains[0]?.hostname ?? "";
    return [
      c.display_name,
      website,
      c.industry ?? "",
      c.city ?? "",
      c.country ?? "",
      lead.status,
      lead.created_at,
    ];
  });
  return [header, ...rows]
    .map((row) => row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(","))
    .join("\n");
}

function LeadInbox({
  campaigns,
  filter,
  onFilter,
}: {
  campaigns: LeadCampaign[];
  filter: number | "all";
  onFilter: (value: number | "all") => void;
}) {
  const leads = useQuery({
    queryKey: ["leads", filter],
    queryFn: () => api.listLeads(200, filter === "all" ? undefined : filter),
  });

  const rows = leads.data ?? [];

  const downloadCsv = () => {
    const blob = new Blob([toCsv(rows)], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "leads.csv";
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  };

  return (
    <Card>
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-lg font-semibold">Lead inbox</h2>
        <div className="flex items-center gap-2">
          <select
            value={filter === "all" ? "all" : String(filter)}
            onChange={(e) => onFilter(e.target.value === "all" ? "all" : Number(e.target.value))}
            className="rounded-lg border border-slate-300 bg-transparent px-2 py-1 text-sm dark:border-slate-700"
          >
            <option value="all">All campaigns</option>
            {campaigns.map((c) => (
              <option key={c.id} value={String(c.id)}>
                {c.name}
              </option>
            ))}
          </select>
          <Button variant="ghost" onClick={downloadCsv} disabled={rows.length === 0}>
            Download CSV
          </Button>
        </div>
      </div>

      {leads.isLoading ? (
        <Spinner />
      ) : rows.length === 0 ? (
        <p className="p-6 text-center text-sm text-slate-400">
          No leads yet. Run a campaign to fill the inbox — freshest leads appear first.
        </p>
      ) : (
        <ul className="divide-y divide-slate-100 dark:divide-slate-800/60">
          {rows.map((lead) => (
            <LeadRow key={lead.id} lead={lead} />
          ))}
        </ul>
      )}
    </Card>
  );
}

function LeadRow({ lead }: { lead: Lead }) {
  const c = lead.company;
  const website = c.domains.find((d) => d.is_primary)?.hostname ?? c.domains[0]?.hostname ?? null;
  const place = [c.city, c.country].filter(Boolean).join(", ");

  return (
    <li className="flex flex-wrap items-center justify-between gap-2 py-3">
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <Link to={`/companies/${c.id}`} className="font-medium text-brand-600">
            {c.display_name}
          </Link>
          <Badge tone={lead.status === "new" ? "brand" : "slate"}>{lead.status}</Badge>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
          {c.industry && <Badge>{c.industry}</Badge>}
          {website && (
            <a
              href={`https://${website}`}
              target="_blank"
              rel="noreferrer"
              className="text-brand-600"
            >
              {website}
            </a>
          )}
          {place && <span>· {place}</span>}
        </div>
      </div>
      <span className="text-xs text-slate-400">{relativeTime(lead.created_at)}</span>
    </li>
  );
}
