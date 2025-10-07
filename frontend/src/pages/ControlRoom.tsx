import { useEffect, useMemo, useState } from 'react';
import { ArrowPathIcon } from '@heroicons/react/24/outline';
import { ShieldCheckIcon, BoltIcon } from '@heroicons/react/24/solid';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { BenchmarkCard, TeamCard, JobCard } from '@/components/design/cards';
import { useBenchmarkStore } from '@/stores/benchmarkStore';
import { cn } from '@/lib/utils';
import { getStoredThreshold, setStoredThreshold, getDefaultThreshold } from '@/lib/threshold';
import { getLLMHealth } from '@/lib/api';

const LLM_HEALTH_MODEL = import.meta.env.VITE_LLM_HEALTH_MODEL ?? 'gpt-4o-mini';

const SUITE_OPTIONS = [
  {
    id: 'output',
    title: 'Calculator Demo Suite',
    description:
      "Mirrors the basic output evaluation script—runs addition string checks, multiplication regex, and a combined objective run.",
    cta: 'Run calculator demo'
  },
  {
    id: 'custom',
    title: 'Custom Agents Suite',
    description: 'Exercises weather and translation agents with custom invoke methods and failure handling.',
    cta: 'Run custom suite'
  },
  {
    id: 'crisis',
    title: 'Crisis Command Suite',
    description:
      'Simulates the complex inventory management benchmark—checks crisis order fulfillment and strategic path efficiency.',
    cta: 'Run crisis suite'
  },
  {
    id: 'all',
    title: 'Run Everything',
    description: 'Execute every suite above and aggregate the reliability snapshot in one click.',
    cta: 'Run all suites'
  }
];

