export function Sparkline({
  data,
  width = 220,
  height = 40,
}: {
  data: number[];
  width?: number;
  height?: number;
}) {
  if (data.length < 2) {
    return (
      <div className="flex h-10 items-center text-xs text-muted-foreground">
        A trend line will appear once you have a few days of history.
      </div>
    );
  }
  const pad = 2;
  const min = Math.min(...data, 0);
  const max = Math.max(...data, 100);
  const range = Math.max(1, max - min);
  const step = (width - pad * 2) / (data.length - 1);
  const points = data
    .map((v, i) => {
      const x = pad + i * step;
      const y = height - pad - ((v - min) / range) * (height - pad * 2);
      return `${x},${y}`;
    })
    .join(" ");
  const lastX = pad + (data.length - 1) * step;
  const lastY = height - pad - ((data[data.length - 1] - min) / range) * (height - pad * 2);
  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      className="text-foreground"
      aria-hidden="true"
    >
      <polyline
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        points={points}
      />
      <circle cx={lastX} cy={lastY} r="2.5" fill="currentColor" />
    </svg>
  );
}
