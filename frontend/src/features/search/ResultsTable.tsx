import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table";
import type { SearchItem } from "@/api/types";
import { Badge, gradeTone } from "@/components/ui";

const columnHelper = createColumnHelper<SearchItem>();

const columns = [
  columnHelper.accessor("display_name", {
    header: "Company",
    cell: (c) => (
      <div>
        <div className="font-medium">{c.getValue()}</div>
        <div className="text-xs text-slate-500">{c.row.original.primary_domain ?? "—"}</div>
      </div>
    ),
  }),
  columnHelper.accessor("industry", {
    header: "Industry",
    cell: (c) => c.getValue() ?? "—",
  }),
  columnHelper.accessor("seo_grade", {
    header: "SEO",
    cell: (c) => {
      const grade = c.getValue();
      const score = c.row.original.seo_score;
      return grade ? (
        <Badge tone={gradeTone(grade)}>
          {grade} {score != null ? `(${Math.round(score)})` : ""}
        </Badge>
      ) : (
        "—"
      );
    },
  }),
  columnHelper.accessor("technologies", {
    header: "Technologies",
    cell: (c) => (
      <div className="flex flex-wrap gap-1">
        {c.getValue().slice(0, 4).map((t) => (
          <Badge key={t} tone="brand">
            {t}
          </Badge>
        ))}
        {c.getValue().length > 4 && <span className="text-xs">+{c.getValue().length - 4}</span>}
      </div>
    ),
  }),
];

interface Props {
  items: SearchItem[];
  selectedId: number | null;
  onSelect: (id: number) => void;
}

export function ResultsTable({ items, selectedId, onSelect }: Props) {
  const table = useReactTable({ data: items, columns, getCoreRowModel: getCoreRowModel() });

  if (items.length === 0) {
    return <div className="p-8 text-center text-sm text-slate-400">No matching companies.</div>;
  }

  return (
    <table className="w-full text-left text-sm">
      <thead className="border-b border-slate-200 text-xs uppercase text-slate-500 dark:border-slate-800">
        {table.getHeaderGroups().map((hg) => (
          <tr key={hg.id}>
            {hg.headers.map((h) => (
              <th key={h.id} className="px-3 py-2 font-medium">
                {flexRender(h.column.columnDef.header, h.getContext())}
              </th>
            ))}
          </tr>
        ))}
      </thead>
      <tbody>
        {table.getRowModel().rows.map((row) => {
          const id = row.original.company_id;
          return (
            <tr
              key={row.id}
              onClick={() => onSelect(id)}
              className={`cursor-pointer border-b border-slate-100 dark:border-slate-800/60 ${
                selectedId === id
                  ? "bg-brand-50 dark:bg-brand-700/20"
                  : "hover:bg-slate-50 dark:hover:bg-slate-800/40"
              }`}
            >
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id} className="px-3 py-2 align-top">
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
