import { cn } from '@/lib/utils';

export type ScoreCardsProps = {
  scores: {
    content: number;
    structure: number;
    completeness: number;
    accuracy: number;
  };
  threshold: number;
  onSelectObjective?: (objective: keyof ScoreCardsProps['scores']) => void;
  activeObjective?: keyof ScoreCardsProps['scores'] | null;
};

const LABELS: Record<keyof ScoreCardsProps['scores'], string> = {
  content: 'Content',
  structure: 'Structure',
  completeness: 'Completeness',
  accuracy: 'Accuracy',
};

export function ScoreCards({ scores, threshold, onSelectObjective, activeObjective }: ScoreCardsProps) {
  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
      {(Object.keys(scores) as Array<keyof ScoreCardsProps['scores']>).map((key) => {
        const value = scores[key];
        const percent = Math.max(0, Math.min(1, value));
        const pass = percent >= threshold;
        const isActive = activeObjective === key;
        return (
          <button
            key={key}
            type="button"
            onClick={() => onSelectObjective?.(key)}
            className={cn(
              'rounded-2xl border bg-card/80 p-4 text-left shadow-sm transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[hsl(var(--accent))]',
              !pass ? 'border-destructive/60' : 'border-card',
              isActive ? 'ring-2 ring-[hsl(var(--accent))]' : undefined
            )}
          >
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-muted-foreground">{LABELS[key]}</span>
              <span className={cn('text-lg font-semibold', pass ? 'text-foreground' : 'text-destructive')}>
                {value.toFixed(2)}
              </span>
            </div>
            <div className="mt-3 h-2 rounded-full bg-muted">
              <div
                className={cn(
                  'h-full rounded-full transition-all',
                  pass ? 'bg-[hsl(var(--accent))]' : 'bg-destructive'
                )}
                style={{ width: `${percent * 100}%` }}
              />
            </div>
            <div className="mt-3 text-xs font-medium uppercase tracking-wide">
              {pass ? (
                <span className="text-emerald-600">Pass</span>
              ) : (
                <span className="text-destructive">Fail (threshold {threshold.toFixed(2)})</span>
              )}
            </div>
          </button>
        );
      })}
    </div>
  );
}
