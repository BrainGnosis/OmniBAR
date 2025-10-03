import { ArrowDownTrayIcon } from '@heroicons/react/24/outline';

export type DownloadButtonProps = {
  href: string;
  filename?: string;
};

export function DownloadButton({ href, filename }: DownloadButtonProps) {
  return (
    <a
      className="inline-flex items-center gap-2 rounded-full border border-border bg-background px-4 py-2 text-sm font-medium text-foreground shadow-sm transition-colors hover:bg-muted"
      href={href}
      download={filename}
    >
      <ArrowDownTrayIcon className="h-4 w-4" />
      Download JSON
    </a>
  );
}
