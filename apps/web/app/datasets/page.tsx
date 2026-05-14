"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { api } from "@/lib/api";
import { UploadDropzone } from "@/components/UploadDropzone";
import { DatasetPicker } from "@/components/DatasetPicker";

export default function DatasetsPage() {
  const query = useQuery({ queryKey: ["datasets"], queryFn: () => api.listDatasets() });

  return (
    <section className="flex flex-col gap-8">
      <div>
        <h1 className="text-2xl font-semibold">Datasets</h1>
        <p className="text-sm text-slate-600">
          Import a curated Hugging Face benchmark or upload your own CSV/JSON/XLSX file.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <DatasetPicker />
        <UploadDropzone />
      </div>

      <div>
        <h2 className="text-lg font-medium">Imported datasets</h2>
        {query.isLoading && <p className="mt-2 text-sm">Loading…</p>}
        {query.isError && (
          <p className="mt-2 text-sm text-red-600">Unable to reach the API.</p>
        )}
        {query.data && query.data.length === 0 && (
          <p className="mt-2 text-sm text-slate-500">No datasets yet.</p>
        )}
        {query.data && query.data.length > 0 && (
          <ul className="mt-3 divide-y divide-slate-200 rounded-lg border border-slate-200">
            {query.data.map((m) => (
              <li key={m.id} className="flex items-center justify-between px-4 py-3">
                <div>
                  <p className="font-medium">{m.dataset_id}</p>
                  <p className="text-xs text-slate-500">
                    {m.row_count} rows · lanes {m.task_lanes.join(", ") || "—"}
                  </p>
                </div>
                <Link
                  href={`/experiments/new?manifest=${m.id}`}
                  className="text-sm font-medium text-brand-600 hover:text-brand-700"
                >
                  Use →
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
