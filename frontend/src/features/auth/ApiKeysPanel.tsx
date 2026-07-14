import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/api/client";
import { Badge, Button, Card, Spinner } from "@/components/ui";

/** Manage the current workspace's API keys: create (secret shown once), list, revoke. */
export function ApiKeysPanel() {
  const qc = useQueryClient();
  const [name, setName] = useState("");
  const [newSecret, setNewSecret] = useState<string | null>(null);

  const whoami = useQuery({ queryKey: ["whoami"], queryFn: api.whoami });
  const keys = useQuery({ queryKey: ["api-keys"], queryFn: api.listApiKeys });

  const create = useMutation({
    mutationFn: (keyName: string) => api.createApiKey(keyName),
    onSuccess: (data) => {
      setNewSecret(data.secret);
      setName("");
      qc.invalidateQueries({ queryKey: ["api-keys"] });
    },
  });
  const revoke = useMutation({
    mutationFn: (id: number) => api.revokeApiKey(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["api-keys"] }),
  });

  return (
    <Card>
      <div className="mb-2 flex items-center justify-between">
        <h2 className="font-semibold">API keys</h2>
        {whoami.data && (
          <span className="text-xs text-slate-500">
            workspace: <span className="font-medium">{whoami.data.slug}</span>
          </span>
        )}
      </div>
      <p className="mb-3 text-sm text-slate-500">
        Keys authenticate API requests when auth is enabled on the backend
        (<code>BISE_AUTH_ENABLED</code>). Send as <code>Authorization: Bearer …</code>.
      </p>

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
          placeholder="Key name (e.g. CI pipeline)"
          className="w-full rounded-lg border border-slate-300 bg-transparent px-3 py-1.5 text-sm dark:border-slate-700"
        />
        <Button type="submit" disabled={create.isPending || !name.trim()}>
          {create.isPending ? "Creating…" : "Create key"}
        </Button>
      </form>

      {newSecret && (
        <div className="mt-3 rounded-lg border border-green-300 bg-green-50 p-3 text-sm dark:border-green-800 dark:bg-green-900/20">
          <div className="mb-1 font-medium text-green-700 dark:text-green-300">
            Copy this key now — it is never shown again.
          </div>
          <code className="block break-all rounded bg-white px-2 py-1 dark:bg-slate-900">
            {newSecret}
          </code>
          <button
            className="mt-2 text-xs text-brand-600"
            onClick={() => {
              void navigator.clipboard?.writeText(newSecret);
            }}
          >
            Copy to clipboard
          </button>
        </div>
      )}

      <div className="mt-4">
        {keys.isLoading ? (
          <Spinner />
        ) : (keys.data ?? []).length === 0 ? (
          <p className="py-3 text-center text-sm text-slate-400">No API keys yet.</p>
        ) : (
          <ul className="divide-y divide-slate-100 dark:divide-slate-800/60">
            {(keys.data ?? []).map((k) => (
              <li key={k.id} className="flex items-center justify-between gap-2 py-2 text-sm">
                <div className="min-w-0">
                  <div className="font-medium">{k.name}</div>
                  <div className="text-xs text-slate-500">
                    <code>{k.prefix}…</code>
                    {k.last_used_at ? ` · last used ${new Date(k.last_used_at).toLocaleString()}` : " · never used"}
                  </div>
                </div>
                {k.revoked ? (
                  <Badge tone="red">revoked</Badge>
                ) : (
                  <Button variant="ghost" onClick={() => k.id != null && revoke.mutate(k.id)}>
                    Revoke
                  </Button>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </Card>
  );
}
