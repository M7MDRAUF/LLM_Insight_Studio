"use client";

import { useEffect } from "react";

interface Props {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function ExperimentDetailError({ error, reset }: Props) {
  useEffect(() => {
    console.error("ExperimentDetail error:", error);
  }, [error]);

  return (
    <section
      role="alert"
      className="rounded-lg border border-red-200 bg-red-50 p-6 text-sm text-red-700"
    >
      <h1 className="text-lg font-semibold">Could not load experiment</h1>
      <p className="mt-2">{error.message || "Unexpected error."}</p>
      <button
        type="button"
        onClick={reset}
        className="mt-4 rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
      >
        Try again
      </button>
    </section>
  );
}
