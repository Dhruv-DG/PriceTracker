import React from 'react';
import type { ProductInfo } from '../types';

interface ProductHeaderProps {
  product: ProductInfo;
  isDemo: boolean;
  latencyMs: number | null;
}

export const ProductHeader: React.FC<ProductHeaderProps> = ({ product, latencyMs }) => {
  const tags = [
    product.brand,
    product.storage,
    product.ram,
    product.color,
    product.variant,
    product.category,
    product.condition !== 'new' ? product.condition : null,
  ].filter(Boolean);

  return (
    <div className="product-header">
      <div style={{ flex: 1 }}>
        <h2>{product.canonical_name}</h2>
        {tags.length > 0 && (
          <div className="product-tags" style={{ marginTop: 8 }}>
            {tags.map((tag, i) => (
              <span key={i} className="product-tag">{tag}</span>
            ))}
          </div>
        )}
        {latencyMs && (
          <div style={{ marginTop: 8, fontSize: '12px', color: 'var(--color-text-muted)' }}>
            Results in {(latencyMs / 1000).toFixed(1)}s
          </div>
        )}
      </div>
    </div>
  );
};
