import { ReactNode } from 'react';

import { Footer } from '@/components/layout/Footer';

const NAV_ITEMS = [
  { id: 'control', label: 'Control Room' },
  { id: 'benchmarks', label: 'Benchmarks' },
  { id: 'runs', label: 'Runs' },
  { id: 'documents', label: 'Doc Extraction' },
  { id: 'latte', label: 'Latte Lab' },
] as const;

type Route = typeof NAV_ITEMS[number]['id'];

type AppShellProps = {
  route: Route;
  onNavigate: (route: Route) => void;
  children: ReactNode;
};

export default function AppShell({ route, onNavigate, children }: AppShellProps) {
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
      </header>
      <main id="main-content" className="mx-auto flex max-w-6xl flex-1 flex-col gap-8 px-6 py-8">
        {children}
      </main>
      <Footer />
    </div>
  );
}

export type AppRoute = Route;
