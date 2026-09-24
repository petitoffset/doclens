import { ChangeEvent, FormEvent, useMemo, useState } from "react";

import {
  AnswerSource,
  askQuestion,
  indexBundledCorpus,
  uploadDocument,
} from "./api";

type Feedback = {
  kind: "success" | "error";
  message: string;
};

function uniqueDocuments(sources: AnswerSource[]): AnswerSource[] {
  return [...new Map(sources.map((source) => [source.source_id, source])).values()];
}

function categoryLabel(category: string): string {
  return category
    .split("-")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Something went wrong.";
}

export default function App() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);
  const [sources, setSources] = useState<AnswerSource[]>([]);
  const [querying, setQuerying] = useState(false);
  const [indexing, setIndexing] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [queryError, setQueryError] = useState<string | null>(null);
  const [corpusFeedback, setCorpusFeedback] = useState<Feedback | null>(null);
  const [uploadFeedback, setUploadFeedback] = useState<Feedback | null>(null);

  const documents = useMemo(() => uniqueDocuments(sources), [sources]);

  async function handleQuery(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalizedQuestion = question.trim();
    if (!normalizedQuestion || querying) return;

    setQuerying(true);
    setQueryError(null);
    try {
      const result = await askQuestion(normalizedQuestion);
      setAnswer(result.answer);
      setSources(result.sources);
    } catch (error) {
      setQueryError(errorMessage(error));
    } finally {
      setQuerying(false);
    }
  }

  async function handleCorpusIndex() {
    setIndexing(true);
    setCorpusFeedback(null);
    try {
      const result = await indexBundledCorpus();
      setCorpusFeedback({
        kind: "success",
        message: `${result.chunks_indexed} chunks indexed`,
      });
    } catch (error) {
      setCorpusFeedback({ kind: "error", message: errorMessage(error) });
    } finally {
      setIndexing(false);
    }
  }

  async function handleUpload(event: ChangeEvent<HTMLInputElement>) {
    const input = event.currentTarget;
    const file = input.files?.[0];
    if (!file || uploading) return;

    setUploading(true);
    setUploadFeedback(null);
    try {
      const result = await uploadDocument(file);
      setUploadFeedback({
        kind: "success",
        message: `${file.name} indexed in ${result.chunks_indexed} ${
          result.chunks_indexed === 1 ? "chunk" : "chunks"
        }`,
      });
    } catch (error) {
      setUploadFeedback({ kind: "error", message: errorMessage(error) });
    } finally {
      setUploading(false);
      input.value = "";
    }
  }

  return (
    <div className="page-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="DocLens home">
          <span className="brand-mark" aria-hidden="true">D</span>
          <span>DocLens</span>
        </a>
        <div className="workspace-label">
          <span className="status-dot" aria-hidden="true" />
          Internal workspace
        </div>
      </header>

      <main className="workspace">
        <header className="workspace-heading">
          <div>
            <p className="eyebrow">Knowledge search</p>
            <h1>Company documentation</h1>
            <p>Ask a question and inspect the documents behind the answer.</p>
          </div>
          <span className="corpus-badge">PulseBoard corpus</span>
        </header>

        <div className="workspace-grid">
          <section className="query-panel" aria-labelledby="query-heading">
            <form onSubmit={handleQuery}>
              <div className="section-heading">
                <h2 id="query-heading">Ask DocLens</h2>
                <span>01 / Query</span>
              </div>
              <label className="visually-hidden" htmlFor="question">Question</label>
              <textarea
                id="question"
                value={question}
                maxLength={2000}
                onChange={(event) => setQuestion(event.target.value)}
                placeholder="How often does a visible PulseBoard dashboard refresh?"
                rows={5}
              />
              <div className="query-actions">
                <p>Answers are grounded in indexed documents.</p>
                <button
                  className="primary-button"
                  type="submit"
                  disabled={!question.trim() || querying}
                >
                  {querying ? "Searching…" : "Ask DocLens"}
                </button>
              </div>
              {queryError && <p className="feedback error" role="alert">{queryError}</p>}
            </form>

            <div className="answer-panel" aria-live="polite" aria-busy={querying}>
              <div className="section-heading">
                <h2>Answer</h2>
                <span>02 / Result</span>
              </div>
              {answer === null ? (
                <p className="empty-answer">Your grounded answer will appear here.</p>
              ) : (
                <>
                  <p className="answer-copy">{answer}</p>
                  <div className="sources-heading">
                    <span>Retrieved sources</span>
                    <span>· {documents.length} {documents.length === 1 ? "document" : "documents"}</span>
                  </div>
                  {documents.length > 0 ? (
                    <ul className="source-list">
                      {documents.map((source) => (
                        <li key={source.source_id} data-testid="source-row">
                          <span className="document-icon" aria-hidden="true">▤</span>
                          <span className="source-name">{source.display_filename}</span>
                          <span className="source-category">{categoryLabel(source.category)}</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="no-sources">No supporting documents were retrieved.</p>
                  )}
                </>
              )}
            </div>
          </section>

          <aside className="document-panel" aria-label="Document preparation">
            <section>
              <div className="section-heading">
                <h2>Prepare documents</h2>
                <span>Corpus</span>
              </div>
              <p className="aside-copy">Index the bundled PulseBoard docs before asking questions.</p>
              <button
                className="secondary-button"
                type="button"
                onClick={handleCorpusIndex}
                disabled={indexing}
              >
                {indexing ? "Indexing…" : "Index bundled corpus"}
              </button>
              {corpusFeedback && (
                <p className={`feedback ${corpusFeedback.kind}`} role={corpusFeedback.kind === "error" ? "alert" : "status"}>
                  <span className="feedback-dot" aria-hidden="true" />
                  {corpusFeedback.message}
                </p>
              )}
            </section>

            <section className="upload-section">
              <h2>Add a document</h2>
              <label className={`upload-control ${uploading ? "disabled" : ""}`}>
                <span className="upload-icon" aria-hidden="true">↑</span>
                <span className="upload-title">{uploading ? "Uploading…" : "Choose a file"}</span>
                <span className="upload-hint">Markdown or plain text · .md, .txt</span>
                <input
                  type="file"
                  aria-label="Choose a file"
                  accept=".md,.txt,text/markdown,text/plain"
                  disabled={uploading}
                  onChange={handleUpload}
                />
              </label>
              {uploadFeedback && (
                <p className={`feedback ${uploadFeedback.kind}`} role={uploadFeedback.kind === "error" ? "alert" : "status"}>
                  <span className="feedback-dot" aria-hidden="true" />
                  {uploadFeedback.message}
                </p>
              )}
            </section>
          </aside>
        </div>
      </main>
    </div>
  );
}
