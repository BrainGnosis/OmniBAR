import { useEffect, useState } from 'react';

import { Badge, type BadgeProps } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { getBenchmarks } from '@/lib/api';
import type { BenchmarkRecord } from '@/types/benchmarks';

const STATUS_LABELS: Record<BenchmarkRecord['status'], { label: string; variant: BadgeProps['variant'] }> = {
  success: { label: 'Passing', variant: 'success' },
  failed: { label: 'Needs Attention', variant: 'destructive' },
  running: { label: 'Running', variant: 'default' },
  pending: { label: 'Pending', variant: 'warning' }
};

export default function Benchmarks() {
  const [benchmarks, setBenchmarks] = useState<BenchmarkRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await getBenchmarks();
        if (mounted) {
          setBenchmarks(data);
        }
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : 'Unable to load benchmarks');
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  const total = benchmarks.length;
  const failing = benchmarks.filter((record) => record.status === 'failed').length;
  const passing = benchmarks.filter((record) => record.status === 'success').length;

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-3xl font-semibold tracking-tight">Benchmark Library</h1>
        <p className="text-muted-foreground">
          This roster pulls from the latest OmniBAR snapshot. Each row captures the most recent run health,
          cost estimates, and latency profile for the suite benchmarks you executed from the Control Room.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Total Benchmarks</CardTitle>
            <CardDescription>Tracked in the most recent run snapshot.</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-semibold">{loading ? '…' : total}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Passing</CardTitle>
            <CardDescription>Benchmarks with zero current failures.</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-semibold text-emerald-600">{loading ? '…' : passing}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Needs Attention</CardTitle>
            <CardDescription>Benchmarks with at least one failing objective.</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-semibold text-red-600">{loading ? '…' : failing}</p>
          </CardContent>
        </Card>
      </div>

      {error ? (
        <div className="rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
          {error}
        </div>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>Latest Benchmark Snapshot</CardTitle>
          <CardDescription>The canonical view of the suites captured in the most recent run.</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-sm text-muted-foreground">Loading benchmarks…</p>
          ) : benchmarks.length === 0 ? (
            <p className="text-sm text-muted-foreground">No benchmark data yet. Run a suite from the Control Room to populate this view.</p>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Suite</TableHead>
                    <TableHead>Iterations</TableHead>
                    <TableHead>Success Rate</TableHead>
                    <TableHead>Latency (s)</TableHead>
                    <TableHead>Cost ($)</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Updated</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {benchmarks.map((record) => {
                    const statusConfig = STATUS_LABELS[record.status] ?? STATUS_LABELS.pending;
                    return (
                      <TableRow key={record.id}>
                        <TableCell className="font-medium">{record.name}</TableCell>
                        <TableCell>{record.suite ?? '—'}</TableCell>
                        <TableCell>{record.iterations}</TableCell>
                        <TableCell>{`${Math.round(record.successRate * 100)}%`}</TableCell>
                        <TableCell>{record.latencySeconds?.toFixed(2) ?? '—'}</TableCell>
                        <TableCell>{record.costUsd?.toFixed(4) ?? '—'}</TableCell>
                        <TableCell>
                          <Badge variant={statusConfig.variant}>{statusConfig.label}</Badge>
                        </TableCell>
                        <TableCell>{new Date(record.updatedAt).toLocaleString()}</TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
