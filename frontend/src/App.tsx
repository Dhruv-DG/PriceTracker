import { useState, useCallback, useRef, useEffect } from 'react';
import { AlertTriangle, Zap } from 'lucide-react';
import { SearchBox } from './components/SearchBox';
import { LoadingOverlay } from './components/LoadingOverlay';
import { ProductHeader } from './components/ProductHeader';
import { HighlightCardsComponent } from './components/HighlightCards';
import { PriceTable } from './components/PriceTable';
import { PriceHistoryChart } from './components/PriceHistoryChart';
import { AveragePriceChart } from './components/AveragePriceChart';
import {
  PriceMovements, PriceStats, PricePositionIndicator,
  DataSources, CheapestInfo,
} from './components/DashboardSections';
import { api } from './services/api';
import type { SearchResponse } from './types';
import './index.css';

function App() {
  const [searchResult, setSearchResult] = useState<SearchResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const dashboardRef = useRef<HTMLDivElement>(null);

  const handleSearch = useCallback(async (query: string) => {
    setIsLoading(true);
    setError(null);
    setSearchResult(null);
    setLoadingStep(0);

    // Simulate progressive loading steps
    const stepTimers = [
      setTimeout(() => setLoadingStep(1), 300),
      setTimeout(() => setLoadingStep(2), 800),
      setTimeout(() => setLoadingStep(3), 1500),
      setTimeout(() => setLoadingStep(4), 2200),
      setTimeout(() => setLoadingStep(5), 2800),
    ];

    try {
      const result = await api.search(query);
      setSearchResult(result);
      setLoadingStep(6);

      // Scroll to dashboard
      setTimeout(() => {
        dashboardRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
    } catch (err: any) {
      setError(err.message || 'Search failed. Please check if the backend is running.');
    } finally {
      stepTimers.forEach(clearTimeout);
      setIsLoading(false);
    }
  }, []);

  const dashboard = searchResult?.dashboard;

  return (
    <div className="app-container">
      {/* Header */}
      <header className="page-header">
        <h1>⚡ Price Intelligence</h1>
        <p>Real-time e-commerce price comparison & historical analysis</p>
      </header>

      {/* Demo Banner */}
      {(searchResult?.is_demo || (!searchResult && true)) && (
        <div className="demo-banner">
          <AlertTriangle size={14} />
          <span>
            <strong>DEMO MODE</strong> — Showing realistic simulated data.
            Add API keys for live data.
          </span>
        </div>
      )}

      {/* Search */}
      <SearchBox onSearch={handleSearch} isLoading={isLoading} />

      {/* Loading */}
      {isLoading && <LoadingOverlay currentStep={loadingStep} />}

      {/* Error */}
      {error && (
        <div style={{
          background: 'var(--color-danger-bg)',
          border: '1px solid rgba(248, 113, 113, 0.2)',
          borderRadius: 'var(--radius-md)',
          padding: 'var(--space-lg)',
          textAlign: 'center',
          color: 'var(--color-danger)',
          marginBottom: 'var(--space-lg)',
        }}>
          <strong>Error:</strong> {error}
          <p style={{ color: 'var(--color-text-muted)', fontSize: '13px', marginTop: 8 }}>
            Make sure the backend is running: <code>cd backend && python -m uvicorn app.main:app --reload</code>
          </p>
        </div>
      )}

      {/* Dashboard */}
      {dashboard && searchResult?.product && (
        <div ref={dashboardRef}>
          {/* Product Header */}
          <ProductHeader
            product={searchResult.product}
            isDemo={searchResult.is_demo}
            latencyMs={searchResult.latency_ms}
          />

          {/* Highlight Cards */}
          <HighlightCardsComponent highlights={dashboard.highlights} />

          {/* Current Prices Table */}
          <PriceTable prices={dashboard.current_prices} />

          {/* Price History Chart */}
          <PriceHistoryChart platformHistories={dashboard.platform_histories} />

          {/* Average Price Over Time */}
          <AveragePriceChart data={dashboard.average_price_over_time} />

          {/* Price Movements */}
          <PriceMovements movements={dashboard.price_movements} />

          {/* Statistics & Volatility */}
          <PriceStats
            currentStats={dashboard.current_statistics}
            historicalStats={dashboard.historical_statistics}
            volatility={dashboard.volatility}
          />

          {/* Price Position Indicator */}
          <PricePositionIndicator position={dashboard.price_position} />

          {/* Where is it cheapest? */}
          <CheapestInfo
            cheapestCurrent={dashboard.cheapest_platform}
            cheapestHistorical={dashboard.cheapest_historical_platform}
            mostConsistent={dashboard.most_consistent_platform}
            mostConsistentMetric={dashboard.most_consistent_metric}
          />

          {/* Data Sources */}
          <DataSources sources={dashboard.data_sources} />

          {/* Track Button */}
          <div className="track-section">
            <button className="track-btn" onClick={() => alert('Tracking will be enabled in the next update!')}>
              <Zap size={18} />
              Track This Product
            </button>
          </div>

          {/* Warnings */}
          {searchResult.warnings.length > 0 && (
            <div style={{ marginTop: 'var(--space-md)', fontSize: '13px', color: 'var(--color-text-muted)' }}>
              {searchResult.warnings.map((w, i) => (
                <div key={i}>⚠ {w}</div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !searchResult && !error && (
        <div style={{
          textAlign: 'center',
          padding: 'var(--space-3xl)',
          color: 'var(--color-text-muted)',
        }}>
          <div style={{ fontSize: '48px', marginBottom: 'var(--space-md)' }}>🔍</div>
          <p style={{ fontSize: 'var(--font-size-lg)' }}>
            Search for any product to see price intelligence
          </p>
          <p style={{ fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-sm)' }}>
            Try "iPhone 17 256GB" or "Sony WH-1000XM6"
          </p>
        </div>
      )}

      {/* Footer */}
      <footer style={{
        textAlign: 'center',
        padding: 'var(--space-2xl)',
        color: 'var(--color-text-muted)',
        fontSize: 'var(--font-size-xs)',
        borderTop: '1px solid var(--color-border)',
        marginTop: 'var(--space-2xl)',
      }}>
        Price Intelligence Dashboard — Built with FastAPI + React + Recharts
      </footer>
    </div>
  );
}

export default App;
