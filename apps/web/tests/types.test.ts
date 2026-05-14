import { describe, expect, it } from "vitest";

import {
  DatasetManifest,
  ExperimentCreateRequest,
  ExperimentResult,
  TaskLane,
} from "@/lib/types";

describe("zod schemas", () => {
  it("parses a dataset manifest", () => {
    const parsed = DatasetManifest.parse({
      id: "00000000-0000-0000-0000-000000000001",
      dataset_id: "demo/rotten_tomatoes",
      source: "hf",
      task_lanes: ["classification"],
      splits: ["train"],
      schema_mapping: { text_columns: ["text"], label_columns: ["label"] },
      row_count: 42,
      created_at: "2024-01-01T00:00:00Z",
    });
    expect(parsed.task_lanes).toContain(TaskLane.enum.classification);
  });

  it("rejects an experiment with zero task lanes", () => {
    expect(() =>
      ExperimentCreateRequest.parse({
        dataset_manifest_id: "00000000-0000-0000-0000-000000000001",
        task_lanes: [],
      }),
    ).toThrow();
  });

  it("applies defaults on experiment results", () => {
    const parsed = ExperimentResult.parse({
      experiment_id: "00000000-0000-0000-0000-000000000001",
      status: "completed",
      metrics: {},
    });
    expect(parsed.artifacts).toEqual([]);
    expect(parsed.summary).toEqual({});
  });

  it("applies defaults for sampling, generation, and report on minimal create request", () => {
    const parsed = ExperimentCreateRequest.parse({
      dataset_manifest_id: "00000000-0000-0000-0000-000000000001",
      task_lanes: ["classification"],
    });
    expect(parsed.sampling).toEqual({ max_rows: 200, strategy: "head", seed: 42 });
    expect(parsed.generation).toEqual({
      temperature: 0.2,
      top_p: 1.0,
      max_new_tokens: 256,
      batch_size: 8,
    });
    expect(parsed.report).toEqual({ enabled: true, include_references: true });
  });

  it("round-trips a full create request with explicit generation and report fields", () => {
    const parsed = ExperimentCreateRequest.parse({
      dataset_manifest_id: "00000000-0000-0000-0000-000000000001",
      task_lanes: ["classification", "summarization"],
      models: { classification: "distilbert-base-uncased-finetuned-sst-2-english" },
      sampling: { max_rows: 50, strategy: "head", seed: 7 },
      generation: { temperature: 0.7, top_p: 0.95, max_new_tokens: 128, batch_size: 4 },
      report: { enabled: false, include_references: false },
      notes: "smoke",
    });
    expect(parsed.report.enabled).toBe(false);
    expect(parsed.generation.temperature).toBeCloseTo(0.7);
    expect(parsed.sampling.max_rows).toBe(50);
  });

  it("rejects out-of-range generation params", () => {
    expect(() =>
      ExperimentCreateRequest.parse({
        dataset_manifest_id: "00000000-0000-0000-0000-000000000001",
        task_lanes: ["classification"],
        generation: { temperature: 5, top_p: 1, max_new_tokens: 1, batch_size: 1 },
      }),
    ).toThrow();
  });
});
