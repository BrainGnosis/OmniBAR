import { useEffect, useMemo, useState } from 'react';
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip as RadarTooltip
} from 'recharts';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { JsonPanel } from '@/components/JsonPanel';
import { TrustCompass } from '@/components/TrustCompass';
import { cn } from '@/lib/utils';
import { getStoredThreshold } from '@/lib/threshold';

type ScoreBreakdown = {
  content: number;
  structure: number;
  completeness: number;
  accuracy: number;
  overall: number;
};

type Metadata = {
  summary?: string;
  promptHighlights?: string[];
  radar?: Array<{ metric: string; value: number }>;
};

type ObjectiveDetail = {
  name: string;
  score: number;
  input: string;
  output: string;
  notes: string;
};

type IterationRecord = {
  id: string;
  label: string;
  strategy: string;
  model: string;
  run_seconds: number;
  avg_output_tokens: number;
  scores: ScoreBreakdown;
  metadata?: Metadata;
  sample?: unknown;
  judgeNotes?: string[];
  objectives?: ObjectiveDetail[];
};

type DashboardPayload = {
  generatedAt: string;
  iterations: IterationRecord[];
};

const DATA_SOURCES = [
  { id: 'document', label: 'Invoice Judge', path: '/data/document_extraction_benchmarks.json' },
  { id: 'gsm8k', label: 'GSM8K Judge', path: '/data/gsm8k_benchmarks.json' },
  { id: 'math_reasoning', label: 'Math Reasoning Judge', path: '/data/math_reasoning_benchmarks.json' }
] as const;

const SOURCE_LABEL: Record<string, string> = Object.fromEntries(DATA_SOURCES.map((source) => [source.id, source.label]));

function formatSeconds(value: number): string {
  return `${value.toFixed(1)} s`;
}

function formatTokens(value: number): string {
  return `${value} tokens`;
}

function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function coerceSample(sample: unknown): unknown {
  if (typeof sample === 'string') {
    try {
      return JSON.parse(sample);
    } catch (error) {
      return sample;
    }
  }
  return sample ?? 'No sample available.';
}

