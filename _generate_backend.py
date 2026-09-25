#!/usr/bin/env python3
"""Generate all TradeMind backend source files."""
import os

BASE = r'D:\PROJECTS\trademind\backend'

def write(path, content):
    full = os.path.join(BASE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'  Created {path}')

# ============================================================
# FEATURES - returns.py
# ============================================================
write('app/features/returns.py', '''\"\"\"Return-based feature engineering.\"\"\"
import numpy as np
import pandas as pd


def add_return_features(df: pd.DataFrame) -> pd.DataFrame:
    \"\"\"Add return-based features. Uses only past data.\"\"\"
    df = df.copy()
    c = df['Close']

    # Daily returns
    df['daily_return'] = c.pct_change()
    df['log_return'] = np.log(c / c.shift(1))

    # Multi-day returns
    for w in [2, 5, 10, 14, 20]:
        df[f'return_{w}d'] = c.pct_change(w)

    # Lagged returns (1-5 days ago)
    for lag in range(1, 6):
        df[f'return_lag_{lag}'] = df['daily_return'].shift(lag)

    # Rolling mean returns
    for w in [5, 10, 20]:
        df[f'rolling_mean_return_{w}d'] = df['daily_return'].rolling(w).mean()

    return df
''')

# ============================================================
# FEATURES - technical.py
# ============================================================
write('app/features/technical.py', '''\"\"\"Technical indicator features.\"\"\"
import numpy as np
import pandas as pd


def _sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window).mean()


def _ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def add_technical_features(df: pd.DataFrame) -> pd.DataFrame:
    \"\"\"Add technical indicator features. Uses only past data.\"\"\"
    df = df.copy()
    c = df['Close']

    # Simple Moving Averages
    for w in [5, 10, 20, 50, 100, 200]:
        sma = _sma(c, w)
        df[f'sma_{w}'] = sma
        df[f'price_sma_{w}_ratio'] = c / sma
        df[f'dist_sma_{w}'] = (c - sma) / sma

    # Exponential Moving Averages
    df['ema_12'] = _ema(c, 12)
    df['ema_26'] = _ema(c, 26)

    # Trend slope (linear regression slope over 20 days)
    df['trend_slope_20'] = c.rolling(20).apply(
        lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) == 20 else np.nan,
        raw=False
    )

    # MA crossover signals
    df['sma_5_20_cross'] = (df['sma_5'] > df['sma_20']).astype(float)
    df['sma_20_50_cross'] = (df['sma_20'] > df['sma_50']).astype(float)
    df['ema_cross'] = (df['ema_12'] > df['ema_26']).astype(float)

    # RSI
    df['rsi_14'] = _rsi(c, 14)

    # MACD
    df['macd'] = df['ema_12'] - df['ema_26']
    df['macd_signal'] = _ema(df['macd'], 9)
    df['macd_histogram'] = df['macd'] - df['macd_signal']

    # Rate of Change
    for w in [5, 10, 20]:
        df[f'roc_{w}'] = c.pct_change(w) * 100

    # Momentum
    for w in [5, 10, 14, 20]:
        df[f'momentum_{w}'] = c - c.shift(w)

    return df
''')

# ============================================================
# FEATURES - volatility.py
# ============================================================
write('app/features/volatility.py', '''\"\"\"Volatility and risk features.\"\"\"
import numpy as np
import pandas as pd


def add_volatility_features(df: pd.DataFrame) -> pd.DataFrame:
    \"\"\"Add volatility/risk features. Uses only past data.\"\"\"
    df = df.copy()
    c = df['Close']
    h = df['High']
    l = df['Low']
    ret = df.get('daily_return', c.pct_change())

    # Rolling volatility (annualized std of daily returns)
    for w in [5, 10, 20, 30]:
        df[f'volatility_{w}d'] = ret.rolling(w).std() * np.sqrt(252)

    # True Range
    prev_close = c.shift(1)
    tr = pd.concat([
        h - l,
        (h - prev_close).abs(),
        (l - prev_close).abs()
    ], axis=1).max(axis=1)
    df['true_range'] = tr

    # ATR
    df['atr_14'] = tr.rolling(14).mean()
    df['atr_pct'] = df['atr_14'] / c

    # High-Low range
    df['hl_range'] = (h - l) / c

    # Rolling max drawdown (20-day)
    rolling_max = c.rolling(20, min_periods=1).max()
    df['rolling_drawdown_20'] = (c - rolling_max) / rolling_max

    return df
''')

