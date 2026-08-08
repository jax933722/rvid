import { useState } from "react";
import type { ExportFormat } from "@/api/client";
import { Button } from "@/components/ui";

const FORMATS: { format: ExportFormat; label: string }[] = [
  { format: "csv", label: "CSV" },
  { format: "xlsx", label: "Excel (.xlsx)" },
  { format: "json", label: "JSON" },
];

/** A small dropdown that exports via the provided callback for the chosen format. */
export function ExportMenu({
  onExport,
  disabled,
  label = "Export",
}: {
  onExport: (format: ExportFormat) => void;
  disabled?: boolean;
  label?: string;
}) {
  const [open, setOpen] = useState(false);

  return (
    <div className="relative">
      <Button variant="ghost" onClick={() => setOpen((v) => !v)} disabled={disabled}>
        ⬇ {label} ▾
      </Button>
      {open && (
        <div className="absolute right-0 top-9 z-10 w-40 rounded-lg border border-slate-200 bg-white p-1 shadow-lg dark:border-slate-700 dark:bg-slate-900">
          {FORMATS.map((f) => (
            <button
              key={f.format}
              onClick={() => {
                onExport(f.format);
                setOpen(false);
              }}
              className="block w-full rounded px-3 py-1.5 text-left text-sm hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              {f.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
