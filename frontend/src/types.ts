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
