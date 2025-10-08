import { ChangeEvent, FormEvent, useCallback, useEffect, useMemo, useState } from 'react';
import { ArrowPathIcon, BoltIcon, DocumentTextIcon, ArrowDownTrayIcon } from '@heroicons/react/24/outline';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { createLatteRun, getLatteConfig, getLatteRollups, getLatteRuns } from '@/lib/api';
import type { LatteConfig, LatteCreatePayload, LatteRollups, LatteRun } from '@/types';
import { LatteLogo } from '@/components/design/latteLogo';

type FormState = {
  systemPrompt: string;
  userPrompt: string;
  temperature: number;
  model: string;
  mock: boolean | null;
};

const DEFAULT_SYSTEM_PROMPT =
  'You are a world-class AI barista who responds with warmth and precision.';

const FALLBACK_CONFIG: LatteConfig = {
  mock_mode: true,
  default_model: 'gpt-4o-mini',
  scoring_model: 'gpt-4o-mini',
  available_models: ['gpt-4o-mini', 'gpt-3.5-turbo'],
};

const FALLBACK_RUN: LatteRun = {
  id: 1,
  created_at: new Date().toISOString(),
  system_prompt: DEFAULT_SYSTEM_PROMPT,
  user_prompt: 'Describe the perfect autumn cappuccino.',
  temperature: 0.6,
  model: 'gpt-4o-mini',
  response:
    'The perfect autumn cappuccino pairs a velvety double shot with steamed oat milk, a drizzle of maple, and a dusting of cinnamon.',
  score: 0.92,
  baristas_note: 'Rich description with clear sensory notes and seasonal flair—OmniBAR approves.',
  scoring_breakdown: { mode: 'offline-demo' },
  latency_ms: 420,
  prompt_tokens: null,
  completion_tokens: null,
  total_tokens: null,
  mock_run: true,
};

const FALLBACK_ROLLUPS: LatteRollups = {
  total_runs: 1,
  average_score: FALLBACK_RUN.score,
  success_rate: 1,
  mock_runs: 1,
  model_breakdown: [
    {
      model: FALLBACK_RUN.model,
      average_score: FALLBACK_RUN.score,
      run_count: 1,
      last_run: FALLBACK_RUN.created_at,
    },
  ],
  daily_scores: [
    {
      date: FALLBACK_RUN.created_at.slice(0, 10),
      average_score: FALLBACK_RUN.score,
      run_count: 1,
    },
  ],
};

const formatDateTime = (value: string) => new Date(value).toLocaleString();
const formatPercent = (value: number) => `${Math.round(value * 100)}%`;

