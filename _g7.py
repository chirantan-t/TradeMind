import os
B = r'D:\PROJECTS\trademind\backend'
def w(p, c):
    fp = os.path.join(B, p)
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    with open(fp, 'w', encoding='utf-8') as f: f.write(c)
    print(f'  {p}')

w('app/backtesting/engine.py', """import logging, numpy as np, pandas as pd
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
""")

w('app/backtesting/metrics.py', """import numpy as np

def calculate_metrics(equity_curve, trades, initial_capital=100000.0,
                      total_costs=0.0, total_slippage=0.0):
    if not equity_curve or len(equity_curve) < 2:
        return {'error': 'Insufficient data'}
    sv = np.array([e['strategy'] for e in equity_curve])
    bv = np.array([e['benchmark'] for e in equity_curve])
    dd = np.array([e['drawdown'] for e in equity_curve])
    n = len(sv)
    sdr = np.diff(sv) / sv[:-1]
    cum_ret = (sv[-1] / initial_capital) - 1
    bench_ret = (bv[-1] / initial_capital) - 1
    years = n / 252
    ann_ret = (1 + cum_ret)**(1/max(years, 0.01)) - 1 if cum_ret > -1 else -1
    vol = float(np.std(sdr) * np.sqrt(252)) if len(sdr) > 0 else 0
    sharpe = float(np.mean(sdr) / np.std(sdr) * np.sqrt(252)) if np.std(sdr) > 0 else 0
    max_dd = float(np.min(dd)) if len(dd) > 0 else 0
    win_days = np.sum(sdr > 0)
    win_rate = float(win_days / len(sdr)) if len(sdr) > 0 else 0
    n_trades = len(trades)
    alpha = cum_ret - bench_ret
    return {
        'cumulative_return': float(cum_ret), 'annualized_return': float(ann_ret),
        'benchmark_return': float(bench_ret), 'sharpe_ratio': float(sharpe),
        'max_drawdown': float(max_dd), 'volatility': float(vol),
        'win_rate': float(win_rate), 'total_trades': n_trades,
        'alpha': float(alpha), 'total_transaction_costs': float(total_costs),
        'total_slippage': float(total_slippage),
        'net_pnl': float(sv[-1] - initial_capital),
        'final_equity': float(sv[-1]),
        'period_start': equity_curve[0]['date'],
        'period_end': equity_curve[-1]['date'],
        'trading_days': n}
""")

w('app/backtesting/costs.py', """class TransactionCostModel:
    def __init__(self, cost_pct=0.001, slippage_pct=0.0005):
        self.cost_pct = cost_pct
        self.slippage_pct = slippage_pct
    def calculate(self, trade_value, position_change):
        cost = abs(position_change) * self.cost_pct * trade_value
        slip = abs(position_change) * self.slippage_pct * trade_value
        return {'transaction_cost': cost, 'slippage': slip, 'total': cost + slip}
""")

print('Backtesting modules done')