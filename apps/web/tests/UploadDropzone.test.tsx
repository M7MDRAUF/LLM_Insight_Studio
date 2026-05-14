import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { UploadDropzone } from "@/components/UploadDropzone";

vi.mock("@/lib/api", () => ({
  api: {
    uploadDataset: vi.fn().mockResolvedValue({ id: "abcdef1234567890" }),
  },
}));

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe("UploadDropzone", () => {
  it("renders an accessible file input with an associated label", () => {
    render(<UploadDropzone />, { wrapper });
    const input = screen.getByLabelText(/select file/i);
    expect(input).toHaveAttribute("type", "file");
    expect(input).toHaveAttribute("id", "upload-file");
  });

  it("disables the upload button until a file is chosen", () => {
    render(<UploadDropzone />, { wrapper });
    const button = screen.getByRole("button", { name: /upload/i });
    expect(button).toBeDisabled();
  });

  it("enables the upload button after selecting a file and shows success", async () => {
    render(<UploadDropzone />, { wrapper });
    const input = screen.getByLabelText(/select file/i) as HTMLInputElement;
    const file = new File(["text\nhello\n"], "tiny.csv", { type: "text/csv" });
    fireEvent.change(input, { target: { files: [file] } });

    const button = screen.getByRole("button", { name: /upload/i });
    expect(button).not.toBeDisabled();

    fireEvent.click(button);
    await waitFor(() => expect(screen.getByText(/Manifest abcdef12 created/i)).toBeInTheDocument());
  });
});
