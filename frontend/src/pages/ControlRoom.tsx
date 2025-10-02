import { ArrowPathIcon } from '@heroicons/react/24/outline';
import { ShieldCheckIcon, BoltIcon } from '@heroicons/react/24/solid';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { BenchmarkCard, TeamCard, JobCard } from '@/components/design/cards';
import { useBenchmarkStore } from '@/stores/benchmarkStore';
import { cn } from '@/lib/utils';

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
  const { fetchBenchmarks, loading, error, summary } = useBenchmarkStore();

  const runSuite = (suiteId: string) => {
    void fetchBenchmarks(suiteId);
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
                <BoltIcon className="h-4 w-4 text-brand-accent" />
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

        {error ? (
          <div className="rounded-md border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">
            {error}
          </div>
        ) : null}

        <section className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Next Steps</CardTitle>
              <CardDescription>Use the navigation to review the freshest benchmark roster or run log.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-muted-foreground">
              <p>
                Benchmarks tab &rarr; full roster, latencies, and cost traces from the latest snapshot you trigger here.
              </p>
              <p>Runs tab &rarr; every historical suite execution with successes, failures, and timestamps.</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Snapshot Quick Glance</CardTitle>
              <CardDescription>High-level counts from the most recent run.</CardDescription>
            </CardHeader>
            <CardContent className="flex items-center gap-6 text-sm">
              <div>
                <p className="text-xs uppercase tracking-wide text-muted-foreground">Benchmarks tracked</p>
                <p className="text-2xl font-semibold text-brand-primary">{summary.total}</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-wide text-muted-foreground">Passing</p>
                <p className="text-2xl font-semibold text-emerald-600">{summary.success}</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-wide text-muted-foreground">Needs attention</p>
                <p className="text-2xl font-semibold text-red-600">{summary.failed}</p>
              </div>
            </CardContent>
          </Card>
        </section>

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
            actions={<Button variant="secondary">View role</Button>}
          />
        </section>

        {loading ? (
          <div className="flex items-center justify-center gap-2 rounded-md border border-dashed p-4 text-sm text-muted-foreground">
            <ArrowPathIcon className="h-4 w-4 animate-spin" />
            Launching suite run...
          </div>
        ) : null}
      </main>
    </div>
  );
}
