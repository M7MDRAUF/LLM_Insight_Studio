"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import { Controller, useForm } from "react-hook-form";
import { z } from "zod";

import { api } from "@/lib/api";

// ── zod schema ────────────────────────────────────────────────────────────────
const LANES = ["classification", "summarization", "qa", "instruct"] as const;

const WizardSchema = z.object({
  manifestId: z.string().min(1, "Please select a dataset"),
  lanes: z
    .array(z.enum(LANES))
    .min(1, "Select at least one task lane"),
  maxRows: z
    .number({ invalid_type_error: "Must be a number" })
    .int("Must be a whole number")
    .min(1, "Min 1 row")
    .max(5000, "Max 5 000 rows"),
  notes: z.string().max(2000, "Max 2 000 characters").optional(),
  // Advanced — generation
  temperature: z
    .number({ invalid_type_error: "Must be a number" })
    .min(0, "Min 0")
    .max(2, "Max 2"),
  topP: z
    .number({ invalid_type_error: "Must be a number" })
    .min(0, "Min 0")
    .max(1, "Max 1"),
  maxNewTokens: z
    .number({ invalid_type_error: "Must be a number" })
    .int("Must be a whole number")
    .min(1, "Min 1")
    .max(4096, "Max 4 096"),
  batchSize: z
    .number({ invalid_type_error: "Must be a number" })
    .int("Must be a whole number")
    .min(1, "Min 1")
    .max(256, "Max 256"),
  // Advanced — report
  reportEnabled: z.boolean(),
  includeReferences: z.boolean(),
});

type WizardValues = z.infer<typeof WizardSchema>;

// ── props ─────────────────────────────────────────────────────────────────────
interface Props {
  initialManifestId?: string;
  onStarted: (id: string) => void;
}

