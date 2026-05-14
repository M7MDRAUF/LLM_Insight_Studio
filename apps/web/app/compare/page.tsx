"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "@/lib/api";
import { ComparisonTable } from "@/components/ComparisonTable";

const LANE_COLORS: Record<string, string> = {
  classification: "text-violet-600 bg-violet-50 border-violet-200",
  summarization: "text-blue-600 bg-blue-50 border-blue-200",
  qa: "text-emerald-600 bg-emerald-50 border-emerald-200",
  instruct: "text-orange-600 bg-orange-50 border-orange-200",
};

export default function ComparePage() {
  const experiments = useQuery({
    queryKey: ["experiments"],
    queryFn: () => api.listExperiments(),
  });
  const [selected, setSelected] = useState<string[]>([]);

  const completed = (experiments.data ?? []).filter((e) => e.status === "completed");

  const results = useQuery({
    queryKey: ["compare", selected],
    queryFn: async () => {
      const rows = await Promise.all(selected.map((id) => api.experimentResult(id)));
      return rows;
    },
    enabled: selected.length > 0,
  });

  const toggle = (id: string) =>
    setSelected((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));

  return (
    <section className="flex flex-col gap-6">
      <header className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Compare experiments</h1>
          <p className="mt-1 text-sm text-slate-500">
            Select completed runs to view side-by-side metrics and rankings.
          </p>
        </div>
        {selected.length > 0 && (
          <div className="flex items-center gap-3">
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
              {selected.length} selected
            </span>
            <button
              type="button"
              onClick={() => setSelected([])}
              className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-500 hover:border-slate-300 hover:bg-slate-50"
            >
              Clear all
            </button>
          </div>
        )}
      </header>

      {/* Experiment selector */}
      <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
        <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-slate-400">
          Available runs
        </p>
        {completed.length === 0 ? (
          <p className="text-sm text-slate-400">No completed experiments yet.</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {completed.map((e) => {
              const active = selected.includes(e.id);
              const lanes = e.task_lanes ?? [];
              return (
                <button
                  key={e.id}
                  type="button"
                  onClick={() => toggle(e.id)}
                  className={`group flex items-center gap-2 rounded-xl border px-3 py-2 text-xs font-medium transition-all ${
                    active
                      ? "border-slate-700 bg-slate-800 text-white shadow-md"
                      : "border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:shadow-sm"
                  }`}
                >
                  {/* Selection indicator */}
                  <span
                    className={`flex h-4 w-4 items-center justify-center rounded-full border text-[9px] font-bold transition-all ${
                      active
                        ? "border-white bg-white text-slate-800"
                        : "border-slate-300 text-transparent"
                    }`}
                  >
                    ✓
                  </span>

                  {/* ID */}
                  <span className="font-mono font-bold tracking-tight">{e.id.slice(0, 8)}</span>

                  {/* Lane pills */}
                  <span className="flex gap-1">
                    {lanes.map((lane) => (
                      <span
                        key={lane}
                        className={`rounded-full border px-1.5 py-0.5 text-[9px] font-semibold ${
                          active
                            ? "border-white/30 bg-white/20 text-white"
                            : (LANE_COLORS[lane] ?? "border-slate-200 text-slate-500")
                        }`}
                      >
                        {lane.slice(0, 3).toUpperCase()}
                      </span>
                    ))}
                  </span>
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Results */}
      {selected.length === 0 && (
        <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-slate-200 py-16 text-center">
          <div className="text-4xl">📊</div>
          <p className="text-sm font-medium text-slate-500">
            Select at least one experiment above to see metrics
          </p>
        </div>
      )}

      {results.isLoading && selected.length > 0 && (
        <div className="flex items-center justify-center gap-2 py-12 text-sm text-slate-400">
          <span className="animate-spin text-xl">⟳</span> Loading results…
        </div>
      )}

      {results.data && results.data.length > 0 && <ComparisonTable results={results.data} />}
    </section>
  );
}

