import type { AgentInput, BenchmarkRow, RunRecord } from '@/types';
import type {
  BenchmarkRecord,
  RunBenchmarkSuiteResponse,
  RunHistoryEntry
} from '@/types/benchmarks';
import { getStoredThreshold } from '@/lib/threshold';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

async function handleResponse<T>(response: Response): Promise<T> {
  const data = (await response.json()) as T;
  if (!response.ok) {
    const payload = data as any;
    const message = payload?.message ?? payload?.detail ?? 'Request failed';
    throw new Error(message);
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
  const threshold = getStoredThreshold();
  const response = await fetch(`${API_BASE}/benchmarks/run`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ suite: suite ?? 'output', save: true, threshold }),
  });
  return handleResponse<RunBenchmarkSuiteResponse>(response);
}

export async function clearRunHistory(): Promise<void> {
  const response = await fetch(`${API_BASE}/runs`, {
    method: 'DELETE',
    credentials: 'include',
  });
  await handleResponse<Record<string, unknown>>(response);
}

export async function getLLMHealth(): Promise<{ status: string; latency: number; model: string; output: string }> {
  const response = await fetch(`${API_BASE}/health/llm`, {
    credentials: 'include',
  });
  return handleResponse(response);
}

export async function runLLMSmokeTest(): Promise<{ status: string; latency: number; output: string }> {
  const response = await fetch(`${API_BASE}/benchmarks/smoke`, {
    method: 'POST',
    credentials: 'include',
  });
  return handleResponse(response);
}
