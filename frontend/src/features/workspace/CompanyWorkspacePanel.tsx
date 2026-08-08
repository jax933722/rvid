import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/api/client";
import { Badge } from "@/components/ui";

/** Tag editing + add-to-list controls for a single company. */
export function CompanyWorkspacePanel({ companyId }: { companyId: number }) {
  const qc = useQueryClient();
  const [label, setLabel] = useState("");

  const tags = useQuery({
    queryKey: ["company-tags", companyId],
    queryFn: () => api.listTags(companyId),
  });
  const lists = useQuery({ queryKey: ["lists"], queryFn: api.listLists });

  const invalidateTags = () => qc.invalidateQueries({ queryKey: ["company-tags", companyId] });
  const addTag = useMutation({
    mutationFn: (value: string) => api.addTag(companyId, value),
    onSuccess: invalidateTags,
  });
  const removeTag = useMutation({
    mutationFn: (value: string) => api.removeTag(companyId, value),
    onSuccess: invalidateTags,
  });
  const addToList = useMutation({
    mutationFn: (listId: number) => api.addToList(listId, companyId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["lists"] }),
  });

  const submitTag = () => {
    const value = label.trim();
    if (value) {
      addTag.mutate(value);
      setLabel("");
    }
  };

  return (
    <div className="space-y-3 border-t border-slate-200 pt-3 dark:border-slate-800">
      <div>
        <div className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-400">Tags</div>
        <div className="mb-2 flex flex-wrap gap-1">
          {(tags.data ?? []).length === 0 && (
            <span className="text-xs text-slate-400">No tags yet</span>
          )}
          {(tags.data ?? []).map((t) => (
            <button
              key={t.id}
              onClick={() => removeTag.mutate(t.label)}
              className="group"
              title="Remove tag"
            >
              <Badge tone="brand">
                {t.label} <span className="opacity-50 group-hover:opacity-100">✕</span>
              </Badge>
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          <input
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && submitTag()}
            placeholder="add tag…"
            className="w-full rounded-lg border border-slate-300 bg-transparent px-2 py-1 text-sm dark:border-slate-700"
          />
        </div>
      </div>

      <div>
        <div className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-400">
          Add to list
        </div>
        {(lists.data ?? []).length === 0 ? (
          <p className="text-xs text-slate-400">Create a list on the Lists page first.</p>
        ) : (
          <select
            defaultValue=""
            onChange={(e) => {
              const id = Number(e.target.value);
              if (id) addToList.mutate(id);
              e.target.value = "";
            }}
            className="w-full rounded-lg border border-slate-300 bg-transparent px-2 py-1 text-sm dark:border-slate-700 dark:bg-slate-900"
          >
            <option value="">Choose a list…</option>
            {(lists.data ?? []).map((l) => (
              <option key={l.id} value={l.id}>
                {l.name} ({l.member_count})
              </option>
            ))}
          </select>
        )}
        {addToList.isSuccess && (
          <p className="mt-1 text-xs text-green-600">Added to {addToList.data.name}.</p>
        )}
      </div>
    </div>
  );
}
