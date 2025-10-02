import { useEffect, useState } from 'react';
import { Pie, PieChart, Cell, ResponsiveContainer, Tooltip } from 'recharts';

import { getRecentRuns } from '@/lib/api';

export function SuccessDonut() {
  const [data, setData] = useState<{ name: string; value: number; color: string }[]>([]);

  useEffect(() => {
    const load = async () => {
      try {
        const runs = await getRecentRuns();
        const pass = runs.filter((run) => run.combinedPass).length;
        const fail = runs.length - pass;
        setData([
          { name: 'Pass', value: pass, color: '#16a34a' },
          { name: 'Fail', value: fail, color: '#dc2626' },
        ]);
      } catch (err) {
        console.error('Failed to load runs', err);
      }
    };
    void load();
  }, []);

  return (
    <div role="img" aria-label="Run success donut chart" className="h-56 w-full">
      <ResponsiveContainer>
        <PieChart>
          <Tooltip formatter={(value: number, name: string) => [`${value}`, name]} />
          <Pie data={data} dataKey="value" nameKey="name" innerRadius={50} outerRadius={70} paddingAngle={2}>
            {data.map((entry) => (
              <Cell key={entry.name} fill={entry.color} />
            ))}
          </Pie>
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
