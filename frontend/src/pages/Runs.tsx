import { useEffect, useState } from 'react';

import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { clearRunHistory, getRecentRuns, runLLMSmokeTest } from '@/lib/api';
import type { RunHistoryEntry } from '@/types/benchmarks';

const STATUS_BADGE: Record<RunHistoryEntry['status'], { label: string; variant: 'success' | 'warning' | 'destructive' | 'default' }> = {
  success: { label: 'Success', variant: 'success' },
  needs_attention: { label: 'Needs Attention', variant: 'destructive' }
};

function formatThreshold(threshold?: number | null): string {
  if (!Number.isFinite(threshold) || threshold == null) {
    return '—';
  }
  return `${Math.round(threshold * 100)}%`;
}

export default function Runs() {
  const [runs, setRuns] = useState<RunHistoryEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [clearing, setClearing] = useState(false);
  const [smokeRunning, setSmokeRunning] = useState(false);
  const [smokeMessage, setSmokeMessage] = useState<string | null>(null);

  const loadRuns = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getRecentRuns();
      setRuns(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load run history');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadRuns();
  }, []);

  const latest = runs[0];

  const handleClearHistory = async () => {
    if (!confirm('Delete local run history? This clears backend/data/run_history.json.')) {
      return;
    }
    setClearing(true);
    try {
      await clearRunHistory();
      setRuns([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to clear history');
    } finally {
      setClearing(false);
    }
  };

  const handleSmokeTest = async () => {
    setSmokeRunning(true);
    setSmokeMessage(null);
    try {
      const result = await runLLMSmokeTest();
      setSmokeMessage(`LLM responded "${result.output}" in ${result.latency.toFixed(2)}s`);
      await loadRuns();
    } catch (error) {
      setSmokeMessage(error instanceof Error ? error.message : 'Smoke test failed');
      await loadRuns();
    } finally {
      setSmokeRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-3xl font-semibold tracking-tight">Recent Runs</h1>
        <p className="text-muted-foreground">
          Track which suites you executed, when they were requested, and how many objectives passed or failed.
          This data is appended every time you launch a suite from the Control Room.
        </p>
        <div className="flex flex-wrap items-center gap-3 pt-2">
          <Button onClick={handleClearHistory} variant="destructive" disabled={clearing}>
            {clearing ? 'Clearing…' : 'Clear Run History'}
          </Button>
          <Button onClick={handleSmokeTest} variant="secondary" disabled={smokeRunning}>
            {smokeRunning ? 'Running Smoke Test…' : 'Run LLM Smoke Test'}
          </Button>
        </div>
        {smokeMessage ? <p className="text-xs text-muted-foreground">{smokeMessage}</p> : null}
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Total Runs Logged</CardTitle>
            <CardDescription>Persisted in the local OmniBAR history file.</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-semibold">{loading ? '…' : runs.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Last Run</CardTitle>
            <CardDescription>Suite and status of the most recent execution.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {loading ? (
              <p className="text-sm text-muted-foreground">Loading…</p>
            ) : latest ? (
              <>
                <div>
                  <p className="text-lg font-medium">{latest.suiteLabel ?? latest.suite}</p>
                  <p className="text-xs text-muted-foreground">Suite ID: {latest.suite}</p>
                </div>
                {(() => {
                  const meta = STATUS_BADGE[latest.status] ?? { label: latest.status, variant: 'default' as const };
                  return <Badge variant={meta.variant}>{meta.label}</Badge>;
                })()}
                <p className="text-xs text-muted-foreground">
                  Requested {new Date(latest.requestedAt).toLocaleString()}
                </p>
                <p className="text-xs text-muted-foreground">
                  Threshold at run: {formatThreshold(latest.threshold)}
                </p>
              </>
            ) : (
              <p className="text-sm text-muted-foreground">No runs recorded yet.</p>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Failures Flagged</CardTitle>
            <CardDescription>Total failing suites across the stored history.</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-semibold text-red-600">
              {loading ? '…' : runs.filter((run) => run.failed > 0).length}
            </p>
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
          <CardTitle>Run History</CardTitle>
          <CardDescription>Ordered by request time (most recent first).</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-sm text-muted-foreground">Loading run history…</p>
          ) : runs.length === 0 ? (
            <p className="text-sm text-muted-foreground">No run history yet. Launch a suite from the Control Room to create entries.</p>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Suite</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Benchmarks</TableHead>
                    <TableHead>Successes</TableHead>
                    <TableHead>Failures</TableHead>
                    <TableHead>Threshold</TableHead>
                    <TableHead>Requested At</TableHead>
                    <TableHead>Snapshot Generated</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {runs.map((run) => {
                    const statusMeta = STATUS_BADGE[run.status] ?? { label: run.status, variant: 'default' as const };
                    return (
                      <TableRow key={run.id}>
                        <TableCell className="font-medium">
                          <div className="flex flex-col">
                            <span>{run.suiteLabel ?? run.suite}</span>
                            <span className="text-xs text-muted-foreground">Suite ID: {run.suite}</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant={statusMeta.variant}>{statusMeta.label}</Badge>
                        </TableCell>
                        <TableCell>{run.benchmarkCount}</TableCell>
                        <TableCell>{run.success}</TableCell>
                        <TableCell>{run.failed}</TableCell>
                        <TableCell>{formatThreshold(run.threshold)}</TableCell>
                        <TableCell>{new Date(run.requestedAt).toLocaleString()}</TableCell>
                        <TableCell>{run.generatedAt ? new Date(run.generatedAt).toLocaleString() : '—'}</TableCell>
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
