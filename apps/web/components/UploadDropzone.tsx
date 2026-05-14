"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "@/lib/api";

export function UploadDropzone() {
  const [file, setFile] = useState<File | null>(null);
  const [textColumns, setTextColumns] = useState("");
  const [labelColumns, setLabelColumns] = useState("");
  const qc = useQueryClient();

  const mutation = useMutation({
    mutationFn: async () => {
      if (!file) throw new Error("Select a file first.");
      return api.uploadDataset(file, {
        textColumns: textColumns || undefined,
        labelColumns: labelColumns || undefined,
      });
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["datasets"] });
    },
  });

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <h3 className="text-lg font-medium">Upload a file</h3>
      <p className="mt-1 text-xs text-slate-500">CSV, JSON, JSONL, TXT or XLSX (≤ 50MB).</p>

      <label htmlFor="upload-file" className="mt-4 block text-sm font-medium">
        Select file
      </label>
      <input
        id="upload-file"
        type="file"
        accept=".csv,.json,.jsonl,.txt,.xlsx"
        onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        className="mt-1 block w-full text-sm"
      />

      <div className="mt-3 grid grid-cols-2 gap-3">
        <label className="block text-sm">
          <span className="font-medium">Text columns</span>
          <input
            placeholder="e.g. text,review"
            className="mt-1 w-full rounded-md border border-slate-300 bg-white px-2 py-1 text-sm"
            value={textColumns}
            onChange={(e) => setTextColumns(e.target.value)}
          />
        </label>
        <label className="block text-sm">
          <span className="font-medium">Label columns</span>
          <input
            placeholder="e.g. label"
            className="mt-1 w-full rounded-md border border-slate-300 bg-white px-2 py-1 text-sm"
            value={labelColumns}
            onChange={(e) => setLabelColumns(e.target.value)}
          />
        </label>
      </div>

      <button
        type="button"
        onClick={() => mutation.mutate()}
        disabled={mutation.isPending || !file}
        className="mt-4 rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
      >
        {mutation.isPending ? "Uploading…" : "Upload"}
      </button>
      {mutation.isError && (
        <p className="mt-2 text-xs text-red-600">
          {mutation.error instanceof Error ? mutation.error.message : "Upload failed."}
        </p>
      )}
      {mutation.data && (
        <p className="mt-2 text-xs text-green-600">Manifest {mutation.data.id.slice(0, 8)} created.</p>
      )}
    </div>
  );
}
