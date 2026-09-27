import React, { useState, useCallback } from 'react';
import { Search, Zap } from 'lucide-react';

interface SearchBoxProps {
  onSearch: (query: string) => void;
  isLoading: boolean;
}

const SUGGESTIONS = [
  'iPhone 17 256GB Black',
  'Sony WH-1000XM6',
  'Samsung Galaxy S26 Ultra',
  'MacBook Air M4 16GB',
  'OnePlus 14 Pro',
  'AirPods Pro 3',
];

export const SearchBox: React.FC<SearchBoxProps> = ({ onSearch, isLoading }) => {
  const [query, setQuery] = useState('');

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSearch(query.trim());
    }
  }, [query, isLoading, onSearch]);

  const handleSuggestion = useCallback((suggestion: string) => {
    setQuery(suggestion);
    onSearch(suggestion);
  }, [onSearch]);

  return (
    <div className="search-container">
      <form onSubmit={handleSubmit} className="search-box">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search any product — e.g., iPhone 17 256GB Black"
          disabled={isLoading}
        />
        <button type="submit" className="search-btn" disabled={isLoading || !query.trim()}>
          {isLoading ? (
            <div className="loading-spinner" style={{ width: 20, height: 20, borderWidth: 2 }} />
          ) : (
            <>
              <Search size={18} />
              <span>Analyze</span>
            </>
          )}
        </button>
      </form>

      <div className="search-suggestions">
        <Zap size={12} style={{ color: 'var(--color-text-muted)' }} />
        {SUGGESTIONS.map((suggestion) => (
          <button
            key={suggestion}
            className="suggestion-chip"
            onClick={() => handleSuggestion(suggestion)}
            disabled={isLoading}
          >
            {suggestion}
          </button>
        ))}
      </div>
    </div>
  );
};
