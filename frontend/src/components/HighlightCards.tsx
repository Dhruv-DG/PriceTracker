import React from 'react';
import { TrendingDown, TrendingUp, BarChart3, DollarSign, Activity, Target } from 'lucide-react';
import type { HighlightCards as HighlightCardsType } from '../types';
import { formatPrice, formatPct } from '../utils/format';

interface HighlightCardsProps {
  highlights: HighlightCardsType;
}

export const HighlightCardsComponent: React.FC<HighlightCardsProps> = ({ highlights }) => {
  const cards = [
    {
      label: 'Current Lowest',
      value: formatPrice(highlights.current_lowest?.effective_price),
      sub: highlights.current_lowest?.platform.name,
      accent: true,
      icon: <TrendingDown size={16} />,
    },
    {
      label: 'Current Average',
      value: formatPrice(highlights.current_average),
      sub: null,
      icon: <BarChart3 size={16} />,
    },
    {
      label: 'Current Highest',
      value: formatPrice(highlights.current_highest?.effective_price),
      sub: highlights.current_highest?.platform.name,
      icon: <TrendingUp size={16} />,
    },
    {
      label: 'Historical Low',
      value: formatPrice(highlights.historical_low),
      sub: highlights.historical_low_platform || null,
      icon: <Target size={16} />,
    },
    {
      label: 'Historical Average',
      value: formatPrice(highlights.historical_avg),
      sub: null,
      icon: <DollarSign size={16} />,
    },
    {
      label: 'Historical High',
      value: formatPrice(highlights.historical_high),
      sub: highlights.historical_high_platform || null,
      icon: <Activity size={16} />,
    },
  ];

  return (
    <div className="highlights-grid">
      {cards.map((card) => (
        <div key={card.label} className={`highlight-card ${card.accent ? 'accent' : ''}`}>
          <div className="label" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            {card.icon}
            {card.label}
          </div>
          <div className="value">{card.value}</div>
          {card.sub && <div className="sub">{card.sub}</div>}
        </div>
      ))}

      {/* VS Historical Average */}
      {highlights.current_vs_hist_avg_pct != null && (
        <div className="highlight-card">
          <div className="label">vs Historical Avg</div>
          <div className={`value ${highlights.current_vs_hist_avg_pct < 0 ? 'change-positive' : 'change-negative'}`}>
            {formatPct(highlights.current_vs_hist_avg_pct)}
          </div>
          <div className="sub">
            {highlights.current_vs_hist_avg_pct < 0 ? 'Below average' : 'Above average'}
          </div>
        </div>
      )}

      {/* VS Historical Low */}
      {highlights.current_vs_hist_low_pct != null && (
        <div className="highlight-card">
          <div className="label">vs Historical Low</div>
          <div className={`value ${highlights.current_vs_hist_low_pct <= 5 ? 'change-positive' : 'change-negative'}`}>
            {formatPct(highlights.current_vs_hist_low_pct)}
          </div>
          <div className="sub">
            {highlights.current_vs_hist_low_pct <= 5 ? 'Near historical low!' : 'Above historical low'}
          </div>
        </div>
      )}
    </div>
  );
};
