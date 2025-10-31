import { ReactNode } from 'react';

import { Footer } from '@/components/layout/Footer';
import { ThemeToggle } from '@/components/layout/ThemeToggle';
import { Badge } from '@/components/ui/badge';

const NAV_ITEMS = [
  { id: 'control', label: 'Control Room' },
  { id: 'benchmarks', label: 'Benchmarks' },
  { id: 'runs', label: 'Runs' },
  { id: 'documents', label: 'Doc Extraction' },
  { id: 'latte', label: 'OmniBrew' },
  { id: 'chat', label: 'Chat' },
] as const;

type Route = typeof NAV_ITEMS[number]['id'];

type AppShellProps = {
  route: Route;
  onNavigate: (route: Route) => void;
  children: ReactNode;
};

export default function AppShell({ route, onNavigate, children }: AppShellProps) {
  const environment = (() => {
    const override = (
      import.meta.env.VITE_OMNIBREW_ENV ?? import.meta.env.VITE_LATTE_ENV ?? ''
    )
      .toString()
      .trim()
      .toLowerCase();
    if (override === 'mock') {
      return {
        label: 'Mock Mode',
        description: 'Serving mocked API responses for safe demoing.',
        variant: 'warning' as const,
      };
    }
    if (override === 'staging') {
      return {
        label: 'Staging',
        description: 'Connected to the staging OmniBrew:Prompt Review stack.',
        variant: 'outline' as const,
      };
    }
    if (override === 'production' || override === 'prod' || override === 'live') {
      return {
        label: 'Live Mode',
        description: 'Connected to the production OmniBrew:Prompt Review backend.',
        variant: 'success' as const,
      };
    }
    if (import.meta.env.VITE_ENABLE_MSW === 'true') {
      return {
        label: 'Mock Mode',
        description: 'Mock Service Worker is intercepting requests.',
        variant: 'warning' as const,
      };
    }
    return {
      label: 'Live Mode',
      description: 'Using live API responses.',
      variant: 'success' as const,
    };
  })();

  const showEnvironmentBadge = environment.variant !== 'success';

  return (
    <div className="min-h-screen bg-background text-foreground">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus:rounded-md focus:bg-card focus:px-3 focus:py-2 focus:shadow"
      >
        Skip to content
      </a>
      <header className="border-b border-border/70 bg-card/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-6 py-4 sm:flex-row sm:items-center sm:justify-between">
          <h1 className="text-xl font-semibold">OmniBAR • Agent Reliability Studio</h1>
          <div className="flex flex-col items-start gap-2 sm:flex-row sm:items-center sm:gap-4">
            {showEnvironmentBadge ? (
              <Badge variant={environment.variant} title={environment.description}>
                {environment.label}
              </Badge>
            ) : null}
            <ThemeToggle className="w-full sm:w-auto" />
            <nav className="flex items-center gap-3 text-sm font-medium">
              {NAV_ITEMS.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => onNavigate(item.id)}
                  className={`rounded-md px-3 py-2 transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[hsl(var(--accent))] ${
                    route === item.id
                      ? 'bg-primary text-primary-foreground shadow'
                      : 'text-muted-foreground hover:text-foreground hover:bg-muted/60'
                  }`}
                >
                  {item.label}
                </button>
              ))}
            </nav>
          </div>
        </div>
      </header>
      <main id="main-content" className="mx-auto flex max-w-6xl flex-1 flex-col gap-8 px-6 py-8">
        {children}
      </main>
      <Footer />
    </div>
  );
}

export type AppRoute = Route;
