import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { RunStatusTimeline } from "@/components/RunStatusTimeline";
import type { ExperimentStatusResponse } from "@/lib/types";

function makeStatus(overrides: Partial<ExperimentStatusResponse> = {}): ExperimentStatusResponse {
  return {
    experiment_id: "00000000-0000-0000-0000-000000000000",
    status: "queued",
    progress: 0,
    message: null,
    ...overrides,
  } as ExperimentStatusResponse;
}

describe("RunStatusTimeline", () => {
  it("renders the queued state by default when no status is provided", () => {
    render(<RunStatusTimeline status={undefined} />);
    expect(screen.getByText(/status:/i)).toBeInTheDocument();
    expect(screen.getAllByText("queued").length).toBeGreaterThan(0);
    expect(screen.getByText(/0%/)).toBeInTheDocument();
  });

  it("renders the running state with progress and message", () => {
    render(
      <RunStatusTimeline
        status={makeStatus({ status: "running", progress: 0.42, message: "running classification" })}
      />,
    );
    expect(screen.getAllByText("running").length).toBeGreaterThan(0);
    expect(screen.getByText(/42%/)).toBeInTheDocument();
    expect(screen.getByText(/running classification/i)).toBeInTheDocument();
  });

  it("indicates failure when status is failed", () => {
    render(<RunStatusTimeline status={makeStatus({ status: "failed", progress: 0.7 })} />);
    expect(screen.getByText("failed")).toBeInTheDocument();
    expect(screen.getByText(/70%/)).toBeInTheDocument();
  });
});
