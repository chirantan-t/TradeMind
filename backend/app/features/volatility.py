"""Volatility and risk features."""
import numpy as np
import pandas as pd


def add_volatility_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add volatility/risk features. Uses only past data."""
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

    # Bollinger Width
    sma_20 = c.rolling(20).mean()
    std_20 = c.rolling(20).std()
    df['bollinger_upper'] = sma_20 + (std_20 * 2)
    df['bollinger_lower'] = sma_20 - (std_20 * 2)
    df['bollinger_width'] = (df['bollinger_upper'] - df['bollinger_lower']) / sma_20

    return df
