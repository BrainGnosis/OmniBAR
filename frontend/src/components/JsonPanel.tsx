import { useMemo, useState } from 'react';
import {
  CheckIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  ClipboardDocumentIcon
} from '@heroicons/react/24/outline';

import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

export interface JsonPanelProps {
  title?: string;
  data: unknown;
  description?: string;
  initiallyOpen?: boolean;
  className?: string;
}

function escapeHtml(value: string) {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function syntaxHighlight(json: string) {
  const escaped = escapeHtml(json);
  return escaped.replace(
    /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(?::)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)/g,
    (match) => {
      let className = 'text-slate-300';
      if (/^".*"$/.test(match)) {
        if (/:$/.test(match)) {
          className = 'text-sky-400';
        } else {
          className = 'text-emerald-400';
        }
      } else if (/true|false/.test(match)) {
        className = 'text-orange-300';
      } else if (/null/.test(match)) {
        className = 'text-rose-300';
      } else {
        className = 'text-amber-300';
      }
      return `<span class="${className}">${match}</span>`;
    }
  );
}

export function JsonPanel({
  title = 'JSON',
  data,
  description,
  initiallyOpen = true,
  className
}: JsonPanelProps) {
  const [open, setOpen] = useState(initiallyOpen);
  const [copyState, setCopyState] = useState<'idle' | 'copied' | 'error'>('idle');

  const formatted = useMemo(() => JSON.stringify(data ?? {}, null, 2), [data]);
  const highlighted = useMemo(() => syntaxHighlight(formatted), [formatted]);

  const handleCopy = async () => {
    if (!navigator?.clipboard) {
      setCopyState('error');
      return;
    }

    try {
      await navigator.clipboard.writeText(formatted);
      setCopyState('copied');
      setTimeout(() => setCopyState('idle'), 2000);
    } catch (error) {
      console.error('Unable to copy JSON', error);
      setCopyState('error');
      setTimeout(() => setCopyState('idle'), 4000);
    }
  };

  return (
    <section className={cn('space-y-3 rounded-xl border border-border/80 bg-secondary/40 p-4 shadow-sm', className)}>
      <header className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <button
            type="button"
            onClick={() => setOpen((prev) => !prev)}
            aria-expanded={open}
            className="flex items-center gap-2 text-left text-sm font-semibold text-[hsl(var(--heading))]"
          >
            {open ? (
              <ChevronDownIcon className="h-4 w-4 text-muted-foreground" />
            ) : (
              <ChevronRightIcon className="h-4 w-4 text-muted-foreground" />
            )}
            {title}
          </button>
          {description ? <p className="text-xs text-muted-foreground">{description}</p> : null}
        </div>
        <div className="flex items-center gap-2">
          <Button
            type="button"
            size="sm"
            variant="ghost"
            className="gap-2 text-xs"
            onClick={handleCopy}
          >
            {copyState === 'copied' ? (
              <CheckIcon className="h-4 w-4 text-emerald-500" />
            ) : (
              <ClipboardDocumentIcon className="h-4 w-4 text-muted-foreground" />
            )}
            {copyState === 'copied' ? 'Copied!' : 'Copy JSON'}
          </Button>
        </div>
      </header>
      {copyState === 'error' ? (
        <p className="text-xs text-destructive">
          Unable to access the clipboard automatically. Select the text below and copy it manually.
        </p>
      ) : null}
      {open ? (
        <div className="overflow-hidden rounded-lg border bg-background/60">
          <pre className="max-h-[480px] overflow-auto bg-slate-950/90 p-4 text-xs leading-6 text-slate-100">
            <code dangerouslySetInnerHTML={{ __html: highlighted }} />
          </pre>
        </div>
      ) : null}
    </section>
  );
}
