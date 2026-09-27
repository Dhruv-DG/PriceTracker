import React, { useState, useMemo } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend,
} from 'recharts';
import { TrendingUp } from 'lucide-react';
import type { PlatformHistory } from '../types';
import { getPlatformColor } from '../utils/theme';
import { formatPrice, formatShortDate } from '../utils/format';

interface PriceHistoryChartProps {
  platformHistories: PlatformHistory[];
}

const PERIODS = [
  { label: '7D', days: 7 },
  { label: '30D', days: 30 },
  { label: '90D', days: 90 },
  { label: '6M', days: 180 },
  { label: '1Y', days: 365 },
  { label: 'ALL', days: 9999 },
];

interface ChartTooltipProps {
  active?: boolean;
  payload?: any[];
  label?: string;
}

const CustomTooltip: React.FC<ChartTooltipProps> = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="custom-tooltip">
      <div className="label">{label}</div>
      {payload.map((entry: any, i: number) => (
        <div key={i} className="tooltip-item">
          <span
            style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              background: entry.color,
              display: 'inline-block',
            }}
          />
          <span style={{ color: 'var(--color-text-secondary)' }}>{entry.name}:</span>
          <span style={{ color: 'var(--color-text-primary)', fontWeight: 600 }}>
            {formatPrice(entry.value)}
          </span>
        </div>
      ))}
    </div>
  );
};

export const PriceHistoryChart: React.FC<PriceHistoryChartProps> = ({ platformHistories }) => {
  const [selectedPeriod, setSelectedPeriod] = useState(2); // 90D default

  const chartData = useMemo(() => {
    const days = PERIODS[selectedPeriod].days;
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - days);

    // Merge all platform observations into unified timeline
    const dateMap = new Map<string, Record<string, number>>();

    platformHistories.forEach((ph) => {
      ph.history.observations.forEach((obs) => {
        const date = new Date(obs.date);
        if (date >= cutoff) {
          const dateStr = date.toISOString().split('T')[0];
          if (!dateMap.has(dateStr)) {
            dateMap.set(dateStr, {});
          }
          dateMap.get(dateStr)![ph.platform.name] = obs.price;
        }
      });
    });

    // Convert to array sorted by date
    return Array.from(dateMap.entries())
      .map(([date, prices]) => ({
        date: formatShortDate(date),
        rawDate: date,
        ...prices,
      }))
      .sort((a, b) => a.rawDate.localeCompare(b.rawDate));
  }, [platformHistories, selectedPeriod]);

  if (!platformHistories.length || !chartData.length) {
    return (
      <div className="dashboard-section">
        <div className="section-header">
          <h3 className="section-title">
            <TrendingUp size={20} />
            Price History
          </h3>
        </div>
        <p style={{ color: 'var(--color-text-muted)', textAlign: 'center', padding: '40px' }}>
          No historical data available yet
        </p>
      </div>
    );
  }

  const platformNames = platformHistories.map(ph => ph.platform.name);

  return (
    <div className="dashboard-section">
      <div className="section-header">
        <h3 className="section-title">
          <TrendingUp size={20} />
          Price History
        </h3>
        <div className="chart-controls">
          {PERIODS.map((period, idx) => (
            <button
              key={period.label}
              className={`chart-period-btn ${idx === selectedPeriod ? 'active' : ''}`}
              onClick={() => setSelectedPeriod(idx)}
            >
              {period.label}
            </button>
          ))}
        </div>
      </div>

      <div className="chart-container">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
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
            <Legend
              wrapperStyle={{ paddingTop: 20, fontSize: 12 }}
            />
            {platformNames.map((name, idx) => (
              <Line
                key={name}
                type="monotone"
                dataKey={name}
                stroke={getPlatformColor(name, idx)}
                strokeWidth={2}
                dot={false}
                connectNulls
                activeDot={{ r: 4, strokeWidth: 2 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
