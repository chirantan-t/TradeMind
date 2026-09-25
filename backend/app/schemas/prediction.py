from pydantic import BaseModel
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
