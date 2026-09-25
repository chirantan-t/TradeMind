import logging, numpy as np, pandas as pd
logger = logging.getLogger(__name__)

def run_backtest(df, signals, initial_capital=100000.0, transaction_cost=0.001,
                 slippage=0.0005, position_mode='long_short'):
    n = len(df)
    if n < 2: return {'error': 'Insufficient data'}
    prices = df['Close'].values
    dates = df['Date'].values
    daily_ret = np.diff(prices) / prices[:-1]

    positions = np.zeros(n)
    for i in range(n - 1):
        s = signals[i]
        if s == 0: positions[i+1] = 1.0
        elif s == 2: positions[i+1] = -1.0 if position_mode == 'long_short' else 0.0
        else: positions[i+1] = 0.0

    strat_ret = np.zeros(n)
    total_costs = 0.0
    total_slip = 0.0
    trades = []
    for i in range(1, n):
        pc = abs(positions[i] - positions[i-1])
        cost = pc * transaction_cost
        slip = pc * slippage
        total_costs += cost * prices[i]
        total_slip += slip * prices[i]
        strat_ret[i] = positions[i] * daily_ret[i-1] - cost - slip
        if pc > 0:
            trades.append({'date': str(dates[i])[:10], 'price': float(prices[i]),
                          'position': float(positions[i]), 'prev_position': float(positions[i-1]),
                          'cost': float(cost)})

    strat_eq = initial_capital * np.cumprod(1 + strat_ret)
    bench_eq = initial_capital * np.cumprod(1 + np.concatenate([[0], daily_ret]))
    rmax = np.maximum.accumulate(strat_eq)
    dd = (strat_eq - rmax) / rmax

    eq = [{'date': str(dates[i])[:10], 'strategy': float(strat_eq[i]),
           'benchmark': float(bench_eq[i]), 'drawdown': float(dd[i])} for i in range(n)]

    return {'equity_curve': eq, 'trades': trades,
            'total_transaction_costs': float(total_costs),
            'total_slippage': float(total_slip)}
