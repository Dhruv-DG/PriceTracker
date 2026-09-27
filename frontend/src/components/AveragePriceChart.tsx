import React, { useMemo } from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { BarChart3 } from 'lucide-react';
import type { AveragePricePoint } from '../types';
import { formatPrice, formatShortDate } from '../utils/format';

interface AveragePriceChartProps {
  data: AveragePricePoint[];
}

const CustomTooltip: React.FC<any> = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  const point = payload[0]?.payload;
  return (
    <div className="custom-tooltip">
      <div className="label">{label}</div>
      <div className="tooltip-item">
        <span style={{ color: 'var(--color-text-secondary)' }}>Average:</span>
        <span style={{ color: '#60a5fa', fontWeight: 600 }}>{formatPrice(point?.average_price)}</span>
      </div>
      <div className="tooltip-item">
        <span style={{ color: 'var(--color-text-secondary)' }}>Min:</span>
        <span style={{ color: 'var(--color-success)', fontWeight: 600 }}>{formatPrice(point?.min_price)}</span>
      </div>
      <div className="tooltip-item">
        <span style={{ color: 'var(--color-text-secondary)' }}>Max:</span>
        <span style={{ color: 'var(--color-danger)', fontWeight: 600 }}>{formatPrice(point?.max_price)}</span>
      </div>
      <div className="tooltip-item" style={{ marginTop: 4, fontSize: 11, color: 'var(--color-text-muted)' }}>
        {point?.platforms_count} platform(s) contributing
      </div>
    </div>
  );
};

export const AveragePriceChart: React.FC<AveragePriceChartProps> = ({ data }) => {
  const chartData = useMemo(() => {
    return data.map(point => ({
      ...point,
      date: formatShortDate(point.date),
    }));
  }, [data]);

  if (!chartData.length) {
    return null;
  }

  return (
    <div className="dashboard-section">
      <div className="section-header">
        <h3 className="section-title">
          <BarChart3 size={20} />
          Average Price Over Time
        </h3>
      </div>

      <div className="chart-container">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <defs>
              <linearGradient id="avgGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#60a5fa" stopOpacity={0.3} />
                <stop offset="100%" stopColor="#60a5fa" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="rangeGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#6366f1" stopOpacity={0.1} />
                <stop offset="100%" stopColor="#6366f1" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
            <XAxis
              dataKey="date"
              tick={{ fill: '#6b7280', fontSize: 11 }}
              tickLine={false}
              axisLine={{ stroke: 'rgba(255,255,255,0.06)' }}
              interval="preserveStartEnd"
            />
            <YAxis
              tick={{ fill: '#6b7280', fontSize: 11 }}
              tickLine={false}
              axisLine={{ stroke: 'rgba(255,255,255,0.06)' }}
              tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}K`}
              domain={['auto', 'auto']}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="max_price"
              stroke="transparent"
              fill="url(#rangeGradient)"
            />
            <Area
              type="monotone"
              dataKey="average_price"
              stroke="#60a5fa"
              strokeWidth={2}
              fill="url(#avgGradient)"
              dot={false}
              activeDot={{ r: 4 }}
            />
            <Area
              type="monotone"
              dataKey="min_price"
              stroke="#10b981"
              strokeWidth={1}
              strokeDasharray="4 4"
              fill="transparent"
              dot={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
