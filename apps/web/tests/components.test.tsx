import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { ExperimentWizard } from "@/components/ExperimentWizard";
import { DatasetPicker } from "@/components/DatasetPicker";

// ── shared helpers ────────────────────────────────────────────────────────────
function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

// ── ExperimentWizard ─────────────────────────────────────────────────────────
describe("ExperimentWizard", () => {
  it("renders the dataset select and all 4 task-lane checkboxes", () => {
    render(<ExperimentWizard onStarted={vi.fn()} />, { wrapper });
    expect(screen.getByText(/dataset manifest/i)).toBeInTheDocument();
    for (const lane of ["classification", "summarization", "qa", "instruct"]) {
      expect(screen.getByLabelText(new RegExp(lane, "i"))).toBeInTheDocument();
    }
  });

  it("shows validation error when submitted without a manifest", async () => {
    render(<ExperimentWizard onStarted={vi.fn()} />, { wrapper });
    // Submit the form without selecting a dataset
    fireEvent.submit(screen.getByRole("button", { name: /start/i }).closest("form")!);
    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent(/select a dataset/i),
    );
  });

  it("shows no validation errors when manifest and lane are both present", async () => {
    render(
      <ExperimentWizard initialManifestId="test-manifest-uuid" onStarted={vi.fn()} />,
      { wrapper },
    );
    // Submit a fully-valid form — no alert roles should appear
    fireEvent.submit(screen.getByRole("button", { name: /start/i }).closest("form")!);
    // Allow React to settle; no alert should be rendered
    await waitFor(() => {
      const alerts = document.querySelectorAll("[role='alert']");
      expect(alerts.length).toBe(0);
    });
  });

  it("shows validation error when all lanes are unchecked on submit", async () => {
    render(
      <ExperimentWizard initialManifestId="test-manifest-uuid" onStarted={vi.fn()} />,
      { wrapper },
    );
    // Uncheck the pre-selected classification lane
    const clsCheckbox = screen.getByLabelText(/classification/i);
    fireEvent.click(clsCheckbox);
    // Submit — should surface the lane validation message
    fireEvent.submit(screen.getByRole("button", { name: /start/i }).closest("form")!);
    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent(/at least one task lane/i),
    );
  });

  it("renders the Max rows input with default value 100", () => {
    render(<ExperimentWizard onStarted={vi.fn()} />, { wrapper });
    const input = screen.getByLabelText(/max rows/i) as HTMLInputElement;
    expect(input.value).toBe("100");
  });

  it("renders the Notes textarea", () => {
    render(<ExperimentWizard onStarted={vi.fn()} />, { wrapper });
    expect(screen.getByLabelText(/notes/i)).toBeInTheDocument();
  });

  it("renders the Advanced section with generation defaults", () => {
    render(<ExperimentWizard onStarted={vi.fn()} />, { wrapper });
    const temperature = screen.getByLabelText(/temperature/i) as HTMLInputElement;
    const topP = screen.getByLabelText(/top-p/i) as HTMLInputElement;
    const maxNewTokens = screen.getByLabelText(/max new tokens/i) as HTMLInputElement;
    const batchSize = screen.getByLabelText(/batch size/i) as HTMLInputElement;
    expect(temperature.value).toBe("0.2");
    expect(topP.value).toBe("1");
    expect(maxNewTokens.value).toBe("256");
    expect(batchSize.value).toBe("8");
  });

  it("renders the Advanced section with report toggles enabled by default", () => {
    render(<ExperimentWizard onStarted={vi.fn()} />, { wrapper });
    const reportEnabled = screen.getByLabelText(/generate research report/i) as HTMLInputElement;
    const includeReferences = screen.getByLabelText(/include curated references/i) as HTMLInputElement;
    expect(reportEnabled.checked).toBe(true);
    expect(includeReferences.checked).toBe(true);
  });
});

// ── DatasetPicker ─────────────────────────────────────────────────────────────
describe("DatasetPicker", () => {
  it("renders the heading and import button", () => {
    render(<DatasetPicker />, { wrapper });
    expect(screen.getByText(/hugging face dataset/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /import/i })).toBeInTheDocument();
  });

  it("renders three presets in the dropdown", () => {
    render(<DatasetPicker />, { wrapper });
    const options = screen.getAllByRole("option");
    expect(options.length).toBe(3);
  });

  it("renders Split and Max rows inputs", () => {
    render(<DatasetPicker />, { wrapper });
    expect(screen.getByLabelText(/split/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/max rows/i)).toBeInTheDocument();
  });

  it("import button is enabled by default", () => {
    render(<DatasetPicker />, { wrapper });
    expect(screen.getByRole("button", { name: /import/i })).not.toBeDisabled();
  });
});
