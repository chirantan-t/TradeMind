"""TradeMind configuration module."""
import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    DATABASE_URL: str = "sqlite:///./trademind.db"
    CORS_ORIGINS: str = "http://localhost:5173"
    DATA_DIR: str = "./data"
    ARTIFACTS_DIR: str = "./artifacts"
    
    # Default assets
    DEFAULT_SYMBOL: str = "^NSEI"
    SUPPORTED_ASSETS: list[str] = [
        "^NSEI",   # NIFTY 50
        "SPY",     # S&P 500 ETF
        "QQQ",     # Nasdaq 100 ETF
        "^GSPC",   # S&P 500 Index
    ]
    
    ASSET_NAMES: dict[str, str] = {
        "^NSEI": "NIFTY 50",
        "SPY": "S&P 500 ETF",
        "QQQ": "Nasdaq 100 ETF",
        "^GSPC": "S&P 500 Index",
    }
    
    ASSET_CURRENCIES: dict[str, str] = {
        "^NSEI": "INR",
        "SPY": "USD",
        "QQQ": "USD",
        "^GSPC": "USD",
    }
    
    # Training defaults
    DEFAULT_HORIZON: int = 5
    DEFAULT_THRESHOLD: float = 0.01
    DEFAULT_TRAIN_RATIO: float = 0.70
    DEFAULT_VALIDATION_RATIO: float = 0.15
    DEFAULT_TEST_RATIO: float = 0.15
    
    # Backtest defaults
    DEFAULT_INITIAL_CAPITAL: float = 100000.0
    DEFAULT_TRANSACTION_COST: float = 0.001   # 0.10%
    DEFAULT_SLIPPAGE: float = 0.0005           # 0.05%
    
    @property
    def data_path(self) -> Path:
        return Path(self.DATA_DIR)
    
    @property
    def artifacts_path(self) -> Path:
        return Path(self.ARTIFACTS_DIR)
    
    @property
    def raw_data_path(self) -> Path:
        return self.data_path / "raw"
    
    @property
    def processed_data_path(self) -> Path:
        return self.data_path / "processed"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
