export type BenchmarkRecord = {
  id: string;
  name: string;
  iterations: number;
  successRate: number;
  status: 'pending' | 'running' | 'success' | 'failed';
  updatedAt: string;
  suite?: string;
  latencySeconds?: number;
  tokensUsed?: number;
  costUsd?: number;
  confidenceReported?: number | null;
  confidenceCalibrated?: number | null;
  errorFlags?: string[];
  history?: Array<{
    timestamp: string | null;
    objective?: string | null;
    result?: boolean;
    message?: string | null;
    expected?: string | null;
    actual?: unknown;
    failureCategory?: string | null;
    latencySeconds?: number;
  }>;
  latestFailure?: {
    objective?: string;
    reason?: string;
    category?: string;
    expected?: string | null;
    actual?: unknown;
  } | null;
};

export type BenchmarkSummary = {
  total: number;
  success: number;
  failed: number;
};

export type LiveRun = {
  id: string;
  benchmarkName: string;
  status: 'running' | 'queued' | 'completed';
  currentIteration: number;
  totalIterations: number;
  startedAt: string | null;
};

export type FailureInsight = {
  id: string;
  benchmarkId: string;
  benchmarkName: string;
  failureRate: number;
  lastFailureAt: string;
  topIssues: string[];
  recommendedFix: string;
  failureCategory?: string;
  inputs?: Record<string, unknown>;
  history?: Array<{
    timestamp: string | null;
    objective?: string | null;
    result?: boolean;
    message?: string | null;
    expected?: string | null;
    actual?: unknown;
    failureCategory?: string | null;
    latencySeconds?: number;
  }>;
};

export type Recommendation = {
  id: string;
  title: string;
  impact: string;
  summary: string;
  action: string;
};

export type RunBenchmarkSuiteResponse = {
  benchmarks: BenchmarkRecord[];
  summary: BenchmarkSummary;
  liveRuns: LiveRun[];
  failureInsights: FailureInsight[];
  recommendations: Recommendation[];
  generatedAt?: string;
  message?: string;
};

export type RunHistoryEntry = {
  id: string;
  suite: string;
  suiteLabel?: string;
  requestedAt: string;
  generatedAt?: string;
  summary: BenchmarkSummary | Record<string, unknown>;
  benchmarkCount: number;
  failed: number;
  success: number;
  status: 'success' | 'needs_attention';
  threshold?: number | null;
};
