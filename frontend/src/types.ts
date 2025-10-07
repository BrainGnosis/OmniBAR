export type Operation = "add" | "multiply";

export interface AgentInput {
  operation: Operation;
  a: number;
  b: number;
}

export interface AgentOutput {
  answer: string;
  explanation: string;
  status: "success" | "error";
}

export type ObjectiveKind = "stringEquals" | "regexMatch";

export interface ObjectiveResult {
  id: string;
  name: string;
  kind: ObjectiveKind;
  pass: boolean;
  details?: string;
}

export interface RunRecord {
  id: string;
  input: AgentInput;
  output: AgentOutput;
  objectives: ObjectiveResult[];
  combinedPass: boolean;
  latencyMs: number;
  startedAt: string;
}

export interface BenchmarkRow {
  id: string;
  name: string;
  iterations: number;
  successRate: number;
  lastUpdated: string;
  status: "passing" | "failing" | "monitor";
}

export interface LatteConfig {
  mock_mode: boolean;
  default_model: string;
  scoring_model: string;
  available_models: string[];
}

export interface LatteCreatePayload {
  system_prompt: string;
  user_prompt: string;
  temperature: number;
  model: string;
  mock: boolean | null;
}

export interface LatteRun {
  id: number;
  created_at: string;
  system_prompt: string;
  user_prompt: string;
  temperature: number;
  model: string;
  response: string;
  score: number;
  baristas_note: string;
  scoring_breakdown: Record<string, unknown>;
  latency_ms: number;
  prompt_tokens: number | null;
  completion_tokens: number | null;
  total_tokens: number | null;
  mock_run: boolean;
}

export interface LatteRunListResponse {
  runs: LatteRun[];
}

export interface LatteRollupModelStat {
  model: string;
  average_score: number;
  run_count: number;
  last_run: string | null;
}

export interface LatteDailyScore {
  date: string;
  average_score: number;
  run_count: number;
}

export interface LatteRollups {
  total_runs: number;
  average_score: number;
  success_rate: number;
  mock_runs: number;
  model_breakdown: LatteRollupModelStat[];
  daily_scores: LatteDailyScore[];
}
