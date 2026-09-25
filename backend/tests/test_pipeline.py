import pytest
import pandas as pd
from app.features.target import generate_target
from app.data.splitter import chronological_split

def test_target_generation():
    # Create dummy data
    df = pd.DataFrame({
        'Date': pd.date_range('2020-01-01', periods=10),
        'Close': [100, 102, 101, 105, 100, 95, 90, 80, 85, 90]
    })
    
    # Generate target with horizon=1, threshold=0.01
    df_tgt, info = generate_target(df, horizon=1, threshold=0.01)
    
    assert 'target' in df_tgt.columns
    assert 'future_return' in df_tgt.columns
    # Horizon=1 means the last row is dropped
    assert len(df_tgt) == 9

def test_chronological_split():
    df = pd.DataFrame({
        'Date': pd.date_range('2020-01-01', periods=100),
        'Val': range(100)
    })
    
    train_df, val_df, test_df, info = chronological_split(df, 0.7, 0.15, 0.15)
    
    assert len(train_df) == 70
    assert len(val_df) == 15
    assert len(test_df) == 15
    # Ensure no shuffling
    assert train_df['Val'].iloc[0] == 0
    assert train_df['Val'].iloc[-1] == 69
    assert val_df['Val'].iloc[0] == 70
