'use client';

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

interface StockChartProps {
  data: { date: string; close: number }[];
}

export const StockChart: React.FC<StockChartProps> = ({ data }) => {
  const validData = (data || []).filter(
    (item) => item.close !== null && item.close !== undefined && typeof item.close === 'number' && !!item.date
  );

  if (validData.length === 0) {
    return (
      <div className="h-[300px] rounded-xl border border-white/10 bg-[rgb(var(--charcoal))] flex items-center justify-center text-sm text-[rgb(var(--blue-gray))]">
        No chart data available.
      </div>
    );
  }

  const formatXAxis = (tickItem: string) => {
    const date = new Date(tickItem);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const formatYAxis = (value: number) => {
    return `$${value.toFixed(2)}`;
  };

  const first = validData[0];
  const last = validData[validData.length - 1];
  const isUp = last.close >= first.close;
  const stroke = isUp ? 'rgb(var(--sage))' : 'rgb(var(--soft-red))';
  const fillId = isUp ? 'chartFillUp' : 'chartFillDown';

  const pctChange = first.close > 0 ? ((last.close - first.close) / first.close) * 100 : 0;

  const formatLabel = (label: string) => {
    const date = new Date(label);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload || payload.length === 0) return null;
    const p = payload[0]?.value;
    const price = typeof p === 'number' ? p : 0;
    const base = first.close;
    const localPct = base > 0 ? ((price - base) / base) * 100 : 0;
    const arrow = localPct >= 0 ? '▲' : '▼';
    const pctColor = localPct >= 0 ? 'text-[rgb(var(--sage))]' : 'text-[rgb(var(--soft-red))]';

    return (
      <div className="rounded-xl border border-white/10 bg-[rgb(var(--charcoal))] px-3 py-2 shadow-sm">
        <div className="text-xs text-[rgb(var(--blue-gray))]">{formatLabel(label)}</div>
        <div className="mt-1 flex items-baseline gap-2">
          <div className="text-sm font-semibold text-white">${price.toFixed(2)}</div>
          <div className={`text-xs font-medium ${pctColor}`}>{arrow} {Math.abs(localPct).toFixed(2)}%</div>
        </div>
      </div>
    );
  };

  return (
    <div className="w-full fade-in" style={{ height: '300px' }}>
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className={`text-xs font-semibold ${isUp ? 'text-[rgb(var(--sage))]' : 'text-[rgb(var(--soft-red))]'}`}>
            {isUp ? '▲' : '▼'} {Math.abs(pctChange).toFixed(2)}%
          </div>
          <div className="text-xs text-[rgb(var(--blue-gray))]">(1M)</div>
        </div>
        <div className="text-xs text-[rgb(var(--blue-gray))]">
          {formatXAxis(first.date)} → {formatXAxis(last.date)}
        </div>
      </div>

      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={validData}
          margin={{ top: 10, right: 16, left: 6, bottom: 6 }}
        >
          <defs>
            <linearGradient id="chartFillUp" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="rgb(var(--sage))" stopOpacity={0.24} />
              <stop offset="100%" stopColor="rgb(var(--sage))" stopOpacity={0.03} />
            </linearGradient>
            <linearGradient id="chartFillDown" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="rgb(var(--soft-red))" stopOpacity={0.20} />
              <stop offset="100%" stopColor="rgb(var(--soft-red))" stopOpacity={0.03} />
            </linearGradient>
          </defs>

          <CartesianGrid strokeDasharray="3 3" stroke="rgba(var(--blue-gray), 0.18)" />
          <XAxis 
            dataKey="date" 
            tickFormatter={formatXAxis}
            tick={{ fontSize: 12 }}
            stroke="rgba(var(--blue-gray), 0.8)"
          />
          <YAxis 
            tickFormatter={formatYAxis}
            tick={{ fontSize: 12 }}
            stroke="rgba(var(--blue-gray), 0.8)"
            domain={['dataMin - 1', 'dataMax + 1']}
          />
          <Tooltip content={<CustomTooltip />} />
          <Area
            type="monotone"
            dataKey="close"
            stroke={stroke}
            strokeWidth={2}
            fill={`url(#${fillId})`}
            fillOpacity={1}
            dot={(props: any) => {
              const { cx, cy, index } = props;
              if (cx == null || cy == null) return null;
              const isEdge = index === 0 || index === validData.length - 1;
              if (!isEdge) return null;
              return (
                <circle
                  cx={cx}
                  cy={cy}
                  r={4}
                  fill={stroke}
                  stroke="#ffffff"
                  strokeWidth={2}
                />
              );
            }}
            activeDot={{ r: 5, fill: stroke, stroke: '#ffffff', strokeWidth: 2 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};
