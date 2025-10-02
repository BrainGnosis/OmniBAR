import type { AgentInput, BenchmarkRow, RunRecord } from '@/types';
import type {
  BenchmarkRecord,
  RunBenchmarkSuiteResponse,
  RunHistoryEntry
} from '@/types/benchmarks';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

async function handleResponse<T>(response: Response): Promise<T> {
  const data = (await response.json()) as T;
  if (!response.ok) {
    throw new Error((data as any)?.message ?? 'Request failed');
  }
  return data;
}

export async function getBenchmarks(): Promise<BenchmarkRecord[]> {
  const response = await fetch(`${API_BASE}/benchmarks`, {
    credentials: 'include',
  });
  return handleResponse<BenchmarkRecord[]>(response);
}

export async function runOnce(input: AgentInput): Promise<RunRecord> {
  const response = await fetch(`${API_BASE}/api/run`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(input),
  });
  return handleResponse<RunRecord>(response);
}

export async function getRecentRuns(): Promise<RunHistoryEntry[]> {
  const response = await fetch(`${API_BASE}/runs`, {
    credentials: 'include',
  });
  return handleResponse<RunHistoryEntry[]>(response);
}

export async function runBenchmarkSuite(suite?: string): Promise<RunBenchmarkSuiteResponse> {
  const response = await fetch(`${API_BASE}/benchmarks/run`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ suite: suite ?? 'output', save: true }),
  });
  return handleResponse<RunBenchmarkSuiteResponse>(response);
}
