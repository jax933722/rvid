import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "@/api/client";
import { Card, Spinner, StatTile } from "@/components/ui";

export function DashboardPage() {
  const companies = useQuery({ queryKey: ["companies", 1], queryFn: () => api.listCompanies(1, 1) });
  const jobs = useQuery({ queryKey: ["jobs", "all"], queryFn: () => api.listCrawlJobs(1, 1) });
  const pending = useQuery({
    queryKey: ["jobs", "pending"],
    queryFn: () => api.listCrawlJobs(1, 1, "pending"),
  });
  const technologies = useQuery({
    queryKey: ["technologies", "count"],
    queryFn: () => api.listTechnologies(1, 1),
  });

  const loading =
    companies.isLoading || jobs.isLoading || pending.isLoading || technologies.isLoading;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-sm text-slate-500">Overview of the indexed business intelligence.</p>
      </div>

      {loading ? (
        <Spinner />
      ) : (
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          <StatTile label="Companies" value={companies.data?.total ?? 0} />
          <StatTile label="Crawl jobs" value={jobs.data?.total ?? 0} />
          <StatTile label="Pending crawls" value={pending.data?.total ?? 0} />
          <StatTile label="Technologies" value={technologies.data?.total ?? 0} />
        </div>
      )}

      <Card>
        <h2 className="mb-2 font-semibold">Get started</h2>
        <ul className="list-inside list-disc space-y-1 text-sm text-slate-600 dark:text-slate-300">
          <li>
            Use the <Link className="text-brand-600" to="/crawlers">Crawler Monitor</Link> to
            crawl a company website.
          </li>
          <li>
            Run technology detection and an SEO scan, then rebuild the search index for that
            company.
          </li>
          <li>
            Explore the data in <Link className="text-brand-600" to="/search">Search</Link> with
            Sales-Navigator-style filters.
          </li>
        </ul>
      </Card>
    </div>
  );
}
