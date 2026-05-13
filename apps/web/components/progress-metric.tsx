type Accent = "default" | "success";

export function ProgressMetric({
  label,
  value,
  target,
  unit,
  accent = "default",
  trailing,
}: {
  label: string;
  value: number;
  target: number;
  unit?: string;
  accent?: Accent;
  trailing?: React.ReactNode;
}) {
  const safeTarget = Math.max(1, target);
  const pct = Math.min(100, (value / safeTarget) * 100);
  const barColor = accent === "success" ? "bg-green-500" : "bg-foreground/85";
  const trackColor = accent === "success" ? "bg-green-100" : "bg-muted";

  return (
    <div>
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          {label}
        </span>
        <span className="flex items-center gap-2 text-sm tabular-nums">
          <span>
            <span className="font-semibold text-foreground">{value}</span>
            <span className="text-muted-foreground"> of {target}</span>
            {unit && <span className="text-muted-foreground"> {unit}</span>}
          </span>
          {trailing}
        </span>
      </div>
      <div className={`mt-1.5 h-2.5 w-full overflow-hidden rounded-full ${trackColor}`}>
        <div
          className={`h-full rounded-full transition-all duration-500 ${barColor}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
