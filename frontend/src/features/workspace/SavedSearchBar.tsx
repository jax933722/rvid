import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/api/client";
import type { SearchRequest } from "@/api/types";
import { Button } from "@/components/ui";

interface Props {
  request: SearchRequest;
  onApply: (request: SearchRequest) => void;
}

/** Save the current Prospector filters, and re-apply a previously saved search. */
export function SavedSearchBar({ request, onApply }: Props) {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);

  const saved = useQuery({ queryKey: ["saved-searches"], queryFn: api.listSavedSearches });

  const save = useMutation({
    mutationFn: (name: string) => api.saveSearch(name, request),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["saved-searches"] }),
  });
  const remove = useMutation({
    mutationFn: (id: number) => api.deleteSavedSearch(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["saved-searches"] }),
  });

  const onSave = () => {
    const name = window.prompt("Name this search")?.trim();
    if (name) save.mutate(name);
  };

  const items = saved.data ?? [];

  return (
    <div className="relative flex items-center gap-2">
      <Button variant="ghost" onClick={onSave} disabled={save.isPending}>
        {save.isPending ? "Saving…" : "☆ Save search"}
      </Button>
      <Button variant="ghost" onClick={() => setOpen((v) => !v)}>
        Saved ({items.length}) ▾
      </Button>

      {open && (
        <div className="absolute right-0 top-9 z-10 w-72 rounded-lg border border-slate-200 bg-white p-2 shadow-lg dark:border-slate-700 dark:bg-slate-900">
          {items.length === 0 ? (
            <p className="p-3 text-center text-xs text-slate-400">No saved searches yet.</p>
          ) : (
            <ul className="max-h-72 space-y-1 overflow-auto">
              {items.map((s) => (
                <li key={s.id} className="flex items-center justify-between gap-2 rounded px-2 py-1 hover:bg-slate-50 dark:hover:bg-slate-800">
                  <button
                    className="min-w-0 flex-1 truncate text-left text-sm"
                    onClick={() => {
                      onApply(s.query);
                      setOpen(false);
                    }}
                  >
                    {s.name}
                  </button>
                  <button
                    className="text-xs text-red-500"
                    onClick={() => remove.mutate(s.id)}
                    aria-label={`Delete ${s.name}`}
                  >
                    ✕
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
