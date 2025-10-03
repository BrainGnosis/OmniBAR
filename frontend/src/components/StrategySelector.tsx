import { cn } from '@/lib/utils';
import type { Run } from '@/components/types';

export type StrategySelectorProps = {
  runs: Run[];
  selected: string | null;
  onSelect: (iteration: string) => void;
};

export function StrategySelector({ runs, selected, onSelect }: StrategySelectorProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {runs.map((run) => {
        const isActive = run.iteration === selected;
        return (
          <button
            key={run.iteration}
            type="button"
            onClick={() => onSelect(run.iteration)}
            className={cn(
              'rounded-full border px-4 py-2 text-sm font-medium transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[hsl(var(--accent))]',
              isActive
                ? 'border-transparent bg-[hsl(var(--accent))] text-white shadow'
                : 'border-border bg-background text-muted-foreground hover:border-[hsl(var(--accent))]/60 hover:text-foreground'
            )}
          >
            {run.iteration}
          </button>
        );
      })}
    </div>
  );
}
