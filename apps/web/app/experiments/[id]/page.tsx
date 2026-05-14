"use client";

import { useMutation, useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { MetricCards } from "@/components/MetricCards";
import { RunStatusTimeline } from "@/components/RunStatusTimeline";

interface Props {
  params: { id: string };
}

export default function ExperimentDetailPage({ params }: Props) {
  const { id } = params;

  const status = useQuery({
    queryKey: ["experiment-status", id],
    queryFn: () => api.experimentStatus(id),
    refetchInterval: (q) => {
      const s = q.state.data?.status;
      return s === "completed" || s === "failed" || s === "cancelled" ? false : 1500;
    },
  });

  const result = useQuery({
    queryKey: ["experiment-result", id],
    queryFn: () => api.experimentResult(id),
    enabled: status.data?.status === "completed",
  });

  const report = useMutation({
    mutationFn: () => api.generateReport({ experiment_id: id, include_references: true }),
  });

  return (
    <section className="flex flex-col gap-6">
      <header>
        <h1 className="text-2xl font-semibold">Experiment {id.slice(0, 8)}</h1>
        <p className="text-sm text-slate-500">Full id: {id}</p>
      </header>

      <RunStatusTimeline status={status.data} />

      {result.data && (
        <>
          <MetricCards metrics={result.data.metrics} />
          <div>
            <h2 className="text-lg font-medium">Summary</h2>
            <pre className="mt-2 overflow-x-auto rounded-md bg-slate-900 p-4 text-xs text-slate-100">
              {JSON.stringify(result.data.summary, null, 2)}
            </pre>
          </div>
          <div>
            <button
              type="button"
              onClick={() => report.mutate()}
              className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
              disabled={report.isPending}
            >
              {report.isPending ? "Generating…" : "Generate research report"}
            </button>
            {report.data && (
              <p className="mt-3 text-sm">
                Report saved: <code>{report.data.report_id}</code> ·{" "}
                {report.data.reference_count} references.
              </p>
            )}
            {report.isError && (
              <p className="mt-3 text-sm text-red-600">Report generation failed.</p>
            )}
          </div>
        </>
      )}

      {status.data?.status === "failed" && (
        <p className="rounded-md bg-red-50 p-3 text-sm text-red-700">
          Run failed: {status.data.message ?? "unknown error"}
        </p>
      )}
    </section>
  );
}
