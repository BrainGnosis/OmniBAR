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
import { cn } from '@/lib/utils';

const DATA_URL = '/data/document_extraction_benchmarks.json';

type ScoreBreakdown = {
  content: number;
  structure: number;
  completeness: number;
  accuracy: number;
  overall: number;
};

type IterationRecord = {
  id: string;
  label: string;
  strategy: string;
  model: string;
  run_seconds: number;
  avg_output_tokens: number;
  scores: ScoreBreakdown;
};

type DashboardPayload = {
  generatedAt: string;
  iterations: IterationRecord[];
};

type IterationMetadata = {
  id: string;
  promptHighlights: string[];
  summary: string;
  radar: Array<{ metric: string; value: number }>;
  extracted: unknown;
  judgeFeedback: string[];
};

const ITERATION_DETAILS: IterationMetadata[] = [
  {
    id: 'iter1',
    promptHighlights: ['Zero-shot', 'No schema hints', 'High hallucination risk'],
    summary:
      'Pure instructions, no exemplars. Misses nested tables and multi-line addresses—baseline for comparison.',
    radar: [
      { metric: 'Entity Recall', value: 0.52 },
      { metric: 'Line-item Accuracy', value: 0.46 },
      { metric: 'Date Normalisation', value: 0.62 },
      { metric: 'Currency Handling', value: 0.49 },
      { metric: 'Layout Robustness', value: 0.44 }
    ],
    extracted: {
      invoice_number: 'INV-1049',
      vendor: 'Northwind Supplies',
      total_due: '$18,430.11',
      due_date: '2025-02-17',
      line_items: [
        { sku: 'NW-4821', description: 'Acrylic signage kit', quantity: 24, unit_price: '$215.00' },
        { sku: 'NW-9930', description: 'Premium mounting hardware set (12 pack)', quantity: 6, unit_price: '$87.00' }
      ]
    },
    judgeFeedback: [
      'Missed secondary address block and misread the PO box number.',
      'Line item quantity parsed correctly, but unit cost formatting drifted.',
      'Requested structured JSON, but response mixed snake_case and camelCase keys.'
    ]
  },
  {
    id: 'iter2',
    promptHighlights: ['Two exemplars', 'Explicit schema keys', 'Validation checklist'],
    summary:
      'Adds exemplars plus schema spec. Stronger consistency, still volatile currency rounding in narration.',
    radar: [
      { metric: 'Entity Recall', value: 0.68 },
      { metric: 'Line-item Accuracy', value: 0.65 },
      { metric: 'Date Normalisation', value: 0.79 },
      { metric: 'Currency Handling', value: 0.58 },
      { metric: 'Layout Robustness', value: 0.63 }
    ],
    extracted: {
      invoice_number: 'INV-1049',
      vendor: {
        name: 'Northwind Supplies',
        address: '81 Devonshire Street, Suite 400, Boston, MA 02109'
      },
      total_due: {
        value: 18430.11,
        currency: 'USD'
      },
      due_date: '2025-02-17',
      line_items: [
        { sku: 'NW-4821', description: 'Acrylic signage kit', quantity: 24, unit_price: 215.0 },
        { sku: 'NW-9930', description: 'Premium mounting hardware set', quantity: 6, unit_price: 87.0 },
        { sku: 'NW-1188', description: 'Expedited freight (2-day)', quantity: 1, unit_price: 145.0 }
      ]
    },
    judgeFeedback: [
      'Schema compliance improved; casing consistent with contract.',
      'Currency normalisation still returns stringified amounts in narration paragraph.',
      'Exemplar referencing improved reasoning trace clarity.'
    ]
  },
  {
    id: 'iter3',
    promptHighlights: ['Calls table_extractor tool', 'Post-process regex checks', 'Confidence tags'],
    summary: 'Introduces table extractor tool and regex guards. Strong gains on line-items.',
    radar: [
      { metric: 'Entity Recall', value: 0.83 },
      { metric: 'Line-item Accuracy', value: 0.82 },
      { metric: 'Date Normalisation', value: 0.86 },
      { metric: 'Currency Handling', value: 0.78 },
      { metric: 'Layout Robustness', value: 0.74 }
    ],
    extracted: {
      invoice_number: 'INV-1049',
      vendor: {
        name: 'Northwind Supplies',
        address: {
          street: '81 Devonshire Street',
          suite: 'Suite 400',
          city: 'Boston',
          state: 'MA',
          postal_code: '02109'
        }
      },
      totals: {
        subtotal: 17685.11,
        tax: 745.0,
        total_due: 18430.11,
        currency: 'USD'
      },
      due_date: '2025-02-17',
      line_items: [
        { sku: 'NW-4821', description: 'Acrylic signage kit', quantity: 24, unit_price: 215.0, confidence: 0.92 },
        { sku: 'NW-9930', description: 'Premium mounting hardware set', quantity: 6, unit_price: 87.0, confidence: 0.89 },
        { sku: 'NW-1188', description: 'Expedited freight (2-day)', quantity: 1, unit_price: 145.0, confidence: 0.85 }
      ]
    },
    judgeFeedback: [
      'Tool call preserved table order; no hallucinated rows detected.',
      'Regex guard caught stray percentage sign and forced retry—excellent.',
      'Recommended adding business-rule: freight lines must be tagged as optional.'
    ]
  },
  {
    id: 'iter4',
    promptHighlights: ['Retrieval context', 'Validator critique loop', 'Cost cap reminders'],
    summary:
      'Final iteration leveraging historical corrections and validator feedback. Production candidate.',
    radar: [
      { metric: 'Entity Recall', value: 0.88 },
      { metric: 'Line-item Accuracy', value: 0.89 },
      { metric: 'Date Normalisation', value: 0.92 },
      { metric: 'Currency Handling', value: 0.85 },
      { metric: 'Layout Robustness', value: 0.82 }
    ],
    extracted: {
      invoice_number: 'INV-1049',
      vendor: {
        name: 'Northwind Supplies',
        address: {
          street: '81 Devonshire Street',
          suite: 'Suite 400',
          city: 'Boston',
          state: 'MA',
          postal_code: '02109',
          country: 'USA'
        },
        contact: {
          email: 'ap@northwind.com',
          phone: '+1-617-555-0198'
        }
      },
      totals: {
        subtotal: 17685.11,
        tax: 745.0,
        total_due: 18430.11,
        currency: 'USD',
        payment_terms: 'Net 30'
      },
      due_date: '2025-02-17',
      line_items: [
        { sku: 'NW-4821', description: 'Acrylic signage kit', quantity: 24, unit_price: 215.0, confidence: 0.94 },
        { sku: 'NW-9930', description: 'Premium mounting hardware set', quantity: 6, unit_price: 87.0, confidence: 0.91 },
        { sku: 'NW-1188', description: 'Expedited freight (2-day)', quantity: 1, unit_price: 145.0, confidence: 0.9 }
      ],
      validation_flags: []
    },
    judgeFeedback: [
      'Extraction aligns with validator corrections—no remaining schema drift.',
      'Consider trimming retrieval context: 30% of tokens are redundant headers.',
      'Confidence scores tracked across line-items and totals—great for monitoring.'
    ]
  }
];

