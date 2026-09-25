import os
F = r'D:\PROJECTS\trademind\frontend\src'
def w(p, c):
    fp = os.path.join(F, p)
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    with open(fp, 'w', encoding='utf-8') as f: f.write(c)
    print(f'  {p}')

# index.css - Tailwind v4 + custom design tokens
w('index.css', """@import "tailwindcss";

@theme {
  --color-bg-primary: #0a0e1a;
  --color-bg-card: #0d1b2a;
  --color-bg-card-hover: #112240;
  --color-border: #1e3a5f;
  --color-border-light: #1a2d47;
  --color-accent: #14b8a6;
  --color-accent-dim: #0d9488;
  --color-text-primary: #e2e8f0;
  --color-text-secondary: #94a3b8;
  --color-text-muted: #64748b;
  --color-buy: #10b981;
  --color-hold: #f59e0b;
  --color-sell: #ef4444;
  --color-bull: #10b981;
  --color-bear: #ef4444;
  --color-sideways: #64748b;
  --font-mono: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
}

@layer base {
  body {
    background-color: var(--color-bg-primary);
    color: var(--color-text-primary);
    font-family: 'Inter', system-ui, sans-serif;
    -webkit-font-smoothing: antialiased;
  }
  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-track { background: var(--color-bg-primary); }
  ::-webkit-scrollbar-thumb { background: var(--color-border); border-radius: 3px; }
}
""")

# types/index.ts
w('types/index.ts', """export interface Asset {
  symbol: string;
  name: string;
  currency: string;
}

export interface Prediction {
  symbol: string;
  date: string;
  signal: string;
  signal_code: number;
  confidence: number;
  probabilities: { BUY: number; HOLD: number; SELL: number };
  regime: { label: string; score: number; volatility: number };
  model: string;
  feature_drivers: FeatureDriver[];
  explanation: string;
}

export interface FeatureDriver {
  feature: string;
  contribution: number;
  importance?: number;
}

export interface ModelMetrics {
  accuracy: number;
  f1_weighted: number;
  f1_macro: number;
  precision_weighted: number;
  recall_weighted: number;
  roc_auc: number | null;
  confusion_matrix: number[][];
  per_class: Record<string, { precision: number; recall: number; f1: number }>;
}

export interface ModelResult {
  name: string;
  val_metrics: ModelMetrics;
  test_metrics: ModelMetrics;
  train_time: number;
  status: string;
}

export interface BacktestMetrics {
  cumulative_return: number;
  annualized_return: number;
  benchmark_return: number;
  sharpe_ratio: number;
  max_drawdown: number;
  volatility: number;
  win_rate: number;
  total_trades: number;
  alpha: number;
  total_transaction_costs: number;
  total_slippage: number;
  net_pnl: number;
  final_equity: number;
  period_start: string;
  period_end: string;
  trading_days: number;
}

export interface EquityPoint {
  date: string;
  strategy: number;
  benchmark: number;
  drawdown: number;
}

export interface SignalItem {
  date: string;
  signal: string;
  confidence: number;
  prob_buy: number;
  prob_hold: number;
  prob_sell: number;
  regime: string;
  regime_score: number;
  close: number;
}

export interface DatasetSummary {
  source: string;
  symbol: string;
  name: string;
  start: string;
  end: string;
  rows: number;
  missing_values: number;
  duplicate_dates: number;
  invalid_ohlc: number;
  feature_count: number;
  split_info: Record<string, any>;
  target_info: Record<string, any>;
  class_distribution: Record<string, number>;
  regime_distribution: Record<string, number>;
  currency: string;
}

export interface TrainRequest {
  symbol: string;
  horizon: number;
  threshold: number;
  train_ratio: number;
  validation_ratio: number;
  use_regime: boolean;
}

export interface TrainResponse {
  run_id: string;
  symbol: string;
  status: string;
  dataset_info: any;
  split_info: any;
  class_distribution: Record<string, number>;
  regime_distribution: Record<string, number>;
  model_results: Record<string, ModelResult>;
  best_model: string;
  feature_count: number;
  backtest_metrics: BacktestMetrics;
  timestamp: string;
}

export interface PricePoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  regime?: string;
}
""")

# services/api.ts
w('services/api.ts', """const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

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
""")

print('Core frontend files done')