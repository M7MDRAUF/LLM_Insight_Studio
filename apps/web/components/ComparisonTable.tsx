"use client";

import type { JSX } from "react";

import type { ExperimentResult } from "@/lib/types";

interface Props {
  results: ExperimentResult[];
}

const LANES = ["classification", "summarization", "qa", "instruct"] as const;
type Lane = (typeof LANES)[number];

/** Primary metric to display prominently per lane */
const PRIMARY_METRIC: Record<Lane, string> = {
  classification: "f1_macro",
  summarization: "rougeL",
  qa: "f1",
  instruct: "f1_macro",
};

/** Human-readable metric labels */
const METRIC_LABELS: Record<string, string> = {
  accuracy: "Accuracy",
  precision_macro: "Precision",
  recall_macro: "Recall",
  f1_macro: "F1 Macro",
  support: "Samples",
  latency_ms: "Latency",
  model_id: "Model",
  rouge1: "ROUGE-1",
  rouge2: "ROUGE-2",
  rougeL: "ROUGE-L",
  exact_match: "Exact Match",
  f1: "F1",
  evidence_hit_rate: "Evidence Hit",
};

/** Per-lane visual configuration */
const LANE_CONFIG: Record<Lane, { label: string; color: string; bg: string; border: string; dot: string }> = {
  classification: {
    label: "Classification",
    color: "text-violet-700",
    bg: "bg-violet-50",
    border: "border-violet-300",
    dot: "bg-violet-500",
  },
  summarization: {
    label: "Summarization",
    color: "text-blue-700",
    bg: "bg-blue-50",
    border: "border-blue-300",
    dot: "bg-blue-500",
  },
  qa: {
    label: "Q&A",
    color: "text-emerald-700",
    bg: "bg-emerald-50",
    border: "border-emerald-300",
    dot: "bg-emerald-500",
  },
  instruct: {
    label: "Instruct",
    color: "text-orange-700",
    bg: "bg-orange-50",
    border: "border-orange-300",
    dot: "bg-orange-500",
  },
};

/** Metrics that are on a 0–1 quality scale */
const QUALITY_METRICS = new Set([
  "accuracy",
  "precision_macro",
  "recall_macro",
  "f1_macro",
  "rouge1",
  "rouge2",
  "rougeL",
  "exact_match",
  "f1",
  "evidence_hit_rate",
]);

function scoreColor(v: number): string {
  if (v >= 0.7) return "text-emerald-600";
  if (v >= 0.4) return "text-amber-500";
  return "text-rose-500";
}

function barColor(v: number): string {
  if (v >= 0.7) return "bg-emerald-500";
  if (v >= 0.4) return "bg-amber-400";
  return "bg-rose-400";
}

