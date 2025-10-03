import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip as RadarTooltip,
} from 'recharts';

export type RadarScoreChartProps = {
  scores: {
    content: number;
    structure: number;
    completeness: number;
    accuracy: number;
  };
};

export function RadarScoreChart({ scores }: RadarScoreChartProps) {
  const data = [
    { metric: 'Content', value: scores.content },
    { metric: 'Structure', value: scores.structure },
    { metric: 'Completeness', value: scores.completeness },
    { metric: 'Accuracy', value: scores.accuracy },
  ];

  return (
    <div className="rounded-2xl border bg-card/80 p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-[hsl(var(--heading))]">Quality Radar</h2>
      <p className="text-sm text-muted-foreground">Comparative profile of the selected prompt iteration.</p>
      <div className="mt-6 h-80">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart data={data} outerRadius="70%">
            <PolarGrid stroke="hsl(var(--muted-foreground))" strokeOpacity={0.4} />
            <PolarAngleAxis dataKey="metric" tick={{ fontSize: 12 }} />
            <PolarRadiusAxis tickFormatter={(value) => `${Math.round((value as number) * 100)}%`} domain={[0, 1]} tickCount={5} />
            <Radar name="Score" dataKey="value" stroke="hsl(var(--accent))" fill="hsl(var(--accent))" fillOpacity={0.3} />
            <RadarTooltip formatter={(value: number) => `${Math.round(value * 100)}%`} />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
