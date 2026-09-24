import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("DocLens frontend", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("submits a question and renders unique source documents by display name", async () => {
    const user = userEvent.setup();
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse({
        answer: "Visible dashboards refresh every 30 seconds.",
        sources: [
          {
            source_id: "specifications/dashboard-refresh.md",
            filename: "dashboard-refresh.md",
            display_filename: "Dashboard Refresh.md",
            category: "specification",
            origin: "bundled",
            chunk_index: 0,
            chunk_id: "chunk-1",
          },
          {
            source_id: "specifications/dashboard-refresh.md",
            filename: "dashboard-refresh.md",
            display_filename: "Dashboard Refresh.md",
            category: "specification",
            origin: "bundled",
            chunk_index: 1,
            chunk_id: "chunk-2",
          },
          {
            source_id: "faqs/dashboards-and-alerts.md",
            filename: "dashboards-and-alerts.md",
            display_filename: "Dashboards & Alerts.md",
            category: "faq",
            origin: "bundled",
            chunk_index: 0,
            chunk_id: "chunk-3",
          },
        ],
      }),
    );

    render(<App />);
    await user.type(screen.getByLabelText("Question"), "How often does it refresh?");
    await user.click(screen.getByRole("button", { name: "Ask DocLens" }));

    expect(await screen.findByText("Visible dashboards refresh every 30 seconds.")).toBeInTheDocument();
    const sourceRows = screen.getAllByTestId("source-row");
    expect(sourceRows).toHaveLength(2);
    expect(within(sourceRows[0]).getByText("Dashboard Refresh.md")).toBeInTheDocument();
    expect(within(sourceRows[1]).getByText("Dashboards & Alerts.md")).toBeInTheDocument();
    expect(screen.queryByText("dashboard-refresh.md")).not.toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith(
      "/api/query",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ question: "How often does it refresh?" }),
      }),
    );
  });

  it("indexes the bundled corpus and reports the chunk count", async () => {
    const user = userEvent.setup();
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse({ chunks_indexed: 45 }));

    render(<App />);
    await user.click(screen.getByRole("button", { name: "Index bundled corpus" }));

    expect(await screen.findByText("45 chunks indexed")).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith("/api/corpus/index", { method: "POST" });
  });

  it("shows a query loading state while the API request is pending", async () => {
    const user = userEvent.setup();
    let resolveRequest!: (response: Response) => void;
    vi.mocked(fetch).mockReturnValueOnce(
      new Promise<Response>((resolve) => {
        resolveRequest = resolve;
      }),
    );

    render(<App />);
    await user.type(screen.getByLabelText("Question"), "What is the refresh rate?");
    await user.click(screen.getByRole("button", { name: "Ask DocLens" }));

    expect(screen.getByRole("button", { name: "Searching…" })).toBeDisabled();
    resolveRequest(jsonResponse({ answer: "Every 30 seconds.", sources: [] }));
    expect(await screen.findByText("Every 30 seconds.")).toBeInTheDocument();
  });

  it("uploads an accepted document and reports its original display name", async () => {
    const user = userEvent.setup();
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(
        {
          filename: "Q3_Customer_Success_Final.md",
          source_id: "uploads/Q3_Customer_Success_Final.md",
          chunks_indexed: 2,
        },
        201,
      ),
    );
    const file = new File(["# Customer success"], "Q3 Customer Success (Final)!.md", {
      type: "text/markdown",
    });

    render(<App />);
    await user.upload(screen.getByLabelText("Choose a file"), file);

    expect(
      await screen.findByText("Q3 Customer Success (Final)!.md indexed in 2 chunks"),
    ).toBeInTheDocument();
    const [, request] = vi.mocked(fetch).mock.calls[0];
    expect(fetch).toHaveBeenCalledWith(
      "/api/documents/upload",
      expect.objectContaining({ method: "POST" }),
    );
    expect(request?.body).toBeInstanceOf(FormData);
  });

  it("shows API errors without replacing the previous result", async () => {
    const user = userEvent.setup();
    vi.mocked(fetch)
      .mockResolvedValueOnce(
        jsonResponse({ answer: "First answer", sources: [] }),
      )
      .mockResolvedValueOnce(
        jsonResponse({ detail: "Answer generation is temporarily unavailable." }, 502),
      );

    render(<App />);
    const question = screen.getByLabelText("Question");
    await user.type(question, "First question");
    await user.click(screen.getByRole("button", { name: "Ask DocLens" }));
    expect(await screen.findByText("First answer")).toBeInTheDocument();

    await user.clear(question);
    await user.type(question, "Second question");
    await user.click(screen.getByRole("button", { name: "Ask DocLens" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "DocLens couldn't complete the request. Please try again.",
    );
    expect(screen.getByText("First answer")).toBeInTheDocument();
  });

  it("shows a safe message when the backend cannot be reached", async () => {
    const user = userEvent.setup();
    vi.mocked(fetch).mockRejectedValueOnce(new TypeError("Failed to fetch"));

    render(<App />);
    await user.type(screen.getByLabelText("Question"), "Is the backend available?");
    await user.click(screen.getByRole("button", { name: "Ask DocLens" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "DocLens couldn't reach the backend. Please try again.",
    );
    expect(screen.queryByText("Failed to fetch")).not.toBeInTheDocument();
  });
});
