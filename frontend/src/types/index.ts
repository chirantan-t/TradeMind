export interface Asset {
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
