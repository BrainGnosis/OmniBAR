export const CardSkeleton = () => (
  <div className="rounded-lg border border-dashed border-border/60 bg-muted/40 p-6">
    <div className="h-5 w-1/3 animate-pulse rounded bg-muted" />
    <div className="mt-3 space-y-2">
      <div className="h-4 w-full animate-pulse rounded bg-muted/80" />
      <div className="h-4 w-5/6 animate-pulse rounded bg-muted/80" />
    </div>
  </div>
);

export const TableSkeleton = ({ rows = 5 }: { rows?: number }) => (
  <div className="overflow-hidden rounded-md border">
    <div className="h-10 bg-muted/60" />
    <div className="divide-y border-t">
      {Array.from({ length: rows }).map((_, index) => (
        <div key={index} className="flex gap-4 px-4 py-3">
          <div className="h-4 w-1/4 animate-pulse rounded bg-muted/80" />
          <div className="h-4 w-1/6 animate-pulse rounded bg-muted/60" />
          <div className="h-4 w-1/5 animate-pulse rounded bg-muted/60" />
        </div>
      ))}
    </div>
  </div>
);

export const LogSkeleton = ({ lines = 4 }: { lines?: number }) => (
  <pre className="rounded bg-muted/30 p-4 text-xs">
    {Array.from({ length: lines }).map((_, index) => (
      <div key={index} className="mb-2 h-3 w-full animate-pulse rounded bg-muted/80" />
    ))}
  </pre>
);
