import type { ObjectiveDetail } from '@/components/types';

export type ObjectiveDrawerProps = {
  objective: ObjectiveDetail | null;
  onClose: () => void;
};

export function ObjectiveDrawer({ objective, onClose }: ObjectiveDrawerProps) {
  if (!objective) {
    return null;
  }

  return (
    <div className="rounded-2xl border bg-card/80 p-6 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-[hsl(var(--heading))]">{objective.name} Drilldown</h2>
          <p className="text-sm text-muted-foreground">Raw evaluation details from the latest run.</p>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="text-sm font-medium text-muted-foreground hover:text-foreground"
        >
          Close
        </button>
      </div>
      <div className="mt-4 space-y-4 text-sm text-muted-foreground">
        <div>
          <span className="font-medium text-foreground">Score:</span> {objective.score.toFixed(2)}
        </div>
        <div>
          <span className="font-medium text-foreground">Input</span>
          <pre className="mt-1 whitespace-pre-wrap rounded-md bg-muted/50 p-3 text-xs text-muted-foreground">
            <code>{objective.input}</code>
          </pre>
        </div>
        <div>
          <span className="font-medium text-foreground">Output</span>
          <pre className="mt-1 whitespace-pre-wrap rounded-md bg-muted/50 p-3 text-xs text-muted-foreground">
            <code>{objective.output}</code>
          </pre>
        </div>
        <div>
          <span className="font-medium text-foreground">Evaluation Notes</span>
          <p className="mt-1 text-sm text-muted-foreground">{objective.notes}</p>
        </div>
      </div>
    </div>
  );
}
