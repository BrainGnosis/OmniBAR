import { useEffect, useState } from 'react';
import { Line, LineChart, ResponsiveContainer, Tooltip, YAxis } from 'recharts';

import { getRecentRuns } from '@/lib/api';

export function TrendSparkline() {
  const [data, setData] = useState<{ index: number; successRate: number }[]>([]);

  useEffect(() => {
    const load = async () => {
      try {
        const runs = await getRecentRuns();
        if (!runs.length) {
          setData([]);
          return;
        }
        const series: { index: number; successRate: number }[] = runs
          .map((run, index) => ({ index, successRate: run.combinedPass ? 1 : 0 }))
          .map((point, index, arr) => {
            const slice = arr.slice(0, index + 1);
            const rate = slice.reduce((acc, cur) => acc + cur.successRate, 0) / slice.length;
            return { index, successRate: Math.round(rate * 100) };
          });
        setData(series);
      } catch (err) {
        console.error('Failed to load runs', err);
      }
    };
    void load();
  }, []);

  return (
    <div role="img" aria-label="Run success trend sparkline" className="h-32 w-full">
      <ResponsiveContainer>
        <LineChart data={data} margin={{ top: 8, left: 8, right: 8, bottom: 8 }}>
          <YAxis domain={[0, 100]} hide />
          <Tooltip formatter={(value: number) => [`${value}%`, 'Success rate']} />
          <Line type="monotone" dataKey="successRate" stroke="#2563eb" dot={false} strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
