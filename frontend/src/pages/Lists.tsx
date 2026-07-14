import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "@/api/client";
import type { CompanyList } from "@/api/types";
import { Button, Card, Spinner } from "@/components/ui";
import { ExportMenu } from "@/features/workspace/ExportMenu";

export function ListsPage() {
  const qc = useQueryClient();
  const [name, setName] = useState("");
  const [openId, setOpenId] = useState<number | null>(null);

  const lists = useQuery({ queryKey: ["lists"], queryFn: api.listLists });
  const create = useMutation({
    mutationFn: (listName: string) => api.createList(listName),
    onSuccess: () => {
      setName("");
      qc.invalidateQueries({ queryKey: ["lists"] });
    },
  });
  const remove = useMutation({
    mutationFn: (id: number) => api.deleteList(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["lists"] }),
  });

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold">Lists</h1>
        <p className="text-sm text-slate-500">
          Group prospects into named lists. Add companies from the Prospector's preview pane.
        </p>
      </div>

      <Card>
        <form
          className="flex gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            if (name.trim()) create.mutate(name.trim());
          }}
        >
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="New list name (e.g. Q3 outreach)"
            className="w-full rounded-lg border border-slate-300 bg-transparent px-3 py-1.5 text-sm dark:border-slate-700"
          />
          <Button type="submit" disabled={create.isPending || !name.trim()}>
            {create.isPending ? "Creating…" : "Create list"}
          </Button>
        </form>
      </Card>

      {lists.isLoading ? (
        <Spinner />
      ) : (lists.data ?? []).length === 0 ? (
        <Card>
          <p className="p-6 text-center text-sm text-slate-400">
            No lists yet. Create one above, then add companies from the Prospector.
          </p>
        </Card>
      ) : (
        <div className="space-y-3">
          {(lists.data ?? []).map((list) => (
            <ListCard
              key={list.id}
              list={list}
              open={openId === list.id}
              onToggle={() => setOpenId(openId === list.id ? null : list.id)}
              onDelete={() => remove.mutate(list.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function ListCard({
  list,
  open,
  onToggle,
  onDelete,
}: {
  list: CompanyList;
  open: boolean;
  onToggle: () => void;
  onDelete: () => void;
}) {
  const qc = useQueryClient();
  const members = useQuery({
    queryKey: ["list-members", list.id],
    queryFn: () => api.listMembers(list.id),
    enabled: open,
  });
  const removeMember = useMutation({
    mutationFn: (companyId: number) => api.removeFromList(list.id, companyId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["list-members", list.id] });
      qc.invalidateQueries({ queryKey: ["lists"] });
    },
  });

  return (
    <Card>
      <div className="flex items-center justify-between">
        <button className="text-left" onClick={onToggle}>
          <div className="font-semibold">{list.name}</div>
          <div className="text-xs text-slate-500">
            {list.member_count} {list.member_count === 1 ? "company" : "companies"}
          </div>
        </button>
        <div className="flex items-center gap-2">
          <ExportMenu
            onExport={(format) => api.exportListMembers(list.id, format)}
            disabled={list.member_count === 0}
          />
          <Button variant="ghost" onClick={onToggle}>
            {open ? "Hide" : "View"}
          </Button>
          <button className="text-xs text-red-500" onClick={onDelete}>
            Delete
          </button>
        </div>
      </div>

      {open && (
        <div className="mt-3 border-t border-slate-100 pt-3 dark:border-slate-800/60">
          {members.isLoading ? (
            <Spinner />
          ) : (members.data ?? []).length === 0 ? (
            <p className="py-4 text-center text-sm text-slate-400">This list is empty.</p>
          ) : (
            <ul className="divide-y divide-slate-100 dark:divide-slate-800/60">
              {(members.data ?? []).map((c) => (
                <li key={c.id} className="flex items-center justify-between gap-2 py-2">
                  <div className="min-w-0">
                    <Link to={`/companies/${c.id}`} className="font-medium text-brand-600">
                      {c.display_name}
                    </Link>
                    <div className="text-xs text-slate-500">
                      {[c.industry, c.city, c.country].filter(Boolean).join(" · ") || "—"}
                    </div>
                  </div>
                  <button
                    className="text-xs text-red-500"
                    onClick={() => c.id != null && removeMember.mutate(c.id)}
                  >
                    Remove
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </Card>
  );
}
