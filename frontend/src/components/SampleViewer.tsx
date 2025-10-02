import { useState } from 'react';
import { ChevronDownIcon, ChevronUpIcon } from '@heroicons/react/24/outline';

export type SampleViewerProps = {
  sample: string;
};

function formatSample(sample: string): string {
  const trimmed = sample.trim();
  if (!trimmed) {
    return 'No sample available.';
  }

  if ((trimmed.startsWith('{') && trimmed.endsWith('}')) || (trimmed.startsWith('[') && trimmed.endsWith(']'))) {
    try {
      return JSON.stringify(JSON.parse(trimmed), null, 2);
    } catch (error) {
      // Fall through to returning the original sample
    }
  }

  return sample;
}

export function SampleViewer({ sample }: SampleViewerProps) {
  const [open, setOpen] = useState(true);
  const formatted = formatSample(sample);

  return (
    <div className="rounded-2xl border bg-card/80 shadow-sm">
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        className="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-medium text-foreground"
      >
        <span>Extraction Sample</span>
        {open ? <ChevronUpIcon className="h-4 w-4" /> : <ChevronDownIcon className="h-4 w-4" />}
      </button>
      {open ? (
        <div className="border-t border-border/60 bg-background/70">
          <pre className="max-h-96 overflow-auto px-4 py-3 text-xs text-muted-foreground">
            <code>{formatted}</code>
          </pre>
        </div>
      ) : null}
    </div>
  );
}
