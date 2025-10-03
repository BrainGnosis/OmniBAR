import { ReactNode } from 'react';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export type BenchmarkCardProps = {
  title: string;
  description: string;
  metrics: Array<{ label: string; value: string; positive?: boolean }>;
  cta?: ReactNode;
};

export function BenchmarkCard({ title, description, metrics, cta }: BenchmarkCardProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          {metrics.map((metric) => (
            <div key={metric.label} className="rounded-lg border bg-muted/30 p-4 text-sm">
              <span className="text-xs uppercase tracking-wide text-muted-foreground">{metric.label}</span>
              <p className="mt-1 text-xl font-semibold text-[hsl(var(--heading))]">
                {metric.value}
              </p>
              {metric.positive !== undefined ? (
                <p className={`text-xs ${metric.positive ? 'text-emerald-600' : 'text-destructive'}`}>
                  {metric.positive ? 'Trending up' : 'Trending down'}
                </p>
              ) : null}
            </div>
          ))}
        </div>
        {cta ? <div className="flex items-center justify-end">{cta}</div> : null}
      </CardContent>
    </Card>
  );
}

export type TeamCardProps = {
  teamName: string;
  owner: string;
  focusAreas: string[];
  health: 'healthy' | 'watch' | 'critical';
  footer?: ReactNode;
};

const healthBadgeConfig = {
  healthy: { text: 'Healthy', variant: 'success' as const },
  watch: { text: 'Monitor', variant: 'warning' as const },
  critical: { text: 'Critical', variant: 'destructive' as const }
};

export function TeamCard({ teamName, owner, focusAreas, health, footer }: TeamCardProps) {
  const badge = healthBadgeConfig[health];
  return (
    <Card className="h-full border-brand-primary/10">
      <CardHeader className="flex flex-col gap-3">
        <div className="flex items-center justify-between gap-3">
          <CardTitle>{teamName}</CardTitle>
          <Badge variant={badge.variant}>{badge.text}</Badge>
        </div>
        <CardDescription>Reliability owner: {owner}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <p className="text-xs uppercase tracking-wide text-muted-foreground">Focus Areas</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {focusAreas.map((area) => (
              <Badge key={area} variant="outline">
                {area}
              </Badge>
            ))}
          </div>
        </div>
        {footer ? <div className="rounded-lg bg-secondary/60 p-3 text-sm text-muted-foreground">{footer}</div> : null}
      </CardContent>
    </Card>
  );
}

export type JobCardProps = {
  title: string;
  description: string;
  tags: string[];
  actions?: ReactNode;
};

export function JobCard({ title, description, tags, actions }: JobCardProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4 text-sm text-muted-foreground">
        <div className="flex flex-wrap gap-2">
          {tags.map((tag) => (
            <Badge key={tag} variant="outline">
              {tag}
            </Badge>
          ))}
        </div>
        {actions ? <div className="flex items-center justify-end gap-3">{actions}</div> : null}
      </CardContent>
    </Card>
  );
}
