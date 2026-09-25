"""Download historical OHLCV data from Yahoo Finance."""
import os
import logging
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf
from app.core.config import settings

logger = logging.getLogger(__name__)


def _safe_symbol_filename(symbol: str) -> str:
    return symbol.replace('^', '').replace('/', '_').replace(' ', '_')


def download_ohlcv(
    symbol: str,
    start: str = '2010-01-01',
    end: str | None = None,
    force: bool = False,
) -> dict:
    """Download OHLCV data for a symbol. Caches to data/raw/{symbol}.csv."""
    if end is None:
        end = datetime.now().strftime('%Y-%m-%d')

    raw_dir = settings.raw_data_path
    raw_dir.mkdir(parents=True, exist_ok=True)

    filename = f'{_safe_symbol_filename(symbol)}.csv'
    filepath = raw_dir / filename

    # Check cache unless forced
    if filepath.exists() and not force:
        df = pd.read_csv(filepath, parse_dates=['Date'])
        last_date = df['Date'].max()
        if (datetime.now() - last_date).days <= 1:
            logger.info(f'Using cached data for {symbol} ({len(df)} rows)')
            return {
                'path': str(filepath),
                'source': 'Yahoo Finance (cached)',
                'symbol': symbol,
                'start': df['Date'].min().strftime('%Y-%m-%d'),
                'end': df['Date'].max().strftime('%Y-%m-%d'),
                'rows': len(df),
                'cached': True,
            }

    logger.info(f'Downloading {symbol} from Yahoo Finance: {start} to {end}')

    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start, end=end, auto_adjust=False)
    except Exception as e:
        raise RuntimeError(f'Failed to download data for {symbol}: {e}')

    if df is None or df.empty:
        raise RuntimeError(
            f'No data returned for {symbol}. '
            f'The ticker may be invalid or data unavailable.'
        )

    df = df.reset_index()

    col_map = {}
    for col in df.columns:
        col_lower = str(col).lower().strip()
        if col_lower == 'date': col_map[col] = 'Date'
        elif col_lower == 'open': col_map[col] = 'Open'
        elif col_lower == 'high': col_map[col] = 'High'
        elif col_lower == 'low': col_map[col] = 'Low'
        elif col_lower == 'close': col_map[col] = 'Close'
        elif col_lower in ('adj close', 'adj_close', 'adjclose'): col_map[col] = 'Adj Close'
        elif col_lower == 'volume': col_map[col] = 'Volume'

    df = df.rename(columns=col_map)

    required = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise RuntimeError(f'Downloaded data for {symbol} is missing columns: {missing}')

    keep = [c for c in required + ['Adj Close'] if c in df.columns]
    df = df[keep].copy()

    if hasattr(df['Date'].dtype, 'tz') and df['Date'].dtype.tz is not None:
        df['Date'] = df['Date'].dt.tz_localize(None)

    df = df.sort_values('Date').reset_index(drop=True)
    df.to_csv(filepath, index=False)
    logger.info(f'Saved {len(df)} rows to {filepath}')

    return {
        'path': str(filepath),
        'source': 'Yahoo Finance',
        'symbol': symbol,
        'start': df['Date'].min().strftime('%Y-%m-%d'),
        'end': df['Date'].max().strftime('%Y-%m-%d'),
        'rows': len(df),
        'cached': False,
    }