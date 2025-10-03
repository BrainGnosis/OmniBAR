export type InfoBarProps = {
  avgLength: number;
  threshold: number;
  runDelta: number | null;
};

export function InfoBar({ avgLength, threshold, runDelta }: InfoBarProps) {
  const deltaLabel = runDelta == null ? null : `${runDelta >= 0 ? '+' : ''}${(runDelta * 100).toFixed(1)}% vs previous`;
  return (
    <div className="flex flex-col gap-3 rounded-2xl border bg-card/60 px-5 py-4 text-sm text-muted-foreground shadow-sm md:flex-row md:items-center md:justify-between">
      <div>
        <span className="font-medium text-foreground">Average extraction length:</span> {avgLength} characters
      </div>
      <div className="flex flex-wrap items-center gap-4">
        <span>
          <span className="font-medium text-foreground">Threshold:</span> {threshold.toFixed(2)} (scores below fail)
        </span>
        <span>
          <span className="font-medium text-foreground">Scoring scale:</span> 0.00 – 1.00 (LLM judge)
        </span>
        {deltaLabel ? (
          <span className={runDelta && runDelta < 0 ? 'text-destructive' : 'text-emerald-600'}>{deltaLabel}</span>
        ) : null}
      </div>
    </div>
  );
}
