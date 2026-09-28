import React from 'react';
import { ShoppingCart, ExternalLink, CheckCircle, AlertCircle, Clock } from 'lucide-react';
import type { PriceData } from '../types';
import { getPlatformColor } from '../utils/theme';
import { formatPrice } from '../utils/format';

interface PriceTableProps {
  prices: PriceData[];
}

export const PriceTable: React.FC<PriceTableProps> = ({ prices }) => {
  if (!prices.length) return null;

  // Compute verified coverage (§39)
  const verifiedCount = prices.filter(p => p.verification_status === 'VERIFIED').length;
  const totalCount = prices.length;

  // Cheapest verified price for highlighting
  const verifiedPrices = prices.filter(
    p => p.verification_status === 'VERIFIED' && p.effective_price && p.effective_price > 0
  );
  const lowestVerifiedPrice = verifiedPrices.length > 0
    ? Math.min(...verifiedPrices.map(p => p.effective_price!))
    : null;

  // Get display price — prefer verified, fall back to search_price
  const getDisplayPrice = (p: PriceData): number | null => {
    if (p.verification_status === 'VERIFIED' && p.verified_price && p.verified_price > 0) {
      return p.verified_price;
    }
    if (p.effective_price && p.effective_price > 0) {
      return p.effective_price;
    }
    if (p.search_price && p.search_price > 0) {
      return p.search_price;
    }
    return null;
  };

  return (
    <div className="dashboard-section">
      <div className="section-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 className="section-title">
          <ShoppingCart size={20} />
          Market Prices
        </h3>
        {/* Verified coverage indicator (§39) */}
        <div style={{
          fontSize: '12px',
          color: 'var(--color-text-muted)',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
        }}>
          <CheckCircle size={14} style={{ color: 'var(--color-success)' }} />
          {verifiedCount} / {totalCount} verified
        </div>
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table className="price-table">
          <thead>
            <tr>
              <th>Platform</th>
              <th>Product / Listing</th>
              <th>Price</th>
              <th>Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {prices.map((price, index) => {
              const displayPrice = getDisplayPrice(price);
              const isLowest = displayPrice !== null && displayPrice === lowestVerifiedPrice && price.verification_status === 'VERIFIED';

              return (
                <tr key={`${price.url}-${index}`}>
                  {/* Platform */}
                  <td>
                    <div className="platform-cell">
                      <span
                        className="platform-dot"
                        style={{ background: getPlatformColor(price.platform.name, index) }}
                      />
                      <span>{price.platform.name}</span>
                    </div>
                  </td>

                  {/* Product / Listing */}
                  <td>
                    <div style={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {price.title || '—'}
                    </div>
                  </td>

                  {/* Price */}
                  <td>
                    {displayPrice !== null ? (
                      <div>
                        <span className={`price-value ${isLowest ? 'price-lowest' : ''}`}>
                          {formatPrice(displayPrice)}
                        </span>
                        {isLowest && (
                          <span style={{
                            marginLeft: 6,
                            fontSize: '10px',
                            padding: '1px 6px',
                            borderRadius: '9999px',
                            background: 'var(--color-success-bg)',
                            color: 'var(--color-success)',
                            fontWeight: 600,
                          }}>
                            LOWEST
                          </span>
                        )}
                        {/* Show "discovered" label for unverified search prices */}
                        {price.verification_status !== 'VERIFIED' && price.search_price && price.search_price > 0 && (
                          <div style={{ fontSize: '10px', color: 'var(--color-text-muted)', marginTop: 2 }}>
                            Discovered price
                          </div>
                        )}
                      </div>
                    ) : (
                      <span style={{ color: 'var(--color-text-muted)', fontStyle: 'italic' }}>
                        Price unavailable
                      </span>
                    )}
                  </td>

                  {/* Status */}
                  <td>
                    {price.verification_status === 'PENDING' && (
                      <span style={{
                        display: 'inline-flex', alignItems: 'center', gap: 4,
                        fontSize: '11px', padding: '2px 8px',
                        background: 'var(--color-warning-bg)', color: 'var(--color-warning)',
                        borderRadius: '4px', fontWeight: 600,
                      }}>
                        <Clock size={12} />
                        Verifying
                      </span>
                    )}
                    {price.verification_status === 'VERIFIED' && (
                      <span style={{
                        display: 'inline-flex', alignItems: 'center', gap: 4,
                        fontSize: '11px', padding: '2px 8px',
                        background: 'var(--color-success-bg)', color: 'var(--color-success)',
                        borderRadius: '4px', fontWeight: 600,
                      }}>
                        <CheckCircle size={12} />
                        Verified
                      </span>
                    )}
                    {price.verification_status === 'FAILED' && (
                      <span style={{
                        display: 'inline-flex', alignItems: 'center', gap: 4,
                        fontSize: '11px', padding: '2px 8px',
                        background: 'var(--color-danger-bg)', color: 'var(--color-danger)',
                        borderRadius: '4px', fontWeight: 600,
                      }}>
                        <AlertCircle size={12} />
                        Unverified
                      </span>
                    )}
                  </td>

                  {/* Link — ALWAYS available regardless of verification (§22) */}
                  <td>
                    <a
                      href={price.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 4,
                        fontSize: '12px',
                        color: 'var(--color-accent-light)',
                        textDecoration: 'none',
                      }}
                    >
                      View <ExternalLink size={12} />
                    </a>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
