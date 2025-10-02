export type ObjectiveDetail = {
  name: string;
  score: number;
  input: string;
  output: string;
  notes: string;
};

export type AgentBreakdown = {
  agent: string;
  scores: {
    content: number;
    structure: number;
    completeness: number;
    accuracy: number;
    overall: number;
  };
};

export type Run = {
  iteration: string;
  scores: {
    content: number;
    structure: number;
    completeness: number;
    accuracy: number;
    overall: number;
  };
  avgLength: number;
  sample: string;
  judgeNotes: string[];
  agent?: string;
  agents?: AgentBreakdown[];
  objectives?: ObjectiveDetail[];
};

export type BenchmarkPayload = {
  runs: Run[];
  model: string;
  paper: string;
  timestamp: string;
};
