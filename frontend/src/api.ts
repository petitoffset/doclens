export interface AnswerSource {
  source_id: string;
  filename: string;
  display_filename: string;
  category: string;
  origin: string;
  chunk_index: number;
  chunk_id: string;
}

export interface QueryResponse {
  answer: string;
  sources: AnswerSource[];
}

export interface CorpusIndexResponse {
  chunks_indexed: number;
}

export interface UploadIndexResponse {
  filename: string;
  source_id: string;
  chunks_indexed: number;
}

async function requestJson<T>(url: string, options: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(url, options);
  } catch {
    throw new Error("DocLens couldn't reach the backend. Please try again.");
  }

  if (!response.ok) {
    const message = response.status >= 500
      ? "DocLens couldn't complete the request. Please try again."
      : "DocLens couldn't process the request. Check your input and try again.";
    throw new Error(message);
  }
  return (await response.json()) as T;
}

export function askQuestion(question: string): Promise<QueryResponse> {
  return requestJson<QueryResponse>("/api/query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
}

export function indexBundledCorpus(): Promise<CorpusIndexResponse> {
  return requestJson<CorpusIndexResponse>("/api/corpus/index", {
    method: "POST",
  });
}

export function uploadDocument(file: File): Promise<UploadIndexResponse> {
  const body = new FormData();
  body.append("file", file);
  return requestJson<UploadIndexResponse>("/api/documents/upload", {
    method: "POST",
    body,
  });
}