export function ExperimentWizard({ initialManifestId = "", onStarted }: Props) {
  const datasets = useQuery({ queryKey: ["datasets"], queryFn: () => api.listDatasets() });

  const {
    register,
    handleSubmit,
    control,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<WizardValues>({
    resolver: zodResolver(WizardSchema),
    defaultValues: {
      manifestId: initialManifestId,
      lanes: ["classification"],
      maxRows: 100,
      notes: "",
      temperature: 0.2,
      topP: 1.0,
      maxNewTokens: 256,
      batchSize: 8,
      reportEnabled: true,
      includeReferences: true,
    },
  });

  // Sync prop changes into the form (e.g. after dataset import)
  useEffect(() => {
    if (initialManifestId) setValue("manifestId", initialManifestId);
  }, [initialManifestId, setValue]);

  const mutation = useMutation({
    mutationFn: (values: WizardValues) =>
      api.createExperiment({
        dataset_manifest_id: values.manifestId,
        task_lanes: values.lanes,
        models: {},
        sampling: { max_rows: values.maxRows, strategy: "head", seed: 42 },
        generation: {
          temperature: values.temperature,
          top_p: values.topP,
          max_new_tokens: values.maxNewTokens,
          batch_size: values.batchSize,
        },
        report: {
          enabled: values.reportEnabled,
          include_references: values.includeReferences,
        },
        notes: values.notes || null,
      }),
    onSuccess: (res) => onStarted(res.experiment_id),
  });

  const onSubmit = handleSubmit((values) => mutation.mutate(values));

  return (
    <form
      onSubmit={onSubmit}
      className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm"
    >
      <div className="grid gap-5">
        {/* Dataset manifest */}
        <div>
          <label htmlFor="wizard-manifest" className="block text-sm font-medium">
            Dataset manifest
          </label>
          <select
            id="wizard-manifest"
            {...register("manifestId")}
            className="mt-1 w-full rounded-md border border-slate-300 bg-white px-2 py-2 text-sm"
          >
            <option value="">Select a dataset…</option>
            {datasets.data?.map((m) => (
              <option key={m.id} value={m.id}>
                {m.dataset_id} ({m.row_count} rows)
              </option>
            ))}
          </select>
          {errors.manifestId && (
            <p role="alert" className="mt-1 text-xs text-red-600">
              {errors.manifestId.message}
            </p>
          )}
        </div>

        {/* Task lanes */}
        <fieldset>
          <legend className="text-sm font-medium">Task lanes</legend>
          <Controller
            control={control}
            name="lanes"
            render={({ field }) => (
              <div className="mt-2 flex flex-wrap gap-2">
                {LANES.map((lane) => {
                  const checked = field.value.includes(lane);
                  return (
                    <label
                      key={lane}
                      htmlFor={`lane-${lane}`}
                      className={
                        "cursor-pointer rounded-full border px-3 py-1 text-xs " +
                        (checked
                          ? "border-brand-600 bg-brand-50 text-brand-700"
                          : "border-slate-300 text-slate-700")
                      }
                    >
                      <input
                        id={`lane-${lane}`}
                        type="checkbox"
                        className="sr-only"
                        checked={checked}
                        onChange={() =>
                          field.onChange(
                            checked
                              ? field.value.filter((x) => x !== lane)
                              : [...field.value, lane],
                          )
                        }
                      />
                      {lane}
                    </label>
                  );
                })}
              </div>
            )}
          />
          {errors.lanes && (
            <p role="alert" className="mt-1 text-xs text-red-600">
              {errors.lanes.message}
            </p>
          )}
        </fieldset>

        {/* Max rows */}
        <div>
          <label htmlFor="wizard-max-rows" className="block text-sm font-medium">
            Max rows
          </label>
          <input
            id="wizard-max-rows"
            type="number"
            min={1}
            max={5000}
            {...register("maxRows", { valueAsNumber: true })}
            className="mt-1 w-40 rounded-md border border-slate-300 bg-white px-2 py-1 text-sm"
          />
          {errors.maxRows && (
            <p role="alert" className="mt-1 text-xs text-red-600">
              {errors.maxRows.message}
            </p>
          )}
        </div>

        {/* Notes */}
        <div>
          <label htmlFor="wizard-notes" className="block text-sm font-medium">
            Notes
          </label>
          <textarea
            id="wizard-notes"
            rows={3}
            {...register("notes")}
            className="mt-1 w-full rounded-md border border-slate-300 bg-white px-2 py-1 text-sm"
          />
          {errors.notes && (
            <p role="alert" className="mt-1 text-xs text-red-600">
              {errors.notes.message}
            </p>
          )}
        </div>

        {/* Advanced (generation + report) */}
        <details className="rounded-md border border-slate-200">
          <summary className="cursor-pointer px-3 py-2 text-sm font-medium">
            Advanced options
          </summary>
          <div className="grid gap-4 px-3 pb-3 pt-2 sm:grid-cols-2">
            <div>
              <label htmlFor="wizard-temperature" className="block text-sm font-medium">
                Temperature
              </label>
              <input
                id="wizard-temperature"
                type="number"
                step="0.1"
                min={0}
                max={2}
                {...register("temperature", { valueAsNumber: true })}
                className="mt-1 w-40 rounded-md border border-slate-300 bg-white px-2 py-1 text-sm"
              />
              {errors.temperature && (
                <p role="alert" className="mt-1 text-xs text-red-600">
                  {errors.temperature.message}
                </p>
              )}
            </div>
            <div>
              <label htmlFor="wizard-top-p" className="block text-sm font-medium">
                Top-p
              </label>
              <input
                id="wizard-top-p"
                type="number"
                step="0.05"
                min={0}
                max={1}
                {...register("topP", { valueAsNumber: true })}
                className="mt-1 w-40 rounded-md border border-slate-300 bg-white px-2 py-1 text-sm"
              />
              {errors.topP && (
                <p role="alert" className="mt-1 text-xs text-red-600">
                  {errors.topP.message}
                </p>
              )}
            </div>
            <div>
              <label htmlFor="wizard-max-new-tokens" className="block text-sm font-medium">
                Max new tokens
              </label>
              <input
                id="wizard-max-new-tokens"
                type="number"
                min={1}
                max={4096}
                {...register("maxNewTokens", { valueAsNumber: true })}
                className="mt-1 w-40 rounded-md border border-slate-300 bg-white px-2 py-1 text-sm"
              />
              {errors.maxNewTokens && (
                <p role="alert" className="mt-1 text-xs text-red-600">
                  {errors.maxNewTokens.message}
                </p>
              )}
            </div>
            <div>
              <label htmlFor="wizard-batch-size" className="block text-sm font-medium">
                Batch size
              </label>
              <input
                id="wizard-batch-size"
                type="number"
                min={1}
                max={256}
                {...register("batchSize", { valueAsNumber: true })}
                className="mt-1 w-40 rounded-md border border-slate-300 bg-white px-2 py-1 text-sm"
              />
              {errors.batchSize && (
                <p role="alert" className="mt-1 text-xs text-red-600">
                  {errors.batchSize.message}
                </p>
              )}
            </div>
            <div className="sm:col-span-2 flex flex-wrap gap-4">
              <label
                htmlFor="wizard-report-enabled"
                className="flex items-center gap-2 text-sm"
              >
                <input
                  id="wizard-report-enabled"
                  type="checkbox"
                  {...register("reportEnabled")}
                />
                Generate research report after run
              </label>
              <label
                htmlFor="wizard-include-references"
                className="flex items-center gap-2 text-sm"
              >
                <input
                  id="wizard-include-references"
                  type="checkbox"
                  {...register("includeReferences")}
                />
                Include curated references
              </label>
            </div>
          </div>
        </details>

        {/* Submit */}
        <div>
          <button
            type="submit"
            disabled={isSubmitting || mutation.isPending}
            className="rounded-md bg-brand-600 px-5 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
          >
            {isSubmitting || mutation.isPending ? "Starting…" : "Start experiment"}
          </button>
          {mutation.isError && (
            <p className="mt-2 text-xs text-red-600">
              {mutation.error instanceof Error ? mutation.error.message : "Failed to start."}
            </p>
          )}
        </div>
      </div>
    </form>
  );
}
