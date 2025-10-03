import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

const navLinks = [
  { label: 'Control Room', href: '#' },
  { label: 'Benchmarks', href: '#' },
  { label: 'Teams', href: '#' },
  { label: 'Jobs', href: '#' }
];

export function NavBar() {
  return (
    <header className="sticky top-0 z-40 border-b border-border/60 bg-[hsl(var(--background))]/95 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-6 px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-primary text-white font-semibold">
            OB
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-semibold text-brand-primary">OmniBAR</span>
            <span className="text-xs text-brand-slate">Agent Reliability Studio</span>
          </div>
        </div>
        <nav className="hidden items-center gap-6 text-sm font-medium text-brand-slate md:flex">
          {navLinks.map((link) => (
            <a key={link.label} href={link.href} className={cn('hover:text-brand-primary transition-colors')}>
              {link.label}
            </a>
          ))}
        </nav>
        <div className="hidden items-center gap-3 md:flex">
          <Button variant="text">Docs</Button>
          <Button variant="secondary">Request Demo</Button>
        </div>
      </div>
    </header>
  );
}
