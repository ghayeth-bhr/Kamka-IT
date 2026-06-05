const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  async uploadDocuments(files: File[]): Promise<import('./types').UploadResponse> {
    const form = new FormData();
    files.forEach((f) => form.append('files', f));
    const res = await fetch(`${BASE}/api/documents/upload`, {
      method: 'POST',
      body: form,
    });
    return handleResponse(res);
  },

  async listDocuments(): Promise<{ documents: import('./types').DocumentMeta[] }> {
    const res = await fetch(`${BASE}/api/documents`);
    return handleResponse(res);
  },

  async chat(
    message: string,
    sessionId?: string
  ): Promise<import('./types').ChatResponse> {
    const res = await fetch(`${BASE}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, session_id: sessionId }),
    });
    return handleResponse(res);
  },

  async clearSession(sessionId: string): Promise<void> {
    await fetch(`${BASE}/api/chat/clear?session_id=${sessionId}`, {
      method: 'POST',
    });
  },
};
