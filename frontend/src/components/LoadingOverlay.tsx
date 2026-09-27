import React from 'react';

interface LoadingOverlayProps {
  currentStep: number;
}

const STEPS = [
  'Understanding your query',
  'Searching e-commerce platforms',
  'Extracting current prices',
  'Fetching historical data',
  'Computing analytics',
  'Building dashboard',
];

export const LoadingOverlay: React.FC<LoadingOverlayProps> = ({ currentStep }) => {
  return (
    <div className="loading-container">
      <div className="loading-spinner" />
      <div className="loading-steps">
        {STEPS.map((step, i) => {
          const status = i < currentStep ? 'done' : i === currentStep ? 'active' : '';
          return (
            <div key={step} className={`loading-step ${status}`}>
              <div className="step-dot" />
              <span>{step}</span>
              {i < currentStep && <span style={{ marginLeft: 'auto', fontSize: '12px' }}>✓</span>}
            </div>
          );
        })}
      </div>
    </div>
  );
};
