import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { ReportViewer } from "@/components/ReportViewer";

const SAMPLE_MD = `# Evaluation Report

This report covers **classification** and _summarization_ lanes.

## Results table

| Lane | F1 | Accuracy |
|------|----|----------|
| cls  | 0.87 | 0.90   |

See [paper](https://arxiv.org/abs/1234.5678) for details.
`;

describe("ReportViewer", () => {
  it("renders a heading as <h1>, not raw #", () => {
    render(<ReportViewer markdown={SAMPLE_MD} />);
    const h1 = screen.getByRole("heading", { level: 1 });
    expect(h1).toBeInTheDocument();
    expect(h1.textContent).toBe("Evaluation Report");
  });

  it("renders GFM table rows", () => {
    render(<ReportViewer markdown={SAMPLE_MD} />);
    expect(screen.getByText("Lane")).toBeInTheDocument();
    expect(screen.getByText("0.87")).toBeInTheDocument();
  });

  it("renders links with noopener noreferrer", () => {
    render(<ReportViewer markdown={SAMPLE_MD} />);
    const link = screen.getByRole("link", { name: /paper/i });
    expect(link).toHaveAttribute("href", "https://arxiv.org/abs/1234.5678");
    expect(link).toHaveAttribute("rel", "noopener noreferrer");
    expect(link).toHaveAttribute("target", "_blank");
  });

  it("renders bold and italic inline", () => {
    render(<ReportViewer markdown={SAMPLE_MD} />);
    expect(screen.getByText("classification")).toBeInTheDocument();
  });

  it("renders empty markdown without crashing", () => {
    render(<ReportViewer markdown="" />);
    const article = document.querySelector("article");
    expect(article).toBeInTheDocument();
  });
});
