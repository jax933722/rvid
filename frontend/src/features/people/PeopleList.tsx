import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { Badge } from "@/components/ui";

const ROLE_LABELS: Record<string, string> = {
  founder: "Founder",
  ceo: "CEO",
  cto: "CTO",
  cfo: "CFO",
  coo: "COO",
  cmo: "CMO",
  vp: "VP",
  director: "Director",
  head: "Head",
  manager: "Manager",
  other: "Team",
};

/** People published on the company's site, with role + public/guessed email. */
export function PeopleList({ companyId }: { companyId: number }) {
  const people = useQuery({
    queryKey: ["company-people", companyId],
    queryFn: () => api.companyPeople(companyId),
  });

  const items = people.data ?? [];
  if (items.length === 0) return null;

  return (
    <div className="border-t border-slate-200 pt-3 dark:border-slate-800">
      <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
        People ({items.length})
      </div>
      <ul className="space-y-2">
        {items.map((p) => (
          <li key={p.id} className="text-sm">
            <div className="flex items-center gap-2">
              <span className="font-medium">{p.name}</span>
              {p.role_category !== "other" && (
                <Badge tone="brand">{ROLE_LABELS[p.role_category] ?? p.role_category}</Badge>
              )}
            </div>
            {p.title && <div className="text-xs text-slate-500">{p.title}</div>}
            {p.email && (
              <div className="flex items-center gap-1 text-xs">
                <a href={`mailto:${p.email}`} className="text-brand-600">
                  {p.email}
                </a>
                {p.email_status === "guessed" ? (
                  <Badge tone="amber">guessed</Badge>
                ) : (
                  <Badge tone="green">public</Badge>
                )}
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
