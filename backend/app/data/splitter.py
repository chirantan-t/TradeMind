"""Chronological time-series data splitting."""
import logging
import pandas as pd

logger = logging.getLogger(__name__)


def chronological_split(
    df: pd.DataFrame,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    """Split data chronologically. NEVER shuffles.

    Returns (train_df, val_df, test_df, split_info).
    """
    assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6, \
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
