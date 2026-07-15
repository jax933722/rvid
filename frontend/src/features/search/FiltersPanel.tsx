import type { ReactNode } from "react";
import type { FacetValue } from "@/api/types";
import { Button } from "@/components/ui";
import type { RangeState, SearchFormState } from "./types";
import { EMPTY_STATE } from "./types";

interface Props {
  state: SearchFormState;
  facets: Record<string, FacetValue[]>;
  onChange: (next: SearchFormState) => void;
}

const FLAG_LABELS: Record<keyof SearchFormState["flags"], string> = {
  has_contact_page: "Has contact page",
  has_careers_page: "Hiring (careers page)",
  has_blog: "Has blog",
  has_ssl: "SSL secured",
};

const SEO_GRADES = ["A", "B", "C", "D", "F"];
const ROLES = [
  ["founder", "Founder"],
  ["ceo", "CEO"],
  ["cto", "CTO"],
  ["cfo", "CFO"],
  ["coo", "COO"],
  ["cmo", "CMO"],
  ["vp", "VP"],
  ["director", "Director"],
  ["head", "Head"],
  ["manager", "Manager"],
] as const;

export function FiltersPanel({ state, facets, onChange }: Props) {
  const set = (patch: Partial<SearchFormState>) => onChange({ ...state, ...patch, page: 1 });

  const toggle = (key: "technologies" | "industries" | "seoGrades" | "roles", value: string) => {
    const current = state[key];
    const has = current.includes(value);
    set({ [key]: has ? current.filter((v) => v !== value) : [...current, value] } as Partial<
      SearchFormState
    >);
  };

  return (
    <div className="space-y-5 text-sm">
      <TextInput
        label="Keywords"
        value={state.text}
        placeholder="dentist, root canal, agency…"
        onChange={(v) => set({ text: v })}
      />

      <Group title="Company">
        <ChipMultiSelect
          label="Industry"
          selected={state.industries}
          facet={facets.industry}
          onToggle={(v) => toggle("industries", v)}
          onClear={() => set({ industries: [] })}
          emptyHint="Search to see industries"
        />
        <RangeInput
          label="Employees"
          range={state.employees}
          onChange={(r) => set({ employees: r })}
          minPlaceholder="min"
          maxPlaceholder="max"
        />
        <RangeInput
          label="Founded (year)"
          range={state.founded}
          onChange={(r) => set({ founded: r })}
          minPlaceholder="from"
          maxPlaceholder="to"
        />
        <ChipMultiSelect
          label="Company size"
          selected={[]}
          facet={facets.size_bucket}
          onToggle={() => {}}
          onClear={() => {}}
          readOnly
          emptyHint="Populated after enrichment"
        />
      </Group>

      <Group title="Location">
        <TextInput
          label="City"
          value={state.city}
          placeholder="Sydney"
          onChange={(v) => set({ city: v })}
          suggestions={facets.city}
          onSuggest={(v) => set({ city: v })}
        />
        <TextInput
          label="State / region"
          value={state.state}
          placeholder="NSW"
          onChange={(v) => set({ state: v })}
        />
        <TextInput
          label="Country"
          value={state.country}
          placeholder="Australia"
          onChange={(v) => set({ country: v })}
          suggestions={facets.country}
          onSuggest={(v) => set({ country: v })}
        />
      </Group>

      <Group title="Technology">
        <ChipMultiSelect
          label="Uses technology"
          selected={state.technologies}
          facet={facets.technology}
          onToggle={(v) => toggle("technologies", v)}
          onClear={() => set({ technologies: [] })}
          emptyHint="Search to see technologies"
        />
      </Group>

      <Group title="People">
        <div>
          <span className="mb-1 block font-medium">Has role</span>
          <div className="flex flex-wrap gap-1">
            {ROLES.map(([value, label]) => (
              <Chip
                key={value}
                active={state.roles.includes(value)}
                onClick={() => toggle("roles", value)}
              >
                {label}
              </Chip>
            ))}
          </div>
          <p className="mt-1 text-xs text-slate-400">From public team pages · enrich to populate</p>
        </div>
      </Group>

      <Group title="SEO quality">
        <div>
          <span className="mb-1 block font-medium">Grade</span>
          <div className="flex flex-wrap gap-1">
            {SEO_GRADES.map((g) => (
              <Chip key={g} active={state.seoGrades.includes(g)} onClick={() => toggle("seoGrades", g)}>
                {g}
              </Chip>
            ))}
          </div>
        </div>
        <RangeInput
          label="Score (0–100)"
          range={state.seo}
          onChange={(r) => set({ seo: r })}
          minPlaceholder="min"
          maxPlaceholder="max"
        />
      </Group>

      <Group title="Signals">
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
      </Group>

      <Button variant="ghost" onClick={() => onChange({ ...EMPTY_STATE })}>
        Clear all filters
      </Button>
    </div>
  );
}

