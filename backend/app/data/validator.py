"""Data validation and cleaning pipeline."""
import logging
import pandas as pd
import numpy as np
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class DataQualityReport:
    total_rows: int
    missing_values: int
    missing_by_column: dict
    duplicate_dates: int
    invalid_ohlc_rows: int
    zero_negative_prices: int
    invalid_volume: int
    date_start: str
    date_end: str
    trading_days: int

    def to_dict(self):
        return asdict(self)


def validate_and_clean(df: pd.DataFrame) -> tuple[pd.DataFrame, DataQualityReport]:
    """Validate and clean OHLCV DataFrame. Returns cleaned df and quality report."""
    df = df.copy()

    # Parse dates
    if not pd.api.types.is_datetime64_any_dtype(df['Date']):
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    # Sort chronologically
    df = df.sort_values('Date').reset_index(drop=True)

    # Track issues
    original_len = len(df)

    # Remove duplicate dates
    dup_dates = df['Date'].duplicated().sum()
    if dup_dates > 0:
        df = df.drop_duplicates(subset='Date', keep='last').reset_index(drop=True)
        logger.warning(f'Removed {dup_dates} duplicate dates')

    # Missing values
    numeric_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    missing_by_col = {}
    for col in numeric_cols:
        if col in df.columns:
            n_miss = df[col].isna().sum()
            if n_miss > 0:
                missing_by_col[col] = int(n_miss)

    total_missing = sum(missing_by_col.values())

    # Forward-fill then backward-fill small gaps
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].ffill().bfill()

    # Validate OHLC relationships: High >= Low, High >= Open, High >= Close
    invalid_ohlc = 0
    if all(c in df.columns for c in ['Open', 'High', 'Low', 'Close']):
        bad = (df['High'] < df['Low']) | (df['High'] < df['Open']) | (df['High'] < df['Close'])
        bad = bad | (df['Low'] > df['Open']) | (df['Low'] > df['Close'])
        invalid_ohlc = int(bad.sum())
        if invalid_ohlc > 0:
            logger.warning(f'{invalid_ohlc} rows with invalid OHLC relationships')

    # Zero or negative prices
    price_cols = ['Open', 'High', 'Low', 'Close']
    zero_neg = 0
    for col in price_cols:
        if col in df.columns:
            bad = df[col] <= 0
            zero_neg += int(bad.sum())

    if zero_neg > 0:
        mask = pd.Series(True, index=df.index)
        for col in price_cols:
            if col in df.columns:
                mask = mask & (df[col] > 0)
        df = df[mask].reset_index(drop=True)
        logger.warning(f'Removed rows with zero/negative prices')

    # Volume validation
    invalid_vol = 0
    if 'Volume' in df.columns:
        bad_vol = df['Volume'] < 0
        invalid_vol = int(bad_vol.sum())
        df.loc[bad_vol, 'Volume'] = 0

    # Drop rows with any remaining NaN in critical columns
    critical = [c for c in ['Date', 'Open', 'High', 'Low', 'Close'] if c in df.columns]
    df = df.dropna(subset=critical).reset_index(drop=True)

    report = DataQualityReport(
        total_rows=len(df),
        missing_values=total_missing,
        missing_by_column=missing_by_col,
        duplicate_dates=int(dup_dates),
        invalid_ohlc_rows=invalid_ohlc,
        zero_negative_prices=zero_neg,
        invalid_volume=invalid_vol,
        date_start=df['Date'].min().strftime('%Y-%m-%d') if len(df) > 0 else '',
        date_end=df['Date'].max().strftime('%Y-%m-%d') if len(df) > 0 else '',
        trading_days=len(df),
    )

    logger.info(f'Validation complete: {len(df)} clean rows')
    return df, report