export default function OmniBrew() {
  const [config, setConfig] = useState<LatteConfig | null>(null);
  const [form, setForm] = useState<FormState>({
    systemPrompt: DEFAULT_SYSTEM_PROMPT,
    userPrompt: '',
    temperature: 0.7,
    model: '',
    mock: null,
  });
  const [runs, setRuns] = useState<LatteRun[]>([]);
  const [rollups, setRollups] = useState<LatteRollups | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const bootstrap = async () => {
      try {
        const [cfg, history, metrics] = await Promise.all([
          getLatteConfig(),
          getLatteRuns(),
          getLatteRollups(),
        ]);
        setConfig(cfg);
        setRuns(history);
        setRollups(metrics);
        setForm((prev) => ({ ...prev, model: cfg.default_model }));
      } catch (err) {
        console.error(err);
        setConfig(FALLBACK_CONFIG);
        setRuns([FALLBACK_RUN]);
        setRollups(FALLBACK_ROLLUPS);
        setForm((prev) => ({ ...prev, model: FALLBACK_CONFIG.default_model }));
        setError('Connected in offline demo mode. Live API is unavailable.');
      }
    };

    void bootstrap();
  }, []);

  const isMockMode = useMemo(() => {
    if (!config) return false;
    if (form.mock !== undefined && form.mock !== null) {
      return form.mock;
    }
    return config.mock_mode;
  }, [config, form.mock]);

  const isLiveMode = useMemo(() => !isMockMode, [isMockMode]);

  const refreshData = useCallback(async () => {
    try {
      const [history, metrics] = await Promise.all([getLatteRuns(), getLatteRollups()]);
      setRuns(history);
      setRollups(metrics);
    } catch (err) {
      console.error(err);
    }
  }, []);

  const handleDownloadLog = () => {
    if (runs.length === 0) return;
    const generatedAt = new Date().toISOString();
    const header = [
      'id',
      'created_at',
      'mode',
      'model',
      'score',
      'latency_ms',
      'system_prompt',
      'user_prompt',
      'response',
      'baristas_note',
      'prompt_tokens',
      'completion_tokens',
      'total_tokens',
      'scoring_breakdown'
    ];
    const quote = (value: unknown) => {
      const str = value === null || value === undefined ? '' : String(value);
      return `"${str.replace(/"/g, '""')}"`;
    };
    const rows = runs.map((run) =>
      [
        run.id,
        run.created_at,
        run.mock_run ? 'mock' : 'live',
        run.model,
        run.score,
        run.latency_ms,
        run.system_prompt,
        run.user_prompt,
        run.response,
        run.baristas_note,
        run.prompt_tokens ?? '',
        run.completion_tokens ?? '',
        run.total_tokens ?? '',
        JSON.stringify(run.scoring_breakdown)
      ].map(quote).join(',')
    );
    const csv = [
      `# OmniBrew run log exported ${generatedAt} (${isMockMode ? 'mock' : 'live'} mode)`,
      header.join(','),
      ...rows
    ].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `omnibrew-run-log-${generatedAt.replace(/[:.]/g, '-')}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setError(null);

    const payload: LatteCreatePayload = {
      system_prompt: form.systemPrompt,
      user_prompt: form.userPrompt,
      temperature: form.temperature,
      model: form.model,
      mock: form.mock,
    };

    try {
      const run = await createLatteRun(payload);
      setRuns((prev) => [run, ...prev]);
      await refreshData();
      setForm((prev) => ({ ...prev, userPrompt: '' }));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to brew latte');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = event.target;
    setForm((prev) => ({
      ...prev,
      [name]:
        name === 'temperature'
          ? Number(value)
          : value,
    }));
  };

  const handleMockChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value;
    setForm((prev) => ({
      ...prev,
      mock: value === 'inherit' ? null : value === 'true',
    }));
  };

  const modelStats = rollups?.model_breakdown ?? [];

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-2">
        <div className="flex items-center gap-2">
          <h2 className="text-3xl font-semibold tracking-tight">OmniBrew</h2>
  <LatteLogo />

          {isMockMode && <Badge>Mock mode</Badge>}
          {isLiveMode && <Badge>Live mode</Badge>}
        </div>
        <p className="text-muted-foreground">
          Craft prompt traces, send them to OmniBAR, and track scoring history without leaving the studio.
        </p>
        {config && (
          <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
            <span className="inline-flex items-center gap-1 rounded-full border border-border px-3 py-1">
              <BoltIcon className="h-4 w-4" />
              Default model {config.default_model}
            </span>
            <span className="inline-flex items-center gap-1 rounded-full border border-border px-3 py-1">
              <DocumentTextIcon className="h-4 w-4" />
              Scoring model {config.scoring_model}
            </span>
          </div>
        )}
      </header>

      {error && (
        <div className="rounded-lg border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
        <Card>
          <CardHeader>
            <CardTitle>Pull a fresh shot</CardTitle>
            <CardDescription>
              Provide prompts and optional model overrides. OmniBAR will brew the response and score fidelity.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-4" onSubmit={handleSubmit}>
              <div className="space-y-2">
                <label htmlFor="systemPrompt" className="text-sm font-medium text-foreground">
                  System prompt
                </label>
                <textarea
                  id="systemPrompt"
                  name="systemPrompt"
                  value={form.systemPrompt}
                  onChange={handleInputChange}
                  className="min-h-[120px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
                />
              </div>
              <div className="space-y-2">
                <label htmlFor="userPrompt" className="text-sm font-medium text-foreground">
                  User prompt
                </label>
                <textarea
                  id="userPrompt"
                  name="userPrompt"
                  value={form.userPrompt}
                  onChange={handleInputChange}
                  placeholder="Share your latte scenario…"
                  className="min-h-[120px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
                  required
                />
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <label htmlFor="temperature" className="text-sm font-medium text-foreground">
                    Temperature ({form.temperature.toFixed(1)})
                  </label>
                  <Input
                    id="temperature"
                    name="temperature"
                    type="number"
                    step="0.1"
                    min={0}
                    max={2}
                    value={form.temperature}
                    onChange={handleInputChange}
                  />
                </div>
                <div className="space-y-2">
                  <label htmlFor="model" className="text-sm font-medium text-foreground">
                    Model
                  </label>
                  <select
                    id="model"
                    name="model"
                    value={form.model}
                    onChange={handleInputChange}
                    className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
                  >
                    {config?.available_models.map((model) => (
                      <option key={model} value={model}>
                        {model}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="space-y-2">
                <label htmlFor="mock" className="text-sm font-medium text-foreground">
                  Run mode
                </label>
                <select
                  id="mock"
                  name="mock"
                  value={form.mock === null ? 'inherit' : String(form.mock)}
                  onChange={handleMockChange}
                  className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
                >
                  <option value="inherit">
                    Inherit ({config?.mock_mode ? 'mock' : 'live'})
                  </option>
                  <option value="false">Live Mode</option>
                  <option value="true">Mock Mode</option>
                </select>
              </div>
              <Button type="submit" disabled={loading} className="flex items-center gap-2">
                {loading && <ArrowPathIcon className="h-4 w-4 animate-spin" />}
                {loading ? 'Brewing…' : 'OmniBrew run'}
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card className="h-fit">
          <CardHeader>
            <CardTitle>OmniBAR snapshot</CardTitle>
            <CardDescription>
              Trace health from the last 30 runs. Use it as a quick reliability read.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="rounded-lg border border-border px-4 py-3">
                <p className="text-muted-foreground">Total runs</p>
                <p className="text-2xl font-semibold">{rollups?.total_runs ?? 0}</p>
              </div>
              <div className="rounded-lg border border-border px-4 py-3">
                <p className="text-muted-foreground">Average score</p>
                <p className="text-2xl font-semibold">{formatPercent(rollups?.average_score ?? 0)}</p>
              </div>
              <div className="rounded-lg border border-border px-4 py-3">
                <p className="text-muted-foreground">Success rate</p>
                <p className="text-2xl font-semibold">{formatPercent(rollups?.success_rate ?? 0)}</p>
              </div>
              <div className="rounded-lg border border-border px-4 py-3">
                <p className="text-muted-foreground">Mock runs</p>
                <p className="text-2xl font-semibold">{rollups?.mock_runs ?? 0}</p>
              </div>
            </div>
            <div className="mt-6 space-y-3">
              <h4 className="text-sm font-semibold text-muted-foreground">Models in rotation</h4>
              {modelStats.length === 0 && <p className="text-sm text-muted-foreground">No runs yet.</p>}
              {modelStats.map((model) => (
                <div
                  key={model.model}
                  className="flex items-center justify-between rounded-md border border-border/70 px-3 py-2 text-sm"
                >
                  <div className="flex flex-col">
                    <span className="font-medium">{model.model}</span>
                    <span className="text-xs text-muted-foreground">
                      Last run {model.last_run ? formatDateTime(model.last_run) : '—'}
                    </span>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold">{formatPercent(model.average_score)}</p>
                    <p className="text-xs text-muted-foreground">{model.run_count} runs</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between gap-4">
          <div>
            <CardTitle>Run history</CardTitle>
            <CardDescription>Every latte scored by OmniBAR, newest first.</CardDescription>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline" className="gap-1">
              <BoltIcon className="h-4 w-4" />
              {isMockMode ? 'Mock brewing' : 'Live brewing'}
            </Badge>
            <Button
              type="button"
              variant="secondary"
              size="sm"
              className="gap-2"
              onClick={handleDownloadLog}
              disabled={runs.length === 0}
            >
              <ArrowDownTrayIcon className="h-4 w-4" />
              Download log
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {runs.length === 0 && (
            <div className="rounded-lg border border-dashed border-border px-6 py-10 text-center text-sm text-muted-foreground">
              No latte runs yet. Brew one to see scoring details.
            </div>
          )}
          {runs.map((run) => (
            <div key={run.id} className="rounded-lg border border-border/60 bg-card/60 p-4 shadow-sm">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-sm text-muted-foreground">{formatDateTime(run.created_at)}</p>
                  <h3 className="mt-1 text-lg font-semibold">{run.user_prompt}</h3>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className="inline-flex items-center rounded-full border border-border px-3 py-1 text-sm font-medium"
                  >
                    {run.model}
                  </span>
                  <span className="inline-flex min-w-[72px] items-center justify-center rounded-full bg-primary px-3 py-1 text-sm font-semibold text-primary-foreground">
                    {formatPercent(run.score)}
                  </span>
                </div>
              </div>
              <dl className="mt-4 grid gap-4 sm:grid-cols-2">
                <div>
                  <dt className="text-xs uppercase text-muted-foreground">Response</dt>
                  <dd className="mt-1 text-sm leading-relaxed">{run.response}</dd>
                </div>
                <div>
                  <dt className="text-xs uppercase text-muted-foreground">Barista note</dt>
                  <dd className="mt-1 text-sm leading-relaxed">{run.baristas_note}</dd>
                </div>
              </dl>
              <div className="mt-4 flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
                <span className="inline-flex items-center gap-1 rounded-full border border-border px-2 py-1">
                  <ArrowPathIcon className="h-3.5 w-3.5" />
                  {run.latency_ms} ms
                </span>
                <span>
                  Tokens: prompt {run.prompt_tokens ?? '—'} · completion {run.completion_tokens ?? '—'} · total{' '}
                  {run.total_tokens ?? '—'}
                </span>
                <span>{run.mock_run ? 'Mock' : 'Live'} mode</span>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
