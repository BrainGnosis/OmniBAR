import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import type { Run } from '@/components/types';
import { cn } from '@/lib/utils';

export type ReliabilityTableProps = {
  runs: Run[];
  activeIteration: string | null;
};

export function ReliabilityTable({ runs, activeIteration }: ReliabilityTableProps) {
  const sorted = runs.slice().sort((a, b) => b.scores.overall - a.scores.overall);

  return (
    <div className="rounded-2xl border bg-card/80 p-6 shadow-sm">
      <div>
        <h2 className="text-lg font-semibold text-[hsl(var(--heading))]">Reliability Scores</h2>
        <p className="text-sm text-muted-foreground">All iterations ordered by overall strength (higher is better).</p>
      </div>
      <div className="mt-4 overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Iteration</TableHead>
              <TableHead className="text-right">Content</TableHead>
              <TableHead className="text-right">Structure</TableHead>
              <TableHead className="text-right">Completeness</TableHead>
              <TableHead className="text-right">Accuracy</TableHead>
              <TableHead className="text-right">Overall</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sorted.map((run, index) => {
              const isLeader = index === 0;
              const isActive = run.iteration === activeIteration;
              return (
                <TableRow
                  key={run.iteration}
                  className={cn(
                    isLeader ? 'bg-emerald-50/70' : undefined,
                    isActive && !isLeader ? 'bg-muted/50' : undefined
                  )}
                >
                  <TableCell className="flex items-center gap-2 font-medium">
                    {run.iteration}
                    {isLeader ? <Badge variant="success">Top</Badge> : null}
                  </TableCell>
                  <TableCell className="text-right">{run.scores.content.toFixed(2)}</TableCell>
                  <TableCell className="text-right">{run.scores.structure.toFixed(2)}</TableCell>
                  <TableCell className="text-right">{run.scores.completeness.toFixed(2)}</TableCell>
                  <TableCell className="text-right">{run.scores.accuracy.toFixed(2)}</TableCell>
                  <TableCell className="text-right font-semibold text-[hsl(var(--heading))]">
                    {run.scores.overall.toFixed(2)}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
