import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { api } from "@/api/client";
import { Badge, Button, Card, gradeTone, Spinner } from "@/components/ui";

type Tab = "overview" | "technology" | "seo";

export function CompanyDetailsPage() {
  const { id } = useParams();
  const companyId = Number(id);
  const [tab, setTab] = useState<Tab>("overview");
  const qc = useQueryClient();

  const company = useQuery({
    queryKey: ["company", companyId],
    queryFn: () => api.getCompany(companyId),
  });
  const tech = useQuery({
    queryKey: ["company-tech", companyId],
    queryFn: () => api.companyTechnologies(companyId),
  });
  const seo = useQuery({
    queryKey: ["company-seo", companyId],
    queryFn: () => api.companySeo(companyId).catch(() => null),
  });

  const reindex = useMutation({
    mutationFn: () => api.reindexCompany(companyId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["search"] }),
  });

  if (company.isLoading) return <Spinner />;
  if (!company.data) return <div className="text-red-500">Company not found.</div>;
  const c = company.data;

  return (
    <div className="space-y-4">
      <Link to="/search" className="text-sm text-brand-600">
        ← Back to search
      </Link>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-2xl font-bold">{c.display_name}</h1>
          <div className="text-sm text-slate-500">{c.industry ?? "Industry unknown"}</div>
        </div>
        <Button onClick={() => reindex.mutate()} disabled={reindex.isPending}>
          {reindex.isPending ? "Indexing…" : "Rebuild search index"}
        </Button>
      </div>

      <div className="flex gap-2 border-b border-slate-200 dark:border-slate-800">
        {(["overview", "technology", "seo"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-3 py-2 text-sm font-medium capitalize ${
              tab === t
                ? "border-b-2 border-brand-500 text-brand-600"
                : "text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "overview" && (
        <Card>
          <dl className="grid grid-cols-2 gap-3 text-sm">
            <Field label="Status" value={c.status} />
            <Field label="Size bucket" value={c.size_bucket ?? "—"} />
            <div className="col-span-2">
              <dt className="text-slate-500">Domains</dt>
              <dd className="mt-1 flex flex-wrap gap-1">
                {c.domains.map((d) => (
                  <Badge key={d.hostname} tone="brand">
                    {d.hostname} · {d.crawl_status}
                  </Badge>
                ))}
              </dd>
            </div>
          </dl>
        </Card>
      )}

      {tab === "technology" && (
        <Card>
          {tech.isLoading ? (
            <Spinner />
          ) : (tech.data ?? []).length === 0 ? (
            <p className="text-sm text-slate-400">No technologies detected yet.</p>
          ) : (
            <table className="w-full text-left text-sm">
              <thead className="text-xs uppercase text-slate-500">
                <tr>
                  <th className="py-1">Technology</th>
                  <th>Category</th>
                  <th>Confidence</th>
                  <th>Version</th>
                </tr>
              </thead>
              <tbody>
                {tech.data!.map((t) => (
                  <tr key={t.name} className="border-t border-slate-100 dark:border-slate-800/60">
                    <td className="py-1 font-medium">{t.name}</td>
                    <td>{t.category}</td>
                    <td>{Math.round(t.confidence * 100)}%</td>
                    <td>{t.version ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>
      )}

      {tab === "seo" && (
        <Card>
          {seo.isLoading ? (
            <Spinner />
          ) : !seo.data ? (
            <p className="text-sm text-slate-400">No SEO scan yet.</p>
          ) : (
            <div className="space-y-3 text-sm">
              <div className="flex items-center gap-2">
                <Badge tone={gradeTone(seo.data.grade)}>
                  {seo.data.grade} · {Math.round(seo.data.score)}
                </Badge>
                <span className="text-slate-500">{seo.data.url}</span>
              </div>
              <dl className="grid grid-cols-2 gap-3">
                <Field label="Title" value={seo.data.title ?? "—"} />
                <Field label="Indexable" value={seo.data.is_indexable ? "Yes" : "No"} />
                <Field label="SSL" value={seo.data.has_ssl ? "Yes" : "No"} />
                <Field label="Structured data" value={seo.data.has_structured_data ? "Yes" : "No"} />
                <Field label="H1 / H2" value={`${seo.data.h1_count} / ${seo.data.h2_count}`} />
                <Field
                  label="Images missing alt"
                  value={`${seo.data.images_missing_alt} / ${seo.data.images_total}`}
                />
              </dl>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-slate-500">{label}</dt>
      <dd className="font-medium">{value}</dd>
    </div>
  );
}
