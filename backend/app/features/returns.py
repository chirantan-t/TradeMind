"""Return-based feature engineering."""
import numpy as np
import pandas as pd


def add_return_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add return-based features. Uses only past data."""
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
