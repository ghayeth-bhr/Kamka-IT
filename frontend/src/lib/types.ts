export interface DocumentMeta {
  id: string;
  filename: string;
  chunks_count: number;
  created_at: string;
}

export interface SourceChunk {
  filename: string;
  page: number | null;
  chunk_index: number;
  content_preview: string;
}

export interface AgentStep {
  tool: string;
  input: string;
  output_summary: string;
}

export interface ChatResponse {
  answer: string;
  sources: SourceChunk[];
  agent_steps: AgentStep[];
  session_id: string;
}

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: SourceChunk[];
  agent_steps?: AgentStep[];
  timestamp: Date;
}

export interface UploadResponse {
  documents: DocumentMeta[];
  message: string;
}
