import { useEffect, useState } from 'react';
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip as RadarTooltip,
} from 'recharts';

export type TrustCompassProps = {
  scores: {
    faithfulness: number;
    reliability: number;
    coherence: number;
    adaptability: number;
  };
};

export function TrustCompass({ scores }: TrustCompassProps) {
  const [animatedScores, setAnimatedScores] = useState({
    faithfulness: 0,
    reliability: 0,
    coherence: 0,
    adaptability: 0,
  });

  useEffect(() => {
    const duration = 2000; // 2 seconds animation
    const steps = 60;
    const interval = duration / steps;
    let step = 0;

    const timer = setInterval(() => {
      step++;
      const progress = step / steps;
      setAnimatedScores({
        faithfulness: scores.faithfulness * progress,
        reliability: scores.reliability * progress,
        coherence: scores.coherence * progress,
        adaptability: scores.adaptability * progress,
      });
      if (step >= steps) {
        clearInterval(timer);
        setAnimatedScores(scores);
      }
    }, interval);

    return () => clearInterval(timer);
  }, [scores]);

  const data = [
    { metric: 'Faithfulness', value: animatedScores.faithfulness },
    { metric: 'Reliability', value: animatedScores.reliability },
    { metric: 'Coherence', value: animatedScores.coherence },
    { metric: 'Adaptability', value: animatedScores.adaptability },
  ];

  return (
    <div className="rounded-2xl border bg-card/80 p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-[hsl(var(--heading))]">Trust Compass</h2>
      <p className="text-sm text-muted-foreground">4-axis radial graph showing trust dimensions.</p>
      <div className="mt-6 h-80">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart data={data} outerRadius="70%">
            <PolarGrid stroke="hsl(var(--muted-foreground))" strokeOpacity={0.4} />
            <PolarAngleAxis dataKey="metric" tick={{ fontSize: 12 }} />
            <PolarRadiusAxis tickFormatter={(value) => `${Math.round((value as number) * 100)}%`} domain={[0, 1]} tickCount={5} />
            <Radar name="Score" dataKey="value" stroke="hsl(var(--primary))" fill="hsl(var(--primary))" fillOpacity={0.3} />
            <RadarTooltip formatter={(value: number) => `${Math.round(value * 100)}%`} />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}