# ============================================================
# FEATURES - volume.py
# ============================================================
write('app/features/volume.py', '''\"\"\"Volume-based features.\"\"\"
import numpy as np
import pandas as pd


def add_volume_features(df: pd.DataFrame) -> pd.DataFrame:
    \"\"\"Add volume features. Uses only past data.\"\"\"
    df = df.copy()
    v = df['Volume'].replace(0, np.nan)

    # Volume % change
    df['volume_pct_change'] = v.pct_change()

    # Volume moving averages
    for w in [5, 10, 20]:
        vma = v.rolling(w).mean()
        df[f'volume_ma_{w}'] = vma
        df[f'volume_ratio_{w}'] = v / vma

    # Volume z-score (20-day)
    v_mean = v.rolling(20).mean()
    v_std = v.rolling(20).std()
    df['volume_zscore'] = (v - v_mean) / v_std.replace(0, np.nan)

    # Price-volume relationship (correlation over 20 days)
    df['price_volume_corr'] = df['Close'].rolling(20).corr(v)

    return df
''')

# ============================================================
# FEATURES - benchmark.py
# ============================================================
write('app/features/benchmark.py', '''\"\"\"Benchmark / market context features.\"\"\"
import numpy as np
import pandas as pd


def add_benchmark_features(df: pd.DataFrame, benchmark_df: pd.DataFrame = None) -> pd.DataFrame:
    \"\"\"Add market context features. If no benchmark, uses self-referential features.\"\"\"
    df = df.copy()
    c = df['Close']
    ret = df.get('daily_return', c.pct_change())

    # Self-benchmark features (market context from the asset itself)
    df['market_trend'] = c.rolling(50).mean().pct_change(20)
    df['market_volatility'] = ret.rolling(20).std() * np.sqrt(252)

    if benchmark_df is not None and len(benchmark_df) > 0:
        # Merge benchmark by date
        bench = benchmark_df[['Date', 'Close']].copy()
        bench = bench.rename(columns={'Close': 'bench_close'})
        df = df.merge(bench, on='Date', how='left')
        df['bench_close'] = df['bench_close'].ffill()

        bench_ret = df['bench_close'].pct_change()
        df['benchmark_return'] = bench_ret
        df['benchmark_volatility'] = bench_ret.rolling(20).std() * np.sqrt(252)
        df['relative_strength'] = ret.rolling(20).mean() / bench_ret.rolling(20).mean().replace(0, np.nan)
        df = df.drop(columns=['bench_close'])
    else:
        # Self-referential
        df['benchmark_return'] = ret.rolling(20).mean()
        df['benchmark_volatility'] = df['market_volatility']
        df['relative_strength'] = 1.0

    return df
''')

# ============================================================
# FEATURES - builder.py
# ============================================================
write('app/features/builder.py', '''\"\"\"Feature engineering orchestrator.\"\"\"
import logging
import pandas as pd
import numpy as np
from app.features.returns import add_return_features
from app.features.technical import add_technical_features
from app.features.volatility import add_volatility_features
from app.features.volume import add_volume_features
from app.features.benchmark import add_benchmark_features

logger = logging.getLogger(__name__)

# Features that are NOT model inputs (identifiers, targets, etc.)
NON_FEATURE_COLS = {'Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Adj Close',
                    'target', 'future_return', 'regime', 'regime_label',
                    'split', 'signal', 'position'}


def build_features(df: pd.DataFrame, benchmark_df: pd.DataFrame = None) -> tuple[pd.DataFrame, list[str]]:
    \"\"\"Build all features from OHLCV data.

    Returns (df_with_features, feature_column_names).
    All features use only information available on or before the current date.
    No future data leakage.
    \"\"\"
    logger.info('Building features...')

    df = add_return_features(df)
    df = add_technical_features(df)
    df = add_volatility_features(df)
    df = add_volume_features(df)
    df = add_benchmark_features(df, benchmark_df)

    # Drop warm-up NaN rows (from longest lookback: SMA 200)
    initial_len = len(df)
    df = df.dropna(subset=['sma_200']).reset_index(drop=True)
    dropped = initial_len - len(df)
    logger.info(f'Dropped {dropped} warm-up rows (SMA-200 lookback)')

    # Identify feature columns
    feature_cols = [c for c in df.columns if c not in NON_FEATURE_COLS]

    # Replace any remaining inf/-inf with NaN, then fill
    for col in feature_cols:
        df[col] = df[col].replace([np.inf, -np.inf], np.nan)
    df[feature_cols] = df[feature_cols].fillna(method='ffill').fillna(0)

    logger.info(f'Feature engineering complete: {len(feature_cols)} features, {len(df)} rows')
    return df, feature_cols
''')

