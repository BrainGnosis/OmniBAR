import { useState } from 'react';

export interface JsonPanelProps {
  title?: string;
  data: unknown;
}

export function JsonPanel({ title = 'JSON', data }: JsonPanelProps) {
  const [open, setOpen] = useState(true);
  const json = JSON.stringify(data, null, 2);

  return (
    <section className="space-y-2">
      <header className="flex items-center justify-between">
        <h3 className="text-sm font-semibold">{title}</h3>
        <button type="button" onClick={() => setOpen((prev) => !prev)}>
          {open ? 'Collapse' : 'Expand'}
        </button>
      </header>
      {open ? (
        <pre className="rounded border bg-muted/40 p-3 text-xs">
          <code>{json}</code>
        </pre>
      ) : null}
    </section>
  );
}
