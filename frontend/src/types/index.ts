// ─── Core Domain Types ────────────────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
  github_access_token?: string;
}

export interface Repository {
  id: string;
  name: string;
  github_url: string;
  branch: string;
  status: 'PENDING' | 'CLONING' | 'INDEXING' | 'COMPLETE' | 'FAILED';
  owner_id: string;
  metadata_info?: RepositoryMetadata;
  created_at: string;
}

export interface RepositoryMetadata {
  total_files: number;
  total_loc: number;
  languages: Record<string, number>;
  languages_loc_percentage: Record<string, number>;
  file_list?: string[];
}

export interface RepositoryCreate {
  github_url: string;
  branch?: string;
}

export interface Documentation {
  id: string;
  repository_id: string;
  doc_type: string;
  title: string;
  content: string;
  updated_at: string;
}

export interface Diagram {
  id: string;
  repository_id: string;
  diagram_type: 'ARCHITECTURE' | 'CLASS' | 'SEQUENCE' | 'DEPENDENCY';
  format: string;
  code: string;
  created_at: string;
}

export interface Report {
  id: string;
  repository_id: string;
  report_type: 'SECURITY' | 'QUALITY';
  score: number;
  findings: Finding[];
  created_at: string;
}

export interface Finding {
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';
  category: string;
  message: string;
  file?: string;
  line?: number;
}

export interface ChatEvidence {
  retrieved_files: string[];
  retrieved_chunks: {
    id: string;
    file_path: string;
    similarity_score: number;
    symbol: string;
  }[];
  graph_trace: {
    path: string[];
    visited_nodes: number;
    depth: number;
  };
  confidence_score: number;
  confidence_label: 'HIGH' | 'MEDIUM' | 'LOW';
  answer_type: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  message: string;
  references?: CodeReference[];
  evidence?: ChatEvidence;
  timestamp?: Date;
}

export interface CodeReference {
  file_path: string;
  symbol_name?: string;
  snippet: string;
  language?: string;
}

export interface ChatRequest {
  repository_id: string;
  message: string;
  conversation_id?: string | null;
}

export interface ChatResponse {
  answer: string;
  references?: CodeReference[];
  evidence?: ChatEvidence;
  conversation_id?: string;
}

export interface ProcessingJob {
  id: string;
  repository_id: string;
  status: 'QUEUED' | 'RUNNING' | 'SUCCESS' | 'FAILED';
  step: string;
  error_message?: string | null;
  retries: number;
  created_at: string;
  updated_at: string;
}

export interface QdrantHealth {
  status: 'healthy' | 'degraded' | 'error';
  mode: string;
  qdrant_url: string;
  qdrant_url_env_set: boolean;
  qdrant_api_key_set: boolean;
  collections: string[];
}

// ─── UI / App State Types ─────────────────────────────────────────────────────

export type RepoStatus = Repository['status'];

export type DiagramType = 'ARCHITECTURE' | 'CLASS' | 'SEQUENCE' | 'DEPENDENCY';

export type ReportType = 'SECURITY' | 'QUALITY';

export type SeverityLevel = Finding['severity'];

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}