# ============================================================
# FEATURES - target.py
# ============================================================
write('app/features/target.py', '''\"\"\"Target variable generation using future returns.\"\"\"
import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def generate_target(
    df: pd.DataFrame,
    horizon: int = 5,
    threshold: float = 0.01,
) -> tuple[pd.DataFrame, dict]:
    \"\"\"Generate BUY/HOLD/SELL target from future returns.

    IMPORTANT: Uses FUTURE prices to create labels.
    The last horizon rows will have no target (dropped).

    Args:
        df: DataFrame with 'Close' column.
        horizon: Number of trading days to look ahead.
        threshold: Return threshold for BUY/SELL classification.

    Returns:
        (df_with_target, target_info_dict)
    \"\"\"
    df = df.copy()

    # Future return: Close[t+horizon] / Close[t] - 1
    df['future_return'] = df['Close'].shift(-horizon) / df['Close'] - 1

    # Classify
    conditions = [
        df['future_return'] > threshold,   # BUY
        df['future_return'] < -threshold,  # SELL
    ]
    choices = [0, 2]  # 0=BUY, 1=HOLD, 2=SELL
    df['target'] = np.select(conditions, choices, default=1)

    # Drop rows where future return is unavailable
    df = df.dropna(subset=['future_return']).reset_index(drop=True)

    # Class distribution
    class_counts = df['target'].value_counts().to_dict()
    label_map = {0: 'BUY', 1: 'HOLD', 2: 'SELL'}
    distribution = {label_map.get(k, str(k)): int(v) for k, v in class_counts.items()}

    info = {
        'horizon': horizon,
        'threshold': threshold,
        'total_samples': len(df),
        'class_distribution': distribution,
        'label_map': label_map,
    }

    logger.info(f'Target generated: horizon={horizon}, threshold={threshold}')
    logger.info(f'Class distribution: {distribution}')
    return df, info
''')

# ============================================================
# DATA - splitter.py
# ============================================================
write('app/data/splitter.py', '''\"\"\"Chronological time-series data splitting.\"\"\"
import logging
import pandas as pd

logger = logging.getLogger(__name__)


def chronological_split(
    df: pd.DataFrame,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    \"\"\"Split data chronologically. NEVER shuffles.

    Returns (train_df, val_df, test_df, split_info).
    \"\"\"
    assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6, \\
        'Split ratios must sum to 1.0'

    n = len(df)
    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))

    train_df = df.iloc[:train_end].copy().reset_index(drop=True)
    val_df = df.iloc[train_end:val_end].copy().reset_index(drop=True)
    test_df = df.iloc[val_end:].copy().reset_index(drop=True)

    split_info = {
        'total_samples': n,
        'train_samples': len(train_df),
        'val_samples': len(val_df),
        'test_samples': len(test_df),
        'train_start': train_df['Date'].min().strftime('%Y-%m-%d'),
        'train_end': train_df['Date'].max().strftime('%Y-%m-%d'),
        'val_start': val_df['Date'].min().strftime('%Y-%m-%d'),
        'val_end': val_df['Date'].max().strftime('%Y-%m-%d'),
        'test_start': test_df['Date'].min().strftime('%Y-%m-%d'),
        'test_end': test_df['Date'].max().strftime('%Y-%m-%d'),
        'train_ratio': train_ratio,
        'val_ratio': val_ratio,
        'test_ratio': test_ratio,
    }

    logger.info(f'Split: train={len(train_df)}, val={len(val_df)}, test={len(test_df)}')
    return train_df, val_df, test_df, split_info
''')

print('\\nPhase 2-4 files created successfully.')