export default function DocumentExtraction() {
  const [sourceId, setSourceId] = useState<(typeof DATA_SOURCES)[number]['id']>(DATA_SOURCES[0].id);
  const [data, setData] = useState<DashboardPayload | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedObjective, setSelectedObjective] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [threshold, setThreshold] = useState(() => {
    if (typeof window === 'undefined') {
      return getStoredThreshold();
    }
    const params = new URLSearchParams(window.location.search);
    const candidate = Number(params.get('threshold'));
    if (Number.isFinite(candidate) && candidate > 0 && candidate <= 1) {
      return candidate;
    }
    return getStoredThreshold();
  });

  useEffect(() => {
    let mounted = true;
    const source = DATA_SOURCES.find((item) => item.id === sourceId) ?? DATA_SOURCES[0];
    setLoading(true);
    setError(null);

    fetch(source.path)
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`Failed to load dashboard data (${response.status})`);
        }
        return (await response.json()) as DashboardPayload;
      })
      .then((payload) => {
        if (!mounted) return;
        setData(payload);
        setSelectedId(payload.iterations[0]?.id ?? null);
        setSelectedObjective(null);
      })
      .catch((err: unknown) => {
        if (mounted) {
          setError(err instanceof Error ? err.message : 'Unable to load benchmark data');
        }
      })
      .finally(() => {
        if (mounted) {
          setLoading(false);
        }
      });

    return () => {
      mounted = false;
    };
  }, [sourceId]);

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }
    const listener = (event: Event) => {
      const detail = (event as CustomEvent<{ value?: number }>).detail;
      if (detail && Number.isFinite(detail.value)) {
        setThreshold(Math.min(Math.max(detail.value ?? threshold, 0.1), 1));
      } else {
        setThreshold(getStoredThreshold());
      }
    };
    window.addEventListener('omnibar-threshold', listener);
    return () => {
      window.removeEventListener('omnibar-threshold', listener);
    };
  }, [threshold]);

  const activeData = useMemo(() => {
    if (!data || !selectedId) return null;
    return data.iterations.find((iteration) => iteration.id === selectedId) ?? data.iterations[0] ?? null;
  }, [data, selectedId]);

  const bestIteration = useMemo(() => {
    if (!data) return null;
    return data.iterations.reduce<IterationRecord | null>((best, current) => {
      if (!best) return current;
      return current.scores.overall > best.scores.overall ? current : best;
    }, null);
  }, [data]);

  const metadata: Metadata = activeData?.metadata ?? {};

  const failingObjectives = useMemo(() => {
    if (!activeData?.objectives) return [];
    return activeData.objectives.filter((objective) => objective.score < threshold);
  }, [activeData, threshold]);

  const selectedObjectiveDetail = useMemo(() => {
    if (!activeData?.objectives || !selectedObjective) return null;
    return activeData.objectives.find((objective) => objective.name === selectedObjective) ?? null;
  }, [activeData, selectedObjective]);

  useEffect(() => {
    setSelectedObjective(null);
  }, [selectedId, sourceId]);

  if (loading && !data) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-semibold tracking-tight">Document Extraction Benchmarks</h1>
        <p className="text-sm text-muted-foreground">Loading reliability dashboard…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-semibold tracking-tight">Document Extraction Benchmarks</h1>
        <div className="rounded-md border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">{error}</div>
      </div>
    );
  }

  if (!data || !activeData) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-semibold tracking-tight">Document Extraction Benchmarks</h1>
        <p className="text-sm text-muted-foreground">No benchmark data available. Run the generator script first.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="space-y-3">
        <h1 className="text-3xl font-semibold tracking-tight">Document Extraction Benchmarks</h1>
        <p className="text-muted-foreground text-sm">
          Snapshot generated {new Date(data.generatedAt).toLocaleString()}. Compare prompt strategies across core reliability
          dimensions—content, structure, completeness, accuracy, and overall fitness.
        </p>
        <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
          <span>
            Active reliability threshold: <span className="font-medium text-foreground">{formatPercent(threshold)}</span>
          </span>
          <label htmlFor="judge-select" className="ml-auto font-medium text-foreground">
            Evaluation config
          </label>
          <select
            id="judge-select"
            value={sourceId}
            onChange={(event) => setSourceId(event.target.value as (typeof DATA_SOURCES)[number]['id'])}
            className="rounded-md border bg-background px-3 py-2 text-sm"
          >
            {DATA_SOURCES.map((source) => (
              <option key={source.id} value={source.id}>
                {source.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[260px,1fr]">
        <aside className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Prompt Strategies</CardTitle>
              <CardDescription>Select an iteration to inspect metrics.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {data.iterations.map((iteration) => {
                const isActive = iteration.id === activeData.id;
                const isWinner = bestIteration?.id === iteration.id;
                return (
                  <Button
                    key={iteration.id}
                    variant={isActive ? 'primary' : 'secondary'}
                    className={cn('w-full items-center justify-between text-left', !isActive && 'bg-muted/50 text-muted-foreground')}
                    onClick={() => setSelectedId(iteration.id)}
                  >
                    <div className="flex flex-col items-start gap-1">
                      <span className="text-sm font-semibold">{iteration.label}</span>
                      <span className="text-xs text-muted-foreground">{iteration.strategy}</span>
                    </div>
                    {isWinner ? <Badge variant="success">Leader</Badge> : null}
                  </Button>
                );
              })}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Prompt Highlights</CardTitle>
              <CardDescription>{activeData.strategy}</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-wrap gap-2">
              {(metadata.promptHighlights ?? []).length ? (
                metadata.promptHighlights!.map((item) => (
                  <Badge key={item} variant="outline">
                    {item}
                  </Badge>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">No highlights recorded for this iteration.</p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Iteration Notes</CardTitle>
              <CardDescription>Why this prompt matters.</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">{metadata.summary ?? 'No summary available.'}</p>
              <p className="mt-3 text-xs text-muted-foreground">
                Scores below <span className="font-medium text-foreground">{formatPercent(threshold)}</span> are treated as failures.
              </p>
            </CardContent>
          </Card>
        </aside>

        <section className="space-y-6">
          <Card>
            <CardHeader className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <CardTitle>{activeData.label}</CardTitle>
                <CardDescription>{SOURCE_LABEL[sourceId]} • {activeData.strategy}</CardDescription>
              </div>
              <div className="flex flex-wrap items-center gap-6 text-sm text-muted-foreground">
                <div>
                  <p className="text-xs uppercase tracking-wide">Model</p>
                  <p className="text-sm font-medium text-foreground">{activeData.model}</p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-wide">Run Time</p>
                  <p className="text-sm font-medium text-foreground">{formatSeconds(activeData.run_seconds)}</p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-wide">Avg Output Length</p>
                  <p className="text-sm font-medium text-foreground">{formatTokens(activeData.avg_output_tokens)}</p>
                </div>
              </div>
            </CardHeader>
          </Card>

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {(['content', 'structure', 'completeness', 'accuracy'] as const).map((metric) => {
              const value = activeData.scores[metric];
              const pass = value >= threshold;
              return (
                <Card key={metric} className={pass ? undefined : 'border-destructive/60'}>
                  <CardHeader>
                    <CardTitle className="text-base capitalize">{metric}</CardTitle>
                    <CardDescription>LLM judge metric</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <p className={cn('text-3xl font-semibold', pass ? 'text-[hsl(var(--heading))]' : 'text-destructive')}>
                      {formatPercent(value)}
                    </p>
                    <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                      {pass ? (
                        <span className="text-emerald-600">Pass (threshold {formatPercent(threshold)})</span>
                      ) : (
                        <span className="text-destructive">Fail (threshold {formatPercent(threshold)})</span>
                      )}
                    </p>
                  </CardContent>
                </Card>
              );
            })}
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Reliability Scores</CardTitle>
              <CardDescription>All iterations ordered by overall strength. Higher is better.</CardDescription>
            </CardHeader>
            <CardContent className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Iteration</TableHead>
                    <TableHead className="text-right">Content</TableHead>
                    <TableHead className="text-right">Structure</TableHead>
                    <TableHead className="text-right">Completeness</TableHead>
                    <TableHead className="text-right">Accuracy</TableHead>
                    <TableHead className="text-right">Overall</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.iterations
                    .slice()
                    .sort((a, b) => b.scores.overall - a.scores.overall)
                    .map((iteration) => {
                      const isWinner = bestIteration?.id === iteration.id;
                      const isActive = activeData.id === iteration.id;
                      return (
                        <TableRow
                          key={iteration.id}
                          className={cn(
                            isWinner ? 'bg-emerald-50/80' : undefined,
                            isActive && !isWinner ? 'bg-muted/40' : undefined
                          )}
                        >
                          <TableCell className="flex items-center gap-2 font-medium">
                            {iteration.label}
                            {isWinner ? <Badge variant="success">Top</Badge> : null}
                          </TableCell>
                          {(['content', 'structure', 'completeness', 'accuracy', 'overall'] as const).map((metric) => {
                            const value = iteration.scores[metric];
                            const pass = value >= threshold;
                            const cellClass = metric === 'overall' ? 'text-right font-semibold text-[hsl(var(--heading))]' : 'text-right';
                            return (
                              <TableCell key={metric} className={cn(cellClass, pass ? undefined : 'text-destructive')}>
                                {formatPercent(value)}
                                {!pass ? (
                                  <span className="ml-1 text-xs text-muted-foreground">(threshold {formatPercent(threshold)})</span>
                                ) : null}
                              </TableCell>
                            );
                          })}
                        </TableRow>
                      );
                    })}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

           <Card>
             <CardHeader>
               <CardTitle>Trust Compass</CardTitle>
               <CardDescription>4-axis radial graph inspired by BoxerLogic: Faithfulness, Reliability, Coherence, Adaptability.</CardDescription>
             </CardHeader>
             <CardContent style={{ height: 320 }}>
               <TrustCompass
                 scores={{
                   faithfulness: activeData.scores.accuracy,
                   reliability: activeData.scores.completeness,
                   coherence: activeData.scores.structure,
                   adaptability: activeData.scores.content,
                 }}
               />
             </CardContent>
           </Card>

           <Card>
             <CardHeader>
               <CardTitle>Trust Compass</CardTitle>
               <CardDescription>4-axis radial graph inspired by BoxerLogic: Faithfulness, Reliability, Coherence, Adaptability.</CardDescription>
             </CardHeader>
             <CardContent style={{ height: 320 }}>
               <TrustCompass
                 scores={{
                   faithfulness: activeData.scores.accuracy,
                   reliability: activeData.scores.completeness,
                   coherence: activeData.scores.structure,
                   adaptability: activeData.scores.content,
                 }}
               />
             </CardContent>
           </Card>

          <Card>
            <CardHeader>
              <CardTitle>Extracted Sample</CardTitle>
              <CardDescription>Raw payload returned by the extraction agent.</CardDescription>
            </CardHeader>
            <CardContent>
              <JsonPanel title="Structured Output" data={coerceSample(activeData.sample)} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Failure Drill-down</CardTitle>
              <CardDescription>Objectives below the active threshold.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {!activeData.objectives ? (
                <p className="text-sm text-muted-foreground">Objective detail not available for this snapshot.</p>
              ) : failingObjectives.length === 0 ? (
                <p className="text-sm text-muted-foreground">No failing objectives at this threshold.</p>
              ) : (
                <div className="space-y-2">
                  {failingObjectives.map((objective) => (
                    <button
                      key={objective.name}
                      type="button"
                      onClick={() => setSelectedObjective(objective.name)}
                      className={cn(
                        'w-full rounded-md border px-3 py-2 text-left text-sm transition-colors',
                        selectedObjective === objective.name ? 'border-[hsl(var(--accent))] bg-muted/60' : 'border-border hover:bg-muted/40'
                      )}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-[hsl(var(--heading))]">{objective.name}</span>
                        <span className="text-destructive">{objective.score.toFixed(2)}</span>
                      </div>
                      <p className="mt-1 text-xs text-muted-foreground">Tap to view input/output</p>
                    </button>
                  ))}
                </div>
              )}

              {selectedObjectiveDetail ? (
                <div className="space-y-3 rounded-md border border-border/70 bg-card/80 p-4 text-sm text-muted-foreground">
                  <div>
                    <span className="font-medium text-foreground">Input</span>
                    <pre className="mt-1 whitespace-pre-wrap rounded bg-muted/50 p-2 text-xs text-muted-foreground">
                      <code>{selectedObjectiveDetail.input}</code>
                    </pre>
                  </div>
                  <div>
                    <span className="font-medium text-foreground">Output</span>
                    <pre className="mt-1 whitespace-pre-wrap rounded bg-muted/50 p-2 text-xs text-muted-foreground">
                      <code>{selectedObjectiveDetail.output}</code>
                    </pre>
                  </div>
                  <div>
                    <span className="font-medium text-foreground">Notes</span>
                    <p className="mt-1 text-xs text-muted-foreground">{selectedObjectiveDetail.notes}</p>
                  </div>
                </div>
              ) : null}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Judge Feedback</CardTitle>
              <CardDescription>LLM judge guidance that shaped the next iteration.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {(activeData.judgeNotes ?? []).length ? (
                activeData.judgeNotes!.map((feedback, index) => (
                  <div key={index} className="rounded-md border border-border/70 bg-secondary/40 p-3 text-sm text-muted-foreground">
                    <span className="font-medium text-[hsl(var(--heading))]">Feedback {index + 1}:</span> {feedback}
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">No judge feedback recorded.</p>
              )}
            </CardContent>
          </Card>
        </section>
      </div>
    </div>
  );
}
