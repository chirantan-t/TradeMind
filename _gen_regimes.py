import os
BASE = r'D:\PROJECTS\trademind\backend'
def write(path, content):
    full = os.path.join(BASE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'  {path}')

write('app/regimes/detector.py', r"""
"Regime detection using rule-based approach."
import logging
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def detect_regimes_rule_based(df: pd.DataFrame) -> pd.DataFrame:
    "Classify market regimes: BULL(0), BEAR(1), SIDEWAYS(2). Uses only past data."
    df = df.copy()
    if 'sma_50' not in df.columns:
        df['sma_50'] = df['Close'].rolling(50).mean()
    if 'sma_200' not in df.columns:
        df['sma_200'] = df['Close'].rolling(200).mean()

    above50 = df['Close'] > df['sma_50']
    above200 = df['Close'] > df['sma_200']
    sma50_above200 = df['sma_50'] > df['sma_200']

    if 'volatility_20d' not in df.columns:
        dr = df['Close'].pct_change()
        df['volatility_20d'] = dr.rolling(20).std() * np.sqrt(252)

    vol_med = df['volatility_20d'].expanding().median()
    high_vol = df['volatility_20d'] > vol_med

    regime = pd.Series(2, index=df.index)
    bull_mask = above50 & above200 & sma50_above200
    regime[bull_mask] = 0
    bear_mask = (~above50 & ~above200) | (~above50 & high_vol)
    regime[bear_mask] = 1

    df['regime'] = regime
    df['regime_label'] = df['regime'].map({0: 'BULL', 1: 'BEAR', 2: 'SIDEWAYS'})

    score = pd.Series(0.5, index=df.index)
    score[bull_mask] = 0.5 + 0.15 * above200.astype(float) + 0.15 * sma50_above200.astype(float) + 0.1 * (~high_vol).astype(float) + 0.1
    score[bear_mask] = 0.5 + 0.15 * (~above200).astype(float) + 0.15 * (~sma50_above200).astype(float) + 0.1 * high_vol.astype(float) + 0.1
    df['regime_score'] = score.clip(0, 1)

    dist = df['regime_label'].value_counts().to_dict()
    logger.info(f'Regime distribution: {dist}')
    return df


def get_regime_features(df: pd.DataFrame) -> pd.DataFrame:
    "Add one-hot regime features for model input."
    df = df.copy()
    if 'regime' not in df.columns:
        df = detect_regimes_rule_based(df)
    df['regime_bull'] = (df['regime'] == 0).astype(float)
    df['regime_bear'] = (df['regime'] == 1).astype(float)
    df['regime_sideways'] = (df['regime'] == 2).astype(float)
    return df
""".strip())

print('Regime detector created')