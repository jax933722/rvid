import type { FacetValue } from "@/api/types";
import { Button } from "@/components/ui";
import type { SearchFormState } from "./types";
import { EMPTY_STATE } from "./types";

interface Props {
  state: SearchFormState;
  facets: Record<string, FacetValue[]>;
  onChange: (next: SearchFormState) => void;
}

const FLAG_LABELS: Record<keyof SearchFormState["flags"], string> = {
  has_contact_page: "Has Contact Page",
  has_careers_page: "Has Careers Page",
  has_blog: "Has Blog",
  has_ssl: "SSL",
};

export function FiltersPanel({ state, facets, onChange }: Props) {
  const set = (patch: Partial<SearchFormState>) => onChange({ ...state, ...patch, page: 1 });

  const toggleTech = (name: string) => {
    const has = state.technologies.includes(name);
    set({
      technologies: has
        ? state.technologies.filter((t) => t !== name)
        : [...state.technologies, name],
    });
  };

  return (
    <div className="space-y-5 text-sm">
      <div>
        <label className="mb-1 block font-medium">Search text</label>
        <input
          value={state.text}
          onChange={(e) => set({ text: e.target.value })}
          placeholder="dentist, agency…"
          className="w-full rounded-lg border border-slate-300 bg-transparent px-3 py-1.5 dark:border-slate-700"
        />
      </div>

      <div>
        <label className="mb-1 block font-medium">Industry</label>
        <input
          value={state.industry}
          onChange={(e) => set({ industry: e.target.value })}
          placeholder="Dentistry"
          className="w-full rounded-lg border border-slate-300 bg-transparent px-3 py-1.5 dark:border-slate-700"
        />
        {(facets.industry ?? []).length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {facets.industry.map((f) => (
              <button
                key={f.value}
                onClick={() => set({ industry: f.value })}
                className="rounded-full bg-slate-100 px-2 py-0.5 text-xs hover:bg-brand-100 dark:bg-slate-800"
              >
                {f.value} ({f.count})
              </button>
            ))}
          </div>
        )}
      </div>

      <div>
        <label className="mb-1 block font-medium">Max SEO score</label>
        <input
          value={state.seoMax}
          onChange={(e) => set({ seoMax: e.target.value })}
          inputMode="numeric"
          placeholder="e.g. 50"
          className="w-full rounded-lg border border-slate-300 bg-transparent px-3 py-1.5 dark:border-slate-700"
        />
      </div>

      <div>
        <span className="mb-1 block font-medium">Website features</span>
        <div className="space-y-1">
          {(Object.keys(state.flags) as (keyof SearchFormState["flags"])[]).map((key) => (
            <label key={key} className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={state.flags[key]}
                onChange={(e) => set({ flags: { ...state.flags, [key]: e.target.checked } })}
              />
              {FLAG_LABELS[key]}
            </label>
          ))}
        </div>
      </div>

      <div>
        <span className="mb-1 block font-medium">Technology</span>
        <div className="flex flex-wrap gap-1">
          {(facets.technology ?? []).map((f) => (
            <button
              key={f.value}
              onClick={() => toggleTech(f.value)}
              className={`rounded-full px-2 py-0.5 text-xs ${
                state.technologies.includes(f.value)
                  ? "bg-brand-600 text-white"
                  : "bg-slate-100 hover:bg-brand-100 dark:bg-slate-800"
              }`}
            >
              {f.value} ({f.count})
            </button>
          ))}
          {(facets.technology ?? []).length === 0 && (
            <span className="text-xs text-slate-400">Run a search to see technologies</span>
          )}
        </div>
      </div>

      <Button variant="ghost" onClick={() => onChange({ ...EMPTY_STATE })}>
        Clear filters
      </Button>
    </div>
  );
}
