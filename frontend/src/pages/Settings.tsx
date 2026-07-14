import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { Badge, Card } from "@/components/ui";
import { ApiKeysPanel } from "@/features/auth/ApiKeysPanel";
import { useTheme } from "@/hooks/useTheme";

export function SettingsPage() {
  const { theme, toggle } = useTheme();
  const health = useQuery({ queryKey: ["health"], queryFn: () => api.health() });

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Settings</h1>

      <Card>
        <h2 className="mb-2 font-semibold">Appearance</h2>
        <div className="flex items-center justify-between text-sm">
          <span>Theme</span>
          <button
            onClick={toggle}
            className="rounded-lg border border-slate-300 px-3 py-1.5 dark:border-slate-700"
          >
            {theme === "dark" ? "Dark" : "Light"}
          </button>
        </div>
      </Card>

      <Card>
        <h2 className="mb-2 font-semibold">API</h2>
        <div className="flex items-center justify-between text-sm">
          <span>Backend health</span>
          {health.isLoading ? (
            <span className="text-slate-400">checking…</span>
          ) : health.data?.status === "ok" ? (
            <Badge tone="green">connected</Badge>
          ) : (
            <Badge tone="red">unreachable</Badge>
          )}
        </div>
      </Card>

      <ApiKeysPanel />

      <Card>
        <h2 className="mb-2 font-semibold">Crawler configuration</h2>
        <p className="text-sm text-slate-500">
          Crawl concurrency, delays, timeouts, user-agent, and robots.txt handling are configured
          on the backend (environment variables). A future release will expose editable settings
          here via a settings endpoint.
        </p>
      </Card>
    </div>
  );
}
