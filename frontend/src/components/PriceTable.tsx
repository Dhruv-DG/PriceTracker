import React from 'react';
import { ShoppingCart, ExternalLink } from 'lucide-react';
import type { PriceData } from '../types';
import { getPlatformColor } from '../utils/theme';
import { formatPrice, formatPct, formatTimeAgo } from '../utils/format';

interface PriceTableProps {
  prices: PriceData[];
}

export const PriceTable: React.FC<PriceTableProps> = ({ prices }) => {
  if (!prices.length) return null;

  const lowestPrice = Math.min(...prices.map(p => p.effective_price));

  return (
    <div className="dashboard-section">
      <div className="section-header">
        <h3 className="section-title">
          <ShoppingCart size={20} />
          Current Prices by Platform
        </h3>
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table className="price-table">
          <thead>
            <tr>
              <th>Platform</th>
              <th>Price</th>
              <th>MRP</th>
              <th>Discount</th>
              <th>Shipping</th>
              <th>Effective Price</th>
              <th>Seller</th>
              <th>Availability</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {prices.map((price, index) => {
              const isLowest = price.effective_price === lowestPrice;
              return (
                <tr key={`${price.platform.domain}-${index}`}>
                  <td>
                    <div className="platform-cell">
                      <span
                        className="platform-dot"
                        style={{ background: getPlatformColor(price.platform.name, index) }}
                      />
                      <span>{price.platform.name}</span>
                    </div>
                  </td>
                  <td>
                    <span className={`price-value ${isLowest ? 'price-lowest' : ''}`}>
                      {formatPrice(price.price)}
                    </span>
                  </td>
                  <td>
                    {price.mrp && price.mrp > price.price ? (
                      <span className="mrp-value">{formatPrice(price.mrp)}</span>
                    ) : (
                      <span style={{ color: 'var(--color-text-muted)' }}>—</span>
                    )}
                  </td>
                  <td>
                    {price.discount_pct ? (
                      <span className="discount-badge">{price.discount_pct}% off</span>
                    ) : (
                      <span style={{ color: 'var(--color-text-muted)' }}>—</span>
                    )}
                  </td>
                  <td style={{ color: 'var(--color-text-secondary)' }}>
                    {price.shipping_note}
                  </td>
                  <td>
                    <span className={`price-value ${isLowest ? 'price-lowest' : ''}`}>
                      {formatPrice(price.effective_price)}
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
                  </td>
                  <td style={{ color: 'var(--color-text-secondary)', fontSize: '13px' }}>
                    {price.seller || '—'}
                  </td>
                  <td>
                    <span style={{
                      color: price.availability === 'in_stock' || price.availability === 'available'
                        ? 'var(--color-success)'
                        : 'var(--color-warning)',
                      fontSize: '12px',
                      fontWeight: 600,
                    }}>
                      {price.availability === 'in_stock' || price.availability === 'available' ? 'In Stock' : price.availability}
                    </span>
                  </td>
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
                      }}
                    >
                      Visit <ExternalLink size={12} />
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
