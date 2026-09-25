"""Technical indicator features."""
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
    """Add technical indicator features. Uses only past data."""
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

    # Stochastic Oscillator
    low_14 = df['Low'].rolling(14).min()
    high_14 = df['High'].rolling(14).max()
    df['stoch_k'] = 100 * ((c - low_14) / (high_14 - low_14 + 1e-8))
    df['stoch_d'] = df['stoch_k'].rolling(3).mean()

    # Williams %R
    df['williams_r'] = -100 * ((high_14 - c) / (high_14 - low_14 + 1e-8))

    return df
