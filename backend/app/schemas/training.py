from pydantic import BaseModel
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
