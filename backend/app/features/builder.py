"""Feature engineering orchestrator."""
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
    """Build all features from OHLCV data.

    Returns (df_with_features, feature_column_names).
    All features use only information available on or before the current date.
    No future data leakage.
    """
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
    df[feature_cols] = df[feature_cols].ffill().fillna(0)

    logger.info(f'Feature engineering complete: {len(feature_cols)} features, {len(df)} rows')
    return df, feature_cols
