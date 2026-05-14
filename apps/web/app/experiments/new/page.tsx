"use client";

import { Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";

import { ExperimentWizard } from "@/components/ExperimentWizard";

function NewExperimentInner() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const manifestId = searchParams.get("manifest") ?? "";

  return (
    <ExperimentWizard
      initialManifestId={manifestId}
      onStarted={(id) => router.push(`/experiments/${id}`)}
    />
  );
}

export default function NewExperimentPage() {
  return (
    <section className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold">New experiment</h1>
        <p className="text-sm text-slate-600">
          Configure task lanes, models and sampling, then launch a run.
        </p>
      </div>
      <Suspense fallback={<p className="text-sm text-slate-500">Loading…</p>}>
        <NewExperimentInner />
      </Suspense>
    </section>
  );
}