export default function ControlRoom() {
  const {
    fetchBenchmarks,
    loading,
    error,
    summary,
    benchmarks,
    liveRuns,
    failureInsights,
    recommendations
  } = useBenchmarkStore();
  const [threshold, setThreshold] = useState(() => getStoredThreshold());
  const [llmStatus, setLLMStatus] = useState<'idle' | 'loading' | 'ok' | 'down'>('idle');
  const [llmLatency, setLLMLatency] = useState<number | null>(null);
  const [llmMessage, setLLMMessage] = useState<string>('');

  useEffect(() => {
    void fetchBenchmarks('output');
  }, [fetchBenchmarks]);

  useEffect(() => {
    setStoredThreshold(threshold);
    const params = new URLSearchParams(window.location.search);
    params.set('threshold', threshold.toFixed(2));
    const query = params.toString();
    const url = `${window.location.pathname}${query ? `?${query}` : ''}`;
    window.history.replaceState(null, '', url);
    window.dispatchEvent(new CustomEvent('omnibar-threshold', { detail: { value: threshold } }));
  }, [threshold]);

  const runSuite = (suiteId: string) => {
    void fetchBenchmarks(suiteId);
  };

  const handleThresholdChange = (value: number) => {
    if (!Number.isFinite(value)) return;
    const clamped = Math.min(Math.max(value, 0.1), 1);
    setThreshold(Number(clamped.toFixed(2)));
  };

  const fetchLLMStatus = async () => {
    setLLMStatus('loading');
    setLLMLatency(null);
    setLLMMessage('');
    try {
      const health = await getLLMHealth();
      setLLMStatus(health.status === 'ok' ? 'ok' : 'down');
      setLLMLatency(health.latency);
      setLLMMessage(health.output);
    } catch (error) {
      setLLMStatus('down');
      setLLMMessage(error instanceof Error ? error.message : 'Unable to reach LLM endpoint');
    }
  };

  useEffect(() => {
    void fetchLLMStatus();
  }, []);

  const quickGlance = useMemo(
    () => [
      { label: 'Benchmarks tracked', value: summary.total, tone: 'text-brand-primary' },
      { label: 'Passing', value: summary.success, tone: 'text-emerald-600' },
      { label: 'Needs attention', value: summary.failed, tone: 'text-red-600' }
    ],
    [summary]
  );

  const suitePayload = useMemo(
    () => ({
      summary,
      liveRuns,
      failureInsights,
      recommendations,
      benchmarks
    }),
    [summary, liveRuns, failureInsights, recommendations, benchmarks]
  );

  const prettifiedSuitePayload = useMemo(
    () => JSON.stringify(suitePayload, null, 2),
    [suitePayload]
  );

  const hasSuiteData = useMemo(
    () =>
      Boolean(
        summary.total ||
          liveRuns.length ||
          failureInsights.length ||
          recommendations.length ||
          benchmarks.length
      ),
    [summary.total, liveRuns.length, failureInsights.length, recommendations.length, benchmarks.length]
  );

  const handleDownloadSuiteJson = () => {
    const blob = new Blob([prettifiedSuitePayload], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'reliability-suite-snapshot.json';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const renderLLMStatus = () => {
    switch (llmStatus) {
      case 'loading':
        return <span className="text-sm text-muted-foreground">Pinging LLM…</span>;
      case 'ok':
        return (
          <div className="flex flex-col text-sm text-emerald-600">
            <span>LLM reachable · latency {llmLatency ? `${llmLatency.toFixed(2)}s` : '—'}</span>
            <span className="text-xs text-muted-foreground">Output: {llmMessage}</span>
          </div>
        );
      case 'down':
        return (
          <div className="flex flex-col text-sm text-destructive">
            <span>LLM unreachable</span>
            {llmMessage ? <span className="text-xs text-muted-foreground">{llmMessage}</span> : null}
          </div>
        );
      default:
        return <span className="text-sm text-muted-foreground">LLM status unknown.</span>;
    }
  };

  return (
    <div className="min-h-screen bg-[hsl(var(--background))] text-[hsl(var(--body))]">
      <main className="mx-auto flex max-w-6xl flex-col gap-8 px-6 py-10">
        <section className="flex flex-col gap-6 rounded-2xl border bg-card/80 p-6 shadow-sm sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-4">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="outline">Structured Agents</Badge>
              <Badge variant="outline">AgentOS Visibility</Badge>
              <Badge variant="success">Live Reliability Pulse</Badge>
            </div>
            <div className="space-y-3">
              <h1>Reliability Control Room</h1>
              <p>
                Launch curated suites, monitor runtime signals, and capture a fresh snapshot before you drill into the
                Benchmarks or Runs tabs for deep analysis.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <Button
                onClick={() => runSuite('output')}
                disabled={loading}
                className="gap-2"
                variant="primary"
              >
                <ArrowPathIcon className={cn('h-4 w-4', loading && 'animate-spin')} />
                Run Output Benchmarks
              </Button>
              <Button variant="secondary" className="gap-2">
                <BoltIcon className="h-4 w-4 text-brand-accent"  title="This button is just for show right now—stay tuned!"/>
                Schedule Reliability Review
              </Button>
              <Button variant="text" className="text-sm">
                Export weekly report
              </Button>
            </div>
          </div>
          <div className="space-y-3 rounded-xl bg-secondary/60 p-5 text-sm text-muted-foreground">
            <p className="font-medium text-[hsl(var(--heading))]">Why it matters</p>
            <p>
              Agents deployed in revenue-critical workflows deserve continuous validation. Run a suite to refresh the
              snapshot, then head to Benchmarks or Runs to review the detailed telemetry.
            </p>
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <ShieldCheckIcon className="h-4 w-4 text-[hsl(var(--accent))]" />
              <span>Aligned with AgentOS reliability SLOs.</span>
            </div>
          </div>
        </section>

        <section className="rounded-2xl border bg-card/80 p-6 shadow-sm">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div className="space-y-1">
              <h2 className="text-base font-semibold text-[hsl(var(--heading))]">Reliability Threshold</h2>
              <p className="text-sm text-muted-foreground">
                Scores below this value will be treated as failures across dashboards. Default is {getDefaultThreshold().toFixed(2)}.
              </p>
            </div>
            <div className="flex w-full max-w-sm items-center gap-3">
              <input
                aria-label="Reliability threshold"
                type="range"
                min="0.1"
                max="1"
                step="0.05"
                value={threshold}
                onChange={(event) => handleThresholdChange(Number(event.target.value))}
                className="grow"
              />
              <input
                aria-label="Threshold value"
                type="number"
                min="0.1"
                max="1"
                step="0.01"
                value={threshold}
                onChange={(event) => handleThresholdChange(Number(event.target.value))}
                className="w-20 rounded-md border bg-background px-2 py-1 text-right text-sm"
              />
            </div>
          </div>
        </section>

        <Card className="border bg-card/80 p-6 shadow-sm">
          <CardHeader className="flex flex-col gap-2">
            <CardTitle>LLM Connectivity</CardTitle>
            <CardDescription>Quick health check using {LLM_HEALTH_MODEL}.</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-3 text-sm">
            {renderLLMStatus()}
            <div>
              <Button variant="secondary" onClick={fetchLLMStatus} disabled={llmStatus === 'loading'}>
                {llmStatus === 'loading' ? 'Checking…' : 'Retry Health Check'}
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="border bg-card/80 p-6 shadow-sm">
          <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="space-y-1">
              <CardTitle>Suite Snapshot JSON</CardTitle>
              <CardDescription>
                Share this prettified payload with stakeholders who need the raw benchmark data.
              </CardDescription>
            </div>
            <Button
              variant="secondary"
              onClick={handleDownloadSuiteJson}
              disabled={!hasSuiteData}
              className="w-full sm:w-auto"
            >
              Download JSON
            </Button>
          </CardHeader>
          <CardContent>
            {hasSuiteData ? (
              <pre className="max-h-80 overflow-auto rounded-lg border bg-muted/40 p-4 font-mono text-xs leading-relaxed text-muted-foreground">
                {prettifiedSuitePayload}
              </pre>
            ) : (
              <p className="text-sm text-muted-foreground">
                Launch a suite to populate the summary, live runs, and recommendations snapshot.
              </p>
            )}
          </CardContent>
        </Card>

        <section className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {SUITE_OPTIONS.map((suite) => (
            <Card key={suite.id} className="h-full border-brand-primary/10">
              <CardHeader>
                <CardTitle>{suite.title}</CardTitle>
              <CardDescription>{suite.description}</CardDescription>
            </CardHeader>
            <CardContent>
              <Button
                variant="primary"
                disabled={loading}
                onClick={() => runSuite(suite.id)}
                className="gap-2"
                title="Kick off this benchmark suite with OmniBAR."
              >
                <ArrowPathIcon className={cn('h-4 w-4', loading && 'animate-spin')} />
                {suite.cta}
              </Button>
            </CardContent>
            </Card>
          ))}
        </section>

        <section className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <BenchmarkCard
            title="Benchmark Performance Snapshot"
            description="Top-line reliability metrics pulled from the latest OmniBAR snapshot."
            metrics={[
              { label: 'Benchmarks Tracked', value: summary.total.toString(), positive: true },
              {
                label: 'Success Rate',
                value: `${summary.total ? Math.round((summary.success / summary.total) * 100) : 0}%`,
                positive: summary.success >= summary.failed
              },
              { label: 'Failures', value: summary.failed.toString(), positive: summary.failed === 0 }
            ]}
            cta={<span className="text-sm text-muted-foreground">Open the Benchmarks tab for full detail.</span>}
          />
          <TeamCard
            teamName="Structured Agents Guild"
            owner="Amelia Rivera"
            focusAreas={['Prompt hygiene', 'Tool guardrails', 'Incident playbooks']}
            health="watch"
            footer={<span>Next sync: Tuesday · Focus on escalation coverage.</span>}
          />
          <JobCard
            title="Reliability Engineer, AgentOS"
            description="Own reliability instrumentation for enterprise agent deployments."
            tags={['Hybrid · NYC', 'AgentOS', 'Observability']}
            actions={
              <Button
                variant="secondary"
                title="This button is just for show right now—stay tuned!"
              >
                View role
              </Button>
            }
          />
        </section>

        {loading ? (
          <div className="flex items-center justify-center gap-2 rounded-md border border-dashed p-4 text-sm text-muted-foreground">
            <ArrowPathIcon className="h-4 w-4 animate-spin" />
            Launching suite run...
          </div>
        ) : null}

        {error ? (
          <div className="rounded-md border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">
            {error}
          </div>
        ) : null}
      </main>
    </div>
  );
}
