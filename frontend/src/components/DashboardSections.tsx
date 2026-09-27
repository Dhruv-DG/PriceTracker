import React from 'react';
import {
  Activity, TrendingDown, TrendingUp, ArrowRight, BarChart2,
  Database, Crosshair, Bell, Info
} from 'lucide-react';
import type {
  PriceMovement, PriceStatistics, VolatilityInfo,
  PricePosition as PricePositionType, DataSourceInfo
} from '../types';
import { formatPrice, formatPct, getDirectionArrow, getDirectionColor } from '../utils/format';

// ─── Price Movements ─────────────────────────────────────

interface PriceMovementsProps {
  movements: PriceMovement[];
}

export const PriceMovements: React.FC<PriceMovementsProps> = ({ movements }) => (
  <div className="dashboard-section">
    <div className="section-header">
      <h3 className="section-title">
        <Activity size={20} />
        Recent Price Movement
      </h3>
    </div>
    <div className="movements-grid">
      {movements.map((m) => (
        <div key={m.period} className="movement-chip">
          <div className="period">{m.period}</div>
          <div className="change" style={{ color: getDirectionColor(m.direction) }}>
            {m.change_pct != null ? (
              <>{getDirectionArrow(m.direction)} {Math.abs(m.change_pct)}%</>
            ) : (
              <span style={{ color: 'var(--color-text-muted)' }}>—</span>
            )}
          </div>
          {m.change_amount != null && (
            <div style={{ fontSize: '12px', color: 'var(--color-text-muted)', marginTop: 4 }}>
              {formatPrice(Math.abs(m.change_amount))}
            </div>
          )}
        </div>
      ))}
    </div>
  </div>
);

// ─── Statistics ──────────────────────────────────────────

interface StatsProps {
  currentStats: PriceStatistics;
  historicalStats: PriceStatistics;
  volatility: VolatilityInfo;
}

export const PriceStats: React.FC<StatsProps> = ({ currentStats, historicalStats, volatility }) => (
  <div className="dashboard-section">
    <div className="section-header">
      <h3 className="section-title">
        <BarChart2 size={20} />
        Price Statistics
      </h3>
    </div>
    <div className="stats-grid">
      <div className="stat-item">
        <div className="stat-label">Mean</div>
        <div className="stat-value">{formatPrice(historicalStats.mean || currentStats.mean)}</div>
      </div>
      <div className="stat-item">
        <div className="stat-label">Median</div>
        <div className="stat-value">{formatPrice(historicalStats.median || currentStats.median)}</div>
      </div>
      <div className="stat-item">
        <div className="stat-label">Min</div>
        <div className="stat-value" style={{ color: 'var(--color-success)' }}>
          {formatPrice(historicalStats.min || currentStats.min)}
        </div>
      </div>
      <div className="stat-item">
        <div className="stat-label">Max</div>
        <div className="stat-value" style={{ color: 'var(--color-danger)' }}>
          {formatPrice(historicalStats.max || currentStats.max)}
        </div>
      </div>
      <div className="stat-item">
        <div className="stat-label">Volatility</div>
        <div className="stat-value" style={{
          color: volatility.level === 'Low' ? 'var(--color-success)' :
                 volatility.level === 'Medium' ? 'var(--color-warning)' : 'var(--color-danger)'
        }}>
          {volatility.level}
        </div>
      </div>
      <div className="stat-item">
        <div className="stat-label">Largest Drop</div>
        <div className="stat-value" style={{ color: 'var(--color-success)' }}>
          {volatility.largest_drop_pct != null ? `${volatility.largest_drop_pct}%` : '—'}
        </div>
      </div>
      <div className="stat-item">
        <div className="stat-label">Largest Rise</div>
        <div className="stat-value" style={{ color: 'var(--color-danger)' }}>
          {volatility.largest_increase_pct != null ? `+${volatility.largest_increase_pct}%` : '—'}
        </div>
      </div>
      <div className="stat-item">
        <div className="stat-label">Observations</div>
        <div className="stat-value">{historicalStats.observations_count || 0}</div>
      </div>
    </div>
  </div>
);

