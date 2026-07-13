import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api, ApiError } from "@/api/client";
import type { DiscoveredBusiness } from "@/api/types";
import { Badge, Button, Card, Spinner } from "@/components/ui";

export function DiscoverPage() {
  const [category, setCategory] = useState("dentist");
  const [location, setLocation] = useState("Sydney, Australia");

  const discover = useMutation({
    mutationFn: () => api.discover(category.trim(), location.trim()),
  });

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold">Discover businesses online</h1>
        <p className="text-sm text-slate-500">
          Live results from OpenStreetMap. Enter a business type and a place, then enrich the ones
          you want to unlock technology, SEO, and marketing filters in Search.
        </p>
      </div>

      <Card>
        <form
          className="grid gap-2 sm:grid-cols-[1fr_1fr_auto]"
          onSubmit={(e) => {
            e.preventDefault();
            if (category.trim() && location.trim()) discover.mutate();
          }}
        >
          <div>
            <label className="mb-1 block text-sm font-medium">Business type</label>
            <input
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              placeholder="dentist, cafe, plumber…"
              className="w-full rounded-lg border border-slate-300 bg-transparent px-3 py-1.5 text-sm dark:border-slate-700"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Location</label>
            <input
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="Sydney, Australia"
              className="w-full rounded-lg border border-slate-300 bg-transparent px-3 py-1.5 text-sm dark:border-slate-700"
            />
          </div>
          <div className="flex items-end">
            <Button type="submit" disabled={discover.isPending}>
              {discover.isPending ? "Searching…" : "Search online"}
            </Button>
          </div>
        </form>
      </Card>

      {discover.isPending && <Spinner />}
      {discover.isError && (
        <Card>
          <p className="text-sm text-red-500">
            {discover.error instanceof ApiError ? discover.error.message : "Discovery failed."}
          </p>
        </Card>
      )}
      {discover.isSuccess && (
        <Card>
          <div className="mb-2 text-sm text-slate-500">
            Found {discover.data.length} businesses ·{" "}
            {discover.data.filter((b) => b.company_id != null).length} have websites (saved)
          </div>
          {discover.data.length === 0 ? (
            <p className="p-6 text-center text-sm text-slate-400">
              No results. Try a broader location or a different business type.
            </p>
          ) : (
            <ul className="divide-y divide-slate-100 dark:divide-slate-800/60">
              {discover.data.map((b, i) => (
                <ResultRow key={`${b.name}-${i}`} business={b} />
              ))}
            </ul>
          )}
        </Card>
      )}
    </div>
  );
}

function ResultRow({ business }: { business: DiscoveredBusiness }) {
  const qc = useQueryClient();
  const enrich = useMutation({
    mutationFn: () => api.enrichCompany(business.company_id as number),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["search"] }),
  });

  const place = [business.address, business.city, business.country].filter(Boolean).join(", ");

  return (
    <li className="flex flex-wrap items-center justify-between gap-2 py-3">
      <div className="min-w-0">
        <div className="font-medium">{business.name}</div>
        <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
          <Badge>{business.category}</Badge>
          {business.website ? (
            <a
              href={business.website_url ?? `https://${business.website}`}
              target="_blank"
              rel="noreferrer"
              className="text-brand-600"
            >
              {business.website}
            </a>
          ) : (
            <span>no website</span>
          )}
          {place && <span>· {place}</span>}
          {business.phone && <span>· {business.phone}</span>}
        </div>
      </div>

      <div className="flex items-center gap-2">
        {business.company_id == null ? (
          <span className="text-xs text-slate-400">not saved</span>
        ) : enrich.isSuccess ? (
          <>
            <Badge tone="green">enriched</Badge>
            <Link to={`/companies/${business.company_id}`} className="text-sm text-brand-600">
              View →
            </Link>
          </>
        ) : (
          <Button variant="ghost" onClick={() => enrich.mutate()} disabled={enrich.isPending}>
            {enrich.isPending ? "Enriching…" : "Enrich"}
          </Button>
        )}
      </div>
    </li>
  );
}
