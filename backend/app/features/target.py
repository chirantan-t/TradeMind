"""Target variable generation using future returns."""
import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def generate_target(
    df: pd.DataFrame,
    horizon: int = 5,
    threshold: float = 0.01,
) -> tuple[pd.DataFrame, dict]:
    """Generate BUY/HOLD/SELL target from future returns.

    IMPORTANT: Uses FUTURE prices to create labels.
    The last horizon rows will have no target (dropped).

    Args:
        df: DataFrame with 'Close' column.
        horizon: Number of trading days to look ahead.
        threshold: Return threshold for BUY/SELL classification.

    Returns:
        (df_with_target, target_info_dict)
    """
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
