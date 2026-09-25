"""Volume-based features."""
import numpy as np
import pandas as pd


def add_volume_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add volume features. Uses only past data."""
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

    # On-Balance Volume (OBV)
    obv_directions = np.sign(df['Close'].diff()).fillna(0)
    df['obv'] = (obv_directions * df['Volume']).cumsum()
    df['obv_ma_20'] = df['obv'].rolling(20).mean()

    return df
