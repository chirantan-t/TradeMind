from pydantic import BaseModel
from typing import Optional

class BacktestRequest(BaseModel):
    symbol: str = '^NSEI'
    initial_capital: float = 100000.0
    transaction_cost: float = 0.001
    slippage: float = 0.0005
    position_mode: str = 'long_short'

class BacktestResponse(BaseModel):
    metrics: dict
    equity_curve: list
    trades: list
    config: dict
