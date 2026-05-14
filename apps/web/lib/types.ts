import { z } from "zod";

export const TaskLane = z.enum(["classification", "summarization", "qa", "instruct"]);
export type TaskLane = z.infer<typeof TaskLane>;

export const DatasetSource = z.enum(["hf", "upload"]);
export type DatasetSource = z.infer<typeof DatasetSource>;

export const ExperimentStatus = z.enum([
  "queued",
  "running",
  "completed",
  "failed",
  "cancelled",
]);
export type ExperimentStatus = z.infer<typeof ExperimentStatus>;

export const DatasetSchemaMapping = z.object({
  text_columns: z.array(z.string()).min(1),
  label_columns: z.array(z.string()).default([]),
  question_column: z.string().nullable().optional(),
  context_column: z.string().nullable().optional(),
  answer_column: z.string().nullable().optional(),
});
export type DatasetSchemaMapping = z.infer<typeof DatasetSchemaMapping>;

export const DatasetManifest = z.object({
  id: z.string().uuid(),
  dataset_id: z.string(),
  source: DatasetSource,
  task_lanes: z.array(TaskLane).default([]),
  splits: z.array(z.string()).default([]),
  schema_mapping: DatasetSchemaMapping,
  row_count: z.number().int().nonnegative(),
  license: z.string().nullable().optional(),
  snapshot: z.string().nullable().optional(),
  created_at: z.string(),
});
export type DatasetManifest = z.infer<typeof DatasetManifest>;

export const DatasetPreviewResponse = z.object({
  manifest_id: z.string().uuid(),
  columns: z.array(z.string()),
  rows: z.array(z.record(z.unknown())),
  total_rows: z.number().int().nonnegative(),
});
export type DatasetPreviewResponse = z.infer<typeof DatasetPreviewResponse>;

export const MetricsByLane = z.object({
  classification: z.record(z.unknown()).nullable().optional(),
  summarization: z.record(z.unknown()).nullable().optional(),
  qa: z.record(z.unknown()).nullable().optional(),
  instruct: z.record(z.unknown()).nullable().optional(),
});
export type MetricsByLane = z.infer<typeof MetricsByLane>;

export const ArtifactRef = z.object({
  type: z.string(),
  path: z.string(),
  bytes: z.number().int().nullable().optional(),
});
export type ArtifactRef = z.infer<typeof ArtifactRef>;

export const ExperimentStatusResponse = z.object({
  experiment_id: z.string().uuid(),
  status: ExperimentStatus,
  progress: z.number().min(0).max(1).default(0),
  message: z.string().nullable().optional(),
});
export type ExperimentStatusResponse = z.infer<typeof ExperimentStatusResponse>;

export const ExperimentResult = z.object({
  experiment_id: z.string().uuid(),
  status: ExperimentStatus,
  summary: z.record(z.unknown()).default({}),
  metrics: MetricsByLane,
  artifacts: z.array(ArtifactRef).default([]),
  error: z.string().nullable().optional(),
});
export type ExperimentResult = z.infer<typeof ExperimentResult>;

export const ExperimentSummary = z.object({
  id: z.string().uuid(),
  dataset_manifest_id: z.string().uuid(),
  task_lanes: z.array(TaskLane),
  status: ExperimentStatus,
  created_at: z.string(),
});
export type ExperimentSummary = z.infer<typeof ExperimentSummary>;

export const SamplingConfig = z
  .object({
    max_rows: z.number().int().min(1).max(5000).default(200),
    strategy: z.enum(["head", "random", "stratified"]).default("head"),
    seed: z.number().int().nonnegative().default(42),
  })
  .default({ max_rows: 200, strategy: "head", seed: 42 });
export type SamplingConfig = z.infer<typeof SamplingConfig>;

export const GenerationParams = z
  .object({
    temperature: z.number().min(0).max(2).default(0.2),
    top_p: z.number().min(0).max(1).default(1.0),
    max_new_tokens: z.number().int().min(1).max(4096).default(256),
    batch_size: z.number().int().min(1).max(256).default(8),
  })
  .default({ temperature: 0.2, top_p: 1.0, max_new_tokens: 256, batch_size: 8 });
export type GenerationParams = z.infer<typeof GenerationParams>;

export const ReportOptions = z
  .object({
    enabled: z.boolean().default(true),
    include_references: z.boolean().default(true),
  })
  .default({ enabled: true, include_references: true });
export type ReportOptions = z.infer<typeof ReportOptions>;

export const ExperimentCreateRequest = z.object({
  dataset_manifest_id: z.string().uuid(),
  task_lanes: z.array(TaskLane).min(1),
  models: z.record(TaskLane, z.string()).default({}),
  sampling: SamplingConfig,
  generation: GenerationParams,
  report: ReportOptions,
  notes: z.string().max(2000).nullable().optional(),
});
export type ExperimentCreateRequest = z.infer<typeof ExperimentCreateRequest>;

export const AgentReferenceItem = z.object({
  title: z.string(),
  url: z.string().url(),
  type: z.enum(["paper", "docs", "dataset", "model_card", "benchmark"]),
  why_it_matters: z.string(),
});
export type AgentReferenceItem = z.infer<typeof AgentReferenceItem>;

export const ResearchPlanResponse = z.object({
  plan_markdown: z.string(),
  references: z.array(AgentReferenceItem).default([]),
});
export type ResearchPlanResponse = z.infer<typeof ResearchPlanResponse>;

export const ResearchReportResponse = z.object({
  report_id: z.string().uuid(),
  path: z.string(),
  reference_count: z.number().int().nonnegative(),
});
export type ResearchReportResponse = z.infer<typeof ResearchReportResponse>;

export const APIErrorBody = z.object({
  error: z.object({
    code: z.string(),
    message: z.string(),
    details: z.record(z.unknown()).default({}),
  }),
});
export type APIErrorBody = z.infer<typeof APIErrorBody>;