function ScoreBar({ value }: { value: number }): JSX.Element {
  const pct = Math.min(Math.max(value * 100, 0), 100);
  return (
    <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-slate-200">
      <div
        className={`h-1.5 rounded-full transition-all ${barColor(value)}`}
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

/** Find the best experiment id for each lane by primary metric */
function findBest(results: ExperimentResult[]): Record<Lane, string | null> {
  const best = { classification: null, summarization: null, qa: null, instruct: null } as Record<
    Lane,
    string | null
  >;
  for (const lane of LANES) {
    let bestVal = -Infinity;
    let bestId: string | null = null;
    for (const r of results) {
      const m = r.metrics[lane] as Record<string, unknown> | null | undefined;
      if (!m) continue;
      const primary = PRIMARY_METRIC[lane];
      const val = typeof m[primary] === "number" ? (m[primary] as number) : -Infinity;
      if (val > bestVal) {
        bestVal = val;
        bestId = r.experiment_id;
      }
    }
    best[lane] = bestId;
  }
  return best;
}

interface MetricCellProps {
  metrics: Record<string, unknown>;
  lane: Lane;
  isBest: boolean;
}

function MetricCell({ metrics, lane, isBest }: MetricCellProps): JSX.Element {
  const config = LANE_CONFIG[lane];
  const primaryKey = PRIMARY_METRIC[lane];
  const primaryVal =
    typeof metrics[primaryKey] === "number" ? (metrics[primaryKey] as number) : null;

  const modelId = typeof metrics.model_id === "string" ? metrics.model_id : null;
  const latency = typeof metrics.latency_ms === "number" ? (metrics.latency_ms as number) : null;
  const support = typeof metrics.support === "number" ? (metrics.support as number) : null;

  const secondaryQualityKeys = Object.keys(metrics).filter(
    (k) =>
      k !== "model_id" &&
      k !== "latency_ms" &&
      k !== "support" &&
      k !== primaryKey &&
      QUALITY_METRICS.has(k),
  );

  return (
    <div
      className={`relative rounded-xl border p-3 transition-shadow hover:shadow-md ${
        isBest
          ? `${config.border} ${config.bg} shadow-sm`
          : "border-slate-200 bg-white"
      }`}
    >
      {/* Best badge */}
      {isBest && (
        <span
          className={`absolute -top-2.5 right-2 rounded-full border px-2 py-0.5 text-[10px] font-bold tracking-wide ${config.color} ${config.bg} ${config.border}`}
        >
          ★ Best
        </span>
      )}

      {/* Primary metric — large display */}
      {primaryVal !== null ? (
        <div className="mb-3">
          <div className={`text-3xl font-extrabold tabular-nums leading-none ${scoreColor(primaryVal)}`}>
            {(primaryVal * 100).toFixed(1)}
            <span className="ml-0.5 text-base font-semibold">%</span>
          </div>
          <div className="mt-0.5 text-[11px] font-medium uppercase tracking-widest text-slate-400">
            {METRIC_LABELS[primaryKey] ?? primaryKey}
          </div>
          <ScoreBar value={primaryVal} />
        </div>
      ) : (
        <div className="mb-3 text-xl font-bold text-slate-300">—</div>
      )}

      {/* Secondary quality metrics grid */}
      {secondaryQualityKeys.length > 0 && (
        <div className="mb-3 grid grid-cols-2 gap-x-3 gap-y-2 border-t border-slate-100 pt-2">
          {secondaryQualityKeys.map((k) => {
            const val = metrics[k];
            const num = typeof val === "number" ? (val as number) : null;
            return (
              <div key={k}>
                <div
                  className={`text-sm font-semibold tabular-nums ${
                    num !== null && QUALITY_METRICS.has(k) ? scoreColor(num) : "text-slate-700"
                  }`}
                >
                  {num !== null ? `${(num * 100).toFixed(1)}%` : "—"}
                </div>
                <div className="text-[10px] text-slate-400">{METRIC_LABELS[k] ?? k}</div>
              </div>
            );
          })}
        </div>
      )}

      {/* Footer: samples + latency */}
      <div className="flex items-center justify-between gap-2 border-t border-slate-100 pt-2 text-[11px]">
        {support !== null && (
          <span className="text-slate-500">
            <span className="font-semibold text-slate-700">{Math.round(support)}</span> samples
          </span>
        )}
        {latency !== null && (
          <span className="flex items-center gap-0.5 text-slate-500">
            <svg
              className="h-3 w-3 text-amber-400"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z"
                clipRule="evenodd"
              />
            </svg>
            <span className="font-semibold text-slate-700">{latency.toFixed(2)}</span>ms
          </span>
        )}
      </div>

      {/* Model badge */}
      {modelId && (
        <div
          className="mt-2 truncate rounded-md bg-slate-100 px-2 py-1 font-mono text-[10px] text-slate-600"
          title={modelId}
        >
          {modelId}
        </div>
      )}
    </div>
  );
}

export function ComparisonTable({ results }: Props): JSX.Element {
  const best = findBest(results);
  const activeLanes = LANES.filter((lane) => results.some((r) => r.metrics[lane] != null));

  return (
    <div className="flex flex-col gap-5">
      {/* Best-per-task summary banner */}
      <div className="rounded-2xl border border-slate-200 bg-gradient-to-br from-slate-50 to-white p-5">
        <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-slate-400">
          Best performer by task
        </p>
        <div className="flex flex-wrap gap-3">
          {activeLanes.map((lane) => {
            const config = LANE_CONFIG[lane];
            const winner = best[lane];
            const winnerResult = winner ? results.find((r) => r.experiment_id === winner) : null;
            const winnerMetrics = winnerResult?.metrics[lane] as
              | Record<string, unknown>
              | null
              | undefined;
            const primaryVal =
              winnerMetrics && typeof winnerMetrics[PRIMARY_METRIC[lane]] === "number"
                ? (winnerMetrics[PRIMARY_METRIC[lane]] as number)
                : null;

            return (
              <div
                key={lane}
                className={`flex min-w-[130px] flex-col gap-1 rounded-xl border px-4 py-3 ${config.bg} ${config.border}`}
              >
                <div className="flex items-center gap-1.5">
                  <span className={`h-2 w-2 rounded-full ${config.dot}`} />
                  <span className={`text-[11px] font-bold uppercase tracking-wider ${config.color}`}>
                    {config.label}
                  </span>
                </div>
                <div className="font-mono text-lg font-extrabold text-slate-800">
                  {winner ? winner.slice(0, 8) : "—"}
                </div>
                {primaryVal !== null && (
                  <div className={`text-sm font-semibold ${scoreColor(primaryVal)}`}>
                    {(primaryVal * 100).toFixed(1)}% {METRIC_LABELS[PRIMARY_METRIC[lane]]}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Main table */}
      <div className="overflow-x-auto rounded-2xl border border-slate-200 shadow-sm">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50">
              <th className="w-32 px-4 py-3 text-left">
                <span className="text-xs font-semibold uppercase tracking-widest text-slate-400">
                  Run
                </span>
              </th>
              {activeLanes.map((lane) => {
                const config = LANE_CONFIG[lane];
                return (
                  <th key={lane} className="min-w-[200px] px-4 py-3 text-left">
                    <span
                      className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold ${config.bg} ${config.color} ${config.border}`}
                    >
                      <span className={`h-1.5 w-1.5 rounded-full ${config.dot}`} />
                      {config.label}
                    </span>
                    <div className="mt-1 text-[10px] font-normal text-slate-400">
                      ↑ {METRIC_LABELS[PRIMARY_METRIC[lane]] ?? PRIMARY_METRIC[lane]}
                    </div>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {results.map((r, idx) => {
              const activeLanesForRow = LANES.filter((l) => r.metrics[l] != null);
              return (
                <tr
                  key={r.experiment_id}
                  className={idx % 2 === 0 ? "bg-white" : "bg-slate-50/40"}
                >
                  {/* Experiment ID cell */}
                  <td className="px-4 py-4 align-top">
                    <span className="inline-block rounded-lg bg-slate-100 px-2.5 py-1.5 font-mono text-xs font-bold text-slate-700 shadow-sm">
                      {r.experiment_id.slice(0, 8)}
                    </span>
                    {activeLanesForRow.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {activeLanesForRow.map((l) => {
                          const c = LANE_CONFIG[l];
                          return (
                            <span
                              key={l}
                              className={`h-1.5 w-1.5 rounded-full ${c.dot}`}
                              title={c.label}
                            />
                          );
                        })}
                      </div>
                    )}
                  </td>

                  {/* Lane metric cells */}
                  {activeLanes.map((lane) => {
                    const m = r.metrics[lane] as Record<string, unknown> | null | undefined;
                    return (
                      <td key={lane} className="px-4 py-4 align-top">
                        {m ? (
                          <MetricCell
                            metrics={m}
                            lane={lane}
                            isBest={best[lane] === r.experiment_id}
                          />
                        ) : (
                          <div className="flex h-16 items-center justify-center rounded-xl border border-dashed border-slate-200 text-lg text-slate-200">
                            —
                          </div>
                        )}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap items-center gap-4 rounded-xl border border-slate-100 bg-slate-50 px-4 py-2.5 text-[11px] text-slate-500">
        <span className="font-semibold text-slate-600">Score legend:</span>
        <span className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" />
          <span>≥ 70% — Good</span>
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-amber-400" />
          <span>40–70% — Fair</span>
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-rose-400" />
          <span>&lt; 40% — Low</span>
        </span>
        <span className="ml-auto text-slate-400">
          ⚡ = inference latency &nbsp;|&nbsp; ★ Best = highest primary metric
        </span>
      </div>
    </div>
  );
}
