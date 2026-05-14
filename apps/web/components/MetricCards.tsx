"use client";

import type { MetricsByLane } from "@/lib/types";

const KEY_METRIC: Record<string, string> = {
  classification: "f1_macro",
  summarization: "rougeL",
  qa: "f1",
  instruct: "support",
};

interface Props {
  metrics: MetricsByLane;
}

export function MetricCards({ metrics }: Props) {
  const lanes = Object.entries(metrics).filter(
    ([, v]) => v && typeof v === "object",
  ) as [string, Record<string, unknown>][];

  if (lanes.length === 0) {
    return <p className="text-sm text-slate-500">No metrics recorded.</p>;
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {lanes.map(([lane, values]) => {
        const keyName = KEY_METRIC[lane] ?? Object.keys(values)[0];
        const keyValue = values[keyName];
        return (
          <div
            key={lane}
            className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm"
          >
            <p className="text-xs uppercase tracking-wide text-slate-500">{lane}</p>
            <p className="mt-2 text-2xl font-semibold">{formatMetric(keyValue)}</p>
            <p className="text-xs text-slate-500">{keyName}</p>
            <dl className="mt-3 space-y-1 text-xs">
              {Object.entries(values)
                .filter(([, v]) => v === null || v === undefined || typeof v !== "object")
                .map(([k, v]) => (
                  <div key={k} className="flex justify-between gap-2">
                    <dt className="text-slate-500">{k}</dt>
                    <dd className="font-mono">{formatMetric(v)}</dd>
                  </div>
                ))}
            </dl>
          </div>
        );
      })}
    </div>
  );
}

function formatMetric(value: unknown): string {
  if (typeof value === "number") {
    return Number.isInteger(value) ? String(value) : value.toFixed(4);
  }
  if (value == null) return "—";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}
