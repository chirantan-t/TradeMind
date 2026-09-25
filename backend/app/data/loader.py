"""Load and prepare data for the ML pipeline."""
import logging
import pandas as pd
from pathlib import Path
from app.core.config import settings
from app.data.provider import market_provider
from app.data.validator import validate_and_clean, DataQualityReport

logger = logging.getLogger(__name__)


def load_data(symbol: str, force_download: bool = False) -> tuple[pd.DataFrame, dict, DataQualityReport]:
    """Load data for a symbol: download if needed, validate, return clean df."""
    meta = market_provider.download_ohlcv(symbol, force=force_download)
    df = pd.read_csv(meta['path'], parse_dates=['Date'])
    df, report = validate_and_clean(df)
    return df, meta, report