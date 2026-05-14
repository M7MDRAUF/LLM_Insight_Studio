"use client";

import type { ExperimentStatusResponse } from "@/lib/types";

const STAGES = ["queued", "running", "completed"] as const;

interface Props {
  status: ExperimentStatusResponse | undefined;
}

export function RunStatusTimeline({ status }: Props) {
  const current = status?.status ?? "queued";
  const failed = current === "failed" || current === "cancelled";

  return (
    <div className="flex flex-col gap-3 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium">
          Status: <span className="font-mono">{current}</span>
        </p>
        <p className="text-xs text-slate-500">
          Progress: {Math.round((status?.progress ?? 0) * 100)}%
        </p>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
        <div
          className={
            "h-full transition-all " +
            (failed ? "bg-red-500" : "bg-brand-500")
          }
          style={{ width: `${Math.round((status?.progress ?? 0) * 100)}%` }}
        />
      </div>
      <ol className="mt-2 flex justify-between text-xs text-slate-500">
        {STAGES.map((s) => (
          <li key={s} className={s === current ? "font-semibold text-brand-600" : undefined}>
            {s}
          </li>
        ))}
      </ol>
      {status?.message && (
        <p className="mt-1 text-xs text-slate-500">Message: {status.message}</p>
      )}
    </div>
  );
}
