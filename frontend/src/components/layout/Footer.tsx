export function Footer() {
  return (
    <footer className="mt-10 border-t border-border/60 bg-brand-primary text-brand-bg">
      <div className="mx-auto flex max-w-6xl flex-col gap-4 px-6 py-8 text-sm">
        <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-base font-semibold">Built for teams shipping trustworthy agents.</p>
            <p className="mt-1 text-sm text-brand-bg/70">
              OmniBAR • Reliability Control Room · Structured Agents · AgentOS Alignment
            </p>
          </div>
          <div className="flex gap-6 text-xs uppercase tracking-wide text-brand-bg/70">
            <a href="#" className="hover:text-brand-bg">
              Privacy
            </a>
            <a href="#" className="hover:text-brand-bg">
              Terms
            </a>
            <a href="#" className="hover:text-brand-bg">
              Status
            </a>
          </div>
        </div>
        <p className="text-xs text-brand-bg/60">
          © {new Date().getFullYear()} BrainGnosis &amp; Ashley Broussard. All rights reserved.
        </p>
      </div>
    </footer>
  );
}
