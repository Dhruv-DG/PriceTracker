/**
 * API service — communicates with the FastAPI backend.
 */
import type { SearchResponse, HealthResponse } from '../types';

const API_BASE = 'http://localhost:8000/api';

class ApiService {
  private async request<T>(url: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE}${url}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(errorData.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  async search(query: string): Promise<SearchResponse> {
    return this.request<SearchResponse>('/search', {
      method: 'POST',
      body: JSON.stringify({ query }),
    });
  }

  async healthCheck(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/health');
  }

  async startTracking(productId: number, frequencyMinutes: number = 360): Promise<any> {
    return this.request('/tracking', {
      method: 'POST',
      body: JSON.stringify({
        product_id: productId,
        frequency_minutes: frequencyMinutes,
      }),
    });
  }
}

export const api = new ApiService();