function formatSeconds(value: number): string {
  return `${value.toFixed(1)} s`;
}

function formatTokens(value: number): string {
  return `${value} tokens`;
}

function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export default function DocumentExtraction() {
  const [data, setData] = useState<DashboardPayload | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    fetch(DATA_URL)
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`Failed to load dashboard data (${response.status})`);
        }
        return (await response.json()) as DashboardPayload;
      })
      .then((payload) => {
        if (mounted) {
          setData(payload);
          setSelectedId(payload.iterations[0]?.id ?? null);
        }
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
  }, []);

  const bestIteration = useMemo(() => {
    if (!data) return null;
    return data.iterations.reduce<IterationRecord | null>((best, current) => {
      if (!best) return current;
      return current.scores.overall > best.scores.overall ? current : best;
    }, null);
  }, [data]);

  const activeIteration = useMemo(() => {
    if (!data || !selectedId) return null;
    return data.iterations.find((item) => item.id === selectedId) ?? data.iterations[0] ?? null;
  }, [data, selectedId]);

  const activeMetadata = useMemo(() => {
    if (!activeIteration) return null;
    return ITERATION_DETAILS.find((item) => item.id === activeIteration.id) ?? null;
  }, [activeIteration]);

  if (loading) {
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

  if (!data || !activeIteration || !activeMetadata) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-semibold tracking-tight">Document Extraction Benchmarks</h1>
        <p className="text-sm text-muted-foreground">No benchmark data available. Run the generator script first.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-3xl font-semibold tracking-tight">Document Extraction Benchmarks</h1>
        <p className="text-muted-foreground text-sm">
          Snapshot generated {new Date(data.generatedAt).toLocaleString()}. Compare prompt strategies across core reliability
          dimensions—content, structure, completeness, accuracy, and overall fitness.
        </p>
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
                const isActive = iteration.id === activeIteration.id;
                const isWinner = bestIteration?.id === iteration.id;
                return (
                  <Button
                    key={iteration.id}
                    variant={isActive ? 'primary' : 'secondary'}
                    className={cn(
                      'w-full items-center justify-between text-left',
                      !isActive && 'bg-muted/50 text-muted-foreground'
                    )}
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
              <CardDescription>{activeIteration.strategy}</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-wrap gap-2">
              {activeMetadata.promptHighlights.map((item) => (
                <Badge key={item} variant="outline">
                  {item}
                </Badge>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Iteration Notes</CardTitle>
              <CardDescription>Why this prompt matters.</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">{activeMetadata.summary}</p>
            </CardContent>
          </Card>
        </aside>

        <section className="space-y-6">
          <Card>
            <CardHeader className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <CardTitle>{activeIteration.label}</CardTitle>
                <CardDescription>{activeIteration.strategy}</CardDescription>
              </div>
              <div className="flex flex-wrap items-center gap-6 text-sm text-muted-foreground">
                <div>
                  <p className="text-xs uppercase tracking-wide">Model</p>
                  <p className="text-sm font-medium text-foreground">{activeIteration.model}</p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-wide">Run Time</p>
                  <p className="text-sm font-medium text-foreground">{formatSeconds(activeIteration.run_seconds)}</p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-wide">Avg Output Length</p>
                  <p className="text-sm font-medium text-foreground">{formatTokens(activeIteration.avg_output_tokens)}</p>
                </div>
              </div>
            </CardHeader>
          </Card>

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {(['content', 'structure', 'completeness', 'accuracy'] as const).map((metric) => (
              <Card key={metric}>
                <CardHeader>
                  <CardTitle className="text-base capitalize">{metric}</CardTitle>
                  <CardDescription>LLM judge metric</CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-semibold text-[hsl(var(--heading))]">
                    {formatPercent(activeIteration.scores[metric])}
                  </p>
                </CardContent>
              </Card>
            ))}
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
                      const isActive = activeIteration.id === iteration.id;
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
                          <TableCell className="text-right">{formatPercent(iteration.scores.content)}</TableCell>
                          <TableCell className="text-right">{formatPercent(iteration.scores.structure)}</TableCell>
                          <TableCell className="text-right">{formatPercent(iteration.scores.completeness)}</TableCell>
                          <TableCell className="text-right">{formatPercent(iteration.scores.accuracy)}</TableCell>
                          <TableCell className="text-right font-semibold text-[hsl(var(--heading))]">
                            {formatPercent(iteration.scores.overall)}
                          </TableCell>
                        </TableRow>
                      );
                    })}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Quality Radar</CardTitle>
              <CardDescription>Granular capability scores for this iteration.</CardDescription>
            </CardHeader>
            <CardContent style={{ height: 320 }}>
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={activeMetadata.radar} outerRadius="75%">
                  <PolarGrid stroke="hsl(var(--muted-foreground))" strokeOpacity={0.4} />
                  <PolarAngleAxis dataKey="metric" tick={{ fontSize: 11 }} />
                  <PolarRadiusAxis tickFormatter={(value) => `${Math.round(value * 100)}%`} domain={[0, 1]} tickCount={5} />
                  <Radar
                    name="Score"
                    dataKey="value"
                    stroke="hsl(var(--accent))"
                    fill="hsl(var(--accent))"
                    fillOpacity={0.3}
                  />
                  <RadarTooltip formatter={(value: number) => `${Math.round((value as number) * 100)}%`} />
                </RadarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Extracted JSON</CardTitle>
              <CardDescription>Raw payload returned by the extraction agent.</CardDescription>
            </CardHeader>
            <CardContent>
              <JsonPanel title="Structured Output" data={activeMetadata.extracted} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Judge Feedback</CardTitle>
              <CardDescription>LLM judge guidance that shaped the next iteration.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {activeMetadata.judgeFeedback.map((feedback, index) => (
                <div key={index} className="rounded-md border border-border/70 bg-secondary/40 p-3 text-sm text-muted-foreground">
                  <span className="font-medium text-[hsl(var(--heading))]">Feedback {index + 1}:</span> {feedback}
                </div>
              ))}
            </CardContent>
          </Card>
        </section>
      </div>
    </div>
  );
}
