import { DownloadButton } from '@/components/DownloadButton';
import { OverallBadge } from '@/components/OverallBadge';

export type HeaderBarProps = {
  title: string;
  model: string;
  timestamp: string;
  overallScore?: number;
};

export function HeaderBar({ title, model, timestamp, overallScore }: HeaderBarProps) {
  return (
    <header className="flex flex-col gap-4 rounded-2xl border bg-card/80 p-6 shadow-sm lg:flex-row lg:items-center lg:justify-between">
      <div className="space-y-2">
        <h1 className="text-3xl font-semibold tracking-tight">{title}</h1>
        <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
          <span className="flex items-center gap-2">
            <span className="font-medium text-foreground">Model:</span>
            {model}
          </span>
          <span className="hidden h-4 w-px bg-border lg:inline" aria-hidden />
          <span>
            <span className="font-medium text-foreground">Timestamp:</span> {new Date(timestamp).toLocaleString()}
          </span>
        </div>
      </div>
      <div className="flex items-center gap-4">
        {overallScore !== undefined ? <OverallBadge value={overallScore} /> : null}
        <DownloadButton href="/benchmarks/latest.json" filename="document_extraction_latest.json" />
      </div>
    </header>
  );
}
