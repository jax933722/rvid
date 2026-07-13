import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "@/api/client";
import { Badge, Card, gradeTone, Spinner } from "@/components/ui";

export function CompanyPreview({ companyId }: { companyId: number | null }) {
  const company = useQuery({
    queryKey: ["company", companyId],
    queryFn: () => api.getCompany(companyId as number),
    enabled: companyId != null,
  });
  const seo = useQuery({
    queryKey: ["company-seo", companyId],
    queryFn: () => api.companySeo(companyId as number).catch(() => null),
    enabled: companyId != null,
  });

  if (companyId == null) {
    return (
      <div className="p-6 text-center text-sm text-slate-400">
        Select a company to preview details.
      </div>
    );
  }
  if (company.isLoading) return <Spinner />;
  if (!company.data) return <div className="p-6 text-sm text-red-500">Failed to load.</div>;

  const c = company.data;
  return (
    <div className="space-y-3">
      <div>
        <h2 className="text-lg font-semibold">{c.display_name}</h2>
        <div className="text-sm text-slate-500">{c.industry ?? "Industry unknown"}</div>
      </div>
      <div className="flex flex-wrap gap-1">
        <Badge>{c.status}</Badge>
        {c.domains.map((d) => (
          <Badge key={d.hostname} tone="brand">
            {d.hostname}
          </Badge>
        ))}
      </div>
      {seo.data && (
        <Card>
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">SEO</span>
            <Badge tone={gradeTone(seo.data.grade)}>
              {seo.data.grade} · {Math.round(seo.data.score)}
            </Badge>
          </div>
          <div className="mt-1 text-xs text-slate-500">
            {seo.data.has_ssl ? "SSL" : "No SSL"} · {seo.data.word_count} words ·{" "}
            {seo.data.images_missing_alt} imgs missing alt
          </div>
        </Card>
      )}
      <Link
        to={`/companies/${companyId}`}
        className="inline-block rounded-lg bg-brand-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-700"
      >
        Open full profile →
      </Link>
    </div>
  );
}
