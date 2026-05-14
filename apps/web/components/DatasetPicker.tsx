"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "@/lib/api";

const PRESETS = [
  { key: "rotten_tomatoes", label: "Rotten Tomatoes (classification)", dataset_id: "cornell-movie-review-data/rotten_tomatoes" },
  { key: "squad", label: "SQuAD (QA)", dataset_id: "rajpurkar/squad" },
  { key: "billsum", label: "BillSum (summarization)", dataset_id: "billsum" },
];

export function DatasetPicker() {
  const [datasetId, setDatasetId] = useState(PRESETS[0].dataset_id);
  const [split, setSplit] = useState("train");
  const [maxRows, setMaxRows] = useState(200);
  const qc = useQueryClient();

  const mutation = useMutation({
    mutationFn: () => api.importHf({ dataset_id: datasetId, split, max_rows: maxRows }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["datasets"] });
    },
  });

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <h3 className="text-lg font-medium">Hugging Face dataset</h3>
      <p className="mt-1 text-xs text-slate-500">Load a curated benchmark via the datasets API.</p>

      <label className="mt-4 block text-sm font-medium">Preset</label>
      <select
        className="mt-1 w-full rounded-md border border-slate-300 bg-white px-2 py-1 text-sm"
        value={datasetId}
        onChange={(e) => setDatasetId(e.target.value)}
      >
        {PRESETS.map((p) => (
          <option key={p.key} value={p.dataset_id}>
            {p.label}
          </option>
        ))}
      </select>

      <div className="mt-4 grid grid-cols-2 gap-3">
        <label className="block text-sm">
          <span className="font-medium">Split</span>
          <input
            className="mt-1 w-full rounded-md border border-slate-300 bg-white px-2 py-1 text-sm"
            value={split}
            onChange={(e) => setSplit(e.target.value)}
          />
        </label>
        <label className="block text-sm">
          <span className="font-medium">Max rows</span>
          <input
            type="number"
            min={1}
            max={10000}
            className="mt-1 w-full rounded-md border border-slate-300 bg-white px-2 py-1 text-sm"
            value={maxRows}
            onChange={(e) => setMaxRows(Number(e.target.value))}
          />
        </label>
      </div>

      <button
        type="button"
        onClick={() => mutation.mutate()}
        disabled={mutation.isPending}
        className="mt-4 rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
      >
        {mutation.isPending ? "Importing…" : "Import"}
      </button>

      {mutation.isError && (
        <p className="mt-2 text-xs text-red-600">Import failed — is the API reachable?</p>
      )}
      {mutation.data && (
        <p className="mt-2 text-xs text-green-600">Imported {mutation.data.row_count} rows.</p>
      )}
    </div>
  );
}
