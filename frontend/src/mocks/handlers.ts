import { http, HttpResponse } from 'msw';
import { v4 as uuid } from 'uuid';

import type {
  AgentInput,
  AgentOutput,
  RunRecord,
  ObjectiveResult,
  BenchmarkRow,
} from '@/types';

const benchmarkRows: BenchmarkRow[] = [
  { id: uuid(), name: 'Addition Accuracy', iterations: 10, successRate: 0.95, lastUpdated: new Date().toISOString(), status: 'passing' },
  { id: uuid(), name: 'Multiplication Coverage', iterations: 12, successRate: 0.58, lastUpdated: new Date().toISOString(), status: 'failing' },
  { id: uuid(), name: 'Division Guardrail', iterations: 8, successRate: 0.72, lastUpdated: new Date().toISOString(), status: 'monitor' },
  { id: uuid(), name: 'Prime Detection', iterations: 15, successRate: 0.88, lastUpdated: new Date().toISOString(), status: 'passing' },
  { id: uuid(), name: 'Modulo Edge Cases', iterations: 6, successRate: 0.42, lastUpdated: new Date().toISOString(), status: 'failing' },
  { id: uuid(), name: 'Floating Point Stability', iterations: 9, successRate: 0.63, lastUpdated: new Date().toISOString(), status: 'monitor' },
];

const runHistory: RunRecord[] = [];

function evaluateObjectives(input: AgentInput, output: AgentOutput): ObjectiveResult[] {
  const expected = input.operation === 'add' ? String(input.a + input.b) : input.operation === 'multiply' ? String(input.a * input.b) : 'error';
  const objectives: ObjectiveResult[] = [];

  objectives.push({
    id: uuid(),
    name: 'Exact answer match',
    kind: 'stringEquals',
    pass: output.answer === expected,
    details: `Expected ${expected}, got ${output.answer}`,
  });

  const regex = /^(Adding|Multiplying) \d+ .* = \d+$/;
  objectives.push({
    id: uuid(),
    name: 'Explanation format',
    kind: 'regexMatch',
    pass: regex.test(output.explanation),
    details: 'Explanation must describe the math operation',
  });

  return objectives;
}

function simulateAgent(input: AgentInput): AgentOutput {
  if (input.operation === 'add') {
    const answer = input.a + input.b;
    return {
      answer: String(answer),
      explanation: `Adding ${input.a} + ${input.b} = ${answer}`,
      status: 'success',
    };
  }
  if (input.operation === 'multiply') {
    const answer = input.a * input.b;
    return {
      answer: String(answer),
      explanation: `Multiplying ${input.a} x ${input.b} = ${answer}`,
      status: 'success',
    };
  }
  return {
    answer: 'error',
    explanation: 'Unsupported operation',
    status: 'error',
  };
}

export const handlers = [
  http.get('/api/benchmarks', () => {
    return HttpResponse.json(benchmarkRows);
  }),
  http.post('/api/run', async ({ request }) => {
    const input = (await request.json()) as AgentInput;
    const output = simulateAgent(input);
    const objectives = evaluateObjectives(input, output);
    const combinedPass = output.status === 'success' && objectives.every((objective) => objective.pass);
    const record: RunRecord = {
      id: uuid(),
      input,
      output,
      objectives,
      combinedPass,
      latencyMs: Math.floor(120 + Math.random() * 260),
      startedAt: new Date().toISOString(),
    };
    runHistory.unshift(record);
    if (runHistory.length > 25) {
      runHistory.length = 25;
    }
    return HttpResponse.json(record, { status: combinedPass ? 200 : 400 });
  }),
  http.get('/api/runs', () => {
    return HttpResponse.json(runHistory);
  }),
];
