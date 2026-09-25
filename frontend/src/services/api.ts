const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${url}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API Error: ${res.status}`);
  }
  return res.json();
}

export const api = {
  health: () => request<any>('/api/health'),
  getAssets: () => request<{ assets: any[] }>('/api/assets'),
  getDatasetSummary: (s: string) => request<any>(`/api/dataset/${encodeURIComponent(s)}/summary`),
  getPrices: (s: string, limit = 500) => request<any>(`/api/dataset/${encodeURIComponent(s)}/prices?limit=${limit}`),
  getFeatures: (s: string) => request<any>(`/api/features/${encodeURIComponent(s)}`),
  getFundamentals: (s: string) => request<any>(`/api/fundamentals/${encodeURIComponent(s)}`),
  getPrediction: (s: string) => request<any>(`/api/prediction/${encodeURIComponent(s)}`),
  getSignals: (s: string, limit = 100) => request<any>(`/api/signals/${encodeURIComponent(s)}?limit=${limit}`),
  getRegime: (s: string) => request<any>(`/api/regime/${encodeURIComponent(s)}`),
  getExplanation: (s: string) => request<any>(`/api/explain/${encodeURIComponent(s)}`),
  getModelMetrics: (s: string) => request<any>(`/api/models/${encodeURIComponent(s)}/metrics`),
  getModelComparison: (s: string) => request<any>(`/api/models/${encodeURIComponent(s)}/comparison`),
  getBacktest: (s: string) => request<any>(`/api/backtest/${encodeURIComponent(s)}`),
  getEquity: (s: string) => request<any>(`/api/backtest/${encodeURIComponent(s)}/equity`),
  train: (data: any) => request<any>('/api/train', { method: 'POST', body: JSON.stringify(data) }),
  runBacktest: (data: any) => request<any>('/api/backtest/run', { method: 'POST', body: JSON.stringify(data) }),
  refreshData: (s: string) => request<any>(`/api/data/refresh?symbol=${encodeURIComponent(s)}`, { method: 'POST' }),
};
