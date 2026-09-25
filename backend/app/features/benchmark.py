"""Benchmark / market context features."""
import numpy as np
import pandas as pd


def add_benchmark_features(df: pd.DataFrame, benchmark_df: pd.DataFrame = None) -> pd.DataFrame:
    """Add market context features. If no benchmark, uses self-referential features."""
    df = df.copy()
    c = df['Close']
    ret = df.get('daily_return', c.pct_change())

    # Self-benchmark features (market context from the asset itself)
    df['market_trend'] = c.rolling(50).mean().pct_change(20)
    df['market_volatility'] = ret.rolling(20).std() * np.sqrt(252)

    if benchmark_df is not None and len(benchmark_df) > 0:
        # Merge benchmark by date
        bench = benchmark_df[['Date', 'Close']].copy()
        bench = bench.rename(columns={'Close': 'bench_close'})
        df = df.merge(bench, on='Date', how='left')
        df['bench_close'] = df['bench_close'].ffill()

        bench_ret = df['bench_close'].pct_change()
        df['benchmark_return'] = bench_ret
        df['benchmark_volatility'] = bench_ret.rolling(20).std() * np.sqrt(252)
        df['relative_strength'] = ret.rolling(20).mean() / bench_ret.rolling(20).mean().replace(0, np.nan)
        df = df.drop(columns=['bench_close'])
    else:
        # Self-referential
        df['benchmark_return'] = ret.rolling(20).mean()
        df['benchmark_volatility'] = df['market_volatility']
        df['relative_strength'] = 1.0

    return df
