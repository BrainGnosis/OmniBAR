import { Badge } from '@/components/ui/badge';

export type PromptDetailsProps = {
  summary: string;
  highlights: string[];
};

export function PromptDetails({ summary, highlights }: PromptDetailsProps) {
  return (
    <div className="rounded-2xl border bg-card/80 p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-[hsl(var(--heading))]">Prompt Highlights</h2>
      <p className="mt-2 text-sm text-muted-foreground">{summary}</p>
      <div className="mt-4 flex flex-wrap gap-2">
        {highlights.map((item) => (
          <Badge key={item} variant="outline">
            {item}
          </Badge>
        ))}
      </div>
    </div>
  );
}
