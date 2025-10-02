export type OverallBadgeProps = {
  value: number;
};

export function OverallBadge({ value }: OverallBadgeProps) {
  const percent = Math.round(value * 100);
  return (
    <div className="flex h-full min-w-[120px] flex-col items-center justify-center rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-emerald-800 shadow-sm">
      <span className="text-xs font-semibold uppercase tracking-wide">Overall</span>
      <span className="text-3xl font-bold">{percent}%</span>
    </div>
  );
}
