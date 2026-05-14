import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { MetricCards } from "@/components/MetricCards";

describe("MetricCards", () => {
  it("renders one card per populated lane", () => {
    render(
      <MetricCards
        metrics={{
          classification: { model_id: "mock:cls", f1_macro: 0.87, accuracy: 0.9 },
          summarization: null,
          qa: null,
          instruct: null,
        }}
      />,
    );
    expect(screen.getByText("classification")).toBeInTheDocument();
    expect(screen.getAllByText("f1_macro").length).toBeGreaterThan(0);
    expect(screen.getAllByText("0.8700").length).toBeGreaterThan(0);
  });

  it("renders fallback when empty", () => {
    render(
      <MetricCards
        metrics={{ classification: null, summarization: null, qa: null, instruct: null }}
      />,
    );
    expect(screen.getByText(/No metrics recorded/i)).toBeInTheDocument();
  });
});
