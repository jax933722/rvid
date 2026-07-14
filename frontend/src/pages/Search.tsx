import { useState } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { Button, Card, Spinner } from "@/components/ui";
import { CompanyPreview } from "@/features/search/CompanyPreview";
import { FiltersPanel } from "@/features/search/FiltersPanel";
import { ResultsTable } from "@/features/search/ResultsTable";
import {
  activeFilterCount,
  EMPTY_STATE,
  fromRequest,
  toRequest,
  type SearchFormState,
} from "@/features/search/types";
import { SavedSearchBar } from "@/features/workspace/SavedSearchBar";

export function SearchPage() {
  const [state, setState] = useState<SearchFormState>(EMPTY_STATE);
  const [selectedId, setSelectedId] = useState<number | null>(null);

  const request = toRequest(state);
  const query = useQuery({
    queryKey: ["search", request],
    queryFn: () => api.search(request),
    placeholderData: keepPreviousData,
  });

  const result = query.data;
  const totalPages = result ? Math.max(1, Math.ceil(result.total / result.page_size)) : 1;
  const filterCount = activeFilterCount(state);

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-[17rem_minmax(0,1fr)_20rem]">
      <Card className="h-fit">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="font-semibold">Filters</h2>
          {filterCount > 0 && (
            <span className="rounded-full bg-brand-600 px-2 py-0.5 text-xs font-medium text-white">
              {filterCount}
            </span>
          )}
        </div>
        <FiltersPanel state={state} facets={result?.facets ?? {}} onChange={setState} />
      </Card>

      <Card className="min-w-0">
        <div className="mb-2 flex items-center justify-between">
          <div>
            <h2 className="font-semibold">
              Prospector{" "}
              {result ? (
                <span className="text-slate-400">· {result.total} companies</span>
              ) : null}
            </h2>
            <p className="text-xs text-slate-500">
              Filters apply live · OR within a field, AND across fields
            </p>
          </div>
          <div className="flex items-center gap-2">
            {query.isFetching && <span className="text-xs text-slate-400">updating…</span>}
            <SavedSearchBar request={request} onApply={(req) => setState(fromRequest(req))} />
          </div>
        </div>
        {query.isLoading ? (
          <Spinner />
        ) : query.isError ? (
          <div className="p-6 text-sm text-red-500">Search failed. Is the API running?</div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <ResultsTable
                items={result?.items ?? []}
                selectedId={selectedId}
                onSelect={setSelectedId}
              />
            </div>
            <div className="mt-3 flex items-center justify-between text-sm">
              <Button
                variant="ghost"
                disabled={state.page <= 1}
                onClick={() => setState({ ...state, page: state.page - 1 })}
              >
                ← Prev
              </Button>
              <span className="text-slate-500">
                Page {state.page} of {totalPages}
              </span>
              <Button
                variant="ghost"
                disabled={state.page >= totalPages}
                onClick={() => setState({ ...state, page: state.page + 1 })}
              >
                Next →
              </Button>
            </div>
          </>
        )}
      </Card>

      <Card className="h-fit">
        <CompanyPreview companyId={selectedId} />
      </Card>
    </div>
  );
}
