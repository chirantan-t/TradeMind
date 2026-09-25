import os
import json
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import yfinance as yf
from app.core.config import settings

logger = logging.getLogger(__name__)

class MarketDataProvider(ABC):
    @abstractmethod
    def download_ohlcv(self, symbol: str, start: str, end: Optional[str] = None, force: bool = False) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_current_fundamentals(self, symbol: str) -> Dict[str, Any]:
        pass

class YahooFinanceProvider(MarketDataProvider):
    def _safe_symbol_filename(self, symbol: str) -> str:
        return symbol.replace('^', '').replace('/', '_').replace(' ', '_')

    def download_ohlcv(self, symbol: str, start: str = '2010-01-01', end: Optional[str] = None, force: bool = False) -> Dict[str, Any]:
        if end is None:
            end = datetime.now().strftime('%Y-%m-%d')

        raw_dir = settings.raw_data_path / 'NSE'
        raw_dir.mkdir(parents=True, exist_ok=True)

        filename = f'{self._safe_symbol_filename(symbol)}.csv'
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
            raise RuntimeError(f'No data returned for {symbol}.')

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

    def get_current_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """Fetch current fundamentals. Point-in-time ONLY for current display, NOT historical training."""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                "pe_ratio": info.get("trailingPE"),
                "pb_ratio": info.get("priceToBook"),
                "ev_ebitda": info.get("enterpriseToEbitda"),
                "roe": info.get("returnOnEquity"),
                "roce": info.get("returnOnAssets"),  # proxy
                "operating_margin": info.get("operatingMargins"),
                "net_margin": info.get("profitMargins"),
                "revenue_growth": info.get("revenueGrowth"),
                "eps_growth": info.get("earningsGrowth"),
                "debt_to_equity": info.get("debtToEquity"),
                "current_ratio": info.get("currentRatio"),
                "dividend_yield": info.get("dividendYield"),
                "market_cap": info.get("marketCap")
            }
        except Exception as e:
            logger.warning(f"Failed to fetch fundamentals for {symbol}: {e}")
            return {}

# Default global provider
market_provider = YahooFinanceProvider()

def get_universe() -> List[Dict[str, str]]:
    """Get the supported universe from stocks.json."""
    stocks_path = Path(__file__).parent / 'stocks.json'
    if not stocks_path.exists():
        return []
    with open(stocks_path, 'r') as f:
        return json.load(f)
