// Thin fetch wrapper acting as a request/response interceptor:
// - attaches the Bearer token to every request,
// - on 401, clears the token and redirects to /login (session expired).

import { API_BASE } from '../config';
import { clearToken, getToken } from '../auth/storage';

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers = new Headers(options.headers);
  headers.set('Accept', 'application/json');
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const resp = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (resp.status === 401) {
    // Token missing/expired/invalid -> force re-login (requirement 1.5).
    clearToken();
    if (window.location.pathname !== '/login') {
      window.location.assign('/login?error=session_expired');
    }
    throw new ApiError(401, 'Unauthorized');
  }

  if (!resp.ok) {
    throw new ApiError(resp.status, `Request failed: HTTP ${resp.status}`);
  }

  // 204 No Content -> no body.
  if (resp.status === 204) {
    return undefined as T;
  }
  return (await resp.json()) as T;
}

export interface CurrentUser {
  id: string;
  github_id: number;
  username: string;
  avatar_url: string | null;
}

export function fetchCurrentUser(): Promise<CurrentUser> {
  return apiFetch<CurrentUser>('/auth/me');
}

// ----------------------------- problems -----------------------------
export type ProblemStatus = 'not_started' | 'in_progress' | 'passed';

export interface ProblemListItem {
  id: number;
  number: number;
  title: string;
  difficulty: string;
  languages: string[];
  status: ProblemStatus;
}

export interface TopicGroup {
  topic_id: number;
  topic_name: string;
  order_index: number;
  problems: ProblemListItem[];
}

export interface ProblemDetail {
  id: number;
  number: number;
  title: string;
  description: string;
  difficulty: string;
  topic_id: number;
  topic_name: string;
  languages: string[];
  templates: Record<string, string>;
  status: ProblemStatus;
  samples: { input: string; expected_output: string }[];
  knowledge_tips: { title: string; content: string; code: Record<string, string> }[];
}

export interface ProblemFilters {
  topic_id?: number;
  difficulty?: string;
  status?: ProblemStatus;
}

export function listProblems(filters: ProblemFilters = {}): Promise<TopicGroup[]> {
  const params = new URLSearchParams();
  if (filters.topic_id != null) params.set('topic_id', String(filters.topic_id));
  if (filters.difficulty) params.set('difficulty', filters.difficulty);
  if (filters.status) params.set('status', filters.status);
  const qs = params.toString();
  return apiFetch<TopicGroup[]>(`/problems${qs ? `?${qs}` : ''}`);
}

export function getProblem(id: number): Promise<ProblemDetail> {
  return apiFetch<ProblemDetail>(`/problems/${id}`);
}

// --------------------------- submissions ---------------------------
export interface FailedCase {
  index: number;
  input: string;
  expected: string;
  actual: string;
}

export interface Submission {
  id: string;
  problem_id: number;
  language: string;
  status: string; // queued | running | done | system_error
  verdict: string | null; // AC | WA | TLE | MLE | CE | RE
  runtime_ms: number | null;
  failed_case: FailedCase | null;
  detail: string | null;
  created_at: string;
}

export interface SubmissionSummary {
  id: string;
  language: string;
  status: string;
  verdict: string | null;
  runtime_ms: number | null;
  created_at: string;
}

export interface SubmissionAccepted {
  id: string;
  status: string;
}

export function createSubmission(body: {
  problem_id: number;
  language: string;
  code: string;
  sample_only: boolean;
}): Promise<SubmissionAccepted> {
  return apiFetch<SubmissionAccepted>('/submissions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

export function getSubmission(id: string): Promise<Submission> {
  return apiFetch<Submission>(`/submissions/${id}`);
}

export function listProblemSubmissions(problemId: number): Promise<SubmissionSummary[]> {
  return apiFetch<SubmissionSummary[]>(`/problems/${problemId}/submissions`);
}

// ----------------------------- progress -----------------------------
export interface TopicProgress {
  topic_id: number;
  topic_name: string;
  total: number;
  passed: number;
  completion_rate: number;
}

export interface Progress {
  total_problems: number;
  passed: number;
  in_progress: number;
  completion_rate: number;
  topics: TopicProgress[];
}

export function getProgress(): Promise<Progress> {
  return apiFetch<Progress>('/me/progress');
}

// --------------------------- learning aids ---------------------------
export interface RoadmapProblem {
  id: number;
  number: number;
  title: string;
  status: ProblemStatus;
}

export interface RoadmapTopic {
  topic_id: number;
  name: string;
  order_index: number;
  pattern_summary: string | null;
  total: number;
  passed: number;
  completion_rate: number;
  problems: RoadmapProblem[];
}

export function getRoadmap(): Promise<RoadmapTopic[]> {
  return apiFetch<RoadmapTopic[]>('/roadmap');
}

export interface HintItem {
  level: number;
  content: string;
}

export interface HintsState {
  problem_id: number;
  total_levels: number;
  unlocked: HintItem[];
  next_level: number | null;
  next_is_full_solution: boolean;
}

export function getHints(problemId: number): Promise<HintsState> {
  return apiFetch<HintsState>(`/problems/${problemId}/hints`);
}

export function unlockHint(problemId: number, level: number): Promise<HintsState> {
  return apiFetch<HintsState>(`/problems/${problemId}/hints?level=${level}`);
}

export interface Pattern {
  pattern_name: string;
  mnemonic: string | null;
  templates: Record<string, string>;
}

export function getPatterns(q?: string): Promise<Pattern[]> {
  const qs = q ? `?q=${encodeURIComponent(q)}` : '';
  return apiFetch<Pattern[]>(`/patterns${qs}`);
}
