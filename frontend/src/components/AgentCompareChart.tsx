import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from 'recharts';

import type { AgentBreakdown } from '@/components/types';

export type AgentCompareChartProps = {
  agents: AgentBreakdown[];
  visible: boolean;
};

const METRICS: Array<{ key: keyof AgentBreakdown['scores']; label: string; color: string }> = [
  { key: 'content', label: 'Content', color: '#4f46e5' },
  { key: 'structure', label: 'Structure', color: '#0891b2' },
  { key: 'completeness', label: 'Completeness', color: '#16a34a' },
  { key: 'accuracy', label: 'Accuracy', color: '#f97316' }
];

export function AgentCompareChart({ agents, visible }: AgentCompareChartProps) {
  if (!visible || agents.length <= 1) {
    return null;
  }

  const data = agents.map((agent) => ({
    agent: agent.agent,
    ...agent.scores,
  }));

  return (
    <div className="rounded-2xl border bg-card/80 p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-[hsl(var(--heading))]">Agent Comparison</h2>
          <p className="text-sm text-muted-foreground">Stacked view across reliability dimensions.</p>
        </div>
      </div>
      <div className="mt-6 h-72">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ left: 80, right: 16, top: 16, bottom: 16 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis type="number" domain={[0, 1]} tickFormatter={(value) => `${Math.round(value * 100)}%`} />
            <YAxis dataKey="agent" type="category" width={120} />
            <Tooltip formatter={(value: number) => `${(value as number).toFixed(2)}`} />
            <Legend />
            {METRICS.map((metric) => (
              <Bar key={metric.key} dataKey={metric.key} stackId="scores" name={metric.label} fill={metric.color} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