// --- building blocks -------------------------------------------------------

function Group({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="space-y-3 border-t border-slate-200 pt-4 dark:border-slate-800">
      <div className="text-xs font-semibold uppercase tracking-wide text-slate-400">{title}</div>
      {children}
    </div>
  );
}

function TextInput({
  label,
  value,
  placeholder,
  onChange,
  suggestions,
  onSuggest,
}: {
  label: string;
  value: string;
  placeholder?: string;
  onChange: (v: string) => void;
  suggestions?: FacetValue[];
  onSuggest?: (v: string) => void;
}) {
  return (
    <div>
      <label className="mb-1 block font-medium">{label}</label>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full rounded-lg border border-slate-300 bg-transparent px-3 py-1.5 dark:border-slate-700"
      />
      {suggestions && suggestions.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {suggestions.slice(0, 8).map((f) => (
            <Chip key={f.value} active={value === f.value} onClick={() => onSuggest?.(f.value)}>
              {f.value} <span className="opacity-60">({f.count})</span>
            </Chip>
          ))}
        </div>
      )}
    </div>
  );
}

function RangeInput({
  label,
  range,
  onChange,
  minPlaceholder,
  maxPlaceholder,
}: {
  label: string;
  range: RangeState;
  onChange: (r: RangeState) => void;
  minPlaceholder: string;
  maxPlaceholder: string;
}) {
  const cls =
    "w-full rounded-lg border border-slate-300 bg-transparent px-3 py-1.5 dark:border-slate-700";
  return (
    <div>
      <label className="mb-1 block font-medium">{label}</label>
      <div className="flex items-center gap-2">
        <input
          value={range.min}
          inputMode="numeric"
          placeholder={minPlaceholder}
          onChange={(e) => onChange({ ...range, min: e.target.value })}
          className={cls}
        />
        <span className="text-slate-400">–</span>
        <input
          value={range.max}
          inputMode="numeric"
          placeholder={maxPlaceholder}
          onChange={(e) => onChange({ ...range, max: e.target.value })}
          className={cls}
        />
      </div>
    </div>
  );
}

function ChipMultiSelect({
  label,
  selected,
  facet,
  onToggle,
  onClear,
  emptyHint,
  readOnly,
}: {
  label: string;
  selected: string[];
  facet?: FacetValue[];
  onToggle: (v: string) => void;
  onClear: () => void;
  emptyHint: string;
  readOnly?: boolean;
}) {
  const values = facet ?? [];
  return (
    <div>
      <div className="mb-1 flex items-center justify-between">
        <span className="font-medium">{label}</span>
        {selected.length > 0 && (
          <button onClick={onClear} className="text-xs text-brand-600">
            clear
          </button>
        )}
      </div>
      <div className="flex flex-wrap gap-1">
        {values.length === 0 ? (
          <span className="text-xs text-slate-400">{emptyHint}</span>
        ) : (
          values.slice(0, 12).map((f) => (
            <Chip
              key={f.value}
              active={selected.includes(f.value)}
              onClick={() => !readOnly && onToggle(f.value)}
            >
              {f.value} <span className="opacity-60">({f.count})</span>
            </Chip>
          ))
        )}
      </div>
    </div>
  );
}

function Chip({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`rounded-full px-2 py-0.5 text-xs ${
        active
          ? "bg-brand-600 text-white"
          : "bg-slate-100 hover:bg-brand-100 dark:bg-slate-800 dark:hover:bg-slate-700"
      }`}
    >
      {children}
    </button>
  );
}
