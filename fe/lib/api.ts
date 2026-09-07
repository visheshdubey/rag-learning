const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000"

export type Health = {
  status: string
  ollama: string
  llm_model: string
  embed_model: string
  indexed_chunks: number
  ollama_models: string[]
}

export type DocumentSource = {
  source: string
  chunks: number
}

export type DocumentStats = {
  chunks: number
  supported_types: string[]
  sources: DocumentSource[]
}

export type SourceHit = {
  source: string
  score: number
  text: string
  metadata: Record<string, unknown>
}

export type QueryResponse = {
  answer: string
  sources: SourceHit[]
}

export type IngestResult = {
  source: string
  documents: number
  chunks: number
}

async function readError(response: Response): Promise<string> {
  const payload = await response.json().catch(() => null)
  const detail = payload?.detail
  if (typeof detail === "string") {
    return detail
  }
  if (Array.isArray(detail)) {
    return detail
      .map((item) => (typeof item === "string" ? item : item?.msg))
      .filter(Boolean)
      .join(", ")
  }
  return response.statusText || "Request failed"
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, init)
  if (!response.ok) {
    throw new Error(await readError(response))
  }
  return (await response.json()) as T
}

export function getHealth() {
  return request<Health>("/health")
}

export function getDocuments() {
  return request<DocumentStats>("/documents")
}

export function queryRag(question: string, topK?: number) {
  return request<QueryResponse>("/query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, top_k: topK }),
  })
}

export async function ingestFiles(files: File[]) {
  const form = new FormData()
  for (const file of files) {
    form.append("files", file)
  }
  const payload = await request<{ ingested: IngestResult[] }>("/documents", {
    method: "POST",
    body: form,
  })
  return payload.ingested
}

export function deleteDocument(source: string) {
  return request<{ source: string; deleted_chunks: number }>(
    `/documents/${encodeURIComponent(source)}`,
    { method: "DELETE" }
  )
}
