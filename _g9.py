import os
B = r'D:\PROJECTS\trademind\backend'
def w(p, c):
    fp = os.path.join(B, p)
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    with open(fp, 'w', encoding='utf-8') as f: f.write(c)
    print(f'  {p}')

w('app/schemas/prediction.py', """from pydantic import BaseModel
from typing import Optional

class PredictionResponse(BaseModel):
    symbol: str
    date: str
    signal: str
    signal_code: int
    confidence: float
    probabilities: dict
    regime: dict
    model: str
    feature_drivers: list
    explanation: str

class SignalHistoryItem(BaseModel):
    date: str
    signal: str
    confidence: float
    regime: str
""")

w('app/schemas/training.py', """from pydantic import BaseModel
from typing import Optional

class TrainRequest(BaseModel):
    symbol: str = '^NSEI'
    horizon: int = 5
    threshold: float = 0.01
    train_ratio: float = 0.70
    validation_ratio: float = 0.15
    use_regime: bool = True

class TrainResponse(BaseModel):
    run_id: str
    symbol: str
    status: str
    dataset_info: dict
    split_info: dict
    class_distribution: dict
    regime_distribution: dict
    model_results: dict
    best_model: str
    feature_count: int
    timestamp: str
""")

w('app/schemas/backtest.py', """from pydantic import BaseModel
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
""")

print('Schemas done')