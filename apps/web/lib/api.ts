import { z, type ZodTypeAny } from "zod";
import {
  APIErrorBody,
  DatasetManifest,
  DatasetPreviewResponse,
  ExperimentCreateRequest,
  ExperimentResult,
  ExperimentStatusResponse,
  ExperimentSummary,
  ResearchPlanResponse,
  ResearchReportResponse,
} from "@/lib/types";

const DEFAULT_BASE = resolveDefaultBase();

function resolveDefaultBase(): string {
  const envBase =
    typeof process !== "undefined" ? process.env.NEXT_PUBLIC_API_BASE_URL : undefined;
  if (envBase) return envBase;
  if (typeof process !== "undefined" && process.env.NODE_ENV === "production") {
    throw new Error(
      "NEXT_PUBLIC_API_BASE_URL must be set in production. " +
        "Refusing to fall back to http://localhost:8000.",
    );
  }
  return "http://localhost:8000/api/v1";
}

export class ApiError extends Error {
  code: string;
  status: number;
  details: Record<string, unknown>;

  constructor(code: string, message: string, status: number, details: Record<string, unknown>) {
    super(message);
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

async function request<T extends ZodTypeAny>(
  path: string,
  init: RequestInit,
  schema: T,
  baseUrl = DEFAULT_BASE,
): Promise<z.infer<T>> {
  const resp = await fetch(`${baseUrl}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      ...(init.headers ?? {}),
    },
  });
  const text = await resp.text();
  if (!resp.ok) {
    let code = "HTTP_ERROR";
    let message = `Request failed: ${resp.status}`;
    let details: Record<string, unknown> = {};
    try {
      const parsed = APIErrorBody.parse(JSON.parse(text));
      code = parsed.error.code;
      message = parsed.error.message;
      details = parsed.error.details;
    } catch {
      message = text || message;
    }
    throw new ApiError(code, message, resp.status, details);
  }
  const json = text ? JSON.parse(text) : null;
  return schema.parse(json);
}

export const api = {
  listDatasets: (base?: string) =>
    request("/datasets", { method: "GET" }, z.array(DatasetManifest), base),

  previewDataset: (id: string, limit = 10, base?: string) =>
    request(`/datasets/${id}/preview?limit=${limit}`, { method: "GET" }, DatasetPreviewResponse, base),

  importHf: (
    payload: { dataset_id: string; split?: string; max_rows?: number },
    base?: string,
  ) =>
    request(
      "/datasets/import/hf",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ split: "train", max_rows: 200, ...payload }),
      },
      DatasetManifest,
      base,
    ),

  uploadDataset: async (
    file: File,
    opts: { textColumns?: string; labelColumns?: string } = {},
    base?: string,
  ): Promise<DatasetManifest> => {
    const form = new FormData();
    form.append("file", file);
    if (opts.textColumns) form.append("text_columns", opts.textColumns);
    if (opts.labelColumns) form.append("label_columns", opts.labelColumns);
    return request(
      "/datasets/import/upload",
      { method: "POST", body: form },
      DatasetManifest,
      base,
    );
  },

  createExperiment: (payload: ExperimentCreateRequest, base?: string) =>
    request(
      "/experiments",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      },
      ExperimentStatusResponse,
      base,
    ),

  listExperiments: (base?: string) =>
    request("/experiments", { method: "GET" }, z.array(ExperimentSummary), base),

  experimentStatus: (id: string, base?: string) =>
    request(`/experiments/${id}/status`, { method: "GET" }, ExperimentStatusResponse, base),

  experimentResult: (id: string, base?: string) =>
    request(`/experiments/${id}/result`, { method: "GET" }, ExperimentResult, base),

  cancelExperiment: (id: string, base?: string) =>
    request(`/experiments/${id}/cancel`, { method: "POST" }, ExperimentStatusResponse, base),

  planResearch: (payload: { topic: string; task_lanes: string[] }, base?: string) =>
    request(
      "/agent/plan",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      },
      ResearchPlanResponse,
      base,
    ),

  generateReport: (payload: { experiment_id: string; include_references?: boolean }, base?: string) =>
    request(
      "/agent/report",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      },
      ResearchReportResponse,
      base,
    ),

  getReportMarkdown: async (id: string, base = DEFAULT_BASE): Promise<string> => {
    const resp = await fetch(`${base}/reports/${id}`, {
      headers: { Accept: "text/plain" },
    });
    if (!resp.ok) {
      throw new ApiError("HTTP_ERROR", `Report fetch failed: ${resp.status}`, resp.status, {});
    }
    return resp.text();
  },
};
