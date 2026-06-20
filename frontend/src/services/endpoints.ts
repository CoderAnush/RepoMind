import apiClient from './api';
import type {
  TokenResponse, User, Repository, RepositoryCreate,
  Documentation, Diagram, Report, ChatRequest, ChatResponse, ProcessingJob
} from '../types';

// ─── Auth ──────────────────────────────────────────────────────────────────────

export const authService = {
  login: async (email: string, password: string): Promise<TokenResponse> => {
    const params = new URLSearchParams();
    params.append('username', email);
    params.append('password', password);
    const { data } = await apiClient.post<TokenResponse>('/auth/token', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return data;
  },

  register: async (email: string, password: string, full_name: string): Promise<User> => {
    const { data } = await apiClient.post<User>('/auth/register', {
      email, password, full_name, role: 'DEVELOPER',
    });
    return data;
  },

  me: async (): Promise<User> => {
    const { data } = await apiClient.get<User>('/auth/me');
    return data;
  },

  getGitHubUrl: async (redirectUri: string): Promise<{ url: string; is_mock: boolean }> => {
    const { data } = await apiClient.get<{ url: string; is_mock: boolean }>(`/auth/github/url?redirect_uri=${encodeURIComponent(redirectUri)}`);
    return data;
  },

  githubLogin: async (code: string): Promise<TokenResponse> => {
    const { data } = await apiClient.post<TokenResponse>('/auth/github/login', { code });
    return data;
  },
};

// ─── Repositories ──────────────────────────────────────────────────────────────

export const repoService = {
  list: async (): Promise<Repository[]> => {
    const { data } = await apiClient.get<Repository[]>('/repositories');
    return data;
  },

  get: async (id: string): Promise<Repository> => {
    const { data } = await apiClient.get<Repository>(`/repositories/${id}`);
    return data;
  },

  submit: async (payload: RepositoryCreate): Promise<Repository> => {
    const { data } = await apiClient.post<Repository>('/repositories', payload);
    return data;
  },

  jobs: async (id: string): Promise<ProcessingJob[]> => {
    const { data } = await apiClient.get<ProcessingJob[]>(`/repositories/${id}/jobs`);
    return data;
  },
};

// ─── Documentation ─────────────────────────────────────────────────────────────

export const docsService = {
  list: async (repoId: string): Promise<Documentation[]> => {
    const { data } = await apiClient.get<Documentation[]>(`/repositories/${repoId}/docs`);
    return data;
  },
};

// ─── Diagrams ──────────────────────────────────────────────────────────────────

export const diagramService = {
  list: async (repoId: string): Promise<Diagram[]> => {
    const { data } = await apiClient.get<Diagram[]>(`/repositories/${repoId}/diagrams`);
    return data;
  },

  svgUrl: (repoId: string, diagramId: string): string =>
    `${import.meta.env.VITE_API_URL || 'https://repomind-api-z6x5.onrender.com/api/v1'}/repositories/${repoId}/diagrams/${diagramId}/svg`,
};

// ─── Reports ───────────────────────────────────────────────────────────────────

export const reportService = {
  get: async (repoId: string, type: 'SECURITY' | 'QUALITY'): Promise<Report> => {
    const { data } = await apiClient.get<Report>(`/repositories/${repoId}/reports/${type}`);
    return data;
  },
};

// ─── Chat ──────────────────────────────────────────────────────────────────────
 
export const chatService = {
  send: async (payload: ChatRequest): Promise<ChatResponse> => {
    const { data } = await apiClient.post<ChatResponse>('/chat', payload);
    return data;
  },
};

// ─── Code Review ───────────────────────────────────────────────────────────────

export const reviewService = {
  get: async (repoId: string): Promise<any> => {
    const { data } = await apiClient.get<any>(`/repositories/${repoId}/review`);
    return data;
  },
  trigger: async (repoId: string): Promise<any> => {
    const { data } = await apiClient.post<any>(`/repositories/${repoId}/review`);
    return data;
  },
};

// ─── Architecture Map ─────────────────────────────────────────────────────────

export const architectureService = {
  get: async (repoId: string): Promise<any> => {
    const { data } = await apiClient.get<any>(`/repositories/${repoId}/architecture`);
    return data;
  },
};