// ─── Price Position ─────────────────────────────────────

interface PricePositionProps {
  position: PricePositionType | null;
}

export const PricePositionIndicator: React.FC<PricePositionProps> = ({ position }) => {
  if (!position) return null;

  return (
    <div className="dashboard-section">
      <div className="section-header">
        <h3 className="section-title">
          <Crosshair size={20} />
          Historical Price Position
        </h3>
      </div>
      <div className="position-indicator">
        <div className="position-bar">
          <div
            className="position-marker"
            style={{ left: `${Math.max(5, Math.min(95, position.position_pct))}%` }}
          />
        </div>
        <div className="position-labels">
          <span>Low: {formatPrice(position.historical_low)}</span>
          <span>Avg: {formatPrice(position.historical_avg)}</span>
          <span>High: {formatPrice(position.historical_high)}</span>
        </div>
        <div className="position-current">
          Current price <strong>{formatPrice(position.current_price)}</strong> is{' '}
          <span style={{
            color: position.vs_low_pct <= 10 ? 'var(--color-success)' : 'var(--color-warning)',
            fontWeight: 600,
          }}>
            {formatPct(position.vs_low_pct)} above historical low
          </span>
        </div>
      </div>
    </div>
  );
};

// ─── Data Sources ───────────────────────────────────────

interface DataSourcesProps {
  sources: DataSourceInfo[];
}

export const DataSources: React.FC<DataSourcesProps> = ({ sources }) => {
  if (!sources.length) return null;

  return (
    <div className="dashboard-section">
      <div className="section-header">
        <h3 className="section-title">
          <Database size={20} />
          Data Sources &amp; Provenance
        </h3>
      </div>
      <div className="data-source-list">
        {sources.map((source, idx) => (
          <div key={idx} className="data-source-item">
            <div>
              <span className="source-platform">{source.platform}</span>
              <span style={{ margin: '0 8px', color: 'var(--color-text-muted)' }}>→</span>
              <span className="source-provider">{source.provider}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <span className="source-coverage">{source.coverage}</span>
              {source.observation_count > 0 && (
                <span style={{ color: 'var(--color-text-muted)', fontSize: '12px' }}>
                  {source.observation_count} obs.
                </span>
              )}
              <span className={`confidence-badge confidence-${source.confidence}`}>
                {source.confidence}
              </span>
              {source.is_demo && (
                <span style={{
                  fontSize: '10px',
                  padding: '1px 6px',
                  borderRadius: '9999px',
                  background: 'var(--color-warning-bg)',
                  color: 'var(--color-warning)',
                  fontWeight: 600,
                }}>
                  DEMO
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// ─── Where is it Cheapest? ──────────────────────────────

interface CheapestInfoProps {
  cheapestCurrent: string | null;
  cheapestHistorical: string | null;
  mostConsistent: string | null;
  mostConsistentMetric: string | null;
}

export const CheapestInfo: React.FC<CheapestInfoProps> = ({
  cheapestCurrent, cheapestHistorical, mostConsistent, mostConsistentMetric,
}) => (
  <div className="dashboard-section">
    <div className="section-header">
      <h3 className="section-title">
        <Info size={20} />
        Where is it Cheapest?
      </h3>
    </div>
    <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
      <div className="stat-item">
        <div className="stat-label">Currently Cheapest</div>
        <div className="stat-value" style={{ fontSize: '16px', color: 'var(--color-success)' }}>
          {cheapestCurrent || '—'}
        </div>
      </div>
      <div className="stat-item">
        <div className="stat-label">Historically Cheapest</div>
        <div className="stat-value" style={{ fontSize: '16px' }}>
          {cheapestHistorical || '—'}
        </div>
      </div>
      <div className="stat-item">
        <div className="stat-label">Most Consistent</div>
        <div className="stat-value" style={{ fontSize: '16px' }}>
          {mostConsistent || '—'}
        </div>
        {mostConsistentMetric && (
          <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', marginTop: 4 }}>
            ({mostConsistentMetric})
          </div>
        )}
      </div>
    </div>
  </div>